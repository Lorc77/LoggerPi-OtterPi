"""Daten-/Rechenfunktionen für das Dashboard."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
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
            "SELECT payload FROM batches ORDER BY rowid DESC LIMIT ?",
            (limit,),
        ).fetchall()

    batches = []
    for (payload,) in rows:
        data = json.loads(payload)
        created_at = data.get("created_at", "")

        if created_at >= cutoff:
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

    measurements = batches[-1].get("measurements", {})

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
        if validity == "valid":
            return "status-ok"
        if validity == "stale":
            return "status-warn"
        return "status-off"

    temp = measurements.get(f"{key}.temperature_1", {})
    hum = measurements.get(f"{key}.humidity", {})
    validities = {temp.get("validity"), hum.get("validity")}

    if "invalid" in validities:
        return "status-critical"
    if validities <= {"valid", "stale"} and len(validities) == 1:
        return "status-warn" if "stale" in validities else "status-ok"
    if temp.get("value") is not None or hum.get("value") is not None:
        return "status-warn"
    return "status-off"


def _series(batches: list[dict], key: str) -> list[dict]:
    """Extrahiert eine Messwert-Reihe aus den Batches."""
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

    return series
