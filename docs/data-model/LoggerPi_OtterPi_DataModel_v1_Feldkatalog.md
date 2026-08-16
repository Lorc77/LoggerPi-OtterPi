# LoggerPi → OtterPi

## Data Model v1 – vollständiger Feldkatalog

**Status:** Feldkatalog abgeschlossen  
**Zweck:** Verbindliche Referenz für die spätere Batch- und API-Struktur  
**Grundprinzip:** Data Model ≠ Core-Batch-Konfiguration

---

## 1. Grundprinzipien

### 1.1 Architektur

```text
LoggerPi
  │
  ├── Systemtelemetrie
  ├── Sensor-/Gerätedaten
  ├── Serial Reader
  ├── AtmoWEB Reader
  └── lokale Zustände
          │
          ▼
      Data Model
          │
          ▼
      Core Batch
          │
          ▼
       OtterPi
          │
          ├── Validierung
          ├── Zustandsbewertung
          ├── Events / Alerts
          └── Dashboard
```

### 1.2 Verantwortlichkeiten

**LoggerPi**

- erfasst Daten
- liest Sensoren/Geräte
- normalisiert Herstellerdaten
- liefert technische Fakten
- liefert Herkunft und Zeitbezug
- überträgt den Batch

**OtterPi**

- bewertet fachliche Gültigkeit
- bewertet Health und Zustände
- erkennt Ausfälle und Zeitlücken
- verarbeitet Events
- stellt Daten im Dashboard dar

### 1.3 Wichtige Trennung

```text
Quelle / Hersteller-API
        ↓
Adapter / Reader
        ↓
gemeinsames Data Model
        ↓
konkrete Batch-Konfiguration
        ↓
tatsächliche Übertragung
```

Nicht jedes Feld des Data Models muss Bestandteil des regelmäßigen Core-Batches sein.

---

## 2. Batch Envelope

Der äußere Rahmen eines Batches enthält die Identität und Reihenfolge der Übertragung.

```text
batch
├── schema_version
├── batch_id
├── logger_id
├── sequence
├── created_at
└── ...
```

### Felder

| Feld | Typ | Bedeutung |
|---|---|---|
| `schema_version` | string | Version des Data Models |
| `batch_id` | string | eindeutige Identität dieses Batches |
| `logger_id` | string | eindeutige Identität des LoggerPi |
| `sequence` | integer | fortlaufende Batch-Nummer des jeweiligen LoggerPi |
| `created_at` | datetime | Zeitpunkt der Batch-Erstellung |

### Sequence-Regel

`sequence` ist pro LoggerPi fortlaufend.

Damit können gleiche Sequenznummern verschiedener LoggerPis problemlos unterschieden werden:

```text
loggerpi-01 / 1842
loggerpi-02 / 1842
```

sind zwei unterschiedliche Batches.

## 3. Zeitmodell

Zeitangaben müssen semantisch getrennt bleiben.

### Vorgesehene Zeitfelder

- `created_at`
- `measured_at`
- `received_at`

### Bedeutung

**`measured_at`**

Zeitpunkt, zu dem ein Messwert tatsächlich erfasst wurde.

**`created_at`**

Zeitpunkt, zu dem der LoggerPi den Batch erzeugt hat.

**`received_at`**

Zeitpunkt, zu dem der OtterPi den Batch empfangen hat.

Diese Zeiten dürfen nicht miteinander vermischt werden.

---

## 4. System / Identity

`system.identity`

### Felder

- `hostname`
- `hardware.model`
- `hardware.revision`
- `hardware.cpu_cores`
- `os.name`
- `os.version`
- `os.codename`
- `kernel.release`

### Beispiel

```text
system.identity.hostname
system.identity.hardware.model
system.identity.hardware.revision
system.identity.hardware.cpu_cores
system.identity.os.name
system.identity.os.version
system.identity.os.codename
system.identity.kernel.release
```

### Hinweis

RAM wird **nicht** als Hardware-Metadatum geführt.

Die tatsächliche Speicherkapazität kommt aus:

`memory.total_bytes`

## 5. System / Time

`system.time`

### Felder

- `current`
- `timezone`
- `clock_state`

### Bedeutung

**`current`**

