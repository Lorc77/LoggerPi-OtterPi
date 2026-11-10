# LoggerPi → OtterPi

## Projektstatus

**Projekt:** LoggerPi → OtterPi  
**Data Model:** v1  
**Projektphase:** Implementierung / Core Batch v1  
**Status:** In aktiver Entwicklung  
**Stand:** 2026-11-08

---

## Deployment-Stand

**Stand:** 2026-11-08

| System | Version | Status |
|--------|---------|--------|
| LoggerPi | `v1.11.19` | Läuft, sendet Batches alle 15 Minuten |
| OtterPi | `v1.11.19` | Empfängt Batches, speichert in SQLite, Admin + Alert-Engine aktiv |

LoggerPi und OtterPi laufen produktiv auf Version `v1.11.19`.

## Phase A – Config-Admin (abgeschlossen, v1.8.0)

Admin (LAN-only): https://observer.makki.route64.de/admin

**Stand:** 2026-11-04

### Umgesetzt

- `dashboard_config.py` → `get_rooms()` mit mtime-Cache, Lock, Fallback auf `_DEFAULT_ROOMS`.
- `dashboard_constants.py`, `dashboard_data.py`, `dashboard_charts.py` aus `dashboard.py` herausgezogen.
- `config_store.py`: JSON-Validierung, `.bak`, atomares Schreiben für `rooms.json`, `alarm_limits.json`, `mail.json`, `notifications.json`.
- `notifier.py`: E-Mail (smtplib), ntfy, Webhook (Discord/Slack/generic), stdlib only.
- `admin.py`: Admin-UI unter `/admin` (JSON-Editor pro Tab).
- `otterpi.py`: Routen `GET /admin`, `GET /api/admin/config`, `PUT /api/admin/*`.
- LAN-only via nginx (`/admin`, `/api/admin/`).

### Teststand

240 Tests, alle grün.

### Nächster Schritt

## Phase B0 – States/Setpoints/Device + Dashboard (abgeschlossen, v1.9.0)

**Stand:** 2026-11-05

### Umgesetzt

- `Batch`: `states`, `operation`, `serial`, `setpoints`, `device`.
- `Measurement`: `validity_reason` (`overflow`/`sensor_error`).
- AtmoWEB: Lights (day/uv bool, led percent), Flap percent, Setpoints, Device-Info.
- Freezer: `serial.state` (disconnected/unknown/connected/degraded), Alarme, USB-IDs.
- MEMMERT: `operation_mode`, Setpoint, Device-Info (address, port, resolution, USB-IDs).
- WeatherHub: `battery_low`, Device-Info (sensor_id, sensor_type, gateway_ip, gateway_timestamp), `validity_reason`.
- Runtime: merged alle Bereiche.
- Dashboard: Status-Chips (erklärend), LED-SVG, Device-Info auf Detailseite; Chips + LED auf Raumdetail-Kacheln; Lampen auf Übersicht.
- Freezer-Anzeigename: „Thermo Scientific HFC · -80 °C".

### Teststand

323 Tests, alle grün.

### Nächster Schritt

Phase B – Alert-Engine (abgeschlossen, v1.10.0).

## Phase B – Alert-Engine (abgeschlossen, v1.10.0)

**Stand:** 2026-11-05

### Umgesetzt

