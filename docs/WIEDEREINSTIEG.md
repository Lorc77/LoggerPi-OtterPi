# Wiedereinstiegsprotokoll – LoggerPi-OtterPi (Stand v1.11.14)

**Projekt:** LoggerPi-OtterPi
**Aktuelle Version:** v1.12.1 (deployed auf OtterPi)
**Teststand:** 432 passed, Ruff/Format clean
**Stand:** 2026-11-10

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

### v1.11.18 – Alert-Message + Chip-Polish

- **Alert-Messages:** Werte auf 1 Nachkommastelle gerundet, Einheiten
  umgewandelt (`celsius` → `°C`, `percent` → `%`).
- **Chip-Texte:** Pfeile für Min/Max (`↓ 20 °C ↑ 23 °C`,
  `↓ 18 °C ↑ 28 °C`, `↕ 1 °C/h`). Nicht konfiguriert: `Warn n/c`,
  `Crit n/c`, `Rate n/c`.
- **`resolve`-Fix:** Alert bleibt aktiv, wenn mindestens ein Channel
  `invalid`/`stale` ist. `resolve` wird nur aufgerufen, wenn alle Channels
  `valid` sind.
- **`UNIT_LABELS`/`unitLabel` in `admin.py`:** Einheiten in Chips und
  Messwerten umgewandelt.
- **`max-content` für State-Chips:** Chip nimmt nur so viel Platz wie nötig.
- **„not applicable" für leere States:** Statt leerer Sektion.
- **Doppelte `.device-row`-Definition bereinigt.**

### v1.11.19 – How-to-Texte + Delete-Sicherheit

- **How-to-Texte in allen Tabs** (Rooms, Alarm Limits, Mail, Notifications,
  Messages, Alerts).
- **Delete-Sicherheit:** Doppelte Abfrage, Räume mit Sensoren können nicht
  gelöscht werden, Limits werden mit dem Sensor gelöscht.

### v1.12.0/v1.12.1 – Dashboard-Limits

- **Limit-Chips** in den Metric-Zellen (Raumdetail: kompakt, Device-Detail:
  ausführlich).
- **Statusleuchte** reagiert auf Limit-Verletzungen.
- **Status-Chips** in der Chip-Leiste.
- **Horizontale Limit-Linien** in den Charts.
- **Bugfixes:** Y-Achse, humidity-Achse, `_stale_age`, Chip-Reihenfolge,
  doppelte Limit-Schleife, Flex-Layout.

---

## 3. Offene Punkte mit detaillierten Plänen

## 3.6 Dashboard-Limits (Konzept, Stand 2026-11-10) --> erledigt, noch nicht getestet.. diesen Punkt nach test entfernen

**Ziel:** Limits (Warn/Crit Min/Max, Rate-of-Change) im Dashboard sichtbar
machen – ohne Redundanz, ohne Overengineering.

### 3.6.1 Design-Entscheidungen

- **Keine Limits für Raumtemperatur.** Die Raumtemperatur ist ein Mittelwert,
  keine Regel. Die einzelnen Sensoren haben Limits.
- **Chips nur auf Raumdetail (verkürzt) und Device-Detail (ausführlich).**
  Nicht auf der Übersicht, nicht auf Climate-Detail.