Aktuelle LoggerPi-Zeit.

**`timezone`**

Zeitzone des Systems.

**`clock_state`**

Zustand der Systemuhr bzw. Zeitsynchronisation.

---

## 6. System / Boot

`system.boot`

### Felder

- `last_boot_at`
- `uptime_seconds`

### Bewusste Entscheidung

Kein separates:

`reboot_detected`

Der OtterPi kann einen Neustart erkennen, wenn sich:

`last_boot_at`

gegenüber dem vorherigen bekannten Zustand verändert.

---

## 7. System / CPU

`system.cpu`

### Auslastung

- `usage_percent`

### Load

- `load.1m`
- `load.5m`
- `load.15m`

### Frequenz

- `frequency.current_hz`
- `frequency.max_hz`

### Temperatur

- `temperature`

### Throttling / Hardwarezustände

- `throttling.undervoltage`
- `throttling.frequency_capped`
- `throttling.throttled`
- `throttling.temperature_limit`

### Einordnung

CPU-Auslastung und Temperatur sind Measurements.

Die Throttling-Werte sind **States**, keine Measurements.

## 8. System / Memory

`memory`

### Rohwerte

- `total_bytes`
- `used_bytes`
- `available_bytes`

### Abgeleiteter Wert

- `used_percent`

Das Grundprinzip lautet:

**Rohdaten möglichst erhalten; abgeleitete Werte dürfen zusätzlich übertragen werden.**

---

## 9. System / Swap

`swap`

### Technische Eigenschaften

- `device`
- `type`
- `state`

### Speicherwerte

- `total_bytes`
- `used_bytes`
- `available_bytes`
- `used_percent`

### Beispiel

```text
device = /dev/zram0
type   = zram
state  = active
```

---

## 10. System / Storage

Storage wird bewusst in **physisches Medium** und **Dateisysteme** getrennt.

### 10.1 Physische Devices

`storage.devices[]`

### Felder

- `device`
- `model`
- `type`
- `manufactured_at`

`manufactured_at` ist optional.

### Beispiel

```text
device = /dev/mmcblk0
model  = SN64G
type   = sd
```

### 10.2 Filesystems

`storage.filesystems{}`

Pro Mountpoint:

- `device`
- `filesystem`
- `mount_state`
- `total_bytes`
- `used_bytes`
- `available_bytes`
- `used_percent`
- `inodes_used_percent`

### Beispiel

```text
/
├── device
├── filesystem
├── mount_state
├── total_bytes
├── used_bytes
├── available_bytes
├── used_percent
└── inodes_used_percent
```

---

## 11. System / Processes

Im Core zunächst bewusst nur aggregiert:

`system.processes.total`

### Beispiel

```text
system.processes.total = 192
```

### Nicht Bestandteil des Core-Feldkatalogs

- PID-Liste
- Prozessnamen
- CPU-Verbrauch jedes Prozesses
- Memory-Verbrauch jedes Prozesses
- vollständige Prozessliste

Das wäre gegebenenfalls spätere Diagnoseinformation.

## 12. Network / Interfaces

`network.interfaces{}`

Pro Interface:

- `state`
- `blocked`
- `mac`
- `addresses[]`

### Beispiele

- `eth0`
- `wlan0`

### Beispielhafte Zustände

- `up`
- `down`

`blocked` beschreibt beispielsweise einen administrativ/radioseitig blockierten Zustand.

Damit ist auch ein Dashboard-Eintrag wie:

**WLAN (wlan0): blockiert**

im Bereich Network / Interfaces abbildbar.

---

## 13. Network / Routing

`network.routing`

### Feld

- `default_gateway`

---

## 14. Network / DNS

`network.dns`

### Feld

- `servers[]`

---

## 15. Connectivity / Upload

Der LoggerPi soll den technischen Übertragungszustand nachvollziehbar machen.

Vorgesehen sind insbesondere Informationen zu:

- `upload`
- `queue`

Die genaue endgültige Unterstruktur wird beim späteren Batch-/API-Design festgelegt.

### Grundprinzip

Ein erfolgreicher Upload zum OtterPi ist bereits ein praktischer Connectivity-Nachweis.

Deshalb keine permanenten redundanten:

