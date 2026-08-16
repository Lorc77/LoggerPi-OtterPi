# LoggerPi → OtterPi

## Core Batch v1

**Data Model:** v1  
**Status:** fachlich definiert / eingefroren  
**Zweck:** Definition der regelmäßig übertragenen Betriebsdaten des LoggerPi

---

## 1. Zweck

Der Core Batch enthält die für den regulären Betrieb des LoggerPi relevanten
Daten.

Er ist bewusst kleiner als das vollständige Data Model.

Der Core Batch wird regelmäßig übertragen, beispielsweise alle 15 Minuten.

Grundprinzip:

> Der Core Batch beschreibt den aktuellen technischen Betriebszustand des
> LoggerPi und die aktuell relevanten Sensor-/Gerätedaten.

Der Core Batch ist nicht dafür vorgesehen, das vollständige System,
sämtliche Metadata oder die vollständige Hersteller-API abzubilden.

---

## 2. Abgrenzung

```text
Data Model v1
      │
      ├── Core Batch
      │      └── regelmäßige Übertragung
      │
      ├── Metadata / Change
      │      └── nur bei Änderung bzw. Synchronisationsbedarf
      │
      ├── Events
      │      └── Ereignisse / Alarme
      │
      └── Configuration
             └── Setpoints / Alarm Limits / weitere Konfiguration
```

Der konkrete Übertragungsmechanismus für Metadata, Events und Configuration
wird separat spezifiziert.

---

## 3. Batch Envelope

Der Core Batch verwendet den bereits definierten Batch Envelope:

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

| Feld | Bedeutung |
|---|---|
| `schema_version` | Version des Data Models |
| `batch_id` | eindeutige Identität dieses Batches |
| `logger_id` | eindeutige Identität des LoggerPi |
| `sequence` | persistente, pro LoggerPi monotone Batch-Nummer |
| `created_at` | Zeitpunkt der Batch-Erzeugung auf dem LoggerPi |

### Sequence

`sequence` wird beim Erzeugen des Batches vergeben.

Sie ist pro LoggerPi persistent und monoton fortlaufend.

Ein Retry erzeugt keinen neuen fachlichen Batch:

```text
gleiche batch_id
gleiche sequence
neuer Zustellversuch
```

---

## 4. Zeitmodell

Die Zeitangaben bleiben semantisch getrennt.

### `created_at`

Zeitpunkt der Erzeugung des Batches auf dem LoggerPi.

### `measured_at`

Zeitpunkt der tatsächlichen Erfassung eines Messwertes.

### `received_at`

Zeitpunkt des Empfangs auf dem OtterPi.

`received_at` wird nicht vom LoggerPi im Core Batch gesetzt.

---

# 5. Core-Batch-Struktur

Die fachliche Struktur des Core Batch ist:

```text
batch
│
├── schema_version
├── batch_id
├── logger_id
├── sequence
├── created_at
│
├── system
│   ├── time
│   ├── boot
│   ├── cpu
│   └── processes
│
├── memory
├── swap
│
├── storage
│   └── filesystems
│
├── network
│   └── interfaces
│
├── connectivity
│   ├── upload
│   └── queue
│
├── services
│
├── serial
│   ├── device
│   ├── state
│   └── diagnostics
│
├── freezer
│   └── temperature
│
├── measurements
│
├── states
│
└── operation
```

---

# 6. System

## 6.1 System / Time

Regelmäßig übertragen werden:

```text
system.time
├── current
├── timezone
└── clock_state
```

### Bedeutung

`current`

Aktuelle Systemzeit des LoggerPi.

`timezone`

Aktuell konfigurierte Zeitzone.

`clock_state`

Technischer Zustand der Systemuhr bzw. Zeitsynchronisation.

Der LoggerPi liefert den technischen Zustand.

Eine fachliche Health-Bewertung erfolgt auf dem OtterPi.

---

## 6.2 System / Boot

```text
system.boot
├── last_boot_at
└── uptime_seconds
```

Ein separates `reboot_detected` ist nicht erforderlich.

Der OtterPi kann einen Neustart anhand einer Veränderung von
`last_boot_at` erkennen.

---

## 6.3 System / CPU

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

CPU-Auslastung, Load, Frequenz und Temperatur sind Measurements.

Die Throttling-Werte sind States.

---

