"""Tests für die Heartbeat-/Offline-Status-Logik."""

from datetime import datetime, timedelta, timezone

from heartbeat import offline_status


def _iso(seconds_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat()


class TestOfflineStatus:
    def test_no_batch(self):
        status_class, text = offline_status(None)
        assert status_class == "status-off"
        assert text == "No batch received yet"

    def test_fresh_batch(self):
        status_class, text = offline_status(_iso(60))
        assert status_class == "status-ok"
        assert "Last batch" in text

    def test_warning_threshold(self):
        status_class, text = offline_status(_iso(1801))
        assert status_class == "status-warn"
        assert "Last batch" in text

    def test_critical_threshold(self):
        status_class, text = offline_status(_iso(3601))
        assert status_class == "status-critical"
        assert "LoggerPi offline" in text

    def test_custom_thresholds(self):
        status_class, _ = offline_status(_iso(120), warning_seconds=60, critical_seconds=300)
        assert status_class == "status-warn"

    def test_invalid_timestamp(self):
        status_class, text = offline_status("not-a-timestamp")
        assert status_class == "status-off"
        assert text == "Invalid timestamp"