- `ping`
- DNS-Test
- HTTPS-Test

nur um Connectivity zu beweisen.

Aktive Tests sind später bei gezielter Diagnose möglich.

---

## 16. Services

`services.<service_id>`

Services werden dynamisch modelliert.

### Felder

- `name`
- `purpose`
- `state`
- `enabled`
- `pid`
- `started_at`
- `last_state_change_at`

Nicht jeder Dienst muss zwangsläufig jedes Feld liefern.

---

## 17. Service State

### Mögliche Zustände

- `running`
- `stopped`
- `failed`
- `starting`
- `stopping`
- `unknown`

Der LoggerPi liefert den technischen Zustand.

Der OtterPi bewertet dessen Bedeutung für Health/Dashboard.

## 18. Autostart

Autostart-Information wird bewusst von einem laufenden Service getrennt.

Konzeptionell:

`autostart`

mit Informationen darüber, ob ein Dienst beim Boot gestartet werden soll.

### Beispielhafte Semantik

```text
enabled = true
state = stopped
```

→ Dienst sollte laufen, läuft aber nicht.

Oder:

```text
enabled = false
state = running
```

→ läuft momentan, wird aber nicht automatisch gestartet.

---

## 19. Timer / Cron

Timer und Cron sind wiederum eine eigene Kategorie.

Sie beantworten:

**Was wird zeitgesteuert ausgeführt?**

und nicht:

**Was läuft gerade?**

Ein vollständiger Linux-Cron-Dump gehört **nicht** in den Core-Batch.

---

## 20. Measurements – gemeinsames Schema

Physikalische Messwerte folgen grundsätzlich demselben Muster:

- `value`
- `unit`
- `measured_at`
- `validity`
- `source`

### Beispiel

```json
{
  "value": 23.1,
  "unit": "celsius",
  "measured_at": "2026-08-15T10:42:10+02:00",
  "validity": "valid",
  "source": "..."
}
```

### Grundsatz

Hersteller-/Quellenbezeichnungen werden nicht einfach in das gemeinsame Data Model übernommen.

---

## 21. Validity

## 21. Validity

`validity` beschreibt den technischen bzw. datenseitigen Zustand eines
übertragenen Measurements.

`validity` ist keine fachliche Health- oder Alarmbewertung.

### Zulässige Zustände

  * `valid`
  * `invalid`
  * `unavailable`
  * `unknown`
  * `stale`

### Semantik

`valid`

Der Messwert wurde erfolgreich erfasst und kann technisch als Messwert
verwendet werden.

`invalid`

Ein Messwert wurde grundsätzlich erkannt, kann aber technisch nicht
zuverlässig als gültiger Messwert verwendet werden.

`unavailable`

Die erwartete Messgröße ist aktuell nicht verfügbar.

`unknown`

Der technische Zustand des Messwertes kann nicht zuverlässig bestimmt
werden.

`stale`

Ein zuvor verfügbarer Messwert ist vorhanden, aber älter als der für die
betreffende Messgröße zulässige Aktualitätszeitraum.

### Value-Konsistenz

Für Measurements gilt:

  * `valid` → `value` ist nicht `null`
  * `invalid` → `value` ist `null`
  * `unavailable` → `value` ist `null`
  * `unknown` → `value` ist `null`
  * `stale` → `value` ist nicht `null`

Bei `stale` bleiben der letzte bekannte Wert und sein tatsächliches
`measured_at` erhalten.

### Verantwortlichkeiten

Der LoggerPi liefert:

  * den erfassten Wert bzw. `null`
  * die Quelle
  * die technische Validity
  * den Zeitbezug

Der OtterPi bewertet daraus:

  * fachliche Health
  * Grenzwertverletzungen
  * Alarme
  * fachliche Kritikalität

Damit bedeutet beispielsweise:

`value = -60`
`validity = valid`

dass der Messwert technisch gültig übertragen wurde.

Ob `-60 °C` fachlich unkritisch oder alarmwürdig ist, entscheidet der
OtterPi anhand der jeweiligen fachlichen Regeln.

### AtmoWEB N/A

Wenn AtmoWEB beispielsweise:

`CO2Read = N/A`

liefert, wird dies als:

```text
value = null
validity = unavailable
```

abgebildet.

Insbesondere niemals:

```text
value = 0
validity = valid
```

## 22. Derived Measurements

Abgeleitete Werte sind zulässig.

### Beispiele

- `used_percent`
- `inodes_used_percent`

Sie dürfen übertragen werden, obwohl sie aus Rohdaten berechnet werden.

Rohdaten sollen, wo sinnvoll, zusätzlich vorhanden sein.

---

## 23. Serial

Der Freezer wird über RS-232 angebunden.

### Technische Parameter

```text
baud: 1200
data_bits: 8
start_bits: 1
stop_bits: 2
parity: none
```

Diese statischen Kommunikationsparameter müssen nicht bei jedem Batch übertragen werden.

---

## 24. Serial State

### Felder

- `serial.device`
- `serial.state`

### Zustände

- `connected`
- `degraded`
- `disconnected`
- `unknown`

### Definition

**`connected`**

`/dev/ttyUSB0` vorhanden

**und**

erwarteter Datenempfang funktioniert.

**`degraded`**

`/dev/ttyUSB0` vorhanden

aber erwarteter Empfang bleibt aus.

**`disconnected`**

`/dev/ttyUSB0` nicht vorhanden.

**`unknown`**

Zustand nicht zuverlässig bestimmbar.

---

## 25. Serial Diagnostics

Vorgesehen:

- `serial.last_rx_at`
- `serial.seconds_since_rx`
- `serial.lines_received`
- `serial.parse_errors`
- `serial.reconnect_count`

Diese Informationen sind **Health-/Diagnosedaten**.

Sie sind keine Freezer-Messwerte.

---

## 26. Freezer Temperature

Der tatsächlich aus dem RS-232-Protokoll gelesene Temperaturwert wird in das gemeinsame Measurement-Modell übersetzt.

`freezer.temperature`

mit:

- `value`
- `unit`
- `measured_at`
- `validity`
- `source`

---

## 27. Freezer Protocol Errors

Das Protokoll kann beispielsweise liefern:

- `UNDERTEMP`
- `OVERTEMP`
- `PWRFAIL`
- `CNTRFAIL`
- `Er07`
- `HSHX FAIL`
- `HOT COND`

sowie:

`T_ERR`

bei bestimmten fehlerhaften Temperaturwerten.

Diese Informationen sind **Events/Fehlerzustände**, nicht einfach normale Temperaturwerte.

## 28. Freezer Events / Alarms

Für solche Ereignisse ist ein separater Event-/Alarmbereich vorgesehen.

Beispielsweise:

`events[]`

Die genaue Event-Struktur wird beim nächsten Arbeitsschritt definiert.

---

## 29. AtmoWEB Measurements

Aus der AtmoWEB-API bekannte Messwerte:

- `Temp1Read`
- `Temp2Read`
- `Temp3Read`
- `Temp4Read`
- `HumRead`
- `VacRead`
- `CO2Read`
- `O2Read`
- `FanRead`

Diese werden auf fachliche Felder abgebildet.

---

## 30. AtmoWEB → Data Model Mapping

Beispiele:

```text
Temp1Read
    ↓
measurements.temperature_1
```

```text
HumRead
    ↓
measurements.humidity
```

```text
VacRead
    ↓
measurements.vacuum
```

```text
CO2Read
    ↓
measurements.co2
```

```text
O2Read
    ↓
measurements.o2
```

```text
FanRead
    ↓
measurements.fan_speed
```

Die endgültige Benennung und Gruppierung wird beim konkreten Batch-Schema noch einmal geprüft.

---

## 31. AtmoWEB N/A

Wenn AtmoWEB beispielsweise:

`CO2Read = N/A`

liefert, darf daraus **nicht**

`0`

werden.

Stattdessen beispielsweise:

```json
{
  "value": null,
  "validity": "unavailable"
}
```

Damit bleibt die Bedeutung erhalten:

**kein verfügbarer Messwert**

und nicht:

**Messwert ist 0.**

## 32. AtmoWEB States

Bekannte States:

- `DoorOpen`
- `DoorLock`
- `LightDay`
- `LightUV`
- `LightLED`
- `SwASet`
- `SwBSet`
- `SwCSet`
- `SwDSet`
- `FlapSet`
- `Defrost`

Diese werden als States und nicht als normale physikalische Measurements behandelt.

---

## 33. Fachliche State-Namen

Beispielsweise:

```text
states.door_open
states.door_locked

states.light_day
states.light_uv
states.light_led

states.switches

states.flap
states.defrost
```

Die Typisierung der States ist im Core-Batch-JSON verbindlich festgelegt.

Die Boolean-States sind:

  * `states.door_open`
  * `states.door_locked`
  * `states.flap`
  * `states.defrost`

Die gruppierten Licht-States sind:

  * `states.lights.day`
  * `states.lights.uv`
  * `states.lights.led`

Die gruppierten Switch-States sind:

  * `states.switches.a`
  * `states.switches.b`
  * `states.switches.c`
  * `states.switches.d`

Diese States sind vom Typ `boolean`.

Nicht vorhandene, fachlich nicht unterstützte Switches dürfen weggelassen
werden.

`null` wird nicht als Ersatz für einen fehlenden State verwendet.

---

## 34. AtmoWEB Operation

AtmoWEB:

`CurOp`

wird als Betriebszustand modelliert.

`operation.mode`

### Mapping

| AtmoWEB | Data Model |
|---|---|
| `Program` | `program` |
| `Idle` | `idle` |
| `Timer` | `timer` |
| `Manual` | `manual` |

---

## 35. Device Metadata

AtmoWEB liefert:

- `SN`
- `DevType`
- `SWRev`

### Fachliche Zuordnung

- `device.serial_number`
- `device.device_type`
- `device.software_revision`

Diese Werte ändern sich normalerweise selten.

Sie müssen deshalb nicht zwangsläufig in jedem Core-Batch vollständig wiederholt werden.

---

## 36. Setpoints

Konzeptioneller Bereich:

`setpoints`

### Vorgesehen

- `temperature`
- `humidity`
- `vacuum`
- `co2`
- `o2`
- `fan`

Setpoints sind **keine Measurements**.

Sie sind Konfigurations-/Sollwerte.

Sie gehören zunächst **nicht automatisch in den Core-Batch v1**.

## 37. Alarm Limits

Konzeptioneller Bereich:

`alarm_limits`

### Vorgesehen

- `temperature`
- `humidity`
- `vacuum`
- `co2`
- `o2`

Auch diese sind keine Measurements.

Sie sind Grenz-/Konfigurationswerte.

---

## 38. Programming / Program Information

Aus AtmoWEB bekannte Informationen:

- `InfoTemp`
- `InfoHum`
- `InfoVac`
- `InfoMsg`
- `Info`
- `ProgStart`
- `ProgStop`
- `ProgExit`
- `ProgCurrent`
- `ProgDuration`
- `ProgRemain`
- `ProgList`
- `ProgLoad`
- `ProgDelete`

Diese Daten werden **nicht automatisch in den Core-Batch übernommen**.

Sie gehören konzeptionell in einen späteren Bereich für Programm-/Betriebsinformationen.

---

## 39. AtmoWEB LOG.TXT

`LOG.TXT` enthält beispielsweise:

- `Door open`
- `Restart`
- `Start: MyProgram`
- `End: MyProgram`
- `Temp. max alarm`

Diese Informationen werden als **Events** betrachtet.

Nicht als:

- Measurement
- Health

---

## 40. Events

Konzeptioneller Bereich:

`events[]`

### Mögliche Quellen

- `freezer`
- `serial`
- `atmoweb`
- `logger`
- `service`
- `connectivity`
- `system`

### Mögliche Ereignisse

- `alarm`
- `restart`
- `service_failure`
- `connectivity_change`
- `device_event`

Die endgültige Event-Struktur ist Bestandteil des nächsten Arbeitsschrittes.

## 41. Metadata

Metadata umfasst selten veränderliche Informationen wie beispielsweise:

- Hardware
- OS
- Kernel
- Device Serial Number
- Device Type
- Software Revision
- Storage Model

### Wichtig

Metadata muss nicht zwangsläufig in jedem regulären Batch vollständig wiederholt werden.

Wenn sich Metadata ändert, muss die Änderung aber über den normalen LoggerPi → OtterPi Kommunikationsweg beim OtterPi ankommen.

Der OtterPi soll **nicht** darauf angewiesen sein, den LoggerPi aktiv erreichen zu können.

---

## 42. Erweiterbare Sensorik

Neue Sensoren können später über Adapter eingebunden werden.

```text
AtmoWEB ───────┐
Modbus ────────┤
MQTT ──────────┼──> gemeinsames Data Model
Serial ────────┤
Sensor X ──────┘
```

Der jeweilige Adapter übersetzt die Quellstruktur in die gemeinsamen fachlichen Felder.

Damit muss das Data Model nicht für jeden Hersteller neu erfunden werden.

---

## 43. Kein misc

Bewusst nicht vorgesehen:

- `measurements.misc`
- `states.misc`

### Begründung

Ein `misc`-Feld würde schnell zum unspezifizierten Auffangbecken werden und die Semantik des Data Models verschlechtern.

Wenn künftig wirklich nicht standardisierte Daten benötigt werden, soll dafür ein **expliziter Erweiterungsmechanismus** definiert werden.

---

## 44. Data Model ≠ Batch

Ein Feld darf im Data Model vorhanden sein, ohne regelmäßig übertragen zu werden.

### Beispiel

`vacuum`

kann grundsätzlich unterstützt werden.

Der konkrete Sensor kann aber:

`VacRead = N/A`

liefern.

Oder Vacuum wird im normalen Core-Batch zunächst überhaupt nicht abgefragt.

Das ist kein Widerspruch.

## 45. Data Model ≠ Hersteller-API

Herstellerfelder bleiben auf Adapter-/Reader-Ebene.

Beispiel:

Temp1Read

ist kein universelles Data-Model-Feld.

Das universelle Modell kennt beispielsweise:

temperature_1

Damit können unterschiedliche Quellen dasselbe fachliche Feld bedienen.

## 46. Einheiten

Einheiten werden zentral und einheitlich verwendet.

Grundprinzip:

- temperature → celsius
- humidity → percent
- pressure → pascal / definierte Druckeinheit
- co2 → definierte Konzentrationseinheit
- o2 → definierte Konzentrationseinheit
- frequency → hz
- memory → bytes
- time → seconds

Die für den Core Batch v1 verbindlich verwendeten Units sind in der
Core-Batch-JSON-Definition festgelegt.

Weitere Units außerhalb des Core Batch werden bei der jeweiligen späteren
Schema-Definition ergänzt.

Units werden nicht durch einzelne Hersteller-APIs bestimmt, sondern durch
das gemeinsame Data Model.

## 47. Core-Batch-Prinzip

Der regelmäßige Core-Batch soll nur die für den laufenden Betrieb sinnvollen Informationen enthalten.

### Nicht automatisch

- vollständige Hersteller-API
- sämtliche Linux-Sensoren
- Prozesslisten
- vollständige Cron-Konfiguration
- seltene Metadata bei jedem Durchlauf
- redundante Connectivity-Tests
- unstrukturierte misc-Daten

### Aber

- ausreichend Systemdaten
- relevante Health-Daten
- relevante Services
- relevante Sensorwerte
- relevante Geräte-/Serial-Zustände
- notwendige Upload-/Queue-Informationen

## 48. Connectivity-Prinzip

Wir vermeiden unnötige aktive Tests.

Nicht standardmäßig bei jedem Batch:

- ping
- DNS lookup
- HTTPS test

wenn die reguläre Übertragung selbst bereits den Kommunikationsweg bestätigt.

Das entspricht dem übergeordneten Projektprinzip:

**So wenig Tests wie möglich, aber so viele Informationen wie für einen zuverlässigen Betrieb tatsächlich nötig sind.**

## 49. Spätere Queue-/Disconnect-Logik

Noch nicht Bestandteil des endgültigen Feldschemas, aber konzeptionell vorgesehen:

```text
LoggerPi offline
      ↓
lokale Queue
      ↓
Verbindung wieder verfügbar
      ↓
Batches nachliefern
      ↓
OtterPi verarbeitet Sequenzen und Zeitstempel
```

Dabei müssen insbesondere:

- `sequence`
- `created_at`
- `measured_at`
- `received_at`

sauber auseinandergehalten werden.

## 50. Feldkatalog – Kategorienübersicht

Damit ergibt sich aktuell folgende Gesamtstruktur:

```text
batch
│
├── Envelope
│   ├── schema_version
│   ├── batch_id
│   ├── logger_id
│   ├── sequence
│   └── created_at
│
├── system
│   ├── identity
│   ├── time
│   ├── boot
│   ├── cpu
│   ├── processes
│   └── ...
│
├── memory
│
├── swap
│
├── storage
│   ├── devices
│   └── filesystems
│
├── network
│   ├── interfaces
│   ├── routing
│   └── dns
│
├── connectivity
│   ├── upload
│   └── queue
│
├── services
│
├── autostart
│
├── timers
│
├── serial
│   ├── state
│   └── diagnostics
│
├── freezer
│   └── temperature
│
├── measurements
│   ├── temperature_1
│   ├── temperature_2
│   ├── temperature_3
│   ├── temperature_4
│   ├── humidity
│   ├── vacuum
│   ├── co2
│   ├── o2
│   └── fan_speed
│
├── states
│   ├── door_open
│   ├── door_locked
│   ├── lights
│   ├── switches
│   ├── flap
│   └── defrost
│
├── operation
│   └── mode
│
├── device
│   ├── serial_number
│   ├── device_type
│   └── software_revision
│
├── setpoints
│
├── alarm_limits
│
├── programming
│
├── events[]
│
└── metadata
```

## 51. Abgeschlossene Entscheidungen

Folgende Punkte gelten als entschieden:

- LoggerPi erfasst Fakten, OtterPi bewertet sie.
- Data Model und tatsächlicher Batch sind getrennt.
- Hersteller-API-Namen werden nicht zu universellen Feldnamen.
- Measurements, States, Health, Metadata, Configuration und Events werden getrennt.
- Rohwerte und sinnvolle abgeleitete Werte dürfen gemeinsam übertragen werden.
- `validity` gehört zum Messwertmodell.
- `system.processes.total` reicht zunächst für den Core.
- Keine Prozessliste im regulären Batch.
- Netzwerkinterfaces gehören in `network.interfaces`.
- `wlan0` `blocked` gehört dort hinein.
- Keine unnötigen aktiven Connectivity-Tests.
- Services sind dynamisch erweiterbar.
- Serial und Freezer werden getrennt von allgemeinen Measurements betrachtet.
- AtmoWEB `N/A` wird niemals als `0` interpretiert.
- Setpoints sind keine Measurements.
- Alarmgrenzen sind keine Measurements.
- LOG-/Alarminformationen sind Events.
- Metadata ist von regelmäßigen Messdaten getrennt.
- `measurements.misc` wird nicht vorgesehen.
- `states.misc` wird nicht vorgesehen.
- Neue Sensoren werden über Adapter in das gemeinsame Modell überführt.
- `sequence` ist pro LoggerPi fortlaufend.
- LoggerPi-Identität und Sequence werden gemeinsam betrachtet.
- Metadata-Änderungen müssen über den normalen Uploadweg beim OtterPi ankommen.
- Der OtterPi soll den LoggerPi nicht aktiv erreichen müssen.
- Der Core-Batch soll schlank bleiben.

## 52. Was ausdrücklich noch NICHT abgeschlossen ist

Der Feldkatalog selbst ist abgeschlossen.

Die daraus abgeleiteten Core-Batch-, JSON-, API- und Delivery-Definitionen
sind inzwischen separat dokumentiert.

Noch nicht abgeschlossen sind insbesondere:

- vollständiges Metadata-Change-/Synchronisationsprotokoll
- Event-Schema
- Authentication
- Schema-Versionierung
- Routing-/DNS-Platzierung
- Behandlung statischer Netzwerk-/Storage-Metadata
- genaue technische Umsetzung der Legacy-Ablösung
- finale Zuordnung weiterer Runtime-Komponenten zum neuen Service-Modell

Damit bleibt der Feldkatalog die verbindliche Data-Model-Referenz, ohne
bereits offene nachgelagerte Designbereiche vorwegzunehmen.
