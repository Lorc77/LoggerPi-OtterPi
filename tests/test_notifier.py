"""Tests für die Notifier."""

import json

from notifier import (
    Alert,
    EmailNotifier,
    NtfyNotifier,
    WebhookNotifier,
    create_notifiers,
)


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _alert():
    return Alert(
        sensor="freezer.temperature",
        severity="critical",
        message="Freezer too warm: -65 °C",
        value=-65.0,
        threshold=-70.0,
    )


class TestNtfyNotifier:
    def test_send_success(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            captured["data"] = req.data
            captured["title"] = req.get_header("Title")
            return FakeResponse(200)

        monkeypatch.setattr("notifier.urlopen", fake_urlopen)
        n = NtfyNotifier({"url": "https://ntfy.sh", "topic": "test"})
        assert n.send(_alert()) is True
        assert captured["url"] == "https://ntfy.sh/test"
        assert captured["data"].decode("utf-8") == "Freezer too warm: -65 °C"
        assert captured["title"] == "CRITICAL: freezer.temperature"

    def test_send_failure(self, monkeypatch):
        def fake_urlopen(req, timeout):
            raise OSError("network down")

        monkeypatch.setattr("notifier.urlopen", fake_urlopen)
        n = NtfyNotifier({"url": "https://ntfy.sh", "topic": "test"})
        assert n.send(_alert()) is False


class TestWebhookNotifier:
    def test_discord_payload(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["data"] = req.data
            return FakeResponse(204)

        monkeypatch.setattr("notifier.urlopen", fake_urlopen)
        n = WebhookNotifier({"url": "https://discord.com/api/webhooks/x", "format": "discord"})
        assert n.send(_alert()) is True
        assert json.loads(captured["data"]) == {"content": "Freezer too warm: -65 °C"}

    def test_generic_payload(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["data"] = req.data
            return FakeResponse(200)

        monkeypatch.setattr("notifier.urlopen", fake_urlopen)
        n = WebhookNotifier({"url": "https://example.com/hook"})
        assert n.send(_alert()) is True
        payload = json.loads(captured["data"])
        assert payload["sensor"] == "freezer.temperature"
        assert payload["severity"] == "critical"


class TestEmailNotifier:
    def test_send_success(self, monkeypatch):
        captured = {}

        class FakeSMTP:
            def __init__(self, host, port, timeout):
                captured["host"] = host
                captured["port"] = port

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def starttls(self):
                captured["starttls"] = True

            def login(self, user, password):
                captured["login"] = (user, password)

            def send_message(self, msg):
                captured["msg"] = msg

        monkeypatch.setattr("notifier.smtplib.SMTP", FakeSMTP)
        n = EmailNotifier(
            {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "u@example.com",
                "from": "f@example.com",
                "recipients": ["a@example.com"],
            },
            password="pw",
        )
        assert n.send(_alert()) is True
        assert captured["starttls"] is True
        assert captured["login"] == ("u@example.com", "pw")
        assert captured["msg"]["Subject"] == "[CRITICAL] freezer.temperature"


class TestCreateNotifiers:
    def test_only_enabled(self):
        notifications = {
            "channels": [
                {"type": "ntfy", "enabled": True, "url": "https://ntfy.sh", "topic": "t"},
                {"type": "webhook", "enabled": False, "url": "https://x"},
            ]
        }
        notifiers = create_notifiers(notifications)
        assert len(notifiers) == 1
        assert isinstance(notifiers[0], NtfyNotifier)

    def test_email_included(self):
        mail = {
            "enabled": True,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "recipients": ["a@example.com"],
        }
        notifiers = create_notifiers({"channels": []}, mail=mail, smtp_password="pw")
        assert len(notifiers) == 1
        assert isinstance(notifiers[0], EmailNotifier)


def test_email_routing(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            captured["msg"] = msg

    monkeypatch.setattr("notifier.smtplib.SMTP", FakeSMTP)
    n = EmailNotifier(
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "recipients": ["a@example.com", "b@example.com"],
            "routing": {
                "critical": ["a@example.com", "b@example.com"],
                "warning": ["a@example.com"],
            },
        },
        password="pw",
    )
    alert = Alert(sensor="x", severity="warning", message="m")
    assert n.send(alert) is True
    assert captured["msg"]["To"] == "a@example.com"


def test_email_from_name(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            captured["msg"] = msg

    monkeypatch.setattr("notifier.smtplib.SMTP", FakeSMTP)
    n = EmailNotifier(
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "from_name": "ZOOLOGY-Observer Alert Engine",
            "recipients": ["a@example.com"],
        },
        password="pw",
    )
    alert = Alert(sensor="x", severity="critical", message="m")
    assert n.send(alert) is True
    assert captured["msg"]["From"] == "ZOOLOGY-Observer Alert Engine <f@example.com>"


def test_email_uses_subject_if_set(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            captured["msg"] = msg

    monkeypatch.setattr("notifier.smtplib.SMTP", FakeSMTP)
    n = EmailNotifier(
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "recipients": ["a@example.com"],
        },
        password="pw",
    )
    alert = Alert(
        sensor="atmoweb_101.temperature_1",
        severity="critical",
        message="m",
        subject="[CRITICAL] Temperature — R1304 / Memmert HPP260",
    )
    assert n.send(alert) is True
    assert captured["msg"]["Subject"] == "[CRITICAL] Temperature — R1304 / Memmert HPP260"


def test_email_falls_back_to_sensor(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            captured["msg"] = msg

    monkeypatch.setattr("notifier.smtplib.SMTP", FakeSMTP)
    n = EmailNotifier(
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "u@example.com",
            "from": "f@example.com",
            "recipients": ["a@example.com"],
        },
        password="pw",
    )
    alert = Alert(sensor="atmoweb_101.temperature_1", severity="critical", message="m")
    assert n.send(alert) is True
    assert captured["msg"]["Subject"] == "[CRITICAL] atmoweb_101.temperature_1"


def test_ntfy_uses_subject_if_set(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["title"] = req.get_header("Title")
        return FakeResponse(200)

    monkeypatch.setattr("notifier.urlopen", fake_urlopen)
    n = NtfyNotifier({"url": "https://ntfy.sh", "topic": "test"})
    alert = Alert(
        sensor="atmoweb_101.temperature_1",
        severity="critical",
        message="m",
        subject="[CRITICAL] Temperature — R1304 / Memmert HPP260",
    )
    assert n.send(alert) is True
    assert captured["title"] == "[CRITICAL] Temperature — R1304 / Memmert HPP260"


def test_ntfy_falls_back_to_sensor(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["title"] = req.get_header("Title")
        return FakeResponse(200)

    monkeypatch.setattr("notifier.urlopen", fake_urlopen)
    n = NtfyNotifier({"url": "https://ntfy.sh", "topic": "test"})
    alert = Alert(sensor="atmoweb_101.temperature_1", severity="critical", message="m")
    assert n.send(alert) is True
    assert captured["title"] == "CRITICAL: atmoweb_101.temperature_1"
