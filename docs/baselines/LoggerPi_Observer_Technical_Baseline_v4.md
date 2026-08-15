# LoggerPi /OBSERVER – TECHNICAL BASELINE / EXPLORATION RECORD v4

**Projekt:** ZOOLOGY / LoggerPi  
**System:** Raspberry Pi observer  
**Rolle:** LoggerPi / Datenerfassungsgerät  
**Zielsystem:** OtterPi / Raspberry-Pi-Server  
**Stand:** 13./14.08.2026  
**Status:** **Exploration abgeschlossen – Referenzstand eingefroren**

---

## 0. TERMINOLOGIE / SYSTEMROLLEN

Diese Begriffe sind für die weitere Arbeit verbindlich.

| Begriff | Bedeutung |
|---|---|
| **LoggerPi** | Raspberry Pi, der die Messdaten erfasst |
| **observer** | Hostname des LoggerPi |
| **Observer** | Logger-/Datenerfassungssoftware auf dem LoggerPi |
| **alter Observer** | aktuell produktives `/home/ZOOLOGY-observ/Programs/observer.py` |
| **neuer Observer** | zukünftiges, neu aufgebautes Erfassungsskript auf dem LoggerPi |
| **OtterPi** | separater Raspberry-Pi-Server, der Daten empfängt, visualisiert und ggf. speichert |
| **ThingSpeak** | derzeitiges externes Datenziel; perspektivisch Übergangs-/Legacy-Komponente |

**Wichtig:**  
Der **OtterPi ist nicht der Observer**.

Der LoggerPi/observer sammelt Daten.

Der OtterPi ist das nachgelagerte Serversystem.

---

## 1. ARCHITEKTUR – AKTUELL

Die aktuelle Datenarchitektur ist:

```text
                  LOGGERPI

              Raspberry Pi

              Hostname: observer

                    │

        ┌───────────┼────────────┐
        │           │            │
        ▼           ▼            ▼

    Sensor 101   Sensor 102   Freezer

        │           │            │

        │           │       USB-Serial

        │           │            │

        │           │        /dev/ttyUSB0

        │           │            │

        │           │         minicom

        │           │            │

        │           │        freezer.log

        │           │            │

        └───────────┼────────────┘

                    ▼

               observer.py

                    │

                    ▼

               ThingSpeak
```

Der OtterPi ist **noch nicht Bestandteil dieser produktiven Messkette**.

---

## 2. ZIELARCHITEKTUR – PERSPEKTIVISCH

Die geplante Zielrichtung ist:

```text
                 LOGGERPI

              Raspberry Pi

              Hostname observer

                     │

         ┌───────────┼────────────┐
         │           │            │
      Sensoren     Freezer    System Health
         │           │            │
         └───────────┼────────────┘
                     ▼
              neuer Observer
                     │
                     │ Netzwerk
                     ▼
                  OTTERPI
              Raspberry-Pi-Server
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
      Speicherung Visualisierung weitere
                               Verarbeitung
```

ThingSpeak soll während der Migration als **temporärer Kompatibilitäts-/Batch-Upload** weitergeführt werden können.

---

## 3. HARDWARE & OS – LOGGERPI

| Parameter | Wert |
|---|---|
| Hostname | observer |
| Raspberry-Pi-Modell | Raspberry Pi 3 Model B Rev 1.2 |
| OS | Raspbian GNU/Linux 11 (bullseye) |
| Kernel | 6.1.21-v7+ |
| Architektur | armv7l |
| RAM | 921 MiB total |
| Swap | 0 B |
| Root-Partition | /dev/root, 15 GiB |
| Zugriff | MeshCentral → Terminal |
| produktiver Observer-Prozess | Root |

Zum dokumentierten Zeitpunkt lag die CPU-Temperatur nach Behebung des Busy-Loops bei ungefähr **49–50 °C**.

---

## 4. PYTHON-UMGEBUNG

- Python **3.9.2**
- keine virtuelle Umgebung
- wichtige Pakete:
  - requests
  - pyserial
  - psutil
  - Flask
  - gpiozero
  - RPi.GPIO
  - numpy
  - weitere installierte Pakete

Produktives Skript:

`/home/ZOOLOGY-observ/Programs/observer.py`

---

## 5. ALTER OBSERVER – START

Der alte Observer wird weiterhin über `/etc/rc.local` gestartet:

```text
python /home/ZOOLOGY-observ/Programs/observer.py &
```

`rc-local.service` ist aktiv.

Der aktuell produktive Prozess war zuletzt:

```text
PID     13821
PPID    1
USER    root
STAT    S
CMD     python /home/ZOOLOGY-observ/Programs/observer.py
```

Der Prozess wurde nach dem Produktivwechsel bewusst neu gestartet.

---

## 6. VERSION DES ALTEN OBSERVERS

**Original**

`9126d43d224be145e58467f34b5f5eb693dd103ddf1d0a4503729b66a663f007`

**Nach CPU-Fix / vor popen-Fix**

`f66d5c48e8208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0`

**Aktuell produktiv**

`f740d8832208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0`

Backup vor dem os.popen()-Fix:

`/home/ZOOLOGY-observ/Programs/observer.py.before_popen_fix`

SHA256:

`f66d5c48e8208e83735c8b10493cd586f17374c9529652af305eb20e3a8ff7dd0`

---

## 7. CPU-BUSY-LOOP – GELÖST

Ursprüngliche Struktur:

```text
while True:
    if time.time() - last_update_time >= update_interval:
        updatesJson()
```

Keine Pause → Busy Loop.

Gemessen:

1.082.799 Schleifen / 5 Sekunden

≈ 216.560 Schleifen/s

CPU:

≈ 99.6–99.7 %

**Fix**

```text
while True:
    if time.time() - last_update_time >= update_interval:
        updatesJson()

    time.sleep(1)
```

**Ergebnis**

Nach dem Fix:

≈ 0–1 % CPU

Zuletzt:

CPU 0.0 %

CPU-Zeit ≈ 1 s

bei rund 49 Minuten Prozesslaufzeit.

**Status: GELÖST.**

---

## 8. CPU-TEMPERATUR

Vor dem CPU-Fix:

≈ 64.5–65 °C

Nach dem Fix:

52.1 °C

51.0 °C

51.5 °C

50.5 °C

49.9 °C

49.4 °C

Der deutliche Rückgang bestätigt unabhängig die Beseitigung des Busy-Loops.

**Status: unauffällig.**

---

## 9. ZOMBIE-PROZESSE – GELÖST / FIX PRODUKTIV

Das ursprüngliche Problem waren:

```text
[sh] <defunct>
```

unterhalb des Observers.

Beispielsweise:

```text
15851 13992 root Z [sh] <defunct>

15853 13992 root Z [sh] <defunct>
```

und später weitere.

---

## 10. URSACHE DER ZOMBIES

Der alte getData() verwendete mehrfach:

```text
os.popen(...).readline().strip()
```

os.popen() verwendet intern eine Shell bzw. subprocess.Popen(..., shell=True).

Es gab keine erkennbare eigene Child-Reaping-Logik:

- kein waitpid()
- kein explizites wait()
- keine erkennbare SIGCHLD-Reaping-Logik

Die Python-3.9-Implementierung von subprocess.Popen.__del__() wurde ebenfalls untersucht.

Die Zombie-Erzeugung war reproduzierbar.

---

## 11. POPENS-FIX

Alle sieben externen Abfragen wurden von os.popen() auf subprocess.run() umgestellt.

Betroffene Abfragen:

1. Temp101
2. Hum101
3. Temp102
4. Hum102
5. LED102
6. freezer.log
7. CPU-Temperatur

Aktuelles Prinzip:

```text
subprocess.run(
    cmd,
    shell=True,
    capture_output=True,
    text=True
).stdout.strip()
```

Kontrolle:

os.popen-Aufrufe: keine

Syntaxprüfung:

python3 -m py_compile ...

Exit-Code: 0

**Status: produktiv.**

---

## 12. ZOMBIE-VALIDIERUNG NACH FIX

Nach dem kontrollierten Neustart:

alter Observer:

PID 13992

verschwand.

Neuer Observer:

PID 13821

PPID 1

