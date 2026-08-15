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

Der aktuelle fachliche Arbeitspunkt ist:

```text
Core Batch → Services
```

Das Data Model ist bereits wesentlich weiter entwickelt als der konkrete Core Batch.

Der Core Batch wird aus dem vorhandenen Feldkatalog abgeleitet und soll nur die für den regulären Betrieb tatsächlich relevanten Daten enthalten.

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

- persistenter Queue
- `batch_id`
- unveränderter `sequence`
- Idempotenz
- ACK-basierter Zustellbestätigung

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

Bereits erzeugte, aber noch nicht bestätigte Batches müssen in einer persistenten lokalen Queue verbleiben.

Ein Verbindungsabbruch darf nicht dazu führen, dass ein bereits erzeugter Batch verloren geht.

Ein Retry erzeugt keinen neuen fachlichen Batch:

```text
gleicher batch_id
gleiche sequence
neuer Zustellversuch
```

Die technische Spezifikation von Queue, ACK und Duplicate Handling ist noch nicht vollständig festgelegt.

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
├── purpose
└── state
```

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

Auf der aktuellen Installation wurden außerdem unter anderem festgestellt:

- `dhcpcd.service`
- `networking.service`
- `wpa_supplicant.service`
- `raspberrypi-net-mods.service`
- `ModemManager.service`
- `bluetooth.service`
- `rsync.service`
- `teamviewerd.service`

Ihre bloße Existenz bedeutet noch nicht, dass sie Bestandteil des fachlichen Core Batch werden.

Für jeden relevanten Dienst wird separat bewertet:

1. operative Relevanz
2. Daten-Erfassungsrelevanz
3. Batch-/Queue-Relevanz
4. API-/Upload-Relevanz
5. Dashboard-Relevanz
6. stabiler funktionaler Zweck

Nur fachlich relevante Services sollen in den regulären Core Batch aufgenommen werden.

### Beobachtete Sonderfälle

`rsync.service` ist aktiviert, läuft aktuell jedoch nicht, da auf der Installation keine `/etc/rsyncd.conf` vorhanden ist.

`teamviewerd.service` ist installiert, aktuell jedoch deaktiviert/inaktiv.

`ModemManager.service` und `bluetooth.service` laufen bzw. sind aktiviert. Ihre tatsächliche fachliche Relevanz für den LoggerPi muss noch bewertet werden.

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
erfolgreiches ACK
    ↓
Änderung gilt als synchronisiert
```

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

Die Inventur ist damit abgeschlossen.

Der nächste fachliche Schritt ist jetzt die funktionale Bewertung der
festgestellten Runtime-Komponenten:

```text
reale Runtime
    ↓
funktionale Services identifizieren
    ↓
Service-Modell gegen Realität abgleichen
    ↓
Legacy-/Infrastruktur-/Recovery-Funktionen abgrenzen
    ↓
Core-Batch-Mitgliedschaft bestimmen
    ↓
konkreten Core Batch ableiten
```

Dabei gilt:

Nicht jeder installierte oder laufende Linux-Dienst ist automatisch ein
LoggerPi-Service im Sinne des Data Models.

Insbesondere müssen fachliche LoggerPi-Funktionen von allgemeinen
Betriebssystem-, Netzwerk-, Remote-Access- und Recovery-Komponenten
getrennt werden.

Die bestehende Legacy-`observer.py` bleibt dabei zunächst als Ist-Zustand
und Referenz erhalten. Ihre Ablösung oder Migration erfolgt erst auf Basis
der neuen Architektur und wird nicht durch die reine Runtime-Inventur
vorweggenommen.

---

## Danach

Nach der Servicebewertung wird der konkrete Core Batch aus dem bereits abgeschlossenen Feldkatalog abgeleitet.

Anschließend werden die noch offenen technischen Details der API und Zustellung spezifiziert.

---

## Offene Entscheidungen

- finale Liste der fachlich relevanten LoggerPi-Services
- finale Core-Batch-Mitgliedschaft
- Routing-/DNS-Platzierung
- Behandlung statischer Netzwerk-/Storage-Metadata
- vollständiges Metadata-Synchronisationsprotokoll
- finale Validitätssemantik
- Event-Schema
- Queue-/ACK-Semantik
- Duplicate Handling
- API Contract
- Authentication
- Schema-Versionierung
- genaue technische Umsetzung der Legacy-Ablösung
- genaue Zuordnung der vorhandenen Runtime-Komponenten zum neuen Service-Modell

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
