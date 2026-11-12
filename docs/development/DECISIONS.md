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

## DEC-018 — Umbenennung `queue.py` → `batch_queue.py`

**Status:** Angenommen
**Datum:** 2026-09-19

### Kontext

Die persistente lokale Queue war zunächst in `queue.py` implementiert.

Beim Import `from queue import BatchQueue` bestand jedoch ein Konflikt mit
dem Python-Standardmodul `queue`.

### Entscheidung

Die Datei wird in `batch_queue.py` umbenannt.

Alle Imports werden entsprechend angepasst:

```python
from batch_queue import BatchQueue
```

### Begründung

Der Name `batch_queue` ist eindeutig und kollidiert nicht mit dem
Python-Standardmodul `queue`.

### Konsequenz

- `queue.py` existiert nicht mehr.
- `batch_queue.py` ist die neue Bezeichnung.
- Alle Imports in `runtime.py`, `loggerpi_observer.py` und Tests wurden
  angepasst.
- Die `install.sh`-Dateien wurden entsprechend aktualisiert.

---

## DEC-019 — Flache Deploy-Struktur und `PYTHONPATH`

**Status:** Angenommen
**Datum:** 2026-09-19

### Kontext

Die Installation kopiert die Anwendungsdateien **flach** nach
`/opt/loggerpi-otterpi/`.

Es wird kein `pip install -e .` verwendet.

### Entscheidung

Die flache Deploy-Struktur wird beibehalten.

Da `model/` ein Unterverzeichnis ist, wird `PYTHONPATH` explizit gesetzt:

```bash
PYTHONPATH=/opt/loggerpi-otterpi:/opt/loggerpi-otterpi/model
```

Dies wird in den Service-Dateien und `.env`-Dateien konfiguriert.

### Begründung

Die flache Struktur ist bewusst gewählt, um ohne `pip`, Virtualenv und
Package-Import auszukommen.

### Konsequenz

- `PYTHONPATH` muss in den Service-Dateien gesetzt werden.
- Lokal unter Windows funktionieren Imports über `pythonpath` in
  `pyproject.toml`.

---

## DEC-020 — Deployment-Versionierung mit `DEPLOYED_VERSION`

**Status:** Angenommen
**Datum:** 2026-09-19

### Kontext

Bisher wurde nach erfolgreichem Deployment nur `DEPLOYED_COMMIT` geschrieben.

Für eine menschenlesbare Version fehlte eine entsprechende Datei.

### Entscheidung

Zusätzlich zu `DEPLOYED_COMMIT` wird `DEPLOYED_VERSION` geschrieben:

```text
/opt/loggerpi-otterpi/DEPLOYED_COMMIT    technischer Git-Commit
/opt/loggerpi-otterpi/DEPLOYED_VERSION   menschenlesbare Version (z. B. v1.0.0)
/opt/loggerpi-otterpi/VERSION            Version aus pyproject.toml (z. B. 1.0.0)
```

Die `DEPLOYED_*`-Dateien werden **nur bei erfolgreichem Update** geschrieben
(Fail-safe-Design).

### Begründung

Damit ist auf dem Zielsystem sofort erkennbar, welche Version tatsächlich
läuft.

### Konsequenz

- `update.sh` schreibt `DEPLOYED_COMMIT` und `DEPLOYED_VERSION`.
- `install.sh` schreibt `VERSION`.
- Bei fehlgeschlagenem Update bleibt die bisherige Version bestehen.

---

## DEC-021 — Erste Release-Version `v1.0.0`

**Status:** Angenommen
**Datum:** 2026-09-19

### Kontext

Der erste reproduzierbare Deployment-Mechanismus ist implementiert und
auf dem OtterPi praktisch verifiziert.

### Entscheidung

Die erste Release-Version wird als `v1.0.0` getaggt.

### Begründung

Der aktuelle Stand ist stabil und getestet (68 Tests).

### Konsequenz

- `pyproject.toml` enthält `version = "1.0.0"`.
- `__init__.py` enthält `__version__ = "1.0.0"`.
- Git-Tag `v1.0.0` ist gesetzt und gepusht.

---

## DEC-022 — AtmoWEB JSON-Fragment-Parsing

**Status:** Angenommen
**Datum:** 2026-09-20

### Kontext

Die realen AtmoWEB-Geräte (HPP260) liefern ihre Antworten als
JSON-Fragment ohne umschließende geschweifte Klammern:

```text
"SN": "W616.0154", "DevType": "HPP260", ...
```

Zusätzlich endet die Antwort mit einem trailing Leerzeichen nach dem
letzten Komma.

### Entscheidung

`atmoweb.py` behandelt das JSON-Fragment als Standard und ergänzt die
Klammern:

```python
json_text = "{" + body.strip().rstrip(",") + "}"
```

Gültiges JSON (z. B. in Tests) wird als Fallback unterstützt.

### Begründung

Der produktive Standardfall (reales AtmoWEB) benötigt nur einen
Parsing-Versuch.

### Konsequenz

- `_request()` unterstützt beide Formate.
- Das trailing Leerzeichen wird mit `strip()` entfernt.

---

## DEC-023 — `OTTERPI_URL` mit vollständigem API-Pfad

**Status:** Angenommen
**Datum:** 2026-09-20

### Kontext

Der LoggerPi sendete Batches an `https://loggerpi.makki.route64.de`
(ohne Pfad). nginx leitete `/` an `return 404` weiter, sodass die
Delivery fehlschlug.

### Entscheidung

`OTTERPI_URL` muss den vollständigen API-Pfad enthalten:

```bash
OTTERPI_URL=https://loggerpi.makki.route64.de/api/v1/batches
```

### Begründung

Der `BatchDelivery` sendet direkt an den konfigurierten Endpoint.
Ohne den Pfad wird nginx-Root (`404`) erreicht.

### Konsequenz

- `loggerpi.env.example` enthält den vollständigen Pfad.
- Bestehende Installationen müssen die URL manuell anpassen.

---

## DEC-024 — Graceful Shutdown mit `threading.Event`

**Status:** Angenommen
**Datum:** 2026-09-20

### Kontext

Der `LoggerPiRunner` nutzte `time.sleep(interval)` (bis zu 900s).
Bei `SIGTERM` konnte der Prozess nicht schnell stoppen → systemd
killte ihn nach 90s mit `SIGKILL`.

### Entscheidung

Statt `time.sleep()` wird `threading.Event.wait(timeout)` verwendet:

```python
self._stop_event.wait(delay)
```

`request_stop()` setzt das Event → `wait()` kehrt sofort zurück.

### Begründung

`Event.wait(timeout)` blockiert ressourcenschonend (kein ständiges
Aufwachen) und reagiert sofort auf Stopp.

### Konsequenz

- Service stoppt sauber (kein `SIGKILL` mehr).
- Ressourcenschonend (keine 1-Sekunden-Schleife).

---

## DEC-025 — E2E-Datenpfad praktisch verifiziert

**Status:** Angenommen
**Datum:** 2026-09-20

### Kontext

Der komplette Datenpfad LoggerPi → OtterPi war implementiert, aber noch
nicht praktisch verifiziert.

### Entscheidung

Der E2E-Datenpfad gilt als praktisch verifiziert:

```text
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
```

### Begründung

LoggerPi und OtterPi laufen produktiv auf `v1.0.4` und übertragen
Batches kontinuierlich (alle 15 Minuten). Die SQLite-Datenbank wächst
nachweislich.

### Konsequenz

- Der E2E-Datenpfad ist als verifiziert zu dokumentieren.
- Weitere Datenquellen (Freezer, IPP300) können schrittweise angebunden
  werden.

---

## DEC-026 — Bearer-Token-Authentication

**Status:** Angenommen
**Datum:** 2026-09-21

### Kontext

Die Übertragung LoggerPi → OtterPi war ungeschützt.

### Entscheidung

Seit `v1.1.0` verwendet die Übertragung einen Bearer-Token:

```text
Authorization: Bearer <token>
```

Der Token wird in `loggerpi.env` (`LOGGERPI_TOKEN`) und `otterpi.env`
(`OTTERPI_TOKEN`) gespeichert.

### Begründung

Schlanke, aber sinnvolle Absicherung der Übertragung.

---

## DEC-027 — Dashboard auf dem OtterPi

**Status:** Angenommen
**Datum:** 2026-09-21

### Kontext

Die gesammelten Batches waren nur in SQLite sichtbar.

### Entscheidung

Seit `v1.2.0` stellt der OtterPi ein Dashboard unter `https://observer.makki.route64.de` und eine Einstiegsseite unter `https://zoology.makki.route64.de` bereit.

Das Dashboard zeigt:
- aktuelle Werte (Temp/Feuchte der MEMMERT HPP260)
- Charts (letzte 48h)
- System-Info

### Begründung

Erster sichtbarer Mehrwert – Daten werden nutzbar.

---

## DEC-028 — Dashboard im OtterPi-Observer integriert

**Status:** Angenommen
**Datum:** 2026-09-21

### Kontext

Das Dashboard hätte als separater Service laufen können.

### Entscheidung

Das Dashboard ist in den OtterPi-Observer integriert (`do_GET`).

### Begründung

Schlanker – kein neuer Service, ein Prozess.

---

## DEC-029 — Raum-basiertes Dashboard

**Status:** Angenommen
**Datum:** 2026-09-21

### Entscheidung

Das Dashboard wird raum-basiert umgebaut:

- `/` → Übersicht mit Raum-Kacheln
- `/raum/<id>` → Detailseite mit Charts

### Begründung

Bessere Orientierung – Räume statt Geräte.

---

## DEC-030 — Freezer direkt über Seriell statt minicom+freezer.log

**Status:** Angenommen
**Datum:** 2026-09-22

### Kontext

