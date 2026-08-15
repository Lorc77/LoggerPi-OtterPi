# Legacy `observer.py`

## Status

**LEGACY / NUR REFERENZ**

Diese Datei dokumentiert die bisher produktiv eingesetzte LoggerPi-Anwendung
`observer.py`.

Sie dient als historische und technische Referenz für die Ablösung durch die
neue LoggerPi → OtterPi-Architektur.

Die archivierte Datei `observer.py` wurde nicht refaktoriert oder bereinigt.
Sie soll das bisherige Verhalten möglichst unverändert dokumentieren.

## Herkunft

Produktiver Pfad auf dem bisherigen LoggerPi:

```text
/home/ZOOLOGY-observ/Programs/observer.py
```

Die produktive Anwendung wurde über `/etc/rc.local` gestartet:

```text
python /home/ZOOLOGY-observ/Programs/observer.py &
```

Damit wurde die Anwendung beim Systemstart automatisch im Hintergrund
gestartet.

## Archivierte Version

Die archivierte `observer.py` entspricht der am LoggerPi erfassten produktiven
Version.

SHA-256 der vom LoggerPi kopierten Datei:

```text
f740d8832208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0
```

Dieser Hash dient zur eindeutigen Identifikation der dokumentierten
Legacy-Version.

## Aufgabe

Die Legacy-Anwendung erfasst regelmäßig Mess- und Systemdaten vom LoggerPi
und überträgt diese gesammelt an einen ThingSpeak-Kanal.

Die Anwendung arbeitet kontinuierlich in einer Endlosschleife.

Der Datenfluss besteht im Wesentlichen aus:

```text
AtmoWEB-Geräte ─┐
                 │
Freezer-Log ────┼──> observer.py ──> message_buffer ──> ThingSpeak
                 │
LoggerPi ───────┘
```

## Datenquellen

### AtmoWEB 101

Vom AtmoWEB-Gerät mit der Adresse `141.51.190.101` werden abgefragt:

- Temperatur über `Temp1Read`
- relative Feuchte über `HumRead`

### AtmoWEB 102

Vom AtmoWEB-Gerät mit der Adresse `141.51.190.102` werden abgefragt:

- Temperatur über `Temp1Read`
- relative Feuchte über `HumRead`
- LED-Wert über `LightLED`

Die Abfragen erfolgen im Legacy-Code über `curl`.

### Freezer

Die Freezer-Temperatur wird aus der letzten Zeile der Datei

```text
/home/ZOOLOGY-observ/Programs/freezer.log
```

extrahiert.

Der Legacy-Code erwartet dabei ein bestimmtes Textformat und extrahiert den
Temperaturwert über String-Splitting.

Der ausgelesene Wert wird anschließend negiert und als `field7` übertragen.

### LoggerPi-Systemdaten

Zusätzlich werden lokale Systemdaten des LoggerPi erfasst:

- CPU-Temperatur
- CPU-Auslastung

Die CPU-Temperatur wird über

```text
vcgencmd measure_temp
```

ermittelt.

Die CPU-Auslastung wird über

```python
psutil.cpu_percent(interval=2)
```

ermittelt.

## Erfassungsintervall

Die Variable

```python
update_interval = 900
```

legt fest, dass die Anwendung ungefähr alle **900 Sekunden (15 Minuten)**
einen neuen Datensatz erfasst.

Die Anwendung prüft die Zeitbedingung innerhalb einer Schleife und ruft
`updatesJson()` nach Ablauf dieses Intervalls auf.

## Übertragungsintervall

Die Variable

```python
posting_interval = 900
```

legt fest, dass der `message_buffer` ungefähr alle **900 Sekunden
(15 Minuten)** an ThingSpeak übertragen wird.

Im aktuell archivierten Code sind `update_interval` und `posting_interval`
beide auf 900 Sekunden gesetzt. Dadurch wird im Normalbetrieb ungefähr ein
Messdatensatz pro Übertragungszyklus erzeugt und anschließend übertragen.

Die Anwendung verwendet trotzdem einen Buffer, sodass mehrere Einträge
grundsätzlich gesammelt und gemeinsam übertragen werden könnten, falls sich
die Intervalle oder die Laufzeitlogik ändern.

## ThingSpeak

Die Legacy-Anwendung verwendet den ThingSpeak-Bulk-Update-Endpunkt:

```text
https://api.thingspeak.com/channels/<channel_ID>/bulk_update.json
```

Der Channel ist im Legacy-Code fest konfiguriert.

Die Authentifizierung erfolgt über einen im Quellcode hinterlegten
Write API Key.

**Hinweis:** Der tatsächliche API Key wird in dieser Dokumentation nicht
archiviert.

## ThingSpeak-Feldbelegung

Die bisherige Anwendung verwendet acht Felder:

| ThingSpeak Field | Inhalt |
|---|---|
| `field1` | AtmoWEB 101 Temperatur |
| `field2` | AtmoWEB 101 relative Feuchte |
| `field3` | AtmoWEB 102 Temperatur |
| `field4` | AtmoWEB 102 relative Feuchte |
| `field5` | LoggerPi CPU-Temperatur |
| `field6` | LoggerPi CPU-Auslastung |
| `field7` | Freezer-Temperatur |
| `field8` | AtmoWEB 102 LED-Wert |

