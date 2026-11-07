"""Tests für die AlertEngine."""

from datetime import datetime, timedelta, timezone

from alert_engine import AlertEngine
from alert_store import AlertStore
from batch_factory import SequenceStore, create_batch
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
