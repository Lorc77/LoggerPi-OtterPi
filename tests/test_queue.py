from loggerpi_otterpi.batch_factory import SequenceStore, create_batch
from loggerpi_otterpi.queue import BatchQueue


def test_queue_persists_batch(tmp_path):
    queue = BatchQueue(tmp_path / "queue.jsonl")
    store = SequenceStore(tmp_path / "sequence")

    batch = create_batch("logger-001", store)

    queue.enqueue(batch)

    pending = queue.pending()

    assert len(pending) == 1
    assert pending[0].to_dict() == batch.to_dict()


def test_empty_queue_has_no_pending_batches(tmp_path):
    queue = BatchQueue(tmp_path / "queue.jsonl")

    assert queue.pending() == []
