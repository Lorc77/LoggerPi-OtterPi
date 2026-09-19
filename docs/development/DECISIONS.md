# Entwicklungs- und Architekturentscheidungen

Dieses Dokument hält wichtige Entscheidungen fest, die während der
Vorbereitung und Implementierung des Projekts LoggerPi-OtterPi getroffen
wurden.

Entscheidungen sollen kurz begründet und bei einer Änderung ihres
Status aktualisiert werden.

---

## DEC-001 — Windows + VS Code als Entwicklungsumgebung

**Status:** Angenommen

Die primäre Entwicklungsumgebung ist Windows 11 mit der stabilen
Version von Visual Studio Code.

VS Code Insiders wird nicht verwendet.

### Begründung

Die stabile VS-Code-Version bietet die benötigte Editor-, Git-,
Terminal-, Debugging- und Erweiterungsunterstützung, ohne die
zusätzliche Instabilität einer Insider-Version.

---

## DEC-002 — GitHub als zentrale Versionsverwaltung

**Status:** Angenommen

GitHub bleibt das zentrale Remote-Repository.

Das lokale Repository wird mit Git for Windows verwaltet und verwendet
HTTPS sowie Git Credential Manager zur Authentifizierung.

Der Hauptbranch ist `main`.

---

## DEC-003 — Kein Docker auf LoggerPi oder OtterPi

**Status:** Angenommen

Docker und Container-Laufzeiten sind nicht Bestandteil der
Laufzeitarchitektur von LoggerPi oder OtterPi.

### Begründung

Beide Geräte sollen möglichst schlank und betrieblich einfach bleiben.

Container würden zusätzlichen Laufzeit-, Speicher- und
Administrationsaufwand verursachen, ohne dass derzeit ein
entsprechender architektonischer Nutzen besteht.

---

## DEC-004 — Unterschiedliche Python-Versionen sind zulässig

**Status:** Angenommen

LoggerPi und OtterPi müssen nicht dieselbe Python-Version verwenden.

### Begründung

Die Systeme kommunizieren über den versionierten Core-Batch-
HTTP-/JSON-Contract.

Die Python-Laufzeit ist daher eine Implementierungsentscheidung des
jeweiligen Systems.

Aktueller Stand:

- LoggerPi: Python 3.9.2
- OtterPi: Python 3.13.5

---

## DEC-005 — LoggerPi möglichst wenig verändern

**Status:** Angenommen

Das bestehende Betriebssystem und die vorhandene System-Python-
Installation des LoggerPi sollen während der ersten Migrationsphase
nicht verändert werden, sofern kein konkreter technischer Grund dies
erfordert.

### Begründung

Der LoggerPi betreibt derzeit noch die Legacy-Observer-Kette.

Ein gleichzeitiger Austausch von Betriebssystem, Python-Laufzeit und
Anwendung würde Fehlersuche und Migration unnötig erschweren.

Die neue Implementierung wird zunächst möglichst parallel zur
bestehenden Umgebung eingeführt.

---

## DEC-006 — Python 3.13.15 für die Windows-Entwicklung

**Status:** Angenommen

Python 3.13.15 ist die derzeit vorgesehene Python-Version für den
Windows-Entwicklungsrechner.

Dies ist noch keine endgültige projektweite Python-
Laufzeitfestlegung.

### Begründung

Python 3.13 ist bereits die native Python-Serie des OtterPi und stellt
eine aktuelle Entwicklungsumgebung unter Windows bereit.

LoggerPi verwendet derzeit Python 3.9.2. Python 3.9 ist jedoch
End-of-Life.

Die endgültige Kompatibilitätsstrategie wird nach Prüfung der
tatsächlich benötigten Abhängigkeiten und der LoggerPi-
Laufzeitbedingungen festgelegt.

---

## DEC-007 — ChatGPT als KI-Unterstützung

**Status:** Angenommen

ChatGPT wird als KI-Unterstützung für Entwicklung, Analyse,
Dokumentation, Reviews und Fehlersuche eingesetzt.

Die KI-Unterstützung ersetzt weder Versionsverwaltung noch Tests oder
bewusste technische Entscheidungen.

---

## DEC-008 — Google Antigravity nicht Bestandteil der Pipeline

