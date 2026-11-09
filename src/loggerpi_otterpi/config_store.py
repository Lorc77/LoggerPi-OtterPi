"""JSON-Config-Verwaltung für den OtterPi Admin.

Liest/schreibt rooms.json, alarm_limits.json, mail.json, notifications.json.
Validierung → .bak → atomar (temp + replace).
"""

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


class ConfigValidationError(ValueError):
    """Fehler bei der Validierung einer Config-Datei."""


_ROOM_KEY_RE = re.compile(r"^[a-z0-9_]+$")
_SENSOR_KEY_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

_ALLOWED_LIMIT_KEYS = {
    "warning_min",
    "warning_max",
    "critical_min",
    "critical_max",
    "rate_of_change_max_per_hour",
    "stale_after_seconds",
    "stale_enabled",
    "invalid_enabled",
    "enabled",
}

_ALLOWED_MAIL_KEYS = {
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "from",
    "from_name",
    "recipients",
    "routing",
    "dedup_seconds",
    "quiet_hours",
    "enabled",
}

_ALLOWED_NOTIFICATION_TYPES = {"ntfy", "webhook"}

_DEFAULT_MESSAGES = {
    "critical_max": "too high",
    "critical_min": "too low",
    "warning_max": "too high",
    "warning_min": "too low",
    "rate_of_change": "rate of change too high",
    "invalid": "invalid",
    "stale": "stale",
    "battery_low": "low",
    "door_open": "open",
    "contact_open": "open",
    "alarm": "alarm",
    "loggerpi_offline": "offline",
}

_ALLOWED_MESSAGE_KEYS = set(_DEFAULT_MESSAGES)


def _config_dir() -> Path:
    return Path(os.environ.get("OTTERPI_CONFIG_DIR", "/var/lib/loggerpi-otterpi/config"))


def _path(name: str) -> Path:
    return _config_dir() / name


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigValidationError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigValidationError(f"Invalid JSON in {path}: {exc}") from exc


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.parent / (path.name + ".bak"))
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _validate_rooms(data: Any) -> None:
    if not isinstance(data, dict):
        raise ConfigValidationError("rooms.json must be an object.")
    rooms = data.get("rooms")
    if not isinstance(rooms, dict) or not rooms:
        raise ConfigValidationError("rooms.json must contain a non-empty 'rooms' object.")

    seen_keys: set[str] = set()
    for room_id, room in rooms.items():
        if not isinstance(room_id, str) or not _ROOM_KEY_RE.match(room_id):
            raise ConfigValidationError(f"Invalid room id: {room_id!r}")
        if not isinstance(room, dict):
            raise ConfigValidationError(f"Room {room_id!r} must be an object.")
        name = room.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigValidationError(f"Room {room_id!r} requires a non-empty 'name'.")
        icon = room.get("icon")
        if icon is not None and not isinstance(icon, str):
            raise ConfigValidationError(f"Room {room_id!r} 'icon' must be a string.")
        devices = room.get("devices", [])
        if not isinstance(devices, list):
            raise ConfigValidationError(f"Room {room_id!r} 'devices' must be a list.")
        for device in devices:
            if not isinstance(device, dict):
                raise ConfigValidationError(f"Room {room_id!r} device must be an object.")
            dname = device.get("name")
            dkey = device.get("key")
            dtype = device.get("type")
            if not isinstance(dname, str) or not dname.strip():
                raise ConfigValidationError(f"Room {room_id!r} device requires 'name'.")
            if not isinstance(dkey, str) or not _ROOM_KEY_RE.match(dkey):
                raise ConfigValidationError(f"Room {room_id!r} device has invalid 'key': {dkey!r}")
            if not isinstance(dtype, str) or not dtype.strip():
                raise ConfigValidationError(f"Room {room_id!r} device requires 'type'.")
            if dkey in seen_keys:
                raise ConfigValidationError(f"Duplicate device key: {dkey!r}")
            seen_keys.add(dkey)
        climate = room.get("weatherhub_climate", [])
        if not isinstance(climate, list) or not all(isinstance(k, str) for k in climate):
            raise ConfigValidationError(
                f"Room {room_id!r} 'weatherhub_climate' must be a list of strings."
            )


