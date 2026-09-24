# Research: TFA WeatherHub / MOBILE-ALERTS Gateway-Proxy

**Projekt:** LoggerPi → OtterPi  
**Subprojekt:** WeatherHub / MOBILE-ALERTS Gateway  
**Status:** Gateway-Transport und Konfigurationszugriff reproduziert;
Name-only-Schreibtest erfolgreich; produktiver Sensor-Proxy noch nicht aktiviert  
**Stand:** 2026-09-24  
**Zweck:** Untersuchung eines lokalen Gateway-Proxy-Datenpfads für
TFA-WeatherHub-/MOBILE-ALERTS-Sensoren

---

## 1. Ziel

Die vorhandenen MOBILE-ALERTS-/WeatherHub-Gateways empfangen die Funkdaten
der Sensoren und übertragen sie normalerweise an die TFA-/Mobile-Alerts-
Cloud:

```text
WeatherHub-Sensoren
        ↓ Funk
MOBILE-ALERTS-Gateway
        ↓
www.data199.com
```

Die Gateway-Firmware unterstützt zusätzlich einen Proxybetrieb. Ziel der
Untersuchung ist, die Sensordaten lokal am LoggerPi abzufangen und später in
das bestehende LoggerPi-OtterPi-Datenmodell zu integrieren.

Der geplante lokale Datenpfad lautet:

```text
WeatherHub-Sensoren
        ↓ Funk
MOBILE-ALERTS-Gateway
        ↓ HTTP PUT /gateway/put
LoggerPi-Proxy
        ↓
WeatherHub-Gateway-Decoder
        ↓
WeatherHub-Adapter
        ↓
normalisierte Measurements
        ↓
Core Batch
        ↓
OtterPi
```

Der Gateway-Proxy soll den bestehenden LoggerPi-→-OtterPi-Pushpfad nicht
ersetzen. Der Gateway-Listener soll zunächst nur eine zusätzliche
LoggerPi-Datenquelle bereitstellen.

Eine spätere optionale Cloud-Semiredundanz ist vorgesehen:

```text
Gateway
    ↓
LoggerPi-Proxy
    ├── lokale Dekodierung
    ├── LoggerPi → OtterPi
    └── optionaler Forward an www.data199.com
```

Der Cloud-Forward ist noch nicht implementiert und noch nicht praktisch
verifiziert.

---

## 2. Abgrenzung zum bisherigen Portalzugriff

Es existieren zwei getrennte WeatherHub-Datenwege.

### 2.1 Portal-/Sparkline-Weg

Der bereits untersuchte Portalweg lautet:

```text
LoggerPi
    ↓ Login
www.wh-observer.de
    ↓
GET /Devices
    ↓
POST /Devices/SparkLineChartData
    ↓
Base64-/protobuf-artige Payload
    ↓
Decoder
```

Dieser Weg ist in folgendem Dokument beschrieben:

```text
docs/research/weatherhub-observer.md
```

### 2.2 Lokaler Gateway-Proxy-Weg

Der hier dokumentierte Weg lautet:

```text
WeatherHub-Sensor
    ↓ Funk
Gateway
    ↓
PUT /gateway/put
    ↓
LoggerPi-Proxy
    ↓
binäre Sensorpayload
```

Dieser Weg benötigt keinen Login bei `www.wh-observer.de`.

Die beiden Wege werden zunächst getrennt behandelt:

```text
weatherhub-observer.md
    → Portalzugriff und SparkLineChartData

weatherhub-gateway-proxy.md
    → lokaler Gateway-Proxy und Binärprotokoll
```

---

## 3. Beteiligte Gateways

### 3.1 Gateway 1 – Experimentgateway

```text
IP:                  141.51.190.121
Aktueller Name:      ZOOLOGY-TEST
Ursprünglicher Name: ZOOLOGY-observ2
Gateway-ID/MAC:      00-1D-8C-0D-F8-1C
Seriennummer:        800DF81C
Software:            MOBILE-ALERTS-Gateway V1.50.00
Compilation:         02/11/15 10:50:00
DHCP:                No
Netmask:             255.255.255.0
Gateway:             141.51.190.1
DNS:                 141.51.8.4
Data Server:         www.data199.com
Use Proxy:           No
Proxy Host:          192.168.1.1
Proxy Port:          80
RF Channel:          2
```

Dieses Gateway wird ausschließlich für kontrollierte Experimente verwendet.

Der Name wurde in einem kontrollierten, minimalinvasiven Schreibtest
geändert:

```text
ZOOLOGY-observ2
        ↓
ZOOLOGY-TEST
```

Alle anderen bekannten Konfigurationswerte blieben unverändert.

Aktuell gilt weiterhin:

```text
Use Proxy: No
```

### 3.2 Gateway 2 – unverändert

