# WeatherHub Observer – technische Untersuchung

## Status

**Subprojekt:** WeatherHub Observer  
**Stand:** 2026-08-15  
**Status:** Technischer Datenkanal gefunden, Binärformat teilweise dekodiert  
**Nächster Schritt:** Timestamp-Feld identifizieren und anschließend einen reproduzierbaren automatisierten Abruf bauen.

Dieses Dokument beschreibt die technische Untersuchung des proprietären
WeatherHub-/Observer-Datenkanals.

Die Untersuchung ist zunächst vom eigentlichen LoggerPi-/OtterPi-Core
getrennt. Eine spätere Integration als LoggerPi-Adapter ist möglich, wenn
der direkte Zugriff reproduzierbar und ausreichend stabil umgesetzt werden
kann.

---

## 1. Ziel

Untersucht wird, ob sich die Daten der vorhandenen WeatherHub-/Observer-
Sensoren automatisiert abrufen und später über einen LoggerPi-Adapter in das
gemeinsame Data Model übernehmen lassen.

Im Bestand befinden sich 19 Sensoren, überwiegend des untersuchten Typs,
sowie mindestens ein weiterer Sensortyp.

Ziel ist ausdrücklich nicht, WeatherHub-spezifische Strukturen in das
allgemeine Data Model zu übernehmen.

Bei erfolgreicher Integration soll die Architektur grundsätzlich sein:

    WeatherHub
        ↓
    WeatherHub-Adapter
        ↓
    gemeinsames LoggerPi Data Model
        ↓
    Core Batch
        ↓
    OtterPi

---

## 2. Ausgangssituation

Die WeatherHub-Observer-Sensoren übertragen ihre Daten an die
WeatherHub-Webplattform.

Vereinfachter Datenweg:

    Sensor
        ↓
    WeatherHub-Infrastruktur
        ↓
    www.wh-observer.de
        ↓
    Webbrowser

Eine offensichtliche öffentliche API zum direkten Abruf war zunächst nicht
auffindbar.

Die Plattform bietet einen CSV-Export. Dieser war für die Untersuchung
zunächst nur manuell über die Weboberfläche nutzbar und daher für einen
späteren automatisierten LoggerPi-Betrieb unpraktisch.

Die entscheidende Untersuchungsmethode war deshalb, die von der
Weboberfläche selbst verwendeten Requests mit den Browser Developer Tools
zu untersuchen.

---

## 3. Browser-Untersuchung

**Browser:** Firefox

**Werkzeug:** Firefox Developer Tools → Network

Beim Öffnen bzw. Anzeigen des Sensor-Diagramms wurde folgender Request
identifiziert:

    POST https://www.wh-observer.de/DeviceDetails/ChartData

Beobachtete Eigenschaften:

- HTTP/1.1 200 OK
- Request Content-Type: `application/json; charset=utf-8`
- Response Content-Type: `application/text; charset=utf-8`
- Server: Microsoft-IIS/10.0
- ASP.NET
- ASP.NET MVC 5.2
- `X-Requested-With: XMLHttpRequest`

Damit ist bewiesen, dass die Weboberfläche einen konkreten
`ChartData`-Endpoint zur Abfrage der Diagrammdaten verwendet.

---

## 4. Request

Der Browser sendet JSON.

Beispiel:

    {
      "deviceID": "XYZ",
      "from": "01.08.2026",
      "to": "01.09.2026",
      "detailLevel": "month"
    }

Beobachtete Parameter:

| Feld | Bedeutung |
|---|---|
| `deviceID` | Sensor-/Gerätekennung |
| `from` | Startdatum |
| `to` | Enddatum |
| `detailLevel` | gewünschte Detailstufe |

Die genaue Bedeutung und alle zulässigen `detailLevel`-Werte sind noch
nicht vollständig untersucht.

---

## 5. Authentifizierung

Der Browser verwendet eine authentifizierte Session.

Unter anderem wurde ein `.ASPXAUTH`-Cookie beobachtet.

Außerdem wurden folgende Cookies beobachtet:

- `ARRAffinity`
- `ARRAffinitySameSite`

Daraus folgt:

Der gefundene `ChartData`-Endpoint ist nicht als öffentliche,
unauthentifizierte API anzusehen.

Bewiesen ist derzeit nur:

> Ein eingeloggter Browser kann den Endpoint erfolgreich verwenden.

Noch offen ist:

> Ob ein LoggerPi den Endpoint mit einer reproduzierbaren Login-/Session-
> Logik automatisiert nutzen kann.

**Wichtig:** Zugangsdaten, Session-Cookies oder sonstige Authentifizierungs-
informationen werden nicht in die Projektdokumentation oder in
Versionskontrolle übernommen.