def _validate_alarm_limits(data: Any) -> None:
    if not isinstance(data, dict):
        raise ConfigValidationError("alarm_limits.json must be an object.")

    system = data.get("system")
    if system is not None:
        if not isinstance(system, dict):
            raise ConfigValidationError("alarm_limits.json 'system' must be an object.")
        allowed = {
            "loggerpi_offline_warning_seconds",
            "loggerpi_offline_critical_seconds",
            "loggerpi_offline_warning_alert_enabled",
        }
        unknown = set(system) - allowed
        if unknown:
            raise ConfigValidationError(
                f"alarm_limits.json 'system' has unknown fields: {sorted(unknown)}"
            )
        for name in (
            "loggerpi_offline_warning_seconds",
            "loggerpi_offline_critical_seconds",
        ):
            if name in system:
                value = system[name]
                if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                    raise ConfigValidationError(
                        f"alarm_limits.json 'system.{name}' must be a positive integer."
                    )
        if "loggerpi_offline_warning_alert_enabled" in system:
            if not isinstance(system["loggerpi_offline_warning_alert_enabled"], bool):
                raise ConfigValidationError(
                    "alarm_limits.json 'system.loggerpi_offline_warning_alert_enabled' "
                    "must be a boolean."
                )
        warning = system.get("loggerpi_offline_warning_seconds")
        critical = system.get("loggerpi_offline_critical_seconds")
        if warning is not None and critical is not None and warning >= critical:
            raise ConfigValidationError(
                "alarm_limits.json 'system.loggerpi_offline_warning_seconds' "
                "must be < 'system.loggerpi_offline_critical_seconds'."
            )

    sensors = data.get("sensors")
    if not isinstance(sensors, dict):
        raise ConfigValidationError("alarm_limits.json must contain a 'sensors' object.")

    for sensor_key, limits in sensors.items():
        if not isinstance(sensor_key, str) or not _SENSOR_KEY_RE.match(sensor_key):
            raise ConfigValidationError(f"Invalid sensor key: {sensor_key!r}")
        if not isinstance(limits, dict):
            raise ConfigValidationError(f"Sensor {sensor_key!r} must be an object.")
        unknown = set(limits) - _ALLOWED_LIMIT_KEYS
        if unknown:
            raise ConfigValidationError(
                f"Sensor {sensor_key!r} has unknown fields: {sorted(unknown)}"
            )
        for field in ("warning_min", "warning_max", "critical_min", "critical_max"):
            if field in limits and not isinstance(limits[field], (int, float)):
                raise ConfigValidationError(f"Sensor {sensor_key!r} '{field}' must be a number.")
        if "rate_of_change_max_per_hour" in limits:
            v = limits["rate_of_change_max_per_hour"]
            if not isinstance(v, (int, float)) or v <= 0:
                raise ConfigValidationError(
                    f"Sensor {sensor_key!r} 'rate_of_change_max_per_hour' must be > 0."
                )
        if "stale_after_seconds" in limits:
            v = limits["stale_after_seconds"]
            if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
                raise ConfigValidationError(
                    f"Sensor {sensor_key!r} 'stale_after_seconds' must be a positive integer."
                )
        if "enabled" in limits and not isinstance(limits["enabled"], bool):
            raise ConfigValidationError(f"Sensor {sensor_key!r} 'enabled' must be a boolean.")
        for field in ("stale_enabled", "invalid_enabled"):
            if field in limits and not isinstance(limits[field], bool):
                raise ConfigValidationError(f"Sensor {sensor_key!r} '{field}' must be a boolean.")

        cmin = limits.get("critical_min")
        wmin = limits.get("warning_min")
        wmax = limits.get("warning_max")
        cmax = limits.get("critical_max")
        if cmin is not None and wmin is not None and cmin > wmin:
            raise ConfigValidationError(f"Sensor {sensor_key!r}: critical_min > warning_min.")
        if wmin is not None and wmax is not None and wmin > wmax:
            raise ConfigValidationError(f"Sensor {sensor_key!r}: warning_min > warning_max.")
        if wmax is not None and cmax is not None and wmax > cmax:
            raise ConfigValidationError(f"Sensor {sensor_key!r}: warning_max > critical_max.")

    states = data.get("states")
    if states is not None:
        if not isinstance(states, dict):
            raise ConfigValidationError("alarm_limits.json 'states' must be an object.")
        for state_key, rule in states.items():
            if not isinstance(state_key, str) or not _SENSOR_KEY_RE.match(state_key):
                raise ConfigValidationError(f"Invalid state key: {state_key!r}")
            if not isinstance(rule, dict):
                raise ConfigValidationError(f"State {state_key!r} must be an object.")
            if not isinstance(rule.get("enabled"), bool):
                raise ConfigValidationError(f"State {state_key!r} requires boolean 'enabled'.")
            if "max_open_seconds" in rule:
                v = rule["max_open_seconds"]
                if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
                    raise ConfigValidationError(
                        f"State {state_key!r} 'max_open_seconds' must be a positive integer."
                    )

    device = data.get("device")
    if device is not None:
        if not isinstance(device, dict):
            raise ConfigValidationError("alarm_limits.json 'device' must be an object.")
        for device_key, rule in device.items():
            if not isinstance(device_key, str) or not _ROOM_KEY_RE.match(device_key):
                raise ConfigValidationError(f"Invalid device key: {device_key!r}")
            if not isinstance(rule, dict):
                raise ConfigValidationError(f"Device {device_key!r} must be an object.")
            for field in ("stale_enabled", "invalid_enabled"):
                if field in rule and not isinstance(rule[field], bool):
                    raise ConfigValidationError(
                        f"Device {device_key!r} '{field}' must be a boolean."
                    )


