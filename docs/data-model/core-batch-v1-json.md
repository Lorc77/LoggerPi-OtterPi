# LoggerPi → OtterPi

## Core Batch v1 — JSON Definition

**Data Model:** v1  
**Core Batch:** v1  
**Status:** technische Definition  
**Basis:** `core-batch-v1.md` und `LoggerPi_OtterPi_DataModel_v1_Feldkatalog.md`

---

## 1. Zweck

Dieses Dokument definiert die konkrete JSON-Repräsentation des
Core Batch v1.

Der fachliche Umfang des Core Batch ist in:

```text
docs/data-model/core-batch-v1.md
```

definiert.

Der zugrunde liegende fachliche Feldkatalog ist:

```text
docs/data-model/LoggerPi_OtterPi_DataModel_v1_Feldkatalog.md
```

Dieses Dokument konkretisiert insbesondere:

- JSON-Struktur
- Datentypen
- Pflicht- und optionale Felder
- `null`-Semantik
- `validity`-Semantik
- Zeitformat
- Einheiten
- Enumerationen
- Wertebereiche, soweit bereits fachlich festgelegt

Dieses Dokument definiert noch nicht:

- HTTP-Endpunkte
- Authentication
- Retry-Mechanismus
- Duplicate Handling
- lokale Queue-Implementierung
- Metadata-Change-Protokoll
- Event-Protokoll

---

## 2. Grundregeln

### 2.1 JSON

Der Core Batch wird als einzelnes JSON-Objekt übertragen.

JSON-Felder verwenden `snake_case`.

Dynamische Schlüssel wie Interface-Namen, Mountpoints oder Service-IDs
werden als Objekt-Schlüssel verwendet.

Unbekannte zusätzliche Felder dürfen nicht stillschweigend als Bestandteil
des definierten Data Models interpretiert werden.

### 2.2 Pflicht und optional

Ein Feld ist `required`, wenn es für die eindeutige Interpretation des
jeweiligen Objekts erforderlich ist.

Ein Feld ist `optional`, wenn es vollständig fehlen darf.

`optional` bedeutet nicht automatisch `nullable`.

Ein optionales Feld darf daher grundsätzlich in zwei unterschiedlichen
Zuständen auftreten:

```text
Feld vorhanden
    → Wert gemäß Definition

Feld nicht vorhanden
    → für dieses Objekt wurde kein Wert übertragen
```

Ein fehlendes optionales Feld darf nicht automatisch als `null`,
`unknown`, `unavailable`, `invalid` oder als Defaultwert interpretiert
werden.

### 2.3 Keine impliziten Defaultwerte

Insbesondere gilt:

```text
fehlend ≠ 0
fehlend ≠ false
fehlend ≠ ""
fehlend ≠ null
fehlend ≠ valid
```

Ein Defaultwert ist nur zulässig, wenn er für das konkrete Feld ausdrücklich
definiert ist.

### 2.4 Technische Fakten und fachliche Bewertung

Der LoggerPi liefert technische Daten und Zustände.

Der Core Batch enthält keine globale Health-Bewertung.

Insbesondere bedeuten technische Zustände oder `validity`-Werte nicht
automatisch:

- `healthy`
- `warning`
- `critical`
- `alarm`

Die fachliche Bewertung erfolgt auf dem OtterPi.

---

# 3. Datentypen

| Bezeichnung | JSON-Typ | Bedeutung |
|---|---|---|
| String | `string` | Text oder definierter Enum-Wert |
| Integer | `integer` | Ganzzahl |
| Number | `number` | numerischer Wert |
| Boolean | `boolean` | `true` oder `false` |
| Object | `object` | strukturiertes JSON-Objekt |
| Array | `array` | geordnete Liste |
| Null | `null` | ausdrücklich erlaubter Nullwert |

Ein Feld darf nur dann mehrere JSON-Typen akzeptieren, wenn dies in diesem
Dokument ausdrücklich definiert ist.

---

# 4. Zeitformat

Alle absoluten Zeitstempel werden als ISO-8601-kompatible Zeitstempel mit
Zeitzoneninformation übertragen.

Beispiel:

```text
2026-08-15T10:45:00+02:00
```

