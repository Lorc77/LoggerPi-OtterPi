# Wiedereinstiegsprotokoll – LoggerPi-OtterPi (Stand v1.11.14)

**Projekt:** LoggerPi-OtterPi
**Aktuelle Version:** v1.11.17 (deployed auf OtterPi)
**Teststand:** 428 passed, Ruff/Format clean
**Stand:** 2026-11-09

---

## 0. Scope & Abgrenzung

- **Wir arbeiten ausschließlich am LoggerPi-OtterPi-Projekt.**
- Der **Private Observer** ist ein **eigenes, separates Projekt**. Er wird später semi-neu aus dem fertigen LoggerPi-OtterPi-Code abgeleitet. **Nicht Teil dieser Planung.**
- Das **Admin-Konzept** (ursprünglich für den Private Observer) wurde in seinen generischen Teilen als **„OtterPi Admin"** in LoggerPi-OtterPi integriert.

---

## 1. Architektur (Ist-Stand)

```text
LoggerPi (Python 3.9.2, User=ZOOLOGY-observ)
  Reader (AtmoWEB, Freezer, MEMMERT, WeatherHub)
    ↓
  Core Batch (states, operation, serial, setpoints, device, measurements)
    ↓
  persistente Queue
    ↓
  HTTPS POST /api/v1/batches
    ↓
OtterPi (Python 3.13.5, User=makki)
  nginx (TLS, LAN-only für /admin)
    ↓
  otterpi.observer.service
    ├── Ingestion
    ├── Dashboard (öffentlich)
    ├── Admin (LAN-only, /admin + /api/admin/*)
    ├── Alert-Engine (Thread, 300 s)
    └── SQLite (batches.sqlite3, alerts.sqlite3)
```

**Deploy-Reihenfolge: erst OtterPi, dann LoggerPi.**

---

## 2. Was in dieser Session erledigt wurde (v1.11.11 – v1.11.14)

### v1.11.11 – LoggerPi-Offline-Erkennung

- **`received_at` in der Batch-Tabelle:** OtterPi-seitiger Empfangszeitpunkt wird persistiert (`BatchStore.latest_received_at()`). Fallback auf `created_at` für bestehende Zeilen.
- **`heartbeat.py`:** Gemeinsame Offline-Status-Logik für Admin und Dashboard (`offline_status()`).
- **`alarm_limits.json` → `system`-Sektion:** Konfigurierbare Schwellenwerte (`loggerpi_offline_warning_seconds`, `loggerpi_offline_critical_seconds`) und optionale Warnstufe (`loggerpi_offline_warning_alert_enabled`).
- **Alert-Engine:** `_check_loggerpi_heartbeat()` prüft den Heartbeat vor den Sensor-/State-Checks. Bei Offline werden Sensor-/State-Checks ausgesetzt (Suppression).
- **Admin:** Statusleuchte im Header, System-Karte im Alarm Limits-Tab.
- **Dashboard:** Statusleuchte im Header, „Last measurement" statt „Last update".
- **`deploy/otterpi/install.sh`:** `heartbeat.py` in der Dateiliste.

### v1.11.12 – Acknowledge + Resolve

- **Acknowledge-Verhalten:** Ein acknowledged Alert wird nicht erneut gesendet, solange der Zustand kritisch bleibt. `AlertStore.is_acknowledged()` prüft den letzten aktiven Alert mit demselben `dedup_key`. `_dispatch()` überspringt acknowledged Alerts.
- **Reset bei Normalisierung:** Sobald der Wert wieder innerhalb der Grenzen ist, ruft die Alert-Engine `reset_acknowledged()` auf.
- **Alert-Resolve:** Neue Spalte `resolved_at` in `alerts.sqlite3`. `AlertStore.resolve()` setzt `resolved_at` für **alle offenen** Alerts mit demselben `dedup_key` (Variante 2). `AlertStore.is_active()` prüft, ob der letzte Alert noch nicht resolved ist.
- **Bugfix:** `reset_acknowledged()` und `resolve()` werden nur aufgerufen, wenn der Wert tatsächlich wieder innerhalb der Grenzen ist – nicht schon bei `validity == "valid"`.
- **Admin:** Alerts-Tab mit Status-Chip („Active" / „Resolved"), Filter „Only active", `resolved_at` im JSON.
- **`otterpi.py`:** Query-Parameter `only_active` für `/api/admin/alerts`.

### v1.11.13 – Message-Templates

