import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from .model.batch import Batch
from .otterpi_store import BatchStore


class OtterPiHandler(BaseHTTPRequestHandler):
    store: Optional[BatchStore] = None

    def do_POST(self) -> None:
        if self.path != "/api/v1/batches":
            self.send_error(404)
            return

        if self.headers.get("Content-Type") != "application/json":
            self._send_json(
                415,
                {
                    "status": "error",
                    "error": {
                        "code": "unsupported_media_type",
                        "message": "Content-Type must be application/json.",
                    },
                },
            )
            return

        try:
            length = int(self.headers["Content-Length"])
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
            batch = _batch_from_dict(data)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self._send_json(
                400,
                {
                    "status": "error",
                    "error": {
                        "code": "invalid_payload",
                        "message": "Request body does not conform to Core Batch v1.",
                    },
                },
            )
            return

        result = self.store.store(batch)

        if result == "conflict":
            self._send_json(
                409,
                {
                    "status": "error",
                    "error": {
                        "code": "batch_conflict",
                        "message": "Batch identity conflicts with an existing batch.",
                    },
                },
            )
            return

        self._send_json(
            202,
            {
                "status": "accepted",
                "batch_id": batch.batch_id,
                "sequence": batch.sequence,
            },
        )

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args) -> None:
        pass


def _batch_from_dict(data: dict) -> Batch:
    measurements = {
        name: _measurement_from_dict(measurement)
        for name, measurement in data.pop("measurements", {}).items()
    }

    return Batch(
        **data,
        measurements=measurements,
    )


def _measurement_from_dict(data: dict):
    from .model.measurement import Measurement

    return Measurement(**data)


def create_server(
    host: str,
    port: int,
    store: BatchStore,
) -> HTTPServer:
    handler = type(
        "OtterPiRequestHandler",
        (OtterPiHandler,),
        {"store": store},
    )

    return HTTPServer((host, port), handler)
