"""Tests für den AlertStore."""

from datetime import datetime, timedelta, timezone

import pytest
from alert_store import AlertStore
from notifier import Alert


def _alert(
    sensor="freezer.temperature",
    rule="critical_min",
    severity="critical",
    message="Freezer too warm",
    value=-65.0,
    threshold=-70.0,
    dedup_key="freezer.temperature:critical_min:critical",
):
    return Alert(
        sensor=sensor,
        severity=severity,
        message=message,
        value=value,
        threshold=threshold,
        rule=rule,
        dedup_key=dedup_key,
    )


class TestStore:
    def test_store_returns_id(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.store(_alert()) == 1

    def test_store_requires_rule_and_dedup_key(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert = Alert(sensor="x", severity="critical", message="m")
        with pytest.raises(ValueError):
            store.store(alert)

    def test_store_persists(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        alerts = store.list_alerts()
        assert len(alerts) == 1
        assert alerts[0]["sensor"] == "freezer.temperature"
        assert alerts[0]["rule"] == "critical_min"
        assert alerts[0]["severity"] == "critical"


class TestRecentDedupKeys:
    def test_recent_dedup_key_found(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert store.recent_dedup_keys("freezer.temperature:critical_min:critical", since) is True

    def test_recent_dedup_key_not_found(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert store.recent_dedup_keys("unknown", since) is False

    def test_recent_dedup_key_outside_window(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        since = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        assert store.recent_dedup_keys("freezer.temperature:critical_min:critical", since) is False


class TestListAlerts:
    def test_list_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.list_alerts() == []

    def test_list_limit(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        for i in range(5):
            store.store(_alert(dedup_key=f"key-{i}"))
        assert len(store.list_alerts(limit=3)) == 3

    def test_list_only_unacknowledged(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        id1 = store.store(_alert(dedup_key="key-1"))
        store.store(_alert(dedup_key="key-2"))
        store.acknowledge(id1, "makki")
        unack = store.list_alerts(only_unacknowledged=True)
        assert len(unack) == 1
        assert unack[0]["dedup_key"] == "key-2"


class TestAcknowledge:
    def test_acknowledge_success(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        assert store.acknowledge(alert_id, "makki") is True
        alerts = store.list_alerts()
        assert alerts[0]["acknowledged"] == 1
        assert alerts[0]["acknowledged_by"] == "makki"

    def test_acknowledge_twice_returns_false(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        assert store.acknowledge(alert_id, "makki") is True
        assert store.acknowledge(alert_id, "makki") is False

    def test_acknowledge_unknown_returns_false(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.acknowledge(999, "makki") is False


class TestIsAcknowledged:
    def test_not_acknowledged(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        assert store.is_acknowledged("freezer.temperature:critical_min:critical") is False

    def test_acknowledged(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        store.acknowledge(alert_id, "makki")
        assert store.is_acknowledged("freezer.temperature:critical_min:critical") is True

    def test_unknown_key(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.is_acknowledged("unknown") is False


class TestResetAcknowledged:
    def test_reset(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        store.acknowledge(alert_id, "makki")
        assert store.is_acknowledged("freezer.temperature:critical_min:critical") is True
        store.reset_acknowledged("freezer.temperature:critical_min:critical")
        assert store.is_acknowledged("freezer.temperature:critical_min:critical") is False

    def test_reset_unknown_key(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.reset_acknowledged("unknown")


class TestResolve:
    def test_resolve_sets_resolved_at(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        assert store.is_active("freezer.temperature:critical_min:critical") is True
        store.resolve("freezer.temperature:critical_min:critical")
        assert store.is_active("freezer.temperature:critical_min:critical") is False

    def test_resolve_all_open_alerts(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert())
        store.store(_alert())
        store.store(_alert())
        store.resolve("freezer.temperature:critical_min:critical")
        alerts = store.list_alerts()
        assert all(a["resolved_at"] is not None for a in alerts)

    def test_resolve_unknown_key(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.resolve("unknown")

    def test_is_active_unknown_key(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.is_active("unknown") is False


class TestListAlertsOnlyActive:
    def test_only_active(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert(dedup_key="key-1"))
        store.store(_alert(dedup_key="key-2"))
        store.resolve("key-1")
        active = store.list_alerts(only_active=True)
        assert len(active) == 1
        assert active[0]["dedup_key"] == "key-2"

    def test_only_active_and_unacknowledged(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        id1 = store.store(_alert(dedup_key="key-1"))
        store.store(_alert(dedup_key="key-2"))
        store.acknowledge(id1, "makki")
        active = store.list_alerts(only_active=True, only_unacknowledged=True)
        assert len(active) == 1
        assert active[0]["dedup_key"] == "key-2"

    def test_only_active_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert(dedup_key="key-1"))
        store.resolve("key-1")
        assert store.list_alerts(only_active=True) == []


class TestResolveById:
    def test_resolve_by_id(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        assert store.is_active("freezer.temperature:critical_min:critical") is True
        assert store.resolve_by_id(alert_id) is True
        assert store.is_active("freezer.temperature:critical_min:critical") is False

    def test_resolve_by_id_twice_returns_false(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        alert_id = store.store(_alert())
        assert store.resolve_by_id(alert_id) is True
        assert store.resolve_by_id(alert_id) is False

    def test_resolve_by_id_unknown_returns_false(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.resolve_by_id(999) is False


class TestCountByDay:
    def test_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.count_by_day() == []

    def test_counts(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert(severity="warning"))
        store.store(_alert(severity="critical"))
        result = store.count_by_day()
        assert len(result) == 1
        assert result[0]["warning"] == 1
        assert result[0]["critical"] == 1
        assert result[0]["resolved"] == 0


class TestCountByStatus:
    def test_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.count_by_status() == {
            "active_critical": 0,
            "active_warning": 0,
            "resolved": 0,
        }

    def test_counts(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        store.store(_alert(severity="warning"))
        store.store(_alert(severity="critical"))
        result = store.count_by_status()
        assert result["active_warning"] == 1
        assert result["active_critical"] == 1
        assert result["resolved"] == 0


class TestBuildWhere:
    def test_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where()
        assert where == ""
        assert params == []

    def test_only_unacknowledged(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(only_unacknowledged=True)
        assert where == " WHERE acknowledged = 0"
        assert params == []

    def test_status_active(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(status="active")
        assert where == " WHERE resolved_at IS NULL"
        assert params == []

    def test_status_resolved(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(status="resolved")
        assert where == " WHERE resolved_at IS NOT NULL"
        assert params == []

    def test_only_active_alias(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(only_active=True)
        assert where == " WHERE resolved_at IS NULL"
        assert params == []

    def test_severity(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(severity="critical")
        assert where == " WHERE severity = ?"
        assert params == ["critical"]

    def test_since_date_only(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(since="2026-11-01")
        assert where == " WHERE created_at >= ?"
        assert params == ["2026-11-01T00:00:00"]

    def test_since_full_timestamp(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(since="2026-11-01T12:00:00")
        assert where == " WHERE created_at >= ?"
        assert params == ["2026-11-01T12:00:00"]

    def test_until_date_only(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(until="2026-11-30")
        assert where == " WHERE created_at < ?"
        assert params == ["2026-12-01T00:00:00"]

    def test_until_full_timestamp(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(until="2026-11-30T23:59:59")
        assert where == " WHERE created_at <= ?"
        assert params == ["2026-11-30T23:59:59"]

    def test_device_prefixes_single(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(device_prefixes=["atmoweb_101"])
        assert where == " WHERE ((sensor = ? OR sensor LIKE ?))"
        assert params == ["atmoweb_101", "atmoweb_101.%"]

    def test_device_prefixes_multiple(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(device_prefixes=["atmoweb_101", "atmoweb_102"])
        assert where == (" WHERE ((sensor = ? OR sensor LIKE ?) OR (sensor = ? OR sensor LIKE ?))")
        assert params == [
            "atmoweb_101",
            "atmoweb_101.%",
            "atmoweb_102",
            "atmoweb_102.%",
        ]

    def test_include_older_active(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(include_older_active=True)
        assert "created_at >= ?" in where
        assert "created_at < ?" in where
        assert "resolved_at IS NULL" in where
        assert len(params) == 2

    def test_combined(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        where, params = store._build_where(
            severity="critical",
            status="active",
            since="2026-11-01",
        )
        assert "severity = ?" in where
        assert "resolved_at IS NULL" in where
        assert "created_at >= ?" in where
        assert params == ["critical", "2026-11-01T00:00:00"]


def _insert_alert(
    store,
    created_at,
    sensor="test.sensor",
    severity="critical",
    resolved_at=None,
):
    with store._connect() as conn:
        conn.execute(
            "INSERT INTO alerts "
            "(created_at, sensor, rule, severity, message, dedup_key, resolved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                created_at,
                sensor,
                "test_rule",
                severity,
                "test",
                "test:rule:critical",
                resolved_at,
            ),
        )


class TestListAlertsFilters:
    def test_since(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(store, "2026-10-01T12:00:00+00:00")
        _insert_alert(store, "2026-11-15T12:00:00+00:00")
        alerts = store.list_alerts(since="2026-11-01")
        assert len(alerts) == 1
        assert alerts[0]["created_at"] == "2026-11-15T12:00:00+00:00"

    def test_until(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(store, "2026-10-01T12:00:00+00:00")
        _insert_alert(store, "2026-11-15T12:00:00+00:00")
        alerts = store.list_alerts(until="2026-10-31")
        assert len(alerts) == 1
        assert alerts[0]["created_at"] == "2026-10-01T12:00:00+00:00"

    def test_device_prefixes(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(
            store,
            "2026-11-15T12:00:00+00:00",
            sensor="atmoweb_101.temperature_1",
        )
        _insert_alert(
            store,
            "2026-11-15T12:00:00+00:00",
            sensor="atmoweb_102.temperature_1",
        )
        alerts = store.list_alerts(device_prefixes=["atmoweb_101"])
        assert len(alerts) == 1
        assert alerts[0]["sensor"] == "atmoweb_101.temperature_1"

    def test_offset(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(store, "2026-11-01T12:00:00+00:00")
        _insert_alert(store, "2026-11-02T12:00:00+00:00")
        _insert_alert(store, "2026-11-03T12:00:00+00:00")
        alerts = store.list_alerts(limit=1, offset=1)
        assert len(alerts) == 1
        assert alerts[0]["created_at"] == "2026-11-02T12:00:00+00:00"


class TestCountAlerts:
    def test_empty(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        assert store.count_alerts() == 0

    def test_counts(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(store, "2026-11-01T12:00:00+00:00")
        _insert_alert(store, "2026-11-02T12:00:00+00:00")
        _insert_alert(store, "2026-11-03T12:00:00+00:00")
        assert store.count_alerts() == 3

    def test_with_filters(self, tmp_path):
        store = AlertStore(tmp_path / "alerts.db")
        _insert_alert(store, "2026-11-01T12:00:00+00:00", severity="critical")
        _insert_alert(store, "2026-11-02T12:00:00+00:00", severity="warning")
        assert store.count_alerts(severity="critical") == 1
