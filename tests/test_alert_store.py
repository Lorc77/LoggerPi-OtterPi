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
