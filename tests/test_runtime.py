from batch_factory import SequenceStore, create_batch
from batch_queue import BatchQueue
from model.measurement import Measurement
from runtime import LoggerRuntime


class FakeReader:
    def __init__(self, measurements):
        self.measurements = measurements
        self.calls = 0

    def read_measurements(self):
        self.calls += 1
        return self.measurements


class FakeDelivery:
    def __init__(self, result):
        self.result = result
        self.batches = []

    def send(self, batch):
        self.batches.append(batch)
        return self.result


def _patch_system_info(monkeypatch):
    monkeypatch.setattr(
        "composer.get_system_info",
        lambda: {
            "time": {
                "current": "2026-09-17T12:00:00+00:00",
                "timezone": "UTC",
                "clock_state": "unknown",
            },
            "boot": {
                "last_boot_at": "2026-09-17T08:00:00+00:00",
                "uptime_seconds": 14400,
            },
            "cpu": {
                "usage_percent": 10.0,
                "load": {
                    "load_1m": 0.1,
                    "load_5m": 0.1,
                    "load_15m": 0.1,
                },
                "temperature_celsius": 45.0,
            },
            "memory": {
                "total_bytes": 100,
                "available_bytes": 50,
                "used_bytes": 50,
            },
        },
    )


def test_runtime_creates_and_delivers_one_batch(tmp_path, monkeypatch):
    measurements = {
        "temperature_1": Measurement(
            value=20.5,
            unit="celsius",
            measured_at="2026-09-17T12:00:00+00:00",
            validity="valid",
            source="atmoweb",
        )
    }

    reader = FakeReader(measurements)
    delivery = FakeDelivery(True)
    queue = BatchQueue(tmp_path / "queue.jsonl")

    _patch_system_info(monkeypatch)

    runtime = LoggerRuntime(
        logger_id="logger-001",
        readers={"atmoweb_101": reader},
        sequence_store=SequenceStore(tmp_path / "sequence"),
        delivery=delivery,
        queue=queue,
    )

    batch = runtime.run_once()

    assert reader.calls == 1
    assert len(delivery.batches) == 1
    assert delivery.batches[0].to_dict() == batch.to_dict()
    assert batch.measurements == {"atmoweb_101.temperature_1": measurements["temperature_1"]}
    assert batch.sequence == 0
    assert queue.pending() == []


def test_runtime_queues_batch_when_delivery_fails(tmp_path, monkeypatch):
    measurements = {
        "temperature_1": Measurement(
            value=20.5,
            unit="celsius",
            measured_at="2026-09-17T12:00:00+00:00",
            validity="valid",
            source="atmoweb",
        )
    }

    reader = FakeReader(measurements)
    delivery = FakeDelivery(False)
    queue = BatchQueue(tmp_path / "queue.jsonl")

    _patch_system_info(monkeypatch)

    runtime = LoggerRuntime(
        logger_id="logger-001",
        readers={"atmoweb_101": reader},
        sequence_store=SequenceStore(tmp_path / "sequence"),
        delivery=delivery,
        queue=queue,
    )

    batch = runtime.run_once()

    assert reader.calls == 1
    assert len(delivery.batches) == 1

    pending = queue.pending()

    assert len(pending) == 1
    assert pending[0].to_dict() == batch.to_dict()


def test_runtime_combines_multiple_readers_into_one_batch(tmp_path, monkeypatch):
    reader_101 = FakeReader(
        {
            "temperature_1": Measurement(
                value=20.5,
                unit="celsius",
                measured_at="2026-09-17T12:00:00+00:00",
                validity="valid",
                source="atmoweb",
            )
        }
    )
    reader_102 = FakeReader(
        {
            "temperature_1": Measurement(
                value=21.5,
                unit="celsius",
                measured_at="2026-09-17T12:00:00+00:00",
                validity="valid",
                source="atmoweb",
            )
        }
    )

    delivery = FakeDelivery(True)
    queue = BatchQueue(tmp_path / "queue.jsonl")

    _patch_system_info(monkeypatch)

    runtime = LoggerRuntime(
        logger_id="logger-001",
        readers={
            "atmoweb_101": reader_101,
            "atmoweb_102": reader_102,
        },
        sequence_store=SequenceStore(tmp_path / "sequence"),
        delivery=delivery,
        queue=queue,
    )

    batch = runtime.run_once()

    assert reader_101.calls == 1
    assert reader_102.calls == 1
    assert len(delivery.batches) == 1
    assert delivery.batches[0] is batch

    assert batch.measurements == {
        "atmoweb_101.temperature_1": reader_101.measurements["temperature_1"],
        "atmoweb_102.temperature_1": reader_102.measurements["temperature_1"],
    }
    assert batch.sequence == 0
    assert queue.pending() == []


def test_runtime_replays_queued_batch_before_new_batch(tmp_path, monkeypatch):
    measurements = {
        "temperature_1": Measurement(
            value=20.5,
            unit="celsius",
            measured_at="2026-09-17T12:00:00+00:00",
            validity="valid",
            source="atmoweb",
        )
    }

    queue = BatchQueue(tmp_path / "queue.jsonl")
    sequence_store = SequenceStore(tmp_path / "sequence")

    queued_batch = create_batch(
        logger_id="logger-001",
        sequence_store=sequence_store,
        measurements=measurements,
    )
    queue.enqueue(queued_batch)

    reader = FakeReader(measurements)
    delivery = FakeDelivery(True)

    monkeypatch.setattr(
        "composer.get_system_info",
        lambda: {
            "time": {
                "current": "2026-09-17T12:00:00+00:00",
                "timezone": "UTC",
                "clock_state": "unknown",
            },
            "boot": {
                "last_boot_at": "2026-09-17T08:00:00+00:00",
                "uptime_seconds": 14400,
            },
            "cpu": {
                "usage_percent": 10.0,
                "load": {
                    "load_1m": 0.1,
                    "load_5m": 0.1,
                    "load_15m": 0.1,
                },
                "temperature_celsius": 45.0,
            },
            "memory": {
                "total_bytes": 100,
                "available_bytes": 50,
                "used_bytes": 50,
            },
        },
    )

    runtime = LoggerRuntime(
        logger_id="logger-001",
        readers={"atmoweb_101": reader},
        sequence_store=sequence_store,
        delivery=delivery,
        queue=queue,
    )

    batch = runtime.run_once()

    assert reader.calls == 1
    assert len(delivery.batches) == 2
    assert delivery.batches[0].to_dict() == queued_batch.to_dict()
    assert delivery.batches[1].to_dict() == batch.to_dict()
    assert queue.pending() == []