## 6.4 System / Processes

Im Core Batch wird ausschließlich die aggregierte Prozessanzahl übertragen:

```text
system.processes.total
```

Eine vollständige Prozessliste ist nicht Bestandteil des Core Batch.

Nicht enthalten sind insbesondere:

- PID-Liste
- Prozessnamen
- CPU-Verbrauch einzelner Prozesse
- Memory-Verbrauch einzelner Prozesse

Diese Informationen können später Bestandteil gezielter Diagnosefunktionen
werden.

---

# 7. Memory

```text
memory
├── total_bytes
├── used_bytes
├── available_bytes
└── used_percent
```

Rohwerte werden bevorzugt erhalten.

Der abgeleitete Wert `used_percent` darf zusätzlich übertragen werden.

---

# 8. Swap

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

Beispiel:

```text
device = /dev/zram0
type   = zram
state  = active
```

---

# 9. Storage

Im Core Batch werden die laufenden Dateisystemdaten übertragen.

```text
storage
└── filesystems
    └── <mountpoint>
        ├── device
        ├── filesystem
        ├── mount_state
        ├── total_bytes
        ├── used_bytes
        ├── available_bytes
        ├── used_percent
        └── inodes_used_percent
```

## Nicht im regelmäßigen Core Batch

Die physischen Storage-Device-Metadata gehören nicht in den regulären Batch:

```text
storage.devices[]
├── device
├── model
├── type
└── manufactured_at
```

Diese Informationen sind Metadata bzw. Change-Daten.

---

# 10. Network

## 10.1 Interfaces

Netzwerkinterfaces werden unter:

```text
network.interfaces
```

geführt.

Pro Interface:

```text
network.interfaces.<interface>
├── state
├── blocked
├── mac
└── addresses[]
```

Beispiele:

```text
eth0
wlan0
```

Mögliche Zustände:

```text
up
down
```

`blocked` beschreibt einen administrativ bzw. radioseitig blockierten Zustand.

Der LoggerPi liefert den technischen Zustand.

Eine fachliche Connectivity-/Health-Bewertung erfolgt auf dem OtterPi.

---

## 10.2 Routing

`network.routing` ist nicht Bestandteil des regelmäßigen Core Batch.

Insbesondere:

```text
network.routing.default_gateway
```

wird nicht regelmäßig übertragen.

---

## 10.3 DNS

`network.dns` ist nicht Bestandteil des regelmäßigen Core Batch.

Insbesondere:

```text
network.dns.servers[]
```

wird nicht regelmäßig übertragen.

---

# 11. Connectivity

Der Core Batch enthält technische Informationen über Upload und lokale Queue.

```text
connectivity
├── upload
└── queue
```

Die genaue Unterstruktur wird im API-/Delivery-Design festgelegt.

### Grundprinzip

Der erfolgreiche Upload des Batches zum OtterPi ist bereits ein praktischer
Nachweis des verwendeten Kommunikationsweges.

Deshalb werden keine permanenten redundanten Connectivity-Tests durchgeführt.

Insbesondere nicht standardmäßig bei jedem Batch:

- ping
- DNS-Test
- HTTPS-Test

Gezielte aktive Tests bleiben für spätere Diagnosefunktionen möglich.

---

# 12. Services

Services werden dynamisch modelliert:

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

## Technischer Service-Zustand

Mögliche Zustände:

```text
running
stopped
failed
starting
stopping
unknown
```

Der LoggerPi liefert den technischen Zustand.

Der OtterPi bewertet dessen fachliche Bedeutung für Health und Dashboard.

---

## 12.1 Aktuell relevante LoggerPi-Services

Die aktuelle Runtime-Bewertung betrachtet insbesondere folgende Services
als relevant:

```text
meshagent
ssh
lightdm
rc-local
systemd-timesyncd
dhcpcd
```

Diese Liste bleibt erweiterbar.

### `meshagent`

Remote-/Mesh-Zugriff.

### `ssh`

Administrativer Remote-Zugriff.

### `lightdm`

Lokale grafische Recovery-/Konfigurationsumgebung.

### `rc-local`

Aktueller Startmechanismus der Legacy-Anwendung.

`rc-local` bleibt solange im Core-Batch-Service-Modell, wie die Legacy-
`observer.py` darüber gestartet wird.

