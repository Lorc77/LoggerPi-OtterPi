# Wiedereinstiegsprotokoll – LoggerPi-OtterPi (Stand v1.12.6)

## Fahrplan (Stand v1.12.6)

### Sofort (morgen)

**1. Admin von außen (3.11, simpel) — ~30 min**

- nginx Basic Auth auf `/admin` und `/api/admin/`
- `.htpasswd` mit starkem Passwort
- HTTPS ist schon da
- Später auf Authelia umsteigen, wenn mehr Sicherheit gewünscht

**2. 3.16 Batch-Delivery-Handling — ~1–2 h**

- `DeliveryResult` (SUCCESS/PERMANENT/TRANSIENT)
- Logging
- Dead-Letter-Queue
- Check auf bestehende Dead Batches

### Diese Woche

**3. 3.15 Alert-Archivierung — ~1–2 h**

- `archive_batches.py` um `_archive_alerts()` erweitern
- Nur resolved Alerts älter als 12 Monate
- Gleicher Timer

**4. Healthchecks.io — ~15 min**

- Auf dem OtterPi: Cronjob, der jede Minute `curl https://hc-ping.com/<uuid>` aufruft
- Alarmiert per Mail/Push, wenn der OtterPi ausfällt

**5. NAS-Backup — ~30 min**

- Täglicher `sqlite3 .backup` für `batches.sqlite3` und `alerts.sqlite3`
- Per cron auf NAS kopieren

### Nächste Wochen

**6. 3.13 Gemeinsame Status-Berechnung — ~7–10 h**

- Refactoring
- Behebt „⛔ Invalid"-Chip-Bug
- Reduziert Duplikate

**7. 3.14 Acknowledge-Button im Dashboard — ~1–2 h**

- Button neben Statusleuchte
- Im Admin bleibt nur Resolve

### Irgendwann

**8. 3.8 Hysterese — ~2–3 h**

- Nur bei rauschenden Sensoren

**9. Advanced Updates (5.1–5.7) — ~10–15 h**

- Send-on-change, ntfy self-host, Diagnostics, Events

**10. Verschobene Punkte**

- CSV-Export, Statuspage, Dry-Run, Config-Backup/Restore, Audit-Log, Mobile-Optimierung

### Im Hinterkopf

- **Healthchecks.io** und **NAS-Backup** sind Betrieb, nicht Code — aber wichtig für „echten" Produktionsbetrieb.
- **Monitoring des OtterPi selbst** — Healthchecks.io deckt das ab.



**Empfehlung für morgen:** Admin von außen zuerst (du brauchst es), dann 3.16. Beides zusammen ~2 h.

---

**Projekt:** LoggerPi-OtterPi
**Aktuelle Version:** v1.12.6 (deployed auf OtterPi + LoggerPi)
**Teststand:** 463 passed, Ruff/Format clean
**Stand:** 2026-11-13

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

### v1.12.2 – Alert-Tab-Überarbeitung (Teil 1)

- **Alert-Tab als Tabelle:** Statt Karten. Spalten: Status, Zeit, Severity,
  Regel, Gerät, Aktionen. Gruppiert nach Tagen.
- **Status-Zeile:** `3 active critical · 5 active warning · 12 resolved`.
- **Balkendiagramm:** 14 Tage kumulativ pro Tag, gestapelt.
- **Neue API-Route:** `GET /api/admin/alerts/stats`.
- **Neue Methoden:** `AlertStore.count_by_day()`, `AlertStore.count_by_status()`.

### v1.12.3 – Alert-Tab Polish + klickbare Status-Zeile

- **Englische Header in der Alert-Tabelle:** `Zeit` → `Time`, `Regel` → `Rule`,
  `Gerät` → `Device`, `Aktionen` → `Actions`.
- **Tages-Header mit Wochentag + Datum + Relativangabe:**
  `Monday, 11.11.2026 (today)` / `Sunday, 10.11.2026 (yesterday)` /
  `Saturday, 09.11.2026 (2 days ago)`.
- **Weichere Chart-Farben:** Warning `#fbbf24` (amber-400), Critical
  `#f87171` (red-400), Resolved `#4ade80` (green-400).
- **Kompaktere Chip-Labels im Alarm Limits-Tab:** `↓15°C ↑18°C` statt
  `↓ 15 °C ↑ 18 °C`.
