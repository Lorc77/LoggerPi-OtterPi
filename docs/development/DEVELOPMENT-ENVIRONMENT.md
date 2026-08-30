# Entwicklungsumgebung

## Zweck

Dieses Dokument beschreibt die Entwicklungsumgebung für das Projekt
LoggerPi-OtterPi.

Die Entwicklungsumgebung ist bewusst von den Laufzeitumgebungen des
LoggerPi und OtterPi getrennt.

## Entwicklungsrechner

### Betriebssystem

- Windows 11

### IDE / Editor

- Visual Studio Code
- stabile Version, nicht VS Code Insiders

VS Code ist unsere primäre Entwicklungsumgebung.

### KI-Unterstützung

ChatGPT wird als KI-Unterstützung bei Entwicklung, Dokumentation,
Analyse, Reviews und Fehlersuche eingesetzt.

Google Antigravity SDK bzw. darauf basierende Entwicklungswerkzeuge
sind nicht Bestandteil unserer geplanten Pipeline.

## Versionsverwaltung

### Git

Git for Windows wird für die lokale Versionsverwaltung eingesetzt.

Aktuell installiert:

- Git 2.55.0.windows.5

### Repository

GitHub-Repository:

`Lorc77/LoggerPi-OtterPi`

Lokaler Pfad:

`D:\Misc\_Makki_Heimserver\LoggerPi-OtterPi`

### Git-Konfiguration

- Hauptbranch: `main`
- Remote: `origin`
- Transport: HTTPS
- HTTPS-Backend: OpenSSL
- Credential Helper: Git Credential Manager
- Standardverhalten von `git pull`: merge
- Working Tree war nach dem Klonen sauber

### Ausgangszustand

Das Repository wurde erfolgreich von GitHub geklont.

Bei der ersten Prüfung:

- Branch: `main`
- Tracking-Branch: `origin/main`
- Working Tree: clean
- Remote-Branch: `origin/main`

## Python

Für die Windows-Entwicklung wird aktuell Python 3.13.15 verwendet.

Installationspfad:

`C:\Program Files\Python313\`

Die Installation wurde im VS-Code-Terminal erfolgreich überprüft:

- `python --version` → Python 3.13.15
- `py --version` → Python 3.13.15
- `python -m pip --version` → pip für Python 3.13
- `python` verweist auf `C:\Program Files\Python313\python.exe`

Die systemweite Python-Installation dient als Basis für die
Entwicklungsumgebung. Projektabhängigkeiten werden nicht direkt in dieser
globalen Installation installiert.

### Virtuelle Umgebung

Jedes Python-Projekt verwendet eine eigene virtuelle Umgebung.

Für dieses Repository liegt sie unter:

`.venv\`

Die Umgebung wird mit

```powershell
python -m venv .venv
```

erstellt und kann in PowerShell mit

```powershell
.\.venv\Scripts\Activate.ps1
```

aktiviert werden.

Falls PowerShell die Ausführung von Skripten verhindert, wird für den
aktuellen Benutzer folgende Ausführungsrichtlinie verwendet:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Eine systemweite Änderung der PowerShell-Ausführungsrichtlinie ist nicht
erforderlich.

Die virtuelle Umgebung wurde erfolgreich verifiziert. Innerhalb der
aktivierten Umgebung verweist `python` auf den Interpreter der
projektlokalen `.venv`.

Die `.venv` wird nicht versioniert.


### VS-Code-Python-Unterstützung

Für die Python-Entwicklung sind derzeit folgende VS-Code-Erweiterungen
installiert:

- Python
- Pylance
- Python Debugger
- Python Environments

VS Code verwendet für dieses Repository die projektlokale virtuelle
Umgebung.

Die Workspace-Konfiguration liegt unter:

`.vscode/settings.json`

und verwendet einen relativen Pfad:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe"
}
```

Damit ist die Konfiguration nicht an einen persönlichen absoluten
Installationspfad gebunden.

