# Research: MEMMERT IPP300 – Kommunikationsschnittstellen

## Status

**Stand:** 2026-08-30  
**Gerät:** MEMMERT IPP300  
**Kommunikation:** je nach Ausstattung RS-232, RS-485, USB oder Ethernet  
**Software:** CELSIUS 10.0 / ältere Geräte ggf. CELSIUS 2005  
**USB-Modul:** MEMMERT USB Interface Module B04118  
**Ziel:** Prüfen, ob die beiden vorhandenen IPP300 direkt in LoggerPi-OtterPi integriert werden können.

---

## 1. Vorhandene Ausstattung

Bei den vorhandenen IPP300 ist offenbar ein älteres **USB-Interface-Modul B04118** verbaut.

Physisch handelt es sich um eine ältere USB-A-Buchse am Gerät. Zusätzlich scheint bei den Geräten ein paralleler Druckeranschluss vorhanden zu sein.

Aus dem CELSIUS-Handbuch ergibt sich, dass MEMMERT-Geräte je nach Ausstattung unterschiedliche Kommunikationsschnittstellen besitzen können:

- RS-232
- RS-485
- USB
- Ethernet/LAN

Die konkrete USB-Hardware der beiden vorhandenen IPP300 muss noch direkt am Gerät bzw. unter Linux untersucht werden.

---

## 2. CELSIUS unterstützt PC-Kommunikation

CELSIUS ist laut Handbuch das PC-Programm zur:

- Programmierung
- Steuerung
- Protokollierung

von MEMMERT-Schränken.

Unterstützt werden Geräte mit:

- RS-232
- RS-485
- USB
- Ethernet

CELSIUS kann aktuelle Messwerte protokollieren und den internen Ringprotokollspeicher des Gerätes auslesen.

Damit ist grundsätzlich klar, dass über die jeweilige Kommunikationsschnittstelle nicht nur Konfiguration, sondern auch Messdaten zugänglich sind.

---

## 3. USB-Anbindung

Das CELSIUS-Handbuch beschreibt USB ausdrücklich als direkte Kommunikationsschnittstelle zum Schrank.

Bei einer USB-Verbindung werden Geräte in CELSIUS als:

- USB 1
- USB 2
- ...
- USB 16

angezeigt.

CELSIUS ermittelt laut Handbuch die Konfiguration online angeschlossener Schränke selbstständig.

Das ist für LoggerPi interessant, weil der physische USB-Port damit nicht zwangsläufig die Geräteidentität darstellen muss.

---

## 4. Geräteadresse

Laut IPP300-Handbuch befindet sich die Kommunikationsadresse im SETUP-Menü unter:

`ADDRESS`

Wertebereich:

`0 ... 15`

Werkseitiger Standardwert:

`0`

Die Adresse wird vom PC verwendet, um einen bestimmten Schrank anzusprechen.

Bei mehreren Geräten müssen unterschiedliche Geräteadressen vergeben werden.

Damit könnte die MEMMERT-Geräteadresse eine stabile logische Identität liefern, unabhängig davon, an welchem USB-Port das Gerät angeschlossen ist.

---

## 5. RS-232 als Referenz

Das IPP300-Handbuch beschreibt eine standardmäßige RS-232C-Schnittstelle.

Pinbelegung:

| Pin | Funktion |
|---:|---|
| 1 | nicht belegt |
| 2 | RxD |
| 3 | TxD |
| 4 | nicht belegt |
| 5 | GND |
| 6 | nicht belegt |
| 7 | nicht belegt |
| 8 | nicht belegt |
| 9 | nicht belegt |

Das vorgesehene Kabel ist ein gedrehtes RS-232-Kabel nach DIN 12900 Teil 1.

MEMMERT bezeichnet ein entsprechendes Kabel als:

`V6`

Besonders interessant:

> Die Protokollbeschreibung der Schnittstelle (nach NAMUR) kann beim MEMMERT-Kundendienst angefordert werden.

Das deutet auf ein dokumentiertes MEMMERT/NAMUR-Kommunikationsprotokoll hin.

---

## 6. RS-485

Bei entsprechender Ausstattung kann statt RS-232 eine RS-485-Schnittstelle vorhanden sein.

Damit können mehrere Geräte über einen gemeinsamen Bus verbunden werden.

Das IPP300-Handbuch nennt:

- 2-Draht-Bus
- Geräteadresse 0 ... 15
- maximal 16 adressierbare Geräte
- 150 m maximale Gesamtkabellänge
- 220-Ohm-Abschlusswiderstand am letzten Gerät

Die genaue maximale Geräteanzahl unterscheidet sich teilweise zwischen älteren MEMMERT/CELSIUS-Dokumentationen. Für LoggerPi ist daher zunächst die konkrete Hardware entscheidend.

---

## 7. Ethernet/LAN

CELSIUS unterstützt ebenfalls Geräte mit Ethernet-Schnittstelle.

Laut CELSIUS-Handbuch:

- jeder Schrank benötigt eine eindeutige IP- bzw. DNS-Adresse
- ältere Geräte können standardmäßig `192.168.100.100` verwenden
- die IP-Adresse kann mit `XTADMIN` geändert werden
- anschließend wird die IP-Adresse in CELSIUS eingetragen

In CELSIUS können bis zu 16 Geräte über LAN verwaltet werden.

Für die beiden vorhandenen IPP300 ist momentan nicht bekannt, ob Ethernet-Hardware vorhanden ist.

---

## 8. CELSIUS-Konfiguration

Aus der gefundenen CELSIUS-Konfigurationsdatei:

```ini
DelayInMilliseconds = 10
PollIntervall=30
```

CELSIUS wartet demnach 10 ms zwischen dem Senden eines Kommandos und dem Lesen der Antwort.

Der Polling-Intervall beträgt standardmäßig 30 Sekunden.

Die Beschreibung zu `PollIntervall` sagt sinngemäß, dass nach Ablauf dieses Intervalls alle aktiven Geräte erneut nach ihren Werten abgefragt werden.

Das ist ein deutlicher Hinweis auf einen Request/Response-Mechanismus.

---

## 9. Gerätestatus

Die CELSIUS-Gerätestatuszeile zeigt beispielsweise:

```text
Regler aktiv COM3 IST: 24.1 °C 40.1 °C 0:02h
```

Dabei werden unter anderem angezeigt:

1. Reglerstatus
2. verwendete COM-Schnittstelle
3. Ist-Temperatur
4. weitere physikalische Eigenschaft bzw. Profilwert
5. Laufzeit

Die Kommunikation wird damit von CELSIUS einer konkreten Schnittstelle zugeordnet.

---

## 10. Möglicher USB-Aufbau

Es wurde ein Prolific-USB-Seriell-Treiber gefunden.

Der Treiber unterstützt beispielsweise:

```text
VID_067B&PID_2303
"Prolific USB-to-Serial Comm Port"
```

sowie:

```text
VID_067B&PID_2304
"Prolific USB-to-Serial Comm Port"
```

Das macht einen **PL2303 USB-to-Serial-Chip** im USB-Interface zumindest plausibel.

Ein möglicher Aufbau wäre:

```text
MEMMERT IPP300
    │
    │ USB
    ▼
USB-Interface-Modul B04118
    │
    │ USB-Serial / PL2303 ?
    ▼
virtueller COM-Port
    │
    ▼
CELSIUS / unser Serial Reader
```

Das ist derzeit eine Arbeitshypothese und muss am tatsächlichen Gerät verifiziert werden.

---

## 11. PL2303-Erkennung

Der gefundene Prolific-Treiber enthält ein eigenes CheckChipVersion-Tool.

Unterstützte Chips umfassen unter anderem:

- PL2303HXA
- PL2303XA
- PL2303HXD
- PL2303EA
- PL2303RA
- PL2303SA
- PL2303TA
- PL2303TB

Das Tool kann unter Windows anhand des COM-Ports die verwendete PL2303-Chipversion erkennen.

Für unsere Untersuchung ist zunächst aber wichtiger, wie das **komplette MEMMERT-USB-Gerät** enumeriert wird.

Interessant sind:

- USB Vendor ID (VID)
- USB Product ID (PID)
- Manufacturer
- Product
- Serial Number
- USB Interface Class
- Interface/Subclass/Protocol
- erzeugtes `/dev/tty*`-Device

---

## 12. USB-Portabhängigkeit

Wenn das MEMMERT-USB-Modul tatsächlich als USB-zu-Seriell-Gerät arbeitet, sollte der physische USB-Port **nicht als Geräteidentität verwendet werden**.

Unter Linux können sich beispielsweise `/dev/ttyUSB0` und `/dev/ttyUSB1` abhängig von Enumeration und Anschlussreihenfolge ändern.

Nicht ideal:

```text
/dev/ttyUSB0 = IPP300-1
/dev/ttyUSB1 = IPP300-2
```

Besser wäre eine Identifikation über stabile Eigenschaften, beispielsweise:

```text
USB VID/PID
+
USB-Seriennummer (falls vorhanden)
+
MEMMERT-Geräteadresse
```

Idealerweise wird die Geräteadresse zusätzlich über das MEMMERT-Protokoll verifiziert.

Beispiel:

```text
USB-Gerät A
    -> MEMMERT
    -> Adresse 3
    -> IPP300
```

und:

```text
USB-Gerät B
    -> MEMMERT
    -> Adresse 7
    -> IPP300
```

Damit wäre die Identität unabhängig vom physischen USB-Port.

---

## 13. Proprietäres USB wäre kein Ausschlusskriterium

Falls sich herausstellt, dass das USB-Modul **nicht** als klassischer USB-Seriell-Adapter erscheint, sondern als `vendor-specific USB device`, wäre die Situation aufwendiger.

Dann müsste zunächst untersucht werden:

- USB Descriptors
- VID/PID
- Interfaces
- Endpoints
- Transferarten
- Kommunikation zwischen CELSIUS und Gerät

Anschließend könnte der Datenverkehr zwischen CELSIUS und IPP300 analysiert werden.

Da CELSIUS das Gerät aktiv abfragt und Messwerte protokollieren kann, wäre grundsätzlich eine Protokollanalyse bzw. Reverse Engineering denkbar.

Das wäre aber erst notwendig, wenn die USB-Hardware tatsächlich kein serielles Interface bereitstellt.

---

## 14. Polling-Modell

Die CELSIUS-Konfiguration enthält:

```ini
DelayInMilliseconds = 10
PollIntervall=30
```

Die Beschreibung von `PollIntervall` macht deutlich, dass CELSIUS aktive Geräte regelmäßig nach ihren Werten fragt.

Vermutetes Modell:

```text
CELSIUS
   │
   │ Anfrage
   ▼
MEMMERT
   │
   │ Antwort
   ▼
CELSIUS
```

Das unterscheidet sich konzeptionell vom derzeit vorhandenen Freezer.

---

## 15. Vergleich mit dem vorhandenen Freezer

Der vorhandene Thermo Scientific HFC -80 °C Freezer funktioniert aktuell über:

```text
RS-232
   │
   ▼
RS-232 → USB Adapter
   │
   ▼
minicom
```

Der Freezer sendet derzeit selbstständig ungefähr alle 60 Minuten eine Meldung, die bereits sauber empfangen werden kann.

Das ist konzeptionell etwas anderes als die MEMMERT-Kommunikation, falls CELSIUS tatsächlich aktiv pollt.

Daraus ergibt sich für LoggerPi voraussichtlich die Möglichkeit, unterschiedliche Adaptertypen zu unterstützen:

```text
Serial Reader
├── passive/streaming devices
│   └── z.B. vorhandener Freezer
│
└── request/response devices
    └── MEMMERT IPP300
```

---

## 16. Bezug zu den bereits vorhandenen MEMMERT-Geräten

Im bestehenden LoggerPi-/Observer-System werden bereits zwei andere MEMMERT-Geräte über Ethernet angesprochen.

Dort wird die MEMMERT-/AtmoControl-API verwendet.

Das ist zunächst von den beiden IPP300 getrennt zu betrachten.

Interessant bleibt jedoch die Frage, ob die IPP300 möglicherweise ebenfalls über eine kompatible MEMMERT-Kommunikationsschicht bzw. AtmoControl/API erreichbar sind.

Dafür gibt es momentan **keinen belastbaren Nachweis**.

Die CELSIUS-Dokumentation zeigt dagegen eindeutig, dass die IPP300 über ihre Kommunikationsschnittstelle abgefragt werden können.

---

## 17. Arbeitshypothesen

### Hypothese A – USB ist USB-Serial

```text
IPP300
  ↓
USB interface module
  ↓
PL2303 oder ähnlicher USB-Serial-Chip
  ↓
/dev/ttyUSBx
  ↓
MEMMERT-Protokoll
```

Das wäre der günstigste Fall.

Dann könnten wir wahrscheinlich direkt einen MEMMERT-Serial-Reader implementieren.

### Hypothese B – proprietäres USB

```text
IPP300
  ↓
USB interface module
  ↓
vendor-specific USB device
  ↓
MEMMERT USB-Protokoll
```

Dann wäre zunächst USB-Protokollanalyse notwendig.

### Hypothese C – USB-Modul stellt intern weiterhin eine serielle Schnittstelle bereit

Auch wenn das Modul auf USB-Seite speziell aussieht, könnte es intern das MEMMERT-Protokoll über eine abstrahierte serielle Verbindung bereitstellen.

Diese Variante muss durch die tatsächliche Enumeration und ggf. CELSIUS-Kommunikation geprüft werden.

---

## 18. Nächster Untersuchungsschritt

Noch **keine Implementierung notwendig**.

Zunächst einen der beiden IPP300 an einen Linux-Rechner anschließen.

Dann:

```bash
lsusb
```

anschließend:

```bash
lsusb -v
```

und:

```bash
dmesg | tail -n 50
```

Zusätzlich:

```bash
ls -l /dev/ttyUSB*
ls -l /dev/ttyACM*
```

Falls ein serielles Gerät auftaucht:

```bash
udevadm info -a -n /dev/ttyUSB0
```

bzw. das tatsächlich erzeugte Device.

Damit lässt sich feststellen, ob das USB-Modul als klassischer USB-Seriell-Adapter erkannt wird.

---

## 19. Wenn ein serieller Port gefunden wird

Dann wäre der nächste Schritt zunächst **passives Beobachten**, nicht Reverse Engineering.

Beispielsweise mit:

```bash
minicom
```

oder einem kleinen Python-Programm, das den seriellen Datenverkehr aufzeichnet.

Zu bestimmen sind:

- Baudrate
- Datenbits
- Parität
- Stopbits
- Flow Control
- ob spontan Daten kommen
- ob das Gerät nur auf Requests antwortet

Die CELSIUS-Konfiguration liefert bereits einen Hinweis auf eine Response-Verzögerung von 10 ms und einen Polling-Intervall von 30 Sekunden.

---

## 20. Relevanz für die LoggerPi-Architektur

Die Geräteidentität sollte nicht an einem zufälligen Linux-Port hängen.

Nicht:

```text
/dev/ttyUSB0 = IPP300-1
/dev/ttyUSB1 = IPP300-2
```

sondern eher:

```text
MEMMERT device identity
    ↓
Geräteadresse / USB-Identität
    ↓
stabile LoggerPi device_id
```

Der konkrete Transport kann dann austauschbar sein:

```text
MEMMERT IPP300
├── serial transport
├── USB transport
└── LAN transport
```

Das passt grundsätzlich gut zu einer Adapterarchitektur.

---

## 21. Vorläufiges Fazit

Die bisherigen Informationen sind sehr vielversprechend.

Besonders wichtig:

1. Die IPP300 besitzen eine dokumentierte PC-Kommunikationsschnittstelle.
2. CELSIUS kann die IPP300 online anbinden und aktuelle Werte protokollieren.
3. USB wird von CELSIUS ausdrücklich als Kommunikationsschnittstelle unterstützt.
4. Die Geräte besitzen eine eigene Kommunikationsadresse von 0–15.
5. Das MEMMERT-Protokoll ist laut Handbuch nach NAMUR beschrieben.
6. Die Kommunikation scheint bei CELSIUS aktiv per Polling zu erfolgen.
7. Ein gefundener Prolific-Treiber macht einen USB-zu-Seriell-Aufbau plausibel.
8. Falls tatsächlich ein PL2303 verwendet wird, wäre kein proprietäres USB-Reverse-Engineering erforderlich.
9. Selbst bei einem proprietären USB-Interface wäre eine Protokollanalyse grundsätzlich denkbar.
10. Für LoggerPi sollte die Geräteidentität nicht vom physischen USB-Port abhängen.

### Noch offen

- Welchen USB-Chip verwendet das konkrete B04118-Modul?
- Welche VID/PID meldet das Modul?
- Wird ein `/dev/ttyUSB*` oder `/dev/ttyACM*` erzeugt?
- Welche seriellen Parameter verwendet die IPP300-Kommunikation?
- Welche konkreten Requests/Responses verwendet das MEMMERT-Protokoll?
- Welche Messwerte können abgefragt werden?
- Wie wird die Geräteadresse im Protokoll übertragen?
- Welche Geräteadressen haben die beiden vorhandenen IPP300?
- Gibt es eine USB-Seriennummer?
- Ist das B04118 tatsächlich nur ein USB-Seriell-Adapter oder enthält es zusätzliche Logik?
- Ist die AtmoControl/API der bereits vorhandenen MEMMERT-Geräte auch für die IPP300 relevant?

Diese Punkte sollten zunächst empirisch am vorhandenen Gerät geklärt werden.