Nach der erfolgreichen Ablösung der Legacy-Anwendung kann `rc-local` aus dem
LoggerPi-Service-Modell entfernt werden.

### `systemd-timesyncd`

Technischer Zustand der Zeitsynchronisation.

### `dhcpcd`

Technischer Zustand des aktuell verwendeten Netzwerkverwaltungs-/DHCP-
Dienstes.

Sollte die Netzwerkverwaltung später auf einen anderen Dienst umgestellt
werden, wird entsprechend der tatsächlich verwendete relevante Dienst
abgebildet.

---

# 13. Serial

Der Freezer besitzt eine serielle Anbindung.

Technische Kommunikationsparameter sind statische Configuration bzw.
Metadata und werden nicht in jedem Batch übertragen.

Der aktuelle LoggerPi verwendet:

```text
/dev/ttyUSB0
```

## 13.1 Serial State

```text
serial
├── device
└── state
```

Mögliche Zustände:

```text
connected
degraded
disconnected
unknown
```

### Definition

`connected`

- Gerät vorhanden
- erwarteter Datenempfang funktioniert

`degraded`

- Gerät vorhanden
- erwarteter Datenempfang bleibt aus

`disconnected`

- Gerät nicht vorhanden

`unknown`

- Zustand nicht zuverlässig bestimmbar

---

## 13.2 Serial Diagnostics

```text
serial.diagnostics
├── last_rx_at
├── seconds_since_rx
├── lines_received
├── parse_errors
└── reconnect_count
```

Diese Informationen sind Diagnose-/Health-Daten.

Sie sind keine Freezer-Messwerte.

---

# 14. Freezer

Der tatsächlich aus dem seriellen Freezer-Protokoll gelesene Temperaturwert
wird in das gemeinsame Measurement-Modell übersetzt.

```text
freezer.temperature
├── value
├── unit
├── measured_at
├── validity
└── source
```

Der Freezer bleibt dabei als eigenes fachliches Gerät vom allgemeinen
`measurements`-Bereich getrennt.

---

# 15. Measurements

Physikalische Messwerte folgen dem gemeinsamen Measurement-Modell:

```text
measurement
├── value
├── unit
├── measured_at
├── validity
└── source
```

Der Core Batch kann derzeit insbesondere folgende Measurements enthalten:

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

Nicht jeder Sensor muss zu jedem Zeitpunkt einen gültigen Wert liefern.

---

# 16. Validity

Vorgesehene Zustände:

```text
valid
invalid
unavailable
unknown
stale
```

# 16. Validity

`validity` beschreibt den technischen bzw. datenseitigen Zustand eines
übertragenen Measurements.

`validity` ist keine fachliche Health- oder Alarmbewertung.

Zulässige Zustände:

```text
valid
invalid
unavailable
unknown
stale
```

Die verbindliche Semantik ist:

```text
valid
    → value ist nicht null

invalid
    → value = null

unavailable
    → value = null

unknown
    → value = null

stale
    → value ist nicht null
```

Bei `stale` bleiben der letzte bekannte Wert und sein tatsächliches
`measured_at` erhalten.

Insbesondere gilt für AtmoWEB:

```text
AtmoWEB N/A
    ↓
value = null
validity = unavailable
```

und niemals:

```text
N/A
    ↓
value = 0
validity = valid
```

Der LoggerPi liefert die technische Validity.

Der OtterPi bewertet daraus fachliche Health, Grenzwertverletzungen,
Alarme und sonstige fachliche Zustände.

Insbesondere gilt:

```text
AtmoWEB N/A
    ↓
validity = unavailable
```

und niemals:

```text
N/A
    ↓
0
```

Damit bleibt die Bedeutung des Quellwertes erhalten.

---

# 17. States

Der Core Batch kann die aktuell relevanten Gerätezustände enthalten:

```text
states
├── door_open
├── door_locked
├── lights
├── switches
├── flap
└── defrost
```

Diese Werte sind States und keine physikalischen Measurements.

Es gibt bewusst kein:

```text
states.misc
```

---

# 18. Operation

Der aktuelle Betriebsmodus wird unter:

```text
operation.mode
```

geführt.

Bekannte fachliche Werte sind:

```text
program
idle
timer
manual
```

Die ursprünglichen Herstellerwerte werden bereits auf Adapter-Ebene in diese
fachlichen Werte übersetzt.

