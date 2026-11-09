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
    load_messages,
    load_notifications,
)
from dashboard_config import get_rooms
from notifier import Alert, create_notifiers
from otterpi_store import BatchStore
from sensor_schemas import MEASUREMENT_DISPLAY_NAMES

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
        try:
            messages = load_messages()
        except ConfigValidationError:
            messages = {}

        notifiers = create_notifiers(notifications, mail, self._smtp_password)

        # Sensor-Map: sensor_key -> (room_name, device_name)
        sensor_map = {}
        for room in get_rooms().values():
            for device in room["devices"]:
                sensor_map[device["key"]] = (room["name"], device["name"])

        # Heartbeat zuerst prüfen (auch wenn noch kein Batch empfangen wurde)
        system_config = alarm_limits.get("system", {})
        offline_alert, is_offline = self._check_loggerpi_heartbeat(system_config, messages)
        if is_offline:
            if offline_alert is not None:
                self._dispatch(offline_alert, mail, notifiers)
            # Sensor-/State-Checks aussetzen, solange der LoggerPi offline ist
            return

        # LoggerPi ist wieder online → Offline-Alerts resolven
        for severity in ("critical", "warning"):
            dedup_key = f"system:loggerpi_offline:{severity}"
            self._alert_store.resolve(dedup_key)

        batch = self._store.latest()
        if batch is None:
            return

        batch_dict = batch.to_dict()
        self._pending_alerts = self._check_sensors(
            batch_dict,
            alarm_limits.get("sensors", {}),
            messages,
            sensor_map,
            alarm_limits.get("device", {}),
        )
        self._pending_alerts.extend(
            self._check_states(batch_dict, alarm_limits.get("states", {}), messages, sensor_map)
        )

        for alert in self._pending_alerts:
            self._dispatch(alert, mail, notifiers)

    def _sensor_display(self, sensor_key: str, sensor_map: dict) -> tuple[str, str]:
        """Liefert (room_name, device_name) für einen sensor_key."""
        device_key = sensor_key.split(".")[0]
        return sensor_map.get(device_key, ("", device_key))

    def _measurement_name(self, sensor_key: str) -> str:
        """Liefert den Anzeigenamen des Measurements."""
        parts = sensor_key.split(".", 1)
        measurement = parts[1] if len(parts) == 2 else parts[0]
        return MEASUREMENT_DISPLAY_NAMES.get(measurement, measurement)

    def _build_message(
        self,
        sensor_key: str,
        rule: str,
        messages: dict,
        sensor_map: dict,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
        unit: str = "",
        validity_reason: Optional[str] = None,
    ) -> str:
        room, device = self._sensor_display(sensor_key, sensor_map)
        measurement = self._measurement_name(sensor_key)
        rule_text = messages.get(rule, rule)
        prefix = f"{room} / {device}" if room else device

        if rule == "invalid":
            reason = f" ({validity_reason})" if validity_reason else ""
            measurement_key = sensor_key.split(".", 1)[-1]
            return f"{prefix} — {measurement} ({measurement_key}) {rule_text}{reason}"
        if rule == "stale":
            measurement_key = sensor_key.split(".", 1)[-1]
            return f"{prefix} — {measurement} ({measurement_key}) {rule_text}"
        if value is not None and threshold is not None:
            operator = ">" if rule.endswith("_max") else "<"
            return (
                f"{prefix} — {measurement} {rule_text}: "
                f"{value} {unit} {operator} {threshold} {unit}"
            )
        return f"{prefix} — {measurement} {rule_text}"

    def _build_subject(self, sensor_key: str, rule: str, severity: str, sensor_map: dict) -> str:
        room, device = self._sensor_display(sensor_key, sensor_map)
        measurement = self._measurement_name(sensor_key)
        prefix = f"{room} / {device}" if room else device
        return f"[{severity.upper()}] {measurement} — {prefix}"

    def _check_loggerpi_heartbeat(
        self, system_config: dict, messages: Optional[dict] = None
    ) -> tuple[Optional[Alert], bool]:
        """Prüft den LoggerPi-Heartbeat.

        Liefert ``(alert, is_offline)``:

        - ``is_offline`` ist True, sobald die Warnschwelle erreicht ist.
          Dann werden Sensor-/State-Checks ausgesetzt.
        - ``alert`` ist nur dann gesetzt, wenn tatsächlich ein Alert
          versendet werden soll (Warnstufe optional, Kritischstufe immer).
        """
        messages = messages or {}
        warning_seconds = system_config.get("loggerpi_offline_warning_seconds", 1800)
        critical_seconds = system_config.get("loggerpi_offline_critical_seconds", 3600)
        warning_alert_enabled = system_config.get("loggerpi_offline_warning_alert_enabled", False)

        rule_text = messages.get("loggerpi_offline", "offline")
        measurement_name = MEASUREMENT_DISPLAY_NAMES.get("loggerpi_offline", "LoggerPi")

        last_received_at = self._store.latest_received_at()
        if last_received_at is None:
            return (None, False)

        try:
            last_dt = datetime.fromisoformat(last_received_at)
        except ValueError:
            return (None, False)

        age_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()
        minutes = int(age_seconds // 60)

        if age_seconds >= critical_seconds:
            return (
                Alert(
                    sensor="system.loggerpi",
                    severity="critical",
                    message=f"LoggerPi {rule_text} for {minutes} minutes.",
                    rule="loggerpi_offline",
                    dedup_key="system:loggerpi_offline:critical",
                    subject=f"[CRITICAL] {measurement_name}",
                ),
                True,
            )

        if age_seconds >= warning_seconds:
            if warning_alert_enabled:
                return (
                    Alert(
                        sensor="system.loggerpi",
                        severity="warning",
                        message=f"LoggerPi {rule_text} for {minutes} minutes.",
                        rule="loggerpi_offline",
                        dedup_key="system:loggerpi_offline:warning",
                        subject=f"[WARNING] {measurement_name}",
                    ),
                    True,
                )
            return (None, True)

        return (None, False)

    def _check_sensors(
        self,
        batch: dict,
        sensors: dict,
        messages: Optional[dict] = None,
        sensor_map: Optional[dict] = None,
        device_config: Optional[dict] = None,
    ) -> list:
        messages = messages or {}
        sensor_map = sensor_map or {}
        device_config = device_config or {}
        alerts = []
        measurements = batch.get("measurements", {})
        recent_batches = self._store.recent(hours=1)

        # Pro Gerät: stale/invalid prüfen (ein Alert pro Gerät)
        device_states = {}
        for sensor_key, limits in sensors.items():
            if not limits.get("enabled", True):
                continue
            measurement = measurements.get(sensor_key)
            if measurement is None:
                continue
            validity = measurement.get("validity")
            validity_reason = measurement.get("validity_reason")
            device_key = sensor_key.split(".")[0]
            if device_key not in device_states:
                device_states[device_key] = {
                    "stale": False,
                    "invalid": False,
                    "reason": None,
                }
            if validity == "invalid":
                device_states[device_key]["invalid"] = True
                device_states[device_key]["reason"] = validity_reason
            elif validity == "stale":
                device_states[device_key]["stale"] = True

        for device_key, state in device_states.items():
            device_rule = device_config.get(device_key, {})
            if state["invalid"] and device_rule.get("invalid_enabled", True):
                alerts.append(
                    self._make_alert(
                        sensor=device_key,
                        rule="invalid",
                        severity="critical",
                        message=self._build_message(
                            device_key,
                            "invalid",
                            messages,
                            sensor_map,
                            validity_reason=state["reason"],
                        ),
                        subject=self._build_subject(device_key, "invalid", "critical", sensor_map),
                    )
                )
            elif state["stale"] and device_rule.get("stale_enabled", True):
                alerts.append(
                    self._make_alert(
                        sensor=device_key,
                        rule="stale",
                        severity="warning",
                        message=self._build_message(device_key, "stale", messages, sensor_map),
                        subject=self._build_subject(device_key, "stale", "warning", sensor_map),
                    )
                )

        # Pro Measurement: Grenzwerte und rate_of_change
        for sensor_key, limits in sensors.items():
            if not limits.get("enabled", True):
                continue
            measurement = measurements.get(sensor_key)
            if measurement is None:
                continue
            value = measurement.get("value")
            validity = measurement.get("validity")

            if validity in ("invalid", "stale"):
                continue

            if value is None:
                continue

            # Sensor ist wieder valid → stale/invalid-Alerts resolven
            device_key = sensor_key.split(".")[0]
            self._alert_store.resolve(f"{device_key}:stale:warning")
            self._alert_store.resolve(f"{device_key}:invalid:critical")

            for rule, threshold, severity in (
                ("critical_min", limits.get("critical_min"), "critical"),
                ("critical_max", limits.get("critical_max"), "critical"),
                ("warning_min", limits.get("warning_min"), "warning"),
                ("warning_max", limits.get("warning_max"), "warning"),
            ):
                if threshold is None:
                    continue
                dedup_key = f"{sensor_key}:{rule}:{severity}"
                if rule.endswith("_min") and value < threshold:
                    alerts.append(
                        self._make_alert(
                            sensor=sensor_key,
                            rule=rule,
                            severity=severity,
                            message=self._build_message(
                                sensor_key,
                                rule,
                                messages,
                                sensor_map,
                                value=value,
                                threshold=threshold,
                                unit=measurement.get("unit", ""),
                            ),
                            value=value,
                            threshold=threshold,
                            subject=self._build_subject(sensor_key, rule, severity, sensor_map),
                        )
                    )
                elif rule.endswith("_max") and value > threshold:
                    alerts.append(
                        self._make_alert(
                            sensor=sensor_key,
                            rule=rule,
                            severity=severity,
                            message=self._build_message(
                                sensor_key,
                                rule,
                                messages,
                                sensor_map,
                                value=value,
                                threshold=threshold,
                                unit=measurement.get("unit", ""),
                            ),
                            value=value,
                            threshold=threshold,
                            subject=self._build_subject(sensor_key, rule, severity, sensor_map),
                        )
                    )
                else:
                    self._alert_store.resolve(dedup_key)

            rate_limit = limits.get("rate_of_change_max_per_hour")
            if rate_limit is not None and value is not None:
                rate = self._calculate_rate_of_change(sensor_key, recent_batches)
                if rate is not None and abs(rate) > rate_limit:
                    alerts.append(
                        self._make_alert(
                            sensor=sensor_key,
                            rule="rate_of_change",
                            severity="warning",
                            message=self._build_message(
                                sensor_key,
                                "rate_of_change",
                                messages,
                                sensor_map,
                                value=rate,
                                threshold=rate_limit,
                                unit="/h",
                            ),
                            value=rate,
                            threshold=rate_limit,
                            subject=self._build_subject(
                                sensor_key, "rate_of_change", "warning", sensor_map
                            ),
                        )
                    )

        return alerts

    def _calculate_rate_of_change(self, sensor_key: str, recent_batches: list) -> Optional[float]:
        values = []
        for batch in recent_batches:
            measurement = batch.measurements.get(sensor_key)
            if measurement is not None and measurement.value is not None:
                values.append((batch.created_at, measurement.value))
        if len(values) < 2:
            return None
        first_time, first_value = values[0]
        last_time, last_value = values[-1]
        dt = datetime.fromisoformat(last_time) - datetime.fromisoformat(first_time)
        hours = dt.total_seconds() / 3600
        if hours <= 0:
            return None
        return (last_value - first_value) / hours

    def _check_states(
        self,
        batch: dict,
        states: dict,
        messages: Optional[dict] = None,
        sensor_map: Optional[dict] = None,
    ) -> list:
        messages = messages or {}
        sensor_map = sensor_map or {}
        alerts = []
        batch_states = batch.get("states", {})
        for state_key, rule in states.items():
            if not rule.get("enabled", True):
                continue
            device_key, _, state_name = state_key.partition(".")
            device_states = batch_states.get(device_key, {})
            value = device_states.get(state_name)

            # State ist wieder normal → Alert resolven
            if state_name == "alarms" and isinstance(value, list) and not value:
                self._alert_store.resolve(f"{state_key}:alarm:critical")
            elif state_name == "battery_low" and value is False:
                self._alert_store.resolve(f"{state_key}:battery_low:warning")
            elif state_name == "door_open" and value is False:
                self._alert_store.resolve(f"{state_key}:door_open:warning")
            elif state_name == "contact_open" and value is False:
                self._alert_store.resolve(f"{state_key}:contact_open:warning")

            if state_name == "alarms" and isinstance(value, list):
                for alarm in value:
                    alerts.append(
                        self._make_alert(
                            sensor=state_key,
                            rule="alarm",
                            severity="critical",
                            message=self._build_message(state_key, "alarm", messages, sensor_map)
                            + f": {alarm}",
                            subject=self._build_subject(state_key, "alarm", "critical", sensor_map),
                        )
                    )
            elif state_name == "battery_low" and value is True:
                alerts.append(
                    self._make_alert(
                        sensor=state_key,
                        rule="battery_low",
                        severity="warning",
                        message=self._build_message(state_key, "battery_low", messages, sensor_map),
                        subject=self._build_subject(
                            state_key, "battery_low", "warning", sensor_map
                        ),
                    )
                )
            elif state_name == "door_open" and value is True:
                alerts.append(
                    self._make_alert(
                        sensor=state_key,
                        rule="door_open",
                        severity="warning",
                        message=self._build_message(state_key, "door_open", messages, sensor_map),
                        subject=self._build_subject(state_key, "door_open", "warning", sensor_map),
                    )
                )
            elif state_name == "contact_open" and value is True:
                alerts.append(
                    self._make_alert(
                        sensor=state_key,
                        rule="contact_open",
                        severity="warning",
                        message=self._build_message(
                            state_key, "contact_open", messages, sensor_map
                        ),
                        subject=self._build_subject(
                            state_key, "contact_open", "warning", sensor_map
                        ),
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
        subject: Optional[str] = None,
    ) -> Alert:
        return Alert(
            sensor=sensor,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold,
            rule=rule,
            dedup_key=f"{sensor}:{rule}:{severity}",
            subject=subject,
        )

    def _dispatch(self, alert: Alert, mail: dict, notifiers: list) -> None:
        dedup_seconds = mail.get("dedup_seconds", 3600)
        since = (datetime.now(timezone.utc) - timedelta(seconds=dedup_seconds)).isoformat()
        if self._alert_store.recent_dedup_keys(alert.dedup_key, since):
            return
        if self._alert_store.is_acknowledged(alert.dedup_key):
            return

        self._alert_store.store(alert)

        if self._in_quiet_hours(mail, alert.severity):
            return

        for notifier in notifiers:
            try:
                if not notifier.send(alert):
                    LOGGER.warning(
                        "Notifier %s returned False for %s",
                        type(notifier).__name__,
                        alert.dedup_key,
                    )
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