Zeitstempel ohne Zeitzoneninformation sind für absolute Zeitpunkte im
Core Batch nicht zulässig.

## 4.1 Zeitfelder

### `created_at`

Zeitpunkt der Erzeugung des Batches auf dem LoggerPi.

Typ:

```text
string
```

Format:

```text
ISO-8601 datetime with timezone
```

Required:

```text
ja
```

Nullable:

```text
nein
```

### `measured_at`

Zeitpunkt der tatsächlichen Erfassung eines Messwertes.

Typ:

```text
string | null
```

Required:

```text
ja
```

Nullable:

```text
ja
```

`null` ist zulässig, wenn für den betreffenden Measurement-Zustand kein
zuverlässiger Messzeitpunkt vorhanden ist.

### `received_at`

`received_at` gehört nicht zum vom LoggerPi erzeugten Core Batch.

Es wird ausschließlich auf dem OtterPi beim Empfang bestimmt.

Es darf daher nicht Bestandteil des LoggerPi-Core-Batch-JSON sein.

---

# 5. Batch Envelope

Der Core Batch verwendet den bereits im Data Model definierten
Batch Envelope.

Struktur:

```text
batch
├── schema_version
├── batch_id
├── logger_id
├── sequence
└── created_at
```

## 5.1 `schema_version`

Typ:

```text
string
```

Required:

```text
ja
```

Nullable:

```text
nein
```

Bedeutung:

Version des Data Models bzw. des verwendeten Batch-Schemas.

Für Core Batch v1 wird verwendet:

```json
"schema_version": "1.0"
```

## 5.2 `batch_id`

Typ:

```text
string
```

Required:

```text
ja
```

Nullable:

```text
nein
```

`batch_id` identifiziert genau diesen fachlichen Batch.

Das konkrete interne Format der ID wird in diesem Dokument nicht weiter
eingeschränkt.

## 5.3 `logger_id`

Typ:

```text
string
```

Required:

```text
ja
```

Nullable:

```text
nein
```

`logger_id` identifiziert den LoggerPi.

## 5.4 `sequence`

Typ:

```text
integer
```

Required:

```text
ja
```

Nullable:

```text
nein
```

`sequence` ist die persistente, pro LoggerPi monotone Batch-Nummer.

Ein Retry erzeugt keinen neuen Batch.

Damit bleiben bei einem Retry erhalten:

```text
batch_id
sequence
created_at
```

## 5.5 `created_at`

Typ:

```text
string
```

Required:

```text
ja
```

Nullable:

```text
nein
```

Siehe Abschnitt 4.

---

# 6. Top-Level-Struktur

Die fachliche Struktur des Core Batch ist:

```text
batch
├── schema_version
├── batch_id
├── logger_id
├── sequence
├── created_at
├── system
├── memory
├── swap
├── storage
├── network
├── connectivity
├── services
├── serial
├── freezer
├── measurements
├── states
└── operation
```

Die Envelope-Felder sind `required`.

Die fachlichen Top-Level-Bereiche sind grundsätzlich `optional`, sofern
für den jeweiligen Bereich keine verwertbaren Daten vorliegen.

Ein Bereich darf nicht durch einen künstlichen Defaultwert ersetzt werden.

Beispielsweise bedeutet:

```text
kein swap-Objekt
```

nicht automatisch:

```text
swap.state = inactive
```

wenn dieser Zustand nicht tatsächlich festgestellt wurde.

---

# 7. System

## 7.1 `system`

Typ:

```text
object
```

Required:

```text
optional
```

Nullable:

```text
nein
```

Wenn `system` vorhanden ist, gelten die folgenden Unterstrukturen.

---

## 7.2 `system.time`

```text
system.time
├── current
├── timezone
└── clock_state
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `current` | string datetime | ja | nein |
| `timezone` | string | ja | nein |
| `clock_state` | string | ja | nein |

`clock_state` beschreibt den technischen Zustand der Systemuhr bzw.
Zeitsynchronisation.

Die konkrete Enum-Liste für `clock_state` wird durch die tatsächlich
verwendete LoggerPi-Zeitquelle bestimmt.

---

## 7.3 `system.boot`

```text
system.boot
├── last_boot_at
└── uptime_seconds
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `last_boot_at` | string datetime | ja | nein |
| `uptime_seconds` | integer | ja | nein |