```text
IP:                  141.51.190.132
Name:                MOBILEALERTS-Gateway
Gateway-ID/MAC:      00-1D-8C-0D-E5-4F
Seriennummer:        800DE54F
Software:            MOBILE-ALERTS-Gateway V1.50.00
Compilation:         02/11/15 10:50:00
DHCP:                No
Netmask:             255.255.255.0
Gateway:             141.51.190.1
DNS:                 141.51.8.4
Data Server:         www.data199.com
Use Proxy:           No
Proxy Host:          192.168.1.1
Proxy Port:          80
RF Channel:          2
```

Gateway `.132` wurde während der Untersuchung nicht verändert.

---

## 4. Netzwerk

Der Windows-Entwicklungsrechner:

```text
141.51.190.135
```

Der LoggerPi:

```text
141.51.190.103
```

Die Gateways, der LoggerPi und der Windows-Rechner befinden sich im
gleichen IPv4-/24-Netz:

```text
141.51.190.0/24
```

Die Gateway-Webinterfaces sind über TCP-Port 80 erreichbar:

```text
141.51.190.121:80
141.51.190.132:80
```

Der vorgesehene LoggerPi-Proxy-Port ist:

```text
141.51.190.103:3778
```

Port `3778` war auf dem LoggerPi zunächst frei.

Ein manueller Testlistener wurde auf diesem Port gestartet. Die
Erreichbarkeit vom Windows-Rechner wurde erfolgreich geprüft:

```text
TcpTestSucceeded: True
```

---

## 5. Referenzquellen

### 5.1 Primäre Protokolldokumentation

Zentrale Referenz:

```text
https://github.com/sarnau/MMMMobileAlerts
```

Relevante Dokumente:

```text
MobileAlerts.markdown
MobileAlertsGateway.markdown
MobileAlertsGatewayUDPInterface.markdown
MobileAlertsGatewayWebInterface.markdown
MobileAlertsGatewayBinaryUpload.markdown
MobileAlertsDevices.markdown
MobileAlertsGatewayRESTAPI.markdown
MobileAlertsGatewayApplicationAPI.markdown
MobileAlertsWebsite.markdown
MobileAlertsSensorQRCode.markdown
```

Die Dokumentation beschreibt unter anderem:

- Gateway-Identität
- Gateway-Webinterface
- UDP-Konfigurationsprotokoll
- Gateway-Upload zur Cloud
- Sensorpakete
- Sensor-ID-Typen
- Sensorwertdekodierung
- Cloud- und Application-API
- historische beziehungsweise vorherige Sensorwerte

### 5.2 Zweite Referenzimplementierung

Zusätzliche Referenzimplementierung:

```text
https://github.com/Black-Blade/TFA_WeatherHub.git
```

Untersuchte Bereiche:

```text
tfa_gateway/
tfa_http_gateway/
tfa_sensor_01/
tfa_sensor_02/
tfa_sensor_03/
tfa_sensor_04/
tfa_sensor_06/
tfa_sensor_07/
tfa_sensor_08/
tfa_sensor_0b/
tfa_sensor_0e/
tfa_sensor_10/
tfa_sensor_11/
libs/
```

Die PHP-Implementierung diente als technische Referenz für:

- Gateway-HTTP-Proxy
- HTTP-Framing
- `HTTP_IDENTIFY`
- `Content-Length`
- 64-Byte-Paketzerlegung
- CRC-Prüfung
- Gateway-Timestamp
- Gateway-/Sensor-ID
- Sensorfamilien-Decoder
- Gateway-Konfigurationszugriff
- Gateway-Konfigurationsantwort
- optionalen Cloud-Forward

Die PHP-Referenzimplementierung ist keine direkte Vorlage für
produktiven LoggerPi-Code. Sie dokumentiert den beobachteten Transport
und die bekannten Payload-Strukturen.

---

## 6. Gateway-Webinterface

Die Gateways liefern eine ältere HTTP/0.9-artige Antwort.

Mit PowerShell `Invoke-WebRequest` war der Zugriff nicht zuverlässig
verarbeitbar. Mit `curl.exe` funktioniert der Abruf:

```cmd
curl.exe --http0.9 http://141.51.190.121/ ^
  -o "C:\Users\LH\Desktop\gateway_141_51_190_121_current.html"
```

Das Webinterface enthält unter anderem:

```text
Software
Compilation Date
Compilation Time
Serial No. (hex.)
Serial No. (dec.)
Name
Registration state
Use DHCP
Fixed IP
Fixed Netmask
Fixed Gateway
Fixed DNS IP
DHCP valid
DHCP IP
DHCP Netmask
DHCP Gateway
DHCP DNS
DNS states
Data Server Name
Use Proxy
Proxy Server Name
Proxy Port
Data Server IP
Last contact
RF channel
Time
```

Das Webinterface wurde read-only ausgelesen.

### 6.1 Referenzdateien für Gateway 1

Vor dem Schreibtest wurden erstellt:

