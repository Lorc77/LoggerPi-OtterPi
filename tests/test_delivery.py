import json

from loggerpi_otterpi.batch_factory import SequenceStore, create_batch
from loggerpi_otterpi.delivery import BatchDelivery


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_delivery_sends_batch_as_json(monkeypatch, tmp_path):
    store = SequenceStore(tmp_path / "sequence")
    batch = create_batch("logger-001", store)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(202)

    monkeypatch.setattr("loggerpi_otterpi.delivery.urlopen", fake_urlopen)

    delivery = BatchDelivery("http://otterpi/api/v1/batches")

    assert delivery.send(batch) is True

    request = captured["request"]

    assert request.method == "POST"
    assert request.full_url == "http://otterpi/api/v1/batches"
    assert request.headers["Content-type"] == "application/json"
    assert json.loads(request.data.decode("utf-8")) == batch.to_dict()
    assert captured["timeout"] == 10.0


def test_delivery_accepts_only_http_202(monkeypatch, tmp_path):
    store = SequenceStore(tmp_path / "sequence")
    batch = create_batch("logger-001", store)

    monkeypatch.setattr(
        "loggerpi_otterpi.delivery.urlopen",
        lambda request, timeout: FakeResponse(200),
    )

    delivery = BatchDelivery("http://otterpi/api/v1/batches")

    assert delivery.send(batch) is False


def test_deliver_pending_removes_successfully_delivered_batch(monkeypatch, tmp_path):
    from loggerpi_otterpi.queue import BatchQueue
    from loggerpi_otterpi.queue_delivery import deliver_pending

    store = SequenceStore(tmp_path / "sequence")
    queue = BatchQueue(tmp_path / "queue.jsonl")
    batch = create_batch("logger-001", store)

    queue.enqueue(batch)

    monkeypatch.setattr(
        "loggerpi_otterpi.delivery.urlopen",
        lambda request, timeout: FakeResponse(202),
    )

    delivery = BatchDelivery("http://otterpi/api/v1/batches")

    assert deliver_pending(queue, delivery) == 1
    assert queue.pending() == []


def test_deliver_pending_keeps_batch_when_delivery_fails(monkeypatch, tmp_path):
    from loggerpi_otterpi.queue import BatchQueue
    from loggerpi_otterpi.queue_delivery import deliver_pending

    store = SequenceStore(tmp_path / "sequence")
    queue = BatchQueue(tmp_path / "queue.jsonl")
    batch = create_batch("logger-001", store)

    queue.enqueue(batch)

    monkeypatch.setattr(
        "loggerpi_otterpi.delivery.urlopen",
        lambda request, timeout: FakeResponse(500),
    )

    delivery = BatchDelivery("http://otterpi/api/v1/batches")

    assert deliver_pending(queue, delivery) == 0
    assert queue.pending()[0].to_dict() == batch.to_dict()
