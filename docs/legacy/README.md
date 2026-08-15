# Legacy

Dieser Ordner enthält die Dokumentation und Referenzdateien für die frühere LoggerPi-Implementierung.

Die Dateien hier dienen als **historische Referenz** für die ursprüngliche Architektur und Implementierung. Sie sind **nicht** die Spezifikation des aktuellen Datenmodells oder der aktuellen LoggerPi-Architektur.

## Inhalt

### `observer.md`

Dokumentation der ursprünglichen `observer.py`-Implementierung.

Die Datei beschreibt insbesondere:

- die ursprüngliche Datenerfassung,
- die verwendeten Datenquellen,
- die Zuordnung der Messwerte zu ThingSpeak-Feldern,
- den ursprünglichen Upload-Mechanismus,
- die zeitgesteuerte Verarbeitung,
- bekannte Eigenschaften und Einschränkungen der Legacy-Implementierung.

### `observer.py`

Referenzkopie der ursprünglichen `observer.py`.

Diese Datei bleibt erhalten, damit nachvollziehbar bleibt, wie die frühere LoggerPi-Implementierung tatsächlich aufgebaut war.

**Wichtig:** Die Legacy-Dateien werden nicht als Grundlage für die Weiterentwicklung des aktuellen Datenmodells verwendet. Bei der Entwicklung ist der aktuelle Stand unter `docs/data-model/` sowie die aktuelle Projektbeschreibung in `docs/PROJECT-STATE.md` maßgeblich.

## Zweck des Legacy-Bereichs

Der Legacy-Bereich verhindert, dass historische Implementierungsdetails verloren gehen, ohne sie mit dem aktuellen Architekturstand zu vermischen.

Insbesondere soll nachvollziehbar bleiben:

1. welche Funktionen die ursprüngliche Implementierung hatte,
2. welche Datenquellen ursprünglich verwendet wurden,
3. welche Annahmen und technischen Einschränkungen damals bestanden,
4. welche Teile später durch das neue Datenmodell ersetzt oder weiterentwickelt wurden.

Neue Änderungen am aktuellen System sollen grundsätzlich **nicht** in diesen Legacy-Dateien dokumentiert werden.
