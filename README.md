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
| `src/loggerpi_otterpi/dashboard.py` | Dashboard (Charts, 48h) |
| `src/loggerpi_otterpi/dashboard_config.py` | Dashboard-Konfiguration (Raum- und Sensor-Zuordnung) |

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

### Aktueller Betriebsstand (2026-10-28)

| System | Version | Status |
|--------|---------|--------|
| LoggerPi | `v1.7.0` | Läuft, sendet Batches alle 15 Minuten |
| OtterPi | `v1.7.0` | Empfängt Batches, speichert in SQLite |

Der E2E-Datenpfad (LoggerPi → nginx → OtterPi → SQLite) ist verifiziert.

Dashboard: `https://zoology.makki.route64.de`
Authentication: Bearer Token (seit v1.1.0)

Datenquellen:
- AtmoWEB 101/102 (MEMMERT HPP260) ✅
- Freezer (HFC-Serie, direkt Serial) ✅
- MEMMERT IPP300 links/rechts ✅
- ThingSpeak-Injektion (field1–7) ✅
- WeatherHub Sensoren (Gateway Proxy, 17 Sensoren) ✅

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

Aktueller Stand: **189 Tests**, alle bestehen.

---

Aktuelle Version: **v1.7.0**

Die Version wird geführt über:

- `pyproject.toml` → `version = "1.7.0"`
- `src/loggerpi_otterpi/__init__.py` → `__version__ = "1.7.0"`
- `src/loggerpi_otterpi/dashboard.py` → `VERSION = "v1.7.0"`
- Git-Tag `v1.7.0`

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