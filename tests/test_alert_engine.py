"""Tests für die AlertEngine."""

import sqlite3
from datetime import datetime, timedelta, timezone

from alert_engine import AlertEngine
from alert_store import AlertStore
from batch_factory import SequenceStore, create_batch
from config_store import _DEFAULT_MESSAGES
from model.measurement import Measurement
from otterpi_store import BatchStore


def _engine(tmp_path):
    return AlertEngine(
        store=BatchStore(tmp_path / "otter.db"),
        alert_store=AlertStore(tmp_path / "alerts.db"),
        smtp_password=None,
        interval_seconds=300,
    )


def test_engine_is_daemon_thread(tmp_path):
    engine = _engine(tmp_path)
    assert engine.daemon is True
    assert engine.name == "AlertEngine"


def test_engine_stop_sets_events(tmp_path):
    engine = _engine(tmp_path)
    engine.stop()
    assert engine._stop.is_set() is True
    assert engine._wake.is_set() is True


def _measurement(value, validity="valid", validity_reason=None):
    return Measurement(
        value=value,
        unit="celsius",
        measured_at=datetime.now(timezone.utc).isoformat(),
        validity=validity,
        source="test",
        validity_reason=validity_reason,
    )


def _store_batch(store, measurements=None, states=None):
    seq = SequenceStore(store.path.parent / "sequence")
    batch = create_batch(
        "logger-001",
        seq,
        measurements=measurements or {},
        states=states,
    )
    store.store(batch)
    return batch


class TestCheckSensors:
    def test_critical_max(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        sensors = {"atmoweb_101.temperature_1": {"critical_max": 28.0, "enabled": True}}
        alerts = engine._check_sensors(engine._store.latest().to_dict(), sensors)
        assert len(alerts) == 1
        assert alerts[0].rule == "critical_max"
        assert alerts[0].severity == "critical"

    def test_warning_min(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(19.0)},
        )
        sensors = {"atmoweb_101.temperature_1": {"warning_min": 20.0, "enabled": True}}
        alerts = engine._check_sensors(engine._store.latest().to_dict(), sensors)
        assert len(alerts) == 1
        assert alerts[0].rule == "warning_min"
        assert alerts[0].severity == "warning"

    def test_invalid(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={
                "atmoweb_101.temperature_1": _measurement(
                    None, validity="invalid", validity_reason="overflow"
                )
            },
        )
        sensors = {"atmoweb_101.temperature_1": {"enabled": True}}
        alerts = engine._check_sensors(engine._store.latest().to_dict(), sensors)
        assert len(alerts) == 1
        assert alerts[0].rule == "invalid"
        assert "overflow" in alerts[0].message

    def test_stale(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(23.0, validity="stale")},
        )
        sensors = {"atmoweb_101.temperature_1": {"enabled": True}}
        alerts = engine._check_sensors(engine._store.latest().to_dict(), sensors)
        assert len(alerts) == 1
        assert alerts[0].rule == "stale"


class TestCheckStates:
    def test_alarm(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            states={"freezer": {"alarms": ["ac_power_failure"]}},
        )
        states = {"freezer.alarms": {"enabled": True}}
        alerts = engine._check_states(engine._store.latest().to_dict(), states)
        assert len(alerts) == 1
        assert alerts[0].rule == "alarm"
        assert "ac_power_failure" in alerts[0].message

    def test_battery_low(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            states={"weatherhub_015f9410f3eb": {"battery_low": True}},
        )
        states = {"weatherhub_015f9410f3eb.battery_low": {"enabled": True}}
        alerts = engine._check_states(engine._store.latest().to_dict(), states)
        assert len(alerts) == 1
        assert alerts[0].rule == "battery_low"

    def test_door_open(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            states={"atmoweb_101": {"door_open": True}},
        )
        states = {"atmoweb_101.door_open": {"enabled": True}}
        alerts = engine._check_states(engine._store.latest().to_dict(), states)
        assert len(alerts) == 1
        assert alerts[0].rule == "door_open"


class TestQuietHours:
    def test_critical_always(self, tmp_path):
        engine = _engine(tmp_path)
        mail = {"quiet_hours": {"start": "00:00", "end": "23:59", "critical_always": True}}
        assert engine._in_quiet_hours(mail, "critical") is False

    def test_warning_in_quiet_hours(self, tmp_path):
        engine = _engine(tmp_path)
        mail = {"quiet_hours": {"start": "00:00", "end": "23:59", "critical_always": True}}
        assert engine._in_quiet_hours(mail, "warning") is True

    def test_no_quiet_hours(self, tmp_path):
        engine = _engine(tmp_path)
        assert engine._in_quiet_hours({}, "warning") is False

    def test_contact_open(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            states={"weatherhub_010203040506": {"contact_open": True}},
        )
        states = {"weatherhub_010203040506.contact_open": {"enabled": True}}
        alerts = engine._check_states(engine._store.latest().to_dict(), states)
        assert len(alerts) == 1
        assert alerts[0].rule == "contact_open"

    def test_rate_of_change(self, tmp_path):
        engine = _engine(tmp_path)
        seq = SequenceStore(engine._store.path.parent / "sequence")
        now = datetime.now(timezone.utc)
        for i, value in enumerate([20.0, 25.0]):
            batch = create_batch(
                "logger-001",
                seq,
                measurements={"atmoweb_101.temperature_1": _measurement(value)},
            )
            batch = batch.__class__(
                batch_id=batch.batch_id,
                logger_id=batch.logger_id,
                sequence=batch.sequence,
                created_at=(now - timedelta(minutes=30 * (1 - i))).isoformat(),
                measurements=batch.measurements,
            )
            engine._store.store(batch)
        sensors = {
            "atmoweb_101.temperature_1": {
                "rate_of_change_max_per_hour": 2.0,
                "enabled": True,
            }
        }
        alerts = engine._check_sensors(engine._store.latest().to_dict(), sensors)
        assert any(a.rule == "rate_of_change" for a in alerts)


class TestLoggerPiHeartbeat:
    def test_no_batch_returns_not_offline(self, tmp_path):
        engine = _engine(tmp_path)
        alert, is_offline = engine._check_loggerpi_heartbeat({})
        assert alert is None
        assert is_offline is False

    def test_fresh_batch_returns_not_offline(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        alert, is_offline = engine._check_loggerpi_heartbeat({})
        assert alert is None
        assert is_offline is False

    def test_warning_threshold_without_alert(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))
        alert, is_offline = engine._check_loggerpi_heartbeat({})
        assert alert is None
        assert is_offline is True

    def test_warning_threshold_with_alert(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))
        alert, is_offline = engine._check_loggerpi_heartbeat(
            {"loggerpi_offline_warning_alert_enabled": True}
        )
        assert alert is not None
        assert alert.severity == "warning"
        assert alert.rule == "loggerpi_offline"
        assert is_offline is True

    def test_critical_threshold(self, tmp_path):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))
        alert, is_offline = engine._check_loggerpi_heartbeat({})
        assert alert is not None
        assert alert.severity == "critical"
        assert alert.rule == "loggerpi_offline"
        assert is_offline is True


class TestCheckSuppression:
    def _mock_config(self, monkeypatch, sensors=None, states=None, system=None):
        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {
                "system": system or {},
                "sensors": sensors or {},
                "states": states or {},
            },
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})

    def test_offline_suppresses_sensor_alerts(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))

        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        assert alerts[0]["rule"] == "loggerpi_offline"
        assert alerts[0]["severity"] == "critical"

    def test_online_runs_sensor_alerts(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )

        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        assert alerts[0]["rule"] == "critical_max"


class TestAcknowledgeSuppression:
    def test_acknowledged_alert_not_redispatched(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {
                "system": {},
                "sensors": {
                    "atmoweb_101.temperature_1": {
                        "critical_max": 28.0,
                        "enabled": True,
                    }
                },
                "states": {},
            },
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})

        engine._check()
        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        alert_id = alerts[0]["id"]
        engine._alert_store.acknowledge(alert_id, "makki")

        # Zweiter Check: acknowledged → kein neuer Alert
        engine._check()
        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1

    def test_reset_on_valid(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {
                "system": {},
                "sensors": {
                    "atmoweb_101.temperature_1": {
                        "critical_max": 28.0,
                        "enabled": True,
                    }
                },
                "states": {},
            },
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})

        engine._check()
        alerts = engine._alert_store.list_alerts()
        alert_id = alerts[0]["id"]
        engine._alert_store.acknowledge(alert_id, "makki")

        # Neuer Batch mit normalem Wert → reset
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(23.0)},
        )
        engine._check()

        assert (
            engine._alert_store.is_acknowledged("atmoweb_101.temperature_1:critical_max:critical")
            is False
        )


