# Entwicklungsqualität und Kompatibilität

Dieses Dokument definiert die Qualitäts-Gates und Python-Kompatibilitätsregeln für LoggerPi-OtterPi.

Ziel ist, sicherzustellen, dass Änderungen nicht nur auf der lokalen Python-Version funktionieren, sondern auch mit der festgelegten minimalen Python-Version kompatibel bleiben und automatisch geprüft werden, bevor Änderungen akzeptiert werden.

## 1. Python-Kompatibilitätsvertrag

LoggerPi-OtterPi definiert aktuell:

```toml
requires-python = ">=3.9"
```

Damit ist Python 3.9 derzeit die minimal unterstützte Python-Version.

Die aktuelle Entwicklungs- und Testversion ist Python 3.13.

Der aktuelle Kompatibilitätsvertrag lautet daher:

- **Python 3.9** — minimal unterstützte Version
- **Python 3.13** — aktuelle Entwicklungs- und Testversion
- zukünftige Python-Versionen können bei Bedarf in die CI-Testmatrix aufgenommen werden

Wichtig ist die Unterscheidung:

> Eine erfolgreiche Ausführung der Tests unter Python 3.13 beweist nicht, dass der Code mit Python 3.9 kompatibel ist.

Deshalb wird Python 3.9 explizit in der CI getestet.

## 2. Lokale Entwicklungsumgebung

Die Entwicklung erfolgt in einer projektlokalen virtuellen Umgebung:

```text
.venv/
```

In VS Code soll der Python-Interpreter auf diese Umgebung zeigen.

Aktuell wird für die lokale Entwicklung Python 3.13 verwendet.

Die virtuelle Umgebung ist ausschließlich ein Hilfsmittel für die Entwicklung. Sie definiert nicht die minimale Kompatibilitätsversion des Projekts.

Maßgeblich für die minimale Python-Version sind `requires-python` und die CI.

## 3. Statische Analyse und Formatierung

Für statische Analyse, Import-Sortierung, Python-Kompatibilitätsprüfungen und Formatierung wird Ruff verwendet.

Die relevante Konfiguration befindet sich in `pyproject.toml`.

Aktuelles Ziel:

```toml
[tool.ruff]
line-length = 100
target-version = "py39"
```

Die aktuell aktivierten Ruff-Regeln sind:

```toml
[tool.ruff.lint]
select = [
    "E",
    "F",
    "I",
    "UP",
    "FA102",
]
```

Diese Kombination ist bewusst gewählt.

### 3.1 `E`

Prüfungen aus dem Umfeld von pycodestyle.

Sie erkennen allgemeine Stil- und Qualitätsprobleme.

### 3.2 `F`

Prüfungen aus dem Umfeld von Pyflakes.

Sie erkennen unter anderem:

- unbenutzte Imports
- undefinierte Namen
- unbenutzte Variablen
- weitere grundlegende statische Probleme

### 3.3 `I`

Prüfungen für Import-Sortierung und Import-Formatierung.

Die Reihenfolge der Imports wird daher nicht dauerhaft manuell gepflegt. Ruff ist hierfür die maßgebliche Instanz.

### 3.4 `UP`

Prüfungen aus dem Umfeld von Pyupgrade.

Sie erkennen unter anderem Möglichkeiten, Code mit modernerer Python-Syntax zu schreiben.

Da das Projekt Python 3.9 als Zielversion verwendet, darf `UP` jedoch nicht als Freigabe verstanden werden, beliebige Syntax neuerer Python-Versionen einzuführen.

### 3.5 `FA102`

`FA102` ist für dieses Projekt besonders wichtig.

Die Regel erkennt PEP-604- und PEP-585-Type-Annotationen, die für ältere Python-Versionen eine besondere Behandlung benötigen.

Beispielsweise soll folgende Schreibweise bei unserem Python-3.9-Kompatibilitätsziel nicht verwendet werden:

```python
def foo(value: str | None) -> None:
    ...
```

Ebenso:

```python
def foo(path: str | Path) -> None:
    ...
```

Stattdessen wird die für Python 3.9 geeignete Schreibweise verwendet:

```python
from typing import Optional


def foo(value: Optional[str]) -> None:
    ...
```

beziehungsweise:

```python
from typing import Union


def foo(path: Union[str, Path]) -> None:
    ...
```

### 3.5.1 Fachliche Auslegung von `FA102`

`FA102` wird in diesem Projekt als Kompatibilitäts-Gate für die minimale
Python-Version verstanden.

Die Regel soll verhindern, dass Type-Annotationen verwendet werden, deren
Syntax unter der minimal unterstützten Python-Version Python 3.9 nicht
direkt unterstützt wird.

Für LoggerPi-OtterPi gilt daher:

- Python 3.9 ist die minimale unterstützte Version.
- PEP-604-Union-Syntax wie `str | None` oder `str | Path` wird im
  Anwendungscode nicht verwendet.
- Entsprechende Annotationen werden mit `Optional[...]` beziehungsweise
  `Union[...]` aus `typing` formuliert.
- `from __future__ import annotations` wird nicht verwendet, um
  PEP-604-Syntax lediglich aus Kompatibilitätsgründen zu ermöglichen.
- `FA102` bleibt als explizites Ruff-Gate aktiviert.
- Ein grüner `ruff check .`-Lauf ist Teil des lokalen Quality Gates.

Wichtig ist die fachliche Einordnung:

`FA102` ist kein vollständiger Python-3.9-Kompatibilitätstest. Die Regel
prüft eine konkrete Klasse von Problemen bei Type-Annotationen.

Die tatsächliche Kompatibilität mit Python 3.9 wird zusätzlich durch den
Python-3.9-Lauf der GitHub-CI abgesichert.

Damit haben die beiden Prüfungen unterschiedliche Aufgaben:

```text
FA102
  → statische Erkennung problematischer Annotationen

Python-3.9-CI
  → tatsächliche Ausführung des Projekts unter Python 3.9
```

Ein Verstoß gegen `FA102` ist daher unabhängig davon ein Fehler, ob die
Tests auf dem lokalen Python-3.13-Interpreter erfolgreich laufen.


## 4. Regel für Type-Annotationen

Die Python-3.9-Kompatibilität ist Bestandteil des aktuellen Projektvertrags.

Daher gilt:

- Keine PEP-604-Union-Schreibweisen wie `str | None`.
- Keine Syntax einführen, die Python 3.10 oder neuer voraussetzt.
- Wo für Python 3.9 erforderlich, `Optional[...]` und `Union[...]` verwenden.
- Generische Typen nur in einer Form verwenden, die von der minimal unterstützten Python-Version unterstützt wird.
- `from __future__ import annotations` nicht lediglich hinzufügen, um neuere Annotation-Syntax verwenden zu können.

Dabei ist `from __future__ import annotations` grundsätzlich keine schlechte Python-Funktion.

Sie kann in anderen Projekten oder unter anderen Kompatibilitätsanforderungen sinnvoll sein.

Für LoggerPi-OtterPi wurde jedoch bewusst die klassische, unmittelbar mit Python 3.9 kompatible Schreibweise gewählt.

Dadurch ist ohne zusätzliche Annahmen erkennbar, welche Syntax die minimale Python-Version tatsächlich unterstützt.

## 5. Lokales Quality-Gate

Vor einem Commit werden alle drei Prüfungen ausgeführt:

```powershell
ruff check .
ruff format --check .
pytest
```

Alle drei Befehle müssen erfolgreich sein.

### Ruff-Prüfung

```powershell
ruff check .
```

muss ohne Fehler durchlaufen:

```text
All checks passed!
```

### Formatierungsprüfung

```powershell
ruff format --check .
```

muss bestätigen, dass die Dateien bereits korrekt formatiert sind.

### Test-Suite

```powershell
pytest
```

Alle Tests müssen erfolgreich sein.

Eine Änderung gilt lokal nicht als abgeschlossen, wenn zwar die Tests bestehen, Ruff aber fehlschlägt oder umgekehrt.

## 6. Entwicklungsabhängigkeiten

