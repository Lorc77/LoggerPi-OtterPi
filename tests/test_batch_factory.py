from loggerpi_otterpi.batch_factory import SequenceStore, create_batch


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