`uptime_seconds` muss größer oder gleich `0` sein.

Ein separates `reboot_detected` wird nicht übertragen.

---

## 7.4 `system.cpu`

```text
system.cpu
├── usage_percent
├── load
│   ├── 1m
│   ├── 5m
│   └── 15m
├── frequency
│   ├── current_hz
│   └── max_hz
├── temperature
└── throttling
    ├── undervoltage
    ├── frequency_capped
    ├── throttled
    └── temperature_limit
```

### `usage_percent`

Typ:

```text
number
```

Bereich:

```text
0 <= value <= 100
```

### `load.1m`, `load.5m`, `load.15m`

Typ:

```text
number
```

Die Werte repräsentieren die jeweiligen System-Load-Averages.

### `frequency.current_hz`

Typ:

```text
integer
```

Einheit:

```text
hertz
```

### `frequency.max_hz`

Typ:

```text
integer
```

Einheit:

```text
hertz
```

### `temperature`

`temperature` folgt dem Measurement-Modell.

Siehe Abschnitt 15.

### `throttling`

Alle vier Felder sind:

```text
boolean
```

Required innerhalb von `throttling`:

```text
ja
```

Nullable:

```text
nein
```

Felder:

```text
undervoltage
frequency_capped
throttled
temperature_limit
```

Diese Werte sind States und keine Measurements.

---

## 7.5 `system.processes`

```text
system.processes
└── total
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `total` | integer | ja | nein |

`total` muss größer oder gleich `0` sein.

Eine vollständige Prozessliste ist nicht Bestandteil des Core Batch.

---

# 8. Memory

```text
memory
├── total_bytes
├── used_bytes
├── available_bytes
└── used_percent
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `total_bytes` | integer | ja | nein |
| `used_bytes` | integer | ja | nein |
| `available_bytes` | integer | ja | nein |
| `used_percent` | number | optional | nein |

Alle Byte-Werte müssen größer oder gleich `0` sein.

`used_percent` ist ein abgeleiteter Wert.

Wenn übertragen:

```text
0 <= used_percent <= 100
```

Rohwerte haben Vorrang gegenüber dem abgeleiteten Prozentwert.

---

# 9. Swap

```text
swap
├── device
├── type
├── state
├── total_bytes
├── used_bytes
├── available_bytes
└── used_percent
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `device` | string | ja | nein |
| `type` | string | ja | nein |
| `state` | string | ja | nein |
| `total_bytes` | integer | ja | nein |
| `used_bytes` | integer | ja | nein |
| `available_bytes` | integer | ja | nein |
| `used_percent` | number | optional | nein |

Die konkreten Werte für `type` und `state` werden nicht durch einen
künstlich kleinen Enum eingeschränkt, solange die Runtime mehrere
technische Swap-Typen bzw. Zustände unterstützen kann.

Wenn `used_percent` vorhanden ist:

```text
0 <= used_percent <= 100
```

Wenn kein Swap vorhanden ist, darf das gesamte `swap`-Objekt fehlen.

---

# 10. Storage

## 10.1 `storage`

```text
storage
└── filesystems
    └── <mountpoint>
```

`storage.devices` ist nicht Bestandteil des regulären Core Batch.

## 10.2 `storage.filesystems`

Typ:

```text
object
```

Die Schlüssel sind Mountpoints.

Beispiel:

```text
"/"
"/boot"
```

Pro Mountpoint:

```text
<mountpoint>
├── device
├── filesystem
├── mount_state
├── total_bytes
├── used_bytes
├── available_bytes
├── used_percent
└── inodes_used_percent
```

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `device` | string | ja | nein |
| `filesystem` | string | ja | nein |
| `mount_state` | string | ja | nein |
| `total_bytes` | integer | ja | nein |
| `used_bytes` | integer | ja | nein |
| `available_bytes` | integer | ja | nein |
| `used_percent` | number | ja | nein |
| `inodes_used_percent` | number | ja | nein |

Prozentwerte:

```text
0 <= used_percent <= 100
0 <= inodes_used_percent <= 100
```

---

# 11. Network

## 11.1 `network.interfaces`

```text
network
└── interfaces
    └── <interface>
        ├── state
        ├── blocked
        ├── mac
        └── addresses