Die Entwicklungswerkzeuge werden in `pyproject.toml` definiert und nicht ausschließlich in der lokalen Umgebung verwaltet.

Aktuell enthält die Entwicklungsgruppe:

```toml
[dependency-groups]
dev = [
    "pytest>=8.4,<9",
    "ruff>=0.16.5,<0.17",
]
```

Die Entwicklungsabhängigkeiten werden daher aus der Projektkonfiguration installiert:

```powershell
python -m pip install --group dev
```

Dadurch bleiben lokale Entwicklung und CI möglichst konsistent.

Nach Änderungen an den Entwicklungsabhängigkeiten müssen die lokale Umgebung und anschließend die vollständige Quality-Gate-Prüfung aktualisiert beziehungsweise erneut ausgeführt werden.

## 7. Continuous Integration

GitHub Actions stellt das zweite und verbindliche Kompatibilitäts-Gate dar.

Der CI-Workflow befindet sich unter:

```text
.github/workflows/ci.yml
```

Die aktuelle Testmatrix enthält:

```yaml
matrix:
  python-version:
    - "3.9"
    - "3.13"
```

Für beide Python-Versionen werden dieselben grundlegenden Prüfungen durchgeführt:

1. Repository auschecken
2. Projekt installieren
3. Entwicklungsabhängigkeiten installieren
4. Python- und Werkzeugversionen anzeigen
5. Ruff ausführen
6. Formatierung prüfen
7. Tests ausführen

Damit wird sowohl geprüft:

```text
Python 3.9  → minimale Kompatibilität
Python 3.13 → aktuelle Entwicklungs-/Laufzeitkompatibilität
```

Ein erfolgreicher lokaler Testlauf unter Python 3.13 reicht daher nicht aus, wenn der Python-3.9-CI-Lauf fehlschlägt.

## 8. Warum die minimale Python-Version in CI getestet wird

Die deklarierte Kompatibilitätsgrenze und der tatsächlich für die Entwicklung verwendete Interpreter sind zwei unterschiedliche Dinge.

Beispielsweise bedeutet:

```text
requires-python = ">=3.9"
```

bei lokaler Entwicklung unter Python 3.13, dass versehentlich Syntax von Python 3.10 oder neuer verwendet werden kann, obwohl sämtliche lokalen Tests erfolgreich sind.

Ohne einen expliziten Python-3.9-CI-Lauf könnte eine solche Regression unbemerkt bleiben.

Die CI-Matrix enthält deshalb bewusst die minimale unterstützte Python-Version.

Dieser Lauf ist kein redundanter Test, sondern ein tatsächlicher Kompatibilitätstest.

## 9. Lessons Learned: Python-3.9-Kompatibilitätsfehler

Ein früherer Änderungsstand hat gezeigt, warum diese Prüfungen notwendig sind.

Im Code wurden PEP-604-Union-Annotationen wie:

```python
str | Path
```

und:

```python
dict[str, Measurement] | None
```

verwendet.

Unter Python 3.13 funktionierte der Code.

Unter Python 3.9 entsprach diese Schreibweise jedoch nicht dem festgelegten Kompatibilitätsziel.

Die entscheidende Erkenntnis war:

> Eine grüne Test-Suite auf der aktuell verwendeten Python-Version beweist nicht die Kompatibilität mit der minimal unterstützten Python-Version.

Die betroffenen Annotationen wurden deshalb auf Python-3.9-kompatible Formen mit `Union` und `Optional` umgestellt.

Anschließend wurde Ruff um `FA102` ergänzt, damit diese Klasse von Fehlern bereits lokal erkannt wird.

Die Python-3.9-CI bleibt die zusätzliche Absicherung, die den Code tatsächlich mit dem minimal unterstützten Interpreter ausführt.

Damit besteht das Schutznetz aus mehreren Ebenen:

```text
Entwickler schreibt Code
        ↓
Ruff statische Analyse
        ↓
FA102 erkennt problematische Annotationen
        ↓
Lokale pytest-Suite
        ↓
GitHub CI unter Python 3.9
        ↓
GitHub CI unter Python 3.13
```

## 10. Warum mehrere Ebenen notwendig sind