Seit dem Produktivwechsel:

neue [sh] <defunct>: 0

Auch die globale Suche nach sh-Zombies war leer.

Beobachtungsdauer:

**mindestens ~48–50 Minuten.**

Der Fix gilt damit als **überzeugend bestätigt**, aber nicht als mathematisch bewiesen für jede denkbare Fehlerbedingung.

---

## 13. MESSDATEN – 8 FIELDS

Der aktuelle Observer erzeugt acht Messwerte:

| ThingSpeak Field | Bedeutung |
|---:|---|
| 1 | Temp101 |
| 2 | Hum101 |
| 3 | Temp102 |
| 4 | Hum102 |
| 5 | CPU-Temperatur |
| 6 | CPU-Auslastung |
| 7 | Freezer-Wert, negativ gespeichert |
| 8 | LED102 |

---

## 14. UPDATE-/POSTING-INTERVALLE

Produktive Werte:

```text
posting_interval = 900 s
update_interval  = 900 s
```

also:

**15 Minuten.**

Widersprüchliche Kommentare im Quelltext wie:

- 15 seconds
- 2 minutes

sind Dokumentationsfehler.

Die tatsächlich ausgeführten Werte sind 900 Sekunden.

---

## 15. DATENERFASSUNG – AKTUELL

Der Observer führt sieben externe Abfragen aus:

1. curl → Sensor 101 Temperatur
2. curl → Sensor 101 Feuchte
3. curl → Sensor 102 Temperatur
4. curl → Sensor 102 Feuchte
5. curl → Sensor 102 LED
6. sed → letzte freezer.log-Zeile
7. vcgencmd → CPU-Temperatur

Die Aufrufe erfolgen seriell.

Bei einem 15-Minuten-Zyklus ist das aktuell keine relevante CPU-Belastung.

---

## 16. SENSOR 101

Erreichbar.

Typische Werte:

Temperatur ≈ 23–24 °C

Feuchte ≈ 60 %

Beispiel:

```text
Temp1Read: 23.985
HumRead:   60.468
```

**Status: OK.**

---

## 17. SENSOR 102

Erreichbar.

Beispiel:

```text
Temp1Read: 23.112
HumRead:   63.543
```

LED-Abfrage:

```text
LightLED: 0
```

**Status: OK.**

---

## 18. FREEZER – WICHTIGSTE ARCHITEKTURERKENNTNIS

Der LoggerPi bzw. observer.py besitzt **keine direkte serielle Erfassung des Freezers**.

Die tatsächliche Kette ist:

```text
Freezer-Sensor

      │

      ▼

USB-Serial-Adapter

      │

      ▼

/dev/ttyUSB0

      │

      ▼

minicom

      │

      ▼

freezer.log

      │

      ▼

observer.py

      │

      ▼

ThingSpeak field 7
```

Der Observer **konsumiert lediglich den zuletzt von Minicom geschriebenen Wert**.

Das ist für die zukünftige Otter-Architektur ausdrücklich zu berücksichtigen.

---

## 19. MINICOM

Konfiguration:

`/dev/ttyUSB0`

1200 baud

2 stopbits

Minicom-Prozess:

PID 1342

PPID 1239

USER ZOOLOGY-observ

STAT Ss+

Startzeit:

13.08.2026 03:30:44

Command:

`minicom -C /home/ZOOLOGY-observ/Programs/freezer.log`

---

## 20. MINICOM-PROZESSKETTE

Aktuell:

PID 1239

lxterminal

    │

    └── PID 1342

        minicom

Ausgabe:

```text
ZOOLOGY+ 1239 1    lxterminal -e minicom -C ...
ZOOLOGY+ 1342 1239 minicom -C ...
```

lxterminal läuft unter dem Benutzer ZOOLOGY-observ.

---

## 21. MINICOM OPEN FILE DESCRIPTORS

Bei minicom:

```text
fd 0 → /dev/pts/0
fd 1 → /dev/pts/0
fd 2 → /dev/pts/0
fd 3 → /home/ZOOLOGY-observ/Programs/freezer.log
fd 4 → /dev/ttyUSB0
```

Damit ist die Funktion eindeutig:

```text
/dev/ttyUSB0

      │

      ▼

   minicom

      │

      └── fd 3 → freezer.log
```

---

## 22. MINICOM-AUTOSTART

Die Suche ergab keinen Minicom-Eintrag in:

- /etc/rc.local
- systemd services
- /etc/cron.d
- /etc/crontab

Gefunden wurde:

`/home/ZOOLOGY-observ/.config/autostart/TerminalAutostart.desktop`

mit:

```text
Exec=lxterminal -e 'minicom -C /home/ZOOLOGY-observ/Programs/freezer.log'
```

Damit ist der unmittelbare Startmechanismus von Minicom dokumentiert:

**Desktop-Autostart des Benutzers ZOOLOGY-observ.**

---

## 23. TÄGLICHER REBOOT

Root-Crontab:

```text
30 3 * * * sudo reboot
```

Damit erfolgt täglich um:

**03:30 Uhr**

ein Reboot.

`/etc/crontab` enthält keinen zusätzlichen Reboot-Eintrag.

Auch `/etc/cron.d` sowie die Standard-Cron-Verzeichnisse enthielten keinen weiteren entsprechenden Eintrag.

---

## 24. ZEITLICHE REIHENFOLGE DES FREEZER-SYSTEMS

Die Architektur erklärt damit die beobachtete zeitliche Abfolge.

```text
**Monatlich**

01. des Monats 03:28

↓

backup_log.sh

↓

├── freezer.log → freezer_backup_DDMMYY.log

└── neue freezer.log

**Täglich**

03:30

↓

root cron

↓

sudo reboot

↓

Boot

↓

Desktop-Session

↓

TerminalAutostart.desktop

↓

lxterminal

↓

minicom

↓

/dev/ttyUSB0 → freezer.log
```

Damit ist die interessante Sequenz:

**03:28 Backup → 03:30 Reboot → Minicom startet → neue freezer.log wird beschrieben**

technisch nachvollziehbar.

---

## 25. FREEZER.LOG

Aktuelle Datei:

`/home/ZOOLOGY-observ/Programs/freezer.log`

Aktueller Inode:

259966

Owner:

`ZOOLOGY-observ:ZOOLOGY-observ`

Permissions:

0644

Zuletzt dokumentierter Stand:

```text
Size:   5562 bytes
Modify: 2026-08-13 23:39:32 +0200
```

Beispiel letzte Werte:

-80 C

-80 C

-82 C

-80 C

-79 C

-82 C

-80 C

-79 C

-82 C

**Status: aktiv fortgeschrieben.**

---

## 26. FREEZER.BACKUP

August-Backup:

`/home/ZOOLOGY-observ/Programs/freezer_backup_010826.log`

Inode:

263807

Größe:

13392 bytes

Letzte Änderung:

2026-08-01 02:38:35 +0200

Letzte Werte enthalten ebenfalls Freezer-Messwerte:

-82 C

-81 C

-80 C

-79 C

-82 C

-80 C

-79 C

-82 C

-80 C

---

## 27. WICHTIGE INODE-ERKENNTNIS

freezer.log und die Backup-Datei sind unterschiedliche Dateien.

Das aktuelle:

`freezer.log`

Inode 259966

ist seit dem August-Backup dieselbe aktuelle Datei.

Der Backup-Vorgang verschiebt die alte Datei und erzeugt eine neue freezer.log.

Minicom öffnet nach dem Boot die aktuelle Datei.

---

## 28. BACKUP-SCRIPT

Datei:

`/home/ZOOLOGY-observ/Programs/backup_log.sh`

Inhalt:

```text
#!/bin/bash

# backup and empty freezer.log

date="$(date +"%d%m%y")"

mv /home/ZOOLOGY-observ/Programs/freezer.log \
   /home/ZOOLOGY-observ/Programs/freezer_backup_$date.log

touch /home/ZOOLOGY-observ/Programs/freezer.log
```

Cron des Benutzers ZOOLOGY-observ:

```text
28 3 1 * * /home/ZOOLOGY-observ/Programs/backup_log.sh
```

---

## 29. BACKUP-HISTORIE

Vorhandene Dateien:

```text
freezer_backup_01062026.log   478 KB
freezer_backup_010626.log      91 B
freezer_backup_010726.log      13 KB
freezer_backup_010826.log      13 KB
freezer.log                     5.5 KB
```

Die Namenshistorie zeigt außerdem eine ältere Inkonsistenz:

01062026

010626

Das ist historische Altlast und derzeit kein Funktionsproblem.

---

## 30. FREEZER-DATENVERARBEITUNG IM OBSERVER

Der Observer liest:

```text
sed 'x;$!d' < /home/ZOOLOGY-observ/Programs/freezer.log
```

also die letzte Zeile.

Der Wert wird anschließend entsprechend verarbeitet und als negativer Freezer-Wert in Field 7 gespeichert.

Wichtig:

**Observer schreibt nicht in freezer.log.**

---

## 31. THINGSPEAK

Produktiver Endpoint:

`https://api.thingspeak.com/channels/2068639/bulk_update.json`

ThingSpeak erhält aktuell die acht Messfelder.

API-Key wurde bei der Diagnose nicht ausgegeben.

Bei zukünftigen Diagnosen:

**API-Key niemals im Klartext ausgeben.**

Nur maskiert, falls zwingend erforderlich.

---

## 32. NETZWERK

Aktueller LoggerPi:

eth0 UP

LOWER_UP

Adresse:

141.51.190.103/24

Gateway:

141.51.190.1

wlan0:

DOWN

Fehlerzähler zuletzt:

```text
RX errors    0
RX dropped   0
RX missed    0
TX errors    0
TX dropped   0
carrier      0
collisions   0
```

---

## 33. MESH CENTRAL

Zugriff auf den LoggerPi erfolgt über MeshCentral.

MeshAgent:

PID 535

Dienst:

`meshagent.service`

Active: active (running)

Verbindung:

`wss://mesh.makki.route64.de:443/agent.ashx`

Gateway:

141.51.190.1

Gateway-Test:

0 % packet loss

≈ 0.65 ms

HTTPS zum Mesh-Server:

HTTP 200

connect ≈ 0.027 s

total ≈ 0.531 s

Der zwischenzeitliche MeshCentral-Disconnect wurde als unkritisch bewertet.

---

## 34. SYSTEMZEIT

LoggerPi:

`Europe/Berlin`

CEST (+0200)

NTP:

active

synchronized

Auch der OtterPi wurde bezüglich Zeit/NTP kontrolliert.

Kein tatsächliches Uhrzeitproblem festgestellt.

---

## 35. PROZESS-/SPEICHERSTATUS

Observer zuletzt:

RSS ≈ 18.5 MB

VSZ ≈ 26.5 MB

Threads = 1

Context switches:

voluntary ≈ 1322

nonvoluntary ≈ 17

Kein Hinweis auf Memory Leak oder ungewöhnliche Thread-Erzeugung.

---

## 36. BEWUSST NICHT VERÄNDERT

Folgende Komponenten wurden bei der bisherigen Fehlerbehebung nicht verändert:

- Minicom
- serielle Logging-Kette
- freezer.log
- backup_log.sh
- Cron
- ThingSpeak-Konfiguration
- API-Key
- Sensor-IP-Adressen
- rc.local
- MeshAgent
- Netzwerk
- GPIO
- USB/serielles Device
- Update-Intervalle

Damit sind die beiden bisherigen Fixes gut isoliert.

---

## 37. OFFENE TECHNISCHE ALTlastEN DES ALTEN OBSERVERS

Diese Punkte sind bekannt, aber **bewusst nicht mehr prioritär**, sofern die Migration auf einen neuen Observer beschlossen wird.

### A. shell=True

Aktuell weiterhin verwendet.

Technisch könnte man externe Kommandos direkt ohne Shell ausführen.

**Nicht ändern, solange der Migrationsplan nicht entschieden ist.**

### B. Fehlende Timeouts

Insbesondere curl besitzt nicht überall explizite Timeouts.

Ein hängender Request könnte getData() blockieren.

### C. Returncodes

subprocess.run() wird derzeit nicht konsequent auf Fehler geprüft.

### D. Parser-Robustheit

Bestimmte Ausgaben werden direkt mit String-Operationen zerlegt.

### E. Exception Handling

Im Code ist weiterhin die historische Problematik:

```text
except e:
```

Korrekt wäre beispielsweise:

```text
except Exception as e:
```

### F. CPU-Messung

`psutil.cpu_percent(interval=2)`

blockiert bewusst zwei Sekunden.

### G. Kommentare

Kommentare und tatsächliche Intervalle stimmen teilweise nicht überein.

---

## 38. WARUM DIESE ALTLASTEN VORERST NICHT BEHOBEN WERDEN SOLLEN

Der alte Observer ist aktuell:

- produktiv
- CPU-seitig stabil
- zombie-seitig stabil
- sensorseitig funktionierend
- Freezer-seitig funktionierend
- ThingSpeak-seitig funktionierend

Eine umfassende Modernisierung würde deshalb ein unnötiges Änderungsrisiko erzeugen, **wenn ohnehin ein neuer Observer geplant ist**.

Der aktuelle Observer soll daher zunächst als:

**stabiler Legacy-Produktivstand**

behandelt werden.

---

## 39. MIGRATIONSSTRATEGIE – VORLÄUFIG

Die bevorzugte zukünftige Strategie ist nicht eine weitere umfangreiche Reparatur des alten Observers.

Stattdessen:

```text
ALTER OBSERVER

      │

      │ bleibt zunächst unverändert

      ▼

STABILER PRODUKTIVBETRIEB


parallel


NEUER OBSERVER

      │

      ▼

sauber neu aufgebaut

      │

      ▼

parallel testen

      │

      ▼

temporärer ThingSpeak-Batch

      │

      ▼

OtterPi als neues Datenziel

      │

      ▼

alter Observer abschalten

      │

      ▼

neuen Observer stabilisieren

      │

      ▼

temporären ThingSpeak-Upload entfernen
```

---

## 40. WICHTIG: NEUER OBSERVER LÄUFT AUF DEM LOGGERPI

Der neue Observer soll **nicht** auf dem OtterPi laufen.

Er soll perspektivisch den alten:

`/home/ZOOLOGY-observ/Programs/observer.py`

auf dem **LoggerPi / Hostname observer** ersetzen.

Der OtterPi bleibt das nachgelagerte Serversystem.

---

## 41. MIGRATIONSZIEL

Langfristig:

```text
                  LOGGERPI

                  observer

                     │

                     │ Messdaten

                     ▼

                   OtterPi

                     │

          ┌──────────┼──────────┐
          ▼          ▼          ▼

      speichern  visualisieren  API/
                              weitere Dienste
```

ThingSpeak ist dann optional bzw. nur noch Legacy/Export.

---

## 42. EMPFOHLENE MIGRATIONSPHASEN

### Phase 1

Neuen Observer konzipieren.

**Noch keine Änderung am alten Observer.**

### Phase 2

Neuen Observer auf dem LoggerPi implementieren.

Lokale Tests.

### Phase 3

Parallelbetrieb.

Alter Observer bleibt produktiv.

Neuer Observer sammelt und vergleicht.

### Phase 4

Temporärer Batch-Upload nach ThingSpeak.

Damit kann die neue Software den bisherigen Datenpfad kontrolliert übernehmen.

### Phase 5

OtterPi übernimmt zuverlässig.

### Phase 6

Alter observer.py wird deaktiviert, aber archiviert.

### Phase 7

Mehrere Tage/Wochen stabiler Betrieb des neuen Systems.

### Phase 8

Temporären ThingSpeak-Upload aus dem neuen Observer entfernen, sofern nicht mehr benötigt.

---

## 43. WICHTIGE MIGRATIONSPRINZIPIEN

1. **Alter Observer bleibt zunächst unangetastet.**
2. **Kein Big-Bang-Rewrite im Produktivsystem.**
3. Jede Änderung einzeln testen.
4. Vor jeder produktiven Änderung Backup erstellen.
5. Neue Software zunächst parallel testen.
6. Messwerte des alten und neuen Systems vergleichen.
7. API-Keys niemals unmaskiert ausgeben.
8. ThingSpeak während der Übergangsphase nur bewusst als Kompatibilitätsschicht verwenden.
9. Nach erfolgreicher Migration alten Observer archivieren, nicht löschen.
10. Erst danach Altlasten entfernen.