- `alert_store.py`: SQLite-Speicher für Alerts (Tabelle `alerts`, Indizes auf `created_at`, `dedup_key`, `acknowledged`).
- `alert_engine.py`: Thread im `otterpi.observer.service`, prüft nach jedem Batch und alle 300 s.
- `sensor_schemas.py`: Zentrale Schema-Definition pro Sensor-Typ (Measurements + States).
- `alarm_limits.json` um `states`-Sektion erweitert (State-basierte Regeln).
- `Alert`-Dataclass um `rule` und `dedup_key` erweitert.
- `load_alarm_limits()` gibt das ganze Objekt zurück (`sensors` + `states`).
- Admin: Tab „Alerts" (Alert History mit Acknowledge-Button), Test-Mail-Button im Mail-Tab.
- Neue Routen: `GET /api/admin/alerts`, `POST /api/admin/alerts/<id>/acknowledge`, `POST /api/admin/test-mail`.
- Neue Env-Variablen: `OTTERPI_ALERT_DB`, `OTTERPI_ALERT_INTERVAL_SECONDS`, `SMTP_PASSWORD`.
- SMTP-Variablen (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_FROM`) aus `otterpi.env.example` entfernt – bleiben in `mail.json`.

### Teststand

318 Tests, alle grün.

### Nächster Schritt

Deploy + Test (B6). Danach Phase C (Komfort).

## Phase C – Komfort (abgeschlossen, v1.11.0)

**Stand:** 2026-11-07

### Umgesetzt

- **Rooms-Tab:** Formular-UI (Raum-/Geräte-Verwaltung, Raumwechsel per Pull-down, Inline-Formulare für Add/Edit/Delete, How-to für neue WeatherHub-Sensoren).
- **Alarm Limits-Tab:** Formular-UI (Measurements + States pro Gerät, Edit Limits mit Inline-Formular, How-to).
- **Mail-Tab:** Formular-UI (SMTP, Empfänger, Routing, Dedup, Quiet Hours, Enabled, Test-Mail-Button).
- **Notifications-Tab:** Formular-UI (ntfy, webhook, Add/Edit/Delete Channel).
- **Rate-of-Change:** `rate_of_change_max_per_hour` in `alert_engine.py` implementiert (nutzt `BatchStore.recent()`).
- **Routing:** `EmailNotifier` nutzt `routing[severity]` statt `recipients`.
- **`contact_open`:** In `alert_engine.py` `_check_states` ergänzt (für zukünftige `weatherhub_id10`-Sensoren).
- **JSON-Editor als „Advanced"-Toggle:** In allen Tabs (Rooms, Alarm Limits, Mail, Notifications).

### Bewusst nicht umgesetzt

- **Door-Open-Dauer:** HPP260 unterstützt `door_open` nicht (liefert `N/A`). Geparkt für evtl. zukünftige AtmoWEB-Geräte.
- **Service-Restart:** Nicht nötig, weil JSON-Configs automatisch gelesen werden (mtime-Cache, `load_*()` bei jedem `_check`).

### Auf „irgendwann" verschoben

- CSV-Export
- Statuspage
- Dry-Run / Test-Mode
- Config-Backup/Restore

### Auf „später" verschoben (wenn Admin öffentlich mit Login)

- Audit-Log

### Teststand

356 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.11). Danach: Acknowledge-Verhalten (3.3), Resolve (3.8),
Message-Templates (3.4), UI-Umbau Alarm Limits (3.2), Dashboard-Limits (3.6),
Rate-of-Change im Admin (3.7).

## Phase C – Offline-Erkennung (abgeschlossen, v1.11.11)

**Stand:** 2026-11-08

### Umgesetzt

- **`received_at` in der Batch-Tabelle:** OtterPi-seitiger Empfangszeitpunkt
  wird jetzt persistiert (`BatchStore.latest_received_at()`). Fallback auf
  `created_at` für bestehende Zeilen ohne `received_at`.
- **`heartbeat.py`:** Gemeinsame Offline-Status-Logik für Admin und Dashboard
  (`offline_status()`).
- **`alarm_limits.json` → `system`-Sektion:** Konfigurierbare Schwellenwerte
  (`loggerpi_offline_warning_seconds`, `loggerpi_offline_critical_seconds`)
  und optionale Warnstufe (`loggerpi_offline_warning_alert_enabled`).
- **Alert-Engine:** `_check_loggerpi_heartbeat()` prüft den Heartbeat vor den
  Sensor-/State-Checks. Bei Offline werden Sensor-/State-Checks ausgesetzt
  (Suppression). Der Offline-Alert hat einen eigenen `dedup_key`
  (`system:loggerpi_offline:critical` bzw. `...:warning`).
- **Admin:** Statusleuchte im Header, System-Karte im Alarm Limits-Tab
  (Schwellenwerte in Minuten, Checkbox für Warn-Alert).
- **Dashboard:** Statusleuchte im Header, „Last measurement" statt „Last update".
- **`deploy/otterpi/install.sh`:** `heartbeat.py` in der Dateiliste.

### Teststand

356 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.11). Danach: Acknowledge-Verhalten (3.3), Resolve (3.8),
Message-Templates (3.4), UI-Umbau Alarm Limits (3.2), Dashboard-Limits (3.6),
Rate-of-Change im Admin (3.7).

## Phase C – Acknowledge + Resolve (abgeschlossen, v1.11.12)

**Stand:** 2026-11-08

### Umgesetzt

- **Acknowledge-Verhalten:** Ein acknowledged Alert wird nicht erneut
  gesendet, solange der Zustand kritisch bleibt. `AlertStore.is_acknowledged()`
  prüft den letzten Alert mit demselben `dedup_key`. `_dispatch()` überspringt
  acknowledged Alerts.
- **Reset bei Normalisierung:** Sobald der Wert wieder innerhalb der Grenzen
  ist (bzw. der State wieder normal ist), ruft die Alert-Engine
  `reset_acknowledged()` auf. Der Alert wird für die Zukunft „entsperrt".
- **Alert-Resolve:** Neue Spalte `resolved_at` in `alerts.sqlite3`.
  `AlertStore.resolve()` setzt `resolved_at` für **alle offenen** Alerts mit
  demselben `dedup_key` (Variante 2). `AlertStore.is_active()` prüft, ob der
  letzte Alert noch nicht resolved ist.
- **Bugfix:** `reset_acknowledged()` und `resolve()` werden nur aufgerufen,
  wenn der Wert tatsächlich wieder innerhalb der Grenzen ist – nicht schon
  bei `validity == "valid"`. Das verhindert, dass ein acknowledged Alert
  resettet wird, obwohl der Zustand noch kritisch ist.
- **Admin:** Alerts-Tab mit Status-Chip („Active" / „Resolved"), Filter
  „Only active", `resolved_at` im JSON.
- **`otterpi.py`:** Query-Parameter `only_active` für `/api/admin/alerts`.

### Teststand

375 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.12). Danach: Message-Templates (3.4), UI-Umbau
Alarm Limits (3.2), Dashboard-Limits (3.6), Rate-of-Change im Admin (3.7).

## Phase C – Message-Templates (abgeschlossen, v1.11.13)

**Stand:** 2026-11-08

### Umgesetzt

- **`messages.json`:** Neue Config-Datei mit globalen Regel-Texten
  („too high", „too low", „invalid", „stale", „low", „open", „alarm",
  „offline"). Defaults werden verwendet, wenn die Datei fehlt.
- **`MEASUREMENT_DISPLAY_NAMES`:** Festes Mapping von Measurement-Key zu
  Anzeigename („Temperature", „Humidity", „Vacuum", „CO₂", „Battery", „Door").
- **Alert-Engine:** `_build_message()` und `_build_subject()` bauen die Texte
  aus Raum, Gerät, Measurement-Name und Regel-Text. Raum/Gerät kommen aus
  `rooms.json` (Fallback auf technischen `sensor_key`).
- **`Alert`-Dataclass:** Neues Feld `subject`. `EmailNotifier` und
  `NtfyNotifier` nutzen es mit Fallback auf den bisherigen Subject.
- **Admin:** Neuer Messages-Tab mit Formular-UI (gruppiert in Measurements,
  States, System), JSON-Editor als „Advanced"-Toggle.
- **`otterpi.py`:** `GET /api/admin/messages`, `PUT /api/admin/messages`.

### Teststand

395 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.13). Danach: UI-Umbau Alarm Limits (3.2),
Dashboard-Limits (3.6), Rate-of-Change im Admin (3.7).

## Phase C – Resolve-Button + UI-Polish (abgeschlossen, v1.11.14)

**Stand:** 2026-11-08

### Umgesetzt

- **Resolve-Button im Admin-Alerts-Tab:** Manuelles Resolven eines Alerts
  (per ID). `AlertStore.resolve_by_id()`, `POST /api/admin/alerts/<id>/resolve`.
- **Alert-Tab als Default:** Der Alerts-Tab ist jetzt der erste Tab und wird
  beim Öffnen des Admins geladen (statt Rooms).
- **Toast-Notification:** Alle Save-/Delete-/Acknowledge-/Resolve-Aktionen
  zeigen eine kurze Toast-Benachrichtigung (grün für Erfolg, rot für Fehler).
- **Bugfixes:**
  - Stale-/Invalid-Alerts werden resolved, wenn der Sensor wieder `valid` ist.
  - `is_acknowledged()` prüft nur aktive (nicht resolved) Alerts. Ein
    resolveder Alert blockiert keinen neuen Alert mehr.
  - `reset_acknowledged()` wird nicht mehr beim Resolve aufgerufen. Ein
    resolveder Alert bleibt acknowledged.

### Teststand

399 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.14). Danach: UI-Umbau Alarm Limits (3.2),
Dashboard-Limits (3.6), Rate-of-Change im Admin (3.7).

## Phase C – Severity-Auswahl + Rate-of-Change (abgeschlossen, v1.11.15)

**Stand:** 2026-11-09

### Umgesetzt

- **Severity-Auswahl pro Kanal:** `notifications.json` → `severities` pro
  Channel (Liste von `critical`/`warning`). `NtfyNotifier` und
  `WebhookNotifier` prüfen die Severity, bevor sie senden. Admin-UI:
  Checkboxen im Notifications-Tab.
- **Rate-of-Change im Admin:** `rate_of_change_max_per_hour` im
  „Edit Limits"-Formular pro Measurement. Spalte „Rate/h".
- **Message-Text bei stale/invalid:** Measurement-Key in Klammern, damit
  `temperature_1` und `temperature_2` unterscheidbar sind.
- **Resolve-Zeitstempel im Alert-Tab:** „✓ Resolved (9.11.2026, 10:15:30)".
- **ntfy-Logging:** `_dispatch` loggt, wenn ein Notifier `False` zurückgibt
  (Diagnose für fehlgeschlagene ntfy-Zustellungen).

### Teststand

406 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.15). Danach: Dashboard-Limits (3.6), UI-Umbau
Alarm Limits (3.2), Hysterese (3.8).

## Phase C – Alarm Limits UI-Umbau (abgeschlossen, v1.11.16)

**Stand:** 2026-11-09

### Umgesetzt

- **Alarm Limits-Tab:** Raum-Kacheln mit Geräte-Kacheln. Jede Geräte-Kachel
  zeigt den Gerätenamen, die Metadaten (Key, Type) und die Measurements/States
  als Liste mit farbigen Chips:
  - `[Enabled]` (grün) / `[Disabled]` (grau)
  - `[Warning 20–26 °C]` (gelb)
  - `[Critical 18–28 °C]` (rot)
  - `[Rate 2.0/h]` (blau)
  - `[not configured]` (grau)
- **Severity-Checkboxen im Notifications-Tab:** Bessere Darstellung
  (Flex-Layout, horizontal, klickbare Labels).
- **States-Tabelle im Edit-Limits-Formular:** Linksbündig, `width: auto`,
  damit die Checkbox direkt nach dem State-Namen steht.
- **ntfy ASCII-safe Title:** `NtfyNotifier` ersetzt Nicht-ASCII-Zeichen im
  `Title`-Header durch ASCII-Äquivalente (`·` → `-`, `—` → `-`, `ä` → `ae`,
  etc.). Behebt `UnicodeEncodeError` bei Sonderzeichen im Subject.

### Teststand

406 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.16). Danach: Dashboard-Limits (3.6), Hysterese (3.8).

## Phase C – Alarm Limits Polish (abgeschlossen, v1.11.17)

**Stand:** 2026-11-09

### Umgesetzt

- **Letzte Messwerte im Alarm Limits-Tab:** Jede Measurement-Zeile zeigt den
  aktuellen Wert (blau, auf eine Nachkommastelle gerundet). Neue Route
  `GET /api/admin/latest-measurements`.
- **„Show all"-Filter:** Checkbox unten im Alarm Limits-Tab. Standard: aus
  (nur aktive Felder). Wenn an: alle Schema-Felder.
- **Stale/Invalid-Alerts pro Gerät:** Neue Sektion `device` in
  `alarm_limits.json` mit `stale_enabled` / `invalid_enabled` pro Gerät.
  Ein Alert pro Gerät, nicht pro Measurement. Behebt doppelte Mails bei
  Sensoren mit mehreren Messkanälen.
- **Nicht-Alarm-Trigger-States entfernt:** `door_locked`, `defrost`, `flap`,
  `lights.day`, `lights.uv`, `lights.led`, `switches.a-d` aus
  `sensor_schemas.py` entfernt (sie lösen keine Alarme aus, bleiben aber im
  Dashboard sichtbar).
- **`operation_mode` entfernt:** Aus `sensor_schemas.py` für `memmert`
  entfernt (kein Alarm-Trigger).
- **Nested State Keys Fix:** Regex in `config_store.py` erlaubt jetzt
  mehrere Punkte (`atmoweb_101.switches.a`, `atmoweb_101.lights.uv`).
- **Chip-Texte gekürzt:** „Warn", „Crit", „not conf." statt „Warning",
  „Critical", „not configured".
- **Einheiten:** „celsius" → „°C", „percent" → „%".

### Teststand

428 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.17). Danach: Dashboard-Limits (3.6), Hysterese (3.8).

## Phase C – Alert-Message + Chip-Polish (abgeschlossen, v1.11.18)

**Stand:** 2026-11-09

### Umgesetzt

- **Alert-Messages:** Werte auf 1 Nachkommastelle gerundet. Einheiten
  umgewandelt (`celsius` → `°C`, `percent` → `%`).
- **Chip-Texte:** Pfeile für Min/Max (`Warn ↓ 20 °C · ↑ 23 °C`,
  `Crit ↓ 18 °C · ↑ 28 °C`, `Rate ↕ 1 °C/h`). Nicht konfigurierte Chips:
  `Warn n/c`, `Crit n/c`, `Rate n/c`.
- **`resolve`-Fix:** Alert bleibt aktiv, wenn mindestens ein Channel
  `invalid`/`stale` ist. `resolve` wird nur aufgerufen, wenn alle Channels
  `valid` sind.
- **`UNIT_LABELS`/`unitLabel` in `admin.py`:** Einheiten in Chips und
  Messwerten umgewandelt.
- **`max-content` für State-Chips:** Chip nimmt nur so viel Platz wie nötig.
- **„not applicable" für leere States:** Statt leerer Sektion.
- **Doppelte `.device-row`-Definition bereinigt.**

### Teststand

430 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.18). Danach: Dashboard-Limits (3.6), Hysterese (3.8).

---

## Phase C – How-to-Texte + Delete-Sicherheit (abgeschlossen, v1.11.19)

**Stand:** 2026-11-10

### Umgesetzt

- **How-to-Texte in allen Tabs:**
  - Rooms: WeatherHub-Sensor anlegen (Name, Key, Type, Raum).
  - Alarm Limits: Warning/Critical, Rate-of-Change, Stale/Invalid, Show all,
    Acknowledge/Resolve.
  - Mail: Recipients, Routing, Quiet Hours, Dedup.
  - Notifications: ntfy, Webhook (Discord/Slack/generic), Severities.
  - Messages: Regel-Texte, Measurement-Name.
  - Alerts: Lampe, Status, Acknowledge, Resolve, Filter.
- **Delete-Sicherheit:**
  - Doppelte Delete-Abfrage bei Räumen und Sensoren.
  - `deleteRoom` verweigert, wenn Sensoren im Raum sind.
  - `deleteDevice` löscht Limits mit (`sensors`, `states`, `device`).
  - Alerts bleiben (Option A, History).

### Teststand

432 Tests, alle grün.

### Nächster Schritt

Deploy + Test (v1.11.19). Danach: Dashboard-Limits (3.6), Hysterese (3.8),
Alert-Tab-Überarbeitung (3.10), Admin nach außen (3.11).

---

Seit `v1.6.3` sind folgende Features implementiert:

- **Stale-Logik für WeatherHub-Sensoren:** Konfigurierbar über
  `WEATHERHUB_STALE_AFTER_SECONDS` (Default: 1800 Sekunden). Sensoren,
  die länger als der Schwellenwert keine Daten senden, werden als
  `stale` markiert und im Dashboard als Warnung angezeigt.
- **Gerätedetailseite:** Jede Gerätekachel auf der Raumdetailseite
  verlinkt auf eine eigene Detailseite mit erweitertem Chart
  (24h, 7d, 14d, 30d, 90d, 365d), Sensor-Informationen und Statistik.
- **Raumklima-Detailseite:** Die Raumklima-Anzeige auf der
  Raumdetailseite ist klickbar und führt zu einer Detailseite mit
  Mittelwert-Charts und Einzelsensor-Diagrammen.
- **URL-Umbenennung:** `/raum/rXY` → `/room/rXY` (mit 301-Redirect).
- **Batch-Archivierung:** Monatlicher Export von Batches älter als
  12 Monate als `loggerpi-otterpi_batches_YYYY-MM.json.gz` nach
  `/var/lib/loggerpi-otterpi/archive/`. Automatisch per systemd-Timer.

Seit `v1.5.0` sind die WeatherHub-Sensoren über den Gateway-Proxy
integriert. Das Gateway `.121` wurde in den Proxymodus versetzt und
sendet seine Daten direkt an den LoggerPi (Port 3778). Der
WeatherHub-Listener empfängt die Daten kontinuierlich, der Reader
sammelt die neuesten Werte, und beim nächsten Batch-Zyklus (alle
15 Minuten) werden die Measurements an den OtterPi übertragen.

Aktuell werden **17 Sensoren** empfangen:
- 15 × ID01 (Temperatursensoren mit 2 Kanälen)
- 1 × ID03 (Temperatur + Feuchte)
- 1 × ID0E (Temperatur + Feuchte, dezimal)

Der komplette Datenpfad ist praktisch verifiziert (Stand 2026-10-26):
WeatherHub-Sensoren → Gateway .121 (Proxy) → LoggerPi-Listener →
WeatherHubDecoder → WeatherHubReader → Core Batch → OtterPi → SQLite.

Seit `v1.3.0` ist der Freezer direkt über die Seriell-Schnittstelle
(FTDI FT232R A9NX8YRE) angebunden – ohne den bisherigen Umweg über
`minicom` und `freezer.log`. Die ThingSpeak-Injektion (semi-redundant)
überträgt ausgewählte Werte im Legacy-Format (field1–field7).

Seit `v1.4.0` sind die beiden MEMMERT IPP300 über ihre seriellen
Schnittstellen angebunden (`memmert_ipp300_links`/`rechts`).
`measured_at` wird seit v1.4.0 einheitlich auf die LoggerPi-
Empfangszeit (UTC) gesetzt (DEC-032).

Seit `v1.4.1` zeigt das Dashboard MEMMERT-Kacheln in R1304 sowie
ein Datum (heute/gestern/xx.xx.xxxx) im Chart-Tooltip.

Das Dashboard zeigt seit `v1.3.1` eine Freezer-Kachel in R1304
(inkl. DryAger-Platzhalter) und seit `v1.3.3` korrekte
Zeitstempel-Konvertierung (UTC→Berlin nur bei UTC-Zeitstempeln).

Seit `v1.1.0` ist die Übertragung durch Bearer-Token-Authentication
geschützt. Seit `v1.2.0` stellt der OtterPi ein Dashboard unter `https://observer.makki.route64.de` und eine Einstiegsseite unter `https://zoology.makki.route64.de` bereit. Seit `v1.2.3` ist das
Dashboard raum-basiert (Übersicht + Detailseiten).

Der zentrale Deployment-Wrapper befindet sich unter:

```text
deploy/update.sh
```

Der Wrapper unterstützt zwei Rollen:

```text
loggerpi
otterpi
```

Auf beiden Zielsystemen wird der Wrapper durch das jeweilige
Installationsskript nach:

```text
/usr/local/sbin/loggerpi-otterpi-update
```

installiert.

Die Skripte `deploy/loggerpi/install.sh` und `deploy/otterpi/install.sh` sind
im Repository als ausführbar markiert (`git update-index --chmod=+x`), damit
`update.sh` sie nach dem `git clone` direkt ausführen kann.

### LoggerPi

Der LoggerPi verwendet:

```text
loggerpi.observer.service
```

und das Deployment erfolgt mit:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update loggerpi
```

### OtterPi

Der OtterPi verwendet:

```text
otterpi.observer.service
```

und das Deployment erfolgt mit:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update otterpi
```

### Deployment-Ablauf

Der Wrapper führt grundsätzlich folgenden Ablauf aus:

```text
GitHub main
    ↓
git clone --depth 1
    ↓
Commit bestimmen
    ↓
chmod +x für install.sh-Dateien
    ↓
rollenabhängiges install.sh
    ↓
systemd daemon-reload / enable
    ↓
Service restart
    ↓
Service-Status prüfen
    ↓
DEPLOYED_COMMIT schreiben
    ↓
DEPLOYED_VERSION schreiben
```

Auf dem Zielsystem werden nach erfolgreichem Deployment folgende Dateien geschrieben:

```text
/opt/loggerpi-otterpi/DEPLOYED_COMMIT    technischer Git-Commit
/opt/loggerpi-otterpi/DEPLOYED_VERSION   menschenlesbare Version (z. B. v1.0.0)
```

Zusätzlich schreibt `install.sh` bereits während der Installation:

```text
/opt/loggerpi-otterpi/VERSION            Version aus pyproject.toml (z. B. 1.0.0)
```

Damit kann auf dem Zielsystem jederzeit nachvollzogen werden,
welcher Repository-Commit zuletzt über den Deployment-Mechanismus
ausgerollt wurde.

### Versionierung und Deployment-Metadaten

Seit `v1.0.0` wird die Version über mehrere Dateien geführt:

| Datei | Inhalt | Herkunft | Geschrieben von |
|-------|--------|----------|-----------------|
| `/opt/loggerpi-otterpi/VERSION` | `1.0.0` | `pyproject.toml` | `install.sh` |
| `/opt/loggerpi-otterpi/DEPLOYED_VERSION` | `v1.0.0` | Git-Tag | `update.sh` |
| `/opt/loggerpi-otterpi/DEPLOYED_COMMIT` | `fa92271...` | Git-Commit | `update.sh` |

Die `DEPLOYED_*`-Dateien werden **nur bei erfolgreichem Update** geschrieben
(Fail-safe-Design). Schlägt der Service-Neustart fehl, bleibt die bisherige
Deployment-Version bestehen, damit auf dem Zielsystem sofort erkennbar ist,
welche Version tatsächlich läuft.

Die Versionskennung `v1.0.0` entstammt dem Git-Tag und wird über
`git describe --tags --exact-match` ermittelt. Fehlt ein Tag, wird `dev`
als Fallback verwendet.

### Wichtige Einschränkung

Der aktuelle Deployment-Mechanismus aktualisiert ausschließlich die
Anwendung und die zugehörigen systemd-Service-Dateien.

Er konfiguriert derzeit **nicht** automatisch:

- nginx
- TLS-Zertifikate
- nginx-Reverse-Proxy-Regeln
- DNS
- Firewall
- FRITZ!Box-/IPv6-Freigaben
- externe Routing-/CDN-/Tunnel-Konfiguration

Diese Infrastruktur bleibt bis zu einer ausdrücklich implementierten
Deployment-Erweiterung ein separater administrativer Schritt.

### Flache Deploy-Struktur und PYTHONPATH

Die Installation kopiert die Anwendungsdateien **flach** nach
`/opt/loggerpi-otterpi/`:

```text
/opt/loggerpi-otterpi/
├── atmoweb.py
├── atmoweb_config.py
├── batch_factory.py
├── batch_queue.py
├── composer.py
├── delivery.py
├── loggerpi_observer.py
├── loggerpi_runner.py
├── otterpi.py
├── otterpi_observer.py
├── otterpi_store.py
├── runtime.py
├── system_info.py
└── model/
    ├── batch.py
    └── measurement.py
```

Da `model/` ein Unterverzeichnis ist und kein Python-Package-Setup
(`pip install -e .`) verwendet wird, muss `PYTHONPATH` explizit gesetzt
werden:

```bash
PYTHONPATH=/opt/loggerpi-otterpi:/opt/loggerpi-otterpi/model
```

Dies wird in den Service-Dateien und den `.env`-Dateien konfiguriert:

- `deploy/loggerpi/loggerpi.observer.service`
- `deploy/otterpi/otterpi.observer.service`
- `deploy/loggerpi/loggerpi.env.example`
- `deploy/otterpi/otterpi.env.example`

Hinweis: Die Anwendung läuft ohne `pip install`, ohne Virtualenv und ohne
Package-Import. Die flache Struktur bleibt bewusst als Deployment-Ansatz
erhalten.

---

## Projektziel

Der LoggerPi erfasst System-, Sensor- und Gerätedaten und überträgt diese an den OtterPi.

Die Kommunikation erfolgt grundsätzlich als Push:

```text
LoggerPi → OtterPi
```

Der OtterPi darf nicht voraussetzen, dass er einen LoggerPi aktiv erreichen kann. LoggerPis können beispielsweise in Netzen betrieben werden, in denen eingehende Verbindungen nicht möglich oder nicht erwünscht sind.

Das Data Model soll ausreichend Informationen für

- Dashboard
- Diagnose
- Betrieb
- Health-Bewertung
- Events und Alerts
- spätere Erweiterungen

bereitstellen, ohne unnötige Daten oder vollständige Systemdumps zu übertragen.

Grundprinzip:

> So schlank wie möglich, aber sinnvoll wie nötig.

---

## Architektur

Der grundsätzliche Datenfluss ist:

```text
Quelle / Hersteller-API
        ↓
Adapter / Reader
        ↓
gemeinsames Data Model
        ↓
Core Batch
        ↓
OtterPi
        ↓
Validierung / Health / Events / Dashboard
```

Herstellerspezifische Feldnamen werden nicht direkt zu universellen Data-Model-Feldern.

Neue Sensoren und Datenquellen sollen über Adapter in das gemeinsame Modell integriert werden können.

Der LoggerPi liefert technische Fakten.

Der OtterPi bewertet deren fachliche Bedeutung, Health und Zustand.

---

## Aktueller Entwicklungsstand

### Abgeschlossen

- Data Model v1 Feldkatalog
- Einheitenkatalog v1
- Batch Envelope
- `schema_version`
- `batch_id`
- `logger_id`
- persistente, pro LoggerPi monotone `sequence`
- Trennung von `created_at`, `measured_at` und `received_at`
- Systemdatenmodell
- CPU-, Memory-, Swap- und Storage-Modell
- Netzwerkinterface-Modell
- `blocked` für Netzwerkinterfaces
- aggregierte Prozessanzahl
- Serial-/Freezer-Modell
- AtmoWEB-Mapping-Konzept
- Trennung von Measurements / States / Metadata / Configuration / Health / Events
- Push-Konzept für Metadata-Synchronisation
- keine `measurements.misc`
- keine `states.misc`
- Legacy-`observer.py` wurde im Repository unter `docs/legacy/` dokumentiert
- aktueller Legacy-`observer.py` wurde zusätzlich als Referenz im Repository hinterlegt
- reale LoggerPi-Runtime-/Service-Inventur wurde durchgeführt
- Legacy-Freezer-Logging aus XDG/LXDE-Terminal-Autostart auf einen stabilen `systemd --user`-Service umgestellt
- Freezer-Logger nach Reboot erfolgreich automatisch gestartet und praktisch verifiziert
- WeatherHub Gateway Proxy Integration (v1.5.0)
- WeatherHub Gateway Decoder (ID01, ID02, ID03, ID04, ID07, ID0E, ID10)
- WeatherHub Gateway Listener (TCP, IP-Allowlist, Cloud-Forward optional)
- WeatherHub Reader/Adapter (Measurement-Erzeugung)
- Runtime-Integration (Thread-Start/Stop, Batch-Integration)
- Praktische Verifikation mit Gateway .121 (17 Sensoren empfangen)

### Aktueller Betriebsstand (2026-10-28)

| Komponente | Status |
|-----------|--------|
| LoggerPi-OtterPi | v1.6.0 |
| WeatherHub Gateway .121 | ✅ Proxy-Modus aktiv (→ LoggerPi:3778) |
| WeatherHub Gateway .132 | ✅ Unverändert (Cloud-Modus) |
| WeatherHub Sensoren | ✅ 17 Sensoren empfangen |
| WeatherHub Measurements im Batch | ✅ 34 Measurements (ID01, ID03, ID0E) |
| Dashboard | ✅ WeatherHub-Sensoren in Räumen zugeordnet |
| Dashboard | ✅ Raumklima (Temperatur + Feuchte) berechnet |
| Dashboard | ✅ Englische UI-Texte |
| Batch | ✅ AtmoWEB: Nur Measurements mit Wert im Batch |
| Tests | ✅ 240 Tests bestanden |
| Stale-Logik WeatherHub | ✅ Implementiert (WEATHERHUB_STALE_AFTER_SECONDS) |
| Gerätedetailseite | ✅ Implementiert (/device/<sensor_id>) |
| Raumklima-Detailseite | ✅ Implementiert (/climate/<room_id>) |
| URL-Umbenennung | ✅ /room/ mit 301-Redirect von /raum/ |
| Batch-Archivierung | ✅ Implementiert (monatlich, 12 Monate Retention) |

### Aktueller Arbeitspunkt

Die funktionale Bewertung der relevanten LoggerPi-Services wurde durchgeführt
und in den Core-Batch-Entwurf übernommen.

Der daraus abgeleitete Core Batch v1 ist unter

```text
docs/data-model/core-batch-v1.md
```

dokumentiert und committed.

Damit ist die fachliche Ableitung

```text
Data Model v1
    ↓
reale LoggerPi-Runtime
    ↓
relevante Services
    ↓
Core Batch v1
```

abgeschlossen.

Die fachliche Ableitung des Core Batch v1 sowie dessen JSON-Repräsentation
und der technische API-/Delivery-Stand sind dokumentiert und committed.

Die Planungs- und Spezifikationsphase für den ersten
Core-Batch-v1-Implementierungsschnitt ist damit abgeschlossen.

Die noch offenen Bereiche Metadata Change, Events,
`connectivity.upload` und `connectivity.queue` sind bewusst nicht Teil
dieses Implementierungsschnitts und blockieren dessen Umsetzung nicht.

---

## Batch Envelope

Ein Batch verwendet grundsätzlich:

```text
schema_version
batch_id
logger_id
created_at
sequence
```

`sequence` ist pro LoggerPi persistent und monoton fortlaufend.

`sequence` wird beim Erzeugen des Batches vergeben, bevor der Batch in die persistente lokale Queue gelangt.

Ein Retry verändert weder `batch_id` noch `sequence`.

Die dauerhafte Zustell- und Retry-Logik basiert auf:

* persistenter Queue
* `batch_id`
* unveränderter `sequence`
* Idempotenz
* erfolgreicher Annahme durch den OtterPi im Push-Verfahren

Der LoggerPi kann keine nachgelagerte Zustellbestätigung vom OtterPi
voraussetzen.

Der OtterPi initiiert keine Verbindung zum LoggerPi.

Eine technische HTTP-Response auf einen vom LoggerPi initiierten Request
ist Teil des jeweiligen Transportprotokolls und wird nicht als separates
ACK-Synchronisationsprotokoll modelliert.

---

## Zeitmodell

### `created_at`

Zeitpunkt der Batch-Erzeugung auf dem LoggerPi.

### `measured_at`

Zeitpunkt der tatsächlichen Messwerterfassung.

### `received_at`

Zeitpunkt des Empfangs auf dem OtterPi.

Diese Zeitbegriffe werden nicht miteinander vermischt.

`received_at` ist ausschließlich ein OtterPi-seitiger Wert.

---

## Queue und Retry

Bereits erzeugte Batches müssen bis zur erfolgreichen technischen
Zustellung bzw. Annahme durch den OtterPi in einer persistenten lokalen
Queue verbleiben.

Ein Verbindungsabbruch darf nicht dazu führen, dass ein bereits erzeugter
Batch verloren geht.

Ein Retry erzeugt keinen neuen fachlichen Batch:

    gleicher `batch_id`
    gleiche `sequence`
    neuer Zustellversuch

Der LoggerPi kann keine aktive Rückverbindung bzw. nachgelagerte
Zustellbestätigung durch den OtterPi voraussetzen.

Die Kommunikation erfolgt grundsätzlich als Push:

    LoggerPi
        │
        │ Request
        ▼
    OtterPi

Der OtterPi muss den LoggerPi nicht aktiv erreichen können.

Eine erfolgreiche technische Antwort auf einen vom LoggerPi initiierten
Request kann zur Feststellung einer erfolgreichen Zustellung dieses
Requests verwendet werden.

Ein separates ACK-Synchronisationsprotokoll zwischen LoggerPi und OtterPi
ist nicht Bestandteil des Kommunikationsmodells.

Duplicate Handling muss deshalb auf Empfängerseite anhand der stabilen
Batch-Identität erfolgen, insbesondere über `batch_id` und die persistente
`sequence`.

Die konkrete technische Ausgestaltung von Queue, Retry und Duplicate
Handling wird im API-/Delivery-Design spezifiziert.

---

## Aktuelles Duplicate Handling auf dem OtterPi

Der `BatchStore` verwendet die Batch-Identität für die serverseitige
Idempotenz.

Bei einem bereits vorhandenen `batch_id` gilt:

```text
gleiche batch_id
        +
identischer Payload
        ↓
duplicate
        ↓
HTTP 202
```

Ein gleicher `batch_id` mit verändertem Inhalt wird dagegen als Konflikt
behandelt:

```text
gleiche batch_id
        +
unterschiedlicher Payload
        ↓
conflict
        ↓
HTTP 409
```

Zusätzlich wird verhindert, dass derselbe LoggerPi dieselbe `sequence`
mit einer anderen Batch-Identität verwendet.

```text
logger_id + sequence
        ↓
bereits vorhanden
        +
andere batch_id
        ↓
conflict
```

Damit ist die serverseitige Annahme eines wiederholt zugestellten Batches
bereits idempotent implementiert.

Die weitergehende fachliche Behandlung von verlorenen Responses,
Retry-Backoff und dauerhaft nicht erreichbarem OtterPi bleibt Bestandteil
des LoggerPi-seitigen Delivery-Designs.

---

## Core System

Der bisher definierte Systembereich umfasst unter anderem:

```text
system
├── identity
├── time
├── boot
├── cpu
├── memory
├── swap
├── storage
├── network
├── connectivity
├── processes
├── services
├── autostart
└── timers
```

Dabei werden laufende Telemetriedaten von statischen Metadata getrennt.

Der reguläre Core Batch soll lean bleiben.

Statische Informationen sollen nicht unnötig in jedem Batch wiederholt werden.

Prozesslisten sind nicht Bestandteil des regulären Core Batches. Eine aggregierte Prozessanzahl kann dagegen Teil des Systemmodells sein.

---

## Sensor- und Gerätedaten

Das Data Model berücksichtigt unter anderem:

- Serial / RS-232
- Freezer
- AtmoWEB
- Temperatur
- Feuchte
- Vakuum
- CO₂
- O₂
- Lüfterdrehzahl
- Gerätezustände
- Betriebszustände
- Events
- Alarme

Herstellerdaten werden über Adapter in gemeinsame fachliche Felder übersetzt.

Rohwerte und sinnvolle abgeleitete Werte dürfen gemeinsam übertragen werden.

Setpoints und Alarmgrenzen sind keine Measurements.

LOG- und Alarminformationen werden als Events behandelt.

`validity` gehört zum Messwertmodell.

---

## Netzwerkmodell

Netzwerkinterfaces werden unter

```text
network.interfaces
```

geführt.

`blocked` ist Bestandteil des Interface-Modells.

Unnötige aktive Connectivity-Tests sollen vermieden werden.

Der LoggerPi liefert technische Netzwerkfakten.

Die fachliche Bewertung der Connectivity und daraus abgeleitete Health-Zustände gehören zum OtterPi.

---

## Services

Das Service-Modell ist strukturell definiert als:

```text
services.<service_id>
├── name
├── purpose
├── state
├── enabled
├── pid
├── started_at
└── last_state_change_at
```

Nicht jeder Service muss zwangsläufig jedes Feld liefern.

Der LoggerPi liefert den technischen Zustand des Dienstes.

Der OtterPi bewertet dessen fachliche Bedeutung für Health und Dashboard.

Die reale LoggerPi-Installation wurde inzwischen untersucht.

### Relevante beobachtete Runtime-Struktur

Aktuell wurden unter anderem folgende Komponenten auf dem LoggerPi festgestellt:

#### `meshagent.service`

- aktiviert
- läuft
- stellt den Mesh-/Remote-Zugriff bereit
- gehört zur aktuellen Betriebsumgebung des LoggerPi

#### `lightdm.service`

- aktiviert
- läuft
- stellt die grafische lokale Umgebung bereit
- die grafische Umgebung soll bewusst erhalten bleiben
- sie dient unter anderem als lokale Recovery-/Konfigurationsmöglichkeit, falls der Remote-Zugriff nicht funktioniert

#### `ssh.service`

- aktiviert
- läuft
- TCP Port 22 ist offen

SSH ist damit ein zentraler administrativer Zugangsweg.

#### `rc-local.service`

`/etc/rc.local` ist ausführbar und wird beim Boot ausgeführt.

Aktuell startet `rc.local` die Legacy-Anwendung:

```text
python /home/ZOOLOGY-observ/Programs/observer.py &
```

Damit ist die Legacy-`observer.py` weiterhin Bestandteil des realen Runtime-Verhaltens.

#### Legacy `observer.py`

Die aktuelle Legacy-Datei befindet sich auf dem LoggerPi unter:

```text
/home/ZOOLOGY-observ/Programs/observer.py
```

Sie läuft derzeit als:

```text
root
```

und wird über `rc.local` gestartet.

Der aktuelle SHA-256-Hash der auf dem LoggerPi vorhandenen Datei ist:

```text
f740d8832208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0
```

Die Legacy-Datei ist im Repository unter `docs/legacy/` dokumentiert.

Die Legacy-Anwendung ist Referenz für den bisherigen Datenpfad, aber nicht das Zielmodell der neuen Architektur.

---

## Aktueller Legacy-Datenpfad

Die Legacy-`observer.py` verwendet unter anderem:

  * AtmoWEB-Endpunkte
  * CPU-Temperatur
  * CPU-Auslastung
  * Freezer-Log
  * ThingSpeak Bulk Update

Der Freezer wird weiterhin über eine serielle Verbindung erfasst.

Das serielle Gerät wird als

    `/dev/ttyUSB0`

bereitgestellt.

Die kontinuierliche Protokollierung erfolgt inzwischen über einen dedizierten `systemd --user`-Service des Benutzerkontos `ZOOLOGY-observ`.

Der aktuelle Runtime-Pfad lautet:

    `/dev/ttyUSB0`
            ↓
       minicom
            ↓
      freezer.log

Der Service wird über

    `~/.config/systemd/user/freezer-log.service`

definiert und ist als User-Service aktiviert.

Der aktuelle Service verwendet für `minicom` eine virtuelle PTY-Umgebung:

    `/usr/bin/script`
            ↓
         minicom
            ↓
      `/dev/ttyUSB0`

Die relevante Startzeile lautet sinngemäß:

    `/usr/bin/script -q -c "/usr/bin/minicom -C /home/ZOOLOGY-observ/Programs/freezer.log -D /dev/ttyUSB0" /dev/null`

Die Verwendung von `script` stellt die für `minicom` erforderliche Terminal-/PTY-Umgebung bereit. Dadurch kann der Freezer-Logger als dauerhafter User-Service betrieben werden, ohne dass ein grafisches Terminalfenster oder eine aktive LXDE-Terminalsitzung erforderlich ist.

Der bisherige XDG/LXDE-Terminal-Autostart wurde deaktiviert. Die frühere Datei

    `/home/ZOOLOGY-observ/.config/autostart/TerminalAutostart.desktop`

wird nicht mehr als aktiver Startmechanismus verwendet.

Die grafische Umgebung selbst bleibt weiterhin Bestandteil der LoggerPi-Installation. Sie dient als lokaler Recovery- und Konfigurationsweg und ist nicht Voraussetzung für den Betrieb des Freezer-Loggers.

Das Freezer-Log befindet sich weiterhin unter:

    `/home/ZOOLOGY-observ/Programs/freezer.log`

Die Legacy-`observer.py` liest weiterhin den jeweils neuesten Freezer-Wert aus dieser Datei.

Damit besteht weiterhin folgende fachliche Abhängigkeit:

    serielles Gerät /dev/ttyUSB0
             |
             v
          minicom
             |
             v
        freezer.log
             |
             v
      Legacy observer.py
             |
             v
         ThingSpeak

Der technische Startmechanismus des Freezer-Loggers ist damit nicht mehr an eine grafische Terminalanwendung gebunden.

Die Freezer-Datenquelle selbst bleibt weiterhin eine Legacy-Datenquelle und wird erst durch einen ausdrücklichen neuen Freezer-Adapter in das neue Datenmodell abgelöst.

---

## Weitere beobachtete Systemdienste

Die Runtime-Inventur hat neben den bereits als relevant identifizierten
Diensten weitere Systemdienste gezeigt.

Nicht jeder installierte oder laufende Linux-Dienst ist automatisch ein
LoggerPi-Service im Sinne des Data Models.

Für die Service-Bewertung ist entscheidend, ob der Zustand eines Dienstes
für Betrieb, Zustand, Health oder Dashboard des LoggerPi relevant ist.

Damit können auch administrative oder infrastrukturelle Dienste relevant
sein, wenn ihr Ausfall den LoggerPi-Betrieb oder dessen Erreichbarkeit
wesentlich beeinflusst.

### Als relevant betrachtete Dienste

Insbesondere gehören dazu:

- `meshagent.service` – Mesh-/Remote-Zugriff
- `ssh.service` – administrative Erreichbarkeit
- `lightdm.service` – lokale grafische Recovery-/Konfigurationsumgebung
- `rc-local.service` – Startmechanismus der aktuellen Legacy-Anwendung
- `systemd-timesyncd.service` – Zeitsynchronisation
- `dhcpcd.service` – Netzwerkverwaltung / DHCP

Diese Dienste sind Bestandteil des Service-Bereichs des Core Batches.

Dabei wird insbesondere der technische Laufzustand übertragen, sodass im
Dashboard beispielsweise sichtbar sein kann:

```text
systemd-timesyncd    running
dhcpcd               running
```

Die fachliche Bewertung eines Ausfalls erfolgt weiterhin auf dem OtterPi.

`rc-local.service` bleibt Bestandteil des Modells, solange die Legacy-
`observer.py` darüber gestartet wird.

Nach der erfolgreichen Ablösung der Legacy-Anwendung kann `rc-local.service`
aus dem LoggerPi-Service-Modell entfernt werden.

### Weitere beobachtete Dienste

Daneben wurden unter anderem festgestellt:

- `networking.service`
- `raspberrypi-net-mods.service`
- `rsync.service`

Diese Dienste werden aktuell nicht als reguläre LoggerPi-Core-Services
geführt.

`rsync.service` ist aktiviert, läuft aktuell jedoch nicht, da auf der
Installation keine `/etc/rsyncd.conf` vorhanden ist.

`dhcpcd.service` wird dagegen als relevanter technischer Service geführt,
da der Zustand der aktuell verwendeten Netzwerkverwaltung für Betrieb,
Health und Diagnose relevant ist.

`systemd-timesyncd.service` wird ebenfalls als relevanter technischer
Service geführt, da die Zeitsynchronisation für die korrekte Interpretation
von Messwerten, Batches und Zeitstempeln relevant ist.

### Nicht für das aktuelle LoggerPi-Service-Modell vorgesehen

Folgende Dienste werden aufgrund der aktuellen Architektur nicht als
relevante LoggerPi-Services weiterverfolgt:

- `wpa_supplicant.service` – WLAN wird für den LoggerPi derzeit nicht
  vorgesehen
- `ModemManager.service` – kein vorgesehenes Modem-Szenario
- `bluetooth.service` – Bluetooth ist für den aktuellen LoggerPi-Betrieb
  nicht vorgesehen
- `avahi-daemon.service` – für den vorgesehenen Betrieb nicht erforderlich
- `teamviewerd.service` – obsolet; TeamViewer wird aus der LoggerPi-Installation entfernt

Diese Einordnung bezieht sich auf den aktuellen Zielzustand. Durch die
weitere Umstellung des LoggerPi können später zusätzliche Dienste
hinzukommen, die heute noch nicht absehbar sind.

Die Service-Liste bleibt deshalb bewusst erweiterbar.

### Bewertungsprinzip

Für einen als relevant betrachteten Service werden insbesondere bewertet:

1. operative Relevanz
2. Relevanz für LoggerPi-Zustand und Health
3. Relevanz für Erreichbarkeit oder Administration
4. stabiler funktionaler Zweck
5. sinnvoller Nutzen für Dashboard und Diagnose

Nicht jeder relevante Service muss dabei eine direkte Daten-Erfassungs-,
Batch- oder API-Funktion besitzen.

Der LoggerPi liefert den technischen Service-Zustand.

Der OtterPi bewertet dessen fachliche Bedeutung für Health und Dashboard.

---

## Aktuelle Netzwerksituation

Bei der Runtime-Inventur wurde festgestellt:

```text
eth0   UP
wlan0  DOWN
```

Der LoggerPi besitzt aktuell eine aktive Ethernet-Verbindung.

SSH lauscht auf:

```text
0.0.0.0:22
[::]:22
```

Die konkrete Netzwerk- und Routing-Konfiguration wird nicht automatisch zum fachlichen Core Batch.

Technische Netzwerkdaten können jedoch Teil des Systemmodells sein.

---

## Lokale Recovery-Fähigkeit

Die lokale grafische Umgebung mit LXDE/LightDM und Xorg bleibt bewusst Bestandteil der Installation.

Ziel ist, dass ein lokal angeschlossener Monitor und eine lokale Eingabemöglichkeit weiterhin als Recovery-/Konfigurationsweg zur Verfügung stehen können, wenn Remote-Zugriffe wie SSH oder Mesh-Zugriff nicht funktionieren.

Die aktuelle HDMI-Situation wurde noch nicht abschließend untersucht, da zum Zeitpunkt der Prüfung kein Monitor angeschlossen war.

---

## Metadata

Metadata wird nicht unnötig in jedem regulären Batch wiederholt.

Das Konzept ist:

```text
Erster Kontakt
        ↓
    vollständige Metadata
        ↓
    keine Änderung
        ↓
    keine erneute vollständige Übertragung

    Änderung
        ↓
    Metadata-Änderung / Delta
        ↓
    Übertragung über normalen LoggerPi → OtterPi Push-Weg
        ↓
    erfolgreiche technische Annahme
        ↓
    Änderung gilt auf Transportebene als zugestellt
```

Der LoggerPi kann keine aktive Rückverbindung des OtterPi voraussetzen.

Ein separates ACK-Synchronisationsprotokoll für Metadata ist nicht
Bestandteil des Kommunikationsmodells.

Die konkrete Behandlung von Wiederholungen, Duplikaten und einer erneuten
Synchronisation wird im Metadata-/Delivery-Design festgelegt.

Die genaue technische Metadata-Synchronisationsprotokollierung ist noch nicht finalisiert.

Der OtterPi darf auch für Metadata-Synchronisation nicht auf eine aktive eingehende Verbindung zum LoggerPi angewiesen sein.

---

## Wichtige Designentscheidungen

- LoggerPi erfasst technische Fakten.
- OtterPi bewertet fachliche Zustände und Health.
- Data Model und tatsächlicher Core Batch sind getrennt.
- Hersteller-API-Namen werden nicht als universelle Feldnamen verwendet.
- Herstellerdaten werden über Adapter in das gemeinsame Modell übersetzt.
- Measurements, States, Metadata, Configuration, Health und Events werden getrennt behandelt.
- Rohwerte und sinnvolle abgeleitete Werte dürfen gemeinsam übertragen werden.
- `validity` gehört zum Messwertmodell.
- Es gibt keine `measurements.misc`.
- Es gibt keine `states.misc`.
- Prozesslisten sind nicht Bestandteil des regulären Core Batches.
- Netzwerkinterfaces werden unter `network.interfaces` geführt.
- `blocked` ist Bestandteil des Interface-Modells.
- Unnötige aktive Connectivity-Tests werden vermieden.
- Setpoints und Alarmgrenzen sind keine Measurements.
- LOG- und Alarminformationen werden als Events behandelt.
- Metadata wird nicht unnötig in jedem regulären Batch wiederholt.
- Metadata-Änderungen müssen über den normalen LoggerPi → OtterPi Kommunikationsweg übertragen werden.
- Der OtterPi darf nicht auf eine aktive Verbindung zum LoggerPi angewiesen sein.
- Die lokale grafische Umgebung bleibt als möglicher Recovery-Weg erhalten.

---

## Aktueller Arbeitsschritt

Die reale LoggerPi-Runtime wurde untersucht und unter
`docs/system-inventory.md` dokumentiert.

Die funktionale Servicebewertung ist abgeschlossen.

Als relevante LoggerPi-Services für den aktuellen Core-Batch-Stand wurden
insbesondere festgelegt:

```text
meshagent
ssh
lightdm
rc-local
systemd-timesyncd
dhcpcd
```

Dabei gilt weiterhin:

Nicht jeder installierte oder laufende Linux-Dienst ist automatisch ein
LoggerPi-Service im Sinne des Data Models.

Auch Dienste für Erreichbarkeit, Administration, Recovery,
Netzwerkverwaltung und Zeitsynchronisation können aufgrund ihrer
Betriebsrelevanz Bestandteil des Service-Modells sein.

Der daraus abgeleitete Core Batch v1 wurde in

```text
docs/data-model/core-batch-v1.md
```

festgehalten und committed.

Die Legacy-`observer.py` bleibt weiterhin als Ist-Zustand und Referenz
erhalten.

`rc-local.service` bleibt so lange im Core-Batch-Service-Modell, wie
`rc-local` die Legacy-`observer.py` startet. Erst nach erfolgreicher
Ablösung der Legacy-Anwendung wird geprüft, ob `rc-local.service` aus dem
Modell entfernt werden kann.

### Aktueller nächster Schritt

Der erste vertikale Core-Batch-Datenpfad ist technisch implementiert und
durch Tests abgesichert.

Der aktuelle Pfad lautet:

```text
LoggerPi-Datenquelle
        ↓
Adapter / Reader
        ↓
Measurement / Systemdaten
        ↓
Core Batch
        ↓
persistente LoggerPi-Queue
        ↓
HTTP Delivery
        ↓
OtterPi POST /api/v1/batches
        ↓
BatchStore
        ↓
SQLite
```

Auf dem LoggerPi ist inzwischen zusätzlich die erste Runtime-Orchestrierung
implementiert.

Die Runtime kann mehrere konfigurierte AtmoWEB-Reader innerhalb einer
Messrunde ausführen und deren Measurements in genau einem Core Batch
zusammenführen:

```text
AtmoWEB 101 ─┐
             ├→ LoggerRuntime → ein Core Batch
AtmoWEB 102 ─┘
```

Der Batch wird anschließend über den bestehenden Delivery-/Queue-Pfad
zugestellt.

Vor der Erzeugung eines neuen Batches werden bereits wartende Batches aus
der persistenten Queue erneut zugestellt. Erfolgreich zugestellte Queue-
Einträge werden entfernt. Kann ein wartender Batch nicht zugestellt werden,
wird die weitere Queue-Wiedergabe für diesen Lauf abgebrochen, damit die
Reihenfolge der ausstehenden Batches erhalten bleibt.

Damit ist die technische Orchestrierung des ersten LoggerPi-Messzyklus
implementiert und durch automatisierte Tests abgesichert.

Der nächste Entwicklungsschritt ist nun **nicht** ein weiterer Adapter,
sondern ein sehr kleiner dauerhafter Runner für den LoggerPi, der
`LoggerRuntime.run_once()` regelmäßig ausführt.

Dabei soll der neue Pfad zunächst parallel zur bestehenden Legacy-
`observer.py` betrieben werden. Die Legacy-Runtime bleibt unverändert
produktiv.

Ziel des nächsten Schrittes:

```text
bestehender Legacy-Observer
        │
        ├── bestehender Legacy-Datenpfad
        │
        └── unverändert weiter

neuer LoggerPi-Runner
        ↓
LoggerRuntime.run_once()
        ↓
AtmoWEB 101 + AtmoWEB 102
        ↓
ein Core Batch
        ↓
Queue / HTTP Delivery
        ↓
OtterPi
```

Der Runner soll bewusst klein und ressourcenschonend bleiben. Es ist keine
zusätzliche Framework-, Async- oder Container-Schicht vorgesehen.

Erst nach erfolgreicher praktischer Verifikation dieses parallelen
LoggerPi-Betriebs werden weitere konkrete LoggerPi-Datenquellen ergänzt.

## Aktueller technischer Stand

Die folgenden Designschritte sind abgeschlossen und committed:

1. Data Model v1
2. Core Batch v1
3. Core Batch JSON Definition v1
4. Core Batch API v1
5. Core Batch Delivery v1

Damit sind insbesondere festgelegt:

- Core Batch Struktur
- Batch Envelope
- Pflicht-/Optional-Semantik
- `null`-Semantik
- `validity`-Semantik
- JSON-Repräsentation
- HTTP Push von LoggerPi → OtterPi
- `POST /api/v1/batches`
- HTTP Response über die vom LoggerPi initiierte Verbindung
- kein eingehender Rückkanal zum LoggerPi
- keine Mesh-Agent-Abhängigkeit für die API
- persistente lokale Queue
- Retry-Verhalten
- Duplicate Handling
- erfolgreiche technische HTTP-Annahme als Zustellentscheidung
- keine separate ACK-Synchronisation
- keine nachgelagerte Rückverbindung vom OtterPi zum LoggerPi

### Erste Core-Batch-Implementierung

Die technische Implementierung des Core-Batch-Datenmodells wurde begonnen
und schrittweise bis zur lokalen Queue und zum HTTP-Delivery-Pfad erweitert.

Aktuell existieren:

src/loggerpi_otterpi/model/
├── batch.py
└── measurement.py

Batch bildet den Batch Envelope ab und enthält:

- schema_version
- batch_id
- logger_id
- sequence
- created_at
- optionale measurements

Measurement bildet einen einzelnen Messwert ab und enthält:

- value
- unit
- measured_at
- validity
- source

Die fachlichen Validierungsregeln für Batch und Measurement sind
implementiert und durch Tests abgesichert.

Ein Batch kann mehrere benannte Measurements enthalten.

Beim Serialisieren werden Measurements in die definierte JSON-Struktur
überführt.

Ein leeres measurements-Objekt wird nicht in den Batch aufgenommen.

### Batch-Erzeugung

Die Batch-Erzeugung erfolgt über eine kleine, gezielte Factory:

src/loggerpi_otterpi/batch_factory.py

Die Factory erzeugt einen vollständigen Batch und verwendet dabei eine
persistente Sequence pro LoggerPi.

Die Sequence wird vor der Queue-Ablage vergeben und ist pro LoggerPi
monoton fortlaufend.

Dabei wurde bewusst keine zusätzliche generische Messwert-Erzeugungsschicht
eingeführt.

Insbesondere existieren bewusst keine:

- MeasurementFactory
- MeasurementBuilder
- zusätzliche system/time.py nur für die JSON-Struktur
- vorsorgliche Modellierung aller möglichen Core-Batch-Sections

Measurement bleibt das gemeinsame fachliche Datenmodell.

Die Batch-Erzeugung ist damit von der konkreten späteren Datenerfassung
getrennt.

### Batch Composer

Für die Zusammenführung bereits erfasster Daten existiert:

`src/loggerpi_otterpi/composer.py`

Der Composer übernimmt die aktuell verfügbaren LoggerPi-Systemdaten und führt sie gemeinsam mit optionalen Measurements in einen vollständigen Core Batch.

Dabei werden aktuell insbesondere:

* `system.time`
* `system.boot`
* `system.cpu`
* `system.cpu.temperature_celsius`
* `memory`

übernommen.

Der Composer ist keine zusätzliche generische Messwert-Erzeugungsschicht. Konkrete externe Sensor- und Gerätedaten werden weiterhin durch ihre jeweiligen Adapter bzw. Reader in das vorhandene `Measurement`-Modell überführt.

### Abgrenzung zur realen Datenerfassung

Die grundlegende Erfassung von LoggerPi-Systemdaten ist inzwischen implementiert.

Dazu gehören insbesondere Zeit, Boot/Uptime, CPU, CPU Load Average, CPU-Temperatur und Memory. Diese Daten können bereits in einen Core Batch übernommen werden.

Die Systemdaten werden über `system_info.py` gesammelt und über den Composer in den Core Batch integriert.

Die CPU-Temperatur ist dabei eine Systeminformation des LoggerPi und kein externer Sensor-Reader.

Weitere konkrete Sensor- und Gerätedaten sind davon getrennt zu betrachten
und werden schrittweise über konkrete Adapter bzw. Reader angebunden.

Die Architektur für weitere reale Datenquellen bleibt:

reale Datenquelle
    ↓
konkreter Adapter / Reader
    ↓
Measurement
    ↓
Batch

Die konkrete Datenquelle wird später angebunden.

Es wird dabei keine zusätzliche generische Messwert-Erzeugungsschicht
zwischen Datenquelle und Measurement eingeführt.

Damit ist insbesondere geklärt:

Wir müssen jetzt keinen künstlichen "Messwert-Erzeuger" bauen.

Die bereits implementierte Batch-Erzeugung stellt den Core-Batch-Rahmen
bereit. Reale Werte werden später durch konkrete Adapter bzw. Reader in
das vorhandene Measurement-Modell überführt.

### Persistente lokale Queue

Die persistente lokale Queue ist implementiert:

src/loggerpi_otterpi/batch_queue.py

Hinweis: Die Datei wurde bewusst von `queue.py` in `batch_queue.py` umbenannt,
damit kein Namenskonflikt mit dem Python-Standardmodul `queue` entsteht.
Andernfalls würde `from queue import BatchQueue` das falsche Modul laden.

Die Queue speichert vollständige Batches lokal als JSON Lines.

Ein bereits erzeugter Batch kann dadurch den Prozess bzw. einen
Verbindungsabbruch überstehen.

Die Queue kann:

- Batches persistent ablegen
- ausstehende Batches wieder einlesen
- einen spezifischen erfolgreich zugestellten Batch entfernen

Die Entfernung erfolgt anhand der stabilen Batch-Identität aus
batch_id und sequence.

Ein fehlgeschlagener Delivery-Versuch entfernt den Batch nicht aus der
Queue.

Damit ist der grundlegende Store-and-Forward-Baustein vorbereitet.

### HTTP Delivery

Der HTTP-Delivery-Baustein ist implementiert:

src/loggerpi_otterpi/delivery.py

Ein Batch wird als JSON per

POST /api/v1/batches

an den konfigurierten OtterPi-Endpunkt übertragen.

Als erfolgreiche technische Annahme gilt ausschließlich HTTP 202.

Andere HTTP-Statuscodes sowie HTTP-/Verbindungsfehler gelten als nicht
erfolgreiche Zustellung.

Die technische HTTP-Response erfolgt weiterhin über die vom LoggerPi
initiierte Verbindung.

Dies ist kein separates ACK-Synchronisationsprotokoll.

### Queue Delivery

Die Queue-Zustellung ist Bestandteil des LoggerRuntime-Laufs (runtime.py).

Der Delivery-Ablauf ist:

persistente Queue
    ↓
pending Batch
    ↓
HTTP Delivery
    ↓
HTTP 202
    ↓
Batch aus Queue entfernen

Bei nicht erfolgreicher Zustellung bleibt der Batch in der Queue.

Damit ist die entscheidende Eigenschaft des Push-Modells umgesetzt:

Ein Batch wird erst nach erfolgreicher technischer Annahme durch den
OtterPi aus der lokalen Queue entfernt.

Ein Retry verwendet denselben bereits erzeugten Batch und erzeugt keinen
neuen fachlichen Batch.

Damit bleiben insbesondere batch_id und sequence unverändert.

### Aktueller technischer Datenpfad

Der bisher implementierte technische Pfad ist damit:

Batch-Erzeugung
    ↓
persistente Sequence
    ↓
lokale Queue
    ↓
HTTP POST /api/v1/batches
    ↓
HTTP 202
    ↓
Queue-Eintrag entfernen

Bei Fehler:

Batch-Erzeugung
    ↓
persistente Sequence
    ↓
lokale Queue
    ↓
HTTP Delivery fehlgeschlagen
    ↓
Batch bleibt in Queue
    ↓
späterer erneuter Zustellversuch

Der vollständige reale Datenpfad ist für die AtmoWEB-Datenquellen
abgeschlossen und praktisch verifiziert (Stand 2026-09-20):

AtmoWEB 101 + AtmoWEB 102
    ↓
AtmoWebReader
    ↓
Measurement / Systemdaten
    ↓
Core Batch
    ↓
persistente Queue
    ↓
HTTPS
    ↓
nginx
    ↓
OtterPi POST /api/v1/batches
    ↓
BatchStore
    ↓
SQLite

Weitere konkrete LoggerPi-Datenquellen (z. B. Freezer) stehen noch aus.

## OtterPi-Ingestion und Persistenz

Die erste serverseitige OtterPi-Ingestion ist implementiert.

Der HTTP-Endpunkt:

```text
POST /api/v1/batches
```

nimmt Core Batches als JSON entgegen.

Die Implementierung befindet sich unter:

```text
src/loggerpi_otterpi/otterpi.py
```

Der HTTP-Handler übernimmt aktuell:

- Prüfung des Request-Pfads
- Prüfung des `Content-Type`
- Lesen und Parsen des JSON-Request-Bodys
- Rekonstruktion des Core Batch v1
- Rückgabe definierter HTTP-Fehler
- Übergabe des Batches an den persistenten `BatchStore`
- Behandlung identischer Duplikate
- Erkennung von Batch-Konflikten

Aktuell verwendete HTTP-Ergebnisse:

```text
202  accepted
400  invalid_payload
404  unknown path
409  batch_conflict
415  unsupported_media_type
```

Bei erfolgreicher Annahme werden `batch_id` und `sequence` in der
HTTP-Response zurückgegeben.

Die serverseitige Persistenz befindet sich unter:

```text
src/loggerpi_otterpi/otterpi_store.py
```

Der `BatchStore` verwendet derzeit SQLite mit einer Tabelle `batches`.

Die Persistenz berücksichtigt:

- `batch_id` als primären Schlüssel
- `logger_id` + `sequence` als eindeutige Batch-Position
- idempotente Annahme identischer Batches
- Erkennung widersprüchlicher Batches
- Speicherung der vollständigen Batch-Repräsentation als JSON

Für den SQLite-Betrieb werden derzeit:

```text
journal_mode = WAL
synchronous  = NORMAL
```

verwendet.

Damit ist die grundlegende serverseitige Ingestion einschließlich
persistenter Speicherung implementiert und durch Tests abgesichert.

## Implementierungsstand: reale Systemdaten

Die zuvor geplante Anbindung der grundlegenden LoggerPi-Systemdaten ist
inzwischen technisch umgesetzt.

Bereits implementiert und getestet sind:

  * `system.time`
  * `system.boot`
  * `system.cpu`
  * CPU Load Average
  * CPU-Temperatur
  * `memory`

Die CPU-Temperatur wird als:

`system.cpu.temperature_celsius`

geführt und stammt aus der LoggerPi-Systeminformation.

Sie ist ausdrücklich kein externer Sensor-Reader.

Die entsprechenden Reader befinden sich in:

```text
src/loggerpi_otterpi/system_info.py
```

Die Daten werden bereits in das vorhandene Core-Batch-Modell integriert.

`Batch` unterstützt dafür optionale:

```text
system
memory
```

und `create_batch()` kann diese Daten übernehmen.

Damit ist für diese Systemdaten **kein weiterer Reader- oder
Systemdaten-Modellierungsschritt** erforderlich.

Insbesondere wird nicht erneut gebaut:

- ein weiterer Temperatur-/Systemdaten-Reader für bereits abgedeckte Werte
- eine zusätzliche generische MeasurementFactory
- ein zusätzlicher MeasurementBuilder
- eine weitere Batch-Abstraktion

Die bestehenden Reader und das bestehende Batch-Modell sind für den
nächsten Implementierungsschritt zu verwenden.

## Implementierungsstand: AtmoWEB

Die AtmoWEB-Anbindung ist als konkreter externer Reader implementiert:

src/loggerpi_otterpi/atmoweb.py

Der Reader übernimmt:

- AtmoWEB-Geräteidentifikation
- Auslesen der AtmoWEB-Messwerte
- Mapping von Temperatur
- Mapping von Feuchte
- Mapping von Vakuum
- Mapping der optionalen CO₂-, O₂- und Lüfterwerte
- Mapping von Gerätezuständen
- Mapping des Betriebsmodus
- Behandlung von `N/A`
- Behandlung von `N/D`
- Validierung und Normalisierung des AtmoWEB-Zeitstempels
- Behandlung ungültiger bzw. nicht numerischer Werte

Die herstellerspezifischen AtmoWEB-Feldnamen werden dabei nicht in das
gemeinsame Data Model übernommen.

Die AtmoWEB-Gerätekonfiguration ist separat gehalten:

src/loggerpi_otterpi/atmoweb_config.py

Damit bleiben Reader-Logik und gerätespezifische Konfiguration getrennt.

Die derzeit bekannte AtmoWEB-Gerätekonfiguration wird dort zentral
definiert und kann unabhängig vom Reader erweitert werden.

Die AtmoWEB-Zustände und Betriebsinformationen werden derzeit technisch
erfasst und in die gemeinsamen Strukturen übersetzt.

Eine endgültige Entscheidung über Change Detection und darüber, welche
States bzw. Operations nur bei Änderung übertragen werden, ist noch nicht
getroffen. Der Reader trifft diese fachliche Transportentscheidung daher
nicht.

### Nächster Implementierungsschritt

Der vertikale End-to-End-Datenpfad wird jetzt schrittweise mit konkreten
realen LoggerPi-Datenquellen erweitert.

Als erste konkrete externe Datenquelle wurde AtmoWEB angebunden.

Der AtmoWEB-Reader übernimmt die herstellerspezifische Kommunikation und
übersetzt die AtmoWEB-Werte in das gemeinsame Measurement-Modell.

Die Architektur bleibt:

konkrete Datenquelle
    ↓
konkreter Adapter / Reader
    ↓
Measurement
    ↓
Batch
    ↓
persistente Queue
    ↓
HTTP Delivery
    ↓
OtterPi

Die AtmoWEB-Gerätekonfiguration ist separat vom Reader gehalten und enthält
die Zuordnung der bekannten AtmoWEB-Geräte.

Die Change-Detection-Architektur für States und Operations ist noch nicht
finalisiert. Der AtmoWEB-Reader liefert deshalb zunächst die technischen
Zustände und Betriebsinformationen; die Entscheidung, welche dieser Werte
später nur bei Änderung übertragen werden, bleibt Bestandteil des noch
offenen Change-Detection-/Batch-Designs.

Als nächstes wird der AtmoWEB-Pfad in den bestehenden Batch-/Queue-/Delivery-
Pfad integriert und anschließend gegen den realen LoggerPi-Betrieb geprüft.

Der nächste Arbeitsschritt ist daher **nicht** die erneute Implementierung
von System-, Memory-, CPU- oder Load-Daten.

Ziel ist zunächst ein kleiner, reproduzierbarer E2E-Schnitt, der nachweist,
dass ein real bzw. realistisch erfasster Wert vom vorhandenen Reader bis
zur HTTP-Zustellung durch den bestehenden Batch-/Queue-/Delivery-Pfad
gelangt.

Erst wenn dieser vertikale Pfad funktioniert, werden weitere reale
LoggerPi-Datenquellen schrittweise ergänzt.

### Aktueller Teststand

Der aktuelle Implementierungsstand ist durch automatisierte Tests
abgesichert.

Derzeit bestehen:

```text
72 Tests
Alle Tests bestehen.
```

Zusätzlich sind die lokalen Ruff-Quality-Gates erfolgreich:

```text
ruff format --check .
45 files already formatted

ruff check .
All checks passed!
```

Abgedeckt sind insbesondere:

- Batch-Modell
- Measurement-Modell
- Batch-Validierung
- Batch-Erzeugung
- Batch Composer
- persistente Sequence
- Queue-Persistenz
- Queue-Wiederherstellung
- Entfernen eines spezifischen Queue-Eintrags
- HTTP-JSON-Delivery
- HTTP-202-Erfolg
- Behandlung nicht erfolgreicher HTTP-Responses
- Systemdaten
- Memory-Daten
- CPU-Daten
- E2E-Datenpfad
- AtmoWEB-Geräteidentifikation
- AtmoWEB-Messwert-Mapping
- AtmoWEB-Validity-Mapping
- AtmoWEB-State-Mapping
- AtmoWEB-Fehlerbehandlung
- AtmoWEB-Gerätekonfiguration
- mehrere AtmoWEB-Quellen innerhalb eines Batches
- Runtime-Orchestrierung
- Replay ausstehender Queue-Batches vor einem neuen Batch
- Entfernen erfolgreich zugestellter Queue-Batches
- Beibehalten der Queue bei fehlgeschlagener Zustellung
- OtterPi-Batch-Annahme
- persistente Speicherung
- Duplicate Handling
- Sequence-Konflikte
- SQLite-WAL-Konfiguration
- ungültige Batch-Payloads
- unbekannte HTTP-Pfade

Zusätzlich gilt:

ruff check .
→ All checks passed!

ruff format --check .
→ alle Dateien formatiert

git diff --check
→ keine inhaltlichen Whitespace-Fehler

Der aktuelle technische Implementierungsstand ist damit lokal getestet.

Der vertikale Implementierungsschnitt mit AtmoWEB als konkreter
LoggerPi-Datenquelle ist abgeschlossen.

Praktisch verifiziert wurde damit:

AtmoWEB
    ↓
AtmoWebReader
    ↓
Measurement
    ↓
Core Batch
    ↓
persistente lokale Queue
    ↓
HTTP POST
    ↓
HTTP 202
    ↓
Queue-Eintrag entfernen

Dabei wurde insbesondere auch die tatsächliche AtmoWEB-Einheit
`mbar` für den Druckwert durch den gesamten Pfad erhalten.

---

## Planungs-Freeze / Übergang in die Implementierung

Mit diesem Stand wird die Planung für den ersten
Core-Batch-v1-Implementierungsschnitt eingefroren.

Die folgenden Dokumente bilden die verbindliche Planungsgrundlage:

```text
docs/data-model/data-model-v1-field-catalog.md
docs/data-model/core-batch-v1.md
docs/data-model/core-batch-v1-json.md
docs/api/core-batch-api-v1.md
docs/api/core-batch-delivery-v1.md
```

Ab jetzt werden diese Dokumente nicht mehr aus Gründen sprachlicher
Optimierung oder weiterer theoretischer Vervollständigung überarbeitet.

Eine Änderung erfolgt nur noch, wenn:

1. die Implementierung einen echten Widerspruch oder eine nicht
   implementierbare Vorgabe aufzeigt,
2. eine bereits getroffene technische Entscheidung nachweislich falsch ist
   oder
3. eine konkrete Implementierungsanforderung eine Änderung des Vertrags
   zwingend erforderlich macht.

Die folgenden Bereiche bleiben bewusst offen und werden nicht vorab
vollständig spezifiziert:

- Metadata Change
- Events
- `connectivity.upload`
- `connectivity.queue`
- weitere spätere Erweiterungen

Diese offenen Bereiche dürfen die aktuelle Core-Batch-v1-Implementierung
nicht blockieren.

## Erster Implementierungsfahrplan

Der bisherige technische Grundpfad ist inzwischen implementiert:

Batch-Erzeugung
    ↓
persistente Sequence
    ↓
lokale Queue
    ↓
HTTP POST /api/v1/batches
    ↓
HTTP 202
    ↓
Queue-Eintrag entfernen

Damit sind die grundlegenden Bausteine für Erzeugung, lokale Persistenz
und technische Zustellung vorhanden.

Der erste vertikale End-to-End-Implementierungsschnitt ist abgeschlossen.

Mit AtmoWEB wurde eine bereits vorhandene konkrete LoggerPi-Datenquelle
in den bestehenden Core-Batch-/Queue-/HTTP-Delivery-Pfad integriert.

Der implementierte Pfad lautet:

AtmoWEB
    ↓
AtmoWebReader
    ↓
Measurement
    ↓
Core Batch
    ↓
persistente Queue
    ↓
HTTP Delivery
    ↓
OtterPi

Der Pfad ist durch einen automatisierten E2E-Test abgesichert.

Damit ist die technische Grundlage für die weitere Runtime-Integration
vorhanden.

### Runtime-Orchestrierung

Die konkrete Runtime-Orchestrierung des ersten LoggerPi-Datenpfades ist
implementiert und getestet.

Die `LoggerRuntime` übernimmt dabei ausschließlich die Orchestrierung der
bereits vorhandenen Bausteine:

```text
konfigurierte Reader
        ↓
Measurements zusammenführen
        ↓
ein Core Batch
        ↓
ausstehende Queue-Batches zustellen
        ↓
neuen Batch zustellen oder in Queue ablegen
```

Die Runtime verwendet mehrere konfigurierte AtmoWEB-Reader, erzeugt daraus
jedoch pro Messrunde bewusst nur **einen** Core Batch.

Die aktuell konfigurierte AtmoWEB-Gruppe umfasst:

```text
atmoweb_101
141.51.190.101

atmoweb_102
141.51.190.102
```

Die Reader-Konfiguration bleibt von der Runtime getrennt. Die
`AtmoWebReader`-Implementierung bleibt für die herstellerspezifische
Kommunikation zuständig.

Die Runtime führt keine fachliche Bewertung der Messwerte durch und enthält
keine herstellerspezifische AtmoWEB-Logik.

Bereits wartende Batches werden vor der Erzeugung eines neuen Batches
wieder zugestellt. Ein erfolgreich zugestellter Queue-Eintrag wird entfernt.
Bei einem fehlgeschlagenen Replay wird die Queue-Wiedergabe für diesen Lauf
abgebrochen.

Die Runtime ist damit bewusst als dünne Orchestrierungsschicht gehalten.

### Nächster Schritt: dauerhafter LoggerPi-Runner

Die Runtime selbst ist nicht als dauerhaft laufender Prozess ausgelegt.

Als nächstes wird ein kleiner Runner benötigt, der `LoggerRuntime.run_once()`
regelmäßig ausführt.

Der Runner soll:

- mit möglichst wenig Ressourcen auskommen,
- keine zusätzlichen Frameworks benötigen,
- den bestehenden Legacy-Observer nicht ersetzen,
- den neuen Datenpfad parallel zum Legacy-Betrieb starten können,
- Fehler eines einzelnen Zyklus kontrolliert behandeln,
- den bestehenden LoggerPi möglichst wenig verändern.

Der konkrete Start-/Service-Mechanismus wird vor der Implementierung gegen
die bestehende LoggerPi-Runtime und die dokumentierten Betriebsbedingungen
geprüft.

Der bestehende Legacy-Observer bleibt bis zur praktischen Verifikation des
neuen Pfades unverändert produktiv.

## Aktuelle offene Arbeitspakete

### P0 – Produktionsdeployment verifiziert ✅

Seit 2026-09-20 laufen LoggerPi und OtterPi produktiv auf `v1.2.2`.

### P0 – Authentication implementiert ✅

Seit `v1.1.0` ist die Übertragung durch Bearer-Token-Authentication
geschützt.

### P0 – Dashboard implementiert ✅

Seit `v1.2.0` stellt der OtterPi ein Dashboard unter `https://observer.makki.route64.de` und eine Einstiegsseite unter `https://zoology.makki.route64.de` bereit (Charts, 48h, Ortszeit).

Der Application-Deploymentmechanismus ist implementiert und auf
LoggerPi und OtterPi praktisch ausgerollt (Stand 2026-09-20).

Beide Systeme laufen auf `v1.0.4` und übertragen Core Batches
kontinuierlich.

Zu verifizieren:

```text
LoggerPi
    ↓
loggerpi-otterpi-update loggerpi
    ↓
loggerpi.observer.service
```

und:

```text
OtterPi
    ↓
loggerpi-otterpi-update otterpi
    ↓
otterpi.observer.service
```

Dabei müssen insbesondere Installation, Service-Start,
Konfiguration und `DEPLOYED_COMMIT` geprüft werden.

### P0 – OtterPi nginx-Integration

Der OtterPi-Anwendungsserver läuft lokal auf:

```text
127.0.0.1:8090
```

Die bestehende nginx-/TLS-Infrastruktur ist vorhanden.

Die konkrete Reverse-Proxy-Konfiguration für den LoggerPi-OtterPi-
API-Endpunkt ist noch nicht fertiggestellt bzw. nicht als Projekt-
Deployment dokumentiert.

Vor der Konfiguration muss die reale nginx-Konfiguration read-only
vollständig erfasst werden.

### P0 – Authentication / Authorization

Für den produktiven LoggerPi → OtterPi HTTP-Betrieb ist noch eine
Authentication-/Authorization-Lösung festzulegen.

### P1 – LoggerPi Runner

Der dauerhafte LoggerPi-Runner für:

```text
LoggerRuntime.run_once()
```

bleibt ein eigener Implementierungsschritt.

Er soll zunächst parallel zur Legacy-`observer.py` betrieben werden.

### P1 – praktischer E2E-Test

Nach Deployment und nginx-Konfiguration muss der reale Pfad geprüft
werden:

```text
LoggerPi
 ↓
Core Batch
 ↓
Queue
 ↓
HTTPS
 ↓
nginx
 ↓
127.0.0.1:8090
 ↓
BatchStore
 ↓
SQLite
 ↓
HTTP 202
 ↓
Queue removal
```

### P1 – Dokumentations-Synchronisation

Nach erfolgreichem Deployment müssen insbesondere aktualisiert werden:

```text
docs/PROJECT-STATE.md
docs/deployment/DEPLOYMENT.md
docs/baselines/OtterPi_Technical_Baseline_v2.md
docs/development/DECISIONS.md
```

### Danach

Nach Festlegung und Implementierung der Runtime-Orchestrierung wird der
bereits getestete AtmoWEB-Datenpfad praktisch auf dem LoggerPi verifiziert.

Erst danach werden weitere konkrete LoggerPi-Datenquellen schrittweise
ergänzt.

### Was ausdrücklich nicht gebaut wird

Die bisherige Implementierung hat gezeigt, dass der Core-Batch-Schnitt
keine zusätzlichen Abstraktionen benötigt.

Bewusst nicht vorgesehen sind insbesondere:

- zweite batch.py
- MeasurementFactory
- MeasurementBuilder
- zusätzliche generische Messwert-Erzeuger
- system/time.py nur wegen der JSON-Struktur
- vorsorgliche Modellierung aller 15 Core-Batch-Sections

Die Architektur bleibt:

konkrete Datenquelle
    ↓
Adapter / Reader
    ↓
Measurement
    ↓
Core Batch

Damit bleibt der aktuelle Code bewusst klein und auf den tatsächlich
benötigten Implementierungsschnitt begrenzt.

Der Project State ist der zentrale Wiedereinstiegspunkt für die
Implementierungsphase.

Bei einem späteren Wiedereinstieg ist nicht erneut in die abgeschlossene
Planungsphase zurückzukehren.

Zuerst wird der tatsächliche Implementierungsstand des Repositories
geprüft und anschließend der nächste konkrete Implementierungsschritt
bestimmt.

Der Implementierungsfahrplan darf sich durch konkrete technische
Erkenntnisse verändern. Bereits getroffene Architektur- und
Datenmodellentscheidungen werden jedoch nicht ohne konkreten technischen
Grund neu aufgerollt.

---

## Bewusst offene spätere Erweiterungen

Die folgenden Punkte sind für den aktuellen
Core-Batch-v1-Implementierungsschnitt bewusst offen:

- vollständiges Metadata-Synchronisationsprotokoll
- Event-Schema
- Routing-/DNS-Platzierung
- Behandlung statischer Netzwerk-/Storage-Metadata
- weitere Details der Legacy-Ablösung
- weitere Zuordnung zusätzlicher Runtime-Komponenten
- Schema-Evolution über v1 hinaus
- konkrete Struktur von `connectivity.upload`
- konkrete Struktur von `connectivity.queue`
- konkrete Authentication-/Authorization-Methode für den produktiven
  HTTP-Betrieb

Authentication ist bewusst außerhalb des Core-Batch-Datenmodells gehalten.

Für den ersten lokalen End-to-End-Implementierungsschnitt ist keine
finale Authentication-/Authorization-Lösung erforderlich.

Vor einem produktiven bzw. entsprechend abgesicherten Betrieb muss die
konkrete Authentication-/Authorization-Methode festgelegt werden.

Credentials, Tokens oder vergleichbare Authentifizierungsinformationen
sind nicht Bestandteil des Core-Batch-JSON.

Diese Punkte werden erst wieder aufgenommen, wenn die laufende
Implementierung einen konkreten Bedarf dafür zeigt.

---

## Referenzdokumente

Der detaillierte Feldkatalog wird unter

```text
docs/data-model/data-model-v1-field-catalog.md
```

geführt.

Der Feldkatalog beschreibt das verfügbare Data Model.
Er definiert nicht automatisch, welche Felder in jedem regulären Core Batch
enthalten sein müssen.

Die übrigen zentralen Spezifikationsdokumente sind:

```text
docs/data-model/core-batch-v1.md
docs/data-model/core-batch-v1-json.md
docs/api/core-batch-api-v1.md
docs/api/core-batch-delivery-v1.md
```

Diese Dokumente bilden gemeinsam die eingefrorene Planungsgrundlage für
die aktuelle Core-Batch-v1-Implementierungsphase.

Die historische Legacy-Implementierung und ihre Dokumentation befinden sich unter:

```text
docs/legacy/
```

Der Project State ist das zentrale Wiedereinstiegsdokument für den aktuellen Entwicklungsstand.

---

### Technische Untersuchungen

Das Reverse Engineering des WeatherHub-Observer-Datenkanals ist separat
dokumentiert unter:

```text
docs/research/weatherhub-observer.md
```

Der aktuelle Stand umfasst einen reproduzierten ChartData-Datenkanal,
doppelte Base64-Dekodierung sowie erste experimentelle Erkenntnisse zur
Binärstruktur. Zusätzlich wurde festgestellt, dass das WeatherHub-Dashboard
für die aktuellen Sensorwerte separate XHR-POST-Requests pro Sensor
verwendet. Diese deutlich kleineren Datenkanäle werden aktuell als möglicher
bevorzugter Zugriff für die benötigten Momentanwerte untersucht.

Der WeatherHub-Strang ist **seit v1.5.0 produktiv integriert**.
Die Integration erfolgt über einen LoggerPi-Adapter (WeatherHubReader),
der die vom Gateway-Proxy empfangenen und dekodierten Sensordaten in
das gemeinsame Measurement-Modell überführt.

Der Portalzugriff (`www.wh-observer.de`) ist **nicht** Bestandteil der
produktiven Integration – der lokale Gateway-Proxy-Datenpfad wird
verwendet.

Zukünftige Erweiterungen:
- Weitere Sensorfamilien (ID06, ID08, ID0B, ID11)
- State/Event-Verarbeitung (ID04 Wasserkontakt, ID10 Tür/Fenster)
- Stale-Logik für WeatherHub-Sensoren
- Gateway-Deduplizierung (wenn .132 ebenfalls in Proxymodus geht)
- Cloud-Forward optional (WEATHERHUB_CLOUD_FORWARD_ENABLED)
- Dashboard-Anzeige für WeatherHub-Sensoren

## Arbeitsregel

Der Project State wird während der Entwicklung aktiv gepflegt.

Wenn eine relevante Erkenntnis gewonnen, eine Architekturentscheidung getroffen oder ein Arbeitsschritt abgeschlossen wurde, soll der Project State zeitnah aktualisiert werden.

Insbesondere vor einem größeren neuen Arbeitsschritt soll geprüft werden:

```text
Repository
    ↓
PROJECT-STATE.md
    ↓
aktueller tatsächlicher Stand
    ↓
nächster konkreter Schritt
```

Damit bleibt der Projektstand unabhängig vom Chatverlauf nachvollziehbar.

---

## Design Principle

> So schlank wie möglich, aber sinnvoll wie nötig.
