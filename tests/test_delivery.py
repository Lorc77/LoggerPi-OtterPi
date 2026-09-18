import json

from batch_factory import SequenceStore, create_batch
from delivery import BatchDelivery


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

    monkeypatch.setattr("delivery.urlopen", fake_urlopen)

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
        "delivery.urlopen",
        lambda request, timeout: FakeResponse(200),
    )

    delivery = BatchDelivery("http://otterpi/api/v1/batches")

    assert delivery.send(batch) is False
