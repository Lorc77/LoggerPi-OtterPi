import json
import sqlite3
from datetime import datetime

from batch_factory import SequenceStore, create_batch
from otterpi_store import BatchStore


def test_batch_store_persists_batch(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    batch = create_batch("logger-001", sequence_store)

    assert store.store(batch) == "stored"
    assert store.get(batch.batch_id).to_dict() == batch.to_dict()


def test_batch_store_accepts_identical_duplicate(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    batch = create_batch("logger-001", sequence_store)

    assert store.store(batch) == "stored"
    assert store.store(batch) == "duplicate"


def test_batch_store_rejects_same_batch_id_with_different_content(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    batch = create_batch("logger-001", sequence_store)

    assert store.store(batch) == "stored"

    conflicting_batch = batch.__class__(
        batch_id=batch.batch_id,
        logger_id=batch.logger_id,
        sequence=batch.sequence,
        created_at=batch.created_at,
        schema_version=batch.schema_version,
        system={"test": "conflict"},
        memory=batch.memory,
        measurements=batch.measurements,
    )

    assert conflicting_batch.to_dict() != batch.to_dict()
    assert store.store(conflicting_batch) == "conflict"


def test_batch_store_rejects_same_sequence_with_different_batch_id(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    first = create_batch("logger-001", sequence_store)

    assert store.store(first) == "stored"

    conflicting_batch = create_batch("logger-001", sequence_store)
    conflicting_batch = conflicting_batch.__class__(
        batch_id=conflicting_batch.batch_id,
        logger_id=first.logger_id,
        sequence=first.sequence,
        created_at=conflicting_batch.created_at,
        schema_version=conflicting_batch.schema_version,
        measurements=conflicting_batch.measurements,
        system=conflicting_batch.system,
        memory=conflicting_batch.memory,
    )

    assert store.store(conflicting_batch) == "conflict"


def test_batch_store_uses_wal(tmp_path):
    store = BatchStore(tmp_path / "otter.db")

    with store._connect() as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

        synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]

    assert journal_mode.lower() == "wal"
    assert synchronous == 1


def test_batch_store_latest_returns_newest(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    first = create_batch("logger-001", sequence_store)
    second = create_batch("logger-001", sequence_store)

    store.store(first)
    store.store(second)

    assert store.latest().to_dict() == second.to_dict()


def test_batch_store_latest_empty(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    assert store.latest() is None


def test_batch_store_recent_returns_batches_in_window(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    first = create_batch("logger-001", sequence_store)
    second = create_batch("logger-001", sequence_store)

    store.store(first)
    store.store(second)

    recent = store.recent(hours=24)
    assert len(recent) == 2
    assert recent[0].to_dict() == first.to_dict()
    assert recent[1].to_dict() == second.to_dict()


def test_batch_store_recent_empty(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    assert store.recent(hours=24) == []


def test_batch_store_sets_received_at(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")

    batch = create_batch("logger-001", sequence_store)
    store.store(batch)

    received_at = store.latest_received_at()
    assert received_at is not None
    datetime.fromisoformat(received_at)


def test_batch_store_latest_received_at_empty(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    assert store.latest_received_at() is None


def test_batch_store_latest_received_at_fallback_to_created_at(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")
    batch = create_batch("logger-001", sequence_store)

    # Simuliere eine alte Zeile ohne received_at
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "INSERT INTO batches (batch_id, logger_id, sequence, payload) VALUES (?, ?, ?, ?)",
            (
                batch.batch_id,
                batch.logger_id,
                batch.sequence,
                json.dumps(batch.to_dict()),
            ),
        )

    assert store.latest_received_at() == batch.created_at