**Status:** Angenommen

Google Antigravity SDK bzw. darauf basierende Entwicklungswerkzeuge
sind nicht Bestandteil der geplanten Entwicklungs- und
Laufzeitpipeline.

### Begründung

Das Projekt soll unnötige externe Werkzeuge und zusätzliche
Abhängigkeiten möglichst vermeiden.

---

## DEC-009 — Core Batch v1 als erster Implementierungsschnitt

**Status:** Angenommen

Die Implementierung beginnt mit dem End-to-End-Pfad des Core Batch v1.

Der erste vertikale Schnitt lautet:

LoggerPi

→ Erzeugung des Core Batch

→ persistente lokale Queue

→ HTTP POST

→ OtterPi

→ Contract-Validierung

→ Duplicate Handling

→ HTTP 202 Accepted

Die bestehenden Legacy-Datenquellen werden erst ersetzt, wenn der neue
Pfad erfolgreich validiert wurde.

---

## DEC-010 — Legacy-LoggerPi als Migrationsreferenz

**Status:** Angenommen

Die bestehende LoggerPi-Observer-Implementierung wird als Legacy-
Referenz und technische Baseline behandelt.

Sie ist nicht die Architektur der neuen Implementierung.

Der bestehende produktive Datenpfad darf nicht allein aufgrund der
Existenz der neuen Implementierung abgeschaltet werden.

---

## DEC-011 — Projektlokale Python-Umgebung

**Status:** Angenommen

Die Python-Entwicklung erfolgt innerhalb einer projektlokalen virtuellen
Umgebung (`.venv`).

Für das Repository `LoggerPi-OtterPi` liegt diese Umgebung im
Projekt-Root:

`.venv\`

VS Code verwendet die projektlokale Umgebung als Python-Interpreter.

### Begründung

Die Entwicklungsumgebung soll unabhängig von anderen Python-Projekten auf
dem Windows-Entwicklungsrechner bleiben.

Eine projektlokale virtuelle Umgebung verhindert, dass
Projektabhängigkeiten unkontrolliert in die systemweite Python-Installation
gelangen.

Gleichzeitig bleibt die systemweite Python-Installation als gemeinsame
technische Basis für die Erstellung und Verwaltung der virtuellen
Umgebungen erhalten.

### Konsequenzen

- Projektabhängigkeiten werden innerhalb der `.venv` installiert.
- Die `.venv` wird nicht in Git versioniert.
- VS Code verwendet für dieses Repository die `.venv`.
- Andere Python-Projekte können eigene virtuelle Umgebungen und
  Abhängigkeiten verwenden.
- Die Verwendung von Python 3.13.15 als Entwicklungsbasis legt weiterhin
  nicht die endgültige Python-Kompatibilität der Anwendung fest.

---

## DEC-012 — Versionierung der Entwicklungswerkzeuge

**Status:** Angenommen

Für die Python-Entwicklung werden `pytest` und Ruff als
Entwicklungswerkzeuge eingesetzt.

Die Entwicklungswerkzeuge sind keine Runtime-Abhängigkeiten der Anwendung
und werden nicht auf LoggerPi oder OtterPi vorausgesetzt.

### Festgelegte Werkzeuge

Für die Entwicklungsumgebung gelten derzeit folgende Versionsbereiche:

- `pytest >=8.4,<9`
- `ruff >=0.16.5,<0.17`

Die konkret auf dem Entwicklungsrechner installierten Versionen können
innerhalb dieser Bereiche aktualisiert werden.

### Begründung

Tests und statische Codeprüfung sollen auf dem Entwicklungsrechner
ausgeführt werden, ohne die Runtime-Umgebungen der Zielsysteme mit
zusätzlichen Entwicklungsabhängigkeiten zu belasten.

Die Versionen werden über die Python-Projektkonfiguration
(`pyproject.toml`) reproduzierbar festgelegt.

### Zielsysteme

Auf den Zielsystemen gelten ausschließlich die für den Betrieb der
Anwendung erforderlichen Runtime-Abhängigkeiten.

`pytest` und Ruff müssen dort nicht installiert sein.

Die derzeit bekannten Python-Versionen der Zielsysteme sind:

- LoggerPi: Python 3.9.2
- OtterPi: Python 3.13.5

Diese Python-Versionen werden bei der späteren Festlegung der
Runtime-Kompatibilität berücksichtigt.

### Konsequenzen

- Development Dependencies und Runtime Dependencies werden getrennt
  behandelt.
- Ein frischer Entwicklungsrechner soll die definierten Werkzeuge über
  die Projektkonfiguration reproduzierbar installieren können.
- Änderungen an den Entwicklungswerkzeugen können unabhängig von den
  Runtime-Abhängigkeiten erfolgen.
- Die Python-Kompatibilität der Anwendung bleibt eine separate
  Architekturentscheidung und wird nicht durch die Versionen von pytest
  oder Ruff festgelegt.

---

## DEC-013 — Python-Kompatibilität und Quality Gates

**Status:** Accepted
**Datum:** 2026-08-30

### Kontext

LoggerPi-OtterPi soll aktuell mindestens mit Python 3.9 kompatibel bleiben, während die lokale Entwicklung derzeit mit Python 3.13 erfolgt.

Ein ausschließlich unter Python 3.13 ausgeführter Testlauf kann jedoch Python-3.9-Inkompatibilitäten übersehen.

Genau dies ist bereits bei Type-Annotationen mit PEP-604-Syntax (`str | None`, `str | Path`) aufgetreten.

### Entscheidung

Python 3.9 bleibt derzeit die minimale unterstützte Python-Version.

Die Kompatibilität wird auf mehreren Ebenen abgesichert:

- `requires-python = ">=3.9"` definiert die minimale Version.
- Ruff verwendet `target-version = "py39"`.
- Ruff prüft zusätzlich mit `FA102` auf problematische Type-Annotationen.
- Für Type-Annotationen wird grundsätzlich Python-3.9-kompatible Syntax verwendet.
- `from __future__ import annotations` wird nicht pauschal als Lösung verwendet, um neuere Annotation-Syntax unter Python 3.9 zu ermöglichen.
- Die CI testet den Code sowohl unter Python 3.9 als auch unter Python 3.13.
- Lokale Entwicklung verwendet Python 3.13 in der projektlokalen `.venv`.
- `FA102` wird dabei ausdrücklich als statisches Teil-Gate für
  Type-Annotation-Kompatibilität verstanden und nicht als vollständiger
  Python-3.9-Kompatibilitätstest.

### Begründung

Die Kombination aus statischer Analyse und tatsächlicher Ausführung unter der minimal unterstützten Python-Version verhindert, dass Kompatibilitätsprobleme ausschließlich durch einen Wechsel des lokalen Interpreters unbemerkt bleiben.

Die klassische Python-3.9-Type-Annotation-Syntax mit `Optional` und `Union` wurde bewusst gewählt, weil sie ohne zusätzliche Laufzeitsemantik unmittelbar mit der minimal unterstützten Version kompatibel ist.

`from __future__ import annotations` ist nicht grundsätzlich abzulehnen, wird für diesen Zweck aber nicht als Standardmechanismus des Projekts verwendet.

### Konsequenz

Eine erfolgreiche lokale Test-Suite unter Python 3.13 ist nicht ausreichend.

Vor einem Commit müssen die lokalen Quality Gates erfolgreich sein. Vor dem Zusammenführen einer Änderung müssen außerdem die Python-3.9- und Python-3.13-CI-Läufe erfolgreich sein.

Die konkreten Entwicklungs- und Prüfregeln sind in `docs/development/DEVELOPMENT-QUALITY.md` dokumentiert.

---

## DEC-014 — Stabilisierung des Legacy-Freezer-Loggers über systemd User Service

Status: Angenommen
Datum: 2026-09-07

### Kontext

Die Legacy-Freezer-Protokollierung wurde ursprünglich über einen grafischen XDG/LXDE-Autostart mit `lxterminal` und `minicom` betrieben.

Der bisherige Startmechanismus hatte eine unnötige Abhängigkeit von der grafischen Terminalumgebung. Gleichzeitig muss der bestehende Legacy-Freezer-Datenpfad weiterhin zuverlässig betrieben werden, da die Legacy-`observer.py` den aktuellen Freezer-Wert aus `freezer.log` liest.

### Entscheidung

Die kontinuierliche Freezer-Protokollierung wird künftig über einen dedizierten `systemd --user`-Service betrieben.

Der Service lautet:

    `freezer-log.service`

Er wird unter dem Benutzer `ZOOLOGY-observ` betrieben und über `default.target` automatisch gestartet.

`minicom` wird innerhalb einer virtuellen PTY-Umgebung über `/usr/bin/script` ausgeführt.

Der technische Datenpfad lautet:

    `/dev/ttyUSB0`
          ↓
       minicom
          ↓
     freezer.log

Der bisherige grafische Terminal-Autostart wird nicht mehr als Startmechanismus verwendet.

### Begründung

Der Freezer-Logger benötigt keine grafische Benutzeroberfläche für die eigentliche Datenerfassung.

Die serielle Schnittstelle und `minicom` können als dauerhafter User-Service betrieben werden. Die Verwendung von `script` stellt die von `minicom` benötigte virtuelle Terminalumgebung bereit.

Damit wird die Legacy-Datenerfassung:

  * unabhängig von einem geöffneten Terminalfenster,
  * unabhängig von einer aktiven LXDE-Terminalsitzung,
  * automatisch nach einem Reboot gestartet,
  * über systemd überwacht,
  * über den normalen User-Service-Mechanismus administrierbar.

Die grafische Umgebung bleibt trotzdem erhalten, da sie weiterhin als lokaler Recovery- und Konfigurationsweg des LoggerPi vorgesehen ist.

### Konsequenzen

Der Freezer-Logger wird nicht mehr über XDG/LXDE-Terminal-Autostart gestartet.

Die bestehende Datei

    `/home/ZOOLOGY-observ/.config/autostart/TerminalAutostart.desktop`

ist kein aktiver Bestandteil des Runtime-Starts mehr.

Der Legacy-Datenpfad über `freezer.log` bleibt unverändert, damit die bestehende `observer.py` weiterhin funktioniert.

Die Entscheidung stellt keine Migration des Freezers in das neue Data Model dar. Sie stabilisiert ausschließlich den bestehenden Legacy-Datenpfad.

Eine spätere vollständige Migration des Freezers soll weiterhin über einen dedizierten Adapter/Reader in das neue Measurement-Modell erfolgen.

---

## DEC-015 — OtterPi als persistenter Core-Batch-Empfänger

**Status:** Accepted
**Datum:** 2026-09-17

### Kontext

Der bisher spezifizierte LoggerPi → OtterPi Push-Weg war zunächst nur auf
Vertragsebene definiert.

Für die weitere Entwicklung wird nun ein tatsächlich persistenter
serverseitiger Empfänger benötigt, damit eingehende Core Batches nicht nur
technisch angenommen, sondern auch lokal gespeichert und später für
Dashboard, Diagnose und weitere Verarbeitung verwendet werden können.

### Entscheidung

Der OtterPi implementiert einen eigenen HTTP-Ingestion-Endpunkt:

```text
POST /api/v1/batches
```

Eingehende Core Batches werden nach erfolgreicher Validierung an einen
serverseitigen `BatchStore` übergeben und persistent gespeichert.

Die Persistenz erfolgt zunächst über SQLite.

Der HTTP-Empfänger bleibt bewusst unabhängig von nginx, MeshCentral und
anderen bestehenden OtterPi-Diensten.

### Begründung

Damit entsteht ein kleiner, eigenständiger und lokal testbarer vertikaler
Datenpfad:

```text
LoggerPi
    ↓
