"""Dashboard für den OtterPi – Raum-basiert mit Geräte-Übersicht."""

import json
from datetime import datetime, timezone
from typing import Optional

from config_store import ConfigValidationError, load_alarm_limits
from dashboard_charts import (
    _render_device_script,
    _tooltip_date_logic,
    _tooltip_label_color,
)
from dashboard_config import get_rooms
from dashboard_constants import (
    BERLIN,
    HUMIDITY_COLORS,
    SENSOR_COLORS,
    TIME_RANGES,
    VERSION,
    VISIBLE_TIME_RANGES,
)
from dashboard_data import (
    _calculate_average_series,
    _calculate_stats,
    _current_values,
    _device_chips,
    _device_current,
    _device_limits,
    _device_status,
    _latest_device,
    _led_value,
    _recent_batches,
    _room_climate,
    _series,
)
from heartbeat import offline_status
from otterpi_store import BatchStore

_USB_NAMES = {
    ("0403", "6001"): "FTDI FT232R",
    ("067b", "2303"): "Prolific PL2303",
}


def _offline_thresholds() -> tuple[int, int]:
    """Liest die Offline-Schwellenwerte aus alarm_limits.json."""
    try:
        data = load_alarm_limits()
    except ConfigValidationError:
        return (1800, 3600)
    system = data.get("system", {})
    return (
        system.get("loggerpi_offline_warning_seconds", 1800),
        system.get("loggerpi_offline_critical_seconds", 3600),
    )