```

Interface-Namen sind dynamische Schlüssel.

Beispiele:

```text
eth0
wlan0
```

Pro Interface:

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `state` | string | ja | nein |
| `blocked` | boolean | ja | nein |
| `mac` | string | ja | nein |
| `addresses` | array[string] | ja | nein |

`state`:

```text
up
down
```

`blocked` beschreibt einen administrativ bzw. radioseitig blockierten
Zustand.

`addresses` darf eine leere Liste sein:

```json
"addresses": []
```

Das bedeutet, dass aktuell keine Adresse übertragen wird.

Routing und DNS gehören nicht zum regulären Core Batch.

---

# 12. Connectivity

Der Core Batch reserviert den Bereich:

```text
connectivity
    ├── upload
    └── queue
```

Die konkrete Unterstruktur von `upload` und `queue` ist noch nicht
spezifiziert und ist nicht Bestandteil der aktuellen API-/Delivery-
Spezifikation.

Daher gilt für diese Version:

```text
connectivity.upload
connectivity.queue
```

sind **reservierte Bereiche**, aber noch kein final spezifizierter
JSON-Untervertrag.

Bis zur separaten Definition dürfen sie nicht mit frei erfundenen
Feldern befüllt werden.

Ein leerer Platzhalter wie:

```json
"upload": {},
"queue": {}
```

ist daher kein Bestandteil des finalen JSON-Vertrags.

---

# 13. Services

Services werden dynamisch modelliert:

```text
services
└── <service_id>
    ├── name
    ├── purpose
    ├── state
    ├── enabled
    ├── pid
    ├── started_at
    └── last_state_change_at
```

`services` ist ein Objekt mit dynamischen Service-IDs.

### Felder

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `name` | string | ja | nein |
| `purpose` | string | optional | nein |
| `state` | string | ja | nein |
| `enabled` | boolean | optional | nein |
| `pid` | integer | optional | nein |
| `started_at` | string datetime | optional | nein |
| `last_state_change_at` | string datetime | optional | nein |

Die optionalen Felder dürfen vollständig fehlen.

`null` ist für diese Felder nicht erforderlich.

### `state`

Zulässige Werte:

```text
running
stopped
failed
starting
stopping
unknown
```

Der technische Zustand wird vom LoggerPi geliefert.

Eine fachliche Bewertung erfolgt auf dem OtterPi.

---

# 14. Serial

```text
serial
├── device
├── state
└── diagnostics
    ├── last_rx_at
    ├── seconds_since_rx
    ├── lines_received
    ├── parse_errors
    └── reconnect_count
```

## 14.1 `serial.device`

Typ:

```text
string
```

Required:

```text
ja
```

Nullable:

```text
nein
```

Der aktuell verwendete LoggerPi-Pfad ist:

```text
/dev/ttyUSB0
```

Der JSON-Vertrag bindet den LoggerPi jedoch nicht dauerhaft an diesen
konkreten Gerätenamen.

## 14.2 `serial.state`

Typ:

```text
string
```

Required:

```text
ja
```

Zulässige Werte:

```text
connected
degraded
disconnected
unknown
```

## 14.3 `serial.diagnostics`

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `last_rx_at` | string datetime | optional | nein |
| `seconds_since_rx` | integer | optional | nein |
| `lines_received` | integer | optional | nein |
| `parse_errors` | integer | optional | nein |
| `reconnect_count` | integer | optional | nein |

Die numerischen Diagnosewerte müssen größer oder gleich `0` sein.

`last_rx_at` darf fehlen, wenn noch kein Empfang festgestellt wurde.

Diese Felder sind Diagnose-/Health-Daten und keine Freezer-Measurements.

---

# 15. Measurement-Modell

Alle physikalischen Measurements verwenden grundsätzlich dieselbe Struktur:

```text
measurement
├── value
├── unit
├── measured_at
├── validity
└── source
```

Alle fünf Felder sind Bestandteil eines Measurement-Objekts.

| Feld | Typ | Required | Nullable |
|---|---|---:|---:|
| `value` | number \| null | ja | ja |
| `unit` | string | ja | nein |
| `measured_at` | string datetime \| null | ja | ja |
| `validity` | string | ja | nein |
| `source` | string | ja | nein |

Ein Measurement darf daher nicht durch einen nackten numerischen Wert
repräsentiert werden.

Nicht zulässig:

```json
"temperature_1": 23.1
```

Zulässig:

```json
"temperature_1": {
  "value": 23.1,
  "unit": "celsius",
  "measured_at": "2026-08-15T10:44:55+02:00",
  "validity": "valid",
  "source": "atmoweb"
}
```

---

# 16. Measurement `null`-Semantik

`value` darf `null` sein.

Dies wird insbesondere verwendet, wenn kein verwertbarer Messwert
vorliegt.

Beispiel:

```json
{
  "value": null,
  "unit": "celsius",
  "measured_at": null,
  "validity": "unavailable",
  "source": "atmoweb"
}
```

`null` darf nicht durch einen künstlichen numerischen Wert ersetzt werden.

Insbesondere:

```text
N/A ≠ 0
N/A ≠ false
N/A ≠ leerer String
```

Bei einem nicht verfügbaren Messwert bleibt das Measurement-Objekt
vorhanden, sofern die betreffende Messgröße Bestandteil des übertragenen
Batches ist.

---

# 17. Validity

`validity` beschreibt den technischen bzw. datenseitigen Zustand des
Measurements.

Sie ist keine globale Health-Bewertung.

Zulässige Werte:

```text
valid
invalid
unavailable
unknown
stale
```

## 17.1 `valid`

Der Wert wurde erfolgreich erfasst und kann technisch als Messwert
verwendet werden.

Regel:

```text
valid → value ist nicht null
```

## 17.2 `invalid`

Ein Messwert wurde grundsätzlich erkannt, kann aber technisch nicht
zuverlässig als gültiger Wert verwendet werden.

Regel:

```text
invalid → value = null
```

Beispiele:

- fehlerhaftes Quellformat
- nicht parsebarer Wert
- technisch unzulässiger Messwert

## 17.3 `unavailable`

Die erwartete Messgröße ist aktuell nicht verfügbar.

Regel:

```text
unavailable → value = null
```

Wenn kein zuverlässiger Erfassungszeitpunkt vorliegt:

```text
measured_at = null
```

Beispiel:

```json
{
  "value": null,
  "unit": "ppm",
  "measured_at": null,
  "validity": "unavailable",
  "source": "atmoweb"
}
```

Insbesondere gilt:

```text
AtmoWEB N/A
    ↓
value = null
validity = unavailable
```

und niemals:

```text
AtmoWEB N/A
    ↓
value = 0
validity = valid
```

## 17.4 `unknown`

Der Zustand des Messwertes kann technisch nicht zuverlässig bestimmt
werden.

Regel:

```text
unknown → value = null
```

`unknown` darf nicht als pauschaler Ersatz für fehlende Implementierung
verwendet werden.

## 17.5 `stale`

Ein zuvor gültiger Messwert ist vorhanden, aber älter als der für die
betreffende Messgröße zulässige Aktualitätszeitraum.

Regel:

```text
stale → value ist nicht null
```

Der ursprüngliche Messwert und sein tatsächliches `measured_at` bleiben
erhalten.

Beispiel:

```json
{
  "value": 21.4,
  "unit": "celsius",
  "measured_at": "2026-08-15T09:30:00+02:00",
  "validity": "stale",
  "source": "atmoweb"
}
```

Die konkreten zeitlichen Schwellenwerte für `stale` sind nicht Bestandteil
dieses JSON-Vertrags.

---

# 18. Validity-Konsistenz

Für Measurements gelten folgende Kombinationen:

| `validity` | `value` | `measured_at` |
|---|---|---|
| `valid` | Wert | Zeitpunkt |
| `invalid` | `null` | Zeitpunkt oder `null` |
| `unavailable` | `null` | Zeitpunkt oder `null` |
| `unknown` | `null` | Zeitpunkt oder `null` |
| `stale` | Wert | Zeitpunkt |

Insbesondere nicht zulässig:

```text
valid + value = null
invalid + scheinbar gültiger Ersatzwert
unavailable + value = 0
unknown + value = 0
stale + value = null
```

---

# 19. Measurement Units

Die Einheit ist Bestandteil jedes Measurement-Objekts und darf nicht aus
dem Feldnamen allein implizit angenommen werden.

Für die aktuell definierten Core-Batch-Measurements gelten folgende
fachliche Einheiten:

| Measurement | Unit |
|---|---|
| `temperature_1` | `celsius` |
| `temperature_2` | `celsius` |
| `temperature_3` | `celsius` |
| `temperature_4` | `celsius` |
| `humidity` | `percent` |
| `vacuum` | `pascal` |
| `co2` | `ppm` |
| `o2` | `percent` |
| `fan_speed` | `rpm` |
| `freezer.temperature` | `celsius` |
| `system.cpu.temperature` | `celsius` |

Für `system.cpu.frequency.current_hz` und `system.cpu.frequency.max_hz`
wird die feste Einheit `hertz` durch das Feldsuffix `_hz` bereits
ausgedrückt; diese Werte sind keine Measurement-Objekte.

---

# 20. Freezer

```text
freezer
└── temperature
    ├── value
    ├── unit
    ├── measured_at
    ├── validity
    └── source
```

`freezer.temperature` ist ein vollständiges Measurement-Objekt.

Es verwendet dieselbe `null`- und `validity`-Semantik wie alle anderen
Measurements.

Die Freezer-Temperatur bleibt als eigenes fachliches Gerät vom allgemeinen
`measurements`-Bereich getrennt.

---

# 21. Measurements im Core Batch

Der reguläre Core Batch kann folgende Measurements enthalten:

```text
measurements
├── temperature_1
├── temperature_2
├── temperature_3
├── temperature_4
├── humidity
├── vacuum
├── co2
├── o2
└── fan_speed
```

Jedes vorhandene Feld ist ein vollständiges Measurement-Objekt.

Einzelne Measurements dürfen fehlen, wenn die betreffende Datenquelle für
den Batch nicht Bestandteil der verfügbaren Daten ist.

Das Fehlen eines Measurements bedeutet nicht automatisch:

```text
unavailable
```

Wenn die Messgröße Bestandteil des übertragenen Modells ist, aber aktuell
keinen Wert liefern kann, wird stattdessen das Measurement mit passender
`validity` übertragen.

---

# 22. States

States sind keine physikalischen Measurements.

Der Core Batch verwendet:

```text
states
├── door_open
├── door_locked
├── lights
├── switches
├── flap
└── defrost
```

## 22.1 Boolean States

Folgende States sind Boolean:

```text
door_open
door_locked
flap
defrost
```

Typ:

```text
boolean
```

Nullable:

```text
nein
```

## 22.2 `lights`

```text
lights
├── day
├── uv
└── led
```

Alle drei Werte sind:

```text
boolean
```

## 22.3 `switches`

```text
switches
├── a
├── b
├── c
└── d
```

Alle vier Werte sind:

```text
boolean
```

Nicht vorhandene, fachlich nicht unterstützte Schalter dürfen weggelassen
werden.

`null` wird nicht als Ersatz für einen fehlenden State verwendet.

---

# 23. Operation

```text
operation
└── mode
```

`mode` ist:

```text
string
```

Required innerhalb von `operation`:

```text
ja
```

Nullable:

```text
nein
```

Definierte fachliche Werte:

```text
program
idle
timer
manual
```

Die Herstellerwerte werden bereits auf Adapter-Ebene in diese fachlichen
Werte übersetzt.

---

# 24. Was nicht Bestandteil des Core-Batch-JSON ist

Folgende Bereiche gehören nicht zum regulären Core Batch:

```text
system.identity
storage.devices
network.routing
network.dns
autostart
timers
device
metadata
setpoints
alarm_limits
programming
```

Ebenfalls nicht Bestandteil:

- vollständige Hersteller-API-Daten
- vollständige Prozesslisten
- `measurements.misc`
- `states.misc`
- permanente aktive Connectivity-Tests
- Freezer-Events
- Freezer-Alarmmeldungen
- Metadata-Change-Daten
- Event-Daten

Diese Bereiche werden separat modelliert.

---

# 25. Connectivity – ausdrücklicher Vorbehalt

Die fachliche Core-Batch-Struktur reserviert:

```text
connectivity.upload
connectivity.queue
```

Die konkrete JSON-Struktur dieser beiden Bereiche ist noch nicht
spezifiziert und ist nicht Bestandteil der aktuellen API-/Delivery-
Spezifikation.

Bis zur separaten Spezifikation dieser Connectivity-Telemetrie dürfen
Implementierungen keine eigenen Unterfelder erfinden.

Das bedeutet insbesondere:

```text
kein frei definiertes
connectivity.upload.status

kein frei definiertes
connectivity.queue.depth
```

ohne vorherige Ergänzung dieses Vertrags.

---

# 26. Beispiel eines vollständigen Core Batch

Das folgende Beispiel ist ein strukturelles Beispiel des JSON-Vertrags.

Nicht jedes optionale Feld muss in jedem realen Batch vorhanden sein.

```json
{
  "schema_version": "1.0",
  "batch_id": "01J...",
  "logger_id": "loggerpi-01",
  "sequence": 1842,
  "created_at": "2026-08-15T10:45:00+02:00",

  "system": {
    "time": {
      "current": "2026-08-15T10:45:00+02:00",
      "timezone": "Europe/Berlin",
      "clock_state": "synchronized"
    },
    "boot": {
      "last_boot_at": "2026-08-15T07:12:31+02:00",
      "uptime_seconds": 12749
    },
    "cpu": {
      "usage_percent": 12.4,
      "load": {
        "1m": 0.21,
        "5m": 0.18,
        "15m": 0.16
      },
      "frequency": {
        "current_hz": 1200000000,
        "max_hz": 1400000000
      },
      "temperature": {
        "value": 48.2,
        "unit": "celsius",
        "measured_at": "2026-08-15T10:44:58+02:00",
        "validity": "valid",
        "source": "system"
      },
      "throttling": {
        "undervoltage": false,
        "frequency_capped": false,
        "throttled": false,
        "temperature_limit": false
      }
    },
    "processes": {
      "total": 192
    }
  },

  "memory": {
    "total_bytes": 4294967296,
    "used_bytes": 812646400,
    "available_bytes": 3482320896,
    "used_percent": 18.9
  },

  "swap": {
    "device": "/dev/zram0",
    "type": "zram",
    "state": "active",
    "total_bytes": 2147483648,
    "used_bytes": 0,
    "available_bytes": 2147483648,
    "used_percent": 0.0
  },

  "storage": {
    "filesystems": {
      "/": {
        "device": "/dev/mmcblk0p2",
        "filesystem": "ext4",
        "mount_state": "rw",
        "total_bytes": 62000000000,
        "used_bytes": 18000000000,
        "available_bytes": 44000000000,
        "used_percent": 29.0,
        "inodes_used_percent": 8.4
      }
    }
  },

  "network": {
    "interfaces": {
      "eth0": {
        "state": "up",
        "blocked": false,
        "mac": "00:11:22:33:44:55",
        "addresses": [
          "141.51.190.103/24"
        ]
      },
      "wlan0": {
        "state": "down",
        "blocked": false,
        "mac": "66:77:88:99:aa:bb",
        "addresses": []
      }
    }
  },

  "services": {
    "meshagent": {
      "name": "meshagent.service",
      "purpose": "mesh_remote_access",
      "state": "running",
      "enabled": true
    },
    "ssh": {
      "name": "ssh.service",
      "purpose": "administration",
      "state": "running",
      "enabled": true
    },
    "lightdm": {
      "name": "lightdm.service",
      "purpose": "local_graphical_recovery",
      "state": "running",
      "enabled": true
    },
    "rc-local": {
      "name": "rc-local.service",
      "purpose": "legacy_application_start",
      "state": "running",
      "enabled": true
    },
    "systemd-timesyncd": {
      "name": "systemd-timesyncd.service",
      "purpose": "time_synchronization",
      "state": "running",
      "enabled": true
    },
    "dhcpcd": {
      "name": "dhcpcd.service",
      "purpose": "network_configuration",
      "state": "running",
      "enabled": true
    }
  },

  "serial": {
    "device": "/dev/ttyUSB0",
    "state": "connected",
    "diagnostics": {
      "last_rx_at": "2026-08-15T10:44:55+02:00",
      "seconds_since_rx": 5,
      "lines_received": 120,
      "parse_errors": 0,
      "reconnect_count": 0
    }
  },

  "freezer": {
    "temperature": {
      "value": -82.0,
      "unit": "celsius",
      "measured_at": "2026-08-15T10:44:55+02:00",
      "validity": "valid",
      "source": "freezer_serial"
    }
  },

  "measurements": {
    "temperature_1": {
      "value": 21.4,
      "unit": "celsius",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "temperature_2": {
      "value": null,
      "unit": "celsius",
      "measured_at": null,
      "validity": "unavailable",
      "source": "atmoweb"
    },
    "temperature_3": {
      "value": 22.1,
      "unit": "celsius",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "temperature_4": {
      "value": 22.4,
      "unit": "celsius",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "humidity": {
      "value": 45.2,
      "unit": "percent",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "vacuum": {
      "value": 101325,
      "unit": "pascal",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "co2": {
      "value": 410,
      "unit": "ppm",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "o2": {
      "value": 20.9,
      "unit": "percent",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    },
    "fan_speed": {
      "value": 1200,
      "unit": "rpm",
      "measured_at": "2026-08-15T10:44:50+02:00",
      "validity": "valid",
      "source": "atmoweb"
    }
  },

  "states": {
    "door_open": false,
    "door_locked": true,
    "lights": {
      "day": true,
      "uv": false,
      "led": true
    },
    "switches": {
      "a": false,
      "b": true,
      "c": false,
      "d": false
    },
    "flap": false,
    "defrost": false
  },

  "operation": {
    "mode": "idle"
  }
}
```

---

# 27. Konformitätsregeln

Ein Core Batch v1 ist konform, wenn mindestens folgende Regeln erfüllt
sind:

1. Alle Envelope-Pflichtfelder sind vorhanden.
2. `schema_version` ist `"1.0"`.
3. `batch_id` ist vorhanden und nicht `null`.
4. `logger_id` ist vorhanden und nicht `null`.
5. `sequence` ist eine Ganzzahl.
6. `created_at` ist ein absoluter Zeitstempel mit Zeitzoneninformation.
7. Measurements verwenden das gemeinsame Measurement-Modell.
8. `validity` verwendet ausschließlich die definierten Werte.
9. `valid` und `stale` liefern einen konkreten `value`.
10. `invalid`, `unavailable` und `unknown` liefern `value = null`.
11. `null` wird nicht als allgemeiner Ersatz für fehlende optionale Felder
    verwendet.
12. `received_at` wird nicht vom LoggerPi übertragen.
13. Nicht definierte zusätzliche Felder werden nicht als Bestandteil des
    Core-Batch-v1-Modells interpretiert.
14. Connectivity-Unterstrukturen werden nicht eigenmächtig erweitert.
15. Fachliche Health- oder Alarmbewertungen werden nicht in den Core Batch
    eingeführt.

---

# 28. Abgrenzung zu API Contract

Dieses Dokument definiert die Datenstruktur.

Es definiert ausdrücklich nicht:

```text
HTTP method
URL
request headers
authentication
retry
duplicate handling
timeout
queue persistence
delivery state machine
```

Die technische Übertragung und Zustellung des Core Batch werden separat
im API- und Delivery-Design definiert.

---

# 29. Abgrenzung zu Metadata und Events

Metadata und selten veränderliche Informationen werden nicht künstlich in
den regulären Core Batch aufgenommen.

Events und Alarme werden ebenfalls nicht als Measurements oder States
simuliert.

Die jeweiligen Strukturen werden separat definiert.

---

# 30. Status

Mit diesem Dokument wird die JSON-Repräsentation des bereits fachlich
definierten Core Batch v1 konkretisiert.

Damit sind insbesondere festgelegt:

- Batch Envelope
- JSON-Datentypen
- Required-/Optional-Semantik
- `null`-Semantik
- Measurement-Modell
- `validity`-Semantik
- Zeitstempel-Semantik
- Core-States
- Operation-Enum
- technische Wertebereiche, soweit bereits festgelegt

Noch separat zu definieren sind:
- konkrete `connectivity.upload`-Struktur
- konkrete `connectivity.queue`-Struktur
- Metadata Change
- Events

---

## Design Principle

> So schlank wie möglich, aber sinnvoll wie nötig.
