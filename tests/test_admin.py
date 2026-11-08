"""Tests für die Admin-Routen."""

import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from config_store import load_alarm_limits, load_mail, load_notifications, load_rooms
from otterpi import create_server
from otterpi_store import BatchStore

TEST_TOKEN = "lp-test-token-1234567890abcdef"


@pytest.fixture(autouse=True)
def _config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OTTERPI_CONFIG_DIR", str(tmp_path / "config"))
    return tmp_path / "config"


def _server(store):
    return create_server("127.0.0.1", 0, store, token=TEST_TOKEN)


def _put(url, data):
    return Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )


def _valid_rooms():
    return {
        "rooms": {
            "r1304": {
                "name": "R1304 · Culture Room I",
                "icon": "🦗",
                "devices": [
                    {"name": "Freezer", "key": "freezer", "type": "freezer"},
                ],
                "weatherhub_climate": [],
            }
        }
    }


def test_admin_page_renders(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/admin") as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert "ZOOLOGY-Observer Admin" in html
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_admin_config_returns_json(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/admin/config") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
        assert set(data) == {"rooms", "alarm_limits", "mail", "notifications"}
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_rooms_saves(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/rooms",
            _valid_rooms(),
        )
        with urlopen(req) as resp:
            assert resp.status == 200
            assert json.loads(resp.read().decode("utf-8")) == {"status": "saved"}
        assert load_rooms() == _valid_rooms()["rooms"]
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_rooms_invalid_returns_400(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/rooms",
            {"rooms": {"R1304": {"name": "X", "devices": []}}},
        )
        try:
            urlopen(req)
        except HTTPError as error:
            assert error.code == 400
            try:
                body = json.loads(error.read().decode("utf-8"))
            except (ConnectionResetError, ConnectionAbortedError):
                return
            assert body["error"]["code"] == "validation_error"
        else:
            raise AssertionError("Expected HTTP 400")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_unknown_returns_404(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/unknown",
            {},
        )
        try:
            urlopen(req)
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("Expected HTTP 404")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_alarm_limits_saves(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        payload = {"sensors": {"atmoweb_101.temperature_1": {"warning_max": 26.0}}}
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/alarm-limits",
            payload,
        )
        with urlopen(req) as resp:
            assert resp.status == 200
        assert load_alarm_limits() == payload
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_mail_saves(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        payload = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "recipients": ["a@example.com"],
        }
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/mail",
            payload,
        )
        with urlopen(req) as resp:
            assert resp.status == 200
        assert load_mail() == payload
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_put_notifications_saves(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        payload = {
            "channels": [{"type": "ntfy", "enabled": True, "url": "https://ntfy.sh", "topic": "t"}]
        }
        req = _put(
            f"http://127.0.0.1:{server.server_port}/api/admin/notifications",
            payload,
        )
        with urlopen(req) as resp:
            assert resp.status == 200
        assert load_notifications() == payload
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_get_alerts_returns_json(tmp_path):
    from alert_store import AlertStore

    store = BatchStore(tmp_path / "otter.db")
    alert_store = AlertStore(tmp_path / "alerts.db")
    server = create_server("127.0.0.1", 0, store, token=TEST_TOKEN, alert_store=alert_store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/admin/alerts") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
        assert data == {"alerts": []}
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_post_acknowledge_alert(tmp_path):
    from alert_store import AlertStore
    from notifier import Alert

    store = BatchStore(tmp_path / "otter.db")
    alert_store = AlertStore(tmp_path / "alerts.db")
    alert_id = alert_store.store(
        Alert(
            sensor="test.sensor",
            severity="critical",
            message="test",
            rule="test_rule",
            dedup_key="test.sensor:test_rule:critical",
        )
    )
    server = create_server("127.0.0.1", 0, store, token=TEST_TOKEN, alert_store=alert_store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        req = Request(
            f"http://127.0.0.1:{server.server_port}/api/admin/alerts/{alert_id}/acknowledge",
            data=json.dumps({"acknowledged_by": "makki"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
        assert data == {"status": "acknowledged"}
        alerts = alert_store.list_alerts()
        assert alerts[0]["acknowledged"] == 1
        assert alerts[0]["acknowledged_by"] == "makki"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_post_test_mail_no_config(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = create_server("127.0.0.1", 0, store, token=TEST_TOKEN)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        req = Request(
            f"http://127.0.0.1:{server.server_port}/api/admin/test-mail",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(req)
        except HTTPError as error:
            assert error.code == 400
            body = json.loads(error.read().decode("utf-8"))
            assert body["error"]["code"] == "invalid_config"
        else:
            raise AssertionError("Expected HTTP 400")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_admin_page_shows_status_lamp(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/admin") as resp:
            html = resp.read().decode("utf-8")
        assert 'class="lamp status-off"' in html
        assert "No batch received yet" in html
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_admin_page_contains_system_config_js(tmp_path):
    store = BatchStore(tmp_path / "otter.db")
    server = _server(store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/admin") as resp:
            html = resp.read().decode("utf-8")
        assert "saveSystemConfig" in html
        assert "system-warning-minutes" in html
        assert "system-critical-minutes" in html
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_render_admin_shows_offline_status():
    from datetime import datetime, timedelta, timezone

    from admin import render_admin

    old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
    config = {
        "rooms": {"rooms": {}},
        "alarm_limits": {"sensors": {}, "states": {}, "system": {}},
        "mail": {},
        "notifications": {"channels": []},
    }
    html = render_admin(config, last_batch_at="", last_received_at=old)
    assert "LoggerPi offline" in html
    assert "status-critical" in html


def test_render_admin_shows_warning_status():
    from datetime import datetime, timedelta, timezone

    from admin import render_admin

    old = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
    config = {
        "rooms": {"rooms": {}},
        "alarm_limits": {"sensors": {}, "states": {}, "system": {}},
        "mail": {},
        "notifications": {"channels": []},
    }
    html = render_admin(config, last_batch_at="", last_received_at=old)
    assert "Last batch" in html
    assert "status-warn" in html


def test_get_alerts_only_active(tmp_path):
    from alert_store import AlertStore
    from notifier import Alert

    store = BatchStore(tmp_path / "otter.db")
    alert_store = AlertStore(tmp_path / "alerts.db")
    alert_store.store(
        Alert(
            sensor="test.sensor",
            severity="critical",
            message="test",
            rule="test_rule",
            dedup_key="test.sensor:test_rule:critical",
        )
    )
    alert_store.store(
        Alert(
            sensor="test.sensor2",
            severity="warning",
            message="test2",
            rule="test_rule2",
            dedup_key="test.sensor2:test_rule2:warning",
        )
    )
    alert_store.resolve("test.sensor:test_rule:critical")

    server = create_server("127.0.0.1", 0, store, token=TEST_TOKEN, alert_store=alert_store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(
            f"http://127.0.0.1:{server.server_port}/api/admin/alerts?only_active=1"
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["dedup_key"] == "test.sensor2:test_rule2:warning"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_get_alerts_includes_resolved_at(tmp_path):
    from alert_store import AlertStore
    from notifier import Alert

    store = BatchStore(tmp_path / "otter.db")
    alert_store = AlertStore(tmp_path / "alerts.db")
    alert_store.store(
        Alert(
            sensor="test.sensor",
            severity="critical",
            message="test",
            rule="test_rule",
            dedup_key="test.sensor:test_rule:critical",
        )
    )
    alert_store.resolve("test.sensor:test_rule:critical")

    server = create_server("127.0.0.1", 0, store, token=TEST_TOKEN, alert_store=alert_store)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/admin/alerts") as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert data["alerts"][0]["resolved_at"] is not None
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