def _validate_mail(data: Any) -> None:
    if not isinstance(data, dict):
        raise ConfigValidationError("mail.json must be an object.")
    unknown = set(data) - _ALLOWED_MAIL_KEYS
    if unknown:
        raise ConfigValidationError(f"mail.json has unknown fields: {sorted(unknown)}")

    if "enabled" in data and not isinstance(data["enabled"], bool):
        raise ConfigValidationError("mail.json 'enabled' must be a boolean.")

    for field in ("smtp_host", "smtp_user", "from"):
        v = data.get(field)
        if not isinstance(v, str) or not v.strip():
            raise ConfigValidationError(f"mail.json requires a non-empty '{field}'.")
    if not _EMAIL_RE.match(data["from"]):
        raise ConfigValidationError("mail.json 'from' is not a valid email address.")
    if "from_name" in data and not isinstance(data["from_name"], str):
        raise ConfigValidationError("mail.json 'from_name' must be a string.")
    port = data.get("smtp_port")
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ConfigValidationError("mail.json 'smtp_port' must be an integer 1-65535.")
    recipients = data.get("recipients")
    if not isinstance(recipients, list) or not recipients:
        raise ConfigValidationError("mail.json 'recipients' must be a non-empty list.")
    for r in recipients:
        if not isinstance(r, str) or not _EMAIL_RE.match(r):
            raise ConfigValidationError(f"Invalid recipient: {r!r}")
    routing = data.get("routing")
    if routing is not None:
        if not isinstance(routing, dict):
            raise ConfigValidationError("mail.json 'routing' must be an object.")
        for sev in ("critical", "warning"):
            if sev in routing:
                lst = routing[sev]
                if not isinstance(lst, list) or not all(
                    isinstance(x, str) and _EMAIL_RE.match(x) for x in lst
                ):
                    raise ConfigValidationError(
                        f"mail.json 'routing.{sev}' must be a list of emails."
                    )
                if not set(lst) <= set(recipients):
                    raise ConfigValidationError(
                        f"mail.json 'routing.{sev}' must be a subset of recipients."
                    )
    dedup = data.get("dedup_seconds")
    if dedup is not None:
        if not isinstance(dedup, int) or isinstance(dedup, bool) or dedup < 0:
            raise ConfigValidationError("mail.json 'dedup_seconds' must be an integer >= 0.")
    qh = data.get("quiet_hours")
    if qh is not None:
        if not isinstance(qh, dict):
            raise ConfigValidationError("mail.json 'quiet_hours' must be an object.")
        for field in ("start", "end"):
            v = qh.get(field)
            if not isinstance(v, str) or not _TIME_RE.match(v):
                raise ConfigValidationError(f"mail.json 'quiet_hours.{field}' must be HH:MM.")
        if "critical_always" in qh and not isinstance(qh["critical_always"], bool):
            raise ConfigValidationError(
                "mail.json 'quiet_hours.critical_always' must be a boolean."
            )