---

## 6. Response

Die Response ist nicht direkt lesbares JSON.

Sie besteht aus einer langen Base64-Zeichenkette.

Beispielanfang:

    CuLFCgoLVGVtcGVyYXR1cmUSCQkAAIDtqft5QhISCQAAuDeq+3lCEWZmZmZmZjBA...

Die untersuchte Response hatte:

    614216 Zeichen

Die erste Base64-Dekodierung ergab:

    460660 Bytes

---

## 7. Doppelte Base64-Kodierung

Nach der ersten Dekodierung waren die resultierenden Bytes erneut als
Base64-Text erkennbar.

Die Prüfung ergab:

    $text2 -match '^[A-Za-z0-9+/=]+$'

Ergebnis:

    True

Damit wurde eine zweite Base64-Dekodierung durchgeführt.

Ergebnis:

    345493 Bytes

Die ersten Bytes lauteten:

    0A E2 C5 0A 0A 0B 54 65 6D 70 65 72 61 74 75 72 65 12 09 ...

Als ASCII ist unter anderem erkennbar:

    Temperature

Damit ist der Datenweg reproduziert:

    HTTP Response
        ↓
    Base64
        ↓
    Base64
        ↓
    Binärdaten

---

## 8. Erste dekodierte Messreihen

Eine ASCII-Suche innerhalb der dekodierten Binärdaten ergab unter anderem:

    Temperature
    Humidity

sowie weitere technische bzw. formatbedingte Strings.

Damit ist bewiesen, dass die dekodierten Binärdaten tatsächlich
Messreihenbezeichnungen enthalten.

---

## 9. Format-Hypothese

Ein Ausschnitt des Datenanfangs:

    0A E2 C5 0A
    0A 0B
    54 65 6D 70 65 72 61 74 75 72 65
    12 09
    09 00 00 80 ED A9 FB 79 42
    12 12
    09 00 00 B8 37 AA FB 79 42
    11 66 66 66 66 66 66 30 40
    12 12
    09 00 00 04 55 AA FB 79 42
    11 00 00 00 00 00 00 30 40

Die Byte-Struktur weist deutliche Ähnlichkeiten mit Protocol Buffers bzw.
einer protobuf-artigen Wire-Struktur auf.

Insbesondere die Bytewerte

    0A
    12
    09
    11

passen zu typischen Protobuf-Tags/Wire-Types.

**Dies ist ausdrücklich nur eine Arbeitshypothese und noch kein
abschließend bewiesenes Binärformat.**

---

## 10. Messpunktstruktur

Ein wiederkehrender Block hat beispielsweise die Form:

    12 12
    09 [8 Bytes]
    11 [8 Bytes]

Die Bedeutung des zweiten 8-Byte-Werts konnte experimentell bestätigt
werden.

---

## 11. Bestätigter Temperaturwert

Bei einem untersuchten Messpunkt befindet sich das relevante
8-Byte-Feld bei Offset 40.

Die Dekodierung mit:

    [BitConverter]::ToDouble($bytes2, 40)

ergab:

    16.4

Damit ist für diesen untersuchten Datenpunkt bewiesen:

- das betreffende Feld ist ein 64-Bit-Wert,
- es kann als IEEE-754 Double dekodiert werden,
- der daraus dekodierte Temperaturwert beträgt 16,4 °C.

Weitere unmittelbar folgende Werte lagen beispielsweise bei:

    16.4
    16.0
    16.0
    16.1
    16.1

Die Werte sind für den untersuchten Sensor physikalisch plausibel.

---

## 12. Aktuelle Rekonstruktion

Die Struktur ist noch nicht vollständig formalisiert.

Aktuelle Arbeitshypothese:

    ChartData
        ↓
    Base64
        ↓
    Base64
        ↓
    Binärstruktur
        ↓
    Measurement Series
        ├── "Temperature"
        │      ├── Measurement Point
        │      │      ├── Feld 1 → 8-Byte-Wert
        │      │      └── Feld 2 → 8-Byte-Double
        │      │                       ↓
        │      │                     16.4 °C
        │      └── ...
        │
        ├── "Humidity"
        └── ...

---

## 13. Noch ungeklärtes Feld

Direkt vor einem bekannten Temperaturwert befindet sich beispielsweise:

    09
    00 00 B8 37 AA FB 79 42

Das 8-Byte-Feld beginnt nach dem `09`.

Es besteht die begründete Vermutung, dass dieses Feld den Timestamp des
Messpunkts enthält.

Das ist **noch nicht bewiesen**.

Zu untersuchende Möglichkeiten sind unter anderem:

