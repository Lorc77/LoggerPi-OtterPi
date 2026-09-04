# Research: MEMMERT IPP300 – Kommunikationsschnittstellen

## Status

**Stand:** 2026-09-04  
**Gerät:** MEMMERT IPP300  
**Kommunikation:** interne RS-232-Kommunikation, über MEMMERT USB Interface B04118 auf USB umgesetzt  
**Protokoll:** MEMMERT-Schnittstellenprotokoll nach NAMUR  
**Software:** CELSIUS 10.0 / ältere Geräte ggf. CELSIUS 2005  
**USB-Modul:** MEMMERT USB Interface Module B04118  
**Ziel:** Prüfen, ob die beiden vorhandenen IPP300 direkt in LoggerPi-OtterPi integriert werden können.

### Aktueller Erkenntnisstand

Der MEMMERT-Service hat auf eine technische Anfrage bestätigt, dass der Controller des Gerätes intern über **RS-232** kommuniziert und das Interface **B04118 diese RS-232-Kommunikation auf USB umsetzt**.

Damit ist der grundsätzliche Kommunikationsweg geklärt:

```text
MEMMERT IPP300 Controller
        │
        │ RS-232
        ▼
MEMMERT USB Interface B04118
        │
        │ USB
        ▼
LoggerPi / Raspberry Pi
```

Zusätzlich wurde vom MEMMERT-Service eine offizielle Schnittstellenbeschreibung zur Verfügung gestellt:

```text
docs/research/sources/MEMMERT_IPP300_Beschreibung_RS232-2010.pdf
```

Die Dokumentation beschreibt die serielle Kommunikation einschließlich Übertragungsparametern, Befehlssyntax, Geräteadressierung, Status- und Fehlerantworten sowie Lese- und Schreibbefehlen.

Damit ist **kein Reverse Engineering des eigentlichen MEMMERT-Kommunikationsprotokolls erforderlich**.

Die verbleibende technische Untersuchung betrifft primär die konkrete USB-Enumeration des B04118 sowie die Verifikation der dokumentierten Kommunikation am real vorhandenen IPP300.

---

## 1. Vorhandene Ausstattung

Bei den vorhandenen IPP300 ist ein **MEMMERT USB Interface Module B04118** verbaut.

Physisch handelt es sich um eine ältere USB-A-Buchse am Gerät. Zusätzlich scheint bei den Geräten ein paralleler Druckeranschluss vorhanden zu sein.

Nach Auskunft des MEMMERT-Service kommuniziert der Controller des Gerätes intern über **RS-232**. Das B04118 übernimmt die Umsetzung dieser RS-232-Kommunikation auf USB.

Die Kommunikationskette ist damit bestätigt als:

```text
MEMMERT IPP300 Controller
        │
        │ RS-232
        ▼
B04118
        │
        │ USB
        ▼
Host / Raspberry Pi
```

Die konkrete USB-Implementierung des B04118 ist noch nicht untersucht. Insbesondere ist noch offen, welcher USB-Controller bzw. USB-Serial-Chip verwendet wird und wie sich das Interface unter Linux enumeriert.

Diese Frage betrifft jedoch nur die Transportebene. Das eigentliche MEMMERT-Kommunikationsprotokoll ist durch die vom Hersteller bereitgestellte Schnittstellendokumentation beschrieben.

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
- Ethernet/LAN

CELSIUS kann aktuelle Messwerte protokollieren und den internen Ringprotokollspeicher des Gerätes auslesen.

Damit ist grundsätzlich klar, dass über die jeweilige Kommunikationsschnittstelle nicht nur Konfiguration, sondern auch Messdaten zugänglich sind.

Für die IPP300 ist durch die vom Hersteller bereitgestellte RS-232-Schnittstellendokumentation inzwischen zusätzlich geklärt, wie die grundlegende Kommunikation auf Protokollebene funktioniert.

---

## 3. USB-Anbindung

Das CELSIUS-Handbuch beschreibt USB ausdrücklich als Kommunikationsschnittstelle zum Schrank.

Bei einer USB-Verbindung werden Geräte in CELSIUS als:

- USB 1
- USB 2
- ...
- USB 16

angezeigt.

CELSIUS ermittelt laut Handbuch die Konfiguration online angeschlossener Schränke selbstständig.

Das ist für LoggerPi interessant, weil der physische USB-Port damit nicht zwangsläufig die logische Geräteidentität darstellen muss.

Durch die Herstellerantwort ist außerdem geklärt, dass das MEMMERT USB Interface B04118 die interne RS-232-Kommunikation des Controllers auf USB umsetzt.

Die offene Frage ist daher nicht mehr, **welches Protokoll über USB verwendet werden muss**, sondern zunächst nur, **wie das B04118 unter Linux als USB-Gerät bzw. serielles Device erscheint**.

---

## 4. Geräteadresse

Das MEMMERT-Protokoll verwendet eine Geräteadresse innerhalb der Befehle.

Für P-Klasse-Regler muss jedem Gerät eine eindeutige Adresse zugeordnet werden.

Der dokumentierte Wertebereich ist:

```text
0 ... F
```

Damit sind 16 Adressen möglich:

```text
0, 1, 2, ... 9, A, B, C, D, E, F
```

Bei P-Klasse-Geräten wird die Adresse im SETUP-Menü konfiguriert.

Bei E-Klasse-Reglern ist die Adresse laut Hersteller nicht fest zugeordnet; der Regler antwortet auf gültige Adressen von `0 ... 9` und `A ... F`.

Wichtig:

> Wenn die Geräteadresse nicht stimmt, antwortet der Regler überhaupt nicht.

Für LoggerPi sollte die MEMMERT-Adresse deshalb als explizite Gerätekonfiguration behandelt werden.

Beispiel:

```yaml
memmert:
  address: 0
```

Die tatsächliche Adresse der beiden vorhandenen IPP300 muss am Gerät verifiziert werden.

Die MEMMERT-Geräteadresse kann damit zusätzlich zur USB-Identität als stabile logische Geräteidentifikation verwendet werden.

---

## 5. Offizielle MEMMERT-RS-232-Schnittstelle

Die vom MEMMERT-Service bereitgestellte Schnittstellendokumentation beschreibt die RS-232-Kommunikation der MEMMERT-Wärmeschränke mit E- oder P-Temperaturreglern.

### 5.1 Serielle Übertragungsparameter

Die Kommunikation verwendet:

| Parameter | Wert |
|---|---|
| Baudrate | 2400 Baud |
| Startbits | 1 |
| Datenbits | 8 |
| Parität | keine |
| Stopbits | 1 |
| Handshake | keiner |
| Übertragungsverfahren | Halbduplex |

Damit ergibt sich für die Implementierung:

```text
2400 8N1
kein Hardware-Handshake
kein Software-Handshake
Halbduplex
```

Diese Werte stammen direkt aus der vom MEMMERT-Service bereitgestellten Schnittstellenbeschreibung.

### 5.2 Elektrische Schnittstelle

Die originale RS-232-Schnittstelle des Gerätes verwendet eine 9-polige Buchse.

MEMMERT beschreibt den Anschluss eines PCs über ein Nullmodemkabel nach DIN 12900-1.

Die in der Herstellerdokumentation angegebene Belegung lautet:

| Pin | Signal | Beschreibung |
|---:|---|---|
| 1 | DCD | im Gerät mit DSR gebrückt |
| 2 | TxD | Sendeleitung |
| 3 | RxD | Empfangsleitung |
| 4 | DTR | nicht verwendet |
| 5 | GND | Masse |
| 6 | DSR | im Gerät mit DCD gebrückt |
| 7 | RTS | im Gerät mit CTS gebrückt |
| 8 | CTS | im Gerät mit RTS gebrückt |
| 9 | RI | nicht verwendet |

Für die LoggerPi-Implementierung ist insbesondere relevant, dass laut Hersteller **kein Handshake** verwendet wird.

### 5.3 Quelle

Quelle:

```text
docs/research/sources/MEMMERT_IPP300_Beschreibung_RS232-2010.pdf
```

Dokumenttitel:

**Schnittstellenbeschreibung für MEMMERT-Wärmeschränke mit Temperaturregler der E- oder P-Klasse**

Stand der Herstellerdokumentation: **April 2011**.

---

## 6. MEMMERT-Kommunikationsprotokoll

Die Datenübertragung erfolgt laut Herstellerdokumentation nach dem **NAMUR-Protokoll**.

Die Befehle bestehen aus ASCII-Text und werden mit `<CR><LF>` abgeschlossen.

### 6.1 Steuerzeichen

| Zeichen | ASCII hex | ASCII dez |
|---|---:|---:|
| `<CR>` | `0D` | 13 |
| `<LF>` | `0A` | 10 |
| Blank | `20` | 32 |

Ein Befehl wird beispielsweise als:

```text
IN_PV_01<CR><LF>
```

übertragen.

Groß- und Kleinschreibung ist laut Hersteller erlaubt.

Führende Leerzeichen sowie mehrere aufeinanderfolgende Leerzeichen sind ebenfalls erlaubt.

### 6.2 Antwortstruktur

Auf einen empfangenen Befehl sendet der Regler zunächst eine Statusmeldung.

Bei erfolgreicher Verarbeitung:

```text
OK<CR><LF>
```

Bei einem Fehler:

```text
ERR_##<CR><LF>
```

Bei Leseoperationen folgt nach der Statusmeldung eine weitere Zeile mit dem angeforderten Wert.

Beispiel:

```text
PC:
IN_PV_01<CR><LF>

Regler:
OK<CR><LF>
220<CR><LF>
```

### 6.3 Fehlercodes

| Code | Bedeutung |
|---:|---|
| `01` | Schaltelement defekt |
| `02` | Leistungsteil defekt |
| `03` | Temperatursensor defekt |
| `04` | Interner Konfigurationsfehler |
| `07` | Keine MEMory Card oder MEMory Card falsch gesteckt |
| `08` | MEMory Card passt nicht zum Gerät |
| `09` | ALARM! Übertemperatur durch Überwachungsregler erkannt |
| `10` | Parameter falsch |
| `11` | Gerät nicht REMOTE |
| `13` | REMOTE nicht möglich |

Die Fehlerantwort sollte im LoggerPi nicht lediglich als generischer Kommunikationsfehler behandelt werden.

Insbesondere Sensorfehler (`ERR_03`) und Übertemperatur (`ERR_09`) sind relevante Gerätezustände und sollten später als solche im Adapter bzw. Logger-Modell berücksichtigt werden.

---

## 7. Relevante Lese-Befehle

Für LoggerPi sind zunächst ausschließlich Read-Operationen relevant.

Die Herstellerdokumentation definiert mehrere Gruppen von Lese-Befehlen.

### 7.1 Istwerte

```text
IN_PV_{ADR}1
```

liest die Ist-Temperatur in °C.

Beispiel für Adresse `0`:

```text
IN_PV_01<CR><LF>
```

Antwort:

```text
OK<CR><LF>
-###.#<CR><LF>
```

Weitere dokumentierte Process Values:

| Befehl | Wert |
|---|---|
| `IN_PV_{ADR}1` | Ist-Temperatur |
| `IN_PV_{ADR}2` | CO₂-Istwert in % |
| `IN_PV_{ADR}3` | rh-Istwert in % |
| `IN_PV_{ADR}5` | zweite Ist-Temperatur |
| `IN_PV_{ADR}A` | Vakuum-/Druck-Istwert in mbar |
| `IN_PV_{ADR}B` | dritte Ist-Temperatur |
| `IN_PV_{ADR}C` | vierte Ist-Temperatur |
| `IN_PV_{ADR}D` | O₂-Istwert in % |

Nicht jeder Befehl ist bei jedem Gerät bzw. jeder Ausstattung implementiert.

### 7.2 Sollwerte

Die Herstellerdokumentation definiert außerdem:

| Befehl | Wert |
|---|---|
| `IN_SP_{ADR}1` | Temperatur-Sollwert |
| `IN_SP_{ADR}2` | CO₂-Sollwert |
| `IN_SP_{ADR}3` | rh-Sollwert |
| `IN_SP_{ADR}4` | Luftklappen-Sollwert |
| `IN_SP_{ADR}5` | Luftturbinen-Sollwert |
| `IN_SP_{ADR}A` | Druck-Sollwert |
| `IN_SP_{ADR}D` | O₂-Sollwert |

Für die erste LoggerPi-Implementierung sind insbesondere die Istwerte relevant.

Sollwerte können später als zusätzliche Mess-/Metadaten aufgenommen werden.

---

## 8. Gerätekonfiguration und verfügbare Messgrößen

Über `IN_PAR` können Eigenschaften und Ausstattung des Reglers abgefragt werden.

Dokumentiert sind unter anderem:

| Befehl | Bedeutung |
|---|---|
| `IN_PAR_{ADR}1` | Reglerauflösung |
| `IN_PAR_{ADR}4` | Luftklappensteuerung vorhanden |
| `IN_PAR_{ADR}5` | Luftturbine vorhanden |
| `IN_PAR_{ADR}6` | Schaltkontakt 1 vorhanden |
| `IN_PAR_{ADR}7` | Schaltkontakt 2 vorhanden |
| `IN_PAR_{ADR}8` | Schaltkontakt 3 vorhanden |
| `IN_PAR_{ADR}9` | zweite Temperatur vorhanden |
| `IN_PAR_{ADR}A` | Druckwert vorhanden |

Damit kann ein Adapter vor oder während der Datenerfassung feststellen, welche Messgrößen bzw. Funktionen das konkrete Gerät unterstützt.

Für LoggerPi ist insbesondere `IN_PAR_{ADR}9` bzw. `IN_PAR_{ADR}A` interessant, da damit optionale zusätzliche Messgrößen erkannt werden können.

---

## 9. Schreibbefehle und REMOTE-Modus

Die MEMMERT-Schnittstelle unterstützt neben Leseoperationen auch die Steuerung des Gerätes.

Der Betriebsmodus kann mit `OUT_MODE` zwischen Local und Remote umgeschaltet werden:

```text
OUT_MODE_{ADR}0_0
```

Local-Betrieb.

```text
OUT_MODE_{ADR}0_1
```

Remote-Betrieb.

Im Remote-Betrieb können unter anderem Sollwerte über `OUT_SP_*` gesetzt werden.

Beispielsweise:

```text
OUT_SP_{ADR}1_55
```

setzt den Temperatur-Sollwert auf 55 °C.

Für die erste LoggerPi-Implementierung werden **keine Schreibbefehle verwendet**.

Der Logger soll zunächst ausschließlich lesend arbeiten.

Dies vermeidet jede unnötige Veränderung des Betriebszustands des Gerätes.

### Achtung beim Verlassen des REMOTE-Modus

Die Herstellerdokumentation weist darauf hin, dass beim Rücksetzen des `REMOTE`-Status das Gerät automatisch in seinen Grundzustand versetzt wird.

Dokumentiert sind unter anderem:

```text
Soll-Temperatur = 20 °C
Luftklappe = geschlossen
Luftturbine = maximale Drehzahl
```

Daher dürfen `OUT_MODE_*` und `OUT_SP_*` nicht versehentlich im Rahmen eines reinen Monitoring-Tests verwendet werden.

---

## 10. CELSIUS-Polling und Request/Response-Modell

Aus der gefundenen CELSIUS-Konfiguration:

```ini
DelayInMilliseconds = 10
PollIntervall=30
```

ergibt sich ein Polling-Intervall von 30 Sekunden.

CELSIUS wartet laut Konfiguration 10 ms zwischen dem Senden eines Kommandos und dem Lesen der Antwort.

Zusammen mit der nun vorliegenden MEMMERT-Protokolldokumentation ist der grundsätzliche Kommunikationsmechanismus geklärt:

```text
CELSIUS / LoggerPi
       │
       │ Request
       ▼
MEMMERT Controller
       │
       │ OK / ERR
       │ + ggf. Wert
       ▼
CELSIUS / LoggerPi
```

Die bisherige Annahme, dass CELSIUS möglicherweise ein Request/Response-Modell verwendet, ist damit nicht mehr lediglich eine Hypothese.

Das MEMMERT-Protokoll ist ausdrücklich als Befehl/Antwort-Protokoll dokumentiert.

Für LoggerPi ist ein periodisches Polling daher der natürliche Integrationsansatz.

Das tatsächliche optimale Polling-Intervall für LoggerPi muss jedoch nicht zwangsläufig 30 Sekunden betragen. `PollIntervall=30` stammt aus der CELSIUS-Konfiguration und ist zunächst als Referenzwert zu betrachten.

---

## 11. Gerätestatus in CELSIUS

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

Die genaue Bedeutung aller dargestellten Felder ist für die LoggerPi-Implementierung noch nicht vollständig untersucht.

Die Statusanzeige bestätigt jedoch die Zuordnung eines MEMMERT-Reglers zu einer konkreten Kommunikationsschnittstelle.

---

## 12. USB-Transport über B04118

MEMMERT hat bestätigt, dass das Interface B04118 die interne RS-232-Kommunikation des Controllers auf USB umsetzt.

Damit ist folgende Architektur bestätigt:

```text
IPP300 Controller
    │
    │ RS-232
    ▼
B04118
    │
    │ USB
    ▼
Host / Raspberry Pi
```

### 12.1 Noch offene USB-Frage

Noch nicht geklärt ist, wie sich das B04118 konkret am Linux-Host präsentiert.

Insbesondere müssen noch ermittelt werden:

- USB Vendor ID (VID)
- USB Product ID (PID)
- Manufacturer
- Product
- Serial Number, falls vorhanden
- USB Interface Class
- Interface/Subclass/Protocol
- Kernel-Treiber
- erzeugtes `/dev/tty*`-Device
- stabile udev-Eigenschaften

### 12.2 PL2303-Hypothese

In der ursprünglichen Untersuchung wurde ein Prolific-USB-Seriell-Treiber gefunden, unter anderem mit Unterstützung für:

```text
VID_067B&PID_2303
"Prolific USB-to-Serial Comm Port"
```

sowie:

```text
VID_067B&PID_2304
"Prolific USB-to-Serial Comm Port"
```

Daraus entstand die Hypothese, dass das B04118 möglicherweise einen PL2303 oder einen ähnlichen USB-Serial-Chip verwendet.

Diese Hypothese ist **nicht durch MEMMERT bestätigt**.

Die Herstellerinformation bestätigt lediglich die Funktion:

```text
RS-232 → USB
```

Der konkrete USB-Controller bleibt zu verifizieren.

Daher darf die PL2303-Annahme nicht als Grundlage der Implementierung verwendet werden.

---

## 13. PL2303-Erkennung

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

Die PL2303-Hypothese ist deshalb derzeit lediglich historischer Recherchekontext und keine bestätigte Hardwareeigenschaft des B04118.

---

## 14. USB-Portabhängigkeit und Geräteidentität

Die Linux-Gerätenamen `/dev/ttyUSB0`, `/dev/ttyUSB1` usw. dürfen nicht als alleinige Geräteidentität verwendet werden.

Unter Linux können sich diese Namen abhängig von Enumeration und Anschlussreihenfolge ändern.

Nicht ideal:

```text
/dev/ttyUSB0 = IPP300-1
/dev/ttyUSB1 = IPP300-2
```

Besser ist eine Identifikation über stabile Eigenschaften.

Mögliche Ebenen:

```text
USB-Geräteidentität
+
MEMMERT-Geräteadresse
+
LoggerPi device_id
```

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

Damit kann die logische Geräteidentität unabhängig vom physischen USB-Port aufgebaut werden.

Falls das B04118 keine USB-Seriennummer bereitstellt, muss die stabile Host-seitige Zuordnung über udev bzw. andere USB-Gerätemerkmale erfolgen.

---

## 15. Proprietäres USB-Protokoll

Die ursprüngliche Untersuchung betrachtete die Möglichkeit, dass das B04118 ein proprietäres USB-Protokoll verwenden könnte.

Durch die Herstellerinformation ist inzwischen geklärt, dass das B04118 funktional als **RS-232-zu-USB-Interface** eingesetzt wird.

Ein Reverse Engineering eines proprietären MEMMERT-USB-Protokolls ist daher derzeit **nicht angezeigt**.

Der nächste Schritt ist zunächst festzustellen, ob das B04118 am Raspberry Pi als USB-Serial-Gerät erscheint.

Nur falls die USB-Enumeration entgegen der erwarteten seriellen Architektur keine direkt nutzbare serielle Schnittstelle bereitstellt, wäre eine weitergehende USB-Untersuchung erforderlich.

Der Fokus der Untersuchung verschiebt sich damit von:

```text
USB-Protokoll reverse engineeren
```

zu:

```text
USB-Serial-Device identifizieren
        ↓
serielle Verbindung öffnen
        ↓
MEMMERT-Protokoll verwenden
```

---

## 16. Polling-Modell im Vergleich zum vorhandenen Freezer

Das MEMMERT-Protokoll ist ein klassisches Request/Response-Protokoll.

Der grundsätzliche Ablauf ist:

```text
LoggerPi
   │
   │ IN_PV_01<CR><LF>
   ▼
MEMMERT
   │
   │ OK<CR><LF>
   │ 24.1<CR><LF>
   ▼
LoggerPi
```

Das unterscheidet sich konzeptionell vom derzeit vorhandenen Freezer.

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

Daraus ergibt sich für LoggerPi die Möglichkeit, unterschiedliche Adaptertypen zu unterstützen:

```text
Serial Reader
├── passive/streaming devices
│   └── z.B. vorhandener Freezer
│
└── request/response devices
    └── MEMMERT IPP300
```

---

## 17. RS-485 und Ethernet als allgemeiner MEMMERT-Kontext

MEMMERT-Geräte können je nach Ausstattung auch über RS-485 oder Ethernet/LAN kommunizieren.

### RS-485

Das IPP300-Handbuch nennt für entsprechende Ausstattung:

- 2-Draht-Bus
- Geräteadresse 0 ... 15
- maximal 16 adressierbare Geräte
- 150 m maximale Gesamtkabellänge
- 220-Ohm-Abschlusswiderstand am letzten Gerät

Die genaue maximale Geräteanzahl unterscheidet sich teilweise zwischen älteren MEMMERT/CELSIUS-Dokumentationen.

Für die aktuelle LoggerPi-Integration ist RS-485 jedoch nicht der primäre Transportweg, da die vorhandenen IPP300 über B04118 an USB angebunden sind.

### Ethernet/LAN

CELSIUS unterstützt ebenfalls Geräte mit Ethernet-Schnittstelle.

Laut CELSIUS-Handbuch:

- jeder Schrank benötigt eine eindeutige IP- bzw. DNS-Adresse
- ältere Geräte können standardmäßig `192.168.100.100` verwenden
- die IP-Adresse kann mit `XTADMIN` geändert werden
- anschließend wird die IP-Adresse in CELSIUS eingetragen

In CELSIUS können bis zu 16 Geräte über LAN verwaltet werden.

Für die beiden vorhandenen IPP300 ist derzeit nicht bekannt, ob Ethernet-Hardware vorhanden ist.

Diese Informationen sind für den aktuellen B04118/USB-Pfad Hintergrundwissen und keine Voraussetzung für die erste Implementierung.

---

## 18. Bezug zu den bereits vorhandenen MEMMERT-Geräten

Im bestehenden LoggerPi-/Observer-System werden bereits zwei andere MEMMERT-Geräte über Ethernet angesprochen.

Dort wird die MEMMERT-/AtmoControl-API verwendet.

Das ist zunächst von den beiden IPP300 getrennt zu betrachten.

Für die IPP300 liegt derzeit kein belastbarer Nachweis vor, dass deren ältere RS-232-/B04118-Kommunikation über dieselbe AtmoControl/API-Schicht erreichbar ist.

Die vorhandene Herstellerdokumentation zeigt dagegen eindeutig einen eigenständigen, textbasierten RS-232-Kommunikationsweg.

Für die IPP300 sollte daher zunächst der dokumentierte RS-232-Weg über B04118 implementiert bzw. getestet werden.

---

## 19. Herstellerkontakt und Primärquelle

Am 2026-09-04 wurde eine technische Anfrage an den MEMMERT-Service gestellt.

MEMMERT bestätigte daraufhin:

> Intern wird über die RS232-Schnittstelle vom Controller kommuniziert. Das Interface B04118 wandelt auf USB, welche in Ihren Geräten als Kommunikations-Schnittstelle herausgeführt ist.

Zusätzlich stellte MEMMERT eine offizielle Schnittstellenbeschreibung zur Verfügung.

### Herstellerdokumentation

**Titel:**

**Schnittstellenbeschreibung für MEMMERT-Wärmeschränke mit Temperaturregler der E- oder P-Klasse**

**Stand:** April 2011

**Lokale Kopie im Repository:**

```text
docs/research/sources/MEMMERT_IPP300_Beschreibung_RS232-2010.pdf
```

Die Dokumentation beschreibt:

- serielle Übertragungsparameter
- RS-232-Anschluss
- NAMUR-basierte Befehlssyntax
- Geräteadressierung
- Statusantworten
- Fehlercodes
- Istwert-Abfragen
- Sollwert-Abfragen
- Konfigurationsabfragen
- Schreib-/Steuerbefehle
- REMOTE-Modus

Die Herstellerdokumentation ist für die Protokollimplementierung die primäre technische Quelle.

---

## 20. Nächste Untersuchungsschritte

Die grundsätzliche Protokollspezifikation ist durch die Herstellerdokumentation geklärt.

Als nächstes soll die Kommunikation am real vorhandenen IPP300 verifiziert werden.

### Schritt 1 – USB-Enumeration

IPP300 über B04118 mit dem Raspberry Pi verbinden und prüfen:

```bash
lsusb
```

danach:

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

Falls ein serielles Device erzeugt wird:

```bash
udevadm info -a -n /dev/ttyUSB0
```

bzw. entsprechend für das tatsächlich erzeugte Device.

### Schritt 2 – USB-Identität dokumentieren

Folgende Informationen sollen für das B04118 festgehalten werden:

- VID
- PID
- Hersteller
- Produktname
- Seriennummer, falls vorhanden
- Kernel-Treiber
- `/dev/tty*`
- stabile udev-Eigenschaften

### Schritt 3 – Serielle Kommunikation testen

Falls das Interface als serielles Device verfügbar ist, zunächst mit den vom Hersteller dokumentierten Parametern:

```text
2400 Baud
8 Datenbits
keine Parität
1 Stopbit
kein Hardware-Handshake
kein Software-Handshake
```

### Schritt 4 – Read-only-Protokoll testen

Als erster Protokolltest soll ausschließlich ein ungefährlicher Lesezugriff erfolgen.

Für ein Gerät mit Adresse `0`:

```text
IN_PV_01<CR><LF>
```

Erwartete Antwortstruktur:

```text
OK<CR><LF>
<Temperatur><CR><LF>
```

Beispiel aus der MEMMERT-Dokumentation:

```text
IN_PV_01<CR><LF>

OK<CR><LF>
220<CR><LF>
```

### Schritt 5 – Weitere Istwerte prüfen

Nach erfolgreicher Temperaturabfrage können optional die weiteren dokumentierten Process Values getestet werden:

```text
IN_PV_{ADR}2
IN_PV_{ADR}3
IN_PV_{ADR}5
IN_PV_{ADR}A
IN_PV_{ADR}B
IN_PV_{ADR}C
IN_PV_{ADR}D
```

Nicht vorhandene bzw. nicht unterstützte Funktionen müssen dabei sauber behandelt werden.

### Schritt 6 – Gerätekonfiguration prüfen

Nach erfolgreicher Kommunikation können zusätzlich die verfügbaren Funktionen über `IN_PAR` abgefragt werden.

Beispielsweise:

```text
IN_PAR_{ADR}1
IN_PAR_{ADR}9
IN_PAR_{ADR}A
```

Damit lässt sich feststellen, welche optionalen Messwerte beim konkreten IPP300 tatsächlich vorhanden sind.

### Schritt 7 – Keine Schreibbefehle im ersten Test

Die dokumentierten `OUT_MODE_*` und `OUT_SP_*` Befehle werden für die erste LoggerPi-Untersuchung **nicht verwendet**.

Der erste Proof-of-Concept soll ausschließlich lesend arbeiten.

Damit besteht kein unnötiges Risiko, Sollwerte oder Betriebszustände des Gerätes zu verändern.

---

## 21. Relevanz für die LoggerPi-Architektur

Die MEMMERT-Kommunikation ist ein Request/Response-Protokoll über eine serielle Verbindung.

Der geplante Adapter sollte deshalb Transport und Protokoll trennen:

```text
MemmertAdapter
      │
      ├── SerialTransport
      │      └── /dev/ttyUSB*
      │
      └── MemmertProtocol
             ├── command generation
             ├── response parsing
             ├── status handling
             └── value conversion
```

Der Transport kennt dabei ausschließlich die serielle Verbindung.

Das Protokoll kennt:

- Geräteadresse
- `IN_PV`
- `IN_SP`
- `IN_PAR`
- `IN_MODE`
- `OK`
- `ERR_##`
- CR/LF framing

Dadurch bleibt die Architektur unabhängig davon, welcher konkrete USB-Serial-Chip im B04118 verwendet wird.

Die Geräteidentität sollte ebenfalls nicht ausschließlich an `/dev/ttyUSB0` oder `/dev/ttyUSB1` gebunden werden.

Stattdessen sollte eine stabile Konfiguration verwendet werden, beispielsweise:

```yaml
memmert:
  port: /dev/ttyUSB0
  address: 0
```

Langfristig kann die Zuordnung über stabile USB-/udev-Eigenschaften und die MEMMERT-Geräteadresse abgesichert werden.

---

## 22. Aktueller Erkenntnisstand

Der MEMMERT-IP­P300-Kommunikationsweg ist durch die Herstellerinformationen wesentlich besser geklärt als zum Beginn der Untersuchung.

### Durch MEMMERT bestätigt

- Der Controller kommuniziert intern über RS-232.
- Das Interface B04118 setzt RS-232 auf USB um.
- Das MEMMERT-Protokoll ist dokumentiert.
- Die Kommunikation erfolgt nach NAMUR.
- Die seriellen Parameter sind 2400 Baud, 8N1.
- Es wird kein Handshake verwendet.
- Die Übertragung ist halbduplex.
- Befehle werden mit CR/LF abgeschlossen.
- Geräte besitzen eine Adresse von 0 bis F.
- Das Protokoll verwendet Statusantworten `OK` bzw. `ERR_##`.
- Istwerte können über `IN_PV_*` abgefragt werden.
- Sollwerte können über `IN_SP_*` abgefragt bzw. gesetzt werden.
- Konfigurationsmerkmale können über `IN_PAR_*` abgefragt werden.

### Nicht mehr notwendig

Ein Reverse Engineering des eigentlichen MEMMERT-Kommunikationsprotokolls ist nicht erforderlich.

Ebenso besteht derzeit kein Grund, ein proprietäres USB-Protokoll zu reverse engineeren.

### Noch zu verifizieren

- konkrete USB-VID/PID des B04118
- verwendeter USB-Serial-Chip bzw. Kernel-Treiber
- erzeugtes Linux-Device
- stabile USB-Identifikationsmerkmale
- tatsächliche Geräteadresse der beiden IPP300
- erfolgreiche Kommunikation mit dem realen Gerät
- tatsächlich verfügbare `IN_PV_*` Werte des konkreten IPP300
- Verhalten bei nicht unterstützten Befehlen
- praktische Antwortzeiten
- sinnvolles Polling-Intervall für LoggerPi
- Verhalten bei Kommunikationsunterbrechungen
- Verhalten bei den dokumentierten `ERR_##` Zuständen

### Ziel des nächsten Tests

Der nächste Test soll einen **read-only Zugriff** auf die Ist-Temperatur demonstrieren:

```text
IN_PV_{ADR}1<CR><LF>
```

mit erwarteter Antwort:

```text
OK<CR><LF>
<Temperatur><CR><LF>
```

Wenn dieser Test erfolgreich ist, ist die technische Grundlage für einen `MemmertAdapter` in LoggerPi-OtterPi gegeben.

### Primärquelle

```text
docs/research/sources/MEMMERT_IPP300_Beschreibung_RS232-2010.pdf
```

**Schnittstellenbeschreibung für MEMMERT-Wärmeschränke mit Temperaturregler der E- oder P-Klasse, Stand April 2011.**
