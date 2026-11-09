"""Notifier für Alerts (E-Mail, ntfy, Webhook).

Reine Standardbibliothek: smtplib, urllib.request, json.
"""

import json
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Alert:
    sensor: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    rule: Optional[str] = None
    dedup_key: Optional[str] = None
    subject: Optional[str] = None


class EmailNotifier:
    def __init__(self, config: dict, password: str) -> None:
        self.host = config["smtp_host"]
        self.port = config["smtp_port"]
        self.user = config["smtp_user"]
        self.from_addr = config["from"]
        self.from_name = config.get("from_name", "")
        self.recipients = config["recipients"]
        self.routing = config.get("routing", {})
        self.password = password

    def send(self, alert: Alert) -> bool:
        recipients = self.routing.get(alert.severity, self.recipients)
        if not recipients:
            return False
        msg = EmailMessage()
        msg["Subject"] = alert.subject or f"[{alert.severity.upper()}] {alert.sensor}"
        if self.from_name:
            msg["From"] = f"{self.from_name} <{self.from_addr}>"
        else:
            msg["From"] = self.from_addr
        msg["To"] = ", ".join(recipients)
        msg.set_content(alert.message)
        try:
            if self.port == 465:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as smtp:
                    smtp.login(self.user, self.password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(self.user, self.password)
                    smtp.send_message(msg)
            return True
        except Exception:
            return False


class NtfyNotifier:
    def __init__(self, config: dict) -> None:
        self.url = config["url"].rstrip("/")
        self.topic = config["topic"]
        self.token = config.get("token")

    def send(self, alert: Alert) -> bool:
        headers = {"Title": alert.subject or f"{alert.severity.upper()}: {alert.sensor}"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(
            f"{self.url}/{self.topic}",
            data=alert.message.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False


class WebhookNotifier:
    def __init__(self, config: dict) -> None:
        self.url = config["url"]
        self.format = config.get("format", "generic")

    def send(self, alert: Alert) -> bool:
        if self.format == "discord":
            payload = {"content": alert.message}
        elif self.format == "slack":
            payload = {"text": alert.message}
        else:
            payload = {
                "sensor": alert.sensor,
                "severity": alert.severity,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
            }
        req = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False


def create_notifiers(
    notifications: dict,
    mail: Optional[dict] = None,
    smtp_password: Optional[str] = None,
) -> list:
    notifiers = []
    if mail and mail.get("enabled", True) and smtp_password:
        notifiers.append(EmailNotifier(mail, smtp_password))
    for channel in notifications.get("channels", []):
        if not channel.get("enabled", False):
            continue
        ctype = channel.get("type")
        if ctype == "ntfy":
            notifiers.append(NtfyNotifier(channel))
        elif ctype == "webhook":
            notifiers.append(WebhookNotifier(channel))
    return notifiers