HTTP
    ↓
OtterPi
    ↓
BatchStore
    ↓
SQLite
```

Diese Struktur ermöglicht es, die neue Architektur parallel zum bestehenden
Legacy-Betrieb einzuführen, ohne den vorhandenen LoggerPi-Datenpfad sofort
ablösen zu müssen.

### Konsequenz

Der OtterPi besitzt nun eine erste tatsächlich persistente Ingestion-Schicht.

Die spätere Dashboard-, Health-, Event- und Auswertungslogik kann auf dieser
Persistenz aufbauen.

Die fachliche Bewertung der Daten bleibt weiterhin Aufgabe des OtterPi.

---

## DEC-016 — SQLite WAL und `synchronous=NORMAL`

**Status:** Accepted
**Datum:** 2026-09-17

### Kontext

Der OtterPi benötigt für den ersten persistenten BatchStore eine lokale,
robuste und wartungsarme Datenbank.

Der erwartete Zugriff besteht zunächst aus häufigen kleinen Batch-Schreibvorgängen
sowie späteren Lesezugriffen durch Dashboard und Diagnose.

### Entscheidung

Der `BatchStore` verwendet SQLite mit:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

Die PRAGMAs werden beim Aufbau jeder SQLite-Verbindung gesetzt.

### Begründung

WAL (`Write-Ahead Logging`) erlaubt parallele Lesezugriffe während
Schreibvorgängen und passt damit zum vorgesehenen Muster aus kontinuierlicher
Batch-Ingestion und lesendem Dashboard-Zugriff.

`synchronous=NORMAL` reduziert gegenüber dem strengeren synchronen Modus
den Schreibaufwand, während SQLite weiterhin die WAL-basierte
Transaktionssicherheit verwendet.

Die Einstellung ist für den aktuellen lokalen OtterPi-Einsatz bewusst als
pragmatische Balance zwischen Persistenzsicherheit und Schreibaufwand gewählt.

### Konsequenz

Der aktuelle BatchStore bleibt bewusst einfach:

```text
HTTP request
    ↓
