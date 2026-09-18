from pathlib import Path

from batch_factory import SequenceStore, create_batch


def test_sequence_is_persistent(tmp_path):
    path = tmp_path / "sequence"

    first_store = SequenceStore(path)
    assert first_store.next() == 0
    assert first_store.next() == 1

    second_store = SequenceStore(path)
    assert second_store.next() == 2


def test_create_batch_uses_persistent_sequence(tmp_path):
    store = SequenceStore(tmp_path / "sequence")

    first = create_batch("logger-001", store)
    second = create_batch("logger-001", store)

    assert first.sequence == 0
    assert second.sequence == 1
    assert first.batch_id != second.batch_id
    assert first.logger_id == "logger-001"
    assert first.schema_version == "1.0"


def test_create_batch_includes_system_and_memory(tmp_path: Path) -> None:
    store = SequenceStore(tmp_path / "sequence")

    system = {
        "time": {
            "current": "2026-08-30T12:00:00+00:00",
            "timezone": "CEST",
            "clock_state": "unknown",
        },
        "boot": {
            "last_boot_at": "2026-08-30T10:00:00+00:00",
            "uptime_seconds": 7200,
        },
        "cpu": {
            "usage_percent": 15.0,
            "load": {
                "1m": 0.42,
                "5m": 0.35,
                "15m": 0.28,
            },
        },
    }
    memory = {
        "total_bytes": 104857600,
        "available_bytes": 26214400,
        "used_bytes": 78643200,
    }

    batch = create_batch(
        "logger-001",
        store,
        system=system,
        memory=memory,
    )

    assert batch.system == system
    assert batch.memory == memory
