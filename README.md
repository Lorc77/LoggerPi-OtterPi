# LoggerPi-OtterPi

> Data Model, API und Software für den Datenpfad LoggerPi → OtterPi

LoggerPi-OtterPi ist ein schlankes, push-basiertes Monitoring-System für
Umgebungs- und Gerätedaten. Ein **LoggerPi** erfasst System-, Sensor- und
Gerätedaten und überträgt diese als **Core Batch** an einen zentralen
**OtterPi**.

---

## Überblick

```text
LoggerPi
    ↓
Core Batch
    ↓
persistente lokale Queue
    ↓
HTTP POST /api/v1/batches
    ↓
OtterPi
    ↓
BatchStore
    ↓
SQLite
```

- **LoggerPi** erfasst technische Fakten (System, Sensor, Gerät).
- **OtterPi** bewertet fachliche Zustände, Health und Dashboard.
- Kommunikation erfolgt grundsätzlich als **Push** (LoggerPi → OtterPi).
- Der OtterPi initiiert keine Verbindung zum LoggerPi.

---

## Architektur

```text
Quelle / Hersteller-API
        ↓
Adapter / Reader
        ↓
gemeinsames Data Model
        ↓
Core Batch
        ↓
persistente Queue
        ↓
HTTP Delivery
        ↓
OtterPi
        ↓
Validierung / Health / Events / Dashboard
```

Herstellerspezifische Feldnamen werden nicht direkt zu universellen
Data-Model-Feldern. Neue Sensoren und Datenquellen werden über Adapter
in das gemeinsame Modell integriert.

---

## Komponenten

| Komponente | Beschreibung |
|------------|--------------|
| `src/loggerpi_otterpi/model/` | Datenmodelle: `Batch`, `Measurement` |
| `src/loggerpi_otterpi/atmoweb.py` | AtmoWEB-Reader (Memmert) |
| `src/loggerpi_otterpi/atmoweb_config.py` | AtmoWEB-Gerätekonfiguration |
| `src/loggerpi_otterpi/freezer.py` | Freezer-Reader (HFC-Serie, direkt Serial) |
| `src/loggerpi_otterpi/freezer_config.py` | Freezer-Konfiguration |
| `src/loggerpi_otterpi/memmert.py` | MEMMERT IPP300-Reader (seriell) |
| `src/loggerpi_otterpi/memmert_config.py` | MEMMERT-Konfiguration |
| `src/loggerpi_otterpi/thingspeak_delivery.py` | ThingSpeak-Injektion (semi-redundant) |
| `src/loggerpi_otterpi/thingspeak_config.py` | ThingSpeak-Konfiguration |
| `src/loggerpi_otterpi/batch_factory.py` | Batch-Erzeugung + persistente Sequence |
| `src/loggerpi_otterpi/composer.py` | Zusammenführung Systemdaten + Measurements |
| `src/loggerpi_otterpi/batch_queue.py` | persistente lokale Queue (JSON Lines) |
| `src/loggerpi_otterpi/delivery.py` | HTTP-Delivery an OtterPi |
| `src/loggerpi_otterpi/runtime.py` | LoggerRuntime-Orchestrierung |
| `src/loggerpi_otterpi/loggerpi_runner.py` | dauerhafter Runner (Intervall + Signal) |
| `src/loggerpi_otterpi/loggerpi_observer.py` | LoggerPi-Prozess-Einstiegspunkt |
| `src/loggerpi_otterpi/system_info.py` | Systemdaten (CPU, Memory, Zeit, Boot) |
| `src/loggerpi_otterpi/otterpi.py` | OtterPi-HTTP-Ingestion |
| `src/loggerpi_otterpi/otterpi_store.py` | BatchStore (SQLite) |
| `src/loggerpi_otterpi/otterpi_observer.py` | OtterPi-Prozess-Einstiegspunkt |
| `src/loggerpi_otterpi/dashboard.py` | Dashboard (Charts, 48h) |
| `src/loggerpi_otterpi/weatherhub.py` | WeatherHub-Adapter (Reader) |
| `src/loggerpi_otterpi/weatherhub_gateway_decoder.py` | WeatherHub-Gateway-Decoder |
| `src/loggerpi_otterpi/weatherhub_gateway_listener.py` | WeatherHub-Gateway-Listener (TCP) |
| `src/loggerpi_otterpi/dashboard_config.py` | Dashboard-Konfiguration (Raum- und Sensor-Zuordnung) |
| `src/loggerpi_otterpi/admin.py` | Admin-UI (Tabs, JSON-Editor, Alert History) |
| `src/loggerpi_otterpi/archive_batches.py` | Batch-Archivierung (monatlich, 12 Monate) |
| `src/loggerpi_otterpi/config_store.py` | JSON-Config-Verwaltung (Validierung, `.bak`, atomar) |
| `src/loggerpi_otterpi/dashboard_charts.py` | Chart-/JS-Helfer für das Dashboard |
| `src/loggerpi_otterpi/dashboard_constants.py` | Dashboard-Konstanten (Zeiträume, Farben, Version) |
| `src/loggerpi_otterpi/dashboard_data.py` | Dashboard-Datenfunktionen (Queries, Berechnungen) |
| `src/loggerpi_otterpi/notifier.py` | Notifier (E-Mail, ntfy, Webhook) |
| `src/loggerpi_otterpi/alert_store.py` | SQLite-Speicher für Alerts |
| `src/loggerpi_otterpi/alert_engine.py` | Alert-Engine (Regeln, Dedup, Quiet Hours, LoggerPi-Heartbeat) |
| `src/loggerpi_otterpi/heartbeat.py` | Gemeinsame Offline-Status-Logik für Admin und Dashboard |
| `src/loggerpi_otterpi/sensor_schemas.py` | Zentrale Schema-Definition pro Sensor-Typ |

---

## Deployment

Die Anwendung wird aus dem GitHub-Repository `main` deployt.

Der Deployment-Wrapper:

```text
deploy/update.sh
```

unterstützt zwei Rollen:

### LoggerPi

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update loggerpi
```

### OtterPi

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update otterpi
```

Nach erfolgreichem Deployment werden geschrieben:

```text
/opt/loggerpi-otterpi/DEPLOYED_COMMIT    technischer Git-Commit
/opt/loggerpi-otterpi/DEPLOYED_VERSION   menschenlesbare Version (z. B. v1.0.0)
/opt/loggerpi-otterpi/VERSION            Version aus pyproject.toml
```

### Flache Deploy-Struktur

Die Installation kopiert die Dateien **flach** nach `/opt/loggerpi-otterpi/`.
Da `model/` ein Unterverzeichnis ist, wird `PYTHONPATH` gesetzt:

```bash
PYTHONPATH=/opt/loggerpi-otterpi:/opt/loggerpi-otterpi/model
```

### Aktueller Betriebsstand (2026-11-08)

| System | Version | Status |
|--------|---------|--------|
| LoggerPi | `v1.12.5` | Läuft, sendet Batches alle 15 Minuten |
| OtterPi | `v1.12.5` | Empfängt Batches, speichert in SQLite, Alert-Engine aktiv |

Der E2E-Datenpfad (LoggerPi → nginx → OtterPi → SQLite) ist verifiziert.

Einstiegsseite: `https://zoology.makki.route64.de`
Dashboard: `https://observer.makki.route64.de`
Authentication: Bearer Token (seit v1.1.0)

Datenquellen:
- AtmoWEB 101/102 (MEMMERT HPP260) ✅
- Freezer (HFC-Serie, direkt Serial) ✅
- MEMMERT IPP300 links/rechts ✅
- ThingSpeak-Injektion (field1–7) ✅
- WeatherHub Sensoren (Gateway Proxy, 17 Sensoren) ✅

Admin (LAN-only): `https://observer.makki.route64.de/admin`
- Rooms-Tab: Formular-UI (Raum-/Geräte-Verwaltung, Raumwechsel, Inline-Formulare,
  How-to für neue WeatherHub-Sensoren, doppelte Delete-Abfrage, Räume mit
  Sensoren können nicht gelöscht werden, Limits werden mit dem Sensor gelöscht)
