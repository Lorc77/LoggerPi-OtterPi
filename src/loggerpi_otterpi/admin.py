"""Admin-UI für den OtterPi."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from dashboard_constants import VERSION
from heartbeat import offline_status

BERLIN = ZoneInfo("Europe/Berlin")


def render_admin(
    config: dict,
    last_batch_at: str = "",
    last_received_at: str = "",
) -> str:
    from sensor_schemas import SENSOR_SCHEMAS

    if last_batch_at:
        last_update = (
            datetime.fromisoformat(last_batch_at).astimezone(BERLIN).strftime("%d.%m.%Y %H:%M Uhr")
        )
    else:
        last_update = "–"

    system_config = config.get("alarm_limits", {}).get("system", {})
    warning_seconds = system_config.get("loggerpi_offline_warning_seconds", 1800)
    critical_seconds = system_config.get("loggerpi_offline_critical_seconds", 3600)
    status_class, status_text = offline_status(last_received_at, warning_seconds, critical_seconds)
    rooms_json = json.dumps(config["rooms"], ensure_ascii=False, indent=2)
    alarm_json = json.dumps(config["alarm_limits"], ensure_ascii=False, indent=2)
    mail_json = json.dumps(config["mail"], ensure_ascii=False, indent=2)
    notifications_json = json.dumps(config["notifications"], ensure_ascii=False, indent=2)
    messages_json = json.dumps(config.get("messages", {}), ensure_ascii=False, indent=2)
    sensor_schemas_json = json.dumps(SENSOR_SCHEMAS, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🛠 ZOOLOGY-Observer Admin</title>
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
    min-height: 60px;
    font-family: ui-monospace, monospace;
    font-size: .85rem;
}}
textarea.json-editor {{
    min-height: 400px;
}}
.to-top {{
    text-align: center;
    margin: 8px 0;
}}
.rooms-list {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 16px;
}}
#notifications-list {{
    grid-template-columns: repeat(2, 1fr);
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
    min-width: 260px;
    max-width: 260px;
    white-space: nowrap;
    text-align: right;
    padding-right: 10px;
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
.config-item-checkbox {{
    justify-content: flex-start;
}}
.config-item-checkbox input[type="checkbox"] {{
    flex: 0 0 auto;
    margin-left: 0;
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
.enabled-yes {{
    color: #22c55e;
    font-weight: 600;
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
.alert-severity-critical {{
    background: rgba(239,68,68,.2);
    color: #fca5a5;
}}
.alert-severity-warn {{
    background: rgba(234,179,8,.2);
    color: #fde047;
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
.alert-resolved {{
    color: #22c55e;
    font-size: .85rem;
}}
.alert-active {{
    color: #ef4444;
    font-size: .85rem;
}}
.alert-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: .85rem;
    margin-top: 12px;
}}
.alert-table th {{
    text-align: left;
    padding: 8px 10px;
    color: #9ca3af;
    font-weight: normal;
    border-bottom: 1px solid rgba(255,255,255,.1);
}}
.alert-table td {{
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255,255,255,.05);
    vertical-align: middle;
}}
.alert-row:hover {{
    background: rgba(147,197,253,.05);
}}
.alert-status {{
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}}
.alert-severity-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: .7rem;
    font-weight: 600;
    text-transform: uppercase;
}}
.alert-severity-badge.critical {{
    background: rgba(239,68,68,.2);
    color: #fca5a5;
}}
.alert-severity-badge.warning {{
    background: rgba(234,179,8,.2);
    color: #fde047;
}}
.alert-actions {{
    display: flex;
    gap: 6px;
    white-space: nowrap;
}}
.alert-day-header {{
    padding: 12px 10px 6px 10px;
    color: #bfdbfe;
    font-size: .9rem;
    font-weight: 600;
    border-bottom: 1px solid rgba(147,197,253,.2);
}}
.alert-chart {{
    position: relative;
    height: 200px;
    margin-top: 12px;
    background: rgba(31,41,55,.5);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
    padding: 12px;
}}
.alert-summary {{
    display: flex;
    gap: 16px;
    margin-top: 12px;
    font-size: .9rem;
}}
.alert-summary-item {{
    cursor: pointer;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(255,255,255,.05);
    transition: .2s;
}}
.alert-summary-item:hover {{
    background: rgba(147,197,253,.15);
}}
.alert-summary-item.critical {{
    color: #fca5a5;
}}
.alert-summary-item.warning {{
    color: #fde047;
}}
.alert-summary-item.resolved {{
    color: #86efac;
}}
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
.status {{ color: #d1d5db; font-size: .9rem; }}
.toast-container {{
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.toast {{
    padding: 12px 20px;
    border-radius: 10px;
    font-size: .9rem;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,.3);
    animation: toast-in 0.3s ease-out;
    max-width: 400px;
}}
.toast-success {{
    background: rgba(34,197,94,.9);
    border: 1px solid rgba(34,197,94,.6);
}}
.toast-error {{
    background: rgba(239,68,68,.9);
    border: 1px solid rgba(239,68,68,.6);
}}
@keyframes toast-in {{
    from {{ opacity: 0; transform: translateX(20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
.chip {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 8px;
    font-size: .7rem;
    font-weight: 600;
    white-space: nowrap;
}}
.chip-ok {{ background: rgba(34,197,94,.2); color: #86efac; }}
.chip-off {{ background: rgba(107,114,128,.2); color: #d1d5db; }}
.chip-warn {{ background: rgba(234,179,8,.2); color: #fde047; }}
.chip-critical {{ background: rgba(239,68,68,.2); color: #fca5a5; }}
.chip-info {{ background: rgba(147,197,253,.15); color: #bfdbfe; }}

.device-card {{
    background: rgba(31,41,55,.5);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 12px;
}}
.device-card h3 {{
    margin: 0 0 4px 0;
    font-size: 1rem;
}}
.device-meta {{
    color: #9ca3af;
    font-size: .8rem;
    margin-bottom: 10px;
}}
.device-section {{
    margin-top: 10px;
}}
.device-section h4 {{
    margin: 0 0 6px 0;
    color: #bfdbfe;
    font-size: .9rem;
}}
.device-row {{
    display: grid;
    grid-template-columns: 120px 70px auto auto auto auto;
    gap: 6px;
    align-items: center;
    padding: 3px 0;
    font-size: .85rem;
}}
.device-row .name {{
    color: #d1d5db;
}}
.severity-checkboxes {{
    display: flex;
    gap: 16px;
    margin-top: 4px;
    margin-bottom: 8px;
}}
.severity-checkboxes label {{
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 0;
    cursor: pointer;
}}
.states-table {{
    width: auto;
}}
.states-table td:first-child {{
    padding-right: 24px;
}}
.checkbox-row {{
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 6px 0;
}}
.checkbox-row label {{
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 0;
    cursor: pointer;
}}
.device-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 12px;
}}
.device-grid .device-card {{
    margin-top: 0;
}}
@media (max-width: 900px) {{
    .device-grid {{
        grid-template-columns: 1fr;
    }}
}}
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {{
    -webkit-appearance: none;
    margin: 0;
}}
input[type="number"] {{
    -moz-appearance: textfield;
}}
.current-value {{
    color: #bfdbfe;
    font-size: .8rem;
    min-width: 70px;
}}
.device-row-states {{
    grid-template-columns: 120px 70px max-content;
}}
</style>
</head>
<body>
<div id="toast-container" class="toast-container"></div>
<div class="container">
<h1>🛠 ZOOLOGY-Observer Admin</h1>
<div class="subtitle">
    <span class="lamp {status_class}"></span> {status_text}
    · Last measurement: {last_update}
</div>
<div class="tabs">
    <button class="tab-btn active" onclick="showTab('alerts', this)">🚨 Alerts</button>
    <button class="tab-btn" onclick="showTab('rooms', this)">🏠 Rooms</button>
    <button class="tab-btn" onclick="showTab('alarm', this)">⚠️ Alarm Limits</button>
    <button class="tab-btn" onclick="showTab('mail', this)">📧 Mail</button>
    <button class="tab-btn" onclick="showTab('notifications', this)">🔔 Notifications</button>
    <button class="tab-btn" onclick="showTab('messages', this)">💬 Messages</button>
</div>

<div id="tab-rooms" class="tab-panel">
    <details class="howto">
        <summary>How-to: Add a new WeatherHub sensor</summary>
        <ol>
            <li>Put the sensor into operation (insert battery, pair).</li>
            <li>Read the sensor ID from the sender or from the batch
                (e.g. <code>015F9410F3EB</code>).</li>
            <li>Click "+ Add Device" in the room where the sensor is located and enter:
                <ul>
                    <li><strong>Name:</strong> a human-readable name (e.g. "Fridge-freezer").</li>
                    <li><strong>Key:</strong> <code>weatherhub_</code> + sensor ID in
                        <strong>lowercase</strong> (e.g. <code>weatherhub_015f9410f3eb</code>).</li>
                    <li><strong>Type:</strong> select from the dropdown, derived from the first
                        two digits of the sensor ID (e.g. ID <code>015F9410F3EB</code> →
                        <code>weatherhub_id01</code>).</li>
                </ul>
            </li>
            <li>The sensor appears in the dashboard.</li>
            <li>For the alert engine: <code>battery_low</code> is added automatically
                (for <code>weatherhub_*</code> types).</li>
        </ol>
    </details>
    <div id="rooms-list" class="rooms-list"></div>
    <div class="save-row">
        <button class="btn btn-primary"
                onclick="showAddRoomForm()">➕ Add Room</button>
        <button class="btn btn-secondary btn-small"
                onclick="toggleRoomsJson()">⚙️ Advanced (JSON)</button>
        <span id="rooms-status" class="status"></span>
    </div>
    <div id="rooms-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="rooms-text" class="json-editor">{rooms_json}</textarea>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    data-endpoint="/api/admin/rooms"
                    data-textarea="rooms-text"
                    data-status="rooms-status"
                    onclick="saveConfig(this)">💾 Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-alarm" class="tab-panel">
    <details class="howto">
        <summary>How-to: Configure alert limits</summary>
        <ol>
            <li>Click "Edit Limits" on a device to configure:
                <ul>
                    <li>Warning/critical limits (min/max) per measurement.</li>
                    <li>Rate-of-change limit (per hour) per measurement.</li>
                    <li>Stale/invalid alerts per device (under "States").</li>
                </ul>
            </li>
            <li>WeatherHub sensors are automatically added to the alert engine
                (battery_low state).</li>
            <li>Limits are checked after every batch and every 300 seconds.</li>
            <li>Alerts are deduplicated, respect quiet hours, and are sent via the
                configured notifiers.</li>
            <li>Use "Show all" to display all schema fields (including unsupported ones).</li>
            <li><strong>Acknowledged alerts are not re-sent until the state changes.</strong></li>
            <li><strong>Resolved alerts are marked as "Resolved" in the alert history.</strong></li>
        </ol>
    </details>
    <div id="alarm-list" class="rooms-list"></div>
    <div class="save-row">
        <label>
            <input type="checkbox" id="alarm-show-all" onchange="loadAlarmLimits()">
            Show all
        </label>
        <button class="btn btn-secondary btn-small"
                onclick="toggleAlarmJson()">⚙️ Advanced (JSON)</button>
        <span id="alarm-status" class="status"></span>
    </div>
    <div id="alarm-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="alarm-text" class="json-editor">{alarm_json}</textarea>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    data-endpoint="/api/admin/alarm-limits"
                    data-textarea="alarm-text"
                    data-status="alarm-status"
                    onclick="saveConfig(this)">💾 Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-mail" class="tab-panel">
    <details class="howto">
        <summary>How-to: Configure email notifications</summary>
        <ol>
            <li><strong>Recipients:</strong> all email addresses that receive alerts
                (comma-separated).</li>
            <li><strong>Routing:</strong> optional per-severity recipients.
                <code>critical</code> and <code>warning</code> can go to different
                addresses (must be a subset of recipients).</li>
            <li><strong>Quiet Hours:</strong> time range (e.g. 22:00–07:00) where
                no emails are sent. <code>Critical Always</code> overrides this for
                critical alerts.</li>
            <li><strong>Dedup Seconds:</strong> how long (in seconds) an identical
                alert is not re-sent. Default: 3600 (1 hour).</li>
            <li><strong>Send Test Mail:</strong> sends a test email to all configured
                notifiers.</li>
        </ol>
    </details>
    <div id="mail-form"></div>
    <div class="save-row">
        <button class="btn btn-primary"
                onclick="saveMailForm()">💾 Save</button>
        <button class="btn btn-secondary"
                onclick="sendTestMail(this)">📧 Send Test Mail</button>
        <button class="btn btn-secondary btn-small"
                onclick="toggleMailJson()">⚙️ Advanced (JSON)</button>
        <span id="mail-status" class="status"></span>
    </div>
    <div id="mail-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="mail-text" class="json-editor">{mail_json}</textarea>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    data-endpoint="/api/admin/mail"
                    data-textarea="mail-text"
                    data-status="mail-status"
                    onclick="saveConfig(this)">💾 Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-notifications" class="tab-panel">
    <details class="howto">
        <summary>How-to: Configure notification channels</summary>
        <ol>
            <li><strong>ntfy:</strong> push notification to a topic (e.g.
                <code>ZOOLOGY-Observer-alerts</code>). Install the ntfy app on your
                phone and subscribe to the topic. Optional: token for protected
                topics.</li>
            <li><strong>Webhook:</strong> HTTP POST to a URL. Formats:
                <ul>
                    <li><code>generic</code>: JSON with sensor, severity, message,
                        value, threshold.</li>
                    <li><code>discord</code>: Discord webhook format.</li>
                    <li><code>slack</code>: Slack webhook format.</li>
                </ul>
            </li>
            <li><strong>Severities:</strong> which severities are sent via this
                channel (critical and/or warning).</li>
            <li><strong>Enabled:</strong> toggle the channel on/off.</li>
        </ol>
    </details>
    <div id="notifications-list" class="rooms-list"></div>
    <div class="save-row">
        <button class="btn btn-primary"
                onclick="showAddChannelForm()">➕ Add Channel</button>
        <button class="btn btn-secondary btn-small"
                onclick="toggleNotificationsJson()">⚙️ Advanced (JSON)</button>
        <span id="notifications-status" class="status"></span>
    </div>
    <div id="notifications-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="notifications-text" class="json-editor">{notifications_json}</textarea>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    data-endpoint="/api/admin/notifications"
                    data-textarea="notifications-text"
                    data-status="notifications-status"
                    onclick="saveConfig(this)">💾 Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-messages" class="tab-panel">
    <details class="howto">
        <summary>How-to: Configure alert messages</summary>
        <ol>
            <li>Each field defines the <strong>rule text</strong> for a specific
                alert type (e.g. "too high", "too low", "invalid", "stale").</li>
            <li>The <strong>measurement name</strong> (e.g. "Temperature",
                "Humidity") is added automatically from the sensor schema.</li>
            <li>Example: <code>critical_max</code> = "too high" →
                "Temperature too high: 30.0 °C > 28.0 °C".</li>
            <li>Changes are applied immediately (no restart needed).</li>
        </ol>
    </details>
    <div id="messages-form"></div>
    <div class="save-row">
        <button class="btn btn-primary" onclick="saveMessages()">💾 Save</button>
        <button class="btn btn-secondary btn-small"
                onclick="toggleMessagesJson()">⚙️ Advanced (JSON)</button>
        <span id="messages-status" class="status"></span>
    </div>
    <div id="messages-json-editor" style="display: none; margin-top: 12px;">
        <textarea id="messages-text" class="json-editor">{messages_json}</textarea>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    data-endpoint="/api/admin/messages"
                    data-textarea="messages-text"
                    data-status="messages-status"
                    onclick="saveConfig(this)">💾 Save JSON</button>
        </div>
    </div>
</div>

<div id="tab-alerts" class="tab-panel active">
    <details class="howto">
        <summary>How-to: Read the alert history</summary>
        <ol>
            <li><strong>Lamp:</strong> green = resolved, red = active.</li>
            <li><strong>Status:</strong> "Active" (not resolved) or "Resolved"
                (state is back to normal).</li>
            <li><strong>Acknowledge:</strong> marks the alert as seen. It will not
                be re-sent until the state changes.</li>
            <li><strong>Resolve:</strong> manually marks the alert as resolved
                (e.g. if the sensor is gone).</li>
            <li><strong>Filters:</strong> "Only unacknowledged" and "Only active".</li>
        </ol>
    </details>
    <div class="save-row">
        <button class="btn btn-primary btn-small"
                onclick="loadAlerts()">🔄 Refresh</button>
        <label>
            <input type="checkbox" id="alerts-only-unack" onchange="loadAlerts()">
            Only unacknowledged
        </label>
        <label>
            <input type="checkbox" id="alerts-only-active" onchange="loadAlerts()">
            Only active
        </label>
        <span id="alerts-status" class="status"></span>
    </div>
    <div id="alerts-summary" class="alert-summary"></div>
    <div id="alerts-chart" class="alert-chart">
        <canvas id="alerts-chart-canvas"></canvas>
    </div>
    <div id="alerts-list"></div>
</div>
<div class="footer">🦦 otterpi · ZOOLOGY-Observer Admin {VERSION}</div>
</div>

<script>
const SENSOR_SCHEMAS = {sensor_schemas_json};

function showToast(message, type) {{
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + (type || 'success');
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {{
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }}, 3000);
}}

function setStatus(statusId, message, type) {{
    const status = document.getElementById(statusId);
    if (status) status.textContent = message;
    showToast(message, type);
}}

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
    if (name === 'messages') {{
        loadMessages();
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
            setStatus(statusId, 'Saved.', 'success');
        }} else {{
            setStatus(statusId, 'Error: ' + (result.error?.message || resp.status), 'error');
        }}
    }} catch (e) {{
        setStatus(statusId, 'Request failed: ' + e.message, 'error');
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
                    <button class="btn btn-primary btn-small"
                            onclick="showAddDeviceForm('${{roomId}}')">➕ Add Device</button>
                    <button class="btn btn-secondary btn-small"
                            onclick="editRoom('${{roomId}}')">✏️ Edit Room</button>
                    <button class="btn btn-danger btn-small"
                            onclick="deleteRoom('${{roomId}}')">🗑 Delete Room</button>
                </div>
            `;
            list.appendChild(card);
            const toTop = document.createElement('div');
            toTop.className = 'to-top';
            toTop.innerHTML = `<button class="btn btn-primary btn-small"
                onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">↑ To Top</button>`;
            list.appendChild(toTop);
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

function buildDeviceContent(
    device, sensors, states, latestMeasurements, latestStates, showAll, deviceConfig
) {{
    const UNIT_LABELS = {{
        celsius: '°C',
        percent: '%',
        mbar: 'mbar',
        ppm: 'ppm',
        rpm: 'rpm',
    }};
    const schema = SENSOR_SCHEMAS[device.type] || {{measurements: [], states: []}};
    let measurementsHtml = '';
    for (const [name, unit] of schema.measurements) {{
        const unitLabel = UNIT_LABELS[unit] || unit;
        const key = device.key + '.' + name;
        const limits = sensors[key] || {{}};
        const current = latestMeasurements[key];
        const isActive = current !== undefined || limits.enabled === true;
        if (!showAll && !isActive) continue;
        const currentValue = current && current.value !== null
            ? `${{current.value.toFixed(1)}} ${{unitLabel}}`
            : '–';
        const enabled = limits.enabled === true;
        const enabledChip = enabled
            ? '<span class="chip chip-ok">Enabled</span>'
            : '<span class="chip chip-off">Disabled</span>';
        const warnMin = limits.warning_min;
        const warnMax = limits.warning_max;
        const critMin = limits.critical_min;
        const critMax = limits.critical_max;
        const rate = limits.rate_of_change_max_per_hour;
        let warnText = '';
        if (warnMin !== undefined) warnText += `↓ ${{warnMin}} ${{unitLabel}}`;
        if (warnMax !== undefined) warnText += ` ↑ ${{warnMax}} ${{unitLabel}}`;
        const warnChip = (warnMin !== undefined || warnMax !== undefined)
            ? `<span class="chip chip-warn">${{warnText.trim()}}</span>`
            : '<span class="chip chip-off">Warn n/c</span>';
        let critText = '';
        if (critMin !== undefined) critText += `↓ ${{critMin}} ${{unitLabel}}`;
        if (critMax !== undefined) critText += ` ↑ ${{critMax}} ${{unitLabel}}`;
        const critChip = (critMin !== undefined || critMax !== undefined)
            ? `<span class="chip chip-critical">${{critText.trim()}}</span>`
            : '<span class="chip chip-off">Crit n/c</span>';
        const rateChip = rate !== undefined
            ? `<span class="chip chip-info">↕ ${{rate}} ${{unitLabel}}/h</span>`
            : '<span class="chip chip-off">Rate n/c</span>';
        measurementsHtml += `
            <div class="device-row">
                <span class="name">${{name}}</span>
                <span class="current-value">${{currentValue}}</span>
                ${{enabledChip}}
                ${{warnChip}}
                ${{critChip}}
                ${{rateChip}}
            </div>
        `;
    }}
    let statesHtml = '';
    for (const [name, type] of schema.states) {{
        const key = device.key + '.' + name;
        const rule = states[key] || {{}};
        const deviceStates = latestStates[device.key] || {{}};
        const current = deviceStates[name];
        const isActive = current !== undefined || rule.enabled === true;
        if (!showAll && !isActive) continue;
        const currentValue = current !== undefined ? String(current) : '–';
        const enabled = rule.enabled === true;
        const enabledChip = enabled
            ? '<span class="chip chip-ok">Enabled</span>'
            : '<span class="chip chip-off">Disabled</span>';
        statesHtml += `
            <div class="device-row device-row-states">
                <span class="name">${{name}}</span>
                <span class="current-value">${{currentValue}}</span>
                ${{enabledChip}}
            </div>
        `;
    }}
    const deviceRule = deviceConfig[device.key] || {{}};
    const staleEnabled = deviceRule.stale_enabled !== false;
    const invalidEnabled = deviceRule.invalid_enabled !== false;
    const staleChip = staleEnabled
        ? '<span class="chip chip-ok">Enabled</span>'
        : '<span class="chip chip-off">Disabled</span>';
    const invalidChip = invalidEnabled
        ? '<span class="chip chip-ok">Enabled</span>'
        : '<span class="chip chip-off">Disabled</span>';
    statesHtml += `
        <div class="device-row device-row-states">
            <span class="name">Stale alerts</span>
            <span class="current-value">–</span>
            ${{staleChip}}
        </div>
        <div class="device-row device-row-states">
            <span class="name">Invalid alerts</span>
            <span class="current-value">–</span>
            ${{invalidChip}}
        </div>
    `;
    const statesSection = statesHtml
        ? `<div class="device-section"><h4>States</h4>${{statesHtml}}</div>`
        : '<div class="device-section"><h4>States</h4><p class="hint">not applicable</p></div>';
    return `
        <div class="device-section">
            <h4>Measurements</h4>
            ${{measurementsHtml}}
        </div>
        ${{statesSection}}
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="showEditLimitsForm('${{device.key}}', '${{device.type}}')">
                ✏️ Edit Limits
            </button>
        </div>
    `;
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
        const deviceConfig = alarmLimits.device || {{}};
        const latestResp = await fetch('/api/admin/latest-measurements');
        const latestData = await latestResp.json();
        const latestMeasurements = latestData.measurements || {{}};
        const latestStates = latestData.states || {{}};
        const showAll = document.getElementById('alarm-show-all').checked;
        list.innerHTML = '';

        // System-Karte (LoggerPi-Offline-Erkennung)
        const system = alarmLimits.system || {{}};
        const warningSeconds = system.loggerpi_offline_warning_seconds ?? 1800;
        const criticalSeconds = system.loggerpi_offline_critical_seconds ?? 3600;
        const warningAlertEnabled = system.loggerpi_offline_warning_alert_enabled ?? false;
        const systemCard = document.createElement('div');
        systemCard.className = 'room-card';
        systemCard.innerHTML = `
            <h3>⚙️ System</h3>
            <p>LoggerPi offline detection</p>
            <div class="config-grid">
                <div class="config-item">
                    <label>Warning threshold (minutes):</label>
                    <input type="number" id="system-warning-minutes"
                            value="${{Math.round(warningSeconds / 60)}}" min="1">
                </div>
                <div class="config-item">
                    <label>Critical threshold (minutes):</label>
                    <input type="number" id="system-critical-minutes"
                            value="${{Math.round(criticalSeconds / 60)}}" min="1">
                </div>
                <div class="config-item config-item-checkbox">
                    <label>Send warning alert at warning threshold:</label>
                    <input type="checkbox" id="system-warning-alert"
                            ${{warningAlertEnabled ? 'checked' : ''}}>
                </div>
            </div>
            <div class="save-row">
                <button class="btn btn-primary btn-small"
                        onclick="saveSystemConfig()">💾 Save System</button>
            </div>
        `;
        list.appendChild(systemCard);

        // Raum-Kacheln mit Geräte-Kacheln
        for (const [roomId, room] of Object.entries(rooms)) {{
            const roomCard = document.createElement('div');
            roomCard.className = 'room-card';
            roomCard.dataset.roomId = roomId;

            let devicesHtml = '';
            for (const device of room.devices) {{
                const meta = `Room: ${{roomId}} · Key: ${{device.key}} · Type: ${{device.type}}`;
                const content = buildDeviceContent(
                    device, sensors, states, latestMeasurements, latestStates,
                    showAll, deviceConfig
                );
                devicesHtml += `
                    <div class="device-card" data-device-key="${{device.key}}">
                        <h3>${{device.name}}</h3>
                        <div class="device-meta">${{meta}}</div>
                        ${{content}}
                    </div>
                `;
            }}

            roomCard.innerHTML = `
                <h3>${{room.icon || ''}} ${{room.name}}</h3>
                <div class="device-grid">${{devicesHtml}}</div>
            `;
            list.appendChild(roomCard);

            const toTop = document.createElement('div');
            toTop.className = 'to-top';
            toTop.innerHTML = `<button class="btn btn-primary btn-small"
                onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">↑ To Top</button>`;
            list.appendChild(toTop);
        }}
        status.textContent = 'Loaded.';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function saveSystemConfig() {{
    const status = document.getElementById('alarm-status');
    status.textContent = 'Saving system config...';
    try {{
        const resp = await fetch('/api/admin/config');
        const result = await resp.json();
        const alarmLimits = result.alarm_limits;
        if (!alarmLimits.system) alarmLimits.system = {{}};
        const warningMinutes = parseInt(
            document.getElementById('system-warning-minutes').value
        );
        const criticalMinutes = parseInt(
            document.getElementById('system-critical-minutes').value
        );
        const warningAlert = document.getElementById('system-warning-alert').checked;
        alarmLimits.system.loggerpi_offline_warning_seconds = warningMinutes * 60;
        alarmLimits.system.loggerpi_offline_critical_seconds = criticalMinutes * 60;
        alarmLimits.system.loggerpi_offline_warning_alert_enabled = warningAlert;
        const putResp = await fetch('/api/admin/alarm-limits', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(alarmLimits)
        }});
        if (putResp.ok) {{
            setStatus('alarm-status', 'System config saved.', 'success');
            loadAlarmLimits();
        }} else {{
            const err = await putResp.json();
            setStatus('alarm-status', 'Error: ' + (err.error?.message || putResp.status), 'error');
        }}
    }} catch (e) {{
        setStatus('alarm-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function showEditLimitsForm(deviceKey, deviceType) {{
    const card = document.querySelector(`[data-device-key="${{deviceKey}}"]`);
    if (!card) return;
    const existingForm = card.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
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
        const enabled = limits.enabled === true ? 'checked' : '';
        measurementsHtml += `
            <tr>
                <td>${{name}}</td>
                <td><input type="checkbox" id="meas-enabled-${{name}}" ${{enabled}}></td>
                <td><input type="number" step="0.1" id="warn-min-${{name}}"
                        value="${{limits.warning_min ?? ''}}"></td>
                <td><input type="number" step="0.1" id="warn-max-${{name}}"
                        value="${{limits.warning_max ?? ''}}"></td>
                <td><input type="number" step="0.1" id="crit-min-${{name}}"
                        value="${{limits.critical_min ?? ''}}"></td>
                <td><input type="number" step="0.1" id="crit-max-${{name}}"
                        value="${{limits.critical_max ?? ''}}"></td>
                <td><input type="number" step="0.1" id="rate-${{name}}"
                        value="${{limits.rate_of_change_max_per_hour ?? ''}}"></td>
            </tr>
        `;
    }}
    let statesHtml = '';
    for (const [name, type] of schema.states) {{
        const key = deviceKey + '.' + name;
        const rule = states[key] || {{}};
        const checked = rule.enabled === true ? 'checked' : '';
        statesHtml += `
            <tr>
                <td>${{name}}</td>
                <td><input type="checkbox" id="state-enabled-${{name}}" ${{checked}}></td>
            </tr>
        `;
    }}
    const deviceRule = (alarmLimits.device || {{}})[deviceKey] || {{}};
    const staleChecked = deviceRule.stale_enabled !== false ? 'checked' : '';
    const invalidChecked = deviceRule.invalid_enabled !== false ? 'checked' : '';
    statesHtml += `
        <tr>
            <td>Stale alerts</td>
            <td><input type="checkbox" id="device-stale-enabled" ${{staleChecked}}></td>
        </tr>
        <tr>
            <td>Invalid alerts</td>
            <td><input type="checkbox" id="device-invalid-enabled" ${{invalidChecked}}></td>
        </tr>
    `;
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Limits: ${{deviceKey}}</h4>
        <h5>Measurements</h5>
        <table class="devices-table">
            <thead>
                <tr>
                    <th>Measurement</th>
                    <th>Enabled</th>
                    <th>Warn Min</th>
                    <th>Warn Max</th>
                    <th>Crit Min</th>
                    <th>Crit Max</th>
                    <th>Rate/h</th>
                </tr>
            </thead>
            <tbody>${{measurementsHtml}}</tbody>
        </table>
        <h5>States</h5>
        <table class="devices-table states-table">
            <thead>
                <tr><th>State</th><th>Enabled</th></tr>
            </thead>
            <tbody>${{statesHtml}}</tbody>
        </table>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitEditLimits('${{deviceKey}}', '${{deviceType}}')">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
            const rate = document.getElementById('rate-' + name).value;
            const enabled = document.getElementById('meas-enabled-' + name).checked;
            const limits = {{}};
            if (warnMin) limits.warning_min = parseFloat(warnMin);
            if (warnMax) limits.warning_max = parseFloat(warnMax);
            if (critMin) limits.critical_min = parseFloat(critMin);
            if (critMax) limits.critical_max = parseFloat(critMax);
            if (rate) limits.rate_of_change_max_per_hour = parseFloat(rate);
            if (enabled || Object.keys(limits).length > 0) {{
                limits.enabled = enabled;
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
        if (!alarmLimits.device) alarmLimits.device = {{}};
        const staleEnabled = document.getElementById('device-stale-enabled').checked;
        const invalidEnabled = document.getElementById('device-invalid-enabled').checked;
        alarmLimits.device[deviceKey] = {{
            stale_enabled: staleEnabled,
            invalid_enabled: invalidEnabled,
        }};
        const putResp = await fetch('/api/admin/alarm-limits', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(alarmLimits)
        }});
        if (putResp.ok) {{
            setStatus('alarm-status', 'Saved.', 'success');
            loadAlarmLimits();
        }} else {{
            const err = await putResp.json();
            setStatus('alarm-status', 'Error: ' + (err.error?.message || putResp.status), 'error');
        }}
    }} catch (e) {{
        setStatus('alarm-status', 'Request failed: ' + e.message, 'error');
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
                    <div class="config-item">
                        <label>From Name:</label>
                        <input type="text" id="mail-from-name"
                                value="${{mail.from_name || ''}}">
                    </div>
                </div>
            </div>
            <div class="config-group">
                <h4>Recipients</h4>
                <div class="config-grid">
                    <div class="config-item config-item-full">
                        <label>Recipients (comma-separated):</label>
                        <textarea id="mail-recipients" rows="2">${{
                            (mail.recipients || []).join(', ')
                        }}</textarea>
                    </div>
                    <div class="config-item config-item-full">
                        <label>Routing Critical (comma-separated):</label>
                        <textarea id="mail-routing-critical" rows="2">${{
                            (mail.routing?.critical || []).join(', ')
                        }}</textarea>
                    </div>
                    <div class="config-item config-item-full">
                        <label>Routing Warning (comma-separated):</label>
                        <textarea id="mail-routing-warning" rows="2">${{
                            (mail.routing?.warning || []).join(', ')
                        }}</textarea>
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
                    <div class="config-item config-item-checkbox">
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
                    <div class="config-item config-item-checkbox">
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
        mail.from_name = document.getElementById('mail-from-name').value.trim();
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
            setStatus('mail-status', 'Saved.', 'success');
        }} else {{
            const err = await putResp.json();
            setStatus('mail-status', 'Error: ' + (err.error?.message || putResp.status), 'error');
        }}
    }} catch (e) {{
        setStatus('mail-status', 'Request failed: ' + e.message, 'error');
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
                <p>${{channel.enabled
                    ? '<span class="enabled-yes">Enabled: ✓</span>'
                    : 'Enabled: –'}}</p>
                <p>URL: ${{channel.url || '–'}}</p>
                ${{channel.type === 'ntfy' ? `<p>Topic: ${{channel.topic || '–'}}</p>` : ''}}
                ${{
                    channel.type === 'webhook'
                        ? `<p>Format: ${{channel.format || 'generic'}}</p>`
                        : ''
                }}
                <div class="save-row">
                    <button class="btn btn-secondary btn-small"
                            onclick="editChannel(${{i}})">✏️ Edit</button>
                    <button class="btn btn-danger btn-small"
                            onclick="deleteChannel(${{i}})">🗑 Delete</button>
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

async function loadMessages() {{
    const status = document.getElementById('messages-status');
    const form = document.getElementById('messages-form');
    status.textContent = 'Loading...';
    try {{
        const resp = await fetch('/api/admin/messages');
        const messages = await resp.json();
        const groups = {{
            'Measurements': [
                ['critical_max', 'Critical Max'],
                ['critical_min', 'Critical Min'],
                ['warning_max', 'Warning Max'],
                ['warning_min', 'Warning Min'],
                ['rate_of_change', 'Rate of Change'],
                ['invalid', 'Invalid'],
                ['stale', 'Stale'],
            ],
            'States': [
                ['battery_low', 'Battery Low'],
                ['door_open', 'Door Open'],
                ['contact_open', 'Contact Open'],
                ['alarm', 'Alarm'],
            ],
            'System': [
                ['loggerpi_offline', 'LoggerPi Offline'],
            ],
        }};
        let html = '';
        for (const [groupName, fields] of Object.entries(groups)) {{
            html += `<div class="config-group"><h4>${{groupName}}</h4><div class="config-grid">`;
            for (const [key, label] of fields) {{
                const value = messages[key] || '';
                html += `
                    <div class="config-item">
                        <label>${{label}}:</label>
                        <input type="text" id="msg-${{key}}" value="${{value}}">
                    </div>
                `;
            }}
            html += `</div></div>`;
        }}
        form.innerHTML = html;
        status.textContent = 'Loaded.';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

async function saveMessages() {{
    const status = document.getElementById('messages-status');
    status.textContent = 'Saving...';
    try {{
        const keys = [
            'critical_max', 'critical_min', 'warning_max', 'warning_min',
            'rate_of_change', 'invalid', 'stale',
            'battery_low', 'door_open', 'contact_open', 'alarm',
            'loggerpi_offline',
        ];
        const messages = {{}};
        for (const key of keys) {{
            messages[key] = document.getElementById('msg-' + key).value;
        }}
        const putResp = await fetch('/api/admin/messages', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(messages)
        }});
        if (putResp.ok) {{
            setStatus('messages-status', 'Saved.', 'success');
        }} else {{
            const err = await putResp.json();
            setStatus(
                'messages-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('messages-status', 'Request failed: ' + e.message, 'error');
    }}
}}

function toggleMessagesJson() {{
    const editor = document.getElementById('messages-json-editor');
    editor.style.display = editor.style.display === 'none' ? 'block' : 'none';
}}

function showAddChannelForm() {{
    const list = document.getElementById('notifications-list');
    const existingForm = list.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
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
        <div class="checkbox-row">
            <label><input type="checkbox" id="new-channel-enabled" checked> Enabled</label>
        </div>
        <label>Severities:</label>
        <div class="severity-checkboxes">
            <label><input type="checkbox" id="new-channel-critical" checked> critical</label>
            <label><input type="checkbox" id="new-channel-warning" checked> warning</label>
        </div>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitAddChannel()">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
    const severities = [];
    if (document.getElementById('new-channel-critical').checked) severities.push('critical');
    if (document.getElementById('new-channel-warning').checked) severities.push('warning');
    channel.severities = severities;
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
            setStatus('notifications-status', 'Added.', 'success');
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'notifications-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('notifications-status', 'Request failed: ' + e.message, 'error');
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
            setStatus('notifications-status', 'Deleted.', 'success');
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'notifications-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('notifications-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function editChannel(index) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const notifications = result.notifications;
    const channel = notifications.channels[index];
    const severities = channel.severities || ['critical', 'warning'];
    const criticalChecked = severities.includes('critical') ? 'checked' : '';
    const warningChecked = severities.includes('warning') ? 'checked' : '';
    const list = document.getElementById('notifications-list');
    const existingForm = list.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
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
        <div class="checkbox-row">
            <label><input type="checkbox" id="edit-channel-enabled"
                    ${{channel.enabled ? 'checked' : ''}}> Enabled</label>
        </div>
        <label>Severities:</label>
        <div class="severity-checkboxes">
            <label><input type="checkbox" id="edit-channel-critical"
                    ${{criticalChecked}}> critical</label>
            <label><input type="checkbox" id="edit-channel-warning"
                    ${{warningChecked}}> warning</label>
        </div>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitEditChannel(${{index}})">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
    const severities = [];
    if (document.getElementById('edit-channel-critical').checked) severities.push('critical');
    if (document.getElementById('edit-channel-warning').checked) severities.push('warning');
    channel.severities = severities;
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
            setStatus('notifications-status', 'Saved.', 'success');
            loadNotifications();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'notifications-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('notifications-status', 'Request failed: ' + e.message, 'error');
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
            setStatus('rooms-status', 'Moved.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
    }}
}}

function showAddDeviceForm(roomId) {{
    const card = document.querySelector(`[data-room-id="${{roomId}}"]`);
    if (!card) return;
    const existingForm = card.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
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
            <button class="btn btn-primary btn-small"
                    onclick="submitAddDevice('${{roomId}}')">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
            setStatus('rooms-status', 'Added.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function deleteDevice(deviceKey) {{
    if (!confirm('Delete device ' + deviceKey + '?')) return;
    if (!confirm('Are you sure? This cannot be undone.')) return;
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
            const alarmResp = await fetch('/api/admin/config');
            const alarmResult = await alarmResp.json();
            const alarmLimits = alarmResult.alarm_limits;
            if (alarmLimits.sensors) {{
                for (const key of Object.keys(alarmLimits.sensors)) {{
                    if (key.startsWith(deviceKey + '.')) {{
                        delete alarmLimits.sensors[key];
                    }}
                }}
            }}
            if (alarmLimits.states) {{
                for (const key of Object.keys(alarmLimits.states)) {{
                    if (key.startsWith(deviceKey + '.')) {{
                        delete alarmLimits.states[key];
                    }}
                }}
            }}
            if (alarmLimits.device) {{
                delete alarmLimits.device[deviceKey];
            }}
            await fetch('/api/admin/alarm-limits', {{
                method: 'PUT',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(alarmLimits)
            }});
            setStatus('rooms-status', 'Deleted.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
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
    const existingForm = card.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Device</h4>
        <label>Name: <input type="text" id="edit-device-name" value="${{device.name}}"></label>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitEditDevice('${{deviceKey}}')">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
            setStatus('rooms-status', 'Saved.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
    }}
}}

function showAddRoomForm() {{
    const list = document.getElementById('rooms-list');
    const existingForm = list.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Add Room</h4>
        <label>Room ID: <input type="text" id="new-room-id" placeholder="r1314"></label>
        <label>Name: <input type="text" id="new-room-name" placeholder="R1314 · New Lab"></label>
        <label>Icon: <input type="text" id="new-room-icon" placeholder="🧪"></label>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitAddRoom()">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
            setStatus('rooms-status', 'Added.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function deleteRoom(roomId) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const rooms = result.rooms.rooms;
    const room = rooms[roomId];
    if (room && room.devices.length > 0) {{
        alert('Cannot delete room with devices. Move or delete devices first.');
        return;
    }}
    if (!confirm('Delete room ' + roomId + '?')) return;
    if (!confirm('Are you sure? This cannot be undone.')) return;
    const status = document.getElementById('rooms-status');
    status.textContent = 'Deleting...';
    try {{
        delete rooms[roomId];
        const putResp = await fetch('/api/admin/rooms', {{
            method: 'PUT',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{rooms: rooms}})
        }});
        if (putResp.ok) {{
            setStatus('rooms-status', 'Deleted.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function editRoom(roomId) {{
    const resp = await fetch('/api/admin/config');
    const result = await resp.json();
    const rooms = result.rooms.rooms;
    const room = rooms[roomId];
    const card = document.querySelector(`[data-room-id="${{roomId}}"]`);
    if (!card) return;
    const existingForm = card.querySelector('.inline-form');
    if (existingForm) {{
        existingForm.remove();
        return;
    }}
    const form = document.createElement('div');
    form.className = 'inline-form';
    form.innerHTML = `
        <h4>Edit Room</h4>
        <label>Name: <input type="text" id="edit-room-name" value="${{room.name}}"></label>
        <label>Icon: <input type="text" id="edit-room-icon" value="${{room.icon || ''}}"></label>
        <div class="save-row">
            <button class="btn btn-primary btn-small"
                    onclick="submitEditRoom('${{roomId}}')">💾 Save</button>
            <button class="btn btn-secondary btn-small"
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
            setStatus('rooms-status', 'Saved.', 'success');
            loadRooms();
        }} else {{
            const err = await putResp.json();
            setStatus(
                'rooms-status',
                'Error: ' + (err.error?.message || putResp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('rooms-status', 'Request failed: ' + e.message, 'error');
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
            setStatus(
                'mail-status',
                'Sent to ' + result.count + ' notifier(s).',
                'success'
            );
        }} else {{
            setStatus(
                'mail-status',
                'Error: ' + (result.error?.message || resp.status),
                'error'
            );
        }}
    }} catch (e) {{
        setStatus('mail-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function loadAlerts() {{
    const status = document.getElementById('alerts-status');
    const list = document.getElementById('alerts-list');
    const summary = document.getElementById('alerts-summary');
    const onlyUnack = document.getElementById('alerts-only-unack').checked;
    const onlyActive = document.getElementById('alerts-only-active').checked;
    status.textContent = 'Loading...';
    try {{
        const configResp = await fetch('/api/admin/config');
        const config = await configResp.json();
        const rooms = config.rooms.rooms;
        const deviceMap = {{}};
        for (const [roomId, room] of Object.entries(rooms)) {{
            for (const device of room.devices) {{
                deviceMap[device.key] = {{
                    roomName: room.name,
                    roomIcon: room.icon || '',
                    deviceName: device.name,
                }};
            }}
        }}
        const url = '/api/admin/alerts?limit=100&only_unacknowledged='
            + (onlyUnack ? '1' : '0')
            + '&only_active=' + (onlyActive ? '1' : '0');
        const resp = await fetch(url);
        const result = await resp.json();
        if (!resp.ok) {{
            status.textContent = 'Error: ' + (result.error?.message || resp.status);
            return;
        }}
        const statsResp = await fetch('/api/admin/alerts/stats');
        const stats = await statsResp.json();
        renderAlertSummary(summary, stats.by_status);
        renderAlertChart(stats.by_day);
        renderAlertTable(list, result.alerts, deviceMap);
        status.textContent = result.alerts.length + ' alert(s).';
    }} catch (e) {{
        status.textContent = 'Request failed: ' + e.message;
    }}
}}

function renderAlertSummary(container, byStatus) {{
    container.innerHTML = `
        <span class="alert-summary-item critical">
            ${{byStatus.active_critical}} active critical
        </span>
        <span class="alert-summary-item warning">
            ${{byStatus.active_warning}} active warning
        </span>
        <span class="alert-summary-item resolved">
            ${{byStatus.resolved}} resolved
        </span>
    `;
}}

let alertsChart = null;
function renderAlertChart(byDay) {{
    const canvas = document.getElementById('alerts-chart-canvas');
    if (!canvas) return;
    if (alertsChart) {{
        alertsChart.destroy();
    }}
    const labels = byDay.map(d => d.date);
    const warningData = byDay.map(d => d.warning);
    const criticalData = byDay.map(d => d.critical);
    const resolvedData = byDay.map(d => d.resolved);
    alertsChart = new Chart(canvas, {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [
                {{
                    label: 'Warning',
                    data: warningData,
                    backgroundColor: '#eab308',
                    stack: 'alerts',
                }},
                {{
                    label: 'Critical',
                    data: criticalData,
                    backgroundColor: '#ef4444',
                    stack: 'alerts',
                }},
                {{
                    label: 'Resolved',
                    data: resolvedData,
                    backgroundColor: '#22c55e',
                    stack: 'alerts',
                }},
            ],
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    labels: {{ color: '#d1d5db' }},
                }},
            }},
            scales: {{
                x: {{ stacked: true, ticks: {{ color: '#9ca3af' }} }},
                y: {{ stacked: true, ticks: {{ color: '#9ca3af' }} }},
            }},
        }},
    }});
}}

function renderAlertTable(container, alerts, deviceMap) {{
    if (alerts.length === 0) {{
        container.innerHTML = '<p class="hint">No alerts.</p>';
        return;
    }}
    const groups = {{}};
    for (const alert of alerts) {{
        const date = new Date(alert.created_at).toLocaleDateString('de-DE');
        if (!groups[date]) {{
            groups[date] = [];
        }}
        groups[date].push(alert);
    }}
    let html = '<table class="alert-table"><thead><tr>'
        + '<th>Status</th><th>Zeit</th><th>Severity</th>'
        + '<th>Regel</th><th>Gerät</th><th>Aktionen</th>'
        + '</tr></thead><tbody>';
    for (const [date, dayAlerts] of Object.entries(groups)) {{
        html += `<tr><td colspan="6" class="alert-day-header">${{date}}</td></tr>`;
        for (const alert of dayAlerts) {{
            html += renderAlertRow(alert, deviceMap);
        }}
    }}
    html += '</tbody></table>';
    container.innerHTML = html;
}}

function renderAlertRow(alert, deviceMap) {{
    const parts = alert.sensor.split('.');
    const deviceKey = parts[0];
    const measurement = parts.slice(1).join('.');
    const info = deviceMap[deviceKey] || {{}};
    const deviceLabel = info.deviceName
        ? `${{info.roomIcon}} ${{info.roomName}} / ${{info.deviceName}}`
        : alert.sensor;
    const timeLabel = new Date(alert.created_at).toLocaleTimeString('de-DE', {{
        hour: '2-digit',
        minute: '2-digit',
    }});
    const statusLabel = alert.resolved_at
        ? '<span class="alert-resolved">🟢 Resolved</span>'
        : '<span class="alert-active">🔴 Active</span>';
    const severityClass = alert.severity === 'critical' ? 'critical' : 'warning';
    const ruleLabel = measurement
        ? `${{measurement}}: ${{alert.rule}}`
        : alert.rule;
    const ackButton = alert.acknowledged
        ? '<span class="alert-ack">✓ Acknowledged</span>'
        : `<button class="btn btn-primary btn-small"
                onclick="acknowledgeAlert(${{alert.id}})">✓ Acknowledge</button>`;
    const resolvedAt = alert.resolved_at
        ? new Date(alert.resolved_at).toLocaleTimeString('de-DE', {{
            hour: '2-digit',
            minute: '2-digit',
        }})
        : '';
    const resolveButton = alert.resolved_at
        ? `<span class="alert-resolved">✓ Resolved (${{resolvedAt}})</span>`
        : `<button class="btn btn-secondary btn-small"
                onclick="resolveAlert(${{alert.id}})">✓ Resolve</button>`;
    return `
        <tr class="alert-row" title="${{alert.message}}">
            <td class="alert-status">${{statusLabel}}</td>
            <td>${{timeLabel}}</td>
            <td>
                <span class="alert-severity-badge ${{severityClass}}">
                    ${{alert.severity}}
                </span>
            </td>
            <td>${{ruleLabel}}</td>
            <td>${{deviceLabel}}</td>
            <td class="alert-actions">${{ackButton}} ${{resolveButton}}</td>
        </tr>
    `;
}}

async function acknowledgeAlert(id) {{
    try {{
        const resp = await fetch('/api/admin/alerts/' + id + '/acknowledge', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{acknowledged_by: 'admin'}})
        }});
        if (resp.ok) {{
            setStatus('alerts-status', 'Acknowledged.', 'success');
            loadAlerts();
        }} else {{
            const result = await resp.json();
            const msg = result.error?.message || resp.status;
            setStatus('alerts-status', 'Error: ' + msg, 'error');
        }}
    }} catch (e) {{
        setStatus('alerts-status', 'Request failed: ' + e.message, 'error');
    }}
}}

async function resolveAlert(id) {{
    try {{
        const resp = await fetch('/api/admin/alerts/' + id + '/resolve', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: '{{}}'
        }});
        if (resp.ok) {{
            setStatus('alerts-status', 'Resolved.', 'success');
            loadAlerts();
        }} else {{
            const result = await resp.json();
            const msg = result.error?.message || resp.status;
            setStatus('alerts-status', 'Error: ' + msg, 'error');
        }}
    }} catch (e) {{
        setStatus('alerts-status', 'Request failed: ' + e.message, 'error');
    }}
}}

loadAlerts();

</script>
</body>
</html>
"""
