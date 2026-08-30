import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from loggerpi_otterpi.batch_factory import SequenceStore
from loggerpi_otterpi.composer import compose_batch
from loggerpi_otterpi.delivery import BatchDelivery
from loggerpi_otterpi.model.measurement import Measurement
from loggerpi_otterpi.queue import BatchQueue
from loggerpi_otterpi.queue_delivery import deliver_pending


def test_measurement_batch_queue_http_e2e(tmp_path: Path) -> None:
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            body = self.rfile.read(length)

            received["path"] = self.path
            received["body"] = json.loads(body.decode("utf-8"))

            self.send_response(202)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever)
    thread.start()

    try:
        measurement = Measurement(
            value=21.5,
            unit="°C",
            measured_at="2026-08-30T18:00:00+00:00",
            validity="valid",
            source="test-reader",
        )

        store = SequenceStore(tmp_path / "sequence")
        queue = BatchQueue(tmp_path / "queue.jsonl")

        with patch(
            "loggerpi_otterpi.composer.get_system_info",
            return_value={
                "time": {
                    "current": "2026-08-30T18:00:00+00:00",
                    "timezone": "UTC",
                    "clock_state": "unknown",
                },
                "boot": {
                    "last_boot_at": "2026-08-30T12:00:00+00:00",
                    "uptime_seconds": 21600,
                },
                "cpu": {
                    "usage_percent": 12.5,
                    "load": {
                        "load_1m": 0.2,
                        "load_5m": 0.1,
                        "load_15m": 0.05,
                    },
                    "temperature_celsius": 42.0,
                },
                "memory": {
                    "total_bytes": 1024 * 1024 * 1024,
                    "available_bytes": 512 * 1024 * 1024,
                    "used_bytes": 512 * 1024 * 1024,
                },
            },
        ):
            batch = compose_batch(
                "logger-001",
                store,
                measurements={"temperature": measurement},
            )

        queue.enqueue(batch)

        delivery = BatchDelivery(f"http://127.0.0.1:{server.server_port}/api/v1/batches")

        assert deliver_pending(queue, delivery) == 1
        assert queue.pending() == []

        assert received["path"] == "/api/v1/batches"
        assert received["body"] == batch.to_dict()
        assert received["body"]["measurements"]["temperature"]["value"] == 21.5
        assert received["body"]["measurements"]["temperature"]["unit"] == "°C"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
