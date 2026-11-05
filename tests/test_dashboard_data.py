"""Tests für die Dashboard-Datenfunktionen."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from dashboard_data import (
    _calculate_average_series,
    _calculate_stats,
    _current_values,
    _recent_batches,
)
from otterpi_store import BatchStore


def _make_batch(measurements=None, created_at=None, batch_id="test-batch", sequence=0):
    return {
        "batch_id": batch_id,
        "logger_id": "loggerpi-001",
        "sequence": sequence,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "measurements": measurements or {},
        "system": {"cpu": {"temperature_celsius": 45.0}},
        "memory": {"total_bytes": 1000, "used_bytes": 500},
    }


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
