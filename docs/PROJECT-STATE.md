# LoggerPi → OtterPi

## Projektstatus

**Projekt:** LoggerPi → OtterPi  
**Data Model:** v1  
**Projektphase:** Data Model v1 / API Design  
**Status:** In aktiver Entwicklung  
**Stand:** 2026-08-15

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

Der nächste Arbeitsschritt betrifft nun die noch offenen bzw. separat zu
spezifizierenden Bereiche wie Metadata Change und Events.

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

- AtmoWEB-Endpunkte
- CPU-Temperatur
- CPU-Auslastung
- Freezer-Log
- ThingSpeak Bulk Update

Der Freezer wird derzeit über eine serielle Verbindung erfasst.

`/dev/ttyUSB0` wird aktuell von `minicom` verwendet:

```text
minicom -C /home/ZOOLOGY-observ/Programs/freezer.log
```

Das Freezer-Log befindet sich unter:

```text
/home/ZOOLOGY-observ/Programs/freezer.log
```

Die bisherige monatliche Archivierung erfolgt über:

```text
/home/ZOOLOGY-observ/Programs/backup_log.sh
```

und einen User-Cronjob.

Diese Legacy-Mechanismen werden nicht automatisch Bestandteil des neuen Core Batch. Sie dienen zunächst als Ist-Zustand und als Quelle für die Ableitung des neuen Datenmodells.

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

---

## Danach

Der konkrete Core Batch v1 ist aus dem Feldkatalog abgeleitet und unter

```text
docs/data-model/core-batch-v1.md
```

dokumentiert und committed.

```text
Data Model v1
    ↓
Core Batch v1
    ↓
Core Batch JSON v1
    ↓
Core Batch API v1
    ↓
Core Batch Delivery v1
    ↓
Metadata Change
    ↓
Events
```

---

## Offene Entscheidungen

- vollständiges Metadata-Synchronisationsprotokoll
- Event-Schema
- Routing-/DNS-Platzierung
- Behandlung statischer Netzwerk-/Storage-Metadata
- genaue technische Umsetzung der Legacy-Ablösung
- genaue Zuordnung der vorhandenen Runtime-Komponenten zum neuen
  Service-Modell
- Schema-Versionierung

---

## Referenzdokumente

Der detaillierte Feldkatalog und der Einheitenkatalog werden separat unter

```text
docs/data-model/
```

geführt.

Der Feldkatalog beschreibt das verfügbare Data Model.

Er definiert nicht automatisch, welche Felder in jedem regulären Core Batch enthalten sein müssen.

Die historische Legacy-Implementierung und ihre Dokumentation befinden sich unter:

```text
docs/legacy/
```

Der Project State ist das zentrale Wiedereinstiegsdokument für den aktuellen Entwicklungsstand.

---

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
