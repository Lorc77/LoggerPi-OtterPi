# LoggerPi → OtterPi
## Project State

**Project:** LoggerPi → OtterPi  
**Data Model:** v1  
**Status:** In active design  
**Last updated:** 2026-08-15

---

## Current Phase

Data Model v1 / API

The field catalog and units catalog are completed.

The current work is the derivation of the concrete Core Batch from the
completed field catalog.

---

## Architecture

Communication is fundamentally:

LoggerPi → OtterPi

The LoggerPi initiates communication via HTTP/API.

The OtterPi must not depend on being able to actively reach a LoggerPi.

---

## Completed

- Data Model v1 field catalog
- Units catalog v1
- Batch envelope
- `schema_version`
- `batch_id`
- `logger_id`
- persistent per-LoggerPi `sequence`
- `created_at` / `measured_at` / `received_at` separation
- system data model
- CPU / memory / swap / storage model
- network interface model
- `blocked` for network interfaces
- aggregated process count
- Serial / Freezer model
- AtmoWEB mapping concept
- Measurements / States / Events separation
- Metadata concept
- Push-based metadata synchronization concept
- no `measurements.misc`
- no `states.misc`

---

## Important Invariants

### Batch identity

`batch_id` identifies one concrete batch.

A retry keeps the same `batch_id`.

### Sequence

`sequence` is:

- persistent
- monotonically increasing
- scoped to one LoggerPi
- assigned when the batch is created
- assigned before the batch enters the persistent queue

A retry does not change the sequence.

### Queue

Already-created but unacknowledged batches remain in the persistent local queue.

A disconnect must not cause an already-created batch to be lost.

### Time

- `created_at` = batch creation time on LoggerPi
- `measured_at` = measurement time
- `received_at` = reception time on OtterPi

`received_at` is an OtterPi-side value.

### Data responsibility

LoggerPi provides technical facts.

OtterPi evaluates their functional meaning, health and state.

---

## Core System Structure

system
├── identity
├── boot
├── cpu
├── memory
├── swap
├── storage
├── network
└── processes

The regular Core Batch should remain lean.
Static metadata should not unnecessarily be repeated in every batch.

## Metadata
Metadata is synchronized via the normal LoggerPi → OtterPi push path.
Concept:
•	first contact → full metadata 
•	unchanged → no repeated full metadata 
•	changed → metadata delta 
•	metadata changes are only considered synchronized after successful acknowledgement 
The exact metadata synchronization protocol is not yet finalized.


## Current Work

Services
The service model is structurally defined:
services.<service_id>
├── purpose
└── state
The actual LoggerPi service inventory has not yet been reviewed.

## Next Step

Compare the actual LoggerPi service inventory against the service model.
For each relevant service determine:
1.	operational relevance 
2.	data-collection relevance 
3.	batch / queue relevance 
4.	API / upload relevance 
5.	dashboard relevance 
6.	stable functional purpose 
Only relevant services should become part of the Core Batch.

## Open Decisions

•	concrete LoggerPi services 
•	final Core Batch membership 
•	routing / DNS placement 
•	static network/storage metadata handling 
•	complete metadata synchronization protocol 
•	final validity semantics 
•	event schema 
•	queue / ACK semantics 
•	duplicate handling 
•	API contract 
•	authentication 
•	schema versioning 

## Reference Documents

The detailed field catalog and units catalog are maintained separately under:
docs/data-model/
The field catalog describes the available Data Model.
It does not define which fields must appear in every regular Core Batch.

## Design Principle

As lean as possible, but as complete as reasonably necessary.


--------------------------------------------------------------------------------------------------------


# LoggerPi → OtterPi

Data Model v1 und API-Konzept für die Kommunikation zwischen LoggerPi und OtterPi.

## Projektziel

Der LoggerPi erfasst System-, Sensor- und Gerätedaten und überträgt diese an den OtterPi.

Die Kommunikation erfolgt grundsätzlich als Push:

LoggerPi → OtterPi

Der OtterPi darf nicht voraussetzen, dass er den LoggerPi aktiv erreichen kann, da LoggerPis beispielsweise in Uni-Netzen betrieben werden können.

## Grundprinzip

Das Projekt verfolgt das Prinzip:

So schlank wie möglich, aber sinnvoll wie nötig.

Das Data Model soll ausreichend Informationen für:

- Dashboard
- Diagnose
- Betrieb
- Health-Bewertung
- Events und Alerts
- spätere Erweiterungen

bereitstellen, ohne unnötige Daten oder vollständige Systemdumps zu übertragen.

## Architektur

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

Herstellerspezifische Feldnamen werden dabei nicht direkt zum universellen Data Model.

Neue Sensoren und Datenquellen sollen über Adapter in das gemeinsame Modell integriert werden können.

## Aktueller Stand

Data Model v1 Feldkatalog: abgeschlossen

Einheitenkatalog v1: abgeschlossen

Core Batch: in Bearbeitung

Services: als Struktur definiert, konkreter LoggerPi-Servicebestand noch abzugleichen

API: noch nicht finalisiert

Queue / Retry / ACK: konzeptionell festgelegt, technische Spezifikation noch offen

Metadata-Synchronisation: konzeptionell festgelegt, technische Spezifikation noch offen

## Batch Envelope

Der Batch verwendet grundsätzlich:

schema_version
batch_id
logger_id
created_at
sequence

sequence ist pro LoggerPi persistent und monoton fortlaufend.

Retries verändern weder batch_id noch sequence.

Die dauerhafte Zustell- und Retry-Logik basiert auf batch_id, persistenter Queue und Idempotenz.

## Zeitmodell

created_at

Zeitpunkt der Batch-Erzeugung auf dem LoggerPi.

measured_at

Zeitpunkt der tatsächlichen Messwerterfassung.

received_at

Zeitpunkt des Empfangs auf dem OtterPi.

Diese Zeitbegriffe werden nicht miteinander vermischt.

## Core System

Der bisher definierte Systembereich umfasst:

system.identity
system.time
system.boot
system.cpu
system.processes
memory
swap
storage
network
connectivity
services
autostart
timers

Dabei werden laufende Telemetriedaten von statischen Metadata getrennt.

## Sensor- und Gerätedaten

Das Data Model berücksichtigt unter anderem:

- Serial / RS-232
- Freezer
- AtmoWEB
- Temperatur
- Feuchte
- Vakuum
- CO2
- O2
- Lüfterdrehzahl
- Gerätezustände
- Betriebszustände
- Events und Alarme

Herstellerdaten werden über Adapter in gemeinsame fachliche Felder übersetzt.

## Wichtige Entscheidungen

- LoggerPi erfasst technische Fakten.
- OtterPi bewertet fachliche Zustände und Health.
- Data Model und tatsächlicher Core Batch sind getrennt.
- Hersteller-API-Namen werden nicht als universelle Feldnamen verwendet.
- Measurements, States, Metadata, Configuration, Health und Events werden getrennt behandelt.
- Rohwerte und sinnvolle abgeleitete Werte dürfen gemeinsam übertragen werden.
- validity gehört zum Messwertmodell.
- Es gibt keine measurements.misc und keine states.misc.
- Prozesslisten sind nicht Bestandteil des regulären Core Batches.
- Netzwerkinterfaces werden unter network.interfaces geführt.
- blocked ist Bestandteil des Interface-Modells.
- Unnötige aktive Connectivity-Tests werden vermieden.
- Setpoints und Alarmgrenzen sind keine Measurements.
- LOG- und Alarminformationen werden als Events behandelt.
- Metadata wird nicht unnötig in jedem regulären Batch wiederholt.
- Metadata-Änderungen müssen über den normalen LoggerPi → OtterPi Kommunikationsweg übertragen werden.
- Der OtterPi darf nicht auf eine aktive Verbindung zum LoggerPi angewiesen sein.

## Repository-Struktur

Die ausführliche Projektdokumentation wird getrennt vom README geführt.

Geplante Struktur:

docs/

LoggerPi_OtterPi_DataModel_v1_Feldkatalog.md

LoggerPi_OtterPi_DataModel_v1_Wiedereinstiegsprotokoll.md

Weitere technische Dokumente werden bei Bedarf ergänzt.

## Aktueller Wiedereinstiegspunkt

Der Feldkatalog und der Einheitenkatalog sind abgeschlossen.

Der nächste fachliche Arbeitsschritt ist:

Tatsächlichen LoggerPi-Servicebestand prüfen und gegen das Data Model abgleichen.

Danach wird der konkrete Core Batch aus dem Feldkatalog abgeleitet.

## Status

Projektphase:

Data Model v1 / API Design

Aktueller Arbeitspunkt:

Core Batch → Services