Die automatische Aktivierung der `.venv` in einem neuen integrierten
PowerShell-Terminal wurde erfolgreich verifiziert.


## Python-Versionen

LoggerPi-OtterPi unterstützt aktuell Python **3.9 und höher**.

Python 3.9 ist dabei die minimale unterstützte Version und damit Teil des Kompatibilitätsvertrags des Projekts.

Für die lokale Entwicklung wird aktuell Python **3.13** verwendet. Die projektlokale virtuelle Umgebung `.venv` wird mit diesem Interpreter betrieben.

Die lokale Entwicklungsumgebung und die minimale unterstützte Python-Version sind bewusst nicht identisch:

```text
Lokale Entwicklung:        Python 3.13
Minimale Unterstützung:    Python 3.9
CI-Kompatibilitätstest:     Python 3.9 + Python 3.13
```

Der Python-3.9-CI-Lauf ist notwendig, weil ein erfolgreicher Testlauf unter Python 3.13 allein keine Kompatibilität mit Python 3.9 garantiert.

Die Python-Kompatibilitäts- und Quality-Gate-Regeln sind ausführlich in `docs/development/DEVELOPMENT-QUALITY.md` dokumentiert.

Wesentliche technische Vorgaben:

- `pyproject.toml` definiert `requires-python = ">=3.9"`.
- Ruff verwendet `target-version = "py39"`.
- Python-3.9-kompatible Type-Annotation-Syntax wird verwendet.
- Ruff `FA102` dient als statisches Teil-Gate für Type-Annotation-
  Kompatibilität. Die Regel erkennt insbesondere PEP-604-/PEP-585-
  Annotationen, die bei einer Unterstützung von Python 3.9 problematisch
  sein können. `FA102` ersetzt nicht den tatsächlichen Python-3.9-CI-Lauf.
- Die GitHub Actions testen den Code unter Python 3.9 und Python 3.13.


## Zielsysteme

LoggerPi und OtterPi verwenden bewusst ihre vorhandenen nativen
Linux-Laufzeitumgebungen.

Docker bzw. Container sind auf den Zielsystemen nicht vorgesehen.

### LoggerPi

Aktueller Stand:

- Distribution: Raspbian GNU/Linux 11 (bullseye)
- Architektur: ARMv7 (`armv7l`)
- System-Python: Python 3.9.2

Die vorhandene Laufzeitumgebung soll während der Migration möglichst
unangetastet bleiben.

### OtterPi

Aktueller Stand:

- Distribution: Debian GNU/Linux 13 (trixie)
- Architektur: ARM64 (`aarch64`)
- System-Python: Python 3.13.5


## Grundsätze für die Zielsysteme

Die Zielsysteme sollen möglichst schlank bleiben.

Vorgesehen sind:

- native Linux-Prozesse
- native Python-Laufzeit
- `systemd` für geeignete Dienste
- kein Docker
- keine Container-Laufzeit
- keine unnötigen Entwicklungswerkzeuge auf LoggerPi oder OtterPi

Entwicklungswerkzeuge bleiben soweit möglich auf dem Windows-
Entwicklungsrechner.

## Status

Die grundlegende Windows-Entwicklungsumgebung wurde eingerichtet und
erfolgreich verifiziert.

Verifiziert sind:

- Windows 11
- stabile Version von Visual Studio Code
- Python 3.13.15
- pip
- Python Launcher (`py`)
- projektlokale virtuelle Umgebung `.venv`
- VS-Code-Python-Unterstützung
- Pylance
- Python Debugger
- Python Environments
- automatische Verwendung der `.venv` durch VS Code
- automatische Aktivierung der `.venv` im integrierten PowerShell-Terminal

Die konkrete Python-Kompatibilität des neuen Anwendungscodes bleibt
weiterhin offen und wird nicht allein durch die verwendete
Entwicklungs-Python-Version festgelegt.

Dieses Dokument ersetzt nicht die technischen Baselines oder die
Architekturdokumentation des Projekts.
