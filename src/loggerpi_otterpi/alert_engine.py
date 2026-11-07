"""Alert-Engine für den OtterPi."""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

from alert_store import AlertStore
from config_store import (
    ConfigValidationError,
    load_alarm_limits,
    load_mail,
    load_notifications,
)
from notifier import Alert, create_notifiers
from otterpi_store import BatchStore

LOGGER = logging.getLogger(__name__)


class AlertEngine(threading.Thread):
    def __init__(
        self,
        *,
        store: BatchStore,
        alert_store: AlertStore,
        smtp_password: Optional[str],
        interval_seconds: int = 300,
    ) -> None:
        super().__init__(name="AlertEngine", daemon=True)
        self._store = store
        self._alert_store = alert_store
        self._smtp_password = smtp_password
        self._interval = interval_seconds
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._pending_alerts: list = []

    def notify_batch(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def run(self) -> None:
        LOGGER.info("AlertEngine started (interval=%ss)", self._interval)
        while not self._stop.is_set():
            self._wake.wait(timeout=self._interval)
            self._wake.clear()
            if self._stop.is_set():
                break
            try:
                self._check()
            except Exception:
                LOGGER.exception("AlertEngine check failed")
        LOGGER.info("AlertEngine stopped")

    def _check(self) -> None:
        batch = self._store.latest()
        if batch is None:
            return

        try:
            alarm_limits = load_alarm_limits()
        except ConfigValidationError:
            LOGGER.warning("alarm_limits.json invalid; skipping check")
            return

        try:
            mail = load_mail()
        except ConfigValidationError:
            mail = {}
        try:
            notifications = load_notifications()
        except ConfigValidationError:
            notifications = {"channels": []}

        notifiers = create_notifiers(notifications, mail, self._smtp_password)

        batch_dict = batch.to_dict()
        self._pending_alerts = self._check_sensors(batch_dict, alarm_limits.get("sensors", {}))
        self._pending_alerts.extend(self._check_states(batch_dict, alarm_limits.get("states", {})))

        for alert in self._pending_alerts:
            self._dispatch(alert, mail, notifiers)

    def _check_sensors(self, batch: dict, sensors: dict) -> list:
        alerts = []
        measurements = batch.get("measurements", {})
        for sensor_key, limits in sensors.items():
            if not limits.get("enabled", True):
                continue
            measurement = measurements.get(sensor_key)
            if measurement is None:
                continue
            value = measurement.get("value")
            validity = measurement.get("validity")
            validity_reason = measurement.get("validity_reason")

            if validity == "invalid":
                alerts.append(
                    self._make_alert(
                        sensor=sensor_key,
                        rule="invalid",
                        severity="critical",
                        message=f"{sensor_key}: invalid ({validity_reason or 'unknown'})",
                    )
                )
                continue

            if validity == "stale":
                alerts.append(
                    self._make_alert(
                        sensor=sensor_key,
                        rule="stale",
                        severity="warning",
                        message=f"{sensor_key}: stale",
                        value=value,
                    )
                )
                continue

            if value is None:
                continue

            for rule, threshold, severity in (
                ("critical_min", limits.get("critical_min"), "critical"),
                ("critical_max", limits.get("critical_max"), "critical"),
                ("warning_min", limits.get("warning_min"), "warning"),
                ("warning_max", limits.get("warning_max"), "warning"),
            ):
                if threshold is None:
                    continue
                if rule.endswith("_min") and value < threshold:
                    alerts.append(
                        self._make_alert(
                            sensor=sensor_key,
                            rule=rule,
                            severity=severity,
                            message=f"{sensor_key}: {value} < {threshold}",
                            value=value,
                            threshold=threshold,
                        )
                    )
                elif rule.endswith("_max") and value > threshold:
                    alerts.append(
                        self._make_alert(
                            sensor=sensor_key,
                            rule=rule,
                            severity=severity,
                            message=f"{sensor_key}: {value} > {threshold}",
                            value=value,
                            threshold=threshold,
                        )
                    )

        return alerts

    def _check_states(self, batch: dict, states: dict) -> list:
        alerts = []
        batch_states = batch.get("states", {})
        for state_key, rule in states.items():
            if not rule.get("enabled", True):
                continue
            device_key, _, state_name = state_key.partition(".")
            device_states = batch_states.get(device_key, {})
            value = device_states.get(state_name)

            if state_name == "alarms" and isinstance(value, list):
                for alarm in value:
                    alerts.append(
                        self._make_alert(
                            sensor=state_key,
                            rule="alarm",
                            severity="critical",
                            message=f"{device_key}: alarm {alarm}",
                        )
                    )
            elif state_name == "battery_low" and value is True:
                alerts.append(
                    self._make_alert(
                        sensor=state_key,
                        rule="battery_low",
                        severity="warning",
                        message=f"{device_key}: battery low",
                    )
                )
            elif state_name == "door_open" and value is True:
                alerts.append(
                    self._make_alert(
                        sensor=state_key,
                        rule="door_open",
                        severity="warning",
                        message=f"{device_key}: door open",
                    )
                )

        return alerts

    def _make_alert(
        self,
        *,
        sensor: str,
        rule: str,
        severity: str,
        message: str,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Alert:
        return Alert(
            sensor=sensor,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold,
            rule=rule,
            dedup_key=f"{sensor}:{rule}:{severity}",
        )

    def _dispatch(self, alert: Alert, mail: dict, notifiers: list) -> None:
        dedup_seconds = mail.get("dedup_seconds", 3600)
        since = (datetime.now(timezone.utc) - timedelta(seconds=dedup_seconds)).isoformat()
        if self._alert_store.recent_dedup_keys(alert.dedup_key, since):
            return

        self._alert_store.store(alert)

        if self._in_quiet_hours(mail, alert.severity):
            return

        for notifier in notifiers:
            try:
                notifier.send(alert)
            except Exception:
                LOGGER.exception("Notifier failed")

    def _in_quiet_hours(self, mail: dict, severity: str) -> bool:
        qh = mail.get("quiet_hours")
        if not qh:
            return False
        if severity == "critical" and qh.get("critical_always", True):
            return False
        now = datetime.now().time()
        start = datetime.strptime(qh["start"], "%H:%M").time()
        end = datetime.strptime(qh["end"], "%H:%M").time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end
