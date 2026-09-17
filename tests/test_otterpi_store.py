from loggerpi_otterpi.batch_factory import SequenceStore, create_batch
from loggerpi_otterpi.otterpi_store import BatchStore


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
