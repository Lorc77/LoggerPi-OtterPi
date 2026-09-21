"""Dashboard für den OtterPi – Raum-basiert mit Geräte-Übersicht."""

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from otterpi_store import BatchStore

BERLIN = ZoneInfo("Europe/Berlin")
VERSION = "v1.2.4"

ROOMS = {
    "r1304": {
        "name": "R1304 · Kulturraum I",
        "icon": "🦗",
        "devices": [
            {"name": "MEMMERT HPP260 links", "key": "atmoweb_101"},
            {"name": "MEMMERT HPP260 rechts", "key": "atmoweb_102"},
        ],
    },
    "r1306": {
        "name": "R1306 · Molekularlab",
        "icon": "🧬",
        "devices": [],
    },
    "r1307": {
        "name": "R1307 · Vorraum Kühlkammer",
        "icon": "❄️",
        "devices": [],
    },
    "r1308": {
        "name": "R1308 · Kulturraum II",
        "icon": "🧫",
        "devices": [],
    },
    "r1309": {
        "name": "R1309 · RNA-lab",
        "icon": "🧪",
        "devices": [],
    },
    "r1310": {
        "name": "R1310 · Histolab",
        "icon": "🔬",
        "devices": [],
    },
    "r1311": {
        "name": "R1311 · Immunolab",
        "icon": "🦠",
        "devices": [],
    },
    "r1313": {
        "name": "R1313 · Praktikumsraum",
        "icon": "🎓",
        "devices": [],
    },
}


def render_dashboard(store: BatchStore, room_id: str = "") -> str:
    """Generiert das Dashboard-HTML."""
    if room_id and room_id in ROOMS:
        return _render_room_detail(store, room_id)

    return _render_overview(store)


def _render_overview(store: BatchStore) -> str:
    """Einstiegsseite mit Raum-Kacheln."""
    batches = _recent_batches(store, hours=48)

    room_cards = ""
    for room_id, room in ROOMS.items():
        has_devices = bool(room["devices"])

        if has_devices:
            device_lines = ""
            for device in room["devices"]:
                current = _device_current(batches, device["key"])
                current["status"] = _device_status(batches, device["key"])
                device_lines += (
                    f'<div class="device-line">'
                    f'<span class="lamp {current["status"]}"></span>'
                    f"<span>{device['name']}</span>"
                    f'<span class="device-value">{current["value"]}</span>'
                    f"</div>"
                )

            card = (
                f'<a class="room-card" href="/raum/{room_id}">'
                f"<h2>{room['icon']} {room['name']}</h2>"
                f'<div class="device-list">{device_lines}</div>'
                f"</a>"
            )
        else:
            card = (
                f'<div class="room-card room-card-empty">'
                f"<h2>{room['icon']} {room['name']}</h2>"
                f'<div class="device-list">'
                f'<div class="device-line no-devices">Keine Geräte</div>'
                f"</div>"
                f"</div>"
            )

        room_cards += card

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

