"""Daten-/Rechenfunktionen für das Dashboard."""

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dashboard_constants import BERLIN
from otterpi_store import BatchStore


def _calculate_average_series(
    batches: list[dict],
    sensor_keys: list[tuple[str, str, str]],
) -> list[dict]:
    """Berechnet eine Mittelwert-Reihe aus mehreren Sensoren pro Zeitpunkt."""
    series = []

    for batch in batches:
        batch_time = batch.get("created_at", "")
        measurements = batch.get("measurements", {})

        values = []
        for _, _, measurement_key in sensor_keys:
            measurement = measurements.get(measurement_key, {})
            value = measurement.get("value")
            if value is not None:
                values.append(value)

        if not values:
            continue

        avg_value = sum(values) / len(values)

        dt = datetime.fromisoformat(batch_time)
        if dt.tzinfo is not None:
            offset = dt.utcoffset()
            if offset is not None and offset.total_seconds() == 0:
                dt = dt.astimezone(BERLIN)

        label = dt.strftime("%H:%M")
        date = dt.strftime("%Y-%m-%d")
        series.append({"label": label, "date": date, "value": avg_value})

    return series


def _calculate_stats(
    temp_series: list[dict[str, Any]],
    hum_series: list[dict[str, Any]],
) -> dict[str, float]:
    """Berechnet Statistiken (Min/Max/Ø) für die Detailseiten."""
    stats = {
        "temp_min": 0.0,
        "temp_max": 0.0,
        "temp_avg": 0.0,
        "hum_min": 0.0,
        "hum_max": 0.0,
        "hum_avg": 0.0,
    }

    if temp_series:
        temp_values = [point["value"] for point in temp_series if point["value"] is not None]
        if temp_values:
            stats["temp_min"] = min(temp_values)
            stats["temp_max"] = max(temp_values)
            stats["temp_avg"] = sum(temp_values) / len(temp_values)

    if hum_series:
        hum_values = [point["value"] for point in hum_series if point["value"] is not None]
        if hum_values:
            stats["hum_min"] = min(hum_values)
            stats["hum_max"] = max(hum_values)
            stats["hum_avg"] = sum(hum_values) / len(hum_values)

    return stats


def _room_climate(batches: list[dict], room: dict) -> dict:
    """Berechnet Raumtemperatur und -feuchte aus den WeatherHub-Sensoren."""
    temps = []
    hums = []

    if not batches:
        return {"temp": None, "hum": None}

    latest = batches[-1]
    measurements = latest.get("measurements", {})

    for device in room["devices"]:
        if device.get("type") == "weatherhub_id01":
            key = device["key"]
            temp = measurements.get(f"{key}.temperature_1", {})
            if temp.get("value") is not None:
                temps.append(temp["value"])

    for sensor_key in room.get("weatherhub_climate", []):
        temp = measurements.get(f"{sensor_key}.temperature", {})
        if temp.get("value") is not None:
            temps.append(temp["value"])

        hum = measurements.get(f"{sensor_key}.humidity", {})
        if hum.get("value") is not None:
            hums.append(hum["value"])

    result = {"temp": None, "hum": None}

    if temps:
        result["temp"] = sum(temps) / len(temps)

    if hums:
        result["hum"] = sum(hums) / len(hums)

    return result


