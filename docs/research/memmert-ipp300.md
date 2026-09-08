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

Der grundsätzliche Kommunikationsweg sowie die praktische Kommunikation mit dem real vorhandenen IPP300 sind inzwischen verifiziert.

Das MEMMERT USB Interface B04118 setzt die interne RS-232-Kommunikation des Controllers auf USB um. Unter Linux wird das Interface als serielles Device bereitgestellt.

Am real vorhandenen IPP300 wurde erfolgreich folgende Kommunikation durchgeführt:

```text
Port      : /dev/ttyUSB1
Baudrate  : 2400
Format    : 8N1
Flow Ctrl : none
Adresse   : 1
```

Die folgenden Read-only-Befehle wurden erfolgreich getestet:

```text
IN_MODE_10
IN_PAR_11
IN_PV_11
IN_SP_11
```

Damit ist die grundlegende Request/Response-Kommunikation des IPP300 über B04118 praktisch nachgewiesen.

Zusätzlich wurde eine vollständige Read-only-Inventur der in der Herstellerdokumentation beschriebenen relevanten `IN_*` Befehle durchgeführt. Dabei wurde festgestellt, dass für den konkret untersuchten IPP300 lediglich folgende Abfragen für die geplante LoggerPi-Integration relevant sind:

```text
IN_MODE_10   Betriebsart
IN_PAR_11    Reglerauflösung
IN_PV_11     Ist-Temperatur
IN_SP_11     Temperatur-Sollwert
```

Die übrigen dokumentierten optionalen Mess- und Konfigurationsabfragen sind für dieses Gerät nicht relevant bzw. laut Gerätekonfiguration nicht vorhanden.

Ein separater Timing-Test mit 20 aufeinanderfolgenden `IN_PV_11` Requests ergab eine sehr konstante Antwortzeit von durchschnittlich 122,39 ms bei 20/20 erfolgreichen Antworten.

Damit ist die technische Grundlage für einen read-only `MemmertAdapter` in LoggerPi-OtterPi gegeben.

Die vollständige Herstellerbefehlsliste bleibt als Research-Dokumentation erhalten. Der Softwareadapter muss jedoch nicht die vollständige MEMMERT-Schnittstelle implementieren, sondern zunächst nur den für den konkreten IPP300 tatsächlich benötigten Read-only-Subset.

---

### Neue Erkenntnisse zur Linux-USB-Identität (2026-09-08)

Die Linux-seitige USB-Erkennung der beiden tatsächlich vorhandenen
MEMMERT-IPPs wurde inzwischen praktisch vollständig untersucht.

Beide MEMMERT-Verbindungen erscheinen als Prolific USB-Serial-Geräte:

```text
Vendor:      Prolific Technology Inc.
VID:         067b
Product:     USB-Serial Controller
PID:         2303
Driver:      pl2303
```

Beide Adapter besitzen in der untersuchten Linux-Enumeration keine
individuelle `ID_SERIAL_SHORT`.

Die beiden Adapter sind daher nicht anhand einer individuellen
USB-Seriennummer unterscheidbar.

Sie lassen sich jedoch eindeutig anhand ihrer physischen USB-Topologie
am LoggerPi unterscheiden:

```text
1-1.4 -> /dev/ttyUSB1 -> MEMMERT-Adresse 1 -> 14,1 °C
1-1.5 -> /dev/ttyUSB2 -> MEMMERT-Adresse 2 -> 24,0 °C
```

Für den späteren LoggerPi-Dauerbetrieb wurden deshalb stabile udev-
Symlinks eingerichtet:

```text
/dev/memmert_ipp300_links
/dev/memmert_ipp300_rechts
```

Die aktuelle Zuordnung lautet:

```text
/dev/memmert_ipp300_links
    -> USB topology 1-1.4
    -> aktuell /dev/ttyUSB1
    -> MEMMERT-Adresse 1
    -> IPP300 links
    -> 14,1 °C

/dev/memmert_ipp300_rechts
    -> USB topology 1-1.5
    -> aktuell /dev/ttyUSB2
    -> MEMMERT-Adresse 2
    -> IPP300 rechts
    -> 24,0 °C
```

Die vollständige Linux-seitige Untersuchung ist separat dokumentiert
unter:

```text
docs/research/memmert-ipp300-linux-usb-identity.md
```

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

Das im Rahmen dieser Untersuchung getestete IPP300 antwortet auf die Geräteadresse:

```text
1
```

Die verwendeten Befehle enthalten daher beispielsweise:

```text
IN_MODE_10
IN_PAR_11
IN_PV_11
IN_SP_11
```

Die Adresse des zweiten vorhandenen IPP300 ist separat zu verifizieren.

Für LoggerPi sollte die MEMMERT-Adresse als explizite Gerätekonfiguration behandelt werden.

Beispiel:

```yaml
memmert:
  address: 1
```

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

Die Herstellerdokumentation definiert zahlreiche `IN_*` Befehle. Eine vollständige Read-only-Inventur des real vorhandenen IPP300 wurde inzwischen durchgeführt.

Für die geplante LoggerPi-Integration sind beim konkret untersuchten IPP300 jedoch nur vier Abfragen relevant:

| Befehl | Bedeutung | Ergebnis beim Test |
|---|---|---|
| `IN_MODE_10` | Betriebsart | `0` = LOCAL |
| `IN_PAR_11` | Reglerauflösung | `0` = 0,1 °C |
| `IN_PV_11` | Ist-Temperatur | `14.7 °C` |
| `IN_SP_11` | Temperatur-Sollwert | `14.7 °C` |

### 7.1 Betriebsart

```text
IN_MODE_10
```

liest die aktuelle Betriebsart des Reglers.

Beim getesteten IPP300:

```text
OK\r\n
0\r\n
```

Ergebnis:

```text
LOCAL / manueller Betrieb
```

### 7.2 Reglerauflösung

```text
IN_PAR_11
```

liest die Auflösung des Temperaturreglers.

Beim getesteten IPP300:

```text
OK\r\n
0\r\n
```

Ergebnis:

```text
0,1 °C
```

### 7.3 Ist-Temperatur

```text
IN_PV_11
```

liest die aktuelle Ist-Temperatur.

Beim getesteten IPP300:

```text
OK\r\n
14.7\r\n
```

Ergebnis:

```text
14.7 °C
```

### 7.4 Temperatur-Sollwert

```text
IN_SP_11
```

liest den aktuell eingestellten Temperatur-Sollwert.

Beim getesteten IPP300:

```text
OK\r\n
14.7\r\n
```

Ergebnis:

```text
14.7 °C
```

### 7.5 Weitere dokumentierte Read-Befehle

Die vollständige Herstellerdokumentation definiert zusätzlich:

| Befehl | Wert |
|---|---|
| `IN_PV_{ADR}2` | CO₂-Istwert |
| `IN_PV_{ADR}3` | rh-Istwert |
| `IN_PV_{ADR}5` | zweite Ist-Temperatur |
| `IN_PV_{ADR}A` | Vakuum-/Druck-Istwert |
| `IN_PV_{ADR}B` | dritte Ist-Temperatur |
| `IN_PV_{ADR}C` | vierte Ist-Temperatur |
| `IN_PV_{ADR}D` | O₂-Istwert |
| `IN_SP_{ADR}2` | CO₂-Sollwert |
| `IN_SP_{ADR}3` | rh-Sollwert |
| `IN_SP_{ADR}4` | Luftklappen-Sollwert |
| `IN_SP_{ADR}5` | Luftturbinen-Sollwert |
| `IN_SP_{ADR}A` | Druck-Sollwert |
| `IN_SP_{ADR}D` | O₂-Sollwert |

Diese Befehle bleiben als Teil der Hersteller-Referenz dokumentiert, werden aber nicht Bestandteil des ersten `MemmertAdapter`.

Der Adapter implementiert zunächst ausschließlich den tatsächlich benötigten Read-only-Subset:

```text
IN_MODE_10
IN_PAR_11
IN_PV_11
IN_SP_11
```

---

## 8. Gerätekonfiguration und nicht vorhandene Funktionen

Die Herstellerdokumentation definiert über `IN_PAR` verschiedene optionale Ausstattungsmerkmale.

Für den konkret untersuchten IPP300 wurde eine vollständige Read-only-Inventur durchgeführt.

Ergebnis:

| Befehl | Funktion | Ergebnis |
|---|---|---|
| `IN_PAR_11` | Reglerauflösung | `0` = 0,1 °C |
| `IN_PAR_14` | Luftklappensteuerung | `0` = nicht vorhanden |
| `IN_PAR_15` | Luftturbine | `0` = nicht vorhanden |
| `IN_PAR_16` | Schaltkontakt 1 | `0` = nicht vorhanden |
| `IN_PAR_17` | Schaltkontakt 2 | `0` = nicht vorhanden |
| `IN_PAR_18` | Schaltkontakt 3 | `0` = nicht vorhanden |
| `IN_PAR_19` | zweite Temperatur | `0` = nicht vorhanden |
| `IN_PAR_1A` | Druck/Vakuum | `0` = nicht vorhanden |

Damit sind für den konkret untersuchten IPP300 insbesondere folgende optionalen Funktionen nicht vorhanden:

- Luftklappensteuerung
- Luftturbine
- Schaltkontakte 1–3
- zweite Temperatur
- Druck/Vakuum

Diese Funktionen werden daher nicht Bestandteil des ersten LoggerPi-Adapters.

Die entsprechenden Herstellerbefehle bleiben ausschließlich als Referenz in dieser Research-Dokumentation erhalten.

### Auffällige Werte optionaler Temperaturkanäle

Bei der vollständigen Inventur lieferten einige nicht vorhandene bzw. nicht relevante Temperaturkanäle dennoch numerische Antworten:

```text
IN_PV_15 -> 0.0
IN_PV_1B -> 819.1
IN_PV_1C -> 819.1
```

Da die Gerätekonfiguration keine entsprechenden zusätzlichen Temperaturkanäle meldet, werden diese Werte nicht als reale Messwerte interpretiert.

Insbesondere darf `819.1` nicht als gültige Temperatur in LoggerPi übernommen werden.

Für den Adapter ist ausschließlich der konfigurierte und tatsächlich benötigte Temperaturkanal `IN_PV_11` relevant.

---

## 9. Schreibbefehle und REMOTE-Modus

Die MEMMERT-Schnittstelle unterstützt neben Leseoperationen auch Schreib- und Steuerbefehle.

Diese Befehle werden in dieser Research-Dokumentation vollständig erfasst, sind aber **nicht Bestandteil des ersten LoggerPi-Adapters**.

### 9.1 Theoretisch verfügbare OUT-Befehle

Die Herstellerdokumentation definiert unter anderem folgende Schreibbefehle:

| Befehl | Funktion |
|---|---|
| `OUT_MODE_{ADR}0_0` | Local-Betrieb |
| `OUT_MODE_{ADR}0_1` | Remote-Betrieb |
| `OUT_SP_{ADR}1_...` | Temperatur-Sollwert |
| `OUT_SP_{ADR}2_...` | CO₂-Sollwert |
| `OUT_SP_{ADR}3_...` | rh-Sollwert |
| `OUT_SP_{ADR}4_...` | Luftklappenstellung |
| `OUT_SP_{ADR}5_...` | Luftturbinendrehzahl |
| `OUT_SP_{ADR}6_...` | Schaltkontakt A |
| `OUT_SP_{ADR}7_...` | Schaltkontakt B |
| `OUT_SP_{ADR}8_...` | Schaltkontakt C |
| `OUT_SP_{ADR}A_...` | Druck-Sollwert |
| `OUT_SP_{ADR}D_...` | O₂-Sollwert |

Für das getestete Gerät mit Adresse `1` wäre der dokumentierte Befehl zum Umschalten auf Remote theoretisch:

```text
OUT_MODE_10_1
```

Dieser Befehl wurde **nicht ausgeführt**.

Ebenso wurden keine `OUT_SP_*` Befehle ausgeführt.

### 9.2 Sicherheitsgrenze der Untersuchung

Die vorhandenen IPP300 sind produktive Geräte.

Daher gilt für die weitere Protokolluntersuchung:

```text
ERLAUBT:
IN_*

NICHT AUSFÜHREN:
OUT_MODE_*
OUT_SP_*
```

Die praktischen Tests wurden ausschließlich mit `IN_*` Befehlen durchgeführt.

Insbesondere wurde der Wechsel von Local nach Remote nicht über die serielle Schnittstelle getestet.

Ob und unter welchen Bedingungen ein Wechsel zwischen Local und Remote über `OUT_MODE_*` im praktischen Betrieb zulässig ist, bleibt für eine spätere, separat geplante Untersuchung offen.

Für die aktuelle LoggerPi-Integration ist dieser Funktionsumfang ausdrücklich nicht erforderlich.

### 9.3 REMOTE-Modus

Die Herstellerdokumentation beschreibt einen REMOTE-Modus, in dem Steuerbefehle über die Kommunikationsschnittstelle möglich sind.

Für den aktuellen Monitoring-Anwendungsfall wird ausschließlich der bestehende Betriebszustand gelesen:

```text
IN_MODE_10
```

Der Logger verändert den Betriebsmodus des Gerätes nicht.

Die dokumentierten Auswirkungen des REMOTE-Modus sowie insbesondere mögliche Zustandsänderungen beim Verlassen von REMOTE sind deshalb lediglich sicherheitsrelevanter Dokumentationskontext und kein Bestandteil des laufenden Integrationstests.

### Achtung beim Verlassen des REMOTE-Modus

Die Herstellerdokumentation weist darauf hin, dass beim Rücksetzen des `REMOTE`-Status das Gerät automatisch in seinen Grundzustand versetzt wird.

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

## 10.1 Praktische Kommunikationslatenz

Mit dem Testskript:

```text
docs/research/sources/memmert_ipp300_timing_test.py
```

wurde die Antwortzeit des IPP300 für 20 aufeinanderfolgende `IN_PV_11` Requests gemessen.

Ergebnis:

| Kennzahl | Wert |
|---|---:|
| Requests | 20 |
| Erfolgreiche Antworten | 20/20 |
| Minimum | 121,88 ms |
| Maximum | 122,56 ms |
| Mittelwert | 122,39 ms |
| Median | 122,41 ms |

Die Antwortzeit lag damit im Test sehr konstant bei ungefähr:

```text
122 ms pro Request
```

Der Test zeigt, dass die Kommunikation zuverlässig und mit reproduzierbarer Latenz funktioniert.

Die gemessenen 122 ms sind ein empirischer Wert des konkreten Tests und keine vom Hersteller spezifizierte maximale Antwortzeit.

Ein aggressives Polling ist für LoggerPi daher nicht erforderlich. Ein deutlich größeres Polling-Intervall, beispielsweise im Bereich von mehreren Sekunden bis hin zu 30 Sekunden, belastet die serielle Schnittstelle nur sehr gering.

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

### 12.1 Linux-Enumeration des B04118 – praktisch verifiziert

Die Linux-Enumeration der beiden tatsächlich vorhandenen MEMMERT-
Verbindungen wurde am 2026-09-08 untersucht.

Beide Interfaces erscheinen als Prolific USB-Serial-Controller:

| Eigenschaft | Wert |
|---|---|
| Manufacturer | Prolific Technology Inc. |
| Product | USB-Serial Controller |
| VID | `067b` |
| PID | `2303` |
| Kernel-Treiber | `pl2303` |
| USB Speed | 12 Mbit/s |
| USB Version | 1.10 |

Eine individuelle `ID_SERIAL_SHORT` wird bei den beiden Geräten nicht
bereitgestellt.

Damit ist die Kombination aus Hersteller und VID/PID nicht ausreichend,
um die beiden Adapter voneinander zu unterscheiden.

Die eindeutige Unterscheidung erfolgt derzeit über die physische
USB-Topologie des LoggerPi:

```text
1-1.4 -> /dev/ttyUSB1 -> MEMMERT 1
1-1.5 -> /dev/ttyUSB2 -> MEMMERT 2
```

Die entsprechenden stabilen udev-Namen sind:

```text
/dev/memmert_ipp300_links
/dev/memmert_ipp300_rechts
```

Die vollständigen Linux-Details sind in
`docs/research/memmert-ipp300-linux-usb-identity.md` dokumentiert.

### 12.2 Schlussfolgerung zur B04118-Identifikation

Die ursprüngliche offene Frage, ob das B04118 am Linux-Host als
USB-Serial-Gerät erscheint, ist beantwortet.

Das reale Gerät wird als USB-Serial-Gerät erkannt und kann direkt über
das Linux-Seriell-Subsystem angesprochen werden.

Die praktische Kette lautet:

```text
IPP300 Controller
    │
    │ RS-232
    ▼
B04118
    │
    │ USB
    ▼
Prolific USB-Serial Controller
    │
    │ pl2303
    ▼
Linux /dev/ttyUSB*
    │
    ▼
udev-stabiler Gerätename
```

Ein Reverse Engineering eines proprietären USB-Protokolls ist für die
vorhandene Hardware daher nicht erforderlich.

Die PL2303-Eigenschaft ist jetzt keine reine historische Hypothese
mehr, sondern wurde am realen LoggerPi über `udevadm` praktisch
verifiziert.

Sie sollte jedoch weiterhin nicht mit einer individuellen Geräte-ID
verwechselt werden: Beide vorhandenen Adapter besitzen dieselben
USB-Identifikationswerte und keine individuelle USB-Seriennummer.

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

Die Linux-Gerätenamen `/dev/ttyUSB0`, `/dev/ttyUSB1` usw. dürfen nicht
als alleinige Geräteidentität verwendet werden.

Unter Linux können sich diese Namen abhängig von Enumeration und
Anschlussreihenfolge ändern.

Für die beiden tatsächlich vorhandenen MEMMERT-USB-Adapter wurde
untersucht, ob eine individuelle USB-Seriennummer oder andere
geräteindividuelle USB-Kennung vorhanden ist.

Ergebnis:

```text
MEMMERT links:
    VID  = 067b
    PID  = 2303
    Serial Short = nicht vorhanden

MEMMERT rechts:
    VID  = 067b
    PID  = 2303
    Serial Short = nicht vorhanden
```

Beide Adapter sind damit auf USB-Geräteebene anhand dieser Merkmale
identisch.

Die praktische Unterscheidung erfolgt deshalb über die physische
USB-Topologie des Raspberry Pi.

### Aktuelle Zuordnung

```text
USB topology 1-1.4
    ↓
/dev/ttyUSB1
    ↓
MEMMERT-Adresse 1
    ↓
IPP300 links
    ↓
/dev/memmert_ipp300_links
```

und:

```text
USB topology 1-1.5
    ↓
/dev/ttyUSB2
    ↓
MEMMERT-Adresse 2
    ↓
IPP300 rechts
    ↓
/dev/memmert_ipp300_rechts
```

Die verwendeten udev-Regeln sind:

```text
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", KERNELS=="1-1.4", SYMLINK+="memmert_ipp300_links"
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", KERNELS=="1-1.5", SYMLINK+="memmert_ipp300_rechts"
```

Damit wird die aktuelle physische Verdrahtung stabil und unabhängig
von der jeweiligen `ttyUSB`-Nummer abgebildet.

### Einschränkung

Diese Identifikation ist portstabil, nicht adapterstabil.

Wenn ein Adapter von `1-1.4` auf `1-1.5` umgesteckt wird, würde die
bisherige logische Zuordnung ebenfalls wechseln.

Daher gilt für die LoggerPi-Hardware:

> Die beiden MEMMERT-Adapter sollen nach Einrichtung der udev-Zuordnung
> nicht zwischen den definierten USB-Buchsen vertauscht werden.

Die MEMMERT-Geräteadresse stellt eine zusätzliche logische Identität
dar:

```text
USB-Port / udev
        +
MEMMERT-Adresse
        +
LoggerPi device_id
```

Damit kann der LoggerPi sowohl den Transportweg als auch das logisch
angesprochene MEMMERT-Gerät eindeutig konfigurieren.

Die vollständige Hardware-/udev-Untersuchung ist dokumentiert unter:

```text
docs/research/memmert-ipp300-linux-usb-identity.md
```

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

### Praktische Testartefakte

Die praktische Verifikation ist durch zwei reproduzierbare Python-Skripte dokumentiert:

```text
docs/research/sources/memmert_ipp300_inventory.py
docs/research/sources/memmert_ipp300_timing_test.py
```

`memmert_ipp300_inventory.py` führt eine vollständige Read-only-Inventur der relevanten dokumentierten `IN_*` Befehle durch.

`memmert_ipp300_timing_test.py` misst die Request/Response-Latenz anhand von 20 aufeinanderfolgenden `IN_PV_11` Requests.

Beide Skripte verwenden ausschließlich `IN_*` Befehle.

Es werden keine `OUT_MODE_*` oder `OUT_SP_*` Befehle ausgeführt.

---

## 20. Verifikation und nächste Schritte

### 20.1 Bereits erfolgreich verifiziert

Folgende Punkte sind inzwischen praktisch nachgewiesen:

- B04118 wird unter Linux als serielles Device bereitgestellt.
- Das getestete Device ist `/dev/ttyUSB1`.
- Die Kommunikation mit `2400 8N1` funktioniert.
- Hardware- und Software-Flow-Control sind nicht erforderlich.
- Das getestete IPP300 antwortet auf Adresse `1`.
- `IN_MODE_10` funktioniert.
- `IN_PAR_11` funktioniert.
- `IN_PV_11` funktioniert.
- `IN_SP_11` funktioniert.
- Das Antwortformat `OK\r\nWert\r\n` wurde praktisch verifiziert.
- Die vollständige Read-only-Inventur wurde durchgeführt.
- Die optionalen Funktionen des konkreten Gerätes wurden über `IN_PAR_*` überprüft.
- Der Timing-Test mit 20 Requests war mit 20/20 Antworten erfolgreich.

### 20.2 Noch offen

Für die eigentliche LoggerPi-Integration sind noch folgende Punkte
relevant:

- Kommunikationsfehler und `ERR_##` sauber im Adapter behandeln
- Verhalten bei Verbindungsunterbrechungen definieren
- geeignetes Polling-Intervall für LoggerPi festlegen
- `MemmertAdapter` implementieren
- Logging und Normalisierung der vier relevanten Werte definieren
- Integration in den bestehenden Core-Batch-/Queue-/Delivery-Pfad
  praktisch verifizieren

Die Identifikation des zweiten IPP300, seine MEMMERT-Adresse sowie die
stabile Linux-seitige udev-Zuordnung sind inzwischen praktisch
verifiziert und daher nicht mehr offen.

### 20.3 Nicht Bestandteil der aktuellen Untersuchung

Die folgenden Funktionen werden bewusst nicht praktisch getestet:

```text
OUT_MODE_*
OUT_SP_*
```

Insbesondere wird kein produktiver IPP300 über die serielle Schnittstelle auf REMOTE geschaltet und es werden keine Sollwerte verändert.

Die vollständige OUT-Befehlsliste bleibt ausschließlich als Referenz in dieser Research-Dokumentation erhalten.

### 20.4 Ziel des Adapters

Der erste `MemmertAdapter` soll ausschließlich den tatsächlich benötigten Read-only-Umfang implementieren:

```text
IN_MODE_10
IN_PAR_11
IN_PV_11
IN_SP_11
```

Damit kann der Adapter mindestens folgende Informationen bereitstellen:

```text
Betriebsart
Reglerauflösung
Ist-Temperatur
Temperatur-Sollwert
```

Die zahlreichen weiteren Funktionen der vollständigen MEMMERT-Schnittstelle sind für den konkreten IPP300 nicht erforderlich und müssen daher nicht Teil der ersten Implementierung sein.

---

## 21. Relevanz für die LoggerPi-Architektur

Die MEMMERT-Kommunikation ist ein Request/Response-Protokoll über eine serielle Verbindung.

Für den konkret untersuchten IPP300 ist für den ersten Adapter lediglich ein kleiner Read-only-Subset erforderlich:

```text
MemmertAdapter
      │
      └── SerialTransport
            │
            ├── 2400 8N1
            ├── no flow control
            └── /dev/ttyUSB*
                  │
                  ▼
            MemmertProtocol
                  │
                  ├── IN_MODE_10
                  ├── IN_PAR_11
                  ├── IN_PV_11
                  └── IN_SP_11
```

Der Transport kennt ausschließlich die serielle Verbindung.

Das Protokoll übernimmt:

- Request-Erzeugung
- CR/LF-Framing
- Response-Parsing
- `OK`-Antworten
- `ERR_##`-Antworten
- Konvertierung der Temperaturwerte
- Geräteadresse

Eine generische Implementierung sämtlicher dokumentierter MEMMERT-Befehle ist für den ersten Adapter nicht erforderlich.

Die vollständige Herstellerbefehlsliste bleibt in der Research-Dokumentation erhalten, wird aber bewusst nicht vollständig in Software abgebildet.

### Vorgesehene Gerätekonfiguration

Die beiden vorhandenen IPP300 sollen über die stabilen udev-Namen
angesprochen werden.

```yaml
memmert:
  devices:
    - id: memmert_ipp300_links
      port: /dev/memmert_ipp300_links
      address: 1

    - id: memmert_ipp300_rechts
      port: /dev/memmert_ipp300_rechts
      address: 2
```

Dabei haben die beiden Ebenen unterschiedliche Aufgaben:

- `id` ist die LoggerPi-seitige logische Geräteidentität.
- `port` identifiziert den stabilen Linux-Gerätepfad.
- `address` ist die logische MEMMERT-Geräteadresse innerhalb des
  MEMMERT-Protokolls.

Aktuelle Zuordnung:

```text
memmert_ipp300_links
    port: /dev/memmert_ipp300_links
    address: 1
    USB topology: 1-1.4
    aktueller Testwert: 14,1 °C

memmert_ipp300_rechts
    port: /dev/memmert_ipp300_rechts
    address: 2
    USB topology: 1-1.5
    aktueller Testwert: 24,0 °C
```

Die Anwendung soll nicht von `/dev/ttyUSB1` oder `/dev/ttyUSB2`
abhängen.

---

## 22. Aktueller Erkenntnisstand

Die Kommunikation des MEMMERT IPP300 über das USB Interface B04118 ist sowohl durch die Herstellerdokumentation als auch praktisch am real vorhandenen Gerät verifiziert.

### Durch Herstellerdokumentation bestätigt

- Der Controller kommuniziert intern über RS-232.
- Das Interface B04118 setzt RS-232 auf USB um.
- Das MEMMERT-Protokoll ist dokumentiert.
- Die Kommunikation erfolgt nach NAMUR.
- Die seriellen Parameter sind 2400 Baud, 8N1.
- Es wird kein Hardware- oder Software-Handshake verwendet.
- Die Übertragung ist halbduplex.
- Befehle werden mit CR/LF abgeschlossen.
- Geräte besitzen eine Adresse von 0 bis F.
- Das Protokoll verwendet Statusantworten `OK` bzw. `ERR_##`.
- Istwerte können über `IN_PV_*` abgefragt werden.
- Sollwerte können über `IN_SP_*` abgefragt werden.
- Konfigurationsmerkmale können über `IN_PAR_*` abgefragt werden.
- Schreib- und Steuerbefehle existieren über `OUT_MODE_*` und `OUT_SP_*`.

### Praktisch am IPP300 verifiziert

- B04118 wird unter Linux als `/dev/ttyUSB1` bereitgestellt.
- 2400 Baud, 8N1 funktionieren.
- Kein Flow-Control ist erforderlich.
- Das getestete Gerät verwendet Adresse `1`.
- `IN_MODE_10` funktioniert.
- `IN_PAR_11` funktioniert.
- `IN_PV_11` funktioniert.
- `IN_SP_11` funktioniert.
- Das erwartete Response-Format wurde bestätigt.
- Die vollständige Read-only-Inventur wurde durchgeführt.
- Die optionalen Funktionen des konkreten Gerätes sind nicht vorhanden.
- 20/20 Timing-Test-Requests waren erfolgreich.
- Die mittlere Antwortzeit betrug 122,39 ms.

### Für den konkreten IPP300 relevante Befehle

```text
IN_MODE_10   Betriebsart
IN_PAR_11    Reglerauflösung
IN_PV_11     Ist-Temperatur
IN_SP_11     Temperatur-Sollwert
```

### Für den konkreten IPP300 nicht relevante Funktionen

Laut `IN_PAR_*` Inventur nicht vorhanden:

```text
Luftklappensteuerung
Luftturbine
Schaltkontakte 1–3
zweite Temperatur
Druck/Vakuum
```

Die entsprechenden Herstellerbefehle bleiben als Referenz dokumentiert, werden aber nicht Bestandteil des ersten Adapters.

### Sicherheitsstatus

Es wurden ausschließlich `IN_*` Befehle ausgeführt.

Keine der folgenden Operationen wurde auf dem produktiven Gerät durchgeführt:

```text
OUT_MODE_*
OUT_SP_*
```

Insbesondere wurde kein REMOTE-Modus über die serielle Schnittstelle aktiviert und kein Sollwert verändert.

### Nicht mehr notwendig

Ein Reverse Engineering des MEMMERT-Kommunikationsprotokolls ist nicht erforderlich.

Ebenso besteht derzeit kein Grund, ein proprietäres USB-Protokoll zu reverse engineeren.

Die technische Untersuchung hat damit den Punkt erreicht, an dem die Implementierung des read-only `MemmertAdapter` beginnen kann.

### Noch offen

- Fehler- und Disconnect-Handling implementieren
- Polling-Intervall festlegen
- Adapter in LoggerPi integrieren
- Normalisierung der MEMMERT-Werte in das gemeinsame Measurement-Modell
- praktischen End-to-End-Betrieb testen

### Inzwischen zusätzlich verifiziert

- zweites IPP300 wurde eindeutig identifiziert
- zweites IPP300 verwendet MEMMERT-Adresse `2`
- erstes IPP300 verwendet MEMMERT-Adresse `1`
- `/dev/ttyUSB1` entspricht aktuell dem physischen USB-Pfad `1-1.4`
- `/dev/ttyUSB2` entspricht aktuell dem physischen USB-Pfad `1-1.5`
- beide USB-Adapter sind Prolific `067b:2303`
- beide Adapter besitzen keine individuelle `ID_SERIAL_SHORT`
- stabile udev-Symlinks wurden eingerichtet
- `/dev/memmert_ipp300_links` verweist aktuell auf `/dev/ttyUSB1`
- `/dev/memmert_ipp300_rechts` verweist aktuell auf `/dev/ttyUSB2`
- die Zuordnung wurde mit `readlink -f` verifiziert
- der physische USB-Port ist damit als Host-seitige Identifikation
  der beiden aktuell fest verdrahteten Adapter dokumentiert

Die detaillierte Linux-/udev-Untersuchung befindet sich unter:

```text
docs/research/memmert-ipp300-linux-usb-identity.md
```

### Primärquelle

```text
docs/research/sources/MEMMERT_IPP300_Beschreibung_RS232-2010.pdf
```

**Schnittstellenbeschreibung für MEMMERT-Wärmeschränke mit Temperaturregler der E- oder P-Klasse, Stand April 2011.**

### Praktische Testartefakte

```text
docs/research/sources/memmert_ipp300_inventory.py
docs/research/sources/memmert_ipp300_timing_test.py
```
