"""Tests für die Dashboard-Datenfunktionen."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from dashboard_data import (
    _calculate_average_series,
    _calculate_stats,
    _current_values,
    _device_chips,
    _device_status,
    _led_value,
    _recent_batches,
)
from otterpi_store import BatchStore


def _make_measurement(
    value, unit="celsius", validity="valid", measured_at=None, validity_reason=None
):
    result = {
        "value": value,
        "unit": unit,
        "measured_at": measured_at or "2026-10-27T12:00:00+00:00",
        "validity": validity,
        "source": "weatherhub",
    }
    if validity_reason is not None:
        result["validity_reason"] = validity_reason
    return result


def _make_batch(measurements=None, created_at=None, batch_id="test-batch", sequence=0, states=None):
    result = {
        "batch_id": batch_id,
        "logger_id": "loggerpi-001",
        "sequence": sequence,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "measurements": measurements or {},
        "system": {"cpu": {"temperature_celsius": 45.0}},
        "memory": {"total_bytes": 1000, "used_bytes": 500},
    }
    if states is not None:
        result["states"] = states
    return result


def _store_batches(tmp_path, batches):
    store = BatchStore(tmp_path / "otter.db")
    with sqlite3.connect(store.path) as conn:
        for batch in batches:
            conn.execute(
                "INSERT INTO batches (batch_id, logger_id, sequence, payload) VALUES (?, ?, ?, ?)",
                (batch["batch_id"], batch["logger_id"], batch["sequence"], json.dumps(batch)),
            )
    return store


class TestCalculateStats:
    def test_empty(self):
        stats = _calculate_stats([], [])
        assert stats == {
            "temp_min": 0.0,
            "temp_max": 0.0,
            "temp_avg": 0.0,
            "hum_min": 0.0,
            "hum_max": 0.0,
            "hum_avg": 0.0,
        }

    def test_temp_only(self):
        stats = _calculate_stats([{"value": 10.0}, {"value": 20.0}], [])
        assert stats["temp_min"] == 10.0
        assert stats["temp_max"] == 20.0
        assert stats["temp_avg"] == 15.0
        assert stats["hum_avg"] == 0.0

    def test_hum_only(self):
        stats = _calculate_stats([], [{"value": 40.0}, {"value": 60.0}])
        assert stats["hum_min"] == 40.0
        assert stats["hum_max"] == 60.0
        assert stats["hum_avg"] == 50.0
        assert stats["temp_avg"] == 0.0

    def test_ignores_none(self):
        stats = _calculate_stats([{"value": 10.0}, {"value": None}], [])
        assert stats["temp_avg"] == 10.0


class TestCalculateAverageSeries:
    def test_average_of_multiple_sensors(self):
        batches = [
            _make_batch(
                {
                    "a.temperature": {"value": 10.0},
                    "b.temperature": {"value": 20.0},
                },
                created_at="2026-10-27T10:00:00+00:00",
            )
        ]
        sensor_keys = [("a", "A", "a.temperature"), ("b", "B", "b.temperature")]
        series = _calculate_average_series(batches, sensor_keys)
        assert len(series) == 1
        assert series[0]["value"] == 15.0

    def test_skips_batches_without_values(self):
        batches = [_make_batch({}, created_at="2026-10-27T10:00:00+00:00")]
        series = _calculate_average_series(batches, [("a", "A", "a.temperature")])
        assert series == []

    def test_time_conversion(self):
        batches = [
            _make_batch(
                {"a.temperature": {"value": 10.0}},
                created_at="2026-10-27T10:00:00+00:00",
            )
        ]
        series = _calculate_average_series(batches, [("a", "A", "a.temperature")])
        assert series[0]["label"] == "11:00"
        assert series[0]["date"] == "2026-10-27"


class TestCurrentValues:
    def test_empty(self):
        current = _current_values([])
        assert current["last_batch"] == "–"
        assert current["temp_101"] == 0.0

    def test_extracts_values(self):
        batch = _make_batch(
            {
                "atmoweb_101.temperature_1": {"value": 23.5},
                "atmoweb_101.humidity": {"value": 60.0},
                "freezer.temperature": {"value": -80.0},
            },
            created_at="2026-10-27T10:00:00+00:00",
        )
        current = _current_values([batch])
        assert current["temp_101"] == 23.5
        assert current["hum_101"] == 60.0
        assert current["temp_freezer"] == -80.0
        assert current["cpu_temp"] == 45.0
        assert current["memory_used"] == 50.0


class TestRecentBatches:
    def test_returns_recent(self, tmp_path):
        now = datetime.now(timezone.utc)
        batches = [
            _make_batch(
                created_at=(now - timedelta(hours=1)).isoformat(), batch_id="b1", sequence=1
            ),
            _make_batch(
                created_at=(now - timedelta(hours=2)).isoformat(), batch_id="b2", sequence=2
            ),
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48)
        assert len(result) == 2

    def test_filters_old(self, tmp_path):
        now = datetime.now(timezone.utc)
        batches = [
            _make_batch(
                created_at=(now - timedelta(hours=1)).isoformat(), batch_id="b1", sequence=1
            ),
            _make_batch(
                created_at=(now - timedelta(hours=100)).isoformat(), batch_id="b2", sequence=2
            ),
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48)
        assert len(result) == 1

    def test_respects_limit(self, tmp_path):
        now = datetime.now(timezone.utc)
        batches = [
            _make_batch(
                created_at=(now - timedelta(minutes=i)).isoformat(),
                batch_id=f"b{i}",
                sequence=i,
            )
            for i in range(5)
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48, limit=3)
        assert len(result) == 3

    def test_chronological_order(self, tmp_path):
        now = datetime.now(timezone.utc)
        batches = [
            _make_batch(
                created_at=(now - timedelta(hours=2)).isoformat(), batch_id="b1", sequence=1
            ),
            _make_batch(
                created_at=(now - timedelta(hours=1)).isoformat(), batch_id="b2", sequence=2
            ),
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48)
        assert result[0]["created_at"] < result[1]["created_at"]


class TestDeviceStatusWithStates:
    def test_battery_low_sets_warn(self):
        batches = [
            _make_batch(
                {"weatherhub_0101f89974e0.temperature_2": _make_measurement(4.5)},
                states={"weatherhub_0101f89974e0": {"battery_low": True}},
            )
        ]
        assert (
            _device_status(batches, "weatherhub_0101f89974e0", "weatherhub_id01") == "status-warn"
        )

    def test_alarm_sets_critical(self):
        batches = [
            _make_batch(
                {"freezer.temperature": _make_measurement(-80.0)},
                states={"freezer": {"alarms": ["ac_power_failure"]}},
            )
        ]
        assert _device_status(batches, "freezer", "freezer") == "status-critical"


class TestDeviceChips:
    def test_ok_chip(self):
        now = datetime.now(timezone.utc).isoformat()
        batches = [
            _make_batch(
                {
                    "atmoweb_101.temperature_1": _make_measurement(23.5, measured_at=now),
                    "atmoweb_101.humidity": _make_measurement(
                        60.0, unit="percent", measured_at=now
                    ),
                }
            )
        ]
        chips = _device_chips(batches, "atmoweb_101", "atmoweb")
        assert ("OK", "chip-ok") in chips

    def test_battery_low_chip(self):
        batches = [
            _make_batch(
                {"weatherhub_0101f89974e0.temperature_2": _make_measurement(4.5)},
                states={"weatherhub_0101f89974e0": {"battery_low": True}},
            )
        ]
        chips = _device_chips(batches, "weatherhub_0101f89974e0", "weatherhub_id01")
        assert ("⚠ Battery low", "chip-warn") in chips

    def test_alarm_chip(self):
        batches = [
            _make_batch(
                {"freezer.temperature": _make_measurement(-80.0)},
                states={"freezer": {"alarms": ["temperature_above_high_alarm"]}},
            )
        ]
        chips = _device_chips(batches, "freezer", "freezer")
        assert ("🚨 Alarm: Overtemperature", "chip-critical") in chips

    def test_invalid_overflow_chip(self):
        batches = [
            _make_batch(
                {
                    "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                        None, validity="invalid", validity_reason="overflow"
                    )
                },
            )
        ]
        chips = _device_chips(batches, "weatherhub_0101f89974e0", "weatherhub_id01")
        assert ("⛔ Sensor overflow", "chip-critical") in chips

    def test_door_open_chip(self):
        batches = [
            _make_batch(
                {"atmoweb_101.temperature_1": _make_measurement(23.5)},
                states={"atmoweb_101": {"door_open": True}},
            )
        ]
        chips = _device_chips(batches, "atmoweb_101", "atmoweb")
        assert ("Door open", "chip-info") in chips


class TestLedValue:
    def test_led_value(self):
        batches = [
            _make_batch(
                {"atmoweb_102.temperature_1": _make_measurement(24.0)},
                states={"atmoweb_102": {"lights": {"led": 2}}},
            )
        ]
        assert _led_value(batches, "atmoweb_102") == 2

    def test_no_led(self):
        batches = [_make_batch({"atmoweb_101.temperature_1": _make_measurement(23.5)})]
        assert _led_value(batches, "atmoweb_101") is None


class TestRecentBatchesReceivedAt:
    def test_received_at_is_set(self, tmp_path):
        now = datetime.now(timezone.utc)
        batches = [
            _make_batch(
                created_at=(now - timedelta(hours=1)).isoformat(),
                batch_id="b1",
                sequence=1,
            ),
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48)
        assert len(result) == 1
        assert "_received_at" in result[0]
        assert result[0]["_received_at"] is not None

    def test_received_at_fallback_to_created_at(self, tmp_path):
        now = datetime.now(timezone.utc)
        created_at = (now - timedelta(hours=1)).isoformat()
        batches = [
            _make_batch(created_at=created_at, batch_id="b1", sequence=1),
        ]
        store = _store_batches(tmp_path, batches)
        result = _recent_batches(store, hours=48)
        assert result[0]["_received_at"] == created_at

    def test_received_at_is_read_from_db(self, tmp_path):
        now = datetime.now(timezone.utc)
        created_at = (now - timedelta(hours=2)).isoformat()
        received_at = (now - timedelta(minutes=5)).isoformat()
        batch = _make_batch(created_at=created_at, batch_id="b1", sequence=1)
        store = BatchStore(tmp_path / "otter.db")
        with sqlite3.connect(store.path) as conn:
            conn.execute(
                "INSERT INTO batches "
                "(batch_id, logger_id, sequence, payload, received_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    batch["batch_id"],
                    batch["logger_id"],
                    batch["sequence"],
                    json.dumps(batch),
                    received_at,
                ),
            )
        result = _recent_batches(store, hours=48)
        assert result[0]["_received_at"] == received_at