Der Freezer (Thermo Scientific HFC-Serie) sendet alle ~60 Minuten
eine Meldung über RS-232. Bisher wurde diese über `minicom` in
`freezer.log` geschrieben und vom Legacy-Observer gelesen.

### Entscheidung

Der neue `FreezerReader` liest die Meldungen direkt von der
Seriell-Schnittstelle (FTDI FT232R A9NX8YRE, 1200 8N2).

`minicom`/`freezer-log.service` wurde deaktiviert.

### Begründung

- Kein Umweg über eine Logdatei
- Kein separater Prozess (minicom)
- Ressourcenschonend (dauerhafte Verbindung, kein Polling)
- `measured_at` = Empfangszeit auf dem LoggerPi (UTC), da der
  Freezer keine eigene Zeit sendet

---

## DEC-031 — ThingSpeak-Injektion als semi-redundanter Speicher

**Status:** Angenommen
**Datum:** 2026-09-22

### Kontext

ThingSpeak wurde bisher über den Legacy-Observer beschrieben.
Nach dessen Ablösung soll ThingSpeak als semi-redundanter
Speicher weitergeführt werden.

### Entscheidung

Eine optionale `ThingSpeakDelivery` liest Werte aus dem Core Batch
und sendet sie im Legacy-Format an ThingSpeak (field1–field7).

Aktivierbar über `LOGGERPI_THINGSPEAK_ENABLED=1`.

`field8` (LED) wird bewusst noch nicht gesendet – bis States/Events
in den Batch integriert sind.

### Begründung

- ThingSpeak bleibt als Backup erhalten
- Kein Legacy-Wissen im Core Batch
- Leicht entfernbar (eigene Komponente)

---

## DEC-032 — `measured_at` einheitlich als LoggerPi-Empfangszeit

**Status:** Angenommen
**Datum:** 2026-09-23

### Kontext

Verschiedene Datenquellen liefern unterschiedliche Zeitstempel:

- AtmoWEB sendet `Time` mit eigener (teilweise falscher) Zeitzone
  (real beobachtet: `+01:00` statt `+02:00` in der Sommerzeit)
- Freezer sendet keine Zeit
- MEMMERT IPP300 (geplant) liefert keine Zeit

Die Gerätezeiten können abweichen (falsche Zeitzone, keine
automatische Sommerzeit-Umstellung).

### Entscheidung

`measured_at` wird einheitlich auf die LoggerPi-Empfangszeit (UTC)
gesetzt – für alle Datenquellen.

Die Gerätezeit wird weiterhin abgefragt (wo möglich) und als
separates Attribut am Reader (`reader.device_time`) verfügbar
gemacht. Sie ist nicht Teil von `measured_at`.

### Begründung

- Konsistente Zeitbasis für alle Messwerte
- Keine Abhängigkeit von korrekt konfigurierten Gerätezeiten
- Sommerzeit-sicher (LoggerPi stellt automatisch um)
- LoggerPi ist die vertrauenswürdige Zeitquelle (NTP/Zeitsynchronisation)
- Gerätezeit bleibt für Diagnose/Zugriff bei Bedarf erhalten

### Konsequenzen

- `measured_at` in allen Readern = `datetime.now(timezone.utc)`
- Gerätezeit nur noch als separates Attribut (`device_time`)
- Doku (`core-batch-v1.md`, `core-batch-v1-json.md`) angepasst

Quelle	measured_at	zusätzliche Gerätezeit
AtmoWEB	LoggerPi UTC	device_time
Freezer	LoggerPi UTC	keine
MEMMERT IPP300	LoggerPi UTC	keine
WeatherHub	LoggerPi UTC	gateway_timestamp

---

## DEC-033 — WeatherHub Gateway Proxy Integration

**Status:** Angenommen
**Datum:** 2026-10-26

### Kontext

Die WeatherHub-Sensoren senden ihre Daten per Funk an ein
MOBILE-ALERTS-Gateway. Normalerweise überträgt das Gateway die Daten
an die TFA-Cloud (`www.data199.com`).

Ziel war es, die Sensordaten lokal am LoggerPi zu empfangen und in das
bestehende LoggerPi-OtterPi-Datenmodell zu integrieren.

### Entscheidung

Das Gateway `.121` wird in den **Proxymodus** versetzt. Es sendet seine
Daten nicht mehr an die Cloud, sondern per HTTP PUT an den LoggerPi
(Port 3778).

Auf dem LoggerPi läuft ein **WeatherHubGatewayListener** als
Background-Thread innerhalb des `loggerpi.observer.service`. Er
empfängt die HTTP-PUT-Requests, dekodiert die Payload mit dem
**WeatherHubGatewayDecoder** und übergibt die dekodierten Pakete an
den **WeatherHubReader**.

Der Reader speichert die neuesten Werte pro Sensor und gibt sie beim
nächsten Batch-Zyklus (alle 15 Minuten) an die Runtime zurück.

Gateway `.132` bleibt unverändert im Cloud-Modus.

### Begründung

- Kein Umweg über die TFA-Cloud (lokal, datensparsam)
- Proxymodus nutzt die vorhandene Gateway-Firmware (kein Hardware-Eingriff)
- Listener als Thread ist ressourcenschonend (wartet auf Verbindungen)
- Reader sammelt kontinuierlich und integriert in den Batch-Zyklus
- 17 Sensoren werden empfangen (ID01, ID03, ID0E)

### Konsequenzen

- `LOGGERPI_WEATHERHUB_ENABLED=1` aktiviert die Integration
- `WEATHERHUB_LISTENER_HOST` / `WEATHERHUB_LISTENER_PORT` konfigurieren den Listener
- `WEATHERHUB_GATEWAY_ALLOWLIST` begrenzt erlaubte Gateway-IPs
- `WEATHERHUB_CLOUD_FORWARD_ENABLED` ermöglicht optionalen Cloud-Forward
- `MAX_BODY_BYTES` wurde auf 2 MB erhöht (große Gateway-Payloads)

### Deployment

- Version `v1.5.0`
- `loggerpi.env.example` um WeatherHub-Variablen erweitert
- `deploy/loggerpi/install.sh` um WeatherHub-Dateien erweitert
- GitHub Actions CI: 136 Tests, alle grün (Python 3.9 + 3.13)

---

## DEC-034 — Batch: Nur Measurements mit tatsächlichem Wert (AtmoWEB)

**Status:** Angenommen
**Datum:** 2026-10-27

### Kontext

AtmoWEB-Geräte liefern für nicht unterstützte Sensoren (z.B. CO2, O2, Vakuum)
`N/A` zurück. Diese Werte wurden bisher als `unavailable`-Measurements mit
`value: null` in den Batch aufgenommen.

### Entscheidung

AtmoWEB-Reader nimmt nur Measurements mit `value is not None` in den Batch auf.

Wenn ein neues AtmoWEB-Gerät angeschlossen wird, das z.B. CO2 unterstützt,
erscheinen die Werte automatisch wieder im Batch (weil dann `valid` statt
`unavailable`).

MEMMERT-Reader behält `unavailable`-Einträge bei, weil konfigurierte Geräte
(z.B. IPP300 rechts in Reparatur) im Dashboard sichtbar bleiben sollen.

### Konsequenz

- Batch wird schlanker (keine null-Platzhalter für nicht unterstützte Sensoren)
- Dashboard kann nicht unterstützte Messwerte nicht mehr anzeigen
- Neue Geräte mit zusätzlichen Sensoren erscheinen automatisch

---

## DEC-035 — Dashboard: WeatherHub-Sensoren in Räumen

**Status:** Angenommen
**Datum:** 2026-10-27

### Kontext

17 WeatherHub-Sensoren (15× ID01, 1× ID03, 1× ID0E) sind im Batch verfügbar.

### Entscheidung

Dashboard zeigt:

- **ID01-Sensoren:** Nur Gerätetemperatur (`temperature_2`) als Kachel mit Chart
- **ID03-Sensoren:** Keine Kachel, nur Raumklima (Temperatur + Feuchte)
- **ID0E (DryAger):** Temperatur + Feuchte als Kachel (AtmoWEB-Stil)
- **Raumtemperatur:** Mittelwert aus ID01-`temperature_1` + ID03-`temperature`
- **Raumfeuchte:** Mittelwert aller ID03-`humidity` Werte
- **Letzte Kachel bei ungerader Anzahl:** Volle Breite

### Konsequenz

- Übersicht zeigt Raumklima in der Raum-Kopfzeile
- Detailseiten zeigen nur relevante Gerätekacheln
- ID0E wird nicht in Raumtemperatur-Berechnung einbezogen (liegt im Gerät)

---

## DEC-036 — Dashboard-Konfiguration in separater Datei

**Status:** Angenommen
**Datum:** 2026-10-27

### Kontext

Sensor-Standorte können sich ändern (Umzüge, neue Geräte). Die Konfiguration
sollte ohne Änderung der Dashboard-Logik anpassbar sein.

### Entscheidung

Die Raum- und Sensor-Zuordnung wird in `dashboard_config.py` ausgelagert.
`dashboard.py` importiert die `ROOMS`-Struktur aus dieser Datei.

### Konsequenz

- Sensor-Umzüge erfordern nur Änderungen in `dashboard_config.py`
- Deployment über `loggerpi-otterpi-update otterpi`
- Alternativ: Direkte Datei-Änderung auf dem OtterPi + Service-Restart

---

## DEC-037 — Dashboard auf Englisch umgestellt

**Status:** Angenommen
**Datum:** 2026-10-27

### Kontext

Das Dashboard war bisher auf Deutsch.

### Entscheidung

Alle UI-Texte wurden auf Englisch umgestellt (Titel, Buttons, Chart-Legenden,
Tooltips, Raumnamen). `ZOOLOGY-Observer` bleibt als Eigenname erhalten.
Datumsformat bleibt deutsch (`27.10.2026 16:45 Uhr`).

### Konsequenz