.room-card h2 {{ margin-top: 0; font-size: 1.1rem; }}

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
}}
</style>
</head>
<body>
<div class="container">
<h1>📡 ZOOLOGY-Observer Dashboard</h1>
<div class="subtitle">Räume & Geräte · Letzte Aktualisierung</div>

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
    room = ROOMS[room_id]
    batches = _recent_batches(store, hours=48)

    current = _current_values(batches)

    temp_101 = _series(batches, "atmoweb_101.temperature_1")
    hum_101 = _series(batches, "atmoweb_101.humidity")
    temp_102 = _series(batches, "atmoweb_102.temperature_1")
    hum_102 = _series(batches, "atmoweb_102.humidity")
    series_by_device = {
        "atmoweb_101": (temp_101, hum_101),
        "atmoweb_102": (temp_102, hum_102),
    }

    device_views = []
    for device in room["devices"]:
        temp_series, hum_series = series_by_device.get(device["key"], ([], []))
        device_current = _device_current(batches, device["key"])
        chart_id = f"chart-{device['key']}"
        device_views.append(
            {
                "name": device["name"],
                "status": _device_status(batches, device["key"]),
                "temp": device_current["temp"],
                "hum": device_current["hum"],
                "chart_id": chart_id,
                "temp_labels": [point["label"] for point in temp_series],
                "temp_values": [point["value"] for point in temp_series],
                "hum_labels": [point["label"] for point in hum_series],
                "hum_values": [point["value"] for point in hum_series],
                "labels_json": json.dumps([point["label"] for point in temp_series or hum_series]),
                "temp_values_json": json.dumps([point["value"] for point in temp_series]),
                "hum_values_json": json.dumps([point["value"] for point in hum_series]),
            }
        )

    device_cards = "".join(
        f"""
    <section class="device-card">
        <div class="device-header">
            <div>
                <h2>{device["name"]}</h2>
                <span class="device-status-label">Status</span>
            </div>
            <span class="status-light {device["status"]}" aria-label="Gerätestatus"></span>
        </div>
        <div class="metric-grid">
            <div class="metric">
                <span>🌡 Temperatur</span>
                <strong>{device["temp"]:.1f} <small>°C</small></strong>
            </div>
            <div class="metric">
                <span>💧 Rel. Feuchte</span>
                <strong>{device["hum"]:.1f} <small>%</small></strong>
            </div>
        </div>
        <div class="device-chart">
            <canvas id="{device["chart_id"]}"></canvas>
        </div>
    </section>
"""
        for device in device_views
    )

    device_scripts = "".join(
        f"""
const {device["chart_id"].replace("-", "_")}Labels = {device["labels_json"]};
new Chart(document.getElementById('{device["chart_id"]}'), {{
    type: 'line',
    data: {{
        labels: {device["chart_id"].replace("-", "_")}Labels,
        datasets: [
            {{ label: 'Temperatur', data: {device["temp_values_json"]},
                borderColor: '#fb923c', borderWidth: 1.5,
                yAxisID: 'temperature', tension: 0.3 }},
            {{ label: 'Rel. Feuchte', data: {device["hum_values_json"]},
                borderColor: '#38bdf8', borderWidth: 1.5,
                yAxisID: 'humidity', tension: 0.3 }}
        ]
    }},
    options: {{
        responsive: true,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{ legend: {{ labels: {{ color: '#d1d5db' }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            temperature: {{
                type: 'linear', position: 'left',
                ticks: {{
                    color: '#fb923c',
                    callback: (value) => value + ' °C'
                }}
            }},
            humidity: {{
                type: 'linear', position: 'right',
                ticks: {{
                    color: '#38bdf8',
                    callback: (value) => value + ' %'
                }},
                grid: {{ drawOnChartArea: false }}
            }}
        }}
    }}
}});
"""
        for device in device_views
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

.grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.device-card, .system-card {{
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.device-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 76px;
}}

.device-header h2 {{ margin: 0; font-size: 1.1rem; }}

.device-status-label {{
    display: block;
    margin-top: 5px;
    color: #9ca3af;
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
}}

.metric span {{
    display: block;
    color: #d1d5db;
    font-size: .8rem;
}}

.metric strong {{
    display: block;
    margin-top: 5px;
    font-size: 1.35rem;
}}

.metric small {{
    color: #9ca3af;
    font-size: .8rem;
}}

.device-chart {{
    position: relative;
    height: 280px;
    margin-top: 18px;
}}

.system-card {{
    grid-column: 1 / -1;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
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
}}
</style>
</head>
<body>
<div class="container">
<a class="back-btn" href="/">← Zur Übersicht</a>
<h1>{room["icon"]} {room["name"]}</h1>
<div class="subtitle">Letzte 48 Stunden</div>

<div class="grid">
{device_cards}

    <div class="system-card">
        <h2>🖥 System</h2>
        <div class="system-line">
            <span>Letzter Batch:</span><span>{current["last_batch"]}</span>
        </div>
        <div class="system-line">
            <span>Batches (48h):</span><span>{len(batches)}</span>
        </div>
        <div class="system-line">
            <span>CPU-Temperatur:</span><span>{current["cpu_temp"]:.1f} °C</span>
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


def _recent_batches(store: BatchStore, hours: int = 48) -> list[dict]:
    """Liest die letzten Batches aus SQLite."""
    import sqlite3

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    with sqlite3.connect(store.path) as conn:
        rows = conn.execute("SELECT payload FROM batches ORDER BY rowid DESC LIMIT 192").fetchall()

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

    if temp_101.get("value") is not None:
        current["temp_101"] = temp_101["value"]
    if hum_101.get("value") is not None:
        current["hum_101"] = hum_101["value"]
    if temp_102.get("value") is not None:
        current["temp_102"] = temp_102["value"]
    if hum_102.get("value") is not None:
        current["hum_102"] = hum_102["value"]

    system = latest.get("system", {})
    cpu = system.get("cpu", {})
    if cpu.get("temperature_celsius") is not None:
        current["cpu_temp"] = cpu["temperature_celsius"]

    memory = latest.get("memory", {})
    if memory.get("total_bytes") and memory.get("used_bytes"):
        current["memory_used"] = memory["used_bytes"] / memory["total_bytes"] * 100

    return current


def _device_current(batches: list[dict], key: str) -> dict:
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


def _device_status(batches: list[dict], key: str) -> str:
    """Ermittelt den erweiterten Status für die Gerätekachel."""
    if not batches:
        return "status-off"

    measurements = batches[-1].get("measurements", {})
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
            label = measured_at[11:16]
            series.append({"label": label, "value": value})

    return series
