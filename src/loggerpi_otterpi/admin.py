"""Admin-UI für den OtterPi."""

import json


def render_admin(config: dict) -> str:
    rooms_json = json.dumps(config["rooms"], ensure_ascii=False, indent=2)
    alarm_json = json.dumps(config["alarm_limits"], ensure_ascii=False, indent=2)
    mail_json = json.dumps(config["mail"], ensure_ascii=False, indent=2)
    notifications_json = json.dumps(config["notifications"], ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OtterPi Admin</title>
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
    width: min(1100px, 95%);
    margin: auto;
    background: rgba(20,35,50,.58);
    backdrop-filter: blur(6px);
    border-radius: 25px;
    padding: 30px;
    box-shadow: 0 20px 50px rgba(0,0,0,.4);
}}
h1 {{ margin-top: 0; }}
.tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
.tab-btn {{
    padding: 8px 16px;
    border-radius: 20px;
    background: rgba(147,197,253,.15);
    border: 1px solid rgba(147,197,253,.4);
    color: #bfdbfe;
    cursor: pointer;
    font-size: .9rem;
}}
.tab-btn.active {{ background: rgba(147,197,253,.5); color: white; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}
textarea {{
    width: 100%;
    min-height: 400px;
    font-family: ui-monospace, monospace;
    font-size: .85rem;
    background: rgba(31,41,55,.78);
    color: white;
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 10px;
    padding: 12px;
}}
.save-row {{ display: flex; gap: 12px; align-items: center; margin-top: 12px; }}
.save-btn {{
    padding: 8px 20px;
    border-radius: 20px;
    background: rgba(34,197,94,.2);
    border: 1px solid rgba(34,197,94,.5);
    color: #bbf7d0;
    cursor: pointer;
}}
.status {{ color: #d1d5db; font-size: .9rem; }}
</style>
</head>
<body>
<div class="container">
<h1>🦦 OtterPi Admin</h1>
<div class="tabs">
    <button class="tab-btn active" onclick="showTab('rooms', this)">Rooms</button>
    <button class="tab-btn" onclick="showTab('alarm', this)">Alarm Limits</button>
    <button class="tab-btn" onclick="showTab('mail', this)">Mail</button>
    <button class="tab-btn" onclick="showTab('notifications', this)">Notifications</button>
</div>

<div id="tab-rooms" class="tab-panel active">
    <textarea id="rooms-text">{rooms_json}</textarea>
    <div class="save-row">
        <button class="save-btn"
                data-endpoint="/api/admin/rooms"
                data-textarea="rooms-text"
                data-status="rooms-status"
                onclick="saveConfig(this)">Save</button>
        <span id="rooms-status" class="status"></span>
    </div>
</div>

<div id="tab-alarm" class="tab-panel">
    <textarea id="alarm-text">{alarm_json}</textarea>
    <div class="save-row">
        <button class="save-btn"
                data-endpoint="/api/admin/alarm-limits"
                data-textarea="alarm-text"
                data-status="alarm-status"
                onclick="saveConfig(this)">Save</button>
        <span id="alarm-status" class="status"></span>
    </div>
</div>

<div id="tab-mail" class="tab-panel">
    <textarea id="mail-text">{mail_json}</textarea>
    <div class="save-row">
        <button class="save-btn"
                data-endpoint="/api/admin/mail"
                data-textarea="mail-text"
                data-status="mail-status"
                onclick="saveConfig(this)">Save</button>
        <span id="mail-status" class="status"></span>
    </div>
</div>

<div id="tab-notifications" class="tab-panel">
    <textarea id="notifications-text">{notifications_json}</textarea>
    <div class="save-row">
        <button class="save-btn"
                data-endpoint="/api/admin/notifications"
                data-textarea="notifications-text"
                data-status="notifications-status"
                onclick="saveConfig(this)">Save</button>
        <span id="notifications-status" class="status"></span>
    </div>
</div>
</div>

<script>
function showTab(name, btn) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
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
</script>
</body>
</html>
"""