- Einheitliche englische UI
- Kein Mix aus Deutsch und Englisch

---

## DEC-038 — Stale-Logik für WeatherHub-Sensoren

**Status:** Angenommen
**Datum:** 2026-10-28

### Kontext

WeatherHub-Sensoren senden typischerweise in einem mehrminütigen Intervall.
Bisher gab es keine Stale-Logik – ein Sensor, der keine Daten mehr sendete,
blieb dauerhaft als `valid` markiert.

### Entscheidung

WeatherHub-Sensoren erhalten eine Stale-Logik analog zum `FreezerReader`.

Der Schwellenwert ist konfigurierbar über:

```text
WEATHERHUB_STALE_AFTER_SECONDS
```

Default: `1800` Sekunden (30 Minuten).

Wenn ein Sensor länger als der Schwellenwert keine Daten gesendet hat,
wird sein letzter bekannter Wert mit `validity = "stale"` markiert.
Sobald der Sensor wieder sendet, wird er automatisch wieder `valid`.

### Konsequenzen

- `weatherhub.py`: `stale_after_seconds` Parameter
- `loggerpi_observer.py`: Env-Variable einlesen
- `loggerpi.env.example`: Variable dokumentiert
- Dashboard zeigt `stale` als Warnung (gelbe Status-Lampe)

---

## DEC-039 — Gerätedetailseite im Dashboard

**Status:** Angenommen
**Datum:** 2026-10-28

### Kontext

Die Raumdetailseite zeigte Gerätekacheln mit kleinen Charts. Für eine
detaillierte Analyse einzelner Geräte fehlte eine eigene Seite.

### Entscheidung

Jede Gerätekachel auf der Raumdetailseite verlinkt auf eine eigene
Gerätedetailseite:

```text
/device/<sensor_id>
```

Die Detailseite enthält:

- Erweiterten Chart mit Zeitraum-Auswahl (24h, 7d, 14d, 30d, 90d, 365d)
- Sensor-Informationen (Name, Key, Typ, Raum, Letzte Aktualisierung, Status)
- Statistik (Min/Max/Ø für Temperatur und Feuchte)

Zusätzlich gibt es eine Raumklima-Detailseite:

```text
/climate/<room_id>
```

Diese zeigt Mittelwert-Charts und Einzelsensor-Diagramme.

### Konsequenzen

- `dashboard.py`: Neue Render-Funktionen `_render_device_detail()` und `_render_climate_detail()`
- `otterpi.py`: Neue Routen `/device/` und `/climate/`
- Kacheln auf Raumdetailseite sind jetzt Links

---

## DEC-040 — Batch-Archivierung

**Status:** Angenommen
**Datum:** 2026-10-28

### Kontext

Die SQLite-Datenbank wächst kontinuierlich. Ohne Archivierung würde sie
unbegrenzt wachsen.

### Entscheidung

Batches älter als 12 Monate werden monatlich archiviert:

- **Format:** JSON Lines + gzip
- **Dateiname:** `loggerpi-otterpi_batches_YYYY-MM.json.gz`
- **Pfad:** `/var/lib/loggerpi-otterpi/archive/`
- **Aufbewahrung:** Unbegrenzt
- **Löschung:** Erst nach erfolgreichem Export

Automatisierung über systemd-Timer (1. des Monats, 03:00 Uhr).

### Verwendung

```bash
# Normaler Lauf (Batches > 12 Monate)
python3 /opt/loggerpi-otterpi/archive_batches.py

# Force-Modus (alle Batches, z.B. für Tests)
python3 /opt/loggerpi-otterpi/archive_batches.py --force

# Mit Ausgabepfad (für Tests) - löscht NICHT die DB
python3 /opt/loggerpi-otterpi/archive_batches.py --output /tmp/test.json.gz --force

# Mit Datumsbereich
python3 /opt/loggerpi-otterpi/archive_batches.py --year 2025 --month 10

# Dry-Run
python3 /opt/loggerpi-otterpi/archive_batches.py --dry-run
```

### Konsequenzen

- `archive_batches.py`: Neues Skript auf dem OtterPi
- `deploy/otterpi/archive-batches.service`: systemd-Service
- `deploy/otterpi/archive-batches.timer`: Monatlicher Timer
- `deploy/otterpi/install.sh`: Installiert Skript + Timer
- 17 neue Tests für Archivierung

---

## DEC-041 — Admin im OtterPi-Service, LAN-only via nginx

**Status:** Accepted
**Datum:** 2026-11-04

### Kontext

Der OtterPi benötigt eine Verwaltungsschicht für Konfiguration (Rooms, Alarm Limits, Mail, Notifications). Sie soll Teil des bestehenden `otterpi.observer.service` sein (ein Prozess, ein Deployment).

### Entscheidung

Der Admin ist Teil des OtterPi-Service. Die Zugriffskontrolle erfolgt ausschließlich über nginx:

```nginx
location /admin { allow 192.168.178.0/24; deny all; ... }
location /api/admin/ { allow 192.168.178.0/24; deny all; ... }
```

Der Handler (`otterpi.py`) macht **keine** IP-Prüfung und bleibt auth-agnostisch.

### Begründung

- Ein Prozess, ein Deployment.
- LAN-only ohne Code-Kopplung.
- Öffentlich-Öffnen später = nginx + Auth, kein Code-Umbau.

### Konsequenz

- Admin-URL: https://observer.makki.route64.de/admin
- Admin-Routen: `GET /admin`, `GET /api/admin/config`, `PUT /api/admin/*`.
- nginx erlaubt IPv4 (192.168.178.0/24) und IPv6 (2a02:908:1a66:ecc0::/64, fdb7:145b:1d9f:0::/64).
- nginx-Konfiguration ist separater Deployment-Schritt.

---

## DEC-042 — Config-Zugriff über `get_rooms()` (Variante B)

**Status:** Accepted
**Datum:** 2026-11-04

### Kontext

`dashboard.py` importierte `ROOMS` modul-level aus `dashboard_config.py`. Änderungen an `rooms.json` wären erst nach Service-Restart wirksam geworden.

### Entscheidung

`dashboard_config.py` bietet `get_rooms()` mit mtime-Cache, Lock und Fallback auf `_DEFAULT_ROOMS`. `dashboard.py` ruft `get_rooms()` pro Render auf.

### Begründung

- Kein Restart-on-Save, keine Privilegien (`makki` → root entfällt).
- Keine Downtime, kein Alert-Engine-Reset.
- Ressourcenschonend: ein `stat()` pro Request, JSON-Parsing nur bei Änderung.

### Konsequenz

- `ROOMS` als Modulkonstante entfällt.
- `test_dashboard.py` nutzt `get_rooms()`.

---

## DEC-043 — JSON-Config mit Validierung, `.bak`, atomarem Schreiben

**Status:** Accepted
**Datum:** 2026-11-04

### Entscheidung

`config_store.py` verwaltet `rooms.json`, `alarm_limits.json`, `mail.json`, `notifications.json`:

- Validierung vor dem Schreiben.
- `.bak` vor jedem Überschreiben.
- Atomar: temp + `os.replace`.

Secrets (SMTP-Passwort) bleiben in `otterpi.env`.

### Konsequenz

- Admin schreibt nur JSON, nie env.
- SMTP-Passwort-Änderung bleibt manuell auf dem OtterPi.

---

## DEC-044 — Notifier: E-Mail, ntfy, Webhook (stdlib only)

**Status:** Accepted
**Datum:** 2026-11-04

### Entscheidung

`notifier.py` implementiert `EmailNotifier`, `NtfyNotifier`, `WebhookNotifier` (generic/discord/slack). Alle nutzen ausschließlich Standardbibliothek (`smtplib`, `urllib.request`, `json`).

Kanäle sind separat über `notifications.json` ein-/ausschaltbar. Dedup/Quiet Hours bleiben global in der Alert-Engine.

### Konsequenz

- Keine neuen Runtime-Dependencies.
- Phase B verdrahtet die Notifier nur noch.

---

## DEC-045 — `dashboard.py` aufgeteilt

**Status:** Accepted
**Datum:** 2026-11-04

### Entscheidung

`dashboard.py` wurde entlastet:

- `dashboard_constants.py` – Konstanten (`BERLIN`, `VERSION`, Zeiträume, Farben).
- `dashboard_data.py` – Queries/Berechnungen (`_recent_batches`, `_series`, `_room_climate`, …).
- `dashboard_charts.py` – JS-/Chart-Helfer.
- `dashboard.py` – nur noch Seiten-Renderer.

### Konsequenz

- Datenfunktionen sind für die Alert-Engine wiederverwendbar.
- Kein Verhaltensunterschied.

---

## DEC-046 — Battery-Low als State (B0), Alert-Regel in Phase B

**Status:** Accepted
**Datum:** 2026-11-04

### Entscheidung

`battery_low` wird als State in den Core Batch aufgenommen (B0) und im Dashboard angezeigt. Eine Boolean-Alert-Regel folgt in Phase B (kleine Schema-Erweiterung in `alarm_limits.json`).

### Konsequenz

- State jetzt erfassbar/anzeigbar.
- Alert-Regel später, kein Blocker.

---

## DEC-047 — States/Setpoints/Device im Core Batch (B0)

**Status:** Accepted
**Datum:** 2026-11-05

`states`, `operation`, `serial`, `setpoints`, `device` sind optionale Top-Level-Bereiche. `Measurement` trägt optional `validity_reason` (`overflow`/`sensor_error`).

- AtmoWEB: Lights day/uv bool, led percent; Flap percent.
- Freezer: `serial.state` (disconnected/unknown/connected/degraded).
- MEMMERT: `operation_mode` Rohwert.
- WeatherHub: `battery_low`, `gateway_ip`.

---

## DEC-048 — Device-Infos in jedem Batch (vorerst)

**Status:** Accepted
**Datum:** 2026-11-05