BatchStore
    ↓
SQLite WAL
```

Eine komplexere Datenbank oder zusätzliche Persistenzschicht ist für den
aktuellen Entwicklungsstand nicht erforderlich.

Die Performance- und Speichercharakteristik soll später anhand realer
LoggerPi-Batchraten beobachtet werden, bevor weitere Optimierungen eingeführt
werden.

---

## DEC-017 — OtterPi Application Listener hinter bestehendem nginx

**Status:** Accepted
**Datum:** 2026-09-19

### Kontext

Der OtterPi-Core-Batch-Empfänger stellt einen lokalen HTTP-Listener
für `POST /api/v1/batches` bereit.

Die Anwendung lauscht derzeit ausschließlich auf:

```text
127.0.0.1:8090
```

Der OtterPi besitzt bereits einen bestehenden nginx-/TLS-Stack für
öffentliche HTTP-/HTTPS-Dienste.

### Entscheidung

Der LoggerPi → OtterPi HTTP-Datenpfad soll für den produktiven Betrieb
über den bestehenden nginx-/TLS-Stack geführt werden.

Die Anwendung selbst bleibt dabei unabhängig von nginx.

```text
LoggerPi
    ↓
HTTPS
    ↓
nginx
    ↓
127.0.0.1:8090
    ↓
OtterPi Observer
```

Port `8090` bleibt ein lokaler Backend-Port und wird nicht als
öffentlicher API-Port verwendet.

### Begründung

Damit bleiben Anwendung und HTTP-Ingestion klein und unabhängig,
während TLS und öffentliche HTTP-Erreichbarkeit durch die bereits
vorhandene Host-Infrastruktur bereitgestellt werden.

Der Core-Batch-API-Vertrag bleibt unabhängig von:

- nginx
- TLS
- DNS
- CDN/Tunnel
- Host-Firewall

### Konsequenz

Das Application Deployment konfiguriert nginx derzeit nicht automatisch.

Die konkrete nginx-Proxy-Konfiguration und die zugehörige Produktions-
Domain müssen separat dokumentiert und verifiziert werden.

Vor produktiver Nutzung muss außerdem eine geeignete
Authentication-/Authorization-Lösung festgelegt werden.

---

# Offene Entscheidungen

Folgende Punkte sind derzeit bewusst noch offen:

- endgültiger Python-Kompatibilitätsbereich
- benötigte Python-Abhängigkeiten
- konkrete Retry-/Backoff-Parameter
- Queue-Größe und Aufbewahrungsdauer
- Umgang mit dauerhaft nicht zustellbaren Batches
- Persistenzimplementierung des OtterPi
- Authentifizierung und Autorisierung im produktiven Betrieb
- endgültige WeatherHub-Adapterimplementierung
- Zeitpunkt der Ablösung des Legacy-Observers