```text
C:\Users\LH\Desktop\gateway_141_51_190_121_before.html
C:\Users\LH\Desktop\gateway_141_51_190_121_BACKUP.json
```

Beim Vergleich der HTML-Dateien änderten sich erwartungsgemäß nur dynamische
Werte wie:

```text
Last contact
Time
```

Diese Änderungen sind kein Hinweis auf eine Änderung der statischen
Netzwerk- oder Proxy-Konfiguration.

---

## 7. Gateway-Identität

Die Gateway-ID/MAC und die Gateway-Seriennummer sind unterschiedliche Werte.

Beispiel Gateway 1:

```text
Gateway-ID/MAC: 00 1D 8C 0D F8 1C
Seriennummer:   80 0D F8 1C
```

Im UDP-Konfigurationsprotokoll wird die sechs Byte lange Gateway-ID/MAC
verwendet:

```text
00 1D 8C 0D F8 1C
```

Die Seriennummer wird getrennt behandelt.

Beispiel Gateway 2:

```text
Gateway-ID/MAC: 00 1D 8C 0D E5 4F
Seriennummer:   80 0D E5 4F
```

---

## 8. UDP-Konfigurationsprotokoll

Die Gateways besitzen eine lokale UDP-Konfigurationsschnittstelle auf
Port `8003`.

Laut Referenzdokumentation werden die Pakete an den Broadcast gesendet:

```text
255.255.255.255:8003
```

### 8.1 Allgemeiner Header

```text
Offset 0..1   Command, Big-Endian
Offset 2..7   Gateway-ID, 6 Bytes
Offset 8..9   Gesamtlänge, Big-Endian
```

### 8.2 Commands

```text
1  Discovery aller Gateways
2  Suche eines bestimmten Gateways
3  Get Config
4  Set Config
5  Reboot
```

### 8.3 Erste UDP-Tests

Die ersten Tests mit Command 1 und Command 2 verwendeten die falsche
Gateway-ID-Darstellung und lieferten nur das eigene Broadcast-Paket zurück.

Die Ursache war die Verwechslung von:

```text
Gateway-Seriennummer
```

und:

```text
sechs Byte Gateway-ID/MAC
```

Mit der korrekten MAC-basierten Gateway-ID funktionierte Command 2.

---

## 9. Read-only-Get-Config-Test

### 9.1 Gateway 1

Request:

```text
00 02 00 1D 8C 0D F8 1C 00 0A
```

Antwort:

```text
Quelle:              141.51.190.121:8003
Command:             3
Tatsächliche Länge:  186 Bytes
Deklarierte Länge:   186 Bytes
Gateway-ID:          00-1D-8C-0D-F8-1C
```

### 9.2 Gateway 2

Request:

```text
00 02 00 1D 8C 0D E5 4F 00 0A
```

Antwort:

```text
Quelle:              141.51.190.132:8003
Command:             3
Tatsächliche Länge:  186 Bytes
Deklarierte Länge:   186 Bytes
Gateway-ID:          00-1D-8C-0D-E5-4F
```

Damit ist der read-only UDP-Konfigurationszugriff für beide Gateways
praktisch verifiziert.

---

## 10. Get-Config-Paket

Ein `Command 3`-Paket ist 186 Bytes lang.

Struktur:

| Offset | Länge | Bedeutung |
|---:|---:|---|
| 0 | 2 | Command `3` |
| 2 | 6 | Gateway-ID |
| 8 | 2 | Gesamtlänge `186` |
| 10 | 1 | unbekannt, bisher `0` |
| 11 | 4 | DHCP-IP |
| 15 | 1 | Use DHCP |
| 16 | 4 | Fixed IP |
| 20 | 4 | Netmask |
| 24 | 4 | Gateway |
| 28 | 21 | Gateway-Name |
| 49 | 65 | Data-Server-Name |
| 114 | 1 | Use Proxy |
| 115 | 65 | Proxy-Server |
| 180 | 2 | Proxy-Port |
| 182 | 4 | DNS |

Mehrbytewerte sind Big-Endian.

---

## 11. Set-Config-Paket

Ein `Command 4`-Paket ist 181 Bytes lang.

Die fünf Bytes gegenüber `Command 3` entfallen, weil DHCP-IP und das
unbekannte Byte nicht Bestandteil des Schreibpakets sind.

Struktur:

| Offset | Länge | Bedeutung |
|---:|---:|---|
| 0 | 2 | Command `4` |
| 2 | 6 | Gateway-ID |
| 8 | 2 | Gesamtlänge `181` |
| 10 | 1 | Use DHCP |
| 11 | 4 | Fixed IP |
| 15 | 4 | Netmask |
| 19 | 4 | Gateway |
| 23 | 21 | Gateway-Name |
| 44 | 65 | Data-Server-Name |
| 109 | 1 | Use Proxy |
| 110 | 65 | Proxy-Server |
| 175 | 2 | Proxy-Port |
| 177 | 4 | DNS |

---

## 12. Kontrollierter Name-only-Schreibtest

Für Gateway 1 wurde ein `Command 4`-Paket aus der live ausgelesenen
`Command 3`-Antwort erzeugt.

Die einzige beabsichtigte Änderung war:

```text
ZOOLOGY-observ2
        ↓
ZOOLOGY-TEST
```

Unverändert blieben:

```text
Use DHCP
Fixed IP
Netmask
Gateway
Data Server
Use Proxy
Proxy Host
Proxy Port
DNS
```

Das Paket wurde semantisch validiert:

```text
Command:       4
Länge:         181 Bytes
Gateway-ID:    00-1D-8C-0D-F8-1C
Name:          ZOOLOGY-TEST
Use Proxy:     0
Proxy Host:    192.168.1.1
Proxy Port:    80
```

SHA-256 des Testpakets:

```text
AE2866B9B42D849BD351DC7547354AB3EA8F77F79407B3D3F2BF14513F5D30C5
```

Das Paket wurde über einen lokal auf `141.51.190.135:8003` gebundenen
UDP-Socket als Broadcast gesendet.

Anschließender read-only-Webabruf:

```html
<TR><TD>Name</TD><TD>ZOOLOGY-TEST</TD></TR>
```

Damit ist praktisch verifiziert:

- `Command 4` wird akzeptiert.
- Die Paketlänge `181` ist korrekt.
- Die Gateway-ID ist korrekt.
- Der UDP-Schreibtransport funktioniert.
- Der Gateway-Name kann kontrolliert geändert werden.
- Proxy- und Cloud-Konfiguration bleiben unverändert.
- Kein Gateway-Reboot wurde ausgelöst.

---

## 13. Gateway-Sensorupload

Der Gateway-Sensorupload verwendet HTTP über den konfigurierten Data
Server beziehungsweise Proxy:

```http
PUT http://www.data199.com/gateway/put HTTP/1.1
Host: www.data199.com
Connection: close
HTTP_IDENTIFY:<gateway-serial>:<gateway-mac>:C0
Content-Type: application/octet-stream
Content-Length:<length>

<binäre Nutzdaten>
```

Der LoggerPi-Proxy muss mit HTTP `200 OK` und 24 Binärbytes antworten.

Referenzstruktur:

```http
HTTP/1.1 200 OK
Pragma: no-cache
Content-Length: 24
Content-Type: application/octet-stream
Expires: -1
Connection: close
```

Die Antwort enthält 24 Binärbytes. Die Bytes 8 bis 11 werden mit einem
aktuellen Unix-Zeitwert belegt.

---

## 14. Gateway-Uploadtypen

Der Gateway-Code unterscheidet mindestens folgende Payload-Längen:

```text
15 Bytes       Boot-/Kontrollpaket
64*n Bytes     Sensorpakete
```

Nicht jede eingehende Payload ist deshalb ein Sensorpaket.

Der Listener muss zunächst unterscheiden:

```text
len(body) == 15
    → Boot-/Kontrollpaket

len(body) % 64 == 0
    → Sensorpaketblock

sonstige Länge
    → unbekanntes oder fehlerhaftes Format
```

Ein 15-Byte-Bootpaket enthält laut Referenz:

```text
Byte 0       Paketlänge
Byte 1..4    Sekunden seit Gateway-Boot
Byte 5..10   Gateway-ID
Byte 11..12  weiterer Wert
Byte 13..14  weiterer Wert
```

---

## 15. Sensorpakete

Normale Sensordaten bestehen aus einem Vielfachen von 64 Bytes.

Ein 64-Byte-Paket enthält:

| Offset | Bedeutung |
|---:|---|
| 0 | Package Header |
| 1..4 | Unix-UTC-Timestamp, Big-Endian |
| 5 | Package Length |
| 6..11 | Sensor-ID, sechs Bytes |
| 12..62 | Sensor-Nutzdaten |
| 63 | 7-Bit-Checksumme |

CRC-Prüfung:

```python
(sum(packet[0:63]) & 0x7F) == packet[63]
```

Die Nutzdatenlänge ergibt sich aus:

```python
payload_length = packet[5] - 12
```

Die Sensor-ID enthält den ID-Typ im ersten Byte:

```text
Device-ID Byte 0
    → Sensorfamilie

Device-ID Bytes 1..5
    → individuelle Sensoridentität
```

---

## 16. Gemeinsame Wertdekodierung

### 16.1 Transmit Counter und Status

Bei Sensorfamilien mit zweibyte-langem Statusbereich:

```python
battery_low = (byte0 & 0x80) != 0
event_transmission = (byte0 & 0x40) != 0
counter = ((byte0 & 0x3F) << 8) | byte1
```

Bei ID0B ist der Counter drei Bytes lang:

```python
battery_low = (byte0 & 0x80) != 0
event_transmission = (byte0 & 0x40) != 0
counter = ((byte0 & 0x3F) << 16) | (byte1 << 8) | byte2
```

### 16.2 Temperatur

```python
raw = ((byte0 & 0x07) << 8) | byte1
```

```text
0..1023      → raw * 0.1 °C
1024..2047   → (2048 - raw) * -0.1 °C
```

Statusbits:

```text
Bit 13       overflow
Bit 12       sensor error
Bits 0..10   Temperaturwert
```

### 16.3 Standard-Feuchte

```python
humidity = byte1 & 0x7F
```

### 16.4 Feuchte mit Dezimalstelle

```python
raw = ((byte0 & 0x03) << 8) | byte1
humidity = raw / 10
```

---

## 17. Sensorfamilie ID01

```text
ID-Typ:           01
Package Header:   0xD2
Gesamtpaketlänge: 0x16 = 22 Bytes
Nutzdatenlänge:   10 Bytes
```

Payload:

```text
Payload 0..1   Batterie, Heartbeat, Counter
Payload 2..3   aktuelle Temperatur intern
Payload 4..5   aktuelle Temperatur Kabelsensor
Payload 6..7   vorherige Temperatur intern
Payload 8..9   vorherige Temperatur Kabelsensor
```

Aktuelle Measurements:

```text
temperature_1 → interne Temperatur
temperature_2 → externe Kabeltemperatur
```

Vorläufiges Mapping:

```text
weatherhub_<device_id>.temperature_1
weatherhub_<device_id>.temperature_2
```

---

## 18. Sensorfamilie ID02

```text
ID-Typ:           02
Package Header:   0xCE
Gesamtpaketlänge: 0x12 = 18 Bytes
Nutzdatenlänge:   6 Bytes
```

Payload:

```text
Payload 0..1   Batterie, Heartbeat, Counter
Payload 2..3   aktuelle Temperatur
Payload 4..5   vorherige Temperatur
```

Aktuelle Measurement:

```text
temperature
```

Mapping:

```text
weatherhub_<device_id>.temperature
```

---

## 19. Sensorfamilie ID03

```text
ID-Typ:           03
Package Header:   0xD2
Gesamtpaketlänge: 0x16 = 22 Bytes
Nutzdatenlänge:   10 Bytes
```

Payload:

```text
Payload 0..1   Batterie, Heartbeat, Counter
Payload 2..3   aktuelle Temperatur
Payload 4..5   aktuelle Feuchte
Payload 6..7   vorherige Temperatur
Payload 8..9   vorherige Feuchte
```

Aktuelle Measurements:

```text
temperature
humidity
```

Units:

```text
temperature → celsius
humidity    → percent
```

---

## 20. Sensorfamilie ID04

```text
ID-Typ:           04
Package Header:   0xD4
Gesamtpaketlänge: 0x18 = 24 Bytes
Nutzdatenlänge:   12 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    aktuelle Temperatur
Payload 4..5    aktuelle Feuchte
Payload 6       aktueller Wasserkontakt
Payload 7..8    vorherige Temperatur
Payload 9..10   vorherige Feuchte
Payload 11      vorheriger Wasserkontakt
```

Aktuelle Measurements:

```text
temperature
humidity
```

Der Wasserkontakt ist ein State-/Event-Kandidat, kein physikalisches
Measurement.

---

## 21. Sensorfamilie ID06

```text
ID-Typ:           06
Package Header:   0xD6
Gesamtpaketlänge: 0x1A = 26 Bytes
Nutzdatenlänge:   14 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    aktuelle Umgebungstemperatur
Payload 4..5    aktuelle Pooltemperatur
Payload 6..7    aktuelle Feuchte
Payload 8..9    vorherige Umgebungstemperatur
Payload 10..11  vorherige Pooltemperatur
Payload 12..13  vorherige Feuchte
```

Aktuelle Measurements:

```text
temperature
pool_temperature
humidity
```

Units:

```text
temperature      → celsius
pool_temperature → celsius
humidity         → percent
```

---

## 22. Sensorfamilie ID07

```text
ID-Typ:           07
Package Header:   0xDA
Gesamtpaketlänge: 0x1E = 30 Bytes
Nutzdatenlänge:   18 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    aktuelle Innentemperatur
Payload 4..5    aktuelle Innenfeuchte
Payload 6..7    aktuelle Außentemperatur
Payload 8..9    aktuelle Außenfeuchte
Payload 10..11  vorherige Innentemperatur
Payload 12..13  vorherige Innenfeuchte
Payload 14..15  vorherige Außentemperatur
Payload 16..17  vorherige Außenfeuchte
```

Aktuelle Measurements:

```text
temperature_indoor
humidity_indoor
temperature_outdoor
humidity_outdoor
```

---

## 23. Sensorfamilie ID08

```text
ID-Typ:           08
Package Header:   0xE1
Gesamtpaketlänge: 0x25 = 37 Bytes
Nutzdatenlänge:   25 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    Temperatur + Positions-/Statusbits
Payload 4..5    Regenzähler
Payload 6..7    Zeit seit aktuellem Regenereignis
Payload 8..9    vorherige Ereigniszeit
Payload 10..11  vorherige Ereigniszeit 1
Payload 12..13  vorherige Ereigniszeit 2
Payload 14..15  vorherige Ereigniszeit 3
Payload 16..17  vorherige Ereigniszeit 4
Payload 18..19  vorherige Ereigniszeit 5
Payload 20..21  vorherige Ereigniszeit 6
Payload 22..23  vorherige Ereigniszeit 7
Payload 24      bisher nicht eindeutig ausgewertet
```

Aktuelle Measurement:

```text
temperature
```

Der Regenzähler benötigt persistenten Zustand:

```text
current_counter
    -
previous_counter
    =
new_rain_ticks
```

Eine produktive Regenmengenintegration benötigt:

- persistente Zählerverwaltung,
- Behandlung von Counter-Überläufen,
- Definition der Regenmengen-Unit,
- spätere Event-/State-Definition.

ID08 wird zunächst nur im Decoder vorbereitet.

---

## 24. Sensorfamilie ID0B

```text
ID-Typ:           0B
Package Header:   0xE2
Gesamtpaketlänge: 0x26 = 38 Bytes
Nutzdatenlänge:   26 Bytes
```

Payload:

```text
Payload 0..2    Batterie, Heartbeat, 3-Byte-Counter
Payload 3..6    aktuelle Winddaten
Payload 7..10   vorherige Winddaten
Payload 11..14  vorherige Winddaten 1
Payload 15..18  vorherige Winddaten 2
Payload 19..22  vorherige Winddaten 3
Payload 23..25  vorherige Winddaten 4, ohne lasttransmit
```

Aktuelle Winddaten:

```text
payload[3:7]
```

### Windrichtung

```python
direction_index = (byte0 & 0xF0) >> 4
direction_degrees = direction_index * 22.5
```

### Windgeschwindigkeit

```python
high_bit = (byte0 & 0x02) >> 1
windspeed = ((high_bit << 8) | byte1) / 10
```

Unit:

```text
m/s
```

### Böengeschwindigkeit

```python
high_bit = byte0 & 0x01
gustspeed = ((high_bit << 8) | byte2) / 10
```

Unit:

```text
m/s
```

Aktuelle Measurements:

```text
wind_direction
wind_speed
gust_speed
```

---

## 25. Sensorfamilie ID0E

```text
ID-Typ:           0E
Package Header:   0xD8
Gesamtpaketlänge: 0x1C = 28 Bytes
Nutzdatenlänge:   16 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    aktuelle Temperatur
Payload 4..5    aktuelle Feuchte mit Dezimalstelle
Payload 6..7    vorherige Temperatur
Payload 8..9    vorherige Feuchte mit Dezimalstelle
Payload 10..11  weitere vorherige Temperatur
Payload 12..13  weitere vorherige Feuchte
Payload 14..15  bisher nicht ausgewertet
```

Aktuelle Measurements:

```text
temperature
humidity
```

Feuchte:

```python
raw = ((byte0 & 0x03) << 8) | byte1
humidity = raw / 10
```

---

## 26. Sensorfamilie ID10

```text
ID-Typ:           10
Package Header:   0xD3
Gesamtpaketlänge: 0x17 = 23 Bytes
Nutzdatenlänge:   11 Bytes
```

Payload:

```text
Payload 0..1    Batterie, Heartbeat, Counter
Payload 2..3    aktueller Tür-/Fensterzustand + Zeitinformation
Payload 4..5    vorheriger Zustand + Zeitinformation
Payload 6..7    vorheriger Zustand 1 + Zeitinformation
Payload 8..9    vorheriger Zustand 2 + Zeitinformation
Payload 10      vorheriger Zustand 3, teilweise ausgewertet
```

ID10 ist primär für States/Events relevant und liefert kein reguläres
physikalisches Measurement.

Vorläufig:

```text
0 → geschlossen
1 → geöffnet
```

Die endgültige Modellierung bleibt offen.

---

## 27. Sensorfamilie ID11

```text
ID-Typ:           11
Package Header:   0xEA
Gesamtpaketlänge: 0x2E = 46 Bytes
Nutzdatenlänge:   34 Bytes
```

Payload:

```text
Payload 0..1     Batterie, Heartbeat, Counter

Payload 2..3     aktuelle Temperatur 1
Payload 4..5     aktuelle Feuchte 1

Payload 6..7     aktuelle Temperatur 2
Payload 8..9     aktuelle Feuchte 2

Payload 10..11   aktuelle Temperatur 3
Payload 12..13   aktuelle Feuchte 3

Payload 14..15   aktuelle Innentemperatur
Payload 16..17   aktuelle Innenfeuchte

Payload 18..19   vorherige Temperatur 1
Payload 20..21   vorherige Feuchte 1
Payload 22..23   vorherige Temperatur 2
Payload 24..25   vorherige Feuchte 2
Payload 26..27   vorherige Temperatur 3
Payload 28..29   vorherige Feuchte 3
Payload 30..31   vorherige Innentemperatur
Payload 32..33   vorherige Innenfeuchte
```

Aktuelle Measurements:

```text
temperature_1
humidity_1
temperature_2
humidity_2
temperature_3
humidity_3
temperature_indoor
humidity_indoor
```

Die physische Bedeutung der drei externen Kanäle wird über Sensor-Metadata
geführt.

---

## 28. Übersicht aller bekannten Sensorfamilien

| ID | Header | Gesamtpaket | Nutzdaten | Aktuelle Daten |
|---|---:|---:|---:|---|
| `01` | `0xD2` | 22 | 10 | Temperatur intern, Kabeltemperatur |
| `02` | `0xCE` | 18 | 6 | Temperatur |
| `03` | `0xD2` | 22 | 10 | Temperatur, Feuchte |
| `04` | `0xD4` | 24 | 12 | Temperatur, Feuchte, Wasserzustand |
| `06` | `0xD6` | 26 | 14 | Temperatur, Pooltemperatur, Feuchte |
| `07` | `0xDA` | 30 | 18 | Innen-/Außentemperatur und Feuchte |
| `08` | `0xE1` | 37 | 25 | Temperatur, Regenzähler, Ereigniszeiten |
| `0B` | `0xE2` | 38 | 26 | Windrichtung, Wind, Böen |
| `0E` | `0xD8` | 28 | 16 | Temperatur, Feuchte |
| `10` | `0xD3` | 23 | 11 | Tür-/Fensterzustand, Ereigniszeit |
| `11` | `0xEA` | 46 | 34 | vier Temperatur-/Feuchte-Kanalpaare |

Die allgemeine Beziehung lautet:

```text
Gesamtpaketlänge = Nutzdatenlänge + 12
```

---

## 29. Zeitmodell

Der Gateway-Payload enthält einen Gateway-Timestamp:

```text
Unix-UTC-Timestamp
```

Nach DEC-032 wird dieser Timestamp zunächst nicht als
`Measurement.measured_at` verwendet.

Für den Core Batch gilt:

```text
measured_at = LoggerPi-Empfangszeit UTC
```

Der Gateway-Timestamp bleibt im internen WeatherHub-Zwischenmodell
erhalten und kann später für:

- Diagnose,
- Übertragungslatenz,
- Plausibilisierung,
- Sensorereigniszeiten

verwendet werden.

`received_at` bleibt ausschließlich OtterPi-seitig und darf nicht vom
LoggerPi gesetzt werden.

---

## 30. Geplante Softwarearchitektur

```text
WeatherHubGatewayListener
    ├── TCP-Listener
    ├── HTTP-Framing
    ├── HTTP_IDENTIFY
    ├── Content-Length
    ├── Gateway-Allowlist
    └── HTTP-200-Antwort

WeatherHubGatewayDecoder
    ├── Bootpaket
    ├── 64-Byte-Pakete
    ├── CRC
    ├── Timestamp
    ├── Device-ID
    └── rohe Sensor-Payload

WeatherHubSensorDecoder
    ├── ID01
    ├── ID02
    ├── ID03
    ├── ID04
    ├── ID06
    ├── ID07
    ├── ID08
    ├── ID0B
    ├── ID0E
    ├── ID10
    └── ID11

WeatherHubAdapter
    ├── Sensoridentität
    ├── Mapping
    ├── Measurement-Erzeugung
    └── später States/Events
```

Der Listener soll nicht selbstständig Core Batches erzeugen:

```text
Gateway
    ↓
Listener
    ↓
letzter bekannter Sensorzustand
    ↓
LoggerRuntime.run_once()
    ↓
Core Batch
    ↓
Queue / HTTP Delivery
```

---

## 31. LoggerPi-Proxy-Test

Auf dem LoggerPi wurde manuell ein temporärer Research-Listener angelegt:

```text
/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test.py
```

Ausgabeverzeichnis:

```text
/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test_output/
```

Der Listener lauscht auf:

```text
141.51.190.103:3778
```

Er wird nicht als systemd-Service installiert und verändert keine
bestehende LoggerPi-Konfiguration.

Ein künstlicher HTTP-Request wurde erfolgreich verarbeitet:

```http
PUT /gateway/put HTTP/1.1
Host: www.data199.com
HTTP_IDENTIFY:TESTGATEWAY:TESTMAC:C0
Content-Length: 12
```

Der Listener:

- nahm die TCP-Verbindung an,
- las Header und `Content-Length`,
- empfing den Body vollständig,
- speicherte Header und Body,
- gab HTTP `200 OK` mit 24 Binärbytes zurück.

Damit ist der lokale TCP-/HTTP-Testlistener grundsätzlich funktionsfähig.

---

## 32. Noch ausstehender Proxy-Test

Der nächste echte Test ist:

```text
Gateway .121
    ↓
Proxy 141.51.190.103:3778
    ↓
Research-Listener
```

Dafür muss Gateway 1 über `Command 4` geändert werden:

```text
Use Proxy:       0 → 1
Proxy Host:      192.168.1.1 → 141.51.190.103
Proxy Port:      80 → 3778
```

Dieser Schritt wurde noch nicht durchgeführt.

Gateway `.132` bleibt unverändert.

Vor dem Proxy-Schreibtest muss festgelegt werden:

- ob der Proxy zunächst nur capturt,
- ob der originale Payload parallel an `www.data199.com` weitergeleitet wird,
- wie Cloud-Fehler behandelt werden,
- ob der Listener zunächst manuell oder später als eigener Service läuft.

---

## 33. Sicherheits- und Änderungsregeln

Bisher wurden keine Sensoren und keine laufenden LoggerPi-Dienste durch
die WeatherHub-Research verändert.

Gateway `.121` wurde ausschließlich durch einen kontrollierten Name-only-
Test verändert:

```text
ZOOLOGY-observ2 → ZOOLOGY-TEST
```

Proxy und Cloud-Konfiguration blieben unverändert.

Kein Gateway-Reboot wurde ausgelöst.

Gateway `.132` wurde nicht verändert.

Vor einem späteren Proxy-Test müssen aktuelle Command-3-Konfigurationen
und Backups erhalten bleiben.

---

## 34. Referenzdateien

Gateway 1:

```text
C:\Users\LH\Desktop\gateway_141_51_190_121_before.html
C:\Users\LH\Desktop\gateway_141_51_190_121_current.html
C:\Users\LH\Desktop\gateway_141_51_190_121_getconfig_*.bin
C:\Users\LH\Desktop\gateway_141_51_190_121_restore.bin
C:\Users\LH\Desktop\gateway_141_51_190_121_test.bin
C:\Users\LH\Desktop\gateway_141_51_190_121_name_test.bin
C:\Users\LH\Desktop\gateway_141_51_190_121_after_name_test.html
```

SHA-256 des Name-only-Testpakets:

```text
AE2866B9B42D849BD351DC7547354AB3EA8F77F79407B3D3F2BF14513F5D30C5
```

Gateway 2:

```text
C:\Users\LH\Desktop\gateway_141_51_190_132_current.html
C:\Users\LH\Desktop\gateway_141_51_190_132_getconfig_*.bin
```

Temporärer LoggerPi-Testlistener:

```text
/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test.py
/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test_output/
```

---

## 35. Aktueller Wiedereinstiegspunkt

Der UDP-Konfigurationszugriff ist praktisch verifiziert:

```text
Command 2
    ↓
Command 3 / Get Config
    ↓
186 Bytes
```

Der Name-only-Schreibtest ist praktisch verifiziert:

```text
Command 4
    ↓
181 Bytes
    ↓
Name ZOOLOGY-TEST
```

Der nächste Schritt ist der kontrollierte Proxy-Test mit Gateway `.121`:

```text
Use Proxy: 1
Proxy Host: 141.51.190.103
Proxy Port: 3778
```

Gateway `.132` bleibt dabei unverändert.

Danach sollen zunächst die echten Binärpayloads von Gateway `.121`
capturiert und gegen die bekannten Sensorfamilien geprüft werden.

Noch nicht produktiv implementiert sind:

- WeatherHub-Gateway-Listener
- Cloud-Forward
- Gateway-Payload-Decoder in Python
- WeatherHub-Sensoradapter
- WeatherHub-Integration in den Core Batch
- States-/Events-Modell für Sensorstatus
- persistente Regenzählerlogik für ID08

### Stand 24.09.2026

Proxy-Test auf `.121` erfolgreich durchgeführt

Skript `docs\research\powershell_weatherhub_change_proxy.sh` hat die Konfiguration erfolgreich zum Gateway `.121` geschrieben. Rücksetzung wäre mit `docs\research\powershell_weatherhub_change_proxy_back.sh` möglich.

Listener `docs\research\weatherhub_gateway_proxy_test.py` empfängt erfolgreich Datenpakete vom umgeschribenen Gateway `.121`. Die outputs liegen auf dem LoggerPi unter `home/ZOOLOGY-observ/weatherhub_gateway_proxy_test_output`.

Funktionierender Decoder ist `docs\research\weatherhub_gateway_decode_test.py`.

Aktuell läuft das Gateway `.121` nachwievor im Proxymodus.

Ergebnisse des Proxytest und der empfangenen Datenpakete unter `docs\research\weatherhub_gateway_inventory_121_summary.txt` und `docs\research\weatherhub_gateway_inventory_121.txt`.