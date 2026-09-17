import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from loggerpi_otterpi.atmoweb import AtmoWebReader
from loggerpi_otterpi.batch_factory import SequenceStore
from loggerpi_otterpi.composer import compose_batch
from loggerpi_otterpi.delivery import BatchDelivery
from loggerpi_otterpi.model.measurement import Measurement
from loggerpi_otterpi.otterpi import create_server
from loggerpi_otterpi.otterpi_store import BatchStore
from loggerpi_otterpi.queue import BatchQueue
from loggerpi_otterpi.queue_delivery import deliver_pending


def test_measurement_batch_queue_http_e2e(tmp_path: Path) -> None:
    store = BatchStore(tmp_path / "otter.db")
    server = create_server("127.0.0.1", 0, store)
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

        sequence_store = SequenceStore(tmp_path / "sequence")
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
                sequence_store,
                measurements={"temperature": measurement},
            )

        queue.enqueue(batch)

        delivery = BatchDelivery(f"http://127.0.0.1:{server.server_port}/api/v1/batches")

        assert deliver_pending(queue, delivery) == 1
        assert queue.pending() == []

        stored = store.get(batch.batch_id)

        assert stored is not None
        assert stored.to_dict() == batch.to_dict()
        assert stored.measurements["temperature"].value == 21.5
        assert stored.measurements["temperature"].unit == "°C"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_atmoweb_measurement_batch_queue_http_e2e(tmp_path: Path) -> None:
    received = {}

    class AtmoWebHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            response = {
                "Time": "2026-08-30T18:00:00+00:00",
                "Temp1Read": 21.5,
                "Temp2Read": 22.0,
                "Temp3Read": "N/A",
                "Temp4Read": "N/D",
                "HumRead": 55.2,
                "VacRead": 1013.25,
                "CO2Read": 450,
                "O2Read": 20.9,
                "FanRead": 1200,
            }

            body = json.dumps(response).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    class OtterHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            body = self.rfile.read(length)

            received["path"] = self.path
            received["body"] = json.loads(body.decode("utf-8"))

            self.send_response(202)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    atmoweb_server = HTTPServer(("127.0.0.1", 0), AtmoWebHandler)
    otter_server = HTTPServer(("127.0.0.1", 0), OtterHandler)

    atmoweb_thread = Thread(target=atmoweb_server.serve_forever)
    otter_thread = Thread(target=otter_server.serve_forever)

    atmoweb_thread.start()
    otter_thread.start()

    try:
        reader = AtmoWebReader(
            "127.0.0.1",
            port=atmoweb_server.server_port,
        )

        measurements = reader.read_measurements()

        assert measurements["temperature_1"].value == 21.5
        assert measurements["temperature_1"].unit == "celsius"
        assert measurements["temperature_1"].validity == "valid"

        assert measurements["humidity"].value == 55.2
        assert measurements["humidity"].unit == "percent"

        assert measurements["vacuum"].value == 1013.25
        assert measurements["vacuum"].unit == "mbar"
        assert measurements["vacuum"].validity == "valid"

        assert measurements["temperature_3"].value is None
        assert measurements["temperature_3"].validity == "unavailable"

        assert measurements["temperature_4"].value is None
        assert measurements["temperature_4"].validity == "unknown"

        sequence_store = SequenceStore(tmp_path / "sequence")
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
                sequence_store,
                measurements=measurements,
            )

        queue.enqueue(batch)

        delivery = BatchDelivery(f"http://127.0.0.1:{otter_server.server_port}/api/v1/batches")

        assert deliver_pending(queue, delivery) == 1
        assert queue.pending() == []

        assert received["path"] == "/api/v1/batches"
        assert received["body"] == batch.to_dict()

        assert received["body"]["measurements"]["temperature_1"]["value"] == 21.5
        assert received["body"]["measurements"]["temperature_1"]["source"] == "atmoweb"

        assert received["body"]["measurements"]["vacuum"]["value"] == 1013.25
        assert received["body"]["measurements"]["vacuum"]["unit"] == "mbar"
        assert received["body"]["measurements"]["vacuum"]["source"] == "atmoweb"
    finally:
        atmoweb_server.shutdown()
        otter_server.shutdown()

        atmoweb_thread.join()
        otter_thread.join()

        atmoweb_server.server_close()
        otter_server.server_close()
