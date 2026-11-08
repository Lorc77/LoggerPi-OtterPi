"""Admin-UI für den OtterPi."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from dashboard_constants import VERSION

BERLIN = ZoneInfo("Europe/Berlin")


def render_admin(config: dict, last_batch_at: str = "") -> str:
    from sensor_schemas import SENSOR_SCHEMAS

    if last_batch_at:
        last_update = (
            datetime.fromisoformat(last_batch_at).astimezone(BERLIN).strftime("%d.%m.%Y %H:%M Uhr")
        )
    else:
        last_update = "–"
    rooms_json = json.dumps(config["rooms"], ensure_ascii=False, indent=2)
    alarm_json = json.dumps(config["alarm_limits"], ensure_ascii=False, indent=2)
    mail_json = json.dumps(config["mail"], ensure_ascii=False, indent=2)
    notifications_json = json.dumps(config["notifications"], ensure_ascii=False, indent=2)
    sensor_schemas_json = json.dumps(SENSOR_SCHEMAS, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🛠 ZOOLOGY-Observer Admin</title>
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
.subtitle {{ text-align: center; color: #d1d5db; margin-bottom: 20px; }}
.tabs {{
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}}
.tab-btn {{
    padding: 10px 20px;
    border-radius: 10px;
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.15);
    color: #d1d5db;
    cursor: pointer;
    font-size: .95rem;
    transition: .2s;
}}
.tab-btn:hover {{
    background: rgba(147,197,253,.15);
    border-color: rgba(147,197,253,.5);
}}
.tab-btn.active {{
    background: rgba(147,197,253,.25);
    border-color: rgba(147,197,253,.6);
    color: #bfdbfe;
}}
.footer {{
    text-align: center;
    margin-top: 30px;
    color: #d1d5db;
    opacity: .85;
    font-size: .9rem;
}}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}
input[type="text"], input[type="number"], select, textarea {{
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.15);
    border-radius: 10px;
    color: white;
    padding: 10px 12px;
    font-size: .95rem;
    width: 100%;
}}
input[type="text"]:focus, input[type="number"]:focus, select:focus, textarea:focus {{
    outline: none;
    border-color: rgba(147,197,253,.5);
}}
input[type="checkbox"] {{
    width: auto;
    accent-color: #93c5fd;
}}
textarea {{
    min-height: 400px;
    font-family: ui-monospace, monospace;
    font-size: .85rem;
}}
.rooms-list {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 16px;
}}
.room-card {{
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    padding: 16px;
}}
.room-card h3 {{
    margin: 0 0 8px 0;
    font-size: 1.1rem;
}}
.room-card p {{
    margin: 4px 0;
    color: #d1d5db;
    font-size: .9rem;
}}
.devices-table {{
    width: 100%;
    margin-top: 8px;
    border-collapse: collapse;
    font-size: .85rem;
}}
.devices-table th, .devices-table td {{
    padding: 4px 8px;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,.08);
}}
.devices-table th {{
    color: #9ca3af;
    font-weight: normal;
}}
.config-group {{
    margin-bottom: 20px;
}}
.config-group h4 {{
    color: #bfdbfe;
    margin: 0 0 10px 0;
    font-size: 1rem;
}}
.config-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}}
.config-item {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.config-item label {{
    color: #9ca3af;
    font-size: .85rem;
    min-width: 200px;
    max-width: 200px;
    white-space: nowrap;
}}
.config-item input {{
    flex: 1;
    padding: 8px 10px;
    font-size: .9rem;
    min-width: 0;
}}
.config-item-full {{
    grid-column: 1 / -1;
}}
.config-item-full input {{
    max-width: none;
}}
.inline-form {{
    margin-top: 12px;
    padding: 12px;
    background: rgba(147,197,253,.1);
    border: 1px solid rgba(147,197,253,.3);
    border-radius: 8px;
}}
.inline-form h4 {{
    margin: 0 0 8px 0;
    color: #bfdbfe;
}}
.inline-form label {{
    display: block;
    margin: 6px 0;
    color: #d1d5db;
    font-size: .9rem;
}}
.inline-form input, .inline-form select {{
    width: 100%;
    padding: 6px 10px;
    margin-top: 4px;
    border-radius: 6px;
    border: 1px solid rgba(147,197,253,.4);
    background: rgba(31,41,55,.78);
    color: white;
    font-size: .9rem;
}}
.howto {{
    background: rgba(147,197,253,.1);
    border: 1px solid rgba(147,197,253,.3);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
}}
.howto summary {{
    cursor: pointer;
    color: #bfdbfe;
    font-weight: 600;
}}
.howto ol {{
    margin: 8px 0 0 0;
    padding-left: 20px;
    color: #d1d5db;
    font-size: .9rem;
}}
.hint {{
    color: #bfdbfe;
    font-size: .85rem;
    margin: 6px 0;
    font-style: italic;
}}
.save-row {{ display: flex; gap: 12px; align-items: center; margin-top: 12px; }}
.btn {{
    padding: 12px 24px;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    transition: .2s;
}}
.btn-primary {{
    background: rgba(147,197,253,.25);
    border: 1px solid rgba(147,197,253,.5);
    color: #bfdbfe;
}}
.btn-primary:hover {{
    background: rgba(147,197,253,.35);
    transform: translateY(-2px);
}}
.btn-secondary {{
    background: rgba(31,41,55,.78);
    border: 1px solid rgba(255,255,255,.15);
    color: #d1d5db;
}}
.btn-secondary:hover {{
    background: rgba(147,197,253,.15);
    border-color: rgba(147,197,253,.5);
    color: #bfdbfe;
}}
.btn-danger {{
    background: rgba(239,68,68,.15);
    border: 1px solid rgba(239,68,68,.4);
    color: #fca5a5;
    padding: 6px 12px;
    font-size: .85rem;
    border-radius: 8px;
    cursor: pointer;
    transition: .2s;
}}
.btn-danger:hover {{
    background: rgba(239,68,68,.3);
    border-color: rgba(239,68,68,.6);
}}
.btn-warning {{
    background: rgba(245,158,11,.15);
    border: 1px solid rgba(245,158,11,.4);
    color: #fcd34d;
    padding: 6px 12px;
    font-size: .85rem;
    border-radius: 8px;
    cursor: pointer;
    transition: .2s;
}}
.btn-warning:hover {{
    background: rgba(245,158,11,.3);
    border-color: rgba(245,158,11,.6);
}}
.btn-small {{
    padding: 4px 10px;
    font-size: .75rem;
    border-radius: 6px;
}}
.alerts-list {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
}}
.alert-card {{
    padding: 12px 15px;
    background: rgba(31,41,55,.5);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,.1);
}}
.alert-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}}
.alert-header strong {{
    color: #bfdbfe;
    font-size: 1rem;
}}
.alert-severity {{
    margin-left: auto;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: .75rem;
    font-weight: 600;
    text-transform: uppercase;
    background: rgba(147,197,253,.15);
    color: #bfdbfe;
}}
.alert-meta {{
    color: #9ca3af;
    font-size: .85rem;
    margin-bottom: 6px;
}}
.alert-message {{
    color: #d1d5db;
    font-size: .9rem;
    margin-bottom: 8px;
}}
.alert-actions {{
    display: flex;
    gap: 8px;
}}
.alert-ack {{
    color: #22c55e;
    font-size: .85rem;
}}
.status {{ color: #d1d5db; font-size: .9rem; }}
</style>
</head>
<body>
<div class="container">
<h1>🛠 ZOOLOGY-Observer Admin</h1>
<div class="subtitle">Last update: {last_update}</div>
<div class="tabs">
    <button class="tab-btn active" onclick="showTab('rooms', this)">🏠 Rooms</button>
    <button class="tab-btn" onclick="showTab('alarm', this)">⚠️ Alarm Limits</button>
    <button class="tab-btn" onclick="showTab('mail', this)">📧 Mail</button>
    <button class="tab-btn" onclick="showTab('notifications', this)">🔔 Notifications</button>
    <button class="tab-btn" onclick="showTab('alerts', this)">🚨 Alerts</button>
</div>

<div id="tab-rooms" class="tab-panel active">
    <details class="howto">
        <summary>How-to: Add a new WeatherHub sensor</summary>
        <ol>
            <li>Put the sensor into operation (insert battery, pair).</li>
            <li>Read the sensor ID from the gateway log or from the batch.</li>
            <li>Click "+ Add WeatherHub-Sensor" and enter sensor ID, name, type, room.</li>
            <li>The sensor appears in the dashboard and in the alert engine.</li>
        </ol>
    </details>
    <div id="rooms-list" class="rooms-list"></div>
    <div class="save-row">
        <button class="save-btn" onclick="showAddRoomForm()">+ Add Room</button>
        <button class="save-btn" onclick="toggleRoomsJson()">Advanced (JSON)</button>
        <span id="rooms-status" class="status"></span>
    </div>
    <div id="rooms-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="rooms-text">{rooms_json}</textarea>
        <div class="save-row">
            <button class="save-btn"
                    data-endpoint="/api/admin/rooms"
                    data-textarea="rooms-text"
                    data-status="rooms-status"
                    onclick="saveConfig(this)">Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-alarm" class="tab-panel">
    <details class="howto">
        <summary>How-to: Configure alert limits</summary>
        <ol>
            <li>Click "Edit Limits" on a device to configure warning/critical limits.</li>
            <li>WeatherHub sensors are automatically added to the alert engine
                (battery_low state).</li>
            <li>Limits are checked after every batch and every 300 seconds.</li>
            <li>Alerts are deduplicated, respect quiet hours, and are sent via the
                configured notifiers.</li>
        </ol>
    </details>
    <div id="alarm-list" class="rooms-list"></div>
    <div class="save-row">
        <button class="save-btn" onclick="toggleAlarmJson()">Advanced (JSON)</button>
        <span id="alarm-status" class="status"></span>
    </div>
    <div id="alarm-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="alarm-text">{alarm_json}</textarea>
        <div class="save-row">
            <button class="save-btn"
                    data-endpoint="/api/admin/alarm-limits"
                    data-textarea="alarm-text"
                    data-status="alarm-status"
                    onclick="saveConfig(this)">Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-mail" class="tab-panel">
    <div id="mail-form"></div>
    <div class="save-row">
        <button class="save-btn" onclick="saveMailForm()">Save</button>
        <button class="save-btn" onclick="sendTestMail(this)">Send Test Mail</button>
        <button class="save-btn" onclick="toggleMailJson()">Advanced (JSON)</button>
        <span id="mail-status" class="status"></span>
    </div>
    <div id="mail-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="mail-text">{mail_json}</textarea>
        <div class="save-row">
            <button class="save-btn"
                    data-endpoint="/api/admin/mail"
                    data-textarea="mail-text"
                    data-status="mail-status"
                    onclick="saveConfig(this)">Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-notifications" class="tab-panel">
    <div id="notifications-list" class="rooms-list"></div>
    <div class="save-row">
        <button class="save-btn" onclick="showAddChannelForm()">+ Add Channel</button>
        <button class="save-btn" onclick="toggleNotificationsJson()">Advanced (JSON)</button>
        <span id="notifications-status" class="status"></span>
    </div>
    <div id="notifications-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="notifications-text">{notifications_json}</textarea>
        <div class="save-row">
            <button class="save-btn"
                    data-endpoint="/api/admin/notifications"
                    data-textarea="notifications-text"
                    data-status="notifications-status"
                    onclick="saveConfig(this)">Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-alerts" class="tab-panel">
    <div class="save-row">
        <button class="save-btn" onclick="loadAlerts()">Refresh</button>
        <label>
            <input type="checkbox" id="alerts-only-unack" onchange="loadAlerts()">
            Only unacknowledged
        </label>
        <span id="alerts-status" class="status"></span>
    </div>
    <div id="alerts-list" class="alerts-list"></div>
</div>
<div class="footer">🦦 otterpi · ZOOLOGY-Observer Admin {VERSION}</div>
</div>

<script>
const SENSOR_SCHEMAS = {sensor_schemas_json};

function showTab(name, btn) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
    if (name === 'alerts') {{
        loadAlerts();
    }}
    if (name === 'rooms') {{
        loadRooms();
    }}
    if (name === 'alarm') {{
        loadAlarmLimits();
    }}
    if (name === 'mail') {{
        loadMailForm();
    }}
    if (name === 'notifications') {{
        loadNotifications();
    }}
}}

async function saveConfig(btn) {{
    const endpoint = btn.dataset.endpoint;
    const textareaId = btn.dataset.textarea;
    const statusId = btn.dataset.status;
    const status = document.getElementById(statusId);
    const text = document.getElementById(textareaId).value;
    let data;
    try {{
        data = JSON.parse(text);
    }} catch (e) {{
        status.textContent = 'Invalid JSON: ' + e.message;
        return;
    }}
    try {{
        const resp = await fetch(endpoint, {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(data)
        }});
        const result = await resp.json();
        if (resp.ok) {{
            status.textContent = 'Saved.';
        }} else {{
            status.textContent = 'Error: ' + (result.error?.message || resp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function loadRooms() {{
    const status = document.getElementById('rooms-status');
    const list = document.getElementById('rooms-list');
    status.textContent = 'Loading...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        const roomIds = Object.keys(rooms);
        list.innerHTML = '';
        for (const [roomId, room] of Object.entries(rooms)) {{
            const card = document.createElement('div');
            card.className = 'room-card';
            card.dataset.roomId = roomId;
            let devicesHtml = '';
            for (const device of room.devices) {{
                const options = roomIds.map(id => {{
                    const sel = id === roomId ? 'selected' : '';
                    return `<option value="${{id}}" ${{sel}}>${{rooms[id].name}}</option>`;
                }}).join('');
                devicesHtml += `
                    <tr>
                        <td>${{device.name}}</td>
                        <td>${{device.key}}</td>
                        <td>${{device.type}}</td>
                        <td>
                            <select onchange="moveDevice('${{device.key}}', this.value)">
                                ${{options}}
                            </select>
                        </td>
                        <td>
                            <button class="btn btn-secondary btn-small"
                                    onclick="editDevice('${{device.key}}')">✏️ Edit</button>
                            <button class="btn btn-danger btn-small"
                                    onclick="deleteDevice('${{device.key}}')">🗑 Delete</button>
                        </td>
                    </tr>
                `;
            }}
            card.innerHTML = `
                <h3>${{room.icon || ''}} ${{room.name}}</h3>
                <p>ID: ${{roomId}}</p>
                <table class="devices-table">
                    <thead>
                        <tr><th>Name</th><th>Key</th><th>Type</th><th>Room</th><th></th></tr>
                    </thead>
                    <tbody>${{devicesHtml}}</tbody>
                </table>
                <div class="save-row">
                    <button class="btn btn-primary"
                            onclick="showAddDeviceForm('${{roomId}}')">➕ Add Device</button>
                    <button class="btn btn-secondary"
                            onclick="editRoom('${{roomId}}')">✏️ Edit Room</button>
                    <button class="btn btn-danger"
                            onclick="deleteRoom('${{roomId}}')">🗑 Delete Room</button>
                </div>
            `;
            list.appendChild(card);
        }}
        status.textContent = Object.keys(rooms).length + ' room(s).';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function toggleRoomsJson() {{
    const editor = document.getElementById('rooms-json-editor');
    editor.style.display = editor.style.display === 'none' ? 'block' : 'none';
}}

async function loadAlarmLimits() {{
    const status = document.getElementById('alarm-status');
    const list = document.getElementById('alarm-list');
    status.textContent = 'Loading...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        const alarmLimits = result.alarm_limits;
        const sensors = alarmLimits.sensors || {{}};
        const states = alarmLimits.states || {{}};
        list.innerHTML = '';
        for (const [roomId, room] of Object.entries(rooms)) {{
            for (const device of room.devices) {{
                const card = document.createElement('div');
                card.className = 'room-card';
                card.dataset.deviceKey = device.key;
                const schema = SENSOR_SCHEMAS[device.type] || {{measurements: [], states: []}};
                let measurementsHtml = '';
                for (const [name, unit] of schema.measurements) {{
                    const key = device.key + '.' + name;
                    const limits = sensors[key] || {{}};
                    measurementsHtml += `
                        <tr>
                            <td>${{name}}</td>
                            <td>${{unit}}</td>
                            <td>${{limits.warning_min ?? '–'}}</td>
                            <td>${{limits.warning_max ?? '–'}}</td>
                            <td>${{limits.critical_min ?? '–'}}</td>
                            <td>${{limits.critical_max ?? '–'}}</td>
                            <td>${{limits.enabled !== false ? '✓' : '–'}}</td>
                        </tr>
                    `;
                }}
                let statesHtml = '';
                for (const [name, type] of schema.states) {{
                    const key = device.key + '.' + name;
                    const rule = states[key] || {{}};
                    statesHtml += `
                        <tr>
                            <td>${{name}}</td>
                            <td>${{type}}</td>
                            <td>${{rule.enabled !== false ? '✓' : '–'}}</td>
                        </tr>
                    `;
                }}
                card.innerHTML = `
                    <h3>${{device.name}}</h3>
                    <p>Key: ${{device.key}}</p>
                    <p>Type: ${{device.type}}</p>
                    <p>Room: ${{room.name}}</p>
                    <h4>Measurements</h4>
                    <table class="devices-table">
                        <thead>
                            <tr>
                                <th>Measurement</th>
                                <th>Unit</th>
                                <th>Warn Min</th>
                                <th>Warn Max</th>
                                <th>Crit Min</th>
                                <th>Crit Max</th>
                                <th>Enabled</th>
                            </tr>
                        </thead>
                        <tbody>${{measurementsHtml}}</tbody>
                    </table>
                    <h4>States</h4>
                    <table class="devices-table">
                        <thead>
                            <tr>
                                <th>State</th>
                                <th>Type</th>
                                <th>Enabled</th>
                            </tr>
                        </thead>
                        <tbody>${{statesHtml}}</tbody>
                    </table>
                    <div class="save-row">
                        <button class="save-btn"
                                onclick="showEditLimitsForm('${{device.key}}', '${{device.type}}')">
                            Edit Limits
                        </button>
                    </div>
                `;
                list.appendChild(card);
            }}
        }}
        status.textContent = 'Loaded.';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function showEditLimitsForm(deviceKey, deviceType) {{
    const card = document.querySelector(`[data-device-key="${{deviceKey}}"]`);
    if (!card) return;
    if (card.querySelector('.inline-form')) return;
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const alarmLimits = result.alarm_limits;
    const sensors = alarmLimits.sensors || {{}};
    const states = alarmLimits.states || {{}};
    const schema = SENSOR_SCHEMAS[deviceType] || {{measurements: [], states: []}};
    let measurementsHtml = '';
    for (const [name, unit] of schema.measurements) {{
        const key = deviceKey + '.' + name;
        const limits = sensors[key] || {{}};
        measurementsHtml += `
            <tr>
                <td>${{name}}</td>
                <td><input type="number" step="0.1" id="warn-min-${{name}}"
                        value="${{limits.warning_min ?? ''}}"></td>
                <td><input type="number" step="0.1" id="warn-max-${{name}}"
                        value="${{limits.warning_max ?? ''}}"></td>
                <td><input type="number" step="0.1" id="crit-min-${{name}}"
                        value="${{limits.critical_min ?? ''}}"></td>
                <td><input type="number" step="0.1" id="crit-max-${{name}}"
                        value="${{limits.critical_max ?? ''}}"></td>
            </tr>
        `;
    }}
    let statesHtml = '';
    for (const [name, type] of schema.states) {{
        const key = deviceKey + '.' + name;
        const rule = states[key] || {{}};
        const checked = rule.enabled !== false ? 'checked' : '';
        statesHtml += `
            <tr>
                <td>${{name}}</td>
                <td><input type="checkbox" id="state-enabled-${{name}}" ${{checked}}></td>
            </tr>
        `;
    }}
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Limits: ${{deviceKey}}</h4>
        <h5>Measurements</h5>
        <table class="devices-table">
            <thead>
                <tr>
                    <th>Measurement</th>
                    <th>Warn Min</th>
                    <th>Warn Max</th>
                    <th>Crit Min</th>
                    <th>Crit Max</th>
                </tr>
            </thead>
            <tbody>${{measurementsHtml}}</tbody>
        </table>
        <h5>States</h5>
        <table class="devices-table">
            <thead>
                <tr><th>State</th><th>Enabled</th></tr>
            </thead>
            <tbody>${{statesHtml}}</tbody>
        </table>
        <div class="save-row">
            <button class="btn btn-primary"
                    onclick="submitEditLimits('${{deviceKey}}', '${{deviceType}}')">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    card.appendChild(form);
}}

async function submitEditLimits(deviceKey, deviceType) {{
    const status = document.getElementById('alarm-status');
    status.textContent = 'Saving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const alarmLimits = result.alarm_limits;
        if (!alarmLimits.sensors) alarmLimits.sensors = {{}};
        if (!alarmLimits.states) alarmLimits.states = {{}};
        const schema = SENSOR_SCHEMAS[deviceType] || {{measurements: [], states: []}};
        for (const [name, unit] of schema.measurements) {{
            const key = deviceKey + '.' + name;
            const warnMin = document.getElementById('warn-min-' + name).value;
            const warnMax = document.getElementById('warn-max-' + name).value;
            const critMin = document.getElementById('crit-min-' + name).value;
            const critMax = document.getElementById('crit-max-' + name).value;
            const limits = {{}};
            if (warnMin) limits.warning_min = parseFloat(warnMin);
            if (warnMax) limits.warning_max = parseFloat(warnMax);
            if (critMin) limits.critical_min = parseFloat(critMin);
            if (critMax) limits.critical_max = parseFloat(critMax);
            if (Object.keys(limits).length > 0) {{
                limits.enabled = true;
                alarmLimits.sensors[key] = limits;
            }} else {{
                delete alarmLimits.sensors[key];
            }}
        }}
        for (const [name, type] of schema.states) {{
            const key = deviceKey + '.' + name;
            const enabled = document.getElementById('state-enabled-' + name).checked;
            if (enabled) {{
                alarmLimits.states[key] = {{enabled: true}};
            }} else {{
                delete alarmLimits.states[key];
            }}
        }}
        const putResp = await fetch('/api/admin/alarm-limits', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(alarmLimits)
        }});
        if (putResp.ok) {{
            status.textContent = 'Saved.';
            loadAlarmLimits();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function toggleAlarmJson() {{
    const editor = document.getElementById('alarm-json-editor');
    editor.style.display = editor.style.display === 'none' ? 'block' : 'none';
}}

async function loadMailForm() {{
    const status = document.getElementById('mail-status');
    const form = document.getElementById('mail-form');
    status.textContent = 'Loading...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const mail = result.mail;
        form.innerHTML = `
            <div class="config-group">
                <h4>SMTP</h4>
                <div class="config-grid">
                    <div class="config-item">
                        <label>SMTP Host:</label>
                        <input type="text" id="mail-smtp-host"
                                value="${{mail.smtp_host || ''}}">
                    </div>
                    <div class="config-item">
                        <label>SMTP Port:</label>
                        <input type="number" id="mail-smtp-port"
                                value="${{mail.smtp_port || 587}}">
                    </div>
                    <div class="config-item">
                        <label>SMTP User:</label>
                        <input type="text" id="mail-smtp-user"
                                value="${{mail.smtp_user || ''}}">
                    </div>
                    <div class="config-item">
                        <label>From:</label>
                        <input type="text" id="mail-from"
                                value="${{mail.from || ''}}">
                    </div>
                </div>
            </div>
            <div class="config-group">
                <h4>Recipients</h4>
                <div class="config-grid">
                    <div class="config-item config-item-full">
                        <label>Recipients (comma-separated):</label>
                        <input type="text" id="mail-recipients"
                                value="${{(mail.recipients || []).join(', ')}}">
                    </div>
                    <div class="config-item config-item-full">
                        <label>Routing Critical (comma-separated):</label>
                        <input type="text" id="mail-routing-critical"
                                value="${{(mail.routing?.critical || []).join(', ')}}">
                    </div>
                    <div class="config-item config-item-full">
                        <label>Routing Warning (comma-separated):</label>
                        <input type="text" id="mail-routing-warning"
                                value="${{(mail.routing?.warning || []).join(', ')}}">
                    </div>
                </div>
            </div>
            <div class="config-group">
                <h4>Quiet Hours</h4>
                <div class="config-grid">
                    <div class="config-item">
                        <label>Start:</label>
                        <input type="text" id="mail-quiet-start"
                                value="${{mail.quiet_hours?.start || '22:00'}}">
                    </div>
                    <div class="config-item">
                        <label>End:</label>
                        <input type="text" id="mail-quiet-end"
                                value="${{mail.quiet_hours?.end || '07:00'}}">
                    </div>
                    <div class="config-item">
                        <label>Critical Always:</label>
                        <input type="checkbox" id="mail-quiet-critical"
                                ${{mail.quiet_hours?.critical_always !== false ? 'checked' : ''}}>
                    </div>
                </div>
            </div>
            <div class="config-group">
                <h4>General</h4>
                <div class="config-grid">
                    <div class="config-item">
                        <label>Dedup Seconds:</label>
                        <input type="number" id="mail-dedup-seconds"
                                value="${{mail.dedup_seconds || 3600}}">
                    </div>
                    <div class="config-item">
                        <label>Enabled:</label>
                        <input type="checkbox" id="mail-enabled"
                                ${{mail.enabled !== false ? 'checked' : ''}}>
                    </div>
                </div>
            </div>
        `;
        status.textContent = 'Loaded.';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function saveMailForm() {{
    const status = document.getElementById('mail-status');
    status.textContent = 'Saving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const mail = result.mail;
        mail.smtp_host = document.getElementById('mail-smtp-host').value.trim();
        mail.smtp_port = parseInt(document.getElementById('mail-smtp-port').value);
        mail.smtp_user = document.getElementById('mail-smtp-user').value.trim();
        mail.from = document.getElementById('mail-from').value.trim();
        mail.recipients = document.getElementById('mail-recipients').value
            .split(',').map(s => s.trim()).filter(s => s);
        mail.routing = {{
            critical: document.getElementById('mail-routing-critical').value
                .split(',').map(s => s.trim()).filter(s => s),
            warning: document.getElementById('mail-routing-warning').value
                .split(',').map(s => s.trim()).filter(s => s)
        }};
        mail.dedup_seconds = parseInt(
            document.getElementById('mail-dedup-seconds').value
        );
        mail.quiet_hours = {{
            start: document.getElementById('mail-quiet-start').value.trim(),
            end: document.getElementById('mail-quiet-end').value.trim(),
            critical_always: document.getElementById('mail-quiet-critical').checked
        }};
        mail.enabled = document.getElementById('mail-enabled').checked;
        const putResp = await fetch('/api/admin/mail', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(mail)
        }});
        if (putResp.ok) {{
            status.textContent = 'Saved.';
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function toggleMailJson() {{
    const editor = document.getElementById('mail-json-editor');
    editor.style.display = editor.style.display === 'none' ? 'block' : 'none';
}}

async function loadNotifications() {{
    const status = document.getElementById('notifications-status');
    const list = document.getElementById('notifications-list');
    status.textContent = 'Loading...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const notifications = result.notifications;
        const channels = notifications.channels || [];
        list.innerHTML = '';
        for (let i = 0; i < channels.length; i++) {{
            const channel = channels[i];
            const card = document.createElement('div');
            card.className = 'room-card';
            card.innerHTML = `
                <h3>${{channel.type}}</h3>
                <p>Enabled: ${{channel.enabled ? '✓' : '–'}}</p>
                <p>URL: ${{channel.url || '–'}}</p>
                ${{channel.type === 'ntfy' ? `<p>Topic: ${{channel.topic || '–'}}</p>` : ''}}
                ${{
                    channel.type === 'webhook'
                        ? `<p>Format: ${{channel.format || 'generic'}}</p>`
                        : ''
                }}
                <div class="save-row">
                    <button class="save-btn"
                            onclick="editChannel(${{i}})">Edit</button>
                    <button class="save-btn"
                            onclick="deleteChannel(${{i}})">Delete</button>
                </div>
            `;
            list.appendChild(card);
        }}
        status.textContent = channels.length + ' channel(s).';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function toggleNotificationsJson() {{
    const editor = document.getElementById('notifications-json-editor');
    editor.style.display = editor.style.display === 'none' ? 'block' : 'none';
}}

function showAddChannelForm() {{
    const list = document.getElementById('notifications-list');
    if (list.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Add Channel</h4>
        <label>Type: <select id="new-channel-type" onchange="updateChannelForm()">
            <option value="ntfy">ntfy</option>
            <option value="webhook">webhook</option>
        </select></label>
        <label>URL: <input type="text" id="new-channel-url"></label>
        <label>Topic (ntfy): <input type="text" id="new-channel-topic"></label>
        <label>Token (ntfy): <input type="text" id="new-channel-token"></label>
        <label>Format (webhook): <select id="new-channel-format">
            <option value="generic">generic</option>
            <option value="discord">discord</option>
            <option value="slack">slack</option>
        </select></label>
        <label>Enabled: <input type="checkbox" id="new-channel-enabled" checked></label>
        <div class="save-row">
            <button class="btn btn-primary" onclick="submitAddChannel()">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    list.appendChild(form);
    updateChannelForm();
}}

function updateChannelForm() {{
    const type = document.getElementById('new-channel-type').value;
    document.getElementById('new-channel-topic').parentElement.style.display =
        type === 'ntfy' ? 'block' : 'none';
    document.getElementById('new-channel-token').parentElement.style.display =
        type === 'ntfy' ? 'block' : 'none';
    document.getElementById('new-channel-format').parentElement.style.display =
        type === 'webhook' ? 'block' : 'none';
}}

async function submitAddChannel() {{
    const type = document.getElementById('new-channel-type').value;
    const url = document.getElementById('new-channel-url').value.trim();
    const enabled = document.getElementById('new-channel-enabled').checked;
    if (!url) {{
        alert('URL required.');
        return;
    }}
    const channel = {{type: type, enabled: enabled, url: url}};
    if (type === 'ntfy') {{
        channel.topic = document.getElementById('new-channel-topic').value.trim();
        const token = document.getElementById('new-channel-token').value.trim();
        if (token) channel.token = token;
    }} else if (type === 'webhook') {{
        channel.format = document.getElementById('new-channel-format').value;
    }}
    const status = document.getElementById('notifications-status');
    status.textContent = 'Adding...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const notifications = result.notifications;
        if (!notifications.channels) notifications.channels = [];
        notifications.channels.push(channel);
        const putResp = await fetch('/api/admin/notifications', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(notifications)
        }});
        if (putResp.ok) {{
            status.textContent = 'Added.';
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function deleteChannel(index) {{
    if (!confirm('Delete channel ' + index + '?')) return;
    const status = document.getElementById('notifications-status');
    status.textContent = 'Deleting...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const notifications = result.notifications;
        notifications.channels.splice(index, 1);
        const putResp = await fetch('/api/admin/notifications', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(notifications)
        }});
        if (putResp.ok) {{
            status.textContent = 'Deleted.';
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function editChannel(index) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const notifications = result.notifications;
    const channel = notifications.channels[index];
    const list = document.getElementById('notifications-list');
    if (list.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Channel</h4>
        <label>Type: <select id="edit-channel-type" onchange="updateEditChannelForm()">
            <option value="ntfy" ${{channel.type === 'ntfy' ? 'selected' : ''}}>ntfy</option>
            <option value="webhook"
                    ${{channel.type === 'webhook' ? 'selected' : ''}}>webhook</option>
        </select></label>
        <label>URL: <input type="text" id="edit-channel-url"
                value="${{channel.url || ''}}"></label>
        <label>Topic (ntfy): <input type="text" id="edit-channel-topic"
                value="${{channel.topic || ''}}"></label>
        <label>Token (ntfy): <input type="text" id="edit-channel-token"
                value="${{channel.token || ''}}"></label>
        <label>Format (webhook): <select id="edit-channel-format">
            <option value="generic"
                    ${{channel.format === 'generic' ? 'selected' : ''}}>generic</option>
            <option value="discord"
                    ${{channel.format === 'discord' ? 'selected' : ''}}>discord</option>
            <option value="slack" ${{channel.format === 'slack' ? 'selected' : ''}}>slack</option>
        </select></label>
        <label>Enabled: <input type="checkbox" id="edit-channel-enabled"
                ${{channel.enabled ? 'checked' : ''}}></label>
        <div class="save-row">
            <button class="btn btn-primary"
                    onclick="submitEditChannel(${{index}})">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    list.appendChild(form);
    updateEditChannelForm();
}}

function updateEditChannelForm() {{
    const type = document.getElementById('edit-channel-type').value;
    document.getElementById('edit-channel-topic').parentElement.style.display =
        type === 'ntfy' ? 'block' : 'none';
    document.getElementById('edit-channel-token').parentElement.style.display =
        type === 'ntfy' ? 'block' : 'none';
    document.getElementById('edit-channel-format').parentElement.style.display =
        type === 'webhook' ? 'block' : 'none';
}}

async function submitEditChannel(index) {{
    const type = document.getElementById('edit-channel-type').value;
    const url = document.getElementById('edit-channel-url').value.trim();
    const enabled = document.getElementById('edit-channel-enabled').checked;
    if (!url) {{
        alert('URL required.');
        return;
    }}
    const channel = {{type: type, enabled: enabled, url: url}};
    if (type === 'ntfy') {{
        channel.topic = document.getElementById('edit-channel-topic').value.trim();
        const token = document.getElementById('edit-channel-token').value.trim();
        if (token) channel.token = token;
    }} else if (type === 'webhook') {{
        channel.format = document.getElementById('edit-channel-format').value;
    }}
    const status = document.getElementById('notifications-status');
    status.textContent = 'Saving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const notifications = result.notifications;
        notifications.channels[index] = channel;
        const putResp = await fetch('/api/admin/notifications', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(notifications)
        }});
        if (putResp.ok) {{
            status.textContent = 'Saved.';
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function moveDevice(deviceKey, newRoomId) {{
    const status = document.getElementById('rooms-status');
    status.textContent = 'Moving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        let device = null;
        for (const room of Object.values(rooms)) {{
            const idx = room.devices.findIndex(d => d.key === deviceKey);
            if (idx >= 0) {{
                device = room.devices.splice(idx, 1)[0];
                break;
            }}
        }}
        if (!device) {{
            status.textContent = 'Device not found.';
            return;
        }}
        rooms[newRoomId].devices.push(device);
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Moved.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function showAddDeviceForm(roomId) {{
    const card = document.querySelector(`[data-room-id="${{roomId}}"]`);
    if (!card) return;
    if (card.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    const typeOptions = Object.keys(SENSOR_SCHEMAS).map(
        t => `<option value="${{t}}">${{t}}</option>`
    ).join('');
    form.innerHTML = `
        <h4>Add Device</h4>
        <label>Name: <input type="text" id="new-device-name"></label>
        <label>Key: <input type="text" id="new-device-key"></label>
        <label>Type: <select id="new-device-type"
                onchange="updateWeatherHubHint()">${{typeOptions}}</select></label>
        <p id="weatherhub-hint" class="hint" style="display: none;">
            WeatherHub sensors are automatically added to the alert engine
            (battery_low state).
        </p>
        <div class="save-row">
            <button class="btn btn-primary"
                    onclick="submitAddDevice('${{roomId}}')">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    card.appendChild(form);
    updateWeatherHubHint();
}}

function updateWeatherHubHint() {{
    const type = document.getElementById('new-device-type').value;
    const hint = document.getElementById('weatherhub-hint');
    hint.style.display = type.startsWith('weatherhub_') ? 'block' : 'none';
}}

async function submitAddDevice(roomId) {{
    const name = document.getElementById('new-device-name').value.trim();
    const key = document.getElementById('new-device-key').value.trim();
    const type = document.getElementById('new-device-type').value;
    if (!name || !key || !type) {{
        alert('All fields required.');
        return;
    }}
    await addDevice(roomId, name, key, type);
    if (type.startsWith('weatherhub_')) {{
        await addWeatherHubToAlertEngine(key);
    }}
}}

async function addWeatherHubToAlertEngine(deviceKey) {{
    const status = document.getElementById('rooms-status');
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const alarmLimits = result.alarm_limits;
        if (!alarmLimits.states) alarmLimits.states = {{}};
        alarmLimits.states[deviceKey + '.battery_low'] = {{enabled: true}};
        const putResp = await fetch('/api/admin/alarm-limits', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(alarmLimits)
        }});
        if (!putResp.ok) {{
            const err = await putResp.json();
            status.textContent = 'Error (alarm-limits): ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function addDevice(roomId, name, key, type) {{
    const status = document.getElementById('rooms-status');
    status.textContent = 'Adding...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        rooms[roomId].devices.push({{name: name, key: key, type: type}});
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Added.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function deleteDevice(deviceKey) {{
    if (!confirm('Delete device ' + deviceKey + '?')) return;
    const status = document.getElementById('rooms-status');
    status.textContent = 'Deleting...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        for (const room of Object.values(rooms)) {{
            const idx = room.devices.findIndex(d => d.key === deviceKey);
            if (idx >= 0) {{
                room.devices.splice(idx, 1);
                break;
            }}
        }}
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Deleted.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function editDevice(deviceKey) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const rooms = result.rooms.rooms;
    let device = null;
    let roomId = null;
    for (const [rid, room] of Object.entries(rooms)) {{
        const found = room.devices.find(d => d.key === deviceKey);
        if (found) {{
            device = found;
            roomId = rid;
            break;
        }}
    }}
    if (!device) return;
    const card = document.querySelector(`[data-room-id="${{roomId}}"]`);
    if (!card) return;
    if (card.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Device</h4>
        <label>Name: <input type="text" id="edit-device-name" value="${{device.name}}"></label>
        <div class="save-row">
            <button class="btn btn-primary"
                    onclick="submitEditDevice('${{deviceKey}}')">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    card.appendChild(form);
}}

async function submitEditDevice(deviceKey) {{
    const name = document.getElementById('edit-device-name').value.trim();
    if (!name) {{
        alert('Name required.');
        return;
    }}
    const status = document.getElementById('rooms-status');
    status.textContent = 'Saving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        for (const room of Object.values(rooms)) {{
            const found = room.devices.find(d => d.key === deviceKey);
            if (found) {{
                found.name = name;
                break;
            }}
        }}
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Saved.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function showAddRoomForm() {{
    const list = document.getElementById('rooms-list');
    if (list.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Add Room</h4>
        <label>Room ID: <input type="text" id="new-room-id" placeholder="r1314"></label>
        <label>Name: <input type="text" id="new-room-name" placeholder="R1314 · New Lab"></label>
        <label>Icon: <input type="text" id="new-room-icon" placeholder="🧪"></label>
        <div class="save-row">
            <button class="btn btn-primary" onclick="submitAddRoom()">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    list.appendChild(form);
}}

async function submitAddRoom() {{
    const roomId = document.getElementById('new-room-id').value.trim();
    const name = document.getElementById('new-room-name').value.trim();
    const icon = document.getElementById('new-room-icon').value.trim();
    if (!roomId || !name) {{
        alert('Room ID and name required.');
        return;
    }}
    await addRoom(roomId, name, icon);
}}

async function addRoom(roomId, name, icon) {{
    const status = document.getElementById('rooms-status');
    status.textContent = 'Adding...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        rooms[roomId] = {{
            name: name,
            icon: icon,
            devices: [],
            weatherhub_climate: []
        }};
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Added.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function deleteRoom(roomId) {{
    if (!confirm('Delete room ' + roomId + '? All devices in this room will be removed.')) return;
    const status = document.getElementById('rooms-status');
    status.textContent = 'Deleting...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        delete rooms[roomId];
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Deleted.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function editRoom(roomId) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const rooms = result.rooms.rooms;
    const room = rooms[roomId];
    const card = document.querySelector(`[data-room-id="${{roomId}}"]`);
    if (!card) return;
    if (card.querySelector('.inline-form')) return;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Room</h4>
        <label>Name: <input type="text" id="edit-room-name" value="${{room.name}}"></label>
        <label>Icon: <input type="text" id="edit-room-icon" value="${{room.icon || ''}}"></label>
        <div class="save-row">
            <button class="btn btn-primary"
                    onclick="submitEditRoom('${{roomId}}')">💾 Save</button>
            <button class="btn btn-secondary"
                    onclick="this.closest('.inline-form').remove()">✖ Cancel</button>
        </div>
    `;
    card.appendChild(form);
}}

async function submitEditRoom(roomId) {{
    const name = document.getElementById('edit-room-name').value.trim();
    const icon = document.getElementById('edit-room-icon').value.trim();
    if (!name) {{
        alert('Name required.');
        return;
    }}
    const status = document.getElementById('rooms-status');
    status.textContent = 'Saving...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const rooms = result.rooms.rooms;
        rooms[roomId].name = name;
        rooms[roomId].icon = icon;
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            status.textContent = 'Saved.';
            loadRooms();
        }} else {{
            const err = await putResp.json();
            status.textContent = 'Error: ' + (err.error?.message || putResp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function sendTestMail(btn) {{
    const status = document.getElementById('mail-status');
    status.textContent = 'Sending...';
    try {{
        const resp = await fetch('/api/admin/test-mail', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: '{{}}'
        }});
        const result = await resp.json();
        if (resp.ok) {{
            status.textContent = 'Sent to ' + result.count + ' notifier(s).';
        }} else {{
            status.textContent = 'Error: ' + (result.error?.message || resp.status);
        }}
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function loadAlerts() {{
    const status = document.getElementById('alerts-status');
    const list = document.getElementById('alerts-list');
    const onlyUnack = document.getElementById('alerts-only-unack').checked;
    status.textContent = 'Loading...';
    try {{
        const url = '/api/admin/alerts?limit=100&only_unacknowledged=' + (onlyUnack ? '1' : '0');
        const resp = await fetch(url);
        const result = await resp.json();
        if (!resp.ok) {{
            status.textContent = 'Error: ' + (result.error?.message || resp.status);
            return;
        }}
        list.innerHTML = '';
        for (const alert of result.alerts) {{
            const severityClass = alert.severity === 'critical'
                ? 'status-critical'
                : 'status-warn';
            const ackButton = alert.acknowledged
                ? '<span class="alert-ack">✓ Acknowledged</span>'
                : `<button class="btn btn-primary btn-small"
                        onclick="acknowledgeAlert(${{alert.id}})">✓ Acknowledge</button>`;
            const card = document.createElement('div');
            card.className = 'alert-card';
            card.innerHTML = `
                <div class="alert-header">
                    <span class="lamp ${{severityClass}}"></span>
                    <strong>${{alert.sensor}}</strong>
                    <span class="alert-severity">${{alert.severity}}</span>
                </div>
                <div class="alert-meta">
                    ${{alert.rule}} · ${{alert.created_at}}
                </div>
                <div class="alert-message">${{alert.message}}</div>
                <div class="alert-actions">
                    ${{ackButton}}
                </div>
            `;
            list.appendChild(card);
        }}
        status.textContent = result.alerts.length + ' alert(s).';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function acknowledgeAlert(id) {{
    try {{
        const resp = await fetch('/api/admin/alerts/' + id + '/acknowledge', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{acknowledged_by: 'admin'}})
        }});
        if (resp.ok) {{
            loadAlerts();
        }} else {{
            const result = await resp.json();
            const msg = result.error?.message || resp.status;
            document.getElementById('alerts-status').textContent = 'Error: ' + msg;
        }}
    }} catch (e) {{
        document.getElementById('alerts-status').textContent = 'Request failed: ' + e.message;
    }}
}}

loadRooms();

</script>
</body>
</html>
"""