`device` und `setpoints` werden vorerst in jedem Batch mitgeschickt (~25 % Overhead). „Send on change" (Metadata-Change) ist als späteres Komfort-Update vorgemerkt.

---

## DEC-049 — (nicht vergeben)

**Status:** Obsolet
**Datum:** 2026-11-05

Diese Nummer wurde ursprünglich für eine Wiederholung von DEC-047 verwendet.
Der Inhalt war identisch mit DEC-047 („States/Setpoints/Device im Core Batch
(B0)"). Die Nummer bleibt zur Nachvollziehbarkeit der Historie erhalten, wird
aber nicht mehr verwendet.

---

## DEC-050 — Dashboard: Status-Chips + LED-SVG

**Status:** Accepted
**Datum:** 2026-11-05

Die Gerätedetailseite und die Raumdetail-Kacheln zeigen Status-Chips (erklärend: `⚠ No data for X min`, `⛔ Sensor error`, `🚨 Alarm: …`, `⚠ Battery low`, `OK`, `Offline`) statt des bisherigen Status-Texts. Die Statuslampe zeigt den schlechtesten Zustand (Alarm/Invalid rot, Stale/Battery gelb). Ein Inline-SVG-LED-Indikator (dynamisch aus `states.<key>.lights.led`) sitzt links neben der Lampe. Die Übersicht nutzt weiterhin nur die Lampen (via `_device_status`).

---

## DEC-051 — Alert-Engine als Thread in `otterpi_observer.py`

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

Die Alert-Engine muss regelmäßig (nach jedem Batch und per Timer) die
konfigurierten Regeln prüfen. Ein separater systemd-Service würde einen
zweiten Prozess, IPC und mehr Deployment-Aufwand bedeuten.

### Entscheidung

Die Alert-Engine läuft als Thread im bestehenden `otterpi.observer.service`.
`Event.wait(timeout)` blockiert ressourcenschonend. `otterpi.py` ruft
`alert_engine.notify_batch()` nach jedem `store.store(batch)` auf.

### Begründung

- Ein Prozess, ein Deployment (DEC-041).
- `Event.wait(timeout)` ist ressourcenschonend (DEC-024).
- Batch-Trigger für schnelle Reaktion, Timer für No-Data-Erkennung.

### Konsequenz

- `otterpi_observer.py` startet den Thread, `otterpi.py` triggert ihn.
- `create_server` bekommt `alert_engine` als optionalen Parameter.

---

## DEC-052 — `alarm_limits.json` mit `states`-Sektion

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

`alarm_limits.json` enthielt bisher nur `sensors` (Measurement-Grenzwerte).
Die Alert-Engine muss aber auch State-basierte Regeln prüfen
(`freezer.alarms`, `battery_low`, `door_open`).

### Entscheidung

`alarm_limits.json` wird um eine `states`-Sektion erweitert:

```json
{
  "sensors": { ... },
  "states": {
    "freezer.alarms": {"enabled": true},
    "weatherhub_015f9410f3eb.battery_low": {"enabled": true},
    "atmoweb_101.door_open": {"enabled": true, "max_open_seconds": 300}
  }
}
```

### Begründung

- Ein Config-File, ein Admin-Tab.
- `sensors` bleibt semantisch korrekt (Measurement-Grenzwerte).
- `states` ist eine klar abgegrenzte neue Sektion.
- Rückwärtskompatibel: bestehende `alarm_limits.json` (nur `sensors`) funktioniert weiter.

### Konsequenz

- `config_store._validate_alarm_limits` prüft `states`.
- `load_alarm_limits()` gibt das ganze Objekt zurück (DEC-054).

---

## DEC-053 — `Alert`-Dataclass erweitert um `rule` und `dedup_key`

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

Die `Alert`-Dataclass in `notifier.py` hatte `sensor`, `severity`, `message`,
`value`, `threshold`. Für die Speicherung in `alerts.sqlite3` und das
Dedup-Lookup braucht sie zusätzlich `rule` und `dedup_key`.

### Entscheidung

`Alert` wird um zwei optionale Felder erweitert:

```python
@dataclass(frozen=True)
class Alert:
    sensor: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    rule: Optional[str] = None
    dedup_key: Optional[str] = None
```

### Begründung

- `Alert` hat dann alle Informationen für Speicherung und Benachrichtigung.
- Bestehende Tests funktionieren weiter, weil die Felder optional sind.
- `alert_store.store()` prüft, dass `rule` und `dedup_key` gesetzt sind.

### Konsequenz

- `notifier.py` erweitert.
- `alert_store.py` nutzt `rule` und `dedup_key`.

---

## DEC-054 — `load_alarm_limits()` gibt das ganze Objekt zurück

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

`load_alarm_limits()` gab bisher nur `data["sensors"]` zurück. Mit der
neuen `states`-Sektion (DEC-052) reicht das nicht mehr.

### Entscheidung

`load_alarm_limits()` gibt das ganze Objekt zurück (`{"sensors": ..., "states": ...}`).
`save_alarm_limits(data)` erwartet das ganze Objekt.

### Begründung

- Semantisch sauberer: eine Funktion, ein Objekt.
- `otterpi.py` (`_load_admin_config`, `do_PUT`) wird angepasst.
- `test_config_store.py` und `test_admin.py` werden angepasst.

### Konsequenz

- `config_store.py` angepasst.
- `otterpi.py` angepasst.
- Tests angepasst.

---

## DEC-055 — `sensor_schemas.py` als zentrale Schema-Definition

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

Der OtterPi kennt die LoggerPi-Reader nicht. Er sieht nur, was tatsächlich
im Batch ankommt. Für den Admin (Limits/States-Anzeige) und die Alert-Engine
(Regel-Prüfung) braucht er aber Wissen darüber, welche Measurements und
States ein Sensor-Typ grundsätzlich liefern kann.

### Entscheidung

`sensor_schemas.py` definiert pro Sensor-Typ, welche Measurements und States
grundsätzlich möglich sind. Enthält auch Sensor-Typen, die im Decoder
vorbereitet, aber noch nicht in `rooms.json` eingebunden sind
(z.B. `weatherhub_id02`, `id04`, `id07`, `id10`).

### Begründung

- Eine Quelle der Wahrheit für Sensor-Typen.
- Admin und Alert-Engine nutzen dieselbe Definition.
- Vorbereitete Sensoren sind schon da, auch wenn sie noch nicht in `rooms.json` sind.
- Test (`test_sensor_schemas.py`) prüft gegen den Reader-Code.

### Konsequenz

- Neue Datei `sensor_schemas.py`.
- Neue Datei `test_sensor_schemas.py`.
- Admin nutzt `SENSOR_SCHEMAS` für die Limits/States-Anzeige.

---

## DEC-056 — SMTP-Variablen nur in `mail.json`, `SMTP_PASSWORD` in `otterpi.env`

**Status:** Accepted
**Datum:** 2026-11-05

### Kontext

`otterpi.env.example` listete `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_FROM` als Env-Variablen. Das widerspricht DEC-043 (dort stehen diese
Werte in `mail.json`, nur `SMTP_PASSWORD` in `otterpi.env`).

### Entscheidung

`mail.json` bleibt die Quelle für `smtp_host`, `smtp_port`, `smtp_user`,
`from`, `recipients`, `routing`, `dedup_seconds`, `quiet_hours`, `enabled`.
`otterpi.env` enthält **nur** `SMTP_PASSWORD`.

Die vier SMTP-Variablen in `otterpi.env.example` fliegen raus.

### Begründung

- Eine Quelle der Wahrheit.
- Admin-Editor lügt nicht.
- Secret (`SMTP_PASSWORD`) bleibt in `otterpi.env`.

### Konsequenz

- `otterpi.env.example` angepasst.
- `mail.json` bleibt unverändert.

---

## DEC-057 — Formular-UI statt JSON-Editor (Phase C)

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

Die Admin-Tabs waren bisher JSON-Editoren. Das war für Phase A (MVP) ausreichend, aber nicht benutzerfreundlich. Raumwechsel, Geräte-Umbenennung und Limit-Bearbeitung erforderten manuelles JSON-Editieren.

### Entscheidung

Alle Admin-Tabs (Rooms, Alarm Limits, Mail, Notifications) werden auf Formular-UI umgestellt:

- **Rooms:** Raum-Kacheln, Geräte-Tabelle, Pull-down für Raumwechsel, Inline-Formulare für Add/Edit/Delete.
- **Alarm Limits:** Measurements- und States-Tabellen pro Gerät, Edit-Limits-Inline-Formular.
- **Mail:** Formular mit SMTP-Feldern, Recipients, Routing, Dedup, Quiet Hours.
- **Notifications:** Channel-Liste mit Add/Edit/Delete.

Der JSON-Editor bleibt als „Advanced"-Toggle in jedem Tab erhalten.

### Begründung

- Benutzerfreundlicher (kein manuelles JSON-Editieren).
- Weniger Fehler (Validierung im Formular).
- Raumwechsel per Pull-down statt JSON-Editieren.

### Konsequenz

- `admin.py` umfangreich erweitert (Inline-Formulare, `loadRooms`, `loadAlarmLimits`, `loadMailForm`, `loadNotifications`).
- `SENSOR_SCHEMAS` wird in `admin.py` eingebettet (für Typ-Auswahl und Measurements/States-Anzeige).

---

## DEC-058 — Rate-of-Change in Alert-Engine

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

`alarm_limits.json` enthält `rate_of_change_max_per_hour`, aber die Alert-Engine hat es bisher ignoriert.

### Entscheidung

`alert_engine.py` `_check_sensors` prüft `rate_of_change_max_per_hour`:

- `BatchStore.recent(hours=1)` liefert die letzten Batches.
- `_calculate_rate_of_change()` berechnet die Rate aus erstem und letztem Wert.
- Wenn `abs(rate) > rate_limit`, wird ein Alert mit `rule="rate_of_change"` erzeugt.

### Begründung

- Frühwarnung, bevor ein Grenzwert erreicht wird.
- Nutzt vorhandene `rate_of_change_max_per_hour`-Konfiguration.

### Konsequenz

- `otterpi_store.py` um `recent(hours)` erweitert.
- `alert_engine.py` um `_calculate_rate_of_change()` erweitert.

---

## DEC-059 — Routing in EmailNotifier

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

`mail.json` enthält `routing.critical` und `routing.warning`, aber `EmailNotifier` hat bisher `recipients` für alle Severities genutzt.

### Entscheidung

`EmailNotifier.send()` nutzt `routing[alert.severity]` statt `recipients`:

```python
recipients = self.routing.get(alert.severity, self.recipients)
```

### Begründung

- Unterschiedliche Empfänger je nach Severity (z.B. nur Bereitschaftsdienst bei critical).
- Fallback auf `recipients`, wenn `routing` fehlt.

### Konsequenz

- `notifier.py` `EmailNotifier` erweitert.
- `test_notifier.py` um `test_email_routing` erweitert.

---

## DEC-060 — `contact_open` in Alert-Engine

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

`weatherhub_id10` (Tür/Fensterkontakt) liefert `contact_open` (bool). Die Alert-Engine hat es bisher ignoriert.

### Entscheidung

`alert_engine.py` `_check_states` prüft `contact_open`:

```python
elif state_name == "contact_open" and value is True:
    alerts.append(self._make_alert(...))
```

### Begründung

- Für zukünftige `weatherhub_id10`-Sensoren (Private Observer).
- Kein akuter Bedarf (aktuell kein `weatherhub_id10` in `rooms.json`).

### Konsequenz

- `alert_engine.py` `_check_states` erweitert.
- `test_alert_engine.py` um `test_contact_open` erweitert.

---

## DEC-061 — Door-Open-Dauer geparkt

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

`alarm_limits.json` `states` enthält `door_open` mit `max_open_seconds`. Die Alert-Engine hat es bisher ignoriert.

### Entscheidung

Door-Open-Dauer wird **nicht** implementiert, weil:

- HPP260 liefert `door_open` nicht (liefert `N/A`).
- Aktuell kein Gerät in `rooms.json` unterstützt `door_open`.

Geparkt für evtl. zukünftige AtmoWEB-Geräte (unwahrscheinlich).

### Begründung

- Kein akuter Bedarf.
- Kein Gerät unterstützt es.

### Konsequenz

- `alert_engine.py` `_check_states` prüft `door_open` (einfach, ohne `max_open_seconds`).
- `max_open_seconds` bleibt in `alarm_limits.json` (für später).

---

## DEC-062 — Service-Restart nicht nötig

**Status:** Accepted
**Datum:** 2026-11-07

### Kontext

Die Admin-UI hat keinen Service-Restart-Button. Änderungen an JSON-Configs werden automatisch gelesen.

### Entscheidung

Kein Service-Restart-Button. JSON-Configs werden automatisch gelesen:

- `rooms.json`: `get_rooms()` mit mtime-Cache (sofort).
- `alarm_limits.json`, `mail.json`, `notifications.json`: `load_*()` bei jedem `_check` (alle 300 s).

Nur `otterpi.env` und Code-Änderungen brauchen einen Restart.

### Begründung

- Kein manueller Restart nötig für JSON-Configs.
- `sudo systemctl restart` reicht für `otterpi.env` und Code-Änderungen.

### Konsequenz

- Kein Service-Restart-Button in der Admin-UI.
- Dokumentation: JSON-Configs automatisch, `otterpi.env` + Code manuell.

---

## DEC-063 — `received_at` in der Batch-Tabelle

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Das Datenmodell definiert `received_at` als OtterPi-seitigen Empfangszeitpunkt,
aber die Tabelle `batches` speicherte ihn bisher nicht. Dashboard, Alert-Engine
und Archivierung nutzten `created_at` (LoggerPi-Zeit). Für die Offline-Erkennung
ist `received_at` robuster, weil es unabhängig von der LoggerPi-Uhr ist und
verspätet nachgelieferte Batches korrekt behandelt.

### Entscheidung

Die Tabelle `batches` erhält eine Spalte `received_at` (TEXT, nullable).
`BatchStore.store()` setzt sie auf `datetime.now(timezone.utc).isoformat()`.
`BatchStore.latest_received_at()` liefert den Wert des neuesten Batches; bei
bestehenden Zeilen ohne `received_at` fällt sie auf `created_at` aus dem
Payload zurück.

### Begründung

`created_at` ist LoggerPi-Zeit und kann bei falscher LoggerPi-Uhr oder
verspäteter Queue-Zustellung zu falschen Offline-Alerts führen. `received_at`
ist OtterPi-Zeit und immer „jetzt" beim Empfang.

### Konsequenz

Schema-Migration via `ALTER TABLE` für bestehende DBs. Dashboard und
Archivierung nutzen weiterhin `created_at` (Messzeit). Nur die
Offline-Erkennung nutzt `received_at`.

---

## DEC-064 — LoggerPi-Offline-Erkennung (2-stufiger Heartbeat)

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Bisher gab es keine Erkennung, wenn der LoggerPi keine Batches mehr sendet.
Die Alert-Engine prüfte den letzten Batch, sah `validity = "valid"` und löste
keine Alerts aus. Der Offline-Zustand blieb unerkannt.

### Entscheidung

Die Alert-Engine prüft vor den Sensor-/State-Checks den LoggerPi-Heartbeat.
Zwei Stufen:

- **Warnung:** `loggerpi_offline_warning_seconds` (Default 1800 = 30 min).
  Statusleuchte gelb. Optionaler `warning`-Alert, steuerbar über
  `loggerpi_offline_warning_alert_enabled` (Default false).
- **Kritisch:** `loggerpi_offline_critical_seconds` (Default 3600 = 1 h).
  Statusleuchte rot. Immer `critical`-Alert.

Konfiguration in `alarm_limits.json` unter `system`.

### Begründung

Ein einzelner verpasster Batch (15 min + Puffer) soll keine Mail auslösen.
Aber nach 30 min soll man es im UI sehen. Nach 1 h (4 verpasste Batches) ist
es ernst genug für einen Alert. Das verhindert Alert-Spam bei kurzen Hängern
und gibt trotzdem rechtzeitig Bescheid.

### Konsequenz

Neue Datei `heartbeat.py` mit `offline_status()`. `alarm_limits.json` um
`system`-Sektion erweitert. Admin und Dashboard zeigen Statusleuchte im
Header. Admin hat System-Karte im Alarm Limits-Tab.

---

## DEC-065 — Suppression der Sensor-/State-Checks bei Offline

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Wenn der LoggerPi offline ist, sind die Daten im letzten Batch veraltet.
Würden die Sensor-/State-Checks weiterlaufen, könnten veraltete Zustände
(z. B. `battery_low = true` aus dem letzten Batch) bei jedem 300s-Check
erneut geprüft werden. Dedup verhindert nur die Wiederholung innerhalb von
`dedup_seconds` (1 h), nicht die grundsätzliche Wiederholung.

### Entscheidung

Sobald die Warnschwelle erreicht ist (`is_offline = True`), werden
`_check_sensors` und `_check_states` nicht aufgerufen. Der einzige Alert in
dieser Phase ist der Offline-Alert. Sobald wieder ein Batch ankommt, laufen
die Checks sofort wieder.

### Begründung

Ohne neue Daten gibt es keine neuen Grenzwertverletzungen. Die alten Werte
sind nicht mehr vertrauenswürdig. Die wichtigste Information ist „LoggerPi
offline", nicht „30 Sensoren sind kaputt".

### Konsequenz

`_check()` ruft zuerst `_check_loggerpi_heartbeat()` auf. Bei
`is_offline = True` wird nach dem Offline-Alert `return` gemacht. Die
Suppression greift auch, wenn die Warnstufe deaktiviert ist (kein Warn-Alert,
aber trotzdem keine Sensor-Checks).

---

## DEC-066 — `system`-Sektion in `alarm_limits.json`

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Die Offline-Schwellenwerte brauchen einen Konfigurationsort. `mail.json` ist
Transport (SMTP, Routing, Dedup, Quiet Hours). `alarm_limits.json` ist
fachlich eine Alarm-Regel.

### Entscheidung

`alarm_limits.json` erhält eine neue Top-Level-Sektion `system`:

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

`config_store._validate_alarm_limits` validiert die Sektion: positive Integers
für die Schwellenwerte, `warning < critical`, Boolean für
`loggerpi_offline_warning_alert_enabled`, keine unbekannten Felder.

### Begründung

Eine Quelle der Wahrheit für Alarm-Regeln. `system` ist semantisch klar von
`sensors` und `states` getrennt. Rückwärtskompatibel: bestehende
`alarm_limits.json` ohne `system` funktioniert weiter (Defaults greifen).

### Konsequenz

`config_store.py` erweitert. Admin-UI hat System-Karte im Alarm Limits-Tab.
`heartbeat.py` und `alert_engine.py` lesen die Sektion.

---

## DEC-067 — Acknowledge-Verhalten (Option B)

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Ein Alert wurde bisher bei jedem Check erneut gesendet, solange der Zustand
kritisch war – dedupliziert nur durch `dedup_seconds` (1 h). Der Nutzer
konnte einen Alert zwar acknowledged, aber das hatte keine Auswirkung auf
weitere Sendungen.

### Entscheidung

Ein acknowledged Alert wird nicht erneut gesendet, solange der Zustand
kritisch bleibt. `AlertStore.is_acknowledged(dedup_key)` prüft den letzten
Alert mit demselben `dedup_key`. `_dispatch()` überspringt acknowledged
Alerts. Sobald der Wert wieder innerhalb der Grenzen ist, ruft die
Alert-Engine `reset_acknowledged(dedup_key)` auf – der Alert wird für die
Zukunft „entsperrt".

Das Verhalten ist immer aktiv, nicht konfigurierbar. Eine zusätzliche
Aktivierungs-Checkbox wäre Overengineering.

### Begründung

Der Sinn von Acknowledge ist, dass der Nutzer den Alert gesehen hat und
nicht bei jedem Check erneut belästigt wird. Erst wenn der Zustand sich
ändert (wieder normal, dann wieder kritisch), soll ein neuer Alert kommen.

### Konsequenz

`AlertStore` um `is_acknowledged()` und `reset_acknowledged()` erweitert.
`_dispatch()` prüft `is_acknowledged()` nach `recent_dedup_keys()`.
`_check_sensors()`/`_check_states()` rufen `reset_acknowledged()` auf, wenn
der Zustand normal ist.

---

## DEC-068 — Alert-Resolve (Active vs. Resolved)

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Alerts blieben bisher für immer in der History, ohne Unterscheidung zwischen
„aktiv" und „erledigt". Der Nutzer konnte nicht sehen, ob ein Alarm
zwischenzeitlich mal aktiv war, sich aber erledigt hat (z. B. Kühlschranktür
kurz offen).

### Entscheidung

Die Tabelle `alerts` erhält eine Spalte `resolved_at` (TEXT, nullable).
`AlertStore.resolve(dedup_key)` setzt `resolved_at` für **alle offenen**
Alerts mit demselben `dedup_key` (Variante 2). `AlertStore.is_active(dedup_key)`
prüft, ob der letzte Alert noch nicht resolved ist.

Die Alert-Engine ruft `resolve()` auf, sobald der Wert wieder innerhalb der
Grenzen ist (bzw. der State wieder normal ist) – analog zu
`reset_acknowledged()`.

### Begründung

Variante 2 (alle offenen Alerts resolven) ist semantisch sauberer als
Variante 1 (nur den letzten). Der `dedup_key` repräsentiert denselben
Zustand. Wenn der Zustand normal wird, sind alle Alerts, die diesen Zustand
repräsentieren, resolved – nicht nur der letzte. Variante 1 führt zu
„Zombie-Alerts", die für immer „Active" bleiben, und macht `is_active()`
inkonsistent.

### Konsequenz

Schema-Migration via `ALTER TABLE` für bestehende DBs. Admin-Alerts-Tab
zeigt Status-Chip („Active" / „Resolved") und Filter „Only active".
`otterpi.py` unterstützt den Query-Parameter `only_active`.

---

## DEC-069 — Bugfix: Reset/Resolve nur bei normalem Wert

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Der erste Entwurf von DEC-067 rief `reset_acknowledged()` auf, sobald
`validity == "valid"` und `value is not None`. Das war zu früh: Wenn der
Wert immer noch außerhalb der Grenzen war (z. B. `30.0 > critical_max 28.0`),
wurde der Alert resettet, obwohl er noch aktiv war. Beim nächsten Check
wurde er wieder ausgelöst – aber weil er resettet wurde, wurde er erneut
gesendet.

### Entscheidung

`reset_acknowledged()` und `resolve()` werden nur im `else`-Zweig der
Grenzwert-Prüfung aufgerufen – also nur, wenn der Wert tatsächlich wieder
innerhalb der Grenzen ist. Für States analog: nur wenn der State wieder
normal ist.

### Begründung

Ein Alert soll acknowledged bleiben, solange der Zustand kritisch ist. Erst
wenn der Zustand normal wird, soll er „entsperrt" und resolved werden.

### Konsequenz

`_check_sensors()` und `_check_states()` entsprechend korrigiert. Neue Tests
(`test_no_resolve_when_still_critical`) sichern das Verhalten ab.

---

## DEC-070 — Message-Templates (globale Regel-Texte + Measurement-Name)

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Die Alert-Message war bisher technisch (`f"{sensor_key}: {value} > {threshold}"`).
Der Nutzer wollte lesbare Texte mit Raum, Gerät und Regel-Beschreibung. Eine
per-Sensor-Konfiguration wäre aufwändig (30 Sensoren × 4 Regeln).

### Entscheidung

Die Message wird aus zwei Teilen zusammengesetzt:

- **Regel-Text** (editierbar in `messages.json`): „too high", „too low",
  „invalid", „stale", „low", „open", „alarm", „offline".
- **Measurement-Name** (fest im Code, `MEASUREMENT_DISPLAY_NAMES`):
  „Temperature", „Humidity", „Vacuum", „CO₂", „Battery", „Door".

Die Alert-Engine baut: `"{room} / {device} — {measurement_name} {rule_text}: {value} {unit} {operator} {threshold} {unit}"`.

### Begründung

- Keine Duplikate: „too high" gilt für alle Measurements.
- Erweiterbar: Neue Measurements brauchen nur einen Eintrag im Mapping.
- Editierbar: Die Regel-Texte bleiben im Messages-Tab anpassbar.
- Lesbar: Raum und Gerät sind in der Message, kein Nachschlagen nötig.

### Konsequenz

Neue Datei `messages.json` (Defaults, Fallback). Neuer Admin-Tab „Messages".
`alert_engine.py` um `_build_message()` und `_build_subject()` erweitert.

---

## DEC-071 — Subject mit Raum/Gerät/Measurement-Name

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Der E-Mail-Subject war bisher `[CRITICAL] atmoweb_101.temperature_1` – technisch
und ohne Raum/Gerät. Der Nutzer wollte einen lesbaren Subject.

### Entscheidung

Der Subject wird in der Alert-Engine gebaut und im `Alert`-Objekt als
`subject`-Feld mitgegeben:

```text
[CRITICAL] Temperature — R1304 · Culture Room I / Memmert HPP260 · left
```

`EmailNotifier` und `NtfyNotifier` nutzen `alert.subject`, wenn gesetzt, sonst
Fallback auf den bisherigen Subject.

### Begründung

Der Subject wird im Notifier gebaut, der keinen Zugriff auf `rooms.json` hat.
Die Alert-Engine hat den Zugriff und kann den Subject vorbereiten. Das ist
sauberer als den Notifier mit `rooms.json`-Kenntnis auszustatten.

### Konsequenz

`Alert`-Dataclass um `subject` erweitert. `EmailNotifier` und `NtfyNotifier`
angepasst. `WebhookNotifier` bleibt unverändert (nutzt `alert.message`).

---

## DEC-072 — Manueller Resolve-Button im Admin

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Alerts werden automatisch resolved, wenn der Zustand wieder normal ist. Aber
wenn ein Sensor aus dem Batch verschwindet (z. B. weil die Batterie leer ist),
wird der Alert nie resolved. Ein automatischer „Sweep" wäre gefährlich, weil
er auch Alerts resolven würde, deren Problem schlimmer geworden ist.

### Entscheidung

Ein manueller Resolve-Button im Admin-Alerts-Tab. `AlertStore.resolve_by_id()`
setzt `resolved_at` für einen bestimmten Alert (per ID).
`POST /api/admin/alerts/<id>/resolve`.

### Begründung

Der Nutzer entscheidet explizit, ob ein Alert erledigt ist. Kein automatischer
Sweep, der falsch-positive Resolves erzeugen könnte.

### Konsequenz

`alert_store.py` um `resolve_by_id()` erweitert. `otterpi.py` um den Endpoint.
`admin.py` um den Resolve-Button (verschwindet, wenn resolved).

---

## DEC-073 — Alert-Tab als Default-Tab

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Der Rooms-Tab war bisher der Default-Tab. In Produktion schaut man aber am
häufigsten nach Alerts.

### Entscheidung

Der Alerts-Tab ist jetzt der erste Tab und der Default. Beim Öffnen des Admins
wird `loadAlerts()` aufgerufen (statt `loadRooms()`).

### Begründung

Der Alert-Tab ist die wichtigste Ansicht für den täglichen Betrieb. Man sieht
sofort, ob es Probleme gibt.

### Konsequenz

Tab-Reihenfolge: Alerts, Rooms, Alarm Limits, Mail, Notifications, Messages.
Der Alerts-Tab-Button und das Alerts-Panel haben `class="active"`.

---

## DEC-074 — Toast-Notification für Save-Buttons

**Status:** Accepted
**Datum:** 2026-11-08

### Kontext

Die Save-Buttons setzten bisher nur `status.textContent = 'Saved.'`. Das war
leicht zu übersehen.

### Entscheidung

Eine globale `showToast(message, type)`-Funktion und eine `setStatus(statusId,
message, type)`-Hilfsfunktion. Alle Save-/Delete-/Acknowledge-/Resolve-Aktionen
zeigen eine kurze Toast-Benachrichtigung (grün für Erfolg, rot für Fehler), die
nach 3 Sekunden verschwindet.

### Begründung

Auffälliger als ein Text-Status, aber nicht aufdringlich. Einmal eingebaut,
für alle Aktionen nutzbar.

### Konsequenz

`admin.py` um CSS (`.toast-container`, `.toast`, `.toast-success`,
`.toast-error`), HTML (`<div id="toast-container">`) und JavaScript
(`showToast`, `setStatus`) erweitert. Alle Save-Funktionen nutzen `setStatus`.

---

## DEC-075 — Severity-Auswahl pro Notifier-Kanal

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

ntfy und Webhook sendeten bisher alle Alerts, unabhängig von der Severity.
Der Nutzer wollte pro Kanal steuern, welche Severity darüber gemeldet wird
(z.B. ntfy nur für critical).

### Entscheidung

`notifications.json` → `severities` pro Channel (Liste von `critical`/`warning`).
`NtfyNotifier` und `WebhookNotifier` prüfen die Severity, bevor sie senden.
Wenn die Severity nicht in der Liste ist, wird der Alert nicht gesendet
(Rückgabe `True`, kein Fehler).

### Begründung

Unterschiedliche Kanäle haben unterschiedliche Zwecke: ntfy ist schnell
(Push), E-Mail ist formell. Manche Nutzer wollen nur critical auf ntfy,
aber alles per E-Mail.

### Konsequenz

`notifier.py` erweitert. `config_store.py` validiert `severities`.
Admin-Notifications-Tab um Checkboxen erweitert.

---

## DEC-076 — Rate-of-Change im Admin-Formular

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

`rate_of_change_max_per_hour` war in der Alert-Engine implementiert, aber
im Admin nicht konfigurierbar. Der Nutzer musste die JSON-Datei manuell
bearbeiten.

### Entscheidung

Im „Edit Limits"-Formular pro Measurement eine zusätzliche Spalte „Rate/h".
Der Wert wird in `limits.rate_of_change_max_per_hour` gespeichert.

### Begründung

Schließt eine Lücke. Der Nutzer kann die Rate-of-Change jetzt ohne
JSON-Editor konfigurieren.

### Konsequenz

`admin.py` `showEditLimitsForm` und `submitEditLimits` erweitert.

---

## DEC-077 — Message-Text bei stale/invalid mit Measurement-Key

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Bei `stale` und `invalid` war die Message für `temperature_1` und
`temperature_2` identisch („Temperature stale"), weil `_measurement_name`
für beide „Temperature" zurückgibt. Der Nutzer bekam zwei identische Mails
pro Sensor.

### Entscheidung

Bei `stale` und `invalid` wird der Measurement-Key in Klammern mit in die
Message aufgenommen:
```
R1308 · Culture Room II / Hypsibius · bottom left/night — Temperature (temperature_1) stale
R1308 · Culture Room II / Hypsibius · bottom left/night — Temperature (temperature_2) stale
```

### Begründung

Die Messages sind jetzt unterscheidbar. Der Measurement-Name bleibt lesbar,
der technische Key ist in Klammern.

### Konsequenz

`alert_engine.py` `_build_message` erweitert.

---

## DEC-078 — Resolve-Zeitstempel im Alert-Tab

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der Alert-Tab zeigte „✓ Resolved", aber nicht, wann der Alert resolved wurde.

### Entscheidung

Der Resolve-Zeitstempel wird neben „✓ Resolved" angezeigt:
```
stale · 9.11.2026, 09:45:12 · ✓ Resolved (9.11.2026, 10:15:30)
```

### Begründung

Der Nutzer sieht, wann der Alert erledigt wurde. Nützlich für die
Nachvollziehbarkeit.

### Konsequenz

`admin.py` `loadAlerts` erweitert.

---

## DEC-079 — Alarm Limits UI-Umbau (Raum-Kacheln mit Geräte-Kacheln)

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der Alarm Limits-Tab zeigte eine flache Liste von Geräte-Karten mit
Measurements- und States-Tabellen. Bei 23 Geräten war das unübersichtlich.

### Entscheidung

Raum-Kacheln mit Geräte-Kacheln. Jede Geräte-Kachel zeigt:
- Gerätename (ohne Raumname, weil der Raum im Raum-Titel steht)
- Metadaten: Key, Type
- Measurements/States als Liste mit farbigen Chips

Chips:
- `[Enabled]` (grün) / `[Disabled]` (grau)
- `[Warning 20–26 °C]` (gelb)
- `[Critical 18–28 °C]` (rot)
- `[Rate 2.0/h]` (blau)
- `[not configured]` (grau)

### Begründung

- **Übersichtlich:** 8 Raum-Kacheln statt 23 Geräte-Karten.
- **Konsistent:** Wie Rooms-Tab.
- **Farbcodiert:** Limits sind auf einen Blick erkennbar.
- **Keine Tabelle:** Die Chips sind lesbarer als eine Tabelle mit 7 Spalten.

### Konsequenz

`admin.py` `loadAlarmLimits` umgebaut. Neue Hilfsfunktion
`buildDeviceContent`. CSS für Chips und Geräte-Kacheln.

---

## DEC-080 — Severity-Checkboxen im Notifications-Tab

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Die Severity-Checkboxen waren in einem `<label>`-Element gequetscht und
unschön dargestellt.

### Entscheidung

Eigene `<div class="severity-checkboxes">` mit Flex-Layout. Jede Checkbox
in einem eigenen `<label>` (klickbar).

### Begründung

Bessere Darstellung, klickbare Labels, horizontal angeordnet.

### Konsequenz

`admin.py` CSS und HTML angepasst.

---

## DEC-081 — States-Tabelle linksbündig

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Die States-Tabelle im Edit-Limits-Formular war `width: 100%`, deshalb wurde
die Checkbox in der zweiten Spalte weit nach rechts geschoben.

### Entscheidung

Die States-Tabelle bekommt `width: auto` und die erste Spalte `padding-right:
24px`. Die Checkbox steht jetzt direkt nach dem State-Namen.

### Begründung

Die States-Tabelle hat nur 2 Spalten, braucht also nicht die volle Breite.
Die Measurements-Tabelle (7 Spalten) behält `width: 100%`.

### Konsequenz

`admin.py` CSS und HTML angepasst.

---

## DEC-082 — ntfy ASCII-safe Title

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der `Title`-Header von ntfy enthielt Nicht-ASCII-Zeichen (`·`, `—`), was zu
`UnicodeEncodeError` führte. ntfy-Benachrichtigungen kamen nicht an.

### Entscheidung

`NtfyNotifier` ersetzt Nicht-ASCII-Zeichen im `Title` durch ASCII-Äquivalente:
`·` → `-`, `—` → `-`, `ä` → `ae`, etc. Verbleibende Nicht-ASCII-Zeichen
werden durch `?` ersetzt (Fallback).

### Begründung

HTTP-Header müssen ASCII sein. Die `message` (Body) bleibt UTF-8, nur der
`Title` wird ASCII-sicher.

### Konsequenz

`notifier.py` um `_ascii_safe()` erweitert. `NtfyNotifier.send` nutzt es.

---

## DEC-083 — Stale/Invalid-Alerts pro Gerät

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

`stale` und `invalid` wurden bisher pro Measurement geprüft. Bei Sensoren mit
mehreren Messkanälen (z. B. WeatherHub ID01 mit `temperature_1` und
`temperature_2`) führte das zu doppelten Mails.

### Entscheidung

`stale` und `invalid` werden pro Gerät geprüft. Ein Alert pro Gerät, nicht
pro Measurement. Neue Sektion `device` in `alarm_limits.json`:

```json
{
  "device": {
    "atmoweb_101": {"stale_enabled": true, "invalid_enabled": true}
  }
}
```

`dedup_key` ist jetzt `device_key:stale:warning` bzw.
`device_key:invalid:critical`.

### Begründung

`stale` und `invalid` sind Eigenschaften des Sensors, nicht des einzelnen
Measurements. Wenn ein Sensor `stale` ist, sind alle seine Measurements
`stale`. Ein Alert pro Gerät reicht.

### Konsequenz

`alert_engine.py` `_check_sensors` umgebaut. `config_store.py` validiert die
`device`-Sektion. `admin.py` zeigt zwei Checkboxen pro Gerät unter „States".

---

## DEC-084 — Letzte Messwerte im Alarm Limits-Tab

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der Nutzer wollte die aktuellen Messwerte sehen, um besser über Limits
entscheiden zu können.

### Entscheidung

Neue Route `GET /api/admin/latest-measurements` liefert die Measurements und
States des letzten Batches. `buildDeviceContent` zeigt den aktuellen Wert
(blau, auf eine Nachkommastelle gerundet) neben jedem Measurement.

### Begründung

Bessere Entscheidungsgrundlage für die Limit-Konfiguration.

### Konsequenz

`otterpi.py` um die Route erweitert. `admin.py` `buildDeviceContent` erweitert.

---

## DEC-085 — „Show all"-Filter im Alarm Limits-Tab

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der HPP260 unterstützt nur einen Teil der AtmoWEB-Felder. Der Admin zeigte
alle Schema-Felder, auch die nicht unterstützten.

### Entscheidung

Checkbox „Show all" unten im Alarm Limits-Tab. Standard: aus (nur aktive
Felder: im letzten Batch vorhanden oder in `alarm_limits.json` konfiguriert).
Wenn an: alle Schema-Felder.

### Begründung

Standardmäßig aufgeräumt, aber flexibel für Konfiguration.

### Konsequenz

`admin.py` `buildDeviceContent` erweitert.

---

## DEC-086 — Nicht-Alarm-Trigger-States entfernt

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

`sensor_schemas.py` listete States, die keine Alarm-Trigger sind
(`door_locked`, `defrost`, `flap`, `lights.*`, `switches.*`). Der Admin
zeigte sie als konfigurierbar, aber die Alert-Engine ignorierte sie.

### Entscheidung

Diese States aus `sensor_schemas.py` entfernt. Sie bleiben im Dashboard
sichtbar (weil `dashboard_data.py` sie direkt aus dem Batch liest).

### Begründung

Konsistenz: Nur Alarm-Trigger im Alarm Limits-Tab.

### Konsequenz

`sensor_schemas.py` für `atmoweb` reduziert auf `door_open`.

---

## DEC-087 — Nested State Keys Fix

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Der Regex in `config_store.py` erlaubte nur einen Punkt im Key. Nested State
Keys wie `atmoweb_101.switches.a` oder `atmoweb_101.lights.uv` wurden
abgelehnt („Invalid state key").

### Entscheidung

Regex auf `^[a-z0-9_]+(\.[a-z0-9_]+)+$` geändert. Erlaubt beliebig viele
Punkte.

### Begründung

Nested State Keys sind notwendig für `switches.a-d` und `lights.day/uv/led`.

### Konsequenz

`config_store.py` `_SENSOR_KEY_RE` angepasst.

---

## DEC-088 — Alert-Messages runden und Einheiten umwandeln

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Die Alert-Messages zeigten Werte mit vielen Nachkommastellen (z. B.
`30.123 °C`) und rohe Einheiten (`celsius`, `percent`).

### Entscheidung

Werte werden auf 1 Nachkommastelle gerundet. Einheiten werden umgewandelt:
`celsius` → `°C`, `percent` → `%`, `mbar`/`ppm`/`rpm` bleiben.

### Begründung

Lesbarkeit. `30.1 °C` ist besser lesbar als `30.123 °C`.

### Konsequenz

`alert_engine.py` `_build_message` erweitert. `UNIT_LABELS` in
`alert_engine.py` definiert.

---

## DEC-089 — Chip-Texte mit Pfeilen

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Die Chips zeigten `Warn 20–23 °C`, was die Richtung (Min/Max) nicht klar
machte.

### Entscheidung

Pfeile für Min/Max: `Warn ↓ 20 °C · ↑ 23 °C`, `Crit ↓ 18 °C · ↑ 28 °C`,
`Rate ↕ 1 °C/h`. Nicht konfigurierte Chips: `Warn n/c`, `Crit n/c`,
`Rate n/c`.

### Begründung

Klarere Lesbarkeit. `↓` = Min, `↑` = Max, `↕` = beide Richtungen.

### Konsequenz

`admin.py` `buildDeviceContent` erweitert.

---

## DEC-090 — `resolve`-Fix: Alert bleibt aktiv, wenn ein Channel invalid ist

**Status:** Accepted
**Datum:** 2026-11-09

### Kontext

Nach dem Umbau auf „stale/invalid pro Gerät" wurde der `resolve`-Aufruf
noch pro Measurement ausgeführt. Wenn `temperature_1` `valid` war und
`temperature_2` `invalid`, wurde der Geräte-Alert resolved, obwohl der
Zustand noch aktiv war.

### Entscheidung

`resolve` wird nur aufgerufen, wenn **alle** Channels eines Geräts `valid`
sind. Wenn mindestens ein Channel `invalid`/`stale` ist, bleibt der Alert
aktiv.

### Begründung

Ein einzelner Sensor am Gerät kann `invalid` sein (z. B. Kabelsensor
defekt), während die anderen `valid` sind. Der Alert soll aktiv bleiben,
solange das Problem besteht.

### Konsequenz

`alert_engine.py` `_check_sensors` umgebaut: `resolve` aus der
Measurement-Schleife entfernt, in die Geräte-Logik verschoben.

---

## DEC-091 — Delete-Sicherheit

**Status:** Accepted
**Datum:** 2026-11-10

### Kontext

Räume mit Sensoren konnten gelöscht werden (die Sensoren wurden mitgelöscht).
Sensoren konnten gelöscht werden, ohne dass ihre Limits aus
`alarm_limits.json` entfernt wurden (verwaiste Limits).

### Entscheidung

1. **Doppelte Delete-Abfrage** bei Räumen und Sensoren (zweiter `confirm()`).
2. **`deleteRoom` verweigert**, wenn Sensoren im Raum sind.
3. **`deleteDevice` löscht Limits mit** (`sensors`, `states`, `device`).
4. **Alerts bleiben** (Option A, History).

### Begründung

- Verhindert versehentliches Löschen von Räumen mit Sensoren.
- Verhindert verwaiste Limits.
- Alerts bleiben für die History erhalten.

### Konsequenz

`admin.py` `deleteDevice` und `deleteRoom` erweitert.

---

## DEC-092 — How-to-Texte in allen Tabs

**Status:** Accepted
**Datum:** 2026-11-10

### Kontext

Die Admin-Tabs hatten keine oder veraltete How-to-Texte. Neue Nutzer wussten
nicht, was die Felder bedeuten.

### Entscheidung

How-to-Texte in allen Tabs (Rooms, Alarm Limits, Mail, Notifications,
Messages, Alerts).

### Begründung

Bessere Benutzerführung. Neue Nutzer finden sich schneller zurecht.

### Konsequenz

`admin.py` um `<details class="howto">`-Blöcke erweitert.

---

## DEC-093 — Dashboard-Limits (Chips, Statusleuchte, Graphen-Linien)

**Status:** Accepted
**Datum:** 2026-11-10

### Kontext

Limits waren im Dashboard nicht sichtbar. Der Nutzer musste im Admin
nachschauen, welche Limits gelten.

### Entscheidung

- **Limit-Chips** in den Metric-Zellen (Raumdetail: kompakt, Device-Detail:
  ausführlich). Nur wenn Limits gesetzt und enabled.
- **Statusleuchte** reagiert auf Limit-Verletzungen (rot/gelb).
- **Status-Chips** in der Chip-Leiste (`Warning: temperature above limit`).
- **Horizontale Limit-Linien** in den Charts (separate Datasets).

### Begründung

- Schneller Überblick über die Limits.
- Visueller Vergleich im Chart.
- Keine Redundanz mit dem Admin (dort werden die Limits konfiguriert).

### Konsequenz

`dashboard_data.py` um `_device_limits`, `_limit_status` erweitert.
`dashboard.py` um `_render_limit_chips` erweitert. `dashboard_charts.py`
um Limit-Linien erweitert.

---

## DEC-094 — Dashboard-Limits Bugfixes

**Status:** Accepted
**Datum:** 2026-11-10

### Kontext

Nach dem Einbau der Dashboard-Limits gab es mehrere Bugs:
- Graue Y-Achse (weil die Achse `y` hieß, die Limit-Linien aber
  `yAxisID: 'temperature'` hatten).
- Graue `humidity`-Achse (weil sie nur bei `hasHumidity` erstellt wurde).
- „No data for X min" bei Limit-Verletzungen (weil `_stale_age` zu
  aggressiv aufgerufen wurde).
- Falsche Chip-Reihenfolge (Limit-Chips nach Mode-Chips).
- Doppelte Limit-Chips (weil die Limit-Schleife zweimal drin war).
- Umbrechende Chips (weil die Metric-Zellen Block-Layout hatten).

### Entscheidung

- Y-Achse in `temperature` umbenannt.
- `humidity`-Achse immer erstellen.
- `_stale_age` nur bei `validity == "stale"`.
- Chip-Reihenfolge: Limit-Chips zuerst, Mode zuletzt.
- Doppelte Limit-Schleife entfernt.
- Flex-Layout für Metric-Zellen.

### Begründung

Konsistenz, Lesbarkeit, keine redundanten Chips.

### Konsequenz

`dashboard_charts.py`, `dashboard_data.py`, `dashboard.py` angepasst.

---

## DEC-095 — Alert-Tab als Tabelle mit Status-Zeile und Balkendiagramm

**Status:** Accepted
**Datum:** 2026-11-12

### Kontext

Der Alert-Tab zeigte Karten. Bei vielen Alerts wurde die Liste lang und
unübersichtlich.

### Entscheidung

- **Tabelle statt Karten:** Spalten: Status, Zeit, Severity, Regel, Gerät,
  Aktionen. Gruppiert nach Tagen.
- **Status-Zeile:** `3 active critical · 5 active warning · 12 resolved`.
- **Balkendiagramm:** 14 Tage kumulativ pro Tag, gestapelt.
- **Tooltip:** Volle Message beim Hover.

### Begründung

- Kompakter (mehr Alerts auf einen Blick).
- Gruppierung nach Tagen erleichtert die Orientierung.
- Balkendiagramm gibt einen schnellen Überblick über die Historie.

### Konsequenz

`alert_store.py` um `count_by_day()` und `count_by_status()` erweitert.
`otterpi.py` um `GET /api/admin/alerts/stats`. `admin.py` um Tabelle,
Status-Zeile und Balkendiagramm.

---

## DEC-096 — Klickbare Status-Zeile im Alert-Tab

**Status:** Accepted
**Datum:** 2026-11-13

### Kontext

Die Status-Zeile im Alert-Tab (`3 active critical · 5 active warning ·
12 resolved`) war bisher nur eine Anzeige. Der Nutzer musste die Filter
manuell über die Checkboxen setzen, um z.B. nur critical Alerts zu sehen.

### Entscheidung

Die drei Status-Items sind klickbar und filtern die Alert-Tabelle:

- Klick auf „3 active critical" → `status=active&severity=critical`
- Klick auf „5 active warning" → `status=active&severity=warning`
- Klick auf „12 resolved" → `status=resolved`

Ein erneuter Klick auf dasselbe Item hebt den Filter wieder auf (Toggle).
Der aktive Filter wird visuell hervorgehoben (`.alert-summary-item.active`).

### Begründung

- Schneller Zugriff auf die häufigsten Filter.
- Kein manuelles Setzen von Checkboxen nötig.
- Toggle-Verhalten ist intuitiv (kein separater „Clear"-Button nötig).

### Konsequenz

- `AlertStore.list_alerts()` um `severity` und `status` erweitert.
- `GET /api/admin/alerts` um `severity` und `status` Query-Parameter erweitert.
- `admin.py`: `filterByStatus()`-Funktion, `currentFilters`-State,
  `onclick`-Handler in `renderAlertSummary()`.
- CSS: `.alert-summary-item.active`.

---

# Offene Entscheidungen

Folgende Punkte sind derzeit bewusst noch offen:

- endgültiger Python-Kompatibilitätsbereich
- benötigte Python-Abhängigkeiten
- konkrete Retry-/Backoff-Parameter
- Queue-Größe und Aufbewahrungsdauer
- Umgang mit dauerhaft nicht zustellbaren Batches
- Authentifizierung und Autorisierung im produktiven Betrieb (geplant:
  API-Key-/Token-Ansatz)
- endgültige WeatherHub-Adapterimplementierung
- Zeitpunkt der Ablösung des Legacy-Observers
- Integration von States/Events (Change Detection)