def _recent_batches(
    store: BatchStore,
    hours: int = 48,
    limit: Optional[int] = None,
) -> list[dict]:
    """Liest die letzten Batches aus SQLite."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    if limit is None:
        limit = 192

    with sqlite3.connect(store.path) as conn:
        rows = conn.execute(
            "SELECT payload, received_at FROM batches ORDER BY rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()

    batches = []
    for payload, received_at in rows:
        data = json.loads(payload)
        created_at = data.get("created_at", "")

        if created_at >= cutoff:
            data["_received_at"] = received_at or created_at
            batches.append(data)

    batches.reverse()
    return batches


def _current_values(batches: list[dict]) -> dict:
    """Ermittelt die aktuellen Werte aus dem letzten Batch."""
    current = {
        "temp_101": 0.0,
        "hum_101": 0.0,
        "temp_102": 0.0,
        "hum_102": 0.0,
        "temp_freezer": 0.0,
        "temp_memmert_links": 0.0,
        "temp_memmert_rechts": 0.0,
        "last_batch": "–",
        "cpu_temp": 0.0,
        "memory_used": 0.0,
    }

    if not batches:
        return current

    latest = batches[-1]

    current["last_batch"] = (
        datetime.fromisoformat(latest["created_at"])
        .astimezone(BERLIN)
        .strftime("%d.%m.%Y %H:%M Uhr")
    )

    measurements = latest.get("measurements", {})

    temp_101 = measurements.get("atmoweb_101.temperature_1", {})
    hum_101 = measurements.get("atmoweb_101.humidity", {})
    temp_102 = measurements.get("atmoweb_102.temperature_1", {})
    hum_102 = measurements.get("atmoweb_102.humidity", {})
    temp_freezer = measurements.get("freezer.temperature", {})
    temp_memmert_links = measurements.get("memmert_ipp300_links.temperature", {})
    temp_memmert_rechts = measurements.get("memmert_ipp300_rechts.temperature", {})

    if temp_101.get("value") is not None:
        current["temp_101"] = temp_101["value"]
    if hum_101.get("value") is not None:
        current["hum_101"] = hum_101["value"]
    if temp_102.get("value") is not None:
        current["temp_102"] = temp_102["value"]
    if hum_102.get("value") is not None:
        current["hum_102"] = hum_102["value"]
    if temp_freezer.get("value") is not None:
        current["temp_freezer"] = temp_freezer["value"]
    if temp_memmert_links.get("value") is not None:
        current["temp_memmert_links"] = temp_memmert_links["value"]
    if temp_memmert_rechts.get("value") is not None:
        current["temp_memmert_rechts"] = temp_memmert_rechts["value"]

    system = latest.get("system", {})
    cpu = system.get("cpu", {})
    if cpu.get("temperature_celsius") is not None:
        current["cpu_temp"] = cpu["temperature_celsius"]

    memory = latest.get("memory", {})
    if memory.get("total_bytes") and memory.get("used_bytes"):
        current["memory_used"] = memory["used_bytes"] / memory["total_bytes"] * 100

    return current


def _device_current(batches: list[dict], key: str, device_type: str = "atmoweb") -> dict:
    """Ermittelt aktuelle Werte + Status für ein Gerät."""
    result = {
        "temp": 0.0,
        "hum": 0.0,
        "value": "–",
        "status": "lamp-off",
    }

    if not batches:
        return result

    latest = batches[-1]
    measurements = latest.get("measurements", {})

    if device_type == "placeholder":
        return result

    if device_type in ("freezer", "memmert"):
        temp = measurements.get(f"{key}.temperature", {})
        if temp.get("value") is not None:
            result["temp"] = temp["value"]
            result["value"] = f"{temp['value']:.1f} °C"

        if result["temp"] != 0.0:
            result["status"] = "lamp-ok"

        return result

    if device_type == "weatherhub_id01":
        temp = measurements.get(f"{key}.temperature_2", {})
        if temp.get("value") is not None:
            result["temp"] = temp["value"]
            result["value"] = f"{temp['value']:.1f} °C"

        if result["temp"] != 0.0:
            result["status"] = "lamp-ok"

        return result

    if device_type == "weatherhub_id0e":
        temp = measurements.get(f"{key}.temperature", {})
        hum = measurements.get(f"{key}.humidity", {})

        if temp.get("value") is not None:
            result["temp"] = temp["value"]
            result["value"] = f"{temp['value']:.1f} °C"

        if hum.get("value") is not None:
            result["hum"] = hum["value"]

        if result["temp"] > 0 or result["hum"] > 0:
            result["status"] = "lamp-ok"

        return result

    temp = measurements.get(f"{key}.temperature_1", {})
    hum = measurements.get(f"{key}.humidity", {})

    if temp.get("value") is not None:
        result["temp"] = temp["value"]
        result["value"] = f"{temp['value']:.1f} °C"

    if hum.get("value") is not None:
        result["hum"] = hum["value"]

    if result["temp"] > 0 or result["hum"] > 0:
        result["status"] = "lamp-ok"

    return result


def _device_status(batches: list[dict], key: str, device_type: str = "atmoweb") -> str:
    """Ermittelt den erweiterten Status für die Gerätekachel."""
    if not batches:
        return "status-off"

    if device_type == "placeholder":
        return "status-off"

    latest = batches[-1]
    measurements = latest.get("measurements", {})
    states = latest.get("states", {}).get(key, {})

    if states.get("alarms"):
        return "status-critical"

    limits = _device_limits(key)
    limit_status = _limit_status(measurements, limits, batches)
    if limit_status == "status-critical":
        return "status-critical"

    if device_type in ("freezer", "memmert", "weatherhub_id01", "weatherhub_id0e"):
        if device_type in ("freezer", "memmert"):
            measurement_key = f"{key}.temperature"
        elif device_type == "weatherhub_id01":
            measurement_key = f"{key}.temperature_2"
        else:
            measurement_key = f"{key}.temperature"

        temp = measurements.get(measurement_key, {})
        validity = temp.get("validity")

        if validity == "invalid":
            return "status-critical"
        if validity == "stale":
            return "status-warn"
        if validity == "valid":
            if states.get("battery_low"):
                return "status-warn"
            if limit_status == "status-warn":
                return "status-warn"
            return "status-ok"
        return "status-off"

    temp = measurements.get(f"{key}.temperature_1", {})
    hum = measurements.get(f"{key}.humidity", {})
    validities = {temp.get("validity"), hum.get("validity")}

    if "invalid" in validities:
        return "status-critical"
    if validities <= {"valid", "stale"} and len(validities) == 1:
        if "stale" in validities:
            return "status-warn"
        if states.get("battery_low"):
            return "status-warn"
        if limit_status == "status-warn":
            return "status-warn"
        return "status-ok"
    if temp.get("value") is not None or hum.get("value") is not None:
        return "status-warn"
    return "status-off"


def _series(batches: list[dict], key: str, max_points: int = 500) -> list[dict]:
    """Extrahiert eine Messwert-Reihe aus den Batches.

    Bei mehr als ``max_points`` Punkten wird auf ``max_points``
    heruntergebrochen (Durchschnitt pro Bucket).
    """
    series = []
    for batch in batches:
        measurement = batch.get("measurements", {}).get(key, {})
        value = measurement.get("value")
        measured_at = measurement.get("measured_at")

        if value is not None and measured_at:
            dt = datetime.fromisoformat(measured_at)

            if dt.tzinfo is not None:
                offset = dt.utcoffset()
                if offset is not None and offset.total_seconds() == 0:
                    dt = dt.astimezone(BERLIN)

            label = dt.strftime("%H:%M")
            date = dt.strftime("%Y-%m-%d")
            series.append({"label": label, "date": date, "value": value})

    if len(series) > max_points:
        step = len(series) / max_points
        downsampled = []
        for i in range(max_points):
            start = int(i * step)
            end = int((i + 1) * step)
            chunk = series[start:end]
            if not chunk:
                continue
            avg = sum(p["value"] for p in chunk) / len(chunk)
            downsampled.append(
                {
                    "label": chunk[0]["label"],
                    "date": chunk[0]["date"],
                    "value": avg,
                }
            )
        series = downsampled

    return series


def _latest_batch(batches: list[dict]) -> dict:
    return batches[-1] if batches else {}


def _latest_states(batches: list[dict], device_key: str) -> dict:
    latest = _latest_batch(batches)
    return latest.get("states", {}).get(device_key, {})


def _latest_setpoints(batches: list[dict], device_key: str) -> dict:
    latest = _latest_batch(batches)
    return latest.get("setpoints", {}).get(device_key, {})


def _latest_device(batches: list[dict], device_key: str) -> dict:
    latest = _latest_batch(batches)
    return latest.get("device", {}).get(device_key, {})


def _latest_serial(batches: list[dict]) -> dict:
    latest = _latest_batch(batches)
    return latest.get("serial", {})


_alarm_limits_cache = {"mtime": None, "data": None}


def _load_alarm_limits_cached() -> dict:
    """Lädt alarm_limits.json mit mtime-Cache."""
    config_dir = os.environ.get(
        "OTTERPI_CONFIG_DIR",
        "/var/lib/loggerpi-otterpi/config",
    )
    path = Path(config_dir) / "alarm_limits.json"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}
    if _alarm_limits_cache["mtime"] == mtime and _alarm_limits_cache["data"] is not None:
        return _alarm_limits_cache["data"]
    try:
        from config_store import load_alarm_limits

        data = load_alarm_limits()
    except Exception:
        return {}
    _alarm_limits_cache["mtime"] = mtime
    _alarm_limits_cache["data"] = data
    return data


def _device_limits(device_key: str) -> dict:
    """Liest die Limits für ein Gerät aus alarm_limits.json.

    Gibt ein Dict ``{full_key: limits}`` zurück (z.B.
    ``{"atmoweb_101.temperature_1": {"warning_min": 22, ...}}``).
    Leeres Dict, wenn keine Limits gesetzt sind.
    """
    data = _load_alarm_limits_cached()
    sensors = data.get("sensors", {})
    result = {}
    for key, limits in sensors.items():
        if key.startswith(device_key + "."):
            result[key] = limits
    return result


def _limit_status(measurements: dict, limits: dict, batches: Optional[list[dict]] = None) -> str:
    """Prüft Limit-Verletzungen.

    Gibt ``"status-critical"``, ``"status-warn"`` oder ``""`` zurück.
    """
    for key, limit in limits.items():
        if not limit.get("enabled", True):
            continue
        measurement = measurements.get(key, {})
        value = measurement.get("value")
        if value is None:
            continue
        if "critical_min" in limit and value < limit["critical_min"]:
            return "status-critical"
        if "critical_max" in limit and value > limit["critical_max"]:
            return "status-critical"
        if "warning_min" in limit and value < limit["warning_min"]:
            return "status-warn"
        if "warning_max" in limit and value > limit["warning_max"]:
            return "status-warn"
        rate_limit = limit.get("rate_of_change_max_per_hour")
        if rate_limit is not None and batches is not None:
            rate = _calculate_rate_of_change(batches, key)
            if rate is not None and abs(rate) > rate_limit:
                return "status-warn"
    return ""


def _calculate_rate_of_change(batches: list[dict], measurement_key: str) -> Optional[float]:
    """Berechnet die Rate of Change (pro Stunde) aus den Batches.

    Verwendet alle Batches (erster und letzter Wert), wie die Alert-Engine.
    """
    values = []
    for batch in batches:
        measurement = batch.get("measurements", {}).get(measurement_key, {})
        value = measurement.get("value")
        created_at = batch.get("created_at")
        if value is not None and created_at:
            values.append((created_at, value))
    if len(values) < 2:
        return None
    first_time, first_value = values[0]
    last_time, last_value = values[-1]
    dt = datetime.fromisoformat(last_time) - datetime.fromisoformat(first_time)
    hours = dt.total_seconds() / 3600
    if hours <= 0:
        return None
    return (last_value - first_value) / hours


_ALARM_LABELS = {
    "temperature_below_low_alarm": "Undertemperature",
    "temperature_above_high_alarm": "Overtemperature",
    "ac_power_failure": "Power failure",
    "control_probe_fault": "Control probe fault",
    "microprocessor_fault": "Microprocessor fault",
    "heat_exchanger_fault": "Heat exchanger fault",
    "hot_condenser": "Hot condenser",
}


def _primary_measurement(measurements: dict, key: str, device_type: str) -> dict:
    if device_type in ("freezer", "memmert"):
        return measurements.get(f"{key}.temperature", {})
    if device_type == "weatherhub_id01":
        return measurements.get(f"{key}.temperature_2", {})
    if device_type == "weatherhub_id0e":
        return measurements.get(f"{key}.temperature", {})
    return measurements.get(f"{key}.temperature_1", {})


def _invalid_reason(measurements: dict, key: str, device_type: str) -> Optional[str]:
    return _primary_measurement(measurements, key, device_type).get("validity_reason")


def _stale_age(measurements: dict, key: str, device_type: str) -> Optional[str]:
    measured_at = _primary_measurement(measurements, key, device_type).get("measured_at")
    if not measured_at:
        return None
    dt = datetime.fromisoformat(measured_at)
    age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
    minutes = int(age_seconds // 60)
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    return f"{hours} h"


def _device_chips(
    batches: list[dict], key: str, device_type: str = "atmoweb"
) -> list[tuple[str, str]]:
    """Liefert die Chips (Text, CSS-Klasse) für ein Gerät."""
    if not batches or device_type == "placeholder":
        return []

    latest = batches[-1]
    measurements = latest.get("measurements", {})
    states = latest.get("states", {}).get(key, {})
    operation = latest.get("operation", {}).get(key, {})
    chips: list[tuple[str, str]] = []

    limits = _device_limits(key)
    for limit_key, limit in limits.items():
        if not limit.get("enabled", True):
            continue
        measurement = measurements.get(limit_key, {})
        value = measurement.get("value")
        if value is None:
            continue
        measurement_name = limit_key.split(".", 1)[1]
        display_name = {
            "temperature_1": "Temperature",
            "temperature_2": "Temperature",
            "temperature_3": "Temperature",
            "temperature_4": "Temperature",
            "temperature": "Temperature",
            "humidity": "Humidity",
            "vacuum": "Vacuum",
            "co2": "CO₂",
            "o2": "O₂",
            "fan_speed": "Fan Speed",
        }.get(measurement_name, measurement_name)
        if "critical_min" in limit and value < limit["critical_min"]:
            chips.append((f"⛔ {display_name} below limit", "chip-critical"))
        if "critical_max" in limit and value > limit["critical_max"]:
            chips.append((f"⛔ {display_name} above limit", "chip-critical"))
        if "warning_min" in limit and value < limit["warning_min"]:
            chips.append((f"⚠ {display_name} below limit", "chip-warn"))
        if "warning_max" in limit and value > limit["warning_max"]:
            chips.append((f"⚠ {display_name} above limit", "chip-warn"))
        rate_limit = limit.get("rate_of_change_max_per_hour")
        if rate_limit is not None:
            rate = _calculate_rate_of_change(batches, limit_key)
            if rate is not None and abs(rate) > rate_limit:
                chips.append((f"⚠ {display_name} rate of change above limit", "chip-warn"))

    alarms = states.get("alarms") or []
    for alarm in alarms:
        label = _ALARM_LABELS.get(alarm, alarm)
        chips.append((f"🚨 Alarm: {label}", "chip-critical"))

    status = _device_status(batches, key, device_type)

    if status == "status-critical" and not alarms:
        reason = _invalid_reason(measurements, key, device_type)
        if reason == "overflow":
            chips.append(("⛔ Sensor overflow", "chip-critical"))
        elif reason == "sensor_error":
            chips.append(("⛔ Sensor error", "chip-critical"))
        else:
            chips.append(("⛔ Invalid", "chip-critical"))
    elif status == "status-warn":
        if states.get("battery_low"):
            chips.append(("⚠ Battery low", "chip-warn"))
        else:
            primary = _primary_measurement(measurements, key, device_type)
            if primary.get("validity") == "stale":
                age = _stale_age(measurements, key, device_type)
                if age is not None:
                    chips.append((f"⚠ No data for {age}", "chip-warn"))
                else:
                    chips.append(("⚠ Stale", "chip-warn"))
    elif status == "status-ok":
        chips.append(("OK", "chip-ok"))
    elif status == "status-off":
        chips.append(("Offline", "chip-off"))

    if states.get("door_open"):
        chips.append(("Door open", "chip-info"))
    if states.get("door_locked"):
        chips.append(("Door locked", "chip-info"))
    if states.get("defrost"):
        chips.append(("Defrost", "chip-info"))
    if "flap" in states:
        chips.append((f"Flap {states['flap']:.0f}%", "chip-info"))
    if "mode" in operation:
        chips.append((f"Mode: {operation['mode']}", "chip-info"))
    if "operation_mode" in states:
        mode = "local" if states["operation_mode"] == 0 else "remote"
        chips.append((f"Mode: {mode}", "chip-info"))

    return chips


def _led_value(batches: list[dict], key: str) -> Optional[float]:
    if not batches:
        return None
    states = batches[-1].get("states", {}).get(key, {})
    lights = states.get("lights", {})
    if isinstance(lights, dict) and "led" in lights:
        return lights["led"]
    return None