- **`messages.json`:** Neue Config-Datei mit globalen Regel-Texten („too high", „too low", „invalid", „stale", „low", „open", „alarm", „offline"). Defaults werden verwendet, wenn die Datei fehlt.
- **`MEASUREMENT_DISPLAY_NAMES`:** Festes Mapping von Measurement-Key zu Anzeigename („Temperature", „Humidity", „Vacuum", „CO₂", „Battery", „Door").
- **Alert-Engine:** `_build_message()` und `_build_subject()` bauen die Texte aus Raum, Gerät, Measurement-Name und Regel-Text. Raum/Gerät kommen aus `rooms.json` (Fallback auf technischen `sensor_key`).
- **`Alert`-Dataclass:** Neues Feld `subject`. `EmailNotifier` und `NtfyNotifier` nutzen es mit Fallback auf den bisherigen Subject.
- **Admin:** Neuer Messages-Tab mit Formular-UI (gruppiert in Measurements, States, System), JSON-Editor als „Advanced"-Toggle.
- **`otterpi.py`:** `GET /api/admin/messages`, `PUT /api/admin/messages`.

### v1.11.14 – Resolve-Button + UI-Polish

- **Resolve-Button im Admin-Alerts-Tab:** Manuelles Resolven eines Alerts (per ID). `AlertStore.resolve_by_id()`, `POST /api/admin/alerts/<id>/resolve`.
- **Alert-Tab als Default:** Der Alerts-Tab ist jetzt der erste Tab und wird beim Öffnen des Admins geladen (statt Rooms).
- **Toast-Notification:** Alle Save-/Delete-/Acknowledge-/Resolve-Aktionen zeigen eine kurze Toast-Benachrichtigung (grün für Erfolg, rot für Fehler).
- **Bugfixes:**
  - Stale-/Invalid-Alerts werden resolved, wenn der Sensor wieder `valid` ist.
  - `is_acknowledged()` prüft nur aktive (nicht resolved) Alerts. Ein resolveder Alert blockiert keinen neuen Alert mehr.
  - `reset_acknowledged()` wird nicht mehr beim Resolve aufgerufen. Ein resolveder Alert bleibt acknowledged.

### v1.11.15 – Severity-Auswahl + Rate-of-Change

- **Severity-Auswahl pro Kanal:** `notifications.json` → `severities` pro
  Channel. `NtfyNotifier` und `WebhookNotifier` prüfen die Severity.
  Admin-UI: Checkboxen im Notifications-Tab.
- **Rate-of-Change im Admin:** Spalte „Rate/h" im „Edit Limits"-Formular.
- **Message-Text bei stale/invalid:** Measurement-Key in Klammern.
- **Resolve-Zeitstempel im Alert-Tab.**
- **ntfy-Logging:** `_dispatch` loggt fehlgeschlagene Notifier.

### v1.11.16 – Alarm Limits UI-Umbau

- **Alarm Limits-Tab:** Raum-Kacheln mit Geräte-Kacheln, Limits als farbige
  Chips (Warning gelb, Critical rot, Rate blau, not configured grau).
- **Severity-Checkboxen im Notifications-Tab:** Flex-Layout, klickbare Labels.
- **States-Tabelle im Edit-Limits-Formular:** Linksbündig, `width: auto`.
- **ntfy ASCII-safe Title:** `NtfyNotifier` ersetzt Nicht-ASCII-Zeichen im
  `Title`-Header.

### v1.11.17 – Alarm Limits Polish

- **Letzte Messwerte:** Aktuelle Werte pro Measurement im Alarm Limits-Tab.
- **„Show all"-Filter:** Checkbox unten im Tab.
- **Stale/Invalid pro Gerät:** Neue `device`-Sektion in `alarm_limits.json`.
  Ein Alert pro Gerät, nicht pro Measurement.
- **Nicht-Alarm-Trigger-States entfernt:** `door_locked`, `defrost`, `flap`,
  `lights.*`, `switches.*` aus `sensor_schemas.py`.
- **`operation_mode` entfernt:** Aus `sensor_schemas.py` für `memmert`.
- **Nested State Keys Fix:** Regex erlaubt mehrere Punkte.
- **Chip-Texte gekürzt:** „Warn", „Crit", „not conf.".
- **Einheiten:** „celsius" → „°C", „percent" → „%".

---

## 3. Offene Punkte mit detaillierten Plänen