class TestResolve:
    def _mock_config(self, monkeypatch, sensors=None, states=None):
        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {
                "system": {},
                "sensors": sensors or {},
                "states": states or {},
            },
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})

    def test_resolve_on_normal_value(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()
        assert (
            engine._alert_store.is_active("atmoweb_101.temperature_1:critical_max:critical") is True
        )

        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(23.0)},
        )
        engine._check()

        assert (
            engine._alert_store.is_active("atmoweb_101.temperature_1:critical_max:critical")
            is False
        )

    def test_no_resolve_when_still_critical(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()
        alerts = engine._alert_store.list_alerts()
        alert_id = alerts[0]["id"]
        engine._alert_store.acknowledge(alert_id, "makki")

        # Immer noch kritisch (29.0 > 28.0) → kein Reset, kein Resolve
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(29.0)},
        )
        engine._check()

        assert (
            engine._alert_store.is_acknowledged("atmoweb_101.temperature_1:critical_max:critical")
            is True
        )
        assert (
            engine._alert_store.is_active("atmoweb_101.temperature_1:critical_max:critical") is True
        )

    def test_resolve_on_battery_low_false(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            states={"weatherhub_015f9410f3eb": {"battery_low": True}},
        )
        self._mock_config(
            monkeypatch,
            states={"weatherhub_015f9410f3eb.battery_low": {"enabled": True}},
        )

        engine._check()
        assert (
            engine._alert_store.is_active("weatherhub_015f9410f3eb.battery_low:battery_low:warning")
            is True
        )

        _store_batch(
            engine._store,
            states={"weatherhub_015f9410f3eb": {"battery_low": False}},
        )
        engine._check()

        assert (
            engine._alert_store.is_active("weatherhub_015f9410f3eb.battery_low:battery_low:warning")
            is False
        )


class TestOfflineResolve:
    def test_offline_alert_resolved_when_online(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))

        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {"system": {}, "sensors": {}, "states": {}},
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})

        engine._check()
        assert engine._alert_store.is_active("system:loggerpi_offline:critical") is True

        # Neuer Batch → LoggerPi wieder online
        _store_batch(engine._store)
        engine._check()

        assert engine._alert_store.is_active("system:loggerpi_offline:critical") is False


class TestMessageAndSubject:
    def _mock_config(self, monkeypatch, sensors=None, states=None, messages=None):
        monkeypatch.setattr(
            "alert_engine.load_alarm_limits",
            lambda: {
                "system": {},
                "sensors": sensors or {},
                "states": states or {},
            },
        )
        monkeypatch.setattr("alert_engine.load_mail", lambda: {})
        monkeypatch.setattr("alert_engine.load_notifications", lambda: {"channels": []})
        monkeypatch.setattr(
            "alert_engine.load_messages",
            lambda: messages if messages is not None else dict(_DEFAULT_MESSAGES),
        )

    def test_message_includes_room_and_device(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        message = alerts[0]["message"]
        assert "R1304" in message
        assert "Memmert HPP260" in message
        assert "Temperature" in message
        assert "too high" in message
        assert "30.0" in message
        assert "28.0" in message

    def test_subject_includes_measurement_and_room(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        # Subject wird nicht in der DB gespeichert, aber im Alert-Objekt
        # Wir prüfen es über _build_subject direkt
        subject = engine._build_subject(
            "atmoweb_101.temperature_1",
            "critical_max",
            "critical",
            {"atmoweb_101": ("R1304 · Culture Room I", "Memmert HPP260 · left")},
        )
        assert subject == (
            "[CRITICAL] Temperature — R1304 · Culture Room I / Memmert HPP260 · left"
        )

    def test_message_uses_custom_rule_text(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"atmoweb_101.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "atmoweb_101.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
            messages={"critical_max": "way too hot"},
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert "way too hot" in alerts[0]["message"]

    def test_message_falls_back_to_technical_key(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(
            engine._store,
            measurements={"unknown_sensor.temperature_1": _measurement(30.0)},
        )
        self._mock_config(
            monkeypatch,
            sensors={
                "unknown_sensor.temperature_1": {
                    "critical_max": 28.0,
                    "enabled": True,
                }
            },
        )

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        assert "unknown_sensor" in alerts[0]["message"]

    def test_offline_message_and_subject(self, tmp_path, monkeypatch):
        engine = _engine(tmp_path)
        _store_batch(engine._store)
        with sqlite3.connect(engine._store.path) as conn:
            old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
            conn.execute("UPDATE batches SET received_at = ?", (old,))

        self._mock_config(monkeypatch)

        engine._check()

        alerts = engine._alert_store.list_alerts()
        assert len(alerts) == 1
        assert "LoggerPi offline" in alerts[0]["message"]
        assert "61" in alerts[0]["message"] or "60" in alerts[0]["message"]