def render_dashboard(
    store: BatchStore,
    room_id: str = "",
    device_id: str = "",
    range_key: str = "7d",
    climate_id: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Generiert das Dashboard-HTML."""
    if climate_id:
        return _render_climate_detail(
            store,
            climate_id,
            range_key=range_key,
            start_date=start_date,
            end_date=end_date,
        )

    if device_id:
        return _render_device_detail(
            store,
            device_id,
            range_key=range_key,
            start_date=start_date,
            end_date=end_date,
        )

    rooms = get_rooms()
    if room_id and room_id in rooms:
        return _render_room_detail(store, room_id)

    return _render_overview(store)


def _status_text(status: str) -> str:
    """Wandelt einen Status in lesbaren Text um."""
    return {
        "status-ok": "OK",
        "status-warn": "STALE",
        "status-critical": "INVALID",
        "status-off": "OFFLINE",
    }.get(status, "UNKNOWN")


def _climate_display_text(climate: dict) -> str:
    """Erzeugt den Klima-Anzeigetext."""
    if climate["temp"] is None:
        return "–"

    text = f"🌡️ Room temperature: {climate['temp']:.1f} °C"
    if climate["hum"] is not None:
        text += f" · 💧 Relative Humidity: {climate['hum']:.1f} %"

    return text


def _render_led_svg(value: Optional[float]) -> str:
    if value is None:
        return ""
    css = "led-on" if value > 0 else "led-off"
    return f"""
    <span class="led-indicator {css}" title="LED {value:.0f}%">
        <svg width="36" height="36" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2 C9 2 5 5 5 9
                     C5 12 8 14 9 15.5
                     L15 15.5
                     C16 14 19 12 19 9
                     C19 5 15 2 12 2 Z"
                  fill="currentColor"/>
            <rect x="8.5" y="15.5" width="7" height="5" rx="0.8" fill="currentColor"/>
            <line x1="8.5" y1="17" x2="15.5" y2="17" stroke="#1f2937" stroke-width="0.4"/>
            <line x1="8.5" y1="18.5" x2="15.5" y2="18.5" stroke="#1f2937" stroke-width="0.4"/>
            <line x1="8.5" y1="20" x2="15.5" y2="20" stroke="#1f2937" stroke-width="0.4"/>
            <text x="12" y="10.5" text-anchor="middle" font-size="6" font-weight="bold"
                  fill="#1f2937">{value:.0f}%</text>
        </svg>
    </span>
    """


def _render_chips(chips: list[tuple[str, str]]) -> str:
    if not chips:
        return ""
    return "".join(f'<span class="chip {css}">{text}</span>' for text, css in chips)


def _render_limit_chips(limits: dict, full_key: str, unit: str, compact: bool = True) -> str:
    """Rendert die Limit-Chips für ein Measurement (rechtsbündig, übereinander)."""
    limit = limits.get(full_key, {})
    if not limit or not limit.get("enabled", True):
        return ""
    chips = []
    warn_min = limit.get("warning_min")
    warn_max = limit.get("warning_max")
    crit_min = limit.get("critical_min")
    crit_max = limit.get("critical_max")
    rate = limit.get("rate_of_change_max_per_hour")
    if warn_min is not None or warn_max is not None:
        text = ""
        if warn_min is not None:
            text += f"↓ {warn_min} {unit}"
        if warn_max is not None:
            text += f" ↑ {warn_max} {unit}"
        if not compact:
            text = f"Warning: {text.strip()}"
        chips.append((text.strip(), "chip-warn"))
    if crit_min is not None or crit_max is not None:
        text = ""
        if crit_min is not None:
            text += f"↓ {crit_min} {unit}"
        if crit_max is not None:
            text += f" ↑ {crit_max} {unit}"
        if not compact:
            text = f"Critical: {text.strip()}"
        chips.append((text.strip(), "chip-critical"))
    if rate is not None:
        text = f"Δ↕ {rate} {unit}/h"
        if not compact:
            text = f"Rate of Change: {text}"
        chips.append((text, "chip-info"))
    if not chips:
        return ""
    inner = "".join(f'<span class="chip {css}">{text}</span>' for text, css in chips)
    extra_class = "" if compact else " limit-chips-detailed"
    return f'<div class="limit-chips{extra_class}">{inner}</div>'


def _render_overview(store: BatchStore) -> str:
    """Einstiegsseite mit Raum-Kacheln."""
    batches = _recent_batches(store, hours=48)

    room_cards = ""
    rooms = get_rooms()
    last_update = "–"
    for room_id, room in rooms.items():
        has_devices = bool(room["devices"])

        # Raumklima berechnen
        climate = _room_climate(batches, room)

        climate_html = ""
        if climate["temp"] is not None:
            climate_html += f'<span class="room-climate">🌡️ {climate["temp"]:.1f} °C'
            if climate["hum"] is not None:
                climate_html += f" · 💧 {climate['hum']:.0f} %"
            climate_html += "</span>"

        if has_devices:
            device_lines = ""
            for device in room["devices"]:
                device_type = device.get("type", "atmoweb")
                current = _device_current(batches, device["key"], device_type)
                current["status"] = _device_status(batches, device["key"], device_type)
                device_lines += (
                    f'<div class="device-line">'
                    f'<span class="lamp {current["status"]}"></span>'
                    f"<span>{device['name']}</span>"
                    f'<span class="device-value">{current["value"]}</span>'
                    f"</div>"
                )

            card = (
                f'<a class="room-card" href="/room/{room_id}">'
                f'<h2 class="room-header">{room["icon"]} {room["name"]}{climate_html}</h2>'
                f'<div class="device-list">{device_lines}</div>'
                f"</a>"
            )
        else:
            card = (
                f'<div class="room-card room-card-empty">'
                f'<h2 class="room-header">{room["icon"]} {room["name"]}{climate_html}</h2>'
                f'<div class="device-list">'
                f'<div class="device-line no-devices">No devices</div>'
                f"</div>"
                f"</div>"
            )

        room_cards += card
        current = _current_values(batches)
        last_update = current["last_batch"]

    last_received = batches[-1].get("_received_at") if batches else None
    warning_seconds, critical_seconds = _offline_thresholds()
    status_class, status_text = offline_status(last_received, warning_seconds, critical_seconds)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📡 ZOOLOGY-Observer Dashboard</title>
<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    min-height: 100vh;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: linear-gradient(rgba(10,20,30,.55), rgba(10,20,30,.70)), url("/otter2.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: white;
    padding: 30px;
}}

.container {{
    width: min(1200px, 95%);
    margin: auto;
    background: rgba(20,35,50,.58);
    backdrop-filter: blur(6px);
    border-radius: 25px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}}

h1 {{ text-align: center; margin-top: 0; }}
.subtitle {{ text-align: center; color: #d1d5db; }}

.rooms-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-top: 30px;
}}

.room-card {{
    display: block;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
    text-decoration: none;
    color: white;
    transition: .2s;
}}

.room-card:hover {{
    background: rgba(147,197,253,.15);
    border-color: rgba(147,197,253,.5);
    transform: translateY(-2px);
}}

.room-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-top: 0;
    font-size: 1.1rem;
}}

.room-climate {{
    color: #d1d5db;
    font-size: .9rem;
    font-weight: normal;
    white-space: nowrap;
}}

.room-card-empty {{
    cursor: default;
    opacity: .7;
}}

.room-card-empty:hover {{
    background: rgba(31,41,55,.78);
    border-color: rgba(255,255,255,.08);
    transform: none;
}}

.device-list {{ margin-top: 12px; }}

.device-line {{
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 10px;
    align-items: center;
    margin: 6px 0;
    font-size: .9rem;
}}

.device-value {{ color: #d1d5db; }}

.no-devices {{ color: #6b7280; font-style: italic; }}

.lamp {{
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    box-shadow: 0 0 9px currentColor;
}}

.lamp.status-ok {{ color: #22c55e; background: #22c55e; }}
.lamp.status-warn {{ color: #eab308; background: #eab308; }}
.lamp.status-critical {{ color: #ef4444; background: #ef4444; }}
.lamp.status-off {{ color: #6b7280; background: #6b7280; box-shadow: none; }}

.footer {{
    text-align: center;
    margin-top: 30px;
    color: #d1d5db;
    opacity: .85;
    font-size: .9rem;
}}

@media(max-width:700px) {{
    body {{ padding: 15px; }}
    .container {{ width: 100%; padding: 20px; border-radius: 18px; }}
    .rooms-grid {{ grid-template-columns: 1fr; }}
    .room-header {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
</head>
<body>
<div class="container">
<h1>📡 ZOOLOGY-Observer Dashboard</h1>
<div class="subtitle">
    <span class="lamp {status_class}"></span> {status_text}
    · Last measurement: {last_update}
</div>

<div class="rooms-grid">
{room_cards}
</div>

<div class="footer">🦦 otterpi · ZOOLOGY-Observer Dashboard {VERSION}</div>
</div>
</body>
</html>
"""


def _render_room_detail(store: BatchStore, room_id: str) -> str:
    """Detailseite für einen Raum."""
    rooms = get_rooms()
    room = rooms[room_id]
    batches = _recent_batches(store, hours=48)

    current = _current_values(batches)

    # Raumklima berechnen
    climate = _room_climate(batches, room)

    climate_display = _climate_display_text(climate)
    climate_link = ""
    if climate["temp"] is not None:
        climate_link = f'<a class="climate-btn" href="/climate/{room_id}">{climate_display}</a>'
    else:
        climate_link = climate_display

    # Serien für bestehende Geräte
    temp_101 = _series(batches, "atmoweb_101.temperature_1")
    hum_101 = _series(batches, "atmoweb_101.humidity")
    temp_102 = _series(batches, "atmoweb_102.temperature_1")
    hum_102 = _series(batches, "atmoweb_102.humidity")
    temp_freezer = _series(batches, "freezer.temperature")
    temp_memmert_links = _series(batches, "memmert_ipp300_links.temperature")
    temp_memmert_rechts = _series(batches, "memmert_ipp300_rechts.temperature")

    series_by_device = {
        "atmoweb_101": (temp_101, hum_101),
        "atmoweb_102": (temp_102, hum_102),
        "freezer": (temp_freezer, []),
        "memmert_ipp300_links": (temp_memmert_links, []),
        "memmert_ipp300_rechts": (temp_memmert_rechts, []),
    }

    # WeatherHub-Serien dynamisch erzeugen
    for device in room["devices"]:
        device_type = device.get("type", "atmoweb")
        key = device["key"]

        if device_type == "weatherhub_id01":
            temp_series = _series(batches, f"{key}.temperature_2")
            series_by_device[key] = (temp_series, [])

        elif device_type == "weatherhub_id0e":
            temp_series = _series(batches, f"{key}.temperature")
            hum_series = _series(batches, f"{key}.humidity")
            series_by_device[key] = (temp_series, hum_series)

    device_views = []
    for device in room["devices"]:
        device_type = device.get("type", "atmoweb")
        temp_series, hum_series = series_by_device.get(device["key"], ([], []))
        device_current = _device_current(batches, device["key"], device_type)
        status = _device_status(batches, device["key"], device_type)
        chart_id = f"chart-{device['key'].replace('_', '-')}"
        limits = _device_limits(device["key"])
        if device_type in ("freezer", "memmert"):
            temp_key = f"{device['key']}.temperature"
            hum_key = None
        elif device_type == "weatherhub_id01":
            temp_key = f"{device['key']}.temperature_2"
            hum_key = None
        elif device_type == "weatherhub_id0e":
            temp_key = f"{device['key']}.temperature"
            hum_key = f"{device['key']}.humidity"
        else:  # atmoweb
            temp_key = f"{device['key']}.temperature_1"
            hum_key = f"{device['key']}.humidity"
        limit_chips_temp = _render_limit_chips(limits, temp_key, "°C")
        limit_chips_hum = _render_limit_chips(limits, hum_key, "%") if hum_key else ""

        limit_lines = []
        for limit_key, limit in limits.items():
            if not limit.get("enabled", True):
                continue
            if limit_key == temp_key:
                axis = "temperature"
            elif limit_key == hum_key:
                axis = "humidity"
            else:
                continue
            warning_color = "#fb923c" if axis == "temperature" else "#38bdf8"
            if "warning_min" in limit:
                limit_lines.append(("Warning Min", limit["warning_min"], warning_color, axis))
            if "warning_max" in limit:
                limit_lines.append(("Warning Max", limit["warning_max"], warning_color, axis))
            if "critical_min" in limit:
                limit_lines.append(("Critical Min", limit["critical_min"], "#ef4444", axis))
            if "critical_max" in limit:
                limit_lines.append(("Critical Max", limit["critical_max"], "#ef4444", axis))
        device_views.append(
            {
                "name": device["name"],
                "key": device["key"],
                "type": device_type,
                "status": status,
                "status_text": _status_text(status),
                "temp": device_current["temp"],
                "hum": device_current["hum"],
                "chart_id": chart_id,
                "temp_labels": [point["label"] for point in temp_series],
                "temp_values": [point["value"] for point in temp_series],
                "hum_labels": [point["label"] for point in hum_series],
                "hum_values": [point["value"] for point in hum_series],
                "labels_json": json.dumps([point["label"] for point in temp_series or hum_series]),
                "dates_json": json.dumps([point["date"] for point in temp_series or hum_series]),
                "temp_values_json": json.dumps([point["value"] for point in temp_series]),
                "hum_values_json": json.dumps([point["value"] for point in hum_series]),
                "chips_html": _render_chips(_device_chips(batches, device["key"], device_type)),
                "led_html": _render_led_svg(_led_value(batches, device["key"])),
                "limit_chips_temp": limit_chips_temp,
                "limit_chips_hum": limit_chips_hum,
                "limit_lines": limit_lines,
            }
        )

    # Letzte Kachel bei ungerader Anzahl auf volle Breite
    for i, device in enumerate(device_views):
        if len(device_views) % 2 == 1 and i == len(device_views) - 1:
            device["full_width"] = True
        else:
            device["full_width"] = False

    device_cards = "".join(_render_device_card(device, device_views) for device in device_views)

    device_scripts = "".join(
        _render_device_script(device) for device in device_views if device["type"] != "placeholder"
    )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{room["icon"]} {room["name"]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    min-height: 100vh;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: linear-gradient(rgba(10,20,30,.55), rgba(10,20,30,.70)), url("/otter2.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: white;
    padding: 30px;
}}

.container {{
    width: min(1200px, 95%);
    margin: auto;
    background: rgba(20,35,50,.58);
    backdrop-filter: blur(6px);
    border-radius: 25px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}}

h1 {{ text-align: center; margin-top: 0; }}
.subtitle {{ text-align: center; color: #d1d5db; }}

.back-btn {{
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
    margin-bottom: 20px;
}}

.back-btn:hover {{
    background: rgba(147,197,253,.3);
}}

.climate-btn {{
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
    font-size: .9rem;
    transition: .2s;
}}

.climate-btn:hover {{
    background: rgba(147,197,253,.3);
    border-color: rgba(147,197,253,.8);
    color: white;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.device-card, .system-card {{
    min-width: 0;
    overflow: hidden;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
    cursor: pointer;
    transition: .2s;
    text-decoration: none;
    color: white;
    display: block;
}}

.device-card:hover {{
    background: rgba(147,197,253,.15);
    border-color: rgba(147,197,253,.5);
    transform: translateY(-2px);
}}

.device-card-full {{
    grid-column: 1 / -1;
}}

.device-card-placeholder {{
    opacity: .6;
    border-style: dashed;
    cursor: default;
}}

.device-card-placeholder:hover {{
    background: rgba(31,41,55,.78);
    border-color: rgba(255,255,255,.08);
    transform: none;
}}

.device-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 76px;
}}

.device-header h2 {{
    margin: 0;
    font-size: 1.1rem;
    min-width: 0;
    overflow-wrap: break-word;
    word-break: break-word;
}}

.device-status-label {{
    display: block;
    margin-top: 5px;
    color: #d1d5db;
    font-size: .8rem;
}}

.status-light {{
    flex: 0 0 auto;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 3px solid rgba(255,255,255,.25);
    box-shadow: 0 0 14px currentColor;
}}

.status-ok {{ color: #22c55e; background: #22c55e; }}
.status-warn {{ color: #eab308; background: #eab308; }}
.status-critical {{ color: #ef4444; background: #ef4444; }}
.status-off {{ color: #6b7280; background: #6b7280; box-shadow: none; }}

.chip-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
}}
.chip {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: .75rem;
    font-weight: 600;
    white-space: nowrap;
}}
.chip-ok {{ background: rgba(34,197,94,.2); color: #86efac; }}
.chip-warn {{ background: rgba(234,179,8,.2); color: #fde047; }}
.chip-critical {{ background: rgba(239,68,68,.2); color: #fca5a5; }}
.chip-off {{ background: rgba(107,114,128,.2); color: #d1d5db; }}
.chip-info {{ background: rgba(147,197,253,.15); color: #bfdbfe; }}

.limit-chips {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    align-self: center;
}}
.limit-chips .chip {{
    font-size: .6rem;
    padding: 0 5px;
    line-height: 1.3;
}}
.metric .limit-chips .chip,
.metric-full .limit-chips .chip {{
    color: #d1d5db;
}}

.status-right {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.led-indicator {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
}}
.led-on {{ color: #fbbf24; }}
.led-off {{ color: #6b7280; }}

.metric-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 18px;
}}

.metric {{
    min-width: 0;
    padding: 12px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}}

.metric-full {{
    width: 100%;
    min-width: 0;
    padding: 12px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
    margin-top: 18px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}}

.metric-left {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-self: flex-start;
}}

.metric span, .metric-full span {{
    color: #d1d5db;
    font-size: .8rem;
}}

.metric strong, .metric-full strong {{
    font-size: 1.35rem;
}}

.metric small, .metric-full small {{
    color: #9ca3af;
    font-size: .8rem;
}}

.device-chart {{
    position: relative;
    height: 280px;
    margin-top: 18px;
    max-width: 100%;
    width: 100%;
}}

.placeholder-chart {{
    background: rgba(255,255,255,.03);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6b7280;
    font-style: italic;
}}

.system-card {{
    grid-column: 1 / -1;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
    cursor: default;
}}

.system-card:hover {{
    background: rgba(31,41,55,.78);
    border-color: rgba(255,255,255,.08);
    transform: none;
}}

.system-line {{
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 12px;
    margin: 6px 0;
}}

.footer {{
    text-align: center;
    margin-top: 30px;
    color: #d1d5db;
    opacity: .85;
    font-size: .9rem;
}}

@media(max-width:700px) {{
    body {{ padding: 15px; }}
    .container {{ width: 100%; padding: 20px; border-radius: 18px; }}
    .grid {{ grid-template-columns: 1fr; }}
    .system-line {{ grid-template-columns: 160px 1fr; }}
    .device-card-full {{ grid-column: 1 / -1; }}
}}
</style>
</head>
<body>
<div class="container">
<a class="back-btn" href="/">← Back to Overview</a>
<h1>{room["icon"]} {room["name"]}</h1>
<div class="subtitle">{climate_link}</div>

<div class="grid">
{device_cards}

    <div class="system-card">
        <h2>🖥 System</h2>
        <div class="system-line">
            <span>Last batch:</span><span>{current["last_batch"]}</span>
        </div>
        <div class="system-line">
            <span>Batches (48h):</span><span>{len(batches)}</span>
        </div>
        <div class="system-line">
            <span>CPU Temperature:</span><span>{current["cpu_temp"]:.1f} °C</span>
        </div>
        <div class="system-line">
            <span>Memory:</span><span>{current["memory_used"]:.0f}%</span>
        </div>
    </div>
</div>

<div class="footer">🦦 otterpi · ZOOLOGY-Observer Dashboard {VERSION}</div>
</div>

<script>
{device_scripts}
</script>
</body>
</html>
"""


def _render_climate_detail(
    store: BatchStore,
    climate_id: str,
    range_key: str = "7d",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Detailseite für das Raumklima eines Raumes."""
    rooms = get_rooms()
    if climate_id not in rooms:
        return _render_not_found()

    room = rooms[climate_id]

    # Zeitraum-Parameter validieren
    if range_key not in TIME_RANGES:
        range_key = "7d"

    hours = TIME_RANGES[range_key]

    # Bei Custom-Datum: Stunden basierend auf Datumsbereich berechnen
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            hours = max(24, int((end_dt - start_dt).total_seconds() / 3600) + 24)
            range_key = "custom"
        except ValueError:
            pass

    # Bei 15-Min-Intervall: 4 Batches/Stunde + Puffer
    limit = hours * 4 + 100
    batches = _recent_batches(store, hours=hours, limit=limit)

    # Beteiligte Sensoren ermitteln
    temp_sensor_keys = []  # (key, display_name, measurement_key)
    hum_sensor_keys = []  # (key, display_name, measurement_key)

    # ID01-Sensoren (temperature_1 = Raumtemperatur)
    for device in room["devices"]:
        if device.get("type") == "weatherhub_id01":
            key = device["key"]
            temp_sensor_keys.append((key, device["name"], f"{key}.temperature_1"))

    # ID03-Sensoren (temperature + humidity)
    for sensor_key in room.get("weatherhub_climate", []):
        # Sensorname aus ROOMS suchen
        sensor_name = sensor_key
        for rid, r in rooms.items():
            for device in r["devices"]:
                if device["key"] == sensor_key:
                    sensor_name = device["name"]
                    break

        temp_sensor_keys.append((sensor_key, sensor_name, f"{sensor_key}.temperature"))
        hum_sensor_keys.append((sensor_key, sensor_name, f"{sensor_key}.humidity"))

    # Zeitraum-Buttons generieren (ohne 365d)
    range_buttons_html = ""
    for key, label in VISIBLE_TIME_RANGES:
        active_class = " active" if key == range_key else ""
        range_buttons_html += (
            f'<a class="time-range-btn{active_class}" '
            f'href="/climate/{climate_id}?range={key}">{label}</a>\n    '
        )

    # Custom-Datum-Formular
    max_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    custom_date_html = f"""
    <form class="custom-date-form" method="get" action="/climate/{climate_id}">
        <input type="date" name="start_date" value="{start_date}" min="2025-01-01" max="{max_date}">
        <span>to</span>
        <input type="date" name="end_date" value="{end_date}" min="2025-01-01" max="{max_date}">
        <button type="submit">Apply</button>
    </form>
    """

    # Mittelwert-Serien berechnen
    temp_avg_series = _calculate_average_series(batches, temp_sensor_keys)
    hum_avg_series = _calculate_average_series(batches, hum_sensor_keys) if hum_sensor_keys else []

    # Einzelsensor-Serien für Charts
    temp_series_by_sensor = []
    for key, name, measurement_key in temp_sensor_keys:
        series = _series(batches, measurement_key)
        if series:
            temp_series_by_sensor.append(
                {
                    "key": key,
                    "name": name,
                    "series": series,
                }
            )

    hum_series_by_sensor = []
    for key, name, measurement_key in hum_sensor_keys:
        series = _series(batches, measurement_key)
        if series:
            hum_series_by_sensor.append(
                {
                    "key": key,
                    "name": name,
                    "series": series,
                }
            )

    # Aktuelle Werte
    climate = _room_climate(batches, room)

    # Letzte Aktualisierung
    last_update = "–"
    if batches:
        latest = batches[-1]
        last_update = (
            datetime.fromisoformat(latest["created_at"])
            .astimezone(BERLIN)
            .strftime("%d.%m.%Y %H:%M Uhr")
        )

    # Sensor-Info
    sensor_info_lines = ""
    sensor_info_lines += (
        f'<div class="info-line">'
        f'<span class="info-label">ID01 Sensors:</span>'
        f'<span class="info-value">{len(temp_sensor_keys) - len(hum_sensor_keys)}</span>'
        f"</div>"
    )
    sensor_info_lines += (
        f'<div class="info-line">'
        f'<span class="info-label">ID03 Sensors:</span>'
        f'<span class="info-value">{len(hum_sensor_keys)}</span>'
        f"</div>"
    )
    sensor_info_lines += (
        f'<div class="info-line">'
        f'<span class="info-label">Last Update:</span>'
        f'<span class="info-value">{last_update}</span>'
        f"</div>"
    )

    # Statistik für Mittelwerte - KORRIGIERT
    temp_stats = _calculate_stats(temp_avg_series, [])
    hum_stats = _calculate_stats([], hum_avg_series)

    # Statistik-HTML
    stats_html = f"""
            <div class="stat">
                <span>🌡️ Min Ø Temperature</span>
                <strong>{temp_stats["temp_min"]:.1f} <small>°C</small></strong>
            </div>
            <div class="stat">
                <span>🌡️ Max Ø Temperature</span>
                <strong>{temp_stats["temp_max"]:.1f} <small>°C</small></strong>
            </div>
            <div class="stat">
                <span>🌡️ Ø Temperature</span>
                <strong>{temp_stats["temp_avg"]:.1f} <small>°C</small></strong>
            </div>
    """

    if hum_avg_series:
        stats_html += f"""
            <div class="stat">
                <span>💧 Min Ø Humidity</span>
                <strong>{hum_stats["hum_min"]:.1f} <small>%</small></strong>
            </div>
            <div class="stat">
                <span>💧 Max Ø Humidity</span>
                <strong>{hum_stats["hum_max"]:.1f} <small>%</small></strong>
            </div>
            <div class="stat">
                <span>💧 Ø Humidity</span>
                <strong>{hum_stats["hum_avg"]:.1f} <small>%</small></strong>
            </div>
        """

    # Chart-Daten für Mittelwerte
    temp_avg_labels = json.dumps([point["label"] for point in temp_avg_series])
    temp_avg_dates = json.dumps([point["date"] for point in temp_avg_series])
    temp_avg_values = json.dumps([point["value"] for point in temp_avg_series])
    hum_avg_labels = json.dumps([point["label"] for point in hum_avg_series])
    hum_avg_dates = json.dumps([point["date"] for point in hum_avg_series])
    hum_avg_values = json.dumps([point["value"] for point in hum_avg_series])

    # Einzelsensor-Datasets für Temperatur (verschiedene Farben)
    temp_sensor_datasets = []
    for i, sensor_data in enumerate(temp_series_by_sensor):
        series = sensor_data["series"]
        values = json.dumps([point["value"] for point in series])
        name = sensor_data["name"].replace("<i>", "").replace("</i>", "")
        color = SENSOR_COLORS[i % len(SENSOR_COLORS)]
        temp_sensor_datasets.append(
            f"""{{
                label: '{name}',
                data: {values},
                borderColor: '{color}',
                borderWidth: 1,
                pointRadius: 1,
                pointHoverRadius: 3,
                tension: 0.3
            }}"""
        )
    temp_sensor_datasets_str = ",\n            ".join(temp_sensor_datasets)

    # Einzelsensor-Datasets für Feuchte (verschiedene Farben, startet mit Hellblau)
    hum_sensor_datasets = []
    for i, sensor_data in enumerate(hum_series_by_sensor):
        series = sensor_data["series"]
        values = json.dumps([point["value"] for point in series])
        name = sensor_data["name"].replace("<i>", "").replace("</i>", "")
        color = HUMIDITY_COLORS[i % len(HUMIDITY_COLORS)]
        hum_sensor_datasets.append(
            f"""{{
                label: '{name}',
                data: {values},
                borderColor: '{color}',
                borderWidth: 1,
                pointRadius: 1,
                pointHoverRadius: 3,
                tension: 0.3
            }}"""
        )
    hum_sensor_datasets_str = ",\n            ".join(hum_sensor_datasets)

    # Chart-HTML für Feuchte (nur wenn vorhanden)
    hum_avg_chart_html = ""
    if hum_avg_series:
        hum_avg_chart_html = (
            "<div class='chart-container'>"
            "<span class='chart-title'>💧 Average Relative Humidity</span>"
            "<canvas id='chart-hum-avg'></canvas>"
            "</div>"
        )

    hum_sensors_chart_html = ""
    if hum_series_by_sensor:
        hum_sensors_chart_html = (
            "<div class='chart-container'>"
            "<span class='chart-title'>💧 Individual Sensors - Humidity</span>"
            "<canvas id='chart-hum-sensors'></canvas>"
            "</div>"
        )

    # Tooltip-Hilfsfunktionen
    tooltip_label_color = _tooltip_label_color()
    tooltip_date_logic_temp = _tooltip_date_logic("tempAvgDates")
    tooltip_date_logic_hum = _tooltip_date_logic("humAvgDates")
    tooltip_date_logic_temp_sensors = _tooltip_date_logic("tempSensorDates")
    tooltip_date_logic_hum_sensors = _tooltip_date_logic("humSensorDates")

    # Chart-Skripte
    hum_avg_script = ""
    if hum_avg_series:
        hum_avg_script = f"""
<script>
// Chart 2: Durchschnittsfeuchte
const humAvgLabels = {hum_avg_labels};
const humAvgDates = {hum_avg_dates};
const humAvgValues = {hum_avg_values};

new Chart(document.getElementById('chart-hum-avg'), {{
    type: 'line',
    data: {{
        labels: humAvgLabels,
        datasets: [{{
            label: 'Ø Rel. Humidity',
            data: humAvgValues,
            borderColor: '#38bdf8',
            borderWidth: 2,
            pointRadius: 2,
            pointHoverRadius: 4,
            tension: 0.3
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{ labels: {{ color: '#d1d5db', usePointStyle: true, pointStyle: 'line' }} }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                callbacks: {{
                    {tooltip_label_color}
                    {tooltip_date_logic_hum}
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        return `Ø Rel. Humidity: ${{value}} %`;
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{
                type: 'linear',
                ticks: {{
                    color: '#38bdf8',
                    callback: (value) => {{
                        const rounded = Math.round(value * 10) / 10;
                        return rounded + ' %';
                    }}
                }}
            }}
        }}
    }}
}});
</script>
"""

    hum_sensors_script = ""
    if hum_series_by_sensor:
        hum_sensors_script = f"""
<script>
// Chart 4: Einzelne Sensoren - Feuchte
const humSensorLabels = {hum_avg_labels if hum_avg_series else "[]"};
const humSensorDates = {hum_avg_dates if hum_avg_series else "[]"};
const humSensorDatasets = [
    {hum_sensor_datasets_str}
];

new Chart(document.getElementById('chart-hum-sensors'), {{
    type: 'line',
    data: {{
        labels: humSensorLabels,
        datasets: humSensorDatasets
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{
                labels: {{ color: '#d1d5db', usePointStyle: true, pointStyle: 'line' }}
            }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                callbacks: {{
                    {tooltip_label_color}
                    {tooltip_date_logic_hum_sensors}
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        return `${{context.dataset.label}}: ${{value}} %`;
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{
                type: 'linear',
                ticks: {{
                    color: '#38bdf8',
                    callback: (value) => {{
                        const rounded = Math.round(value * 10) / 10;
                        return rounded + ' %';
                    }}
                }}
            }}
        }}
    }}
}});
</script>
"""

    # Große aktuelle Werte-Header (kleiner Stil wie auf Raumübersicht)
    current_temp = climate["temp"] if climate["temp"] is not None else 0.0
    current_hum = climate["hum"] if climate["hum"] is not None else 0.0
    has_humidity = climate["hum"] is not None

    if has_humidity:
        current_values_header = f"""
<div class="current-values-header">
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">🌡️ Temperature</span>
            <span class="current-value">{current_temp:.1f} <small>°C</small></span>
        </div>
    </div>
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">💧 Relative Humidity</span>
            <span class="current-value">{current_hum:.1f} <small>%</small></span>
        </div>
    </div>
</div>
"""
    else:
        current_values_header = f"""
<div class="current-values-header">
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">🌡️ Temperature</span>
            <span class="current-value">{current_temp:.1f} <small>°C</small></span>
        </div>
    </div>
</div>
"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Room Climate · {room["name"]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    min-height: 100vh;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: linear-gradient(rgba(10,20,30,.55), rgba(10,20,30,.70)), url("/otter2.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: white;
    padding: 30px;
}}

.container {{
    width: min(1200px, 95%);
    margin: auto;
    background: rgba(20,35,50,.58);
    backdrop-filter: blur(6px);
    border-radius: 25px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}}

h1 {{ text-align: center; margin-top: 0; }}
.subtitle {{ text-align: center; color: #d1d5db; }}

.back-buttons {{
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}}

.back-btn {{
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
}}

.back-btn:hover {{
    background: rgba(147,197,253,.3);
}}

.current-values-header {{
    display: flex;
    gap: 20px;
    margin-top: 20px;
    flex-wrap: wrap;
}}

.current-value-box {{
    min-width: 200px;
    flex: 1;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: left;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}}

.current-value-left {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-self: flex-start;
}}

.current-value-label {{
    color: #d1d5db;
    font-size: .85rem;
}}

.current-value {{
    font-size: 1.6rem;
    font-weight: 600;
    color: white;
}}

.current-value small {{
    font-size: 1rem;
    color: #9ca3af;
}}

.time-range-buttons {{
    display: flex;
    gap: 8px;
    margin-top: 20px;
    flex-wrap: wrap;
    align-items: center;
}}

.time-range-btn {{
    padding: 8px 16px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
    font-size: .9rem;
    transition: .2s;
}}

.time-range-btn:hover {{
    background: rgba(147,197,253,.3);
}}

.time-range-btn.active {{
    background: rgba(147,197,253,.5);
    border-color: rgba(147,197,253,.8);
    color: white;
}}

.custom-date-form {{
    display: flex;
    gap: 8px;
    align-items: center;
    margin-left: 10px;
}}

.custom-date-form input {{
    padding: 6px 10px;
    border-radius: 8px;
    border: 1px solid rgba(147,197,253,.4);
    background: rgba(31,41,55,.78);
    color: white;
    font-size: .85rem;
}}

.custom-date-form button {{
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    cursor: pointer;
    font-size: .85rem;
}}

.custom-date-form button:hover {{
    background: rgba(147,197,253,.3);
}}

.chart-container {{
    position: relative;
    height: 300px;
    margin-top: 20px;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.chart-title {{
    position: absolute;
    top: 10px;
    left: 20px;
    color: #d1d5db;
    font-size: .9rem;
    z-index: 1;
}}

.info-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.info-card {{
    min-width: 0;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.info-card h3 {{
    margin-top: 0;
    color: #d1d5db;
    font-size: 1rem;
}}

.info-line {{
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 12px;
    margin: 8px 0;
    font-size: .9rem;
}}

.info-label {{
    color: #9ca3af;
}}

.info-value {{
    color: white;
}}

.stat-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}}

.stat {{
    padding: 12px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
}}

.stat span {{
    display: block;
    color: #d1d5db;
    font-size: .8rem;
}}

.stat strong {{
    display: block;
    margin-top: 5px;
    font-size: 1.1rem;
}}

.stat small {{
    color: #9ca3af;
    font-size: .8rem;
}}

.footer {{
    text-align: center;
    margin-top: 30px;
    color: #d1d5db;
    opacity: .85;
    font-size: .9rem;
}}

@media(max-width:700px) {{
    body {{ padding: 15px; }}
    .container {{ width: 100%; padding: 20px; border-radius: 18px; }}
    .info-grid {{ grid-template-columns: 1fr; }}
    .stat-grid {{ grid-template-columns: 1fr; }}
    .info-line {{ grid-template-columns: 140px 1fr; }}
    .custom-date-form {{ margin-left: 0; margin-top: 10px; }}
    .current-values-header {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<div class="container">
<div class="back-buttons">
    <a class="back-btn" href="/room/{climate_id}">← Back to {room["name"]}</a>
    <a class="back-btn" href="/">← Back to Overview</a>
</div>
<h1>{room["icon"]} Room Climate · {room["name"]}</h1>

{current_values_header}

<div class="time-range-buttons">
    {range_buttons_html}
    {custom_date_html}
</div>

<div class="chart-container">
    <span class="chart-title">🌡️ Average Temperature</span>
    <canvas id="chart-temp-avg"></canvas>
</div>

{hum_avg_chart_html}

<div class="chart-container">
    <span class="chart-title">🌡️ Individual Sensors - Temperature</span>
    <canvas id="chart-temp-sensors"></canvas>
</div>

{hum_sensors_chart_html}

<div class="info-grid">
    <div class="info-card">
        <h3>📊 Statistics</h3>
        <div class="stat-grid">
            {stats_html}
        </div>
    </div>

    <div class="info-card">
        <h3>📋 Sensor Information</h3>
        {sensor_info_lines}
    </div>
</div>

<div class="footer">🦦 otterpi · ZOOLOGY-Observer Dashboard {VERSION}</div>
</div>

<script>
// Chart 1: Durchschnittstemperatur
const tempAvgLabels = {temp_avg_labels};
const tempAvgDates = {temp_avg_dates};
const tempAvgValues = {temp_avg_values};

new Chart(document.getElementById('chart-temp-avg'), {{
    type: 'line',
    data: {{
        labels: tempAvgLabels,
        datasets: [{{
            label: 'Ø Temperature',
            data: tempAvgValues,
            borderColor: '#fb923c',
            borderWidth: 2,
            pointRadius: 2,
            pointHoverRadius: 4,
            tension: 0.3
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{ labels: {{ color: '#d1d5db', usePointStyle: true, pointStyle: 'line' }} }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                callbacks: {{
                    {tooltip_label_color}
                    {tooltip_date_logic_temp}
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        return `Ø Temperature: ${{value}} °C`;
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{
                type: 'linear',
                ticks: {{
                    color: '#fb923c',
                    callback: (value) => {{
                        const rounded = Math.round(value * 10) / 10;
                        return rounded + ' °C';
                    }}
                }}
            }}
        }}
    }}
}});
</script>

{hum_avg_script}

<script>
// Chart 3: Einzelne Sensoren - Temperatur
const tempSensorLabels = {temp_avg_labels};
const tempSensorDates = {temp_avg_dates};
const tempSensorDatasets = [
    {temp_sensor_datasets_str}
];

new Chart(document.getElementById('chart-temp-sensors'), {{
    type: 'line',
    data: {{
        labels: tempSensorLabels,
        datasets: tempSensorDatasets
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{
                labels: {{ color: '#d1d5db', usePointStyle: true, pointStyle: 'line' }}
            }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                callbacks: {{
                    {tooltip_label_color}
                    {tooltip_date_logic_temp_sensors}
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        return `${{context.dataset.label}}: ${{value}} °C`;
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{
                type: 'linear',
                ticks: {{
                    color: '#fb923c',
                    callback: (value) => {{
                        const rounded = Math.round(value * 10) / 10;
                        return rounded + ' °C';
                    }}
                }}
            }}
        }}
    }}
}});
</script>

{hum_sensors_script}

</body>
</html>
"""


def _render_device_detail(
    store: BatchStore,
    device_key: str,
    range_key: str = "7d",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Detailseite für ein einzelnes Gerät."""
    # Zeitraum-Parameter validieren
    if range_key not in TIME_RANGES:
        range_key = "7d"

    # Gerät in ROOMS suchen
    device_info = None
    room_id = None
    room = None

    rooms = get_rooms()
    for rid, r in rooms.items():
        for device in r["devices"]:
            if device["key"] == device_key:
                device_info = device
                room_id = rid
                room = r
                break
        if device_info:
            break

    if device_info is None:
        return _render_not_found()

    device_type = device_info.get("type", "atmoweb")

    # Zeitraum aus Query-Parameter lesen
    hours = TIME_RANGES[range_key]

    # Bei Custom-Datum: Stunden basierend auf Datumsbereich berechnen
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            hours = max(24, int((end_dt - start_dt).total_seconds() / 3600) + 24)
            range_key = "custom"
        except ValueError:
            pass

    # Bei 15-Min-Intervall: 4 Batches/Stunde + Puffer
    limit = hours * 4 + 100
    batches = _recent_batches(store, hours=hours, limit=limit)

    # Messwert-Schlüssel je nach Gerätetyp bestimmen
    if device_type == "weatherhub_id01":
        temp_key = f"{device_key}.temperature_2"
        hum_key = None
    elif device_type == "weatherhub_id0e":
        temp_key = f"{device_key}.temperature"
        hum_key = f"{device_key}.humidity"
    elif device_type in ("freezer", "memmert"):
        temp_key = f"{device_key}.temperature"
        hum_key = None
    else:  # atmoweb
        temp_key = f"{device_key}.temperature_1"
        hum_key = f"{device_key}.humidity"

    # Serien laden
    temp_series = _series(batches, temp_key)
    hum_series = _series(batches, hum_key) if hum_key else []

    # Aktuelle Werte
    device_current = _device_current(batches, device_key, device_type)

    # Aktueller Status
    status = _device_status(batches, device_key, device_type)
    status_text = _status_text(status)

    # Statistik - KORREKT: temp_series als ersten, hum_series als zweiten Parameter
    stats = _calculate_stats(temp_series, hum_series)

    # Letzte Aktualisierung
    last_update = "–"
    if batches:
        latest = batches[-1]
        last_update = (
            datetime.fromisoformat(latest["created_at"])
            .astimezone(BERLIN)
            .strftime("%d.%m.%Y %H:%M Uhr")
        )

    # Humidity-Statistik nur anzeigen, wenn Feuchte vorhanden
    hum_stats_html = ""
    if hum_key:
        hum_stats_html = f"""
            <div class="stat">
                <span>💧 Min Humidity</span>
                <strong>{stats["hum_min"]:.1f} <small>%</small></strong>
            </div>
            <div class="stat">
                <span>💧 Max Humidity</span>
                <strong>{stats["hum_max"]:.1f} <small>%</small></strong>
            </div>
            <div class="stat">
                <span>💧 Avg Humidity</span>
                <strong>{stats["hum_avg"]:.1f} <small>%</small></strong>
            </div>
        """

    # Zeitraum-Buttons generieren (ohne 365d)
    range_buttons_html = ""
    for key, label in VISIBLE_TIME_RANGES:
        active_class = " active" if key == range_key else ""
        range_buttons_html += (
            f'<a class="time-range-btn{active_class}" '
            f'href="/device/{device_key}?range={key}">{label}</a>\n    '
        )

    # Custom-Datum-Formular
    max_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    custom_date_html = f"""
    <form class="custom-date-form" method="get" action="/device/{device_key}">
        <input type="date" name="start_date" value="{start_date}" min="2025-01-01" max="{max_date}">
        <span>to</span>
        <input type="date" name="end_date" value="{end_date}" min="2025-01-01" max="{max_date}">
        <button type="submit">Apply</button>
    </form>
    """

    # Chart-Daten
    temp_labels_json = json.dumps([point["label"] for point in temp_series])
    temp_dates_json = json.dumps([point["date"] for point in temp_series])
    temp_values_json = json.dumps([point["value"] for point in temp_series])
    hum_values_json = json.dumps([point["value"] for point in hum_series])

    # Limit-Chips (vor current_values_header definieren)
    limits = _device_limits(device_key)
    limit_chips_temp = _render_limit_chips(limits, temp_key, "°C", compact=False)
    limit_chips_hum = _render_limit_chips(limits, hum_key, "%", compact=False) if hum_key else ""

    limit_lines = []
    for limit_key, limit in limits.items():
        if not limit.get("enabled", True):
            continue
        if limit_key == temp_key:
            axis = "temperature"
        elif limit_key == hum_key:
            axis = "humidity"
        else:
            continue
        warning_color = "#fb923c" if axis == "temperature" else "#38bdf8"
        if "warning_min" in limit:
            limit_lines.append(("Warning Min", limit["warning_min"], warning_color, axis))
        if "warning_max" in limit:
            limit_lines.append(("Warning Max", limit["warning_max"], warning_color, axis))
        if "critical_min" in limit:
            limit_lines.append(("Critical Min", limit["critical_min"], "#ef4444", axis))
        if "critical_max" in limit:
            limit_lines.append(("Critical Max", limit["critical_max"], "#ef4444", axis))

    limit_datasets = ""
    for label, value, color, axis in limit_lines:
        limit_datasets += f"""
            {{
                label: '{label}',
                data: tempValues.map(() => {value}),
                borderColor: '{color}',
                borderDash: [5, 5],
                pointRadius: 0,
                borderWidth: 1,
                yAxisID: '{axis}',
            }},"""

    # Große aktuelle Werte-Header (kleiner Stil wie auf Raumübersicht)
    has_humidity = len(hum_series) > 0

    if has_humidity:
        current_values_header = f"""
<div class="current-values-header">
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">🌡️ Temperature</span>
            <span class="current-value">{device_current["temp"]:.1f} <small>°C</small></span>
        </div>
        {limit_chips_temp}
    </div>
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">💧 Relative Humidity</span>
            <span class="current-value">{device_current["hum"]:.1f} <small>%</small></span>
        </div>
        {limit_chips_hum}
    </div>
</div>
"""
    else:
        current_values_header = f"""
<div class="current-values-header">
    <div class="current-value-box">
        <div class="current-value-left">
            <span class="current-value-label">🌡️ Temperature</span>
            <span class="current-value">{device_current["temp"]:.1f} <small>°C</small></span>
        </div>
        {limit_chips_temp}
    </div>
</div>
"""

    chips_html = _render_chips(_device_chips(batches, device_key, device_type))
    led_html = _render_led_svg(_led_value(batches, device_key))

    device_meta = _latest_device(batches, device_key)
    device_meta_html = ""
    for label, field in (
        ("Serial Number", "serial_number"),
        ("Device Type", "device_type"),
        ("Software Revision", "software_revision"),
        ("Host", "host"),
        ("Address", "address"),
        ("Port", "port"),
        ("Resolution", "resolution"),
        ("USB Serial", "usb_serial"),
        ("Sensor ID", "sensor_id"),
        ("Sensor Type", "sensor_type"),
        ("Gateway IP", "gateway_ip"),
        ("Gateway Timestamp", "gateway_timestamp"),
    ):
        if field in device_meta and device_meta[field] is not None:
            value = device_meta[field]
            if field == "resolution":
                value = "0.1 °C" if value == 0 else "1 °C"
            elif field == "sensor_type":
                value = f"ID{value:02X}"
            elif field == "gateway_timestamp":
                value = (
                    datetime.fromtimestamp(value, tz=timezone.utc)
                    .astimezone(BERLIN)
                    .strftime("%d.%m.%Y %H:%M:%S Uhr")
                )
            device_meta_html += f"""
        <div class="info-line">
            <span class="info-label">{label}:</span>
            <span class="info-value">{value}</span>
        </div>
"""

    usb_vid = device_meta.get("usb_vid")
    usb_pid = device_meta.get("usb_pid")
    if usb_vid and usb_pid:
        usb_name = _USB_NAMES.get((usb_vid, usb_pid))
        usb_label = f"{usb_name} ({usb_vid}:{usb_pid})" if usb_name else f"{usb_vid}:{usb_pid}"
        device_meta_html += f"""
        <div class="info-line">
            <span class="info-label">USB:</span>
            <span class="info-value">{usb_label}</span>
        </div>
"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{device_info["name"]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    min-height: 100vh;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: linear-gradient(rgba(10,20,30,.55), rgba(10,20,30,.70)), url("/otter2.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: white;
    padding: 30px;
}}

.container {{
    width: min(1200px, 95%);
    margin: auto;
    background: rgba(20,35,50,.58);
    backdrop-filter: blur(6px);
    border-radius: 25px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}}

h1 {{ text-align: center; margin-top: 0; }}
.subtitle {{ text-align: center; color: #d1d5db; }}

.back-buttons {{
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}}

.back-btn {{
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
}}

.back-btn:hover {{
    background: rgba(147,197,253,.3);
}}

.device-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-top: 20px;
}}

.device-header h2 {{
    margin: 0;
    font-size: 1.1rem;
    min-width: 0;
    overflow-wrap: break-word;
    word-break: break-word;
}}

.device-status-label {{
    display: block;
    margin-top: 5px;
    color: #d1d5db;
    font-size: .8rem;
}}

.status-light {{
    flex: 0 0 auto;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 3px solid rgba(255,255,255,.25);
    box-shadow: 0 0 14px currentColor;
}}

.status-ok {{ color: #22c55e; background: #22c55e; }}
.status-warn {{ color: #eab308; background: #eab308; }}
.status-critical {{ color: #ef4444; background: #ef4444; }}
.status-off {{ color: #6b7280; background: #6b7280; box-shadow: none; }}

.chip-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
}}
.chip {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: .75rem;
    font-weight: 600;
    white-space: nowrap;
}}
.chip-ok {{ background: rgba(34,197,94,.2); color: #86efac; }}
.chip-warn {{ background: rgba(234,179,8,.2); color: #fde047; }}
.chip-critical {{ background: rgba(239,68,68,.2); color: #fca5a5; }}
.chip-off {{ background: rgba(107,114,128,.2); color: #d1d5db; }}
.chip-info {{ background: rgba(147,197,253,.15); color: #bfdbfe; }}

.limit-chips {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    align-self: center;
}}
.limit-chips .chip {{
    font-size: .6rem;
    padding: 0 5px;
    line-height: 1.3;
}}
.limit-chips-detailed .chip {{
    font-size: .7rem;
    padding: 1px 6px;
    color: #d1d5db;
}}

.status-right {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.led-indicator {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
}}
.led-on {{ color: #fbbf24; }}
.led-off {{ color: #6b7280; }}

.current-values-header {{
    display: flex;
    gap: 20px;
    margin-top: 20px;
    flex-wrap: wrap;
}}

.current-value-box {{
    min-width: 200px;
    flex: 1;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: left;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}}

.current-value-left {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-self: flex-start;
}}

.current-value-label {{
    color: #d1d5db;
    font-size: .85rem;
}}

.current-value {{
    font-size: 1.6rem;
    font-weight: 600;
    color: white;
}}

.current-value small {{
    font-size: 1rem;
    color: #9ca3af;
}}

.time-range-buttons {{
    display: flex;
    gap: 8px;
    margin-top: 20px;
    flex-wrap: wrap;
    align-items: center;
}}

.time-range-btn {{
    padding: 8px 16px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
    font-size: .9rem;
    transition: .2s;
}}

.time-range-btn:hover {{
    background: rgba(147,197,253,.3);
}}

.time-range-btn.active {{
    background: rgba(147,197,253,.5);
    border-color: rgba(147,197,253,.8);
    color: white;
}}

.custom-date-form {{
    display: flex;
    gap: 8px;
    align-items: center;
    margin-left: 10px;
}}

.custom-date-form input {{
    padding: 6px 10px;
    border-radius: 8px;
    border: 1px solid rgba(147,197,253,.4);
    background: rgba(31,41,55,.78);
    color: white;
    font-size: .85rem;
}}

.custom-date-form button {{
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    cursor: pointer;
    font-size: .85rem;
}}

.custom-date-form button:hover {{
    background: rgba(147,197,253,.3);
}}

.chart-container {{
    position: relative;
    height: 400px;
    margin-top: 20px;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.info-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.info-card {{
    min-width: 0;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.info-card h3 {{
    margin-top: 0;
    color: #d1d5db;
    font-size: 1rem;
}}

.info-line {{
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 12px;
    margin: 8px 0;
    font-size: .9rem;
}}

.info-label {{
    color: #9ca3af;
}}

.info-value {{
    color: white;
}}

.stat-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}}

.stat {{
    padding: 12px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
}}

.stat span {{
    display: block;
    color: #d1d5db;
    font-size: .8rem;
}}

.stat strong {{
    display: block;
    margin-top: 5px;
    font-size: 1.1rem;
}}

.stat small {{
    color: #9ca3af;
    font-size: .8rem;
}}

.footer {{
    text-align: center;
    margin-top: 30px;
    color: #d1d5db;
    opacity: .85;
    font-size: .9rem;
}}

@media(max-width:700px) {{
    body {{ padding: 15px; }}
    .container {{ width: 100%; padding: 20px; border-radius: 18px; }}
    .info-grid {{ grid-template-columns: 1fr; }}
    .stat-grid {{ grid-template-columns: 1fr; }}
    .info-line {{ grid-template-columns: 140px 1fr; }}
    .custom-date-form {{ margin-left: 0; margin-top: 10px; }}
    .current-values-header {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<div class="container">
<div class="back-buttons">
    <a class="back-btn" href="/room/{room_id}">← Back to {room["name"]}</a>
    <a class="back-btn" href="/">← Back to Overview</a>
</div>
<h1>{device_info["name"]}</h1>

<div class="device-header">
    <div>
        <h2>Current Status</h2>
        <div class="chip-row">{chips_html}</div>
    </div>
    <div class="status-right">
        {led_html}
        <span class="status-light {status}" aria-label="Device Status"></span>
    </div>
</div>

{current_values_header}

<div class="time-range-buttons">
    {range_buttons_html}
    {custom_date_html}
</div>

<div class="chart-container">
    <canvas id="device-chart"></canvas>
</div>

<div class="info-grid">
    <div class="info-card">
        <h3>📊 Statistics</h3>
        <div class="stat-grid">
            <div class="stat">
                <span>🌡️ Min Temperature</span>
                <strong>{stats["temp_min"]:.1f} <small>°C</small></strong>
            </div>
            <div class="stat">
                <span>🌡️ Max Temperature</span>
                <strong>{stats["temp_max"]:.1f} <small>°C</small></strong>
            </div>
            <div class="stat">
                <span>🌡️ Avg Temperature</span>
                <strong>{stats["temp_avg"]:.1f} <small>°C</small></strong>
            </div>
            {hum_stats_html}
        </div>
    </div>

    <div class="info-card">
        <h3>📋 Sensor Information</h3>
        <div class="info-line">
            <span class="info-label">Device Name:</span>
            <span class="info-value">{device_info["name"]}</span>
        </div>
        <div class="info-line">
            <span class="info-label">Device Key:</span>
            <span class="info-value">{device_key}</span>
        </div>
        <div class="info-line">
            <span class="info-label">Type:</span>
            <span class="info-value">{device_type}</span>
        </div>
        <div class="info-line">
            <span class="info-label">Room:</span>
            <span class="info-value">{room["name"]}</span>
        </div>
        <div class="info-line">
            <span class="info-label">Last Update:</span>
            <span class="info-value">{last_update}</span>
        </div>
        <div class="info-line">
            <span class="info-label">Status:</span>
            <span class="info-value">{status_text}</span>
        </div>
        {device_meta_html}
    </div>
</div>

<div class="footer">🦦 otterpi · ZOOLOGY-Observer Dashboard {VERSION}</div>
</div>

<script>
const tempLabels = {temp_labels_json};
const tempDates = {temp_dates_json};
const tempValues = {temp_values_json};
const humValues = {hum_values_json};
const hasHumidity = humValues.length > 0;

const datasets = [
    {{
        label: 'Temperature',
        data: tempValues,
        borderColor: '#fb923c',
        borderWidth: 1.5,
        pointRadius: 2,
        pointHoverRadius: 4,
        yAxisID: 'temperature',
        tension: 0.3
    }},{limit_datasets}
];

const scales = {{
    x: {{
        ticks: {{
            color: '#9ca3af',
            callback: (value) => tempLabels[value]
        }}
    }},
    temperature: {{
        type: 'linear',
        position: 'left',
        ticks: {{
            color: '#fb923c',
            callback: (value) => {{
                const rounded = Math.round(value * 10) / 10;
                return rounded + ' °C';
            }}
        }}
    }}
}};

if (hasHumidity) {{
    datasets.push({{
        label: 'Relative Humidity',
        data: humValues,
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        pointRadius: 2,
        pointHoverRadius: 4,
        yAxisID: 'humidity',
        tension: 0.3
    }});
    scales.humidity = {{
        type: 'linear',
        position: 'right',
        ticks: {{
            color: '#38bdf8',
            callback: (value) => {{
                const rounded = Math.round(value * 10) / 10;
                return rounded + ' %';
            }}
        }},
        grid: {{ drawOnChartArea: false }}
    }};
}}

new Chart(document.getElementById('device-chart'), {{
    type: 'line',
    data: {{
        labels: tempLabels,
        datasets: datasets
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{
                labels: {{
                    color: '#d1d5db',
                    usePointStyle: true,
                    pointStyle: 'line',
                }}
            }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                filter: (item) => {{
                    const label = item.dataset.label || '';
                    return !label.startsWith('Warning') && !label.startsWith('Critical');
                }},
                callbacks: {{
                    labelColor: (context) => ({{
                        borderColor: context.dataset.borderColor,
                        backgroundColor: context.dataset.borderColor
                    }}),
                    labelPointStyle: () => ({{
                        pointStyle: 'circle',
                        rotation: 0
                    }}),
                    title: (items) => {{
                        if (items.length > 0) {{
                            const idx = items[0].dataIndex;
                            const dateStr = tempDates[idx] || '';
                            const label = items[0].label;

                            let dateLabel = '';
                            if (dateStr) {{
                                const today = new Date();
                                const date = new Date(dateStr + 'T00:00:00');

                                const todayMidnight = new Date(
                                    today.getFullYear(), today.getMonth(), today.getDate()
                                );
                                const dateMidnight = new Date(
                                    date.getFullYear(), date.getMonth(), date.getDate()
                                );

                                const diffDays = Math.round(
                                    (todayMidnight - dateMidnight) / (1000 * 60 * 60 * 24)
                                );

                                if (diffDays === 0) {{
                                    dateLabel = 'today';
                                }} else if (diffDays === 1) {{
                                    dateLabel = 'yesterday';
                                }} else {{
                                    const dd = String(date.getDate()).padStart(2, '0');
                                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                                    const yyyy = date.getFullYear();
                                    dateLabel = `${{dd}}.${{mm}}.${{yyyy}}`;
                                }}
                            }}

                            return `📅 Date: ${{dateLabel}}\\n⏰ Time: ${{label}}`;
                        }}
                        return '';
                    }},
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        if (context.dataset.label === 'Temperature') {{
                            return `Temperature: ${{value}} °C`;
                        }}
                        return `Rel. Humidity: ${{value}} %`;
                    }}
                }}
            }}
        }},
        scales: scales
    }}
}});
</script>
</body>
</html>
"""


def _render_not_found() -> str:
    """Zeigt eine 404-ähnliche Meldung."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Not Found</title>
<style>
body {
    margin: 0;
    min-height: 100vh;
    font-family: system-ui, sans-serif;
    background: linear-gradient(rgba(10,20,30,.55), rgba(10,20,30,.70)), url("/otter2.png");
    background-size: cover;
    background-position: center;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 30px;
}
.container {
    text-align: center;
    background: rgba(20,35,50,.8);
    border-radius: 25px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}
a {
    display: inline-block;
    margin-top: 20px;
    padding: 10px 24px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    text-decoration: none;
}
</style>
</head>
<body>
<div class="container">
<h1>🔍 Not Found</h1>
<p>The requested resource does not exist.</p>
<a href="/">← Back to Overview</a>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Hilfsfunktionen zur Karten-Erzeugung
# ---------------------------------------------------------------------------


def _render_device_card(device: dict, device_views: list[dict]) -> str:
    """Erzeugt die HTML-Karte für ein Gerät."""
    if device["type"] == "placeholder":
        return f"""
    <section class="device-card device-card-placeholder">
        <div class="device-header">
            <div>
                <h2>{device["name"]}</h2>
                <span class="device-status-label">planned</span>
            </div>
            <span class="status-light status-off" aria-label="Placeholder"></span>
        </div>
        <div class="metric-grid">
            <div class="metric">
                <span>🌡️ Temperature</span>
                <strong>– <small>°C</small></strong>
            </div>
            <div class="metric">
                <span>💧 Relative Humidity</span>
                <strong>– <small>%</small></strong>
            </div>
        </div>
        <div class="device-chart placeholder-chart"></div>
    </section>
"""

    full_width_class = " device-card-full" if device.get("full_width") else ""

    # Verlinkung auf die Gerätedetailseite
    device_key = device["key"]
    device_link = f"/device/{device_key}"

    if device["type"] in ("freezer", "memmert", "weatherhub_id01"):
        # Nur Temperatur-Kachel (ohne Feuchte) - Status-Text statt Temperatur
        return f"""
    <a class="device-card{full_width_class}" href="{device_link}">
        <div class="device-header">
            <div>
                <h2>{device["name"]}</h2>
                <div class="chip-row">{device["chips_html"]}</div>
            </div>
            <div class="status-right">
                {device["led_html"]}
                <span class="status-light {device["status"]}" aria-label="Device Status"></span>
            </div>
        </div>
        <div class="metric-full">
            <div class="metric-left">
                <span>🌡️ Temperature</span>
                <strong>{device["temp"]:.1f} <small>°C</small></strong>
            </div>
            {device["limit_chips_temp"]}
        </div>
        <div class="device-chart">
            <canvas id="{device["chart_id"]}"></canvas>
        </div>
    </a>
"""

    # AtmoWEB und weatherhub_id0e (Temp + Feuchte) - Status-Text statt Temperatur
    return f"""
    <a class="device-card{full_width_class}" href="{device_link}">
        <div class="device-header">
            <div>
                <h2>{device["name"]}</h2>
                <div class="chip-row">{device["chips_html"]}</div>
            </div>
            <div class="status-right">
                {device["led_html"]}
                <span class="status-light {device["status"]}" aria-label="Device Status"></span>
            </div>
        </div>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-left">
                    <span>🌡️ Temperature</span>
                    <strong>{device["temp"]:.1f} <small>°C</small></strong>
                </div>
                {device["limit_chips_temp"]}
            </div>
            <div class="metric">
                <div class="metric-left">
                    <span>💧 Relative Humidity</span>
                    <strong>{device["hum"]:.1f} <small>%</small></strong>
                </div>
                {device["limit_chips_hum"]}
            </div>
        </div>
        <div class="device-chart">
            <canvas id="{device["chart_id"]}"></canvas>
        </div>
    </a>
"""