### 3.6 Dashboard-Limits

**Ziel:** Limits (Warn/Crit Min/Max, Rate-of-Change, Stale) im Dashboard sichtbar machen.

**Vorschläge (alle, nicht nur Empfehlung):**

**1. Gerätekacheln (Raumdetail):**
- **Limit-Badges** unter dem Gerätenamen: z.B. `⚠ 20–26 °C · ⛔ 18–28 °C`.
- **Status-Chip** „Near limit" (gelb), wenn der Wert innerhalb von 10 % des Warn-Limits liegt.
- **Status-Chip** „At limit" (rot), wenn der Wert das Crit-Limit erreicht.

**2. Graphen (Device-Detail + Raumdetail):**
- **Horizontale Linien** für Warn Min/Max (gelb, gestrichelt) und Crit Min/Max (rot, gestrichelt).
- **Chart.js-Plugin** `annotation` (oder manuell via `scales.y.grid`).
- **Legende** mit „Warning Min/Max", „Critical Min/Max".

**3. Device-Detail:**
- **Limits-Tabelle** (zusätzlich zur Statistik): `Warning Min`, `Warning Max`, `Critical Min`, `Critical Max`, `Rate of Change`, `Stale After`.
- **Aktueller Status** relativ zu den Limits (z.B. „OK", „Near warning", „At critical").

**4. Übersicht (Raum-Kacheln):**
- **Limit-Badge** in der Raum-Kopfzeile: z.B. „2 sensors near limit".
- **Status-Lampe** bereits vorhanden (grün/gelb/rot).

**Empfohlene Priorität:**
1. **Graphen:** Horizontale Linien für Warn/Crit (größter visueller Nutzen).
2. **Gerätekacheln:** Limit-Badges (schneller Überblick).
3. **Device-Detail:** Limits-Tabelle (Detail-Info).
4. **Übersicht:** Limit-Badge in Raum-Kopfzeile (optional).

**Konkrete Vorgehensweise:**

1. **`dashboard_data.py` – Limits laden:**
   - Neue Funktion `_device_limits(device_key, device_type)` → liest `alarm_limits.json` und gibt Limits für das Gerät zurück.
   - `_device_chips` erweitern: „Near limit", „At limit".

2. **`dashboard_charts.py` – Chart.js-Plugin:**
   - `_render_device_script` erweitern: Horizontale Linien für Warn/Crit Min/Max.
   - Chart.js-Plugin `annotation` (oder manuell via `scales.y.grid`).

3. **`dashboard.py` – Device-Detail:**
   - Limits-Tabelle in der Info-Card.
   - Status relativ zu Limits.

4. **`dashboard.py` – Raumdetail:**
   - Limit-Badges unter Gerätenamen.

5. **`dashboard.py` – Übersicht:**
   - Limit-Badge in Raum-Kopfzeile.

6. **Tests:**
   - `test_dashboard_data.py`: `_device_limits`, `_device_chips` (Near/At limit).
   - `test_dashboard.py`: Smoke-Tests für Limits-Anzeige.

**Aufwand:** Mittel (2–3 h).

---

### 3.8 Hysterese (Reset-Hysterese)

**Problem:** Aktuell gibt es keine Hysterese. Wenn der Wert um den Limit-Punkt flackert, könnte nach `dedup_seconds` (1 Stunde) erneut ein Alert kommen.

**Ziel:** Reset-Hysterese, nicht Trigger-Hysterese. Der Alert wird ausgelöst, wenn `value > threshold` (nicht `threshold + hysteresis`). Aber: Der Alert wird erst zurückgesetzt, wenn `value < threshold - hysteresis`.

**Beispiel:**
- `critical_max: 28.0`, `hysteresis: 0.5`.
- Trigger: `value > 28.0`.
- Reset: `value < 27.5`.
- Zwischen 27.5 und 28.0: Kein neuer Alert (Hysterese-Band).

**Konkrete Vorgehensweise:**

1. **`alarm_limits.json` – neues Feld `hysteresis`:**
   ```json
   {
     "sensors": {
       "atmoweb_101.temperature_1": {
         "critical_max": 28.0,
         "hysteresis": 0.5,
         "enabled": true
       }
     }
   }
   ```

2. **`config_store.py` – `_validate_alarm_limits` erweitern:**
   - `_ALLOWED_LIMIT_KEYS` um `hysteresis` erweitern.
   - Validierung: Zahl >= 0.

3. **`alert_engine.py` – `_check_sensors` erweitern:**
   - `hysteresis = limits.get("hysteresis", 0.0)`
   - Trigger: `value > threshold` (wie bisher).
   - Reset: `value < threshold - hysteresis` (statt `value <= threshold`).

4. **`alert_store.py` – `is_active(dedup_key)` prüfen:**
   - Wenn der Alert aktiv ist und der Wert im Hysterese-Band liegt, kein neuer Alert.
   - Wenn der Wert unter `threshold - hysteresis` fällt, `resolve()` aufrufen.

5. **`admin.py` – „Edit Limits"-Formular um `hysteresis`-Feld erweitern:**
   - Zusätzliche Spalte `<th>Hysteresis</th>`.
   - Zusätzliche Zelle pro Measurement.

6. **Tests:**
   - `test_config_store.py`: `hysteresis` wird validiert.
   - `test_alert_engine.py`: Hysterese verhindert mehrfache Alerts; Reset bei `value < threshold - hysteresis`.

**Aufwand:** Mittel (2–3 h).

---

## 4. Advanced Updates (Abschnitt 5, aus dem ursprünglichen Protokoll)

### 5.1 „Send on change" für device/setpoints

**Problem:** `device` und `setpoints` werden aktuell in jedem Batch mitgeschickt (~25 % Overhead, ~2–3 KB pro Batch). Sie ändern sich aber praktisch nie.

**Ziel:** Nur beim ersten Kontakt und bei Änderung senden.

**Konkrete Vorgehensweise:**

1. **LoggerPi – State-Datei:**
   - Neue Datei `device_state.json` in `/var/lib/loggerpi-otterpi/`.
   - Format: `{"device": {...}, "setpoints": {...}}`.
   - `runtime.py`: Vor dem Batch-Versand `device`/`setpoints` mit State-Datei vergleichen. Unverändert → weglassen. Geändert → mitsenden und State-Datei aktualisieren.

2. **OtterPi – `device_metadata`-Tabelle:**
   - Neue Tabelle in `batches.sqlite3` (oder separate `metadata.sqlite3`).
   - `BatchStore.store()`: Wenn `device`/`setpoints` im Batch vorhanden, in `device_metadata` speichern.
   - `dashboard_data.py`: `_latest_device` liest aus `device_metadata` statt aus dem letzten Batch.

3. **Tests:**
   - `test_runtime.py`: `device`/`setpoints` werden nur bei Änderung gesendet.
   - `test_otterpi_store.py`: `device_metadata` wird korrekt gespeichert/gelesen.

**Aufwand:** Groß (4–6 h).

---

### 5.2 Advanced Diagnostics (pro Device)

**Idee:** Tiefere Transport-Diagnose pro Gerät, nicht nur `validity`/`states`.

| Device | Mögliche Diagnostics |
|---|---|
| AtmoWEB | HTTP-Status, Timeouts, Latenz pro Request |
| MEMMERT | Seriell-Zähler (wie Freezer) |
| WeatherHub | Paketanzahl, CRC-Fehler, letzter Paketzeitpunkt pro Sensor |

**Status:** Nicht designed. Wäre eine neue Ebene (`diagnostics.<device>` oder generalisiertes `diagnostics`). `serial.diagnostics` ist im Vertrag freezer-spezifisch. Für die anderen Devices gibt es noch kein Äquivalent.

**Entscheidung:** Nicht jetzt. Wenn konkreter Bedarf (z. B. „AtmoWEB antwortet langsam", „WeatherHub CRC-Fehler häufen sich"), führen wir es bewusst ein.

**Aufwand:** Groß (4–6 h).

---

### 5.3 `serial.diagnostics` für den Freezer

**Felder:**
```text
serial.diagnostics
├── last_rx_at
├── seconds_since_rx
├── lines_received
├── parse_errors
└── reconnect_count
```

**Zweck:**
- Rohdaten-Ebene hinter `serial.state`.
- OtterPi kann eigene Schwellen/Trends anwenden (z. B. „keine Daten seit X min", steigende `parse_errors`, viele `reconnect_count`).
- Diagnose ohne Re-Derivation.

**Konkrete Vorgehensweise:**

1. **`freezer.py` – Zähler:**
   - Neue Attribute: `_lines_received`, `_parse_errors`, `_reconnect_count`, `_last_rx_at`.
   - `_drain_pending()`: `_lines_received` erhöhen, `_last_rx_at` setzen.
   - `_parse_frame()`: Bei Fehler `_parse_errors` erhöhen.
   - `_open_serial()`: Bei Reconnect `_reconnect_count` erhöhen.

2. **`freezer.py` – `serial`-Property erweitern:**
   ```python
   @property
   def serial(self) -> dict:
       return {
           "device": self.port,
           "state": state,
           "diagnostics": {
               "last_rx_at": self._last_rx_at,
               "seconds_since_rx": ...,
               "lines_received": self._lines_received,
               "parse_errors": self._parse_errors,
               "reconnect_count": self._reconnect_count,
           },
       }
   ```

3. **`runtime.py`:** `serial` wird bereits in den Batch übernommen. Keine Änderung nötig.

4. **`dashboard_data.py`:** `_latest_serial` erweitern, um Diagnostics anzuzeigen.

5. **Tests:** `test_freezer.py` erweitern.

**Aufwand:** Mittel (2 h).

---

### 5.4 Events (`events[]`, nur bei Änderung)

**Prinzip:** Events sind ein eigener Kanal, getrennt vom Core Batch. Sie werden nur bei Änderung übertragen (nicht in jedem Batch).

**Beispiele:**
- Service-Ausfall / Restart
- Connectivity-Change
- Device-Event (Tür geöffnet, Wasserkontakt, Freezer-Alarm-Übergang)
- Metadata-Change

**Aktueller Stand:**
- Keine Events implementiert.
- Die Alert-Engine (Phase B) leitet Übergänge aus States ab (aktueller State vs. letzter State). Das reicht für „Tür offen", „Freezer-Alarm aktiv", „Battery Low".
- **Grenze:** Wenn eine Tür zwischen zwei Batches (15 min) auf- und wieder zugeht, sieht der OtterPi nur „zu" – der Übergang geht verloren. Für garantierte Ereignis-Zustellung bräuchte es das echte `events[]`-Channel.

**Konkrete Vorgehensweise:**

1. **LoggerPi – `events[]` im Batch:**
   - Neues Top-Level-Feld `events` in `Batch`.
   - Format: `[{"type": "door_open", "device": "atmoweb_101", "timestamp": "...", "details": {...}}]`.
   - `runtime.py`: Events aus Readern sammeln (z.B. `atmoweb.py` erkennt Tür-Übergang).

2. **OtterPi – `events`-Tabelle:**
   - Neue Tabelle in `batches.sqlite3` (oder separate `events.sqlite3`).
   - `BatchStore.store()`: Events speichern.
   - `alert_engine.py`: Events als Trigger nutzen (zusätzlich zu States).

3. **Tests:** `test_runtime.py`, `test_otterpi_store.py`, `test_alert_engine.py`.

**Aufwand:** Groß (6–8 h).

---

### 5.5 ntfy-Token in env

**Aktuell:** Token steht in `notifications.json`.

**Problem:** Bei geschütztem Topic ist das ein Secret.

**Vorgemerkt:** Später in `otterpi.env` ziehen (z. B. `NTFY_TOKEN`).

**Konkrete Vorgehensweise:**

1. **`otterpi.env`:** `NTFY_TOKEN=<token>` hinzufügen.

2. **`notifier.py` – `NtfyNotifier`:**
   ```python
   class NtfyNotifier:
       def __init__(self, config: dict, token: Optional[str] = None) -> None:
           self.url = config["url"].rstrip("/")
           self.topic = config["topic"]
           self.token = token or config.get("token")
   ```

3. **`create_notifiers`:** `token` aus `os.environ.get("NTFY_TOKEN")` übergeben.

4. **`config_store.py`:** `_validate_notifications` erlauben, dass `token` fehlt (wenn in env).

5. **Tests:** `test_notifier.py` erweitern.

**Aufwand:** Klein (30 Min).

---

### 5.7 ntfy self-host (Komfort-Update)

**Ziel:** ntfy auf dem OtterPi selbst hosten, um geschützte Topics (Token-Auth) zu ermöglichen und keine öffentlichen Topics mehr zu nutzen.

**Ressourcenverbrauch:**
- RAM: ~10–30 MB (Idle), ~30–50 MB (unter Last).
- CPU: <1 % (Idle).
- Disk: ~1 MB (Config) + Nachrichten-Cache (optional).
- Binary: ~20 MB (Go, ARM64).

**Aufwand:** ~30–60 Minuten.

**Konkrete Vorgehensweise:**

1. **Binary herunterladen:**
   ```bash
   wget https://github.com/binwiederhier/ntfy/releases/latest/download/ntfy_<version>_linux_arm64.tar.gz
   tar -xzf ntfy_<version>_linux_arm64.tar.gz
   sudo mv ntfy /usr/local/bin/
   ```

2. **systemd-Service:**
   ```ini
   [Unit]
   Description=ntfy
   After=network.target

   [Service]
   User=ntfy
   Group=ntfy
   ExecStart=/usr/local/bin/ntfy serve
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. **Config (`/etc/ntfy/server.yml`):**
   ```yaml
   base-url: "https://ntfy.makki.route64.de"
   listen-http: ":2586"
   cache-file: "/var/cache/ntfy/cache.db"
   auth-file: "/var/lib/ntfy/user.db"
   auth-default-access: "deny-all"
   ```

4. **User anlegen:**
   ```bash
   sudo ntfy user add --role=admin makki
   ```

5. **nginx-Reverse-Proxy (optional, für TLS):**
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:2586;
       proxy_http_version 1.1;
       proxy_set_header Host \$host;
       proxy_set_header Upgrade \$http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

6. **Testen:**
   ```bash
   curl -u makki:passwort -d "Test" https://ntfy.makki.route64.de/loggerpi-alerts
   ```

7. **`notifications.json` anpassen:**
   ```json
   {
     "channels": [
       {
         "type": "ntfy",
         "enabled": true,
         "url": "https://ntfy.makki.route64.de",
         "topic": "loggerpi-alerts",
         "token": "<token>"
       }
     ]
   }
   ```

8. **`otterpi.env`:** `NTFY_TOKEN=<token>` (siehe 5.5).

**Aufwand:** Mittel (1 h).

---

## 5. Verschobene Punkte

### 5.1 Auf „irgendwann" verschoben

| Punkt | Zweck | Status |
|---|---|---|
| **CSV-Export** | Daten als CSV exportieren (für Excel/Analyse). | ⏸️ verschoben |
| **Statuspage** | Service-Status, Queue, letzter Upload, Sensor-Empfang. | ⏸️ verschoben (Integration in bestehende Statuspage unklar) |
| **Dry-Run / Test-Mode** | Alerts ohne Versand testen. | ⏸️ verschoben (durch `enabled: false` in `mail.json` simulierbar) |
| **Config-Backup/Restore** | Configs exportieren/importieren. | ⏸️ verschoben (`config_store.py` macht bereits `.bak`) |

### 5.2 Auf „später" verschoben (wenn Admin öffentlich mit Login)

| Punkt | Zweck | Status |
|---|---|---|
| **Audit-Log** | Wer hat wann was geändert. | ⏸️ verschoben (sinnvoll bei mehreren Nutzern) |

### 5.3 Gestrichen

| Punkt | Grund |
|---|---|
| **Door-Open-Dauer** | HPP260 unterstützt `door_open` nicht (liefert `N/A`). Geparkt für evtl. zukünftige AtmoWEB-Geräte. |
| **Service-Restart** | Nicht nötig, weil JSON-Configs automatisch gelesen werden (mtime-Cache, `load_*()` bei jedem `_check`). |

---

## 6. Design-Entscheidungen (DECs)

Die folgenden DECs sind in dieser Session entstanden und sollten nicht rückgängig gemacht werden:

- **DEC-063:** `received_at` in der Batch-Tabelle (OtterPi-seitiger Empfangszeitpunkt).
- **DEC-064:** LoggerPi-Offline-Erkennung (2-stufiger Heartbeat: 30 min gelb, 1 h rot).
- **DEC-065:** Suppression der Sensor-/State-Checks bei Offline.
- **DEC-066:** `system`-Sektion in `alarm_limits.json`.
- **DEC-067:** Acknowledge-Verhalten (Option B: acknowledged Alert wird nicht erneut gesendet, bis der Zustand sich ändert).
- **DEC-068:** Alert-Resolve (Active vs. Resolved, Variante 2: alle offenen Alerts mit demselben `dedup_key` werden resolved).
- **DEC-069:** Bugfix: Reset/Resolve nur bei normalem Wert (nicht schon bei `validity == "valid"`).
- **DEC-070:** Message-Templates (globale Regel-Texte + Measurement-Name).
- **DEC-071:** Subject mit Raum/Gerät/Measurement-Name.
- **DEC-072:** Manueller Resolve-Button (kein automatischer Sweep für verwaiste Alerts).
- **DEC-073:** Alert-Tab als Default-Tab.
- **DEC-074:** Toast-Notification für Save-Buttons.

**Bewusste Entscheidungen, die nicht rückgängig gemacht werden sollten:**

- **Kein Sweep für verwaiste Alerts:** Wenn ein Sensor nicht mehr im Batch ist (z.B. Batterie leer), wird der Alert **nicht** automatisch resolved. Stattdessen manueller Resolve-Button. Grund: Ein Sweep würde auch Alerts resolven, deren Problem schlimmer geworden ist.
- **`is_acknowledged()` prüft nur aktive Alerts:** Ein resolveder Alert blockiert keinen neuen Alert, auch wenn er acknowledged war.
- **`reset_acknowledged()` wird nicht mehr beim Resolve aufgerufen:** Ein resolveder Alert bleibt acknowledged.
- **Message = Regel-Text + Measurement-Name:** Keine per-Sensor-Templates. Neue Measurements brauchen nur einen Eintrag in `MEASUREMENT_DISPLAY_NAMES`.
- **Subject kürzer als Message:** Subject = `[CRITICAL] Temperature — Raum / Gerät`, Message = `Raum / Gerät — Temperature too high: 30.0 °C > 28.0 °C`.
- **Test-Mail bleibt statisch:** Die Test-Mail nutzt nicht das neue Format. Bewusste Entscheidung, um Aufwand zu sparen.

---

## 7. Technische Leitplanken

- **Python 3.9** ist verbindlich (LoggerPi 3.9.2). Keine PEP-604-Unions (`str | None`), kein `match`. `Optional`/`Union` verwenden. Ruff `target-version = "py39"`, `FA102` aktiv.
- **Keine neuen Runtime-Dependencies** (`pyserial` bleibt einzige; `smtplib`/`urllib` sind stdlib).
- **OtterPi-Service** läuft als `makki`.
- **Config-Dir:** `/var/lib/loggerpi-otterpi/config/`.
- **Deploy-Reihenfolge:** OtterPi → LoggerPi.
- **Quality Gates:** `ruff check .`, `ruff format --check .`, `pytest`, `git diff --check`.
- **Versionierung:** `pyproject.toml`, `__init__.py`, `dashboard_constants.py`, Git-Tag. Alle drei müssen konsistent sein.

---

## 8. Nächster konkreter Schritt

**Empfohlene Reihenfolge für morgen:**

1. **3.7 Rate-of-Change im Admin** (30 Min) – klein, schließt eine Lücke.
2. **3.6 Dashboard-Limits** (2–3 h) – visuell, inhaltlich relevant.
3. **3.2 UI-Umbau Alarm Limits** (2–3 h) – größerer UI-Eingriff.
4. **3.8 Hysterese** (2–3 h) – verhindert Flackern.

**Danach (nach Bedarf):**
- Advanced Updates (5.1–5.5, 5.7).
- Verschobene Punkte (CSV-Export, Statuspage, Dry-Run, Config-Backup/Restore, Audit-Log).

---

## 9. Bekannte Lücken / bewusste Entscheidungen

| Lücke | Grund | Status |
|---|---|---|
| Test-Mail nutzt nicht das neue Format | Bewusste Entscheidung, um Aufwand zu sparen | ⏸️ |
| Kein Sweep für verwaiste Alerts | Würde falsch-positive Resolves erzeugen | ⏸️ (manueller Resolve-Button) |
| Hysterese nicht implementiert | Noch nicht gebaut | ⏳ (3.8) |
| `rate_of_change_max_per_hour` nicht im Admin-Formular | Noch nicht gebaut | ⏳ (3.7) |
| Dashboard zeigt keine Limits | Noch nicht gebaut | ⏳ (3.6) |
| Alarm Limits-Tab ist flache Liste | Noch nicht umgebaut | ⏳ (3.2) |

---

## 10. Offene Fragen

- Soll `dedup_seconds` angepasst werden? (Aktuell: 3600 s = 1 Stunde.)
- Soll `from_name` in `mail.json` bleiben? (Ja, umgesetzt.)
- Soll `btn-warning` entfernt werden? (Aktuell: behalten für spätere Aktionen.)
- Soll die Statuspage in die bestehende System-Statuspage integriert werden? (Unklar, aufgeschoben.)
