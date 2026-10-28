import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from model.batch import Batch
from otterpi_store import BatchStore


class OtterPiHandler(BaseHTTPRequestHandler):
    store: Optional[BatchStore] = None
    token: Optional[str] = None

    def do_POST(self) -> None:
        if self.path != "/api/v1/batches":
            self.send_error(404)
            return

        # Token validieren
        auth = self.headers.get("Authorization", "")
        expected = f"Bearer {self.token}"

        if auth != expected:
            self._send_json(
                401,
                {
                    "status": "error",
                    "error": {
                        "code": "unauthorized",
                        "message": "Invalid or missing token.",
                    },
                },
            )
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

    def do_GET(self) -> None:
        # Neue Routen: /room/, /device/, /climate/ + Redirect von /raum/
        if (
            self.path == "/"
            or self.path.startswith("/room/")
            or self.path.startswith("/device/")
            or self.path.startswith("/climate/")
        ):
            from dashboard import render_dashboard

            room_id = ""
            device_id = ""
            climate_id = ""
            range_key = "7d"
            start_date = ""
            end_date = ""

            if self.path.startswith("/room/"):
                room_id = self.path.split("/")[2]

            elif self.path.startswith("/device/"):
                # /device/<key> oder /device/<key>?range=7d&start_date=...
                path_part = self.path.split("/")[2]

                # Query-Parameter extrahieren
                if "?" in path_part:
                    path_part, query = path_part.split("?", 1)
                    for param in query.split("&"):
                        if param.startswith("range="):
                            range_key = param.split("=")[1]
                        elif param.startswith("start_date="):
                            start_date = param.split("=")[1]
                        elif param.startswith("end_date="):
                            end_date = param.split("=")[1]

                device_id = path_part

            elif self.path.startswith("/climate/"):
                # /climate/<room_id> oder /climate/<room_id>?range=7d&start_date=...
                path_part = self.path.split("/")[2]

                # Query-Parameter extrahieren
                if "?" in path_part:
                    path_part, query = path_part.split("?", 1)
                    for param in query.split("&"):
                        if param.startswith("range="):
                            range_key = param.split("=")[1]
                        elif param.startswith("start_date="):
                            start_date = param.split("=")[1]
                        elif param.startswith("end_date="):
                            end_date = param.split("=")[1]

                climate_id = path_part

            html = render_dashboard(
                self.store,
                room_id=room_id,
                device_id=device_id,
                range_key=range_key,
                climate_id=climate_id,
                start_date=start_date,
                end_date=end_date,
            )
            body = html.encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=UTF-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Redirect von alten /raum/ URLs auf /room/
        if self.path.startswith("/raum/"):
            room_id = self.path.split("/")[2]
            self.send_response(301)
            self.send_header("Location", f"/room/{room_id}")
            self.end_headers()
            return

        if self.path == "/otter2.png":
            with open("/opt/loggerpi-otterpi/otter2.png", "rb") as f:
                body = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

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
        for name, measurement in data.get("measurements", {}).items()
    }

    batch_data = {key: value for key, value in data.items() if key != "measurements"}

    return Batch(
        **batch_data,
        measurements=measurements,
    )


def _measurement_from_dict(data: dict):
    from model.measurement import Measurement

    return Measurement(**data)


def create_server(
    host: str,
    port: int,
    store: BatchStore,
    token: Optional[str] = None,
) -> HTTPServer:
    handler = type(
        "OtterPiRequestHandler",
        (OtterPiHandler,),
        {"store": store, "token": token},
    )

    return HTTPServer((host, port), handler)
