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

**Status:** Vorgeschlagen

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

- `pytest >=9.1.1,<10`
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
