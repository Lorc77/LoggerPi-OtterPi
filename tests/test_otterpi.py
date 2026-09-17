import json
from threading import Thread

from loggerpi_otterpi.batch_factory import SequenceStore, create_batch
from loggerpi_otterpi.otterpi import create_server
from loggerpi_otterpi.otterpi_store import BatchStore


def test_otterpi_accepts_new_batch(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")
    batch = create_batch("logger-001", sequence_store)

    server = create_server("127.0.0.1", 0, store)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        from urllib.request import Request, urlopen

        body = json.dumps(batch.to_dict()).encode("utf-8")

        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/v1/batches",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request) as response:
            assert response.status == 202
            response_body = json.loads(response.read().decode("utf-8"))

        assert response_body == {
            "status": "accepted",
            "batch_id": batch.batch_id,
            "sequence": batch.sequence,
        }

        assert store.get(batch.batch_id).to_dict() == batch.to_dict()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_otterpi_accepts_identical_duplicate(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    sequence_store = SequenceStore(tmp_path / "sequence")
    batch = create_batch("logger-001", sequence_store)

    server = create_server("127.0.0.1", 0, store)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        from urllib.request import Request, urlopen

        body = json.dumps(batch.to_dict()).encode("utf-8")
        url = f"http://127.0.0.1:{server.server_port}/api/v1/batches"

        for _ in range(2):
            request = Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(request) as response:
                assert response.status == 202
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_otterpi_rejects_wrong_content_type(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = create_server("127.0.0.1", 0, store)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/v1/batches",
            data=b"{}",
            headers={"Content-Type": "text/plain"},
            method="POST",
        )

        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 415
            response_body = json.loads(error.read().decode("utf-8"))
            assert response_body["error"]["code"] == "unsupported_media_type"
        else:
            raise AssertionError("Request should have failed with HTTP 415.")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_otterpi_rejects_invalid_batch(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = create_server("127.0.0.1", 0, store)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/v1/batches",
            data=b'{"not_a_batch": true}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 400
            response_body = json.loads(error.read().decode("utf-8"))
            assert response_body["error"]["code"] == "invalid_payload"
        else:
            raise AssertionError("Request should have failed with HTTP 400.")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_otterpi_returns_404_for_unknown_path(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = create_server("127.0.0.1", 0, store)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/v1/unknown",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            urlopen(request)
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("Request should have failed with HTTP 404.")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
