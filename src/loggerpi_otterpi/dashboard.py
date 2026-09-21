"""Dashboard für den OtterPi – zeigt AtmoWEB-Daten aus SQLite."""

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from otterpi_store import BatchStore

BERLIN = ZoneInfo("Europe/Berlin")


def render_dashboard(store: BatchStore) -> str:
    """Generiert das Dashboard-HTML."""
    batches = _recent_batches(store, hours=48)

    current = _current_values(batches)

    temp_101 = _series(batches, "atmoweb_101.temperature_1")
    hum_101 = _series(batches, "atmoweb_101.humidity")
    temp_102 = _series(batches, "atmoweb_102.temperature_1")
    hum_102 = _series(batches, "atmoweb_102.humidity")

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🦦 ZOOLOGY-observer Dashboard v1.2.1</title>
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

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-top: 30px;
}}

.card {{
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.card h2 {{ margin-top: 0; font-size: 1.1rem; }}

.value {{
    font-size: 2rem;
    font-weight: 700;
    margin: 10px 0 0 0;
}}

.value-blue {{ color: #38bdf8; }}
.value-orange {{ color: #eab308; }}

.unit {{ font-size: 1rem; color: #9ca3af; }}

.chart-card {{
    grid-column: 1 / -1;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 20px;
}}

.chart-card h2 {{ margin-top: 0; }}

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
<h1>🦦 ZOOLOGY-observer Dashboard v1.2.1</h1>
<div class="subtitle">MEMMERT HPP260 Klimaschränke · Letzte 48 Stunden</div>

<div class="grid">
    <div class="card">
        <h2>🌡 Temperatur links</h2>
        <div class="value value-blue">{current["temp_101"]:.1f} <span class="unit">°C</span></div>
    </div>
    <div class="card">
        <h2>💧 Rel. Feuchte links</h2>
        <div class="value value-blue">{current["hum_101"]:.1f} <span class="unit">%</span></div>
    </div>
    <div class="card">
        <h2>🌡 Temperatur rechts</h2>
        <div class="value value-orange">{current["temp_102"]:.1f} <span class="unit">°C</span></div>
    </div>
    <div class="card">
        <h2>💧 Rel. Feuchte rechts</h2>
        <div class="value value-orange">{current["hum_102"]:.1f} <span class="unit">%</span></div>
    </div>

    <div class="chart-card">
        <h2>📈 Temperatur (48h)</h2>
        <canvas id="tempChart"></canvas>
    </div>

    <div class="chart-card">
        <h2>📈 Rel. Feuchte (48h)</h2>
        <canvas id="humChart"></canvas>
    </div>

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

<div class="footer">🦦 otterpi · ZOOLOGY-observer Dashboard v1.2.1</div>
</div>

<script>
const tempLabels = {json.dumps([b["label"] for b in temp_101])};
const temp101 = {json.dumps([b["value"] for b in temp_101])};
const temp102 = {json.dumps([b["value"] for b in temp_102])};
const humLabels = {json.dumps([b["label"] for b in hum_101])};
const hum101 = {json.dumps([b["value"] for b in hum_101])};
const hum102 = {json.dumps([b["value"] for b in hum_102])};

new Chart(document.getElementById('tempChart'), {{
    type: 'line',
    data: {{
        labels: tempLabels,
        datasets: [
            {{ label: 'HPP260 links', data: temp101, borderColor: '#38bdf8', tension: 0.3 }},
            {{ label: 'HPP260 rechts', data: temp102, borderColor: '#eab308', tension: 0.3 }}
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#d1d5db' }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }} }}
        }}
    }}
}});

new Chart(document.getElementById('humChart'), {{
    type: 'line',
    data: {{
        labels: humLabels,
        datasets: [
            {{ label: 'HPP260 links', data: hum101, borderColor: '#38bdf8', tension: 0.3 }},
            {{ label: 'HPP260 rechts', data: hum102, borderColor: '#eab308', tension: 0.3 }}
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#d1d5db' }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }} }}
        }}
    }}
}});
</script>
</body>
</html>
"""


def _recent_batches(store: BatchStore, hours: int = 48) -> list[dict]:
    """Liest die letzten Batches aus SQLite (max. 192 für 48h bei 15-min-Intervall)."""
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

    # Chronologisch sortieren (älteste zuerst)
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
        datetime.fromisoformat(latest["created_at"]).astimezone(BERLIN).strftime("%d.%m.%Y %H:%M")
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


def _series(batches: list[dict], key: str) -> list[dict]:
    """Extrahiert eine Messwert-Reihe aus den Batches."""
    series = []
    for batch in batches:
        measurement = batch.get("measurements", {}).get(key, {})
        value = measurement.get("value")
        measured_at = measurement.get("measured_at")

        if value is not None and measured_at:
            label = datetime.fromisoformat(measured_at).astimezone(BERLIN).strftime("%H:%M")
            series.append({"label": label, "value": value})

    return series
