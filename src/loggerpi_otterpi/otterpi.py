import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from alert_engine import AlertEngine
from alert_store import AlertStore
from config_store import (
    ConfigValidationError,
    load_alarm_limits,
    load_mail,
    load_notifications,
    load_rooms,
    save_alarm_limits,
    save_mail,
    save_notifications,
    save_rooms,
)
from dashboard_config import get_rooms
from model.batch import Batch
from notifier import Alert, create_notifiers
from otterpi_store import BatchStore


def _load_admin_config() -> dict:
    try:
        rooms = load_rooms()
    except ConfigValidationError:
        rooms = get_rooms()
    try:
        alarm_limits = load_alarm_limits()
    except ConfigValidationError:
        alarm_limits = {"sensors": {}, "states": {}}
    try:
        mail = load_mail()
    except ConfigValidationError:
        mail = {}
    try:
        notifications = load_notifications()
    except ConfigValidationError:
        notifications = {"channels": []}
    return {
        "rooms": {"rooms": rooms},
        "alarm_limits": alarm_limits,
        "mail": mail,
        "notifications": notifications,
    }


class OtterPiHandler(BaseHTTPRequestHandler):
    store: Optional[BatchStore] = None
    token: Optional[str] = None
    alert_engine: Optional[AlertEngine] = None
    alert_store: Optional[AlertStore] = None

    def do_POST(self) -> None:
        if self.path.startswith("/api/admin/alerts/") and self.path.endswith("/acknowledge"):
            parts = self.path.split("/")
            if len(parts) != 6:
                self.send_error(404)
                return
            try:
                alert_id = int(parts[4])
            except ValueError:
                self.send_error(400)
                return
            try:
                data = self._read_json_body()
                acknowledged_by = data.get("acknowledged_by", "unknown")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": {
                            "code": "invalid_payload",
                            "message": "Invalid JSON body.",
                        },
                    },
                )
                return
            if self.alert_store is None:
                self._send_json(
                    404,
                    {
                        "status": "error",
                        "error": {
                            "code": "not_found",
                            "message": "Alert store not configured.",
                        },
                    },
                )
                return
            success = self.alert_store.acknowledge(alert_id, acknowledged_by)
            if not success:
                self._send_json(
                    404,
                    {
                        "status": "error",
                        "error": {
                            "code": "not_found",
                            "message": "Alert not found or already acknowledged.",
                        },
                    },
                )
                return
            self._send_json(200, {"status": "acknowledged"})
            return

        if self.path == "/api/admin/test-mail":
            try:
                mail = load_mail()
            except ConfigValidationError as exc:
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": {"code": "invalid_config", "message": str(exc)},
                    },
                )
                return
            try:
                notifications = load_notifications()
            except ConfigValidationError:
                notifications = {"channels": []}
            smtp_password = os.environ.get("SMTP_PASSWORD")
            notifiers = create_notifiers(notifications, mail, smtp_password)
            if not notifiers:
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": {
                            "code": "no_notifiers",
                            "message": "No notifiers configured.",
                        },
                    },
                )
                return
            test_alert = Alert(
                sensor="test",
                severity="warning",
                message="This is a test alert from OtterPi Admin.",
            )
            sent = 0
            for notifier in notifiers:
                try:
                    if notifier.send(test_alert):
                        sent += 1
                except Exception:
                    pass
            self._send_json(200, {"status": "sent", "count": sent})
            return

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

        if self.alert_engine is not None:
            self.alert_engine.notify_batch()

        self._send_json(
            202,
            {
                "status": "accepted",
                "batch_id": batch.batch_id,
                "sequence": batch.sequence,
            },
        )

    def do_PUT(self) -> None:
        routes = {
            "/api/admin/rooms": ("rooms", save_rooms),
            "/api/admin/alarm-limits": (None, save_alarm_limits),
            "/api/admin/mail": (None, save_mail),
            "/api/admin/notifications": (None, save_notifications),
        }
        if self.path not in routes:
            self.send_error(404)
            return

        key, save_fn = routes[self.path]
        try:
            data = self._read_json_body()
            if key is not None:
                data = data[key]
            save_fn(data)
        except ConfigValidationError as exc:
            self._send_json(
                400,
                {"status": "error", "error": {"code": "validation_error", "message": str(exc)}},
            )
            return
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(
                400,
                {"status": "error", "error": {"code": "invalid_config", "message": str(exc)}},
            )
            return

        self._send_json(200, {"status": "saved"})

    def do_GET(self) -> None:
        if self.path == "/admin":
            from admin import render_admin

            latest = self.store.latest()
            last_batch_at = latest.created_at if latest else ""
            self._send_html(200, render_admin(_load_admin_config(), last_batch_at))
            return

        if self.path == "/api/admin/config":
            self._send_json(200, _load_admin_config())
            return

        if self.path.startswith("/api/admin/alerts"):
            limit = 100
            only_unacknowledged = False
            if "?" in self.path:
                _, query = self.path.split("?", 1)
                for param in query.split("&"):
                    if param.startswith("limit="):
                        try:
                            limit = int(param.split("=", 1)[1])
                        except ValueError:
                            pass
                    elif param.startswith("only_unacknowledged="):
                        only_unacknowledged = param.split("=", 1)[1] == "1"
            if self.alert_store is None:
                self._send_json(200, {"alerts": []})
                return
            alerts = self.alert_store.list_alerts(
                limit=limit,
                only_unacknowledged=only_unacknowledged,
            )
            self._send_json(200, {"alerts": alerts})
            return

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

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        return json.loads(body.decode("utf-8"))

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=UTF-8")
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
    alert_engine: Optional[AlertEngine] = None,
    alert_store: Optional[AlertStore] = None,
) -> HTTPServer:
    handler = type(
        "OtterPiRequestHandler",
        (OtterPiHandler,),
        {
            "store": store,
            "token": token,
            "alert_engine": alert_engine,
            "alert_store": alert_store,
        },
    )
    return HTTPServer((host, port), handler)
