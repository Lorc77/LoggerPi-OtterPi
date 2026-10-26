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

Seit `v1.2.0` stellt der OtterPi ein Dashboard unter
`https://zoology.makki.route64.de` bereit.

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
- Dashboard auf dem OtterPi (geplant: `zoology.makki.route64.de`)