- Unix Timestamp
- Unix Milliseconds
- JavaScript Timestamp
- .NET-/OLE-artige Zeitbasis
- proprietäre Zeitbasis

---

## 14. Bewiesen

Aktuell als technisch reproduziert bzw. bestätigt gelten:

- Die Weboberfläche verwendet `POST /DeviceDetails/ChartData`.
- Der Request verwendet JSON.
- Der Endpoint liefert die Diagrammdaten direkt.
- Die untersuchte Response ist doppelt Base64-kodiert.
- Nach der Dekodierung erhält man strukturierte Binärdaten.
- Die Daten enthalten Messreihenbezeichnungen wie `Temperature` und
  `Humidity`.
- Temperaturdaten enthalten 64-Bit-Werte.
- Ein konkreter Wert konnte bytegenau als `16.4 °C` dekodiert werden.
- Der Datenkanal kann grundsätzlich außerhalb der reinen
  Diagrammdarstellung untersucht werden.

---

## 15. Arbeitshypothesen

Noch nicht endgültig bewiesen sind:

- protobuf-/protobuf-artige Binärstruktur
- Bedeutung sämtlicher Felder
- Zuordnung sämtlicher Wire-Tags
- Struktur der einzelnen Measurement Points
- Bedeutung des ersten 8-Byte-Feldes

---

## 16. Noch offen

- exaktes Binärformat
- Timestamp-Format
- vollständige Messpunktstruktur
- alle verfügbaren Measurement-Typen
- Login-/Session-Ablauf für einen automatisierten Client
- Zuordnung der vorhandenen Sensoren
- Unterschiede zwischen den vorhandenen Sensortypen
- Stabilität des `ChartData`-Endpoints
- Rate Limits bzw. mögliche Nutzungsbeschränkungen
- Eignung des Web-Endpoints für einen dauerhaften LoggerPi-Betrieb

---

## 17. Nächster Untersuchungsschritt

Nicht wieder bei der Browser-Suche beginnen.

Der relevante Endpoint und der grundlegende Datenweg sind bereits bekannt.

Als nächstes:

### Schritt 1

Timestamp-Feld identifizieren.

### Schritt 2

Einen kleinen Decoder erstellen, der zunächst nur folgende Informationen
extrahiert:

    sensor
    temperature
    timestamp
    value

### Schritt 3

Prüfen, ob weitere Measurement Series automatisch erkannt werden können,
z. B.:

    Temperature
    Humidity
    ...

### Schritt 4

Danach den Login-/Session-Ablauf untersuchen und prüfen, ob der Abruf ohne
manuelle Browseraktion reproduzierbar durchgeführt werden kann.

### Schritt 5

Erst wenn diese Punkte funktionieren, die Integration als
LoggerPi-Adapter bewerten.

---

## 18. Geplante Integration

Bei erfolgreichem direkten Zugriff soll WeatherHub nicht als Sonderfall in
das allgemeine Data Model eingebaut werden.

Stattdessen:

    WeatherHub
        ↓
    WeatherHub Adapter
        ↓
    gemeinsames LoggerPi Data Model
        ↓
    Core Batch
        ↓
    OtterPi

Der Adapter übernimmt insbesondere:

- Authentication / Session
- Abruf von `ChartData`
- Base64-Dekodierung
- Dekodierung des proprietären Binärformats
- Erkennung der Messreihen
- Timestamp-Konvertierung
- Sensor-ID-Zuordnung
- Übersetzung in das gemeinsame Data Model

Der Rest der LoggerPi-Architektur soll nicht von der proprietären
WeatherHub-Datenrepräsentation abhängig sein.

---

## 19. Reproduktionsmaterial

Die damalige Response wurde lokal als:

    C:\chartdata.txt

gespeichert.

Diese Datei kann reale Sensorwerte enthalten und gehört daher nicht
automatisch in das öffentliche Repository.

Insbesondere dürfen keine Zugangsdaten, Session-Cookies oder sonstigen
Authentifizierungsinformationen in Versionskontrolle übernommen werden.

Die bisher verwendeten PowerShell-Dekodierungsschritte werden in diesem
Dokument als Reproduktionsreferenz festgehalten.

Für spätere automatisierte Tests soll möglichst eine bereinigte,
nicht-sensitive Testprobe verwendet werden.

---

## 20. Wiedereinstiegspunkt

Der nächste Wiedereinstieg erfolgt bei:

> **Timestamp-Feld des dekodierten Messpunkts identifizieren.**

Danach:

    Timestamp
        ↓
    kleiner Decoder
        ↓
    Temperature + Timestamp + Value
        ↓
    weitere Measurement Series
        ↓
    automatisierter ChartData-Abruf
        ↓
    WeatherHub LoggerPi Adapter