- **Chips nur, wenn Limits gesetzt und enabled sind.** Sonst weglassen
  (kein „–").
- **Statusleuchte folgt derselben Logik** wie die Chips (Limit-Verletzungen
  werden erkannt).
- **Graphen-Linien als separate Datasets** (konstante Werte), keine
  zusätzliche Dependency.
- **Keine Statistik-Blöcke, keine Tabellen, keine Kopfzeilen.**

### 3.6.2 Was wo erscheint

| Seite | Chips? | Format | Graphen-Linien? |
|---|---|---|---|
| **Übersicht (Raum-Kacheln)** | ❌ Nein | – | ❌ Nein |
| **Raumdetail (Gerätekacheln)** | ✅ Ja | Verkürzt: `↓ 15 °C ↑ 18 °C` | ✅ Ja |
| **Device-Detail** | ✅ Ja | Ausführlich: `Warning: ↓ 15 °C ↑ 18 °C` | ✅ Ja |
| **Climate-Detail** | ❌ Nein | – | ❌ Nein |

**Platzierung:** Rechtsbündig im Header, wo `🌡️ Temperature 16.3 °C` bzw.
`💧 Relative Humidity 62.2 %` steht. Die Chips werden **übereinander**
angeordnet (Flex-Column, rechtsbündig).

**Nur die Limits des jeweiligen Headers:** Bei ID01-Sensoren wird nur
`temperature_2` angezeigt (nicht `temperature_1`). Bei AtmoWEB werden
`temperature_1` und `humidity` angezeigt.

### 3.6.3 Chip-Logik

**Limit-Chips (immer sichtbar, wenn Limit gesetzt und enabled):**
- `[↓ 15 °C ↑ 18 °C]` (gelb) – Warning Min/Max.
- `[↓ 13 °C ↑ 20 °C]` (rot) – Critical Min/Max.
- `[↕ 3 °C/h]` (blau) – Rate-of-Change.

**Status-Chips (nur wenn Zustand aktiv):**
- `[Warning: below limit]` (gelb) – wenn `value < warning_min`.
- `[Warning: above limit]` (gelb) – wenn `value > warning_max`.
- `[Critical: below limit]` (rot) – wenn `value < critical_min`.
- `[Critical: above limit]` (rot) – wenn `value > critical_max`.
- `[Warning: rate of change above limit]` (gelb) – wenn
  `abs(rate) > rate_of_change_max_per_hour`.

**Mehrere Status-Chips simultan möglich:** z.B.
`[Warning: above limit] [Battery low] [Door open]`.

### 3.6.4 Statusleuchte-Logik

**Prioritäten (Rot > Gelb > Grün > Grau):**
1. **Rot:** Alarm (freezer.alarms), Invalid, Critical (below/above limit).
2. **Gelb:** Warning (below/above limit), Warning (rate of change above
   limit), Stale, Battery low.
3. **Grün:** OK.
4. **Grau:** Offline.

**Die Statusleuchte auf der Übersicht folgt derselben Logik** (via
`_device_status`). Wenn wir `_device_status` erweitern, folgt die Übersicht
automatisch.

### 3.6.5 Graphen-Linien

**Wo:** Device-Detail, Raumdetail. **Nicht** Climate-Detail.

**Welche Linien:**
- **Warn Min/Max:** gelb (`#eab308`), gestrichelt (`borderDash: [5, 5]`).
- **Crit Min/Max:** rot (`#ef4444`), gestrichelt (`borderDash: [5, 5]`).
- **Nur wenn Limits gesetzt:** Sonst keine Linien.

**Implementierung:** Separate Datasets pro Limit-Linie, mit konstanten
Werten (`tempValues.map(() => 15)`), `pointRadius: 0`, `borderWidth: 1`.

**Legende:** „Warning Min/Max", „Critical Min/Max" (ausblendbar).

### 3.6.6 Implementierungsschritte

**Schritt 1: Chips (Raumdetail + Device-Detail)**

1. **`dashboard_data.py`:**
   - `_device_limits(device_key, device_type)` – liest `alarm_limits.json`,
     gibt `None` zurück, wenn keine Limits gesetzt sind.
   - `_device_status` erweitern: Limit-Verletzungen erkennen.
   - `_device_chips` erweitern: Limit-Chips hinzufügen.

2. **`dashboard.py`:**
   - Chips in den Metric-Zellen (Raumdetail + Device-Detail).
   - CSS für die Chips (Flex-Column, rechtsbündig).

3. **Tests:**
   - `test_dashboard_data.py`: `_device_limits`, `_device_status`
     (Limit-Verletzungen), `_device_chips` (Limit-Chips).
   - `test_dashboard.py`: Smoke-Tests.

**Schritt 2: Statusleuchte (Raumdetail + Device-Detail)**

- `_device_status` erweitern (siehe 3.6.4).
- Tests.

**Schritt 3: Graphen-Linien (Device-Detail + Raumdetail)**

- `dashboard_charts.py`: `_render_device_script` erweitern, um Limit-Linien
  als separate Datasets hinzuzufügen.
- Tests.

### 3.6.7 Offene Fragen

- **Rate-of-Change in der Statusleuchte:** Soll die Lampe auch auf
  Rate-of-Change reagieren? (Vorschlag: ja, gelb.)
- **Stale/Invalid:** Die Lampe zeigt schon stale/invalid. Das bleibt.
- **Chips auf der Übersicht:** Nein (entschieden).
- **Chips auf Climate-Detail:** Nein (entschieden).
- **Limits für Raumtemperatur:** Nein (entschieden).

### 3.6.8 Bekannte Lücken

- **Keine Limits für Raumtemperatur:** Bewusste Entscheidung.
- **Keine Chips auf der Übersicht:** Bewusste Entscheidung.
- **Keine Chips auf Climate-Detail:** Bewusste Entscheidung.

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

### 3.10 Alert-Tab-Überarbeitung

**Problem:** Der Alert-Tab wächst mit jedem Alert. Bei vielen Alerts wird die
Liste unübersichtlich.

**Ziel:** Übersichtlichere Darstellung, schnellere Orientierung.

**Ideen (zu besprechen):**

1. **Filter:**
   - Severity: critical / warning / alle.
   - Raum: Dropdown (alle Räume / R1304 / R1306 / …).
   - Gerät: Dropdown (alle Geräte / spezifisches Gerät).
   - Status: active / resolved / acknowledged / alle.

2. **Kompakte Tabelle statt Karten:**
   - Eine Zeile pro Alert: Zeit, Gerät, Regel, Severity, Status, Aktionen.
   - Mehr Alerts auf einen Blick.
   - Weniger visuell (keine Lampe, keine Karte).

3. **Gruppierung nach Datum:**
   - Alerts nach Tag gruppiert (heute, gestern, älter).

4. **Accordion pro Gerät:**
   - Jedes Gerät ein Accordion. Eingeklappt: Gerätename + Anzahl.
   - Aufgeklappt: Die Alerts.

5. **Zusammenfassung oben:**
   - `3 active critical · 5 active warning · 12 resolved`.

6. **Pagination / „Load more":**
   - Nur die letzten 20 Alerts, mit „Load more"-Button.

7. **Dedup-Anzeige:**
   - Wenn ein Alert mehrfach ausgelöst wurde (z.B. jede Stunde), nur den
     letzten anzeigen, mit Zähler (`3×`).

**Empfehlung:** Kombination aus 1 + 2 + 3 (Filter, kompakte Tabelle,
Gruppierung nach Datum). Aufwand: 2–3 h.

**Status:** Nach 3.6 (Dashboard-Limits) besprechen.

---

### 3.11 Admin nach außen öffnen (nicht nur LAN)

**Aktuell:** Der Admin ist LAN-only via nginx (`allow 192.168.178.0/24;
deny all;`). Kein Login, keine Authentifizierung.

**Ziel:** Admin von außen erreichbar machen, mit angemessener
Authentifizierung und Sicherheit.

**Sicherheits-Level (zu besprechen):**

**Level 1 (Minimum):**
- HTTPS-only (bereits vorhanden).
- Basic Auth oder Token-basierte Auth.
- Rate Limiting (nginx `limit_req`).
- **Aufwand:** Klein (1 h).
- **Risiko:** Basic Auth ist anfällig für Brute-Force. Nur mit HTTPS und
  starken Passwörtern akzeptabel.

**Level 2 (Standard):**
- Session-basierte Auth (Login-Formular).
- CSRF-Schutz.
- Sichere Cookies (HttpOnly, Secure, SameSite=Strict).
- Passwort-Hashing (bcrypt/argon2).
- Account-Lockout nach Fehlversuchen.
- **Aufwand:** Mittel (4–6 h).
- **Risiko:** Self-Made-Auth im Python-Server (`BaseHTTPRequestHandler`) ist
  fehleranfällig. Besser: Reverse-Proxy mit Auth.

**Level 3 (Fortgeschritten):**
- 2FA (TOTP).
- Audit-Log (wer hat wann was geändert).
- Fail2ban.
- Content-Security-Policy.
- **Aufwand:** Groß (8–12 h).

**Level 4 (Maximum):**
- Reverse-Proxy mit Auth (z.B. Authelia, Authentik).
- OIDC / SSO.
- **Aufwand:** Mittel (2–4 h), aber abhängig von der Lösung.
- **Vorteil:** Bewährte Auth-Lösung, weniger Self-Made-Code.

**Empfehlung:** Level 4 (Reverse-Proxy mit Auth, z.B. Authelia). Begründung:
- Bewährte Lösung, weniger Self-Made-Code.
- Zentrale Auth für alle Admin-Routen.
- Erweiterbar (2FA, SSO).
- Der Python-Server (`otterpi.py`) bleibt auth-agnostisch.

**Alternativ:** Level 2 (Self-Made-Auth), wenn keine externe Lösung gewünscht
ist. Aber: Mehr Aufwand, mehr Risiko.

**Status:** Später (nach 3.6, 3.8, Alert-Tab).

---

### 3.13 Gemeinsame Logik / Refactoring

**Problem:** Mehrere Logiken sind dupliziert. Das führt zu Inkonsistenzen und
Wartungsaufwand.

#### 3.13.1 Alert-Logik (Dashboard vs. Alert-Engine)

| Logik | Dashboard | Alert-Engine |
|---|---|---|
| **Grenzwerte** (critical/warning min/max) | `_limit_status` | `_check_sensors` |
| **Stale/Invalid** | `_device_status` | `_check_sensors` |
| **States** (battery_low, door_open, etc.) | `_device_chips` | `_check_states` |
| **Rate-of-Change** | `_calculate_rate_of_change` | `_calculate_rate_of_change` |

**Ziel:** Eine gemeinsame Status-Berechnung (z.B. `status.py`), die von beiden
verwendet wird.

**Vorschlag:**
1. Neue Datei `status.py` mit gemeinsamen Funktionen:
   - `calculate_rate_of_change(batches, measurement_key, hours)`.
   - `check_limits(measurements, limits)` → `(status, chips)`.
   - `check_states(states, rules)` → `(status, chips)`.
   - `check_stale_invalid(measurements, device_config)` → `(status, chips)`.
2. `alert_engine.py` importiert diese Funktionen.
3. `dashboard_data.py` importiert diese Funktionen.
4. Beide verwenden dieselbe Logik.

**Hotfix (bereits live):** Dashboard-Rate-of-Change an Alert-Engine angepasst
(alle Batches, erster/letzter Wert, `created_at`).

#### 3.13.2 Chart-Logik (dashboard_charts.py vs. dashboard.py)

**Problem:** Die Chart.js-Skripte sind dupliziert:
- `_render_device_script` (in `dashboard_charts.py`) für die Gerätekacheln
  (Raumdetailseite).
- `_render_device_detail` (in `dashboard.py`) für die Device-Detailseite.

Beide enthalten ähnliche Tooltip-, Legenden- und Skalen-Logik. Änderungen
müssen an mehreren Stellen gemacht werden.

**Ziel:** Eine gemeinsame Funktion `_render_chart_script(device, options)`,
die von beiden verwendet wird.

**Vorschlag:**
1. Gemeinsame Funktion in `dashboard_charts.py`:
   `_render_chart_script(device, *, height, show_limits, show_legend)`.
2. `_render_device_script` ruft sie mit `height=280, show_limits=True` auf.
3. `_render_device_detail` ruft sie mit `height=400, show_limits=True` auf.
4. `_render_climate_detail` ruft sie mit `show_limits=False` auf (keine
   Limit-Linien).

**Aufwand:** Mittel (2–3 h).

#### 3.13.3 Unit-Labels (alert_engine.py vs. admin.py)

**Problem:** `UNIT_LABELS` ist zweimal definiert:
- `alert_engine.py` (für Alert-Messages).
- `admin.py` (für die Chips im Alarm Limits-Tab).

**Ziel:** Eine gemeinsame Konstante in `sensor_schemas.py` (oder einer neuen
`units.py`).

**Vorschlag:**
1. `UNIT_LABELS` in `sensor_schemas.py` verschieben.
2. `alert_engine.py` und `admin.py` importieren sie.

**Aufwand:** Klein (30 Min).

#### 3.13.4 Measurement-Display-Names (sensor_schemas.py vs. dashboard_data.py)

**Problem:** Die Anzeigenamen für Measurements sind zweimal definiert:
- `MEASUREMENT_DISPLAY_NAMES` in `sensor_schemas.py` (für Alert-Messages).
- `display_name`-Map in `dashboard_data.py` (`_device_chips`).

**Ziel:** Eine gemeinsame Konstante in `sensor_schemas.py`.

**Vorschlag:**
1. `display_name`-Map in `dashboard_data.py` durch
   `MEASUREMENT_DISPLAY_NAMES` ersetzen.
2. `dashboard_data.py` importiert `MEASUREMENT_DISPLAY_NAMES`.

**Aufwand:** Klein (30 Min).

#### 3.13.5 Offline-Thresholds (dashboard.py vs. alert_engine.py)

**Problem:** Die Offline-Schwellenwerte werden an zwei Stellen gelesen:
- `_offline_thresholds` in `dashboard.py` (für die Statusleuchte im Header).
- `_check_loggerpi_heartbeat` in `alert_engine.py` (für den Offline-Alert).

**Ziel:** Eine gemeinsame Funktion in `heartbeat.py` (oder `config_store.py`).

**Vorschlag:**
1. `load_offline_thresholds()` in `heartbeat.py`.
2. `dashboard.py` und `alert_engine.py` importieren sie.

**Aufwand:** Klein (30 Min).

#### 3.13.6 RAM-Optimierung

**Problem:** Der OtterPi hat nur ~966 MB RAM (aktuell 742 MB verfügbar). Bei
langen Zeiträumen (90d) könnten die Batches viel RAM verbrauchen.

**Optimierungen:**

1. **SQL-Filterung in `_recent_batches`:**
   - Aktuell: Alle Batches werden geladen (`LIMIT`), dann in Python nach
     `created_at >= cutoff` gefiltert.
   - Neu: `WHERE created_at >= ?` in SQL. Das reduziert die Anzahl der
     geladenen Batches.
   - **Gewinn:** Bei 24h: ~50% weniger Batches (~5–10 MB). Bei 90d: ~10–15 MB.

2. **mtime-Cache für `alarm_limits.json`:**
   - Aktuell: `_device_limits` ruft `load_alarm_limits()` bei jedem Aufruf auf
     (46 Datei-Lesevorgänge pro Dashboard-Render).
   - Neu: mtime-Cache (analog zu `get_rooms()` in `dashboard_config.py`).
   - **Gewinn:** ~0 MB RAM (nur CPU-Entlastung).

3. **Chart-Daten per AJAX (optional):**
   - Aktuell: Chart-Daten werden als JSON in den HTML-Code eingebettet.
   - Neu: `GET /api/dashboard/series?device=...&range=...`.
   - **Gewinn:** Bei 90d: ~5–8 MB (weniger HTML-Generierung).
   - **Aufwand:** 2–3 h (größerer Umbau).

**Geschätzte RAM-Gewinne:**

| Optimierung | Gewinn (24h) | Gewinn (90d) |
|---|---|---|
| SQL-Filterung | ~5–10 MB | ~10–15 MB |
| mtime-Cache | ~0 MB | ~0 MB |
| Chart-Daten per AJAX | ~1–2 MB | ~5–8 MB |
| **Gesamt** | **~6–12 MB** | **~15–23 MB** |

**Priorität:** SQL-Filterung (30 Min, größter Gewinn). mtime-Cache (30 Min,
CPU-Entlastung). AJAX (2–3 h, optional).

#### 3.13.7 Gesamtaufwand

| Punkt | Aufwand |
|---|---|
| 3.13.1 Alert-Logik | 2–3 h |
| 3.13.2 Chart-Logik | 2–3 h |
| 3.13.3 Unit-Labels | 30 Min |
| 3.13.4 Measurement-Display-Names | 30 Min |
| 3.13.5 Offline-Thresholds | 30 Min |
| 3.13.6 RAM-Optimierung | 1–2 h (SQL + Cache), 2–3 h (AJAX) |
| **Gesamt** | **7–10 h** |

**Status:** Nach 3.8 (Hysterese) und 3.10 (Alert-Tab).

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

0. **3.12.1/3.12.2** (ca. 1h) - Smoke-Test-Routine/Delete-Sicherheit
1. **3.6 Dashboard-Limits** (2–3 h) – visuell, inhaltlich relevant.
2. **3.8 Hysterese** (2–3 h) – verhindert Flackern.
3. **3.10 Alert-Tab-Überarbeitung**
4. **3.13 Gemeinsame Status-Berechnung**
5. **3.11 Admin nach außen öffnen**

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
| Dashboard zeigt keine Limits | Noch nicht gebaut | ⏳ (3.6) |
| Alert-Tab wird lang | Noch nicht umgebaut | ⏳ (3.10) |
| Admin nur LAN-only | Kein Login, keine Auth | ⏳ (3.11) |

---

## 10. Offene Fragen

- Soll `dedup_seconds` angepasst werden? (Aktuell: 3600 s = 1 Stunde.)
- Soll `from_name` in `mail.json` bleiben? (Ja, umgesetzt.)
- Soll `btn-warning` entfernt werden? (Aktuell: behalten für spätere Aktionen.)
- Soll die Statuspage in die bestehende System-Statuspage integriert werden? (Unklar, aufgeschoben.)