---

## 44. EXPLORATION STATUS

Die Bestandsaufnahme des LoggerPi wurde hinsichtlich der bisher relevanten Bereiche abgeschlossen.

Untersucht und dokumentiert wurden insbesondere:

- Hardware
- OS
- Python
- Observer-Prozess
- Startmechanismus
- CPU-Busy-Loop
- CPU-Thermik
- Zombie-Prozesse
- os.popen()
- subprocess.run()
- Sensor 101
- Sensor 102
- LED102
- Freezer-Datenkette
- USB-Serial
- /dev/ttyUSB0
- Minicom
- Minicom-FDs
- Minicom-Autostart
- freezer.log
- Backup-Dateien
- Inodes
- Backup-Cron
- täglicher Reboot
- Cron-Konfiguration
- ThingSpeak
- Netzwerk
- MeshAgent
- NTP/Systemzeit
- Prozess-/Speicherzustand
- aktuelle Versionsstände

**Exploration abgeschlossen.**

---

## 45. REFERENZSTATUS V4

Der aktuelle LoggerPi-Zustand wird ab jetzt als:

# **OBSERVER v4 – FROZEN TECHNICAL BASELINE**

behandelt.

Das bedeutet:

**Nicht erneut explorieren, was bereits dokumentiert ist.**

Bei der nächsten Sitzung kann direkt mit der nächsten Entwicklungsphase begonnen werden.

---

## 46. AKTUELLER GESAMTSTATUS

| Bereich | Status |
|---|---|
| LoggerPi | ✅ stabil |
| alter Observer | ✅ produktiv |
| Autostart | ✅ |
| CPU-Busy-Loop | ✅ behoben |
| CPU-Last | ✅ ~0 % |
| CPU-Temperatur | ✅ ~49–50 °C |
| os.popen() | ✅ entfernt |
| neue Zombie-Shells | ✅ bislang keine |
| Sensor 101 | ✅ |
| Sensor 102 | ✅ |
| LED102 | ✅ |
| Freezer.log | ✅ aktiv |
| Minicom | ✅ aktiv |
| /dev/ttyUSB0 | ✅ |
| Minicom-Autostart | ✅ bekannt |
| Freezer-Backup | ✅ |
| täglicher Reboot | ✅ bekannt |
| ThingSpeak | ✅ |
| Netzwerk | ✅ |
| MeshAgent | ✅ |
| NTP | ✅ |
| Syntax | ✅ |
| Versionskette | ✅ dokumentiert |
| Exploration | **✅ abgeschlossen** |
| neue Observer-Architektur | 🟡 nächster Entwicklungsschritt |
| OtterPi-Anbindung | 🟡 geplant |
| Migration | 🟡 geplant |

---

## 47. NÄCHSTER SCHRITT

**Nicht mehr am alten observer.py feintunen.**

Stattdessen zunächst **die Architektur des neuen Observers auf dem LoggerPi entwerfen**.

Dabei sollten wir vor dem ersten Code insbesondere festlegen:

1. Datenquellen
2. Messzyklus
3. Datenmodell
4. lokale Fehler-/Ausfallstrategie
5. Freezer-Anbindung
6. Health-Daten
7. Kommunikation LoggerPi → OtterPi
8. temporärer ThingSpeak-Batch
9. Parallelbetrieb
10. Umschaltkriterium
11. Rückfallstrategie
12. endgültige Entfernung der ThingSpeak-Kompatibilität

**Bis dahin bleibt observer.py v4 unverändert produktiv.**

---

# ENDE – OBSERVER TECHNICAL BASELINE v4

**Dokumentstatus:** Referenzstand / eingefroren  
**Exploration:** abgeschlossen  
**Produktivsystem:** nicht weiter verändern, außer ausdrücklich beschlossen  
**Nächster Arbeitsbereich:** Design des neuen Observers auf dem **LoggerPi** und seiner zukünftigen Kommunikation mit dem **OtterPi**.