Die ThingSpeak-Feldnummern stellen ausschließlich die historische
Legacy-Abbildung dar.

Sie sind **nicht** die Definition des neuen Datenmodells.

## Batch-Verarbeitung

Jeder erfasste Messwert wird als Dictionary in `message_buffer` abgelegt.

Ein Eintrag enthält:

```text
delta_t
field1
field2
field3
field4
field5
field6
field7
field8
```

`delta_t` beschreibt im Legacy-Protokoll die seit dem letzten
`last_update_time` vergangene Zeit.

Beim Erreichen des Übertragungsintervalls wird der gesamte Puffer als JSON
an ThingSpeak übertragen.

Nach dem HTTP-Aufruf wird der lokale Puffer zurückgesetzt.

## Start und Laufzeit

Die Anwendung wird nicht über einen eigenen systemd-Service gestartet.

Der bisherige Start erfolgt über:

```text
/etc/rc.local
```

mit:

```text
python /home/ZOOLOGY-observ/Programs/observer.py &
```

Die Anwendung läuft dadurch als Hintergrundprozess.

Auf dem aktuell untersuchten LoggerPi war sie als Prozess sichtbar als:

```text
python /home/ZOOLOGY-observ/Programs/observer.py
```

## Abhängigkeiten

Die Legacy-Anwendung verwendet unter anderem:

### Python-Module

- `json`
- `time`
- `os`
- `psutil`
- `requests`
- `subprocess`

### Externe Programme / Systemkomponenten

- `curl`
- `sed`
- `vcgencmd`
- ThingSpeak HTTP API
- AtmoWEB HTTP-Schnittstellen

## Bekannte Eigenschaften und technische Schulden

Der Legacy-Code ist historisch gewachsen und wird nicht als Vorlage für die
neue Architektur betrachtet.

Unter anderem:

- Datenquellen werden direkt innerhalb einer einzelnen Python-Datei
  abgefragt.
- HTTP-Abfragen werden über Shell-Kommandos und `curl` ausgeführt.
- Freezer-Daten werden durch Textverarbeitung aus einer Logdatei extrahiert.
- ThingSpeak-Feldnummern bilden direkt das damalige Datenmodell ab.
- Es gibt keine persistente lokale Batch-Queue.
- Es gibt keine persistente Sequenznummer pro LoggerPi.
- Die Datenübertragung besitzt kein mit dem neuen Architekturmodell
  vergleichbares ACK-/Retry-Verfahren.
- Fehlerbehandlung ist teilweise rudimentär.
- Datenquellen und deren Parsing sind direkt mit der Übertragungslogik
  gekoppelt.
- Zugangsdaten zur ThingSpeak-API waren Bestandteil des Legacy-Quellcodes.
- Mehrere Kommentare im Legacy-Code entsprechen nicht mehr exakt den
  tatsächlich konfigurierten Intervallen.

Diese Eigenschaften dokumentieren den damaligen Stand und sollen bei der
Ablösung nicht ungeprüft übernommen werden.

## Bedeutung für die neue Architektur

Die Legacy-Anwendung ist wichtig, um sicherzustellen, dass bei der Migration
keine bisher tatsächlich erfassten Informationen verloren gehen.

Die fachliche Definition der neuen Lösung erfolgt jedoch ausschließlich über
das aktuelle Data Model und die dazugehörigen Dokumente im Repository.

Insbesondere sind die historischen ThingSpeak-Feldnummern nicht als neue
universelle Datenfeldnamen zu verstehen.

Die grundsätzliche Zielarchitektur ist:

```text
Quelle / Hersteller-Schnittstelle
            │
            ▼
       Reader / Adapter
            │
            ▼
     gemeinsames Data Model
            │
            ▼
        Core / Batch
            │
            ▼
          OtterPi
```

Die Legacy-`observer.py` dient dabei als **Quelle für Anforderungen und
Migrationsabgleich**, nicht als Architekturvorlage.

## Ablösung

Die `observer.py` soll langfristig durch die neue LoggerPi → OtterPi-Lösung
ersetzt werden.

Bis die neue Lösung vollständig implementiert, getestet und produktiv
validiert ist, bleibt die Legacy-Anwendung eine wichtige Referenz für das
bisherige Produktionsverhalten.

Bei der Migration ist insbesondere zu prüfen, dass alle bisher tatsächlich
erfassten Messgrößen und deren fachliche Bedeutung im neuen Data Model
berücksichtigt wurden.

## Verwandte Dokumentation

Die normative Beschreibung der neuen Architektur befindet sich in den
aktuellen Data-Model- und Baseline-Dokumenten des Repositorys.

Diese Legacy-Dokumentation beschreibt dagegen ausschließlich den historischen
Ist-Zustand der bisherigen `observer.py`.

---

**Status:** Legacy / nur Referenz  
**Quelle:** produktiver LoggerPi  
**Archivierte Datei:** `docs/legacy/observer.py`  
**SHA-256:** `f740d8832208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0`