- **Klickbare Status-Zeile:** Klick auf „3 active critical" filtert auf
  `status=active&severity=critical`. Nochmal klicken hebt den Filter auf.
  Aktiver Filter wird visuell hervorgehoben.
- **`AlertStore.list_alerts()` erweitert:** Neue Parameter `severity` und
  `status` (`"active"` / `"resolved"`). `only_active` bleibt als Alias.
- **`GET /api/admin/alerts` erweitert:** Query-Parameter `severity` und
  `status`.

### v1.12.4 – Archiv-Tab

- **Archiv als Sub-Tab innerhalb „Alerts":** Sub-Tab-Buttons
  `[Current] [Archive]` oben im Alerts-Tab. Der bisherige Inhalt wandert
  in `#subtab-current`, der neue Archiv-Inhalt in `#subtab-archive`.
- **Short-Klick-Buttons:** „Last week", „Last month", „Last 3 months".
- **Kalender:** From/To-Datum mit „Apply"-Button.
- **Filter:** Device, Severity, Room, Status (Dropdowns).
- **Pagination:** 50 Alerts pro Seite, „Load more"-Button.
- **Tabelle:** Wiederverwendet `renderAlertRow`, gruppiert nach Tagen
  (ohne „Older active"-Sektion).
- **`AlertStore._build_where()`:** Neue Hilfsmethode, baut die
  WHERE-Klausel aus allen Filtern (wird von `list_alerts` und
  `count_alerts` genutzt).
- **`AlertStore.list_alerts()` erweitert:** Neue Parameter `offset`,
  `since`, `until`, `device_prefixes`.
- **`AlertStore.count_alerts()` neu:** Liefert die Gesamtzahl der
  gefilterten Alerts (für Pagination).
- **`GET /api/admin/alerts` erweitert:** Query-Parameter `offset`,
  `since`, `until`, `devices` (kommasepariert). Response um `total`,
  `offset`, `limit` erweitert.
- **Bugfix `until`-Handling:** `until=YYYY-MM-DD` wird als
  `created_at < (Datum + 1 Tag)` interpretiert, damit Alerts am
  letzten Tag (auch mit Mikrosekunden) eingeschlossen werden.
- **Tests:** `TestBuildWhere` (14), `TestListAlertsFilters` (4),
  `TestCountAlerts` (3), `test_get_alerts_with_since`,
  `test_get_alerts_with_devices`, `test_get_alerts_with_offset`,
  `test_admin_page_contains_archive_tab`. Gesamt: 462 Tests.

### v1.12.5 – Archiv-Sub-Tab Bugfixes

- **Layout:** From/To/Apply in einer Zeile mit den Perioden-Buttons.
- **Refresh-Button entfernt:** Filter-Dropdowns refreshen automatisch
  (`onchange="loadArchive('custom')"`).
- **Room-Dropdown-Bugfix:** Räume mit mehreren Geräten liefern jetzt Alerts.
  Ursache: `encodeURIComponent(f.devices.join(','))` kodierte das Komma zu
  `%2C`, Python splittet aber auf `,`. Fix:
  `f.devices.map(encodeURIComponent).join(',')`.
- **Neue Räume/Geräte:** Erscheinen sofort in den Dropdowns (kein F5 mehr
  nötig). `archiveDropdownsPopulated`-Flag entfernt.
- **Auswahl bleibt erhalten:** `populateArchiveDropdowns` merkt sich die
  aktuelle Auswahl.
- **Datumsbereich bleibt erhalten:** Perioden-Buttons füllen die From/To-Felder,
  damit Filter-Wechsel den Zeitraum nicht verlieren.
- **Room-Dropdown nach vorn:** Reihenfolge jetzt Room → Device → Severity → Status.
- **Device-Dropdown nach Room gefiltert:** Zeigt nur Geräte des gewählten Raums.
  Bei Room = „All" alle Geräte. Verhindert stillen Override.

### v1.12.6 – Alert-Tab-Umbau

- **Current-Tab zeigt nur aktive Alerts:** `only_active=1` fest,
  „Only active"-Checkbox entfernt, `include_older_active` entfernt
  (redundant).
- **Current-Tab nutzt `renderArchiveTable`:** Tagesgruppen für alle aktiven
  Alerts, keine „Older active"-Sektion mehr. `renderAlertTable` gelöscht.
- **Archive-Tab: „Last 3 days"-Button** als erster/Default-Button.
  `getArchiveDateRange('3days')` neu. `showSubTab` lädt `3days` statt `week`.
- **Archive-Tab: „Unacknowledged" im Status-Dropdown.** Filtert auf
  `acknowledged = 0` (unabhängig von Active/Resolved).
  `only_unacknowledged=1` wird gesendet.
- **Chart: Datum als `dd.mm.yyyy`** statt `YYYY-MM-DD`.
- **Aktiver Perioden-Button wird highlighted** (`.btn.active`).
- **„↑ To Top"-Button** in Current und Archive, zentriert, dynamisch
  ausgeblendet bei leerer Tabelle.
- **How-to-Texte** in Current und Archive aktualisiert.

---

## 3. Offene Punkte mit detaillierten Plänen

### 3.8 Hysterese (⏸️ zurückgestellt – „wenn Bedarf")

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

**Status:** ⏸️ Zurückgestellt. Dedup + Autoresolve decken die meisten Fälle
ab. Hysterese kann später ergänzt werden, wenn konkreter Bedarf besteht
(z.B. bei einem rauschenden Sensor).

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

**Bekannter Bug (beim Umbau mitfixen):**

- **Falscher „⛔ Invalid"-Chip bei Limit-Verletzung:**
  - `_device_chips()` fügt den generischen „⛔ Invalid"-Chip hinzu, sobald
    `status == "status-critical"` und keine Alarme vorliegen — unabhängig
    davon, ob die Ursache eine Grenzwertverletzung oder ein ungültiger
    Messwert ist.
  - Bei einem AtmoWEB-Gerät, das z.B. `critical_max` in `humidity`
    überschreitet, erscheinen **beide** Chips: „⛔ Humidity above limit"
    (korrekt) und „⛔ Invalid" (irreführend).
  - **Fix:** In `_device_chips()` tracken, ob bereits ein kritischer
    Limit-Chip hinzugefügt wurde (`limit_critical_added`). Den generischen
    „⛔ Invalid"-Chip nur zeigen, wenn `not limit_critical_added`.
  - **Verwandt:** `_status_text()` mappt `status-critical` pauschal auf
    „INVALID" (Device-Detailseite). Sollte auf „CRITICAL" umgestellt werden,
    oder die Detailseite sollte den konkreten Grund anzeigen.
  - **Test:** `test_dashboard_data.py::test_no_invalid_chip_when_limit_violation`.
  - **Aufwand:** ~15–30 Min (Teil von 3.13.1).

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
| 3.13.1 Alert-Logik | 2–3 h (inkl. Chip-Fix) |
| 3.13.2 Chart-Logik | 2–3 h |
| 3.13.3 Unit-Labels | 30 Min |
| 3.13.4 Measurement-Display-Names | 30 Min |
| 3.13.5 Offline-Thresholds | 30 Min |
| 3.13.6 RAM-Optimierung | 1–2 h (SQL + Cache), 2–3 h (AJAX) |
| **Gesamt** | **7–10 h** |

**Status:** Nach 3.8 (Hysterese) und 3.10 (Alert-Tab).

#### 3.13.8 Aufräumen (verwaister Code/CSS)

**Problem:** Durch die Umbauten (3.10 Alert-Tab, 3.6 Dashboard-Limits) sind
Code und CSS verwaist.

**Verwaiste Python-Funktionen in `dashboard_data.py`:**
- `_latest_batch` – nicht mehr verwendet.
- `_latest_states` – nicht mehr verwendet.
- `_latest_setpoints` – nicht mehr verwendet.
- `_latest_serial` – nicht mehr verwendet.

**Verwaiste CSS-Klassen in `admin.py` (nach 3.10-Umbau):**
- `.alert-card` – Karten-Container (durch Tabelle ersetzt).
- `.alert-header` – Karten-Header.
- `.alert-header strong` – Sensor-Label.
- `.alert-severity` – Severity-Badge (Karte).
- `.alert-severity-critical` – Severity-Badge (critical).
- `.alert-severity-warn` – Severity-Badge (warning).
- `.alert-meta` – Meta-Zeile.
- `.alert-message` – Message-Zeile.

**Vorgehen:**
1. Prüfen, ob die Funktionen/Klassen wirklich nirgends mehr verwendet werden
   (z.B. mit `grep`).
2. Entfernen.
3. Tests laufen lassen (`pytest`).
4. Deployen.

**Aufwand:** Klein (30–60 Min).

**Status:** Nach 3.10 (Alert-Tab) und 3.13.1–3.13.7.

---

### 3.14 Acknowledge-Button im Dashboard

**Problem:** Der Acknowledge-Button ist aktuell nur im Admin verfügbar. Der
Nutzer muss also in den Admin wechseln, um einen Alert zu quittieren. Das ist
umständlich, weil er die Alerts im Dashboard sieht.

**Idee:** Der Acknowledge-Button erscheint im Dashboard direkt neben der
Statusleuchte (Raumseite + Device-Detailseite), wenn ein aktiver Alarm
existiert. Der Button wird grün, wenn jemand ihn gedrückt hat. Im Admin bleibt
nur der Resolve-Button (die „Acknowledged"-Anzeige bleibt sichtbar).

**Ziel:** Der Acknowledge-Button ist dort, wo man ihn braucht (im Dashboard,
wo man die Alerts sieht). Der Admin bleibt für das Resolven zuständig.

#### 3.14.1 Konzept

**Wo:**
- **Raumseite** (Gerätekacheln): Neben der Statusleuchte im `device-header`.
- **Device-Detailseite:** Neben der Statusleuchte im `device-header`.

**Wann sichtbar:**
- Nur wenn ein **aktiver Alarm** für das Gerät existiert (Status `critical`
  oder `warn`).
- Nicht sichtbar, wenn der Status `ok` oder `off` ist.

**Verhalten:**
- **Nicht acknowledged:** Button „✓ Acknowledge" (blau/grau).
- **Acknowledged:** Button wird grün, Text „✓ Acknowledged".
- **Klick:** Ruft `POST /api/dashboard/acknowledge?dedup_key=...` auf.
- **Nach Klick:** Button wird grün, ohne Seiten-Reload (via JavaScript).

**Im Admin:**
- Der Acknowledge-Button wird **entfernt**.
- Der Resolve-Button bleibt.
- Die „Acknowledged"-Anzeige bleibt sichtbar (als Text, nicht als Button).

#### 3.14.2 Sicherheitsproblem

**Das Dashboard ist öffentlich** (`observer.makki.route64.de`). Jeder könnte
den Acknowledge-Button drücken. Das könnte missbraucht werden.

**Optionen:**
- **A:** Button nur für Nutzer im LAN anzeigen (IP-Prüfung). **Nicht möglich**,
  weil der Otter nicht im selben Netz wie einige Nutzer steht.
- **B:** Button mit einem Token schützen (z.B. `?token=...`). Aufwand: mittel.
- **C:** Dashboard authentifizieren (das ist 3.11). Aufwand: groß.
- **D:** Button im Dashboard anzeigen, aber ohne Schutz (Risiko). **Für den
  Anfang akzeptabel**, um das Konzept zu testen.

**Entscheidung:** Option D (ohne Schutz) für den ersten Wurf. Später kann man
auf Option B oder C umsteigen.

#### 3.14.3 Abhängigkeiten

**3.13.1 (Alert-Logik):** Die gemeinsame `status.py` berechnet die
`dedup_key`s. Das Dashboard weiß dann, welche Alerts aktiv sind. Ohne 3.13
müsste das Dashboard die `dedup_key`s selbst berechnen (Duplikation).

**Aufwand:**
- **Mit 3.13:** 1–2 h.
- **Ohne 3.13:** 2–3 h.

#### 3.14.4 Bausteine

1. **API-Route `GET /api/dashboard/alerts`:**
   - Liefert die aktiven Alerts (aus `alerts.sqlite3`) mit Acknowledge-Status.
   - Optional: Filter nach `dedup_key`.
   - ~30 Zeilen.

2. **API-Route `POST /api/dashboard/acknowledge?dedup_key=...`:**
   - Ruft `AlertStore.acknowledge_by_dedup_key(dedup_key)` auf.
   - ~30 Zeilen.

3. **`AlertStore.acknowledge_by_dedup_key(dedup_key)`:**
   - Neue Methode, die den letzten aktiven Alert mit diesem `dedup_key`
     acknowledged.
   - ~10 Zeilen.

4. **Dashboard-Button (Raumseite + Device-Detail):**
   - HTML: `<button class="btn btn-ack" onclick="acknowledgeAlert('...')">✓ Acknowledge</button>`
   - Nur sichtbar, wenn ein aktiver Alarm existiert.
   - ~30 Zeilen.

5. **JavaScript `acknowledgeAlert(dedup_key)`:**
   - Ruft `POST /api/dashboard/acknowledge?dedup_key=...` auf.
   - Ändert den Button-Status (grün, „✓ Acknowledged").
   - ~20 Zeilen.

6. **Admin: Acknowledge-Button entfernen:**
   - In `loadAlerts` den Acknowledge-Button durch die „Acknowledged"-Anzeige
     ersetzen.
   - ~10 Zeilen.

7. **Tests:**
   - `test_alert_store.py`: `acknowledge_by_dedup_key`.
   - `test_admin.py`: API-Routen.
   - ~30 Zeilen.

#### 3.14.5 Offene Fragen

1. **Sicherheit:** Option D (ohne Schutz) für den Anfang. Später Option B
   (Token) oder C (Auth)?
2. **Button-Design:** Blau/grau (nicht acknowledged) → grün (acknowledged).
   Oder andere Farben?
3. **Mehrere Alerts pro Gerät:** Wenn ein Gerät mehrere aktive Alerts hat
   (z.B. `critical_max` und `warning_min`), soll der Button alle auf einmal
   acknowledgen, oder nur den schwerwiegendsten?
4. **Admin:** Soll der Acknowledge-Button komplett entfernt werden, oder als
   „Advanced"-Option bleiben?

#### 3.14.6 Status

**Zurückgestellt** – nach 3.13 (Gemeinsame Logik) und 3.10 (Alert-Tab).

**Aufwand:** 1–2 h (mit 3.13), 2–3 h (ohne 3.13).

---

### 3.15 Alert-Archivierung (geplant, Option B)

**Problem:** `alerts.sqlite3` wächst kontinuierlich. Ohne Archivierung würde
sie unbegrenzt wachsen. `archive_batches.py` archiviert bisher nur Batches.

**Ziel:** `archive_batches.py` um `_archive_alerts()` erweitern (Option B).
Nur **resolved** Alerts (`resolved_at IS NOT NULL`) älter als 12 Monate
werden archiviert. Aktive Alerts bleiben in der Live-DB.

**Format:** JSON Lines + gzip, `loggerpi-otterpi_alerts_YYYY-MM.json.gz`.
Gleicher systemd-Timer (`archive-batches.timer`).

**Begründung:**
- Aktive Alerts müssen in der Live-DB bleiben, damit die Alert-Engine
  `is_acknowledged()` und `is_active()` korrekt prüfen kann.
- Ein gemeinsamer Timer reicht (Option B), kein separater Service.
- Gleiches Format wie Batches (JSON Lines + gzip).

**Aufwand:** ~1–2 h.

**Status:** Proposed (DEC-100). Noch nicht implementiert.

---

### 3.16 Batch-Delivery-Handling

**Problem:** `delivery.py` unterscheidet nicht zwischen permanenten und
transienten Fehlern. Ein 400 (invalid payload) bleibt für immer in der
Queue und blockiert alle nachfolgenden Batches (wegen `break` im
Queue-Replay). Kein Logging, keine Dead-Letter-Queue, kein Backoff.

**Aktueller Code:**

`delivery.py`:
```python
try:
    with urlopen(request, timeout=self.timeout) as response:
        return response.status == 202
except (HTTPError, URLError):
    return False
```

`runtime.py`:
```python
for queued_batch in self.queue.pending():
    if self.delivery.send(queued_batch):
        self.queue.remove(queued_batch)
    else:
        break
```

**Ziel:**

- **4xx** (permanent) von **5xx/Netzwerk** (transient) unterscheiden.
- **Logging** für jeden Fehlschlag (Status, Grund, Batch-ID).
- **Dead-Letter-Queue** für permanente Fehler (manuell inspizierbar).
- **Transiente Fehler** bleiben in der Queue, Reihenfolge erhalten.
- **Backoff** (optional): Retry-Intervall bei wiederholten Fehlern erhöhen.

**HTTP-Codes:**

| Code | Bedeutung | Retry sinnvoll? |
|---|---|---|
| 202 | accepted | – (Erfolg) |
| 400 | invalid payload | ❌ permanent |
| 401 | unauthorized (Token falsch) | ❌ permanent |
| 404 | unknown path (URL falsch) | ❌ permanent |
| 409 | batch conflict | ❌ permanent |
| 415 | unsupported media type | ❌ permanent |
| 408 | request timeout | ✅ transient |
| 429 | too many requests | ✅ transient |
| 500 | server error | ✅ transient |
| 502/503/504 | gateway error | ✅ transient |
| Netzwerk-Timeout | – | ✅ transient |

**Lösungsideen:**

**1. `DeliveryResult` in `delivery.py`:**

```python
class DeliveryResult:
    SUCCESS = "success"  # 202
    PERMANENT = "permanent"  # 4xx (außer 408, 429)
    TRANSIENT = "transient"  # 5xx, Netzwerk, Timeout
```

**2. `send()` gibt `DeliveryResult` zurück:**

```python
def send(self, batch: Batch) -> str:
    try:
        with urlopen(request, timeout=self.timeout) as response:
            if response.status == 202:
                return DeliveryResult.SUCCESS
            LOGGER.warning(
                "Delivery: HTTP %s for batch %s",
                response.status,
                batch.batch_id,
            )
            return DeliveryResult.TRANSIENT
    except HTTPError as exc:
        if 400 <= exc.code < 500 and exc.code not in (408, 429):
            LOGGER.error(
                "Delivery: permanent HTTP %s for batch %s",
                exc.code,
                batch.batch_id,
            )
            return DeliveryResult.PERMANENT
        LOGGER.warning(
            "Delivery: transient HTTP %s for batch %s",
            exc.code,
            batch.batch_id,
        )
        return DeliveryResult.TRANSIENT
    except URLError as exc:
        LOGGER.warning(
            "Delivery: network error for batch %s: %s",
            batch.batch_id,
            exc,
        )
        return DeliveryResult.TRANSIENT
```

**3. `runtime.py` Queue-Replay:**

```python
for queued_batch in self.queue.pending():
    result = self.delivery.send(queued_batch)
    if result == DeliveryResult.SUCCESS:
        self.queue.remove(queued_batch)
    elif result == DeliveryResult.PERMANENT:
        LOGGER.error(
            "Batch %s permanently failed; moving to dead-letter",
            queued_batch.batch_id,
        )
        self.queue.move_to_dead_letter(queued_batch)
    else:
        break  # transient → Reihenfolge erhalten
```

**4. Dead-Letter-Queue in `batch_queue.py`:**

```python
def move_to_dead_letter(self, batch: Batch) -> None:
    dead_letter_path = self.path.parent / "dead_letter.jsonl"
    with dead_letter_path.open("a", encoding="utf-8") as f:
        json.dump(batch.to_dict(), f, ensure_ascii=False)
        f.write("\n")
    self.remove(batch)
```

**5. Logging in `runtime.py`:**

```python
LOGGER.info("Queue replay: %d pending", len(self.queue.pending()))
```

**6. Backoff (optional):**

- Track consecutive failures in `runtime.py`.
- Increase retry interval (15 min → 30 min → 1 h → 2 h).
- Reset on success.

**Check auf bestehende Dead Batches:**

Auf dem LoggerPi:

```bash
# Queue-Datei finden
echo \$LOGGERPI_QUEUE_FILE
# oder
grep LOGGERPI_QUEUE_FILE /etc/loggerpi-otterpi/loggerpi.env

# Queue-Größe
wc -l /var/lib/loggerpi-otterpi/queue.jsonl

# Ältester Batch (erste Zeile)
head -1 /var/lib/loggerpi-otterpi/queue.jsonl | python3 -m json.tool

# Neuester Batch (letzte Zeile)
tail -1 /var/lib/loggerpi-otterpi/queue.jsonl | python3 -m json.tool

# Delivery-Fehler im Log
journalctl -u loggerpi.observer.service -n 200 --no-pager | grep -i "delivery\|error\|fail"
```

**Was prüfen:**

- Ist die Queue leer? → Alles gut.
- Sind Batches drin, die älter als 1 Tag sind? → Möglicherweise permanent
  fehlgeschlagen.
- Gibt es Delivery-Fehler im Log? → Welche HTTP-Codes?

**Tests:**

- `test_delivery.py`: `send()` gibt `SUCCESS` bei 202, `PERMANENT` bei 400,
  `TRANSIENT` bei 500/Netzwerkfehler.
- `test_runtime.py`: Queue-Replay entfernt bei `SUCCESS`, verschiebt in
  Dead-Letter bei `PERMANENT`, bricht ab bei `TRANSIENT`.
- `test_batch_queue.py`: `move_to_dead_letter()` schreibt in
  `dead_letter.jsonl` und entfernt aus der Queue.

**Aufwand:** ~1–2 h inkl. Tests.

**Status:** Proposed. Nächster Schritt nach 3.15 (Alert-Archivierung).

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

### 5.4 Auf „irgendwann" verschoben

| Punkt | Zweck | Status |
|---|---|---|
| **Mobile-Optimierung Alert-Tabelle** | Spalten ausblenden oder auf Karten umstellen (aktuell: horizontal scrollen). | ⏸️ verschoben |

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
- **DEC-098:** Current-Tab zeigt nur aktive Alerts (Tagesgruppen für alle aktiven, keine „Older active"-Sektion mehr).
- **DEC-099:** Archive: „Last 3 days"-Button (Default) + „Unacknowledged" im Status-Dropdown.
- **DEC-100:** Alert-Archivierung (geplant, Option B — Erweiterung von `archive_batches.py`, nur resolved Alerts).

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

**Empfohlene Reihenfolge:**

1. **3.13 Gemeinsame Status-Berechnung** (7–10 h) – Refactoring.
   Inkl. Fix für den falschen „⛔ Invalid"-Chip.
2. **3.14 Acknowledge-Button im Dashboard** (1–2 h, nach 3.13).
3. **3.11 Admin nach außen öffnen** (2–6 h, je nach Level).
4. **3.15 Alert-Archivierung** (1–2 h, Option B).

**Danach (nach Bedarf):**
- Advanced Updates (5.1–5.5, 5.7).
- Verschobene Punkte (CSV-Export, Statuspage, Dry-Run, Config-Backup/Restore, Audit-Log).

---

## 9. Bekannte Lücken / bewusste Entscheidungen

| Lücke | Grund | Status |
|---|---|---|
| Test-Mail nutzt nicht das neue Format | Bewusste Entscheidung, um Aufwand zu sparen | ⏸️ |
| Kein Sweep für verwaiste Alerts | Würde falsch-positive Resolves erzeugen | ⏸️ (manueller Resolve-Button) |
| Hysterese nicht implementiert | Zurückgestellt („wenn Bedarf") | ⏸️ |
| Dashboard zeigt Limits | ✅ Erledigt (v1.12.1) | ✅ |
| Alert-Tab wird lang | ✅ Erledigt (v1.12.6, Current nur aktive) | ✅ |
| Admin nur LAN-only | Kein Login, keine Auth | ⏳ (3.11) |
| Falscher „⛔ Invalid"-Chip bei Limit-Verletzung | `_device_chips()` prüft nicht, ob die Ursache eine Limit-Verletzung ist | ⏳ (3.13.1) |
| Alert-Archivierung fehlt | `alerts.sqlite3` wächst unbegrenzt | ⏳ (3.15) |

---

## 10. Offene Fragen

- Soll `dedup_seconds` angepasst werden? (Aktuell: 3600 s = 1 Stunde.)
- Soll `from_name` in `mail.json` bleiben? (Ja, umgesetzt.)
- Soll `btn-warning` entfernt werden? (Aktuell: behalten für spätere Aktionen.)
- Soll die Statuspage in die bestehende System-Statuspage integriert werden? (Unklar, aufgeschoben.)
- Soll `_status_text()` auf „CRITICAL" umgestellt werden, oder soll die
  Device-Detailseite den konkreten Grund (Limit/Alarm/Invalid) anzeigen?