- Alarm Limits-Tab: Raum-Kacheln mit Geräte-Kacheln, Limits als farbige Chips
  (Warn ↓ 20 °C · ↑ 23 °C, Crit ↓ 18 °C · ↑ 28 °C, Rate ↕ 1 °C/h,
  Warn/Crit/Rate n/c), letzte Messwerte pro Measurement, „Show all"-Filter,
  Stale/Invalid-Alerts pro Gerät konfigurierbar, Edit Limits pro Gerät,
  System-Karte für LoggerPi-Offline-Erkennung
- Mail-Tab: Formular-UI (SMTP, Empfänger, Routing, Dedup, Quiet Hours)
- Notifications-Tab: Formular-UI (ntfy, webhook, Severity-Auswahl pro Kanal)
- Messages-Tab: Formular-UI (globale Regel-Texte, gruppiert in Measurements,
  States, System)
- Alerts-Tab (Default-Tab): Alert History als Tabelle (Status, Zeit, Severity,
  Regel, Gerät, Aktionen), gruppiert nach Tagen, Status-Zeile
  („3 active critical · 5 active warning · 12 resolved"), Balkendiagramm
  (14 Tage kumulativ), Acknowledge-Button, Resolve-Button, Filter
  „Only unacknowledged" / „Only active"
- Test-Mail-Button im Mail-Tab
- JSON-Editor als „Advanced"-Toggle (alle Tabs)
- JSON-Validierung, `.bak`, atomares Schreiben
- Statusleuchte im Header (LoggerPi-Offline-Status)
- Toast-Notification bei allen Save-/Delete-/Acknowledge-/Resolve-Aktionen
- How-to-Texte in allen Tabs (Rooms, Alarm Limits, Mail, Notifications,
  Messages, Alerts)

## Alert-Engine

Die Alert-Engine läuft als Thread im `otterpi.observer.service` und prüft
nach jedem Batch (und alle 300 s) die konfigurierten Regeln:

- **Measurements:** `warning_min/max`, `critical_min/max`, `rate_of_change`, `stale`, `invalid`
- **States:** `freezer.alarms`, `battery_low`, `door_open`, `contact_open`
- **System:** LoggerPi-Heartbeat (2-stufig, siehe unten)

Alerts werden dedupliziert (`dedup_seconds`), unterliegen Quiet Hours
(`quiet_hours`) und werden über die konfigurierten Notifier (E-Mail, ntfy,
Webhook) versendet. Die Alert History ist im Admin unter „Alerts" sichtbar.

### LoggerPi-Offline-Erkennung

Die Alert-Engine prüft, wann der letzte Batch auf dem OtterPi **empfangen**
wurde (`received_at`, OtterPi-seitig). Daraus ergeben sich zwei Stufen:

| Stufe | Schwelle | Anzeige | Alert |
|---|---|---|---|
| OK | < 30 min | grüne Lampe, „Last batch X min ago" | – |
| Warnung | 30 min – 1 h | gelbe Lampe, „Last batch X min ago" | optional (`warning`) |
| Kritisch | ≥ 1 h | rote Lampe, „LoggerPi offline for X min" | immer (`critical`) |

Die Schwellenwerte und die optionale Warnstufe sind in `alarm_limits.json`
unter `system` konfigurierbar:

```json
{
  "system": {
    "loggerpi_offline_warning_seconds": 1800,
    "loggerpi_offline_critical_seconds": 3600,
    "loggerpi_offline_warning_alert_enabled": false
  },
  "sensors": { ... },
  "states": { ... }
}
```

Solange der LoggerPi als offline gilt (Warnschwelle erreicht), werden die
Sensor- und State-Checks ausgesetzt. Grund: Ohne neue Daten gibt es keine
neuen Grenzwertverletzungen, und die alten Werte sind nicht mehr
vertrauenswürdig. Der einzige Alert in dieser Phase ist der Offline-Alert.

Die Statusleuchte erscheint im Header von Admin und Dashboard. Im Dashboard
wird zusätzlich die Messzeit („Last measurement") angezeigt – das ist die
LoggerPi-Zeit (`created_at`), nicht die Empfangszeit.

### Acknowledge und Resolve

Ein Alert kann zwei unabhängige Zustände haben:

- **Acknowledged:** Der Nutzer hat den Alert gesehen und quittiert. Solange
  der Zustand kritisch bleibt, wird kein weiterer Alert mit demselben
  `dedup_key` gesendet. Erst wenn der Zustand wieder normal wird, wird der
  Alert „entsperrt".
- **Resolved:** Der Zustand, der den Alert ausgelöst hat, ist wieder normal.
  Der Alert bleibt in der History, wird aber als „Resolved" markiert.

Beide Zustände werden in der Alert-Engine automatisch gepflegt:
`reset_acknowledged()` und `resolve()` werden aufgerufen, sobald der Wert
wieder innerhalb der Grenzen ist (bzw. der State wieder normal ist). Der
Admin-Alerts-Tab zeigt den Status als Chip („Active" / „Resolved") und
bietet einen Filter „Only active".

### Message-Templates

Die Alert-Texte werden aus zwei Teilen zusammengesetzt:

- **Regel-Text** (editierbar in `messages.json`, Admin-Tab „Messages"):
  z. B. „too high", „too low", „invalid", „stale", „low", „open".
- **Measurement-Name** (fest im Code, `MEASUREMENT_DISPLAY_NAMES`):
  z. B. „Temperature", „Humidity", „Vacuum", „CO₂", „Battery", „Door".

Die Message wird automatisch gebaut:

```text
R1304 · Culture Room I / Memmert HPP260 · left — Temperature too high: 30.0 °C > 28.0 °C
```

Der Subject ist kürzer:

```text
[CRITICAL] Temperature — R1304 · Culture Room I / Memmert HPP260 · left
```

Raum und Gerät kommen aus `rooms.json`. Wenn ein Sensor nicht zugeordnet ist,
fällt die Message auf den technischen `sensor_key` zurück.

**Bewusst offen:** Door-Open-Dauer (HPP260 unterstützt es nicht), Defrost,
Flap (HPP260 unterstützt es nicht). CSV-Export, Statuspage, Dry-Run, Config-Backup/Restore auf „irgendwann"
verschoben. Alert-Resolve (Active vs. Resolved) und Hysterese sind für einen
späteren Schritt vorgesehen.

---

## Entwicklung

### Voraussetzungen

- Windows 11
- Visual Studio Code
- Python 3.13 (Entwicklung)
- Python 3.9 (minimale Unterstützung)

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --group dev
```

### Quality Gates

```powershell
ruff check .
ruff format --check .
pytest
git diff --check
```

Aktueller Stand: **432 Tests**, alle bestehen.

---

Aktuelle Version: **v1.12.5**

Die Version wird geführt über:

- `pyproject.toml` → `version = "1.12.5"`
- `src/loggerpi_otterpi/__init__.py` → `__version__ = "1.12.5"`
- `src/loggerpi_otterpi/dashboard_constants.py` → `VERSION = "v1.12.5"`
- Git-Tag `v1.12.5`

---

## Dokumentation

Weitere Dokumentation:

```text
docs/PROJECT-STATE.md
docs/system-inventory.md

docs/deployment/DEPLOYMENT.md

docs/development/DEVELOPMENT-ENVIRONMENT.md
docs/development/DEVELOPMENT-QUALITY.md
docs/development/DECISIONS.md

docs/data-model/data-model-v1-field-catalog.md
docs/data-model/core-batch-v1.md
docs/data-model/core-batch-v1-json.md

docs/api/core-batch-api-v1.md
docs/api/core-batch-delivery-v1.md

docs/baselines/LoggerPi_Observer_Technical_Baseline_v4.md
docs/baselines/OtterPi_Technical_Baseline_v1.md
docs/baselines/freezer-log.service

docs/legacy/README.md
docs/legacy/observer.md
docs/legacy/observer.py
```

---

## Lizenz

(Noch nicht festgelegt)