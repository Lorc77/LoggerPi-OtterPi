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

## Python-Kompatibilitätsstrategie

LoggerPi und OtterPi müssen nicht dieselbe Python-Version verwenden.

Die Kommunikation zwischen beiden Systemen erfolgt über den
versionierten HTTP-/JSON-Contract und nicht über eine gemeinsame
Python-Laufzeitumgebung.

Der neue Anwendungscode soll zunächst möglichst mit der vorhandenen
Python-3.9-Umgebung des LoggerPi kompatibel sein.

Python 3.9 ist allerdings bereits End-of-Life und soll deshalb nicht
automatisch als langfristige Entwicklungsbasis festgelegt werden.

Die endgültige Python-Kompatibilitätsanforderung bleibt offen, bis die
benötigten Abhängigkeiten und die tatsächlichen Laufzeitanforderungen
geprüft wurden.

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
