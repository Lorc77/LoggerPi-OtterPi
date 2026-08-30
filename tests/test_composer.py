from pathlib import Path

from loggerpi_otterpi.batch_factory import SequenceStore
from loggerpi_otterpi.composer import compose_batch


def test_compose_batch_maps_system_info_to_batch(tmp_path: Path, monkeypatch) -> None:
    system_info = {
        "time": {
            "current": "2026-08-30T18:00:00+00:00",
            "timezone": "UTC",
            "clock_state": "unknown",
        },
        "boot": {
            "last_boot_at": "2026-08-30T12:00:00+00:00",
            "uptime_seconds": 21600,
        },
        "cpu": {
            "usage_percent": 12.5,
            "load": {
                "load_1m": 0.5,
                "load_5m": 0.4,
                "load_15m": 0.3,
            },
            "temperature_celsius": 47.774,
        },
        "memory": {
            "total_bytes": 104857600,
            "available_bytes": 26214400,
            "used_bytes": 78643200,
        },
    }

    monkeypatch.setattr(
        "loggerpi_otterpi.composer.get_system_info",
        lambda: system_info,
    )

    batch = compose_batch(
        logger_id="logger-001",
        sequence_store=SequenceStore(tmp_path / "sequence"),
    )

    assert batch.logger_id == "logger-001"
    assert batch.sequence == 0
    assert batch.system == {
        "time": system_info["time"],
        "boot": system_info["boot"],
        "cpu": system_info["cpu"],
    }
    assert batch.memory == system_info["memory"]
    assert batch.measurements == {}