---

# 19. Nicht Bestandteil des regulären Core Batch

Folgende Bereiche des Data Model v1 werden nicht regelmäßig im Core Batch
übertragen:

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

Außerdem nicht:

- vollständige Hersteller-API-Daten
- Prozesslisten
- unstrukturierte `measurements.misc`
- unstrukturierte `states.misc`
- redundante aktive Connectivity-Tests

---

# 20. Metadata / Change

Statische bzw. selten veränderliche Informationen werden getrennt vom
regelmäßigen Core Batch behandelt.

Dazu gehören beispielsweise:

```text
system.identity
storage.devices
device
metadata
```

Beispiel:

```text
Erster Kontakt
    ↓
vollständige Metadata
    ↓
keine Änderung
    ↓
keine Wiederholung

Änderung
    ↓
Metadata Change
    ↓
LoggerPi → OtterPi
    ↓
erfolgreiche technische Annahme
    ↓
Änderung synchronisiert
```

Die genaue technische Struktur des Metadata-Change-Mechanismus wird separat
definiert.

---

# 21. Events

Events sind ebenfalls vom Core Batch getrennt.

Mögliche Quellen:

```text
freezer
serial
atmoweb
logger
service
connectivity
system
```

Beispiele:

```text
alarm
restart
service_failure
connectivity_change
device_event
```

Die endgültige Event-Struktur wird separat definiert.

Ein Event wird nicht künstlich als Measurement oder Health-Feld in den Core
Batch eingebaut.

---

# 22. Beispiel eines Core Batch

Das folgende Beispiel zeigt die fachliche Struktur des Core Batch v1.

Die verbindliche JSON-Repräsentation ist in
`docs/data-model/core-batch-v1-json.md` definiert.

Der technische HTTP-Contract ist in
`docs/api/core-batch-api-v1.md` definiert.

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
    "value": 23.1,
    "unit": "celsius",
    "measured_at": "2026-08-15T10:44:55+02:00",
    "validity": "valid",
    "source": "atmoweb"
  },
  "humidity": {
    "value": 45.2,
    "unit": "percent",
    "measured_at": "2026-08-15T10:44:55+02:00",
    "validity": "valid",
    "source": "atmoweb"
  },
  "co2": {
    "value": null,
    "unit": "ppm",
    "measured_at": null,
    "validity": "unavailable",
    "source": "atmoweb"
  }
},

  "states": {
    "door_open": false,
    "door_locked": true,
    "lights": {},
    "switches": {},
    "flap": false,
    "defrost": false
  },

  "operation": {
    "mode": "idle"
  }
}
```

---

## 23. Status

Mit diesem Dokument ist die fachliche Struktur des Core Batch v1 aus dem
Data Model v1 abgeleitet.

Die technische Übertragung und Zustellung des Core Batch sind separat
spezifiziert in:

- `docs/api/core-batch-api-v1.md`
- `docs/api/core-batch-delivery-v1.md`

Damit sind insbesondere festgelegt:

- API-Endpunkt und Request-/Response-Schema
- HTTP Push von LoggerPi → OtterPi
- technische HTTP-Annahme über die vom LoggerPi initiierte Verbindung
- Delivery- und Persistenz-Semantik
- Retry-Grundverhalten
- Duplicate Handling
- persistente lokale Queue
- keine nachgelagerte Rückverbindung zum LoggerPi

Die konkrete Authentication ist noch nicht final festgelegt.

Die Bereiche `connectivity.upload` und `connectivity.queue` sind als
technische Connectivity-Telemetrie vorgesehen.

Ihre konkrete Unterstruktur ist noch nicht spezifiziert und ist nicht
Bestandteil der aktuellen API-/Delivery-Spezifikation.

Bis zur separaten Spezifikation dieser Connectivity-Telemetrie werden
unter `connectivity.upload` und `connectivity.queue` keine verbindlichen
Unterfelder definiert.

Die JSON-Repräsentation des Core Batch v1 einschließlich
Required-/Optional-/Nullable-Semantik, `null`-Semantik,
Validity-Semantik und Units ist in `core-batch-v1-json.md` festgelegt.

Event- und Metadata-Change-Schemata werden separat definiert.

---

## Design Principle

> So schlank wie möglich, aber sinnvoll wie nötig.