Kein einzelnes Werkzeug bietet vollständigen Schutz.

### Ruff

Erkennt viele Probleme bereits vor der Ausführung, darunter mit den aktivierten Regeln auch bestimmte Python-Kompatibilitätsprobleme.

### Pytest

Prüft das tatsächliche Laufzeitverhalten und die Anwendungslogik.

### Python 3.9 CI

Führt das Projekt tatsächlich mit dem minimal unterstützten Interpreter aus.

### Python 3.13 CI

Stellt sicher, dass das Projekt auch mit der aktuellen Entwicklungs-/Testversion funktioniert.

Jede Ebene deckt damit eine andere Fehlerklasse ab.

## 11. Vorgehen vor einem Commit

Für normale Änderungen am Quellcode:

```powershell
ruff check .
ruff format --check .
pytest
git status
```

Anschließend sollte der Arbeitsbaum ausschließlich beabsichtigte Änderungen enthalten.

Vor dem Staging sollte außerdem das tatsächliche Diff geprüft werden:

```powershell
git diff
```

Für bereits gestagte Änderungen:

```powershell
git diff --cached
```

Zusätzliche Prüfung auf Whitespace-Probleme:

```powershell
git diff --check
```

Ein sauberer lokaler Durchlauf sieht damit ungefähr so aus:

```text
ruff check .          → All checks passed
ruff format --check . → alle Dateien formatiert
pytest                → alle Tests erfolgreich
git diff --check      → keine Fehler
```

## 12. Änderungen an der Python-Kompatibilitätsgrenze

Wenn die minimal unterstützte Python-Version in Zukunft bewusst geändert wird, müssen mindestens folgende Punkte gemeinsam überprüft werden:

- `project.requires-python`
- Ruff `target-version`
- Python-Kompatibilitätsregeln von Ruff
- Type-Annotation-Regeln
- Python-Versionen in der GitHub-Actions-Matrix
- Entwicklungsdokumentation
- Tests
- Kompatibilität der Abhängigkeiten
- Laufzeit- und Deployment-Anforderungen
- entsprechende Architektur-/Entscheidungsdokumentation

Die minimale Python-Version darf nicht lediglich deshalb geändert werden, weil eine neuere Python-Version für die Entwicklung bequemer ist.

Eine Änderung der Kompatibilitätsgrenze ist eine bewusste Projektentscheidung.

## 13. Quellen der Wahrheit

Für die relevanten Bereiche gilt folgende Hierarchie:

1. `pyproject.toml` definiert die deklarierte Python- und Entwicklungswerkzeug-Konfiguration.
2. `.github/workflows/ci.yml` definiert die automatisierte Python-Kompatibilitätsmatrix.
3. Dieses Dokument beschreibt Entwicklungs- und Quality-Gate-Regeln.
4. `DECISIONS.md` dokumentiert wesentliche Projektentscheidungen und deren Begründungen.
5. Die lokale `.venv` ist ein Detail der Entwicklungsumgebung und keine Kompatibilitätsdefinition.

Wenn Dokumentation und Konfiguration voneinander abweichen, gilt zunächst die Konfiguration als technische Quelle der Wahrheit. Die Dokumentation muss anschließend korrigiert werden.

## 14. Definition of Done

Eine Änderung gilt als bereit, wenn:

- die gewünschte Funktionalität implementiert ist
- die vorhandenen Tests erfolgreich sind
- für neue Funktionalität geeignete Tests vorhanden sind
- `ruff check .` erfolgreich ist
- `ruff format --check .` erfolgreich ist
- Python-3.9-Kompatibilität erhalten bleibt
- Python 3.13 weiterhin unterstützt wird
- die GitHub-CI-Matrix vollständig grün ist
- keine unbeabsichtigten Änderungen im Arbeitsbaum verbleiben
- relevante Architektur- oder Entwicklungsdokumentation aktualisiert wurde

Diese Regeln sollen keinen unnötigen bürokratischen Aufwand erzeugen.

Sie sollen das Repository gegen genau die Art von unbemerkten Kompatibilitätsfehlern absichern, die zuvor aufgetreten ist.