def _validate_notifications(data: Any) -> None:
    if not isinstance(data, dict):
        raise ConfigValidationError("notifications.json must be an object.")
    channels = data.get("channels")
    if not isinstance(channels, list):
        raise ConfigValidationError("notifications.json must contain a 'channels' list.")
    for i, channel in enumerate(channels):
        if not isinstance(channel, dict):
            raise ConfigValidationError(f"Channel {i} must be an object.")
        ctype = channel.get("type")
        if ctype not in _ALLOWED_NOTIFICATION_TYPES:
            raise ConfigValidationError(f"Channel {i} has invalid type: {ctype!r}")
        if not isinstance(channel.get("enabled"), bool):
            raise ConfigValidationError(f"Channel {i} requires boolean 'enabled'.")
        severities = channel.get("severities")
        if severities is not None:
            if not isinstance(severities, list) or not all(
                s in {"critical", "warning"} for s in severities
            ):
                raise ConfigValidationError(
                    f"Channel {i} 'severities' must be a list of 'critical' and/or 'warning'."
                )
        if ctype == "ntfy":
            if not isinstance(channel.get("url"), str) or not channel["url"].strip():
                raise ConfigValidationError(f"Channel {i} (ntfy) requires 'url'.")
            if not isinstance(channel.get("topic"), str) or not channel["topic"].strip():
                raise ConfigValidationError(f"Channel {i} (ntfy) requires 'topic'.")
            token = channel.get("token")
            if token is not None and not isinstance(token, str):
                raise ConfigValidationError(f"Channel {i} (ntfy) 'token' must be a string or null.")
        elif ctype == "webhook":
            if not isinstance(channel.get("url"), str) or not channel["url"].strip():
                raise ConfigValidationError(f"Channel {i} (webhook) requires 'url'.")
            fmt = channel.get("format", "generic")
            if fmt not in {"generic", "discord", "slack"}:
                raise ConfigValidationError(f"Channel {i} (webhook) has invalid format: {fmt!r}")


def _validate_messages(data: Any) -> None:
    if not isinstance(data, dict):
        raise ConfigValidationError("messages.json must be an object.")
    unknown = set(data) - _ALLOWED_MESSAGE_KEYS
    if unknown:
        raise ConfigValidationError(f"messages.json has unknown fields: {sorted(unknown)}")
    for key, value in data.items():
        if not isinstance(value, str):
            raise ConfigValidationError(f"messages.json '{key}' must be a string.")
        if len(value) > 200:
            raise ConfigValidationError(f"messages.json '{key}' must be at most 200 characters.")


def load_rooms() -> dict:
    data = _read_json(_path("rooms.json"))
    _validate_rooms(data)
    return data["rooms"]


def save_rooms(rooms: dict) -> None:
    data = {"rooms": rooms}
    _validate_rooms(data)
    _write_json_atomic(_path("rooms.json"), data)


def load_alarm_limits() -> dict:
    data = _read_json(_path("alarm_limits.json"))
    _validate_alarm_limits(data)
    return data


def save_alarm_limits(data: dict) -> None:
    _validate_alarm_limits(data)
    _write_json_atomic(_path("alarm_limits.json"), data)


def load_mail() -> dict:
    data = _read_json(_path("mail.json"))
    _validate_mail(data)
    return data


def save_mail(data: dict) -> None:
    _validate_mail(data)
    _write_json_atomic(_path("mail.json"), data)


def load_notifications() -> dict:
    data = _read_json(_path("notifications.json"))
    _validate_notifications(data)
    return data


def save_notifications(data: dict) -> None:
    _validate_notifications(data)
    _write_json_atomic(_path("notifications.json"), data)


def load_messages() -> dict:
    path = _path("messages.json")
    if not path.exists():
        return dict(_DEFAULT_MESSAGES)
    data = _read_json(path)
    _validate_messages(data)
    # Fehlende Keys mit Defaults auffüllen
    merged = dict(_DEFAULT_MESSAGES)
    merged.update(data)
    return merged


def save_messages(data: dict) -> None:
    _validate_messages(data)
    _write_json_atomic(_path("messages.json"), data)
