# WeatherHub Observer – technische Untersuchung

## Status

**Subprojekt:** WeatherHub Observer  
**Stand:** 2026-09-04  
**Status:** Authentifizierter Datenabruf, automatische Device Discovery und vollständiger Cross-Dump-Abruf aller aktuell 19 Geräte reproduziert; SparkLineChartData dekodiert; ID-Typen `0E` und `01` sowie deren aktuell beobachtete Kanalstrukturen verifiziert  
**Nächster Schritt:** Überführung der verifizierten Referenzimplementierung in `WeatherHubClient`, `WeatherHubDecoder` und `WeatherHubAdapter` sowie Normalisierung in das gemeinsame LoggerPi Data Model.

Dieses Dokument beschreibt die technische Untersuchung des proprietären
WeatherHub-/Observer-Datenkanals sowie den inzwischen reproduzierbaren
automatisierten Datenabruf.

Die Untersuchung ist vom eigentlichen LoggerPi-/OtterPi-Core getrennt.
WeatherHub-spezifische Strukturen sollen ausschließlich im WeatherHub-Adapter
behandelt werden.

## Dokumentationshinweis

Die Abschnitte mit konkreten Testläufen und historischen Beobachtungen
dokumentieren den Entstehungs- und Verifikationsweg der Untersuchung.

Für die aktuelle Implementierung sind insbesondere folgende Abschnitte
maßgeblich:

- Abschnitt 37 – Golden Path
- Abschnitt 43 – Komponentenaufteilung
- Abschnitt 45 – gemeinsames Data Model
- Abschnitt 46 – Health-/Monitoring-Abgrenzung
- Abschnitt 47 – Fehlerbehandlung
- Abschnitt 50 – Teststrategie
- Abschnitt 58 – nächste Implementierungsschritte
- Abschnitt 59 – aktueller Wiedereinstiegspunkt
- Abschnitt 61 – Cross-Dump-Meilenstein

Historische Testdetails dürfen erhalten bleiben, sollen aber nicht als
aktuelle offene Aufgaben interpretiert werden.

---

## Reproduzierbares Testskript

Das aktuell verwendeten Referenz-/Testskripte sind:

Reproduktionsskript:
    test-weatherhub-observer-v4.ps1

Decoder:
    decode-weatherhub-v2.ps1

Das Skript enthält derzeit die technische Referenzimplementierung für:

- Login via `/Account/LogOn`
- Aufbau der `WebRequestSession`
- Authentifizierungsprüfung über `/Devices`
- Device Discovery
- Abruf von `SparkLineChartData`
- Base64-Dekodierung
- Dekodierung von `ChartData`
- Ausgabe von `ChartSeries` und `ChartDataset`

Das Skript dient aktuell als technische Referenz und Regressionstest.

Die produktive Implementierung soll die darin enthaltene Logik später in
separate Komponenten (`WeatherHubClient`, `WeatherHubDecoder`,
`WeatherHubAdapter`) überführen.

Das Skript bleibt bis dahin als Golden-Path-Test erhalten.

---

## 1. Ziel

Untersucht wird, ob sich die Daten der vorhandenen WeatherHub-/Observer-
Sensoren automatisiert abrufen und anschließend über einen WeatherHub-Adapter
in das gemeinsame LoggerPi Data Model übernehmen lassen.

Im Bestand befinden sich derzeit 19 Sensoren.

Ziel ist ausdrücklich nicht, WeatherHub-spezifische Strukturen in das
allgemeine Data Model zu übernehmen.

Die geplante Architektur ist:

    WeatherHub Observer
        ↓
    WeatherHub Adapter
        ↓
    gemeinsames LoggerPi Data Model
        ↓
    Core Batch
        ↓
    OtterPi

Der WeatherHub-Adapter soll die komplette proprietäre Kommunikation und
Dekodierung kapseln.

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

Die Webplattform stellt unter anderem Diagramm- und CSV-Funktionen bereit.
Für einen automatisierten LoggerPi-/OtterPi-Betrieb ist eine direkte
Reproduktion der vom Browser verwendeten Requests jedoch wesentlich
interessanter als ein manueller Export.

Die Untersuchung wurde deshalb über die Browser Developer Tools und
anschließende Reproduktion mit PowerShell durchgeführt.

---

## 3. Browser-Untersuchung

**Browser:** Firefox

**Werkzeug:** Firefox Developer Tools → Network

Bei der Untersuchung der Weboberfläche wurden mehrere relevante Requests
identifiziert.

Dabei sind zwei Datenpfade zu unterscheiden:

### 3.1 Sensor-Detailseite / ChartData

Beim Öffnen eines Sensor-Diagramms wurde folgender Endpoint beobachtet:

    POST https://www.wh-observer.de/DeviceDetails/ChartData

Dieser Endpoint liefert einen größeren Datenbestand für die
Diagrammdarstellung.

Beobachtete Eigenschaften:

- HTTP `200 OK`
- Request Content-Type: `application/json; charset=utf-8`
- Response Content-Type: `application/text; charset=utf-8`
- Microsoft IIS / ASP.NET
- ASP.NET MVC
- `X-Requested-With: XMLHttpRequest`

Die Response kann deutlich größer sein als die Sparkline-Responses und
wurde während der Untersuchung mit ungefähr 168 KiB beobachtet.

Dieser Endpoint ist deshalb von dem später identifizierten
`SparkLineChartData`-Endpoint zu unterscheiden.

### 3.2 Dashboard / SparkLineChartData

Auf der Dashboard-/Übersichtsseite werden für die vorhandenen Sensoren
offenbar jeweils einzelne Requests ausgeführt:

    POST https://www.wh-observer.de/Devices/SparkLineChartData

Beispiel:

    {
      "deviceID": "016783F33A2A"
    }

Dieser Endpoint ist für den geplanten periodischen OtterPi-Abruf besonders
interessant, da er pro Sensor eine kompakte aktuelle Diagramm-/Status-
Payload liefert.

---

## 4. Entscheidende Erkenntnis: Authentifizierung

Der WeatherHub-Observer-Datenkanal ist nicht einfach eine öffentliche,
unauthentifizierte HTTP-API.

Der Zugriff auf `SparkLineChartData` wurde mit und ohne authentifizierte
Session getestet.

### Ohne funktionierende Session

Der Request führte zu:

    HTTP/1.1 500 Internal Server Error

mit einer HTML-Fehlerseite:

    <h1>Error.</h1>
    <h2>An error occurred while processing your request.</h2>

Das ist kein Beweis dafür, dass der Endpoint selbst defekt ist.

Der entscheidende Gegenversuch wurde mit einer über den Login aufgebauten
PowerShell-WebSession durchgeführt.

### Mit authentifizierter Session

Derselbe Endpoint wurde mit:

    -WebSession $session

aufgerufen.

Ergebnis:

    StatusCode        : 200
    StatusDescription : OK
    Content-Length    : 2944
    Content-Type      : application/text; charset=utf-8

Damit ist reproduzierbar bewiesen:

> `POST /Devices/SparkLineChartData` funktioniert mit einer gültigen
> authentifizierten Session.

---

## 5. Login

Der Login erfolgt über:

    POST https://www.wh-observer.de/Account/LogOn

Request Content-Type:

    application/x-www-form-urlencoded

Der relevante Form-Body enthält:

    ResendActivationMail=
    &ErrorMessage=
    &Lang=de
    &Username=<USERNAME>
    &Password=<PASSWORD>

Die tatsächlichen Zugangsdaten werden niemals in Dokumentation,
Versionskontrolle oder Logs gespeichert.

Für einen automatisierten Client sollen die Zugangsdaten über eine geeignete
lokale Konfiguration bzw. Secret-Verwaltung bereitgestellt werden.

---

## 6. Authentifizierte PowerShell-WebSession

Der funktionierende Mechanismus verwendet eine gemeinsame:

    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Diese Session wird zunächst für den Login verwendet.

Anschließend wird dieselbe Session für alle weiteren Requests verwendet:

    -WebSession $session

Dadurch verwaltet PowerShell die vom Server gesetzten Cookies automatisch.

Der Ablauf ist:

    Login
      ↓
    $session
      ↓
    authentifizierte Cookies
      ↓
    /Devices
      ↓
    SparkLineChartData

Es ist ausdrücklich nicht notwendig, für jeden Sensor einen neuen Login
durchzuführen.

---

## 7. Relevante Session-Cookies

In der funktionierenden Session wurden unter anderem folgende Cookies
beobachtet:

- `ARRAffinity`
- `ARRAffinitySameSite`
- `.ASPXAUTH`

Insbesondere `.ASPXAUTH` ist das relevante Authentifizierungs-Cookie.

Die konkreten Werte werden nicht dokumentiert und nicht gespeichert.

Beispiel:

    ARRAffinity = [REDACTED]
    ARRAffinitySameSite = [REDACTED]
    .ASPXAUTH = [REDACTED]

Die wichtige Erkenntnis ist nicht der Cookie-Wert selbst, sondern:

> Die Authentifizierung wird vom Server über die Session-/Cookie-Struktur
> bereitgestellt und kann von PowerShell automatisch weitergeführt werden.

Manuelles Kopieren von Browser-Cookies ist daher für die spätere
Implementierung nicht erforderlich.

---

## 8. Login erfolgreich reproduziert

Nach dem Login wurde mit derselben `$session` die Devices-Seite aufgerufen:

    $devices = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri "https://www.wh-observer.de/Devices" `
        -Method GET `
        -WebSession $session

Ergebnis:

    Devices HTTP: 200
    URL: https://www.wh-observer.de/Devices

Damit ist zusätzlich bewiesen, dass die PowerShell-Session nach dem Login
tatsächlich als authentifizierte WebSession akzeptiert wird.

Der erfolgreiche Ablauf ist damit:

    POST /Account/LogOn
          ↓
    authentifizierte $session
          ↓
    GET /Devices
          ↓
    HTTP 200

---

## 9. SparkLineChartData

Der für den automatisierten Dashboard-Abruf relevante Endpoint lautet:

    POST https://www.wh-observer.de/Devices/SparkLineChartData

Request:

    POST /Devices/SparkLineChartData HTTP/1.1
    Host: www.wh-observer.de
    Content-Type: application/json
    X-Requested-With: XMLHttpRequest
    Origin: https://www.wh-observer.de
    Referer: https://www.wh-observer.de/devices

Body:

    {"deviceID":"016783F33A2A"}

Die Device-ID identifiziert den konkreten Sensor.

---

## 10. Browser-Request

Der Browser verwendet sinngemäß einen Request dieser Form:

    POST /Devices/SparkLineChartData HTTP/1.1
    Host: www.wh-observer.de
    User-Agent: Mozilla/5.0 ...
    Accept: */*
    Accept-Language: de,en-US;q=0.9,en;q=0.8
    Accept-Encoding: gzip, deflate, br, zstd
    Content-Type: application/json
    X-Requested-With: XMLHttpRequest
    Origin: https://www.wh-observer.de
    Referer: https://www.wh-observer.de/devices
    Cookie: ARRAffinity=...; ARRAffinitySameSite=...; .ASPXAUTH=...
    Sec-Fetch-Dest: empty
    Sec-Fetch-Mode: cors
    Sec-Fetch-Site: same-origin

    {"deviceID":"016783F33A2A"}

Für PowerShell müssen jedoch nicht zwangsläufig sämtliche Browser-Header
künstlich nachgebaut werden.

Der erfolgreiche Test zeigt, dass insbesondere die authentifizierte Session
entscheidend ist.

---

## 11. Reproduzierbarer PowerShell-Abruf

Der entscheidende erfolgreiche Test war sinngemäß:

    $response = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri "https://www.wh-observer.de/Devices/SparkLineChartData" `
        -Method "POST" `
        -WebSession $session `
        -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0" `
        -Headers @{
            "Accept" = "*/*"
            "Accept-Language" = "de,en-US;q=0.9,en;q=0.8"
            "Accept-Encoding" = "gzip, deflate, br, zstd"
            "X-Requested-With" = "XMLHttpRequest"
            "Origin" = "https://www.wh-observer.de"
            "Sec-GPC" = "1"
            "Referer" = "https://www.wh-observer.de/devices"
            "Sec-Fetch-Dest" = "empty"
            "Sec-Fetch-Mode" = "cors"
            "Sec-Fetch-Site" = "same-origin"
        } `
        -ContentType "application/json; charset=utf-8" `
        -Body '{"deviceID":"016783F33A2A"}'

Ergebnis:

    StatusCode: 200
    Content-Length: 2944

Damit ist der grundlegende automatisierte Datenabruf reproduzierbar.

---

## 12. Response

Die Response des `SparkLineChartData`-Endpoints ist kein JSON.

Sie besteht aus Base64-kodierten Daten.

Beispielanfang:

    CswICgxUZW1wZXJhdHVyZTESEgkAAKD3wAB6QhGamZmZmZk0QBISCQCA5V7BAHpCEQAAAAAAgDRA...

Für den konkret getesteten Sensor:

    Device ID: 016783F33A2A
    Response-Länge: 2944 Zeichen
    Content-Length: 2944

Die Base64-Eigenschaften wurden geprüft:

    First char: C
    Last char: =
    Länge % 4: 0

Damit ist die Response formal eine gültige Base64-Darstellung.

---

## 13. Base64-Dekodierung

Die Response wird zunächst von Text in Binärdaten dekodiert:

    Base64
        ↓
    byte[]

Der Decoder arbeitet direkt auf diesen Binärdaten.

Wichtig ist die Unterscheidung zwischen:

    $response.Content

und:

    $responseText

Bei `Invoke-WebRequest` war `$response.Content` in der verwendeten
PowerShell-Umgebung zunächst ein `System.Byte[]`.

Deshalb funktionierte beispielsweise:

    $response.Content.Substring(...)

nicht.

Für weitere Verarbeitung muss der Inhalt sauber als Text bzw. Byte-Array
behandelt werden.

---

## 14. Response-Datei

Eine Response wurde erfolgreich lokal gespeichert:

    C:\Users\Lorc\WeatherHub\sparkline-016783F33A2A.txt

Der direkte Schreibversuch nach:

    C:\

führte wegen fehlender Berechtigungen zu einem Fehler.

Für weitere Tests soll deshalb ein beschreibbarer Arbeitsordner verwendet
werden, beispielsweise:

    $workDir = Join-Path $env:USERPROFILE "WeatherHub"

    New-Item -ItemType Directory -Path $workDir -Force | Out-Null

Anschließend können Response-Dateien beispielsweise unterhalb von:

    C:\Users\<USER>\WeatherHub\

gespeichert werden.

---

## 15. Abgrenzung zum größeren ChartData-Abruf

Während der Untersuchung wurde zeitweise eine deutlich größere Response
von ungefähr:

    168 KiB
    bzw. ca. 174 KB

beobachtet.

Diese Größe darf nicht mit einem einzelnen
`SparkLineChartData`-Request gleichgesetzt werden.

Der konkret getestete einzelne Request:

    POST /Devices/SparkLineChartData
    {"deviceID":"016783F33A2A"}

liefert:

    2944 Bytes

Bei 19 Sensoren ergibt das überschlägig:

    19 × 2944 = 55.936 Bytes

also ungefähr:

    54,6 KiB

Die früher beobachtete Größenordnung von etwa 168 KiB stammt daher sehr
wahrscheinlich aus einem anderen Datenabruf bzw. einer anderen Datenmenge.

Die beiden Datenpfade müssen getrennt betrachtet werden:

    Dashboard
        ↓
    19 × SparkLineChartData
        ↓
    kompakte Einzelresponses

und:

    Sensor-Detailseite
        ↓
    ChartData
        ↓
    größerer Datenbestand

---

## 16. Bereits reverse-engineerte Datenstruktur

Der entscheidende Fortschritt gegenüber der ursprünglichen Untersuchung ist,
dass die Response inzwischen nicht nur als „Base64-Daten“ erkannt wurde.

Der Binärdatenstrom wurde byteweise analysiert.

Dabei konnte eine strukturierte, protobuf-artige Nachrichtenstruktur
rekonstruiert werden.

Der aktuelle Decoder verwendet folgende logische Struktur:

    ChartData
      field 1 = Series (repeated ChartSeries)

    ChartSeries
      field 1  = SeriesID
      field 2  = Datasets (repeated ChartDataset)
      field 3  = LineColor
      field 4  = FormattedTimestamp
      field 5  = FormattedMeasurement
      field 6  = ConnectionLost
      field 7  = LowBattery
      field 8  = AlertWasActive
      field 9  = CardStatus
      field 10 = AlertActive
      field 11 = AlertSettingActive

    ChartDataset
      field 1 = Timestamp
      field 2 = Value

Für `ChartDataset` sind derzeit nur `field 1` und `field 2` belastbar
verifiziert.

Weitere historische Feldzuordnungen wurden aus der aktuellen
Strukturbeschreibung entfernt, da sie nicht ausreichend reproduzierbar
belegt sind.

Die Struktur ist damit für den aktuell untersuchten Datenstrom weitgehend
rekonstruiert.

---

## 17. Proto-Wire-Types

Der Decoder berücksichtigt derzeit die folgenden Wire-Types:

    0 = varint
    1 = fixed64
    2 = length-delimited
    5 = fixed32

Die relevanten Datentypen sind unter anderem:

    string
    bool
    double
    nested message

Die Byte-Tags und die daraus resultierende Feldstruktur sind mit den
beobachteten Payloads konsistent.

Die Bezeichnung „protobuf-artig“ bleibt dennoch bewusst bestehen, solange
keine originale `.proto`-Definition oder Server-Schemaquelle vorliegt.

---

## 18. Aktueller Decoder

Der vorhandene PowerShell-Decoder kann:

- Base64 einlesen
- Binärdaten erzeugen
- Varints lesen
- Fixed64-/Double-Werte lesen
- Length-delimited Felder lesen
- UTF-8-Strings lesen
- unbekannte Felder überspringen
- `ChartData` dekodieren
- `ChartSeries` dekodieren
- `ChartDataset` dekodieren
- Status-/Alert-Felder auswerten
- mehrere Series erkennen
- mehrere Datasets pro Series erkennen
- Timestamp-Werte in eine lesbare Zeitdarstellung umwandeln

Der Decoder ist damit bereits als eigenständige technische Komponente
vorhanden.

---

## 19. Proto2-Semantik

Ein wichtiger Punkt des Decoders ist die Behandlung optionaler Felder.

Bei der untersuchten Struktur gilt konzeptionell:

    absent != explicit false

Das bedeutet:

Ein nicht vorhandenes boolesches Feld darf nicht automatisch als
explizit gesetztes `false` interpretiert werden.

Der Decoder gibt deshalb nur Felder aus, die tatsächlich in der Payload
vorhanden sind.

Das ist insbesondere für Status- und Alert-Felder relevant.

---

## 20. ChartSeries – bekannte Felder

Eine `ChartSeries` enthält derzeit folgende rekonstruierten Felder:

Feld  | Typ  | Bedeutung
--- | --- | ---
1  | string  | SeriesID
2  | message  | Datasets
3  | string  | LineColor
4  | string  | FormattedTimestamp
5  | string  | FormattedMeasurement
6  | bool  | ConnectionLost
7  | bool  | LowBattery
8  | bool  | AlertWasActive
9  | string  | CardStatus
10  | bool  | AlertActive
11  | bool  | AlertSettingActive

`FormattedMeasurement` ist ein serverseitig bereits formatierter Messwert der jeweiligen
Series. Die Cross-Dump-Untersuchung vom 03.09.2026 zeigt beispielsweise:

- Temperature → `"17,0°C"`
- Humidity → `"61 %"`
- Temperature1 → `"22,3°C"`

Damit handelt es sich sehr wahrscheinlich um den für die Dashboard-/Card-Darstellung
bestimmten aktuellen Anzeigewert der jeweiligen Messreihe.

Der Wert ist von `ChartDataset.field 2 = Value` zu unterscheiden:
`Value` enthält die numerischen historischen Messpunkte, während `FormattedMeasurement`
bereits als Darstellungstext mit Einheit und lokaler Formatierung vorliegt.

Die Interpretation als Dashboard-Anzeigewert ist durch die beobachteten Payloads stark
gestützt, aber noch nicht durch einen direkten Vergleich mit dem gerenderten Dashboard-HTML
als endgültiges Server-Schema bewiesen.

Die Felder `ConnectionLost` und `LowBattery` sind für die spätere Überwachung besonders interessant.

---

## 21. ChartDataset – aktuell verifizierte Struktur

Für `ChartDataset` sind im aktuellen Stand des Decoders nur folgende Felder
belastbar verifiziert:

| Feld | Wire Type | Bedeutung |
|---:|---:|---|
| 1 | fixed64 | Timestamp |
| 2 | fixed64 | Value |

Dabei gilt:

    field 1 = Timestamp
    field 2 = Value

`Timestamp` wird aktuell als Unix-Zeit in Millisekunden interpretiert.

`Value` wird als IEEE-754 Double dekodiert.

Die früher in der Untersuchung dokumentierten Felder:

    field 3
    field 4
    ...
    field 13

sind **nicht als Bestandteil der aktuell verifizierten `ChartDataset`-
Struktur anzusehen**.

Die entsprechende frühere Feldzuordnung war ein historischer
Reverse-Engineering-Versuch und wird für die aktuelle Implementierung
nicht mehr verwendet.

Insbesondere darf `field 4` nicht als bekanntes `Measurement`-Nested-Message
behandelt werden.

Weitere Felder dürfen erst dann dokumentiert werden, wenn sie anhand
konkreter Payloads reproduzierbar nachgewiesen und dem jeweiligen
Wire-Type eindeutig zugeordnet wurden.

---

## 22. Timestamp

Der Timestamp ist inzwischen Bestandteil der rekonstruierten
`ChartDataset`-Struktur:

    field 1 = Timestamp
    wire type = 1
    representation = 64-bit double

Der Decoder verwendet derzeit:

    [DateTimeOffset]::FromUnixTimeMilliseconds(
        [Int64]$ds.Timestamp
    )

Damit wird der Wert aktuell als Unix-Zeit in Millisekunden interpretiert.

Die Verwendung dieser Zeitbasis ist mit den beobachteten Messdaten
konsistent und wird im Decoder bereits praktisch verwendet.

---

## 23. Messwerte

Das Feld:

    ChartDataset.field 2

wird als:

    fixed64 / IEEE-754 double

dekodiert.

Damit können die Messwerte direkt als numerische Werte übernommen werden.

Beispielhaft wurden bei der Untersuchung Temperaturwerte wie:

    16.4
    16.0
    16.0
    16.1
    16.1

dekodiert.

Diese Werte sind für den untersuchten Sensor physikalisch plausibel.

---

## 24. Sensor- und Gerätetypen

Während der Untersuchung wurden mehrere TFA-Sensortypen betrachtet.

Bekannte Modelle:

| Kat.-Nr. | ID-Typ | Bekannte Eigenschaften |
|---|---:|---|
| 30.3302.02 | 09 | interne Temperatur, Kabelfühler-Temperatur, Luftfeuchte, Batterie |
| 30.3312.02 | 0E | Temperatur, Luftfeuchte |
| 30.3313.02 | 01 | interne Temperatur, externe/Kabelfühler-Temperatur |
| 30.3308.02 | 01 | interne Temperatur, externe/Kabelfühler-Temperatur |

Die Funkintervalle der untersuchten Geräte liegen je nach Modell ungefähr
bei 3½ bzw. 7 Minuten.

Die exakten Sensorcharakteristika sollten für die spätere Implementierung
nicht ausschließlich aus der Artikelnummer abgeleitet werden.

---

## 25. ID-Typ als Decoder-Konzept

Eine wichtige Erkenntnis ist die Wiederverwendung desselben ID-Typs bei
unterschiedlichen Artikelnummern.

Beispielsweise:

    30.3313.02 → ID-Typ 01
    30.3308.02 → ID-Typ 01

Daher sollte die spätere Architektur nicht primär:

    Artikelnummer
        ↓
    Decoder

verwenden.

Sinnvoller ist:

    ID-Typ
        ↓
    Payload-/Kanalstruktur
        ↓
    verfügbare Messkanäle

Die konkrete Sensor-Konfiguration wird davon getrennt behandelt.

Beispiel:

    Device
        ├── deviceID
        ├── article/model
        ├── idType
        └── expected channels

und:

    Decoder
        └── idType → payload structure

### Konsequenz für die Implementierung

Der Binary-Decoder darf die fachliche Interpretation der Series nicht
fest verdrahten.

Beispielsweise dekodiert der Decoder lediglich:

    SeriesID = "Temperature1"
    Value = 22.3

Er entscheidet nicht selbst, dass `Temperature1` eine
Umgebungstemperatur darstellt.

Diese Interpretation erfolgt in einer WeatherHub-spezifischen
Mapping-Schicht.

Konzeptionell:

    ID-Typ
        ↓
    WeatherHub Channel Mapping
        ↓
    SeriesID
        ↓
    neutrales Measurement

Aktuell verifiziert:

    ID-Typ 0E
        Temperature → temperature
        Humidity    → humidity

    ID-Typ 01
        Temperature1 → ambient_temperature
        Temperature2 → monitored_temperature

Die fachliche Interpretation von `Temperature1` und `Temperature2` basiert
auf Sensorhardware, Einsatzort und Cross-Dump-Ergebnissen.

Die ursprünglichen `SeriesID`-Werte bleiben trotzdem Bestandteil der
WeatherHub-spezifischen Roh-/Zwischenstruktur.

---

## 26. Für Monitoring relevante Daten

Für das geplante OtterPi-Monitoring sind nicht alle Portalinformationen
gleich wichtig.

Die primär interessanten Daten sind:

- Temperatur
- Luftfeuchte
- weitere vorhandene Messkanäle
- Batterie-/Batteriestatus
- Sensor-/Messfehler
- Verbindungs-/Übertragungsstatus
- Kanal-/Sensortyp
- Timestamp

Das WeatherHub-Portal selbst soll dabei nicht die eigentliche Alerting-Logik
für den OtterPi übernehmen.

Der OtterPi soll die Rohinformationen in einen eigenen Health-/Alert-State
überführen.

---

## 27. Batterieüberwachung

Der Decoder liefert auf `ChartSeries`-Ebene unter anderem:

    LowBattery

Damit kann der OtterPi einen eigenen Batterie-Status ableiten.

Beispiel:

    LowBattery = false
        ↓
    Batterie aktuell unauffällig

    LowBattery = true
        ↓
    Battery warning

Die genaue Alarmstrategie wird später im Monitoring-Core definiert.

---

## 28. Sensor-/Messfehler

Auf `ChartDataset`-Ebene sind aktuell nur `Timestamp` und `Value`
belastbar verifiziert.

Statusinformationen wie Verbindungs- oder Batteriezustand sind davon
getrennt zu betrachten und werden derzeit insbesondere über die
verifizierten `ChartSeries`-Felder untersucht.

Eine Ableitung von Sensorfehlern aus nicht verifizierten
`ChartDataset.field`-Nummern erfolgt nicht.

---

## 29. Funk-/Übertragungsstatus

Für die lokale Überwachung ist insbesondere die Unterscheidung zwischen:

    Sensor misst nicht

und:

    Sensor misst,
    aber die Datenübertragung funktioniert nicht

interessant.

`ConnectionLost` kann hierfür eine direkte Informationsquelle sein.

Zusätzlich kann der OtterPi anhand des Alters des letzten gültigen
Messpunkts selbst feststellen, ob ein Sensor über längere Zeit keine neuen
Daten geliefert hat.

Damit kann später beispielsweise zwischen:

    OK
    STALE
    CONNECTION_LOST
    SENSOR_ERROR
    LOW_BATTERY

unterschieden werden.

Die endgültige Zustandslogik gehört jedoch in den Monitoring-/Core-Bereich
und nicht in den WeatherHub-Decoder.

---

## 30. Kanal-/Sensortyp-Plausibilität

Der rekonstruierte Datenstrom enthält genügend Informationen, um später
auch Plausibilitätsprüfungen zu ermöglichen.

Grundsätzlich:

    Sensor-ID
        ↓
    ID-Typ
        ↓
    erwartete Kanäle
        ↓
    tatsächlich gelieferte Series
        ↓
    Plausibilitätsprüfung

Damit kann beispielsweise erkannt werden:

- erwarteter externer Fühler fehlt
- unerwarteter Kanal erscheint
- erwartete Measurement Series fehlt
- Payload passt nicht zum erwarteten Sensortyp
- Sensor-Konfiguration hat sich verändert

Das ist für einen robusten Langzeitbetrieb wertvoll.

---

## 31. 19 Sensoren – geplanter Abruf

Auf dem Dashboard befinden sich aktuell 19 Sensoren.

Das beobachtete Verhalten entspricht:

    Dashboard
        ↓
    Sensor 1 → SparkLineChartData
    Sensor 2 → SparkLineChartData
    Sensor 3 → SparkLineChartData
    ...
    Sensor 19 → SparkLineChartData

Für den automatisierten Betrieb ist daher der folgende Ablauf geplant:

    LOGIN
      ↓
    $session
      ↓
    Sensor-/Device-Liste
      ↓
    foreach deviceID
      ↓
    POST /Devices/SparkLineChartData
      ↓
    Base64
      ↓
    Decoder
      ↓
    gemeinsames Data Model

---

## 32. Kein Login pro Sensor

Es ist ausdrücklich nicht notwendig, für jeden Sensor einen separaten
Login durchzuführen.

Die Session wird einmal aufgebaut:

    LOGIN
      ↓
    $session

Danach können alle Sensoren über dieselbe Session abgefragt werden:

    Sensor 1
    Sensor 2
    Sensor 3
    ...
    Sensor 19

Das reduziert die Zahl der Authentifizierungsvorgänge erheblich.

---

## 33. Session-Lebensdauer

Die genaue Lebensdauer von `.ASPXAUTH` wurde noch nicht systematisch
bestimmt.

Für die erste robuste OtterPi-Version ist deshalb ein konservativer Ablauf
sinnvoll:

    Scheduler startet
        ↓
    Login
        ↓
    neue $session
        ↓
    Sensoren abrufen
        ↓
    Daten verarbeiten
        ↓
    Zyklus beendet

Bei einem 15-Minuten-Intervall ist dieser Ansatz zunächst ausreichend.

Eine spätere Optimierung kann eine Session-Wiederverwendung ermöglichen:

    vorhandene Session
        ↓
    Request
        ↓
    Session weiterhin gültig
        ↓
    weiterverwenden

oder bei erkennbarer Authentifizierungsproblematik:

    401 / Login-Redirect / ungültige Session
        ↓
    neu einloggen
        ↓
    Request wiederholen

Diese Optimierung ist nicht Teil des ersten stabilen Implementierungsschritts.

---

## 34. Geplanter Abrufintervall

Für das OtterPi-Monitoring genügt ein Abruf ungefähr alle:

    15 Minuten

Die Sensoren selbst übertragen je nach Modell wesentlich häufiger.

Der OtterPi muss daher nicht jeden einzelnen Sensor-Übertragungszyklus
mitverfolgen.

Der 15-Minuten-Abruf dient der lokalen Überwachung und Statusbewertung.

---

## 35. PowerShell-Spezialproblem

Bei `Invoke-WebRequest` trat in der verwendeten PowerShell-Umgebung
zunächst eine Sicherheits-/Parsing-Warnung auf.

Die verwendete Lösung ist:

    -UseBasicParsing

Für die reproduzierbare PowerShell-Implementierung sollte deshalb
konsequent verwendet werden:

    Invoke-WebRequest -UseBasicParsing

---

## 36. Frühere curl-Problematik

Frühe Tests mit `curl.exe` lieferten unter anderem:

    curl exit code: 3

ohne erwartete Response-Datei.

Das war eine lokale Quoting-/Argument-Problematik und kein belastbarer
Nachweis dafür, dass der Server den Request grundsätzlich ablehnt.

Später konnte mit `curl.exe` zwar eine HTTP-500-Response sichtbar gemacht
werden, der entscheidende erfolgreiche Test wurde jedoch mit:

    Invoke-WebRequest
    +
    -WebSession $session

durchgeführt.

Für die weitere Entwicklung sollte deshalb zunächst PowerShell mit
`WebRequestSession` verwendet werden.

---

## 37. Golden Path

Der aktuell reproduzierbare technische Golden Path lautet:

    WeatherHub Observer
          │
          ▼
    POST /Account/LogOn
          │
          ▼
    authentifizierte PowerShell-WebSession
          │
          ├── ARRAffinity
          ├── ARRAffinitySameSite
          └── .ASPXAUTH
          │
          ▼
    GET /Devices
          │
          ▼
    HTTP 200
          │
          ▼
    Device-ID
          │
          ▼
    POST /Devices/SparkLineChartData
          │
          ▼
    HTTP 200
          │
          ▼
    Base64-Response
          │
          ▼
    Binärdaten
          │
          ▼
    ChartData / ChartSeries / ChartDataset
          │
          ▼
    Messwerte + Statusinformationen
          │
          ▼
    gemeinsames LoggerPi Data Model

Dieser Ablauf ist der derzeit wichtigste technische Baseline-Test.

---

## 38. Was inzwischen bewiesen ist

Folgende Punkte sind praktisch reproduziert:

1. WeatherHub Observer besitzt einen authentifizierten Webzugang.
2. Der Login erfolgt über `POST /Account/LogOn`.
3. PowerShell kann den Login reproduzierbar durchführen.
4. Eine `WebRequestSession` kann die Authentifizierung weiterführen.
5. `/Devices` liefert mit der authentifizierten Session HTTP 200.
6. `POST /Devices/SparkLineChartData` funktioniert mit derselben Session.
7. Ein einzelner Sparkline-Request liefert ungefähr 2,9 KiB Payload.
8. Die Response ist Base64-kodiert.
9. Die Base64-Daten lassen sich in Binärdaten zurückführen.
10. Die Binärdaten besitzen eine protobuf-artige strukturierte Feldkodierung.
11. `ChartData`, `ChartSeries` und `ChartDataset` konnten rekonstruiert werden.
12. Timestamp und Value können dekodiert werden.
13. Status-/Alert-Felder können dekodiert werden.
14. Mindestens ID-Typ `0E` wurde praktisch getestet.
15. Mindestens ID-Typ `01` wurde praktisch getestet.
16. Mehrere TFA-Sensorfamilien konnten der Untersuchung zugeordnet werden.
17. Die grundlegende Kette Login → Session → Sensorrequest → Decoder
    funktioniert.

Damit ist die Untersuchung vom reinen Reverse Engineering in eine
Engineering-/Integrationsphase übergegangen.

---

## 39. Was noch nicht vollständig geklärt ist

Trotz des weit fortgeschrittenen Standes sind einige Punkte weiterhin offen:

  * vollständige Bedeutung des `Measurement`-Nested-Messages
  * vollständige Bedeutung aller Statusfelder
  * exakte Session-Lebensdauer
  * Verhalten bei abgelaufener Session
  * Verhalten bei temporären HTTP-Fehlern
  * Verhalten bei einzelnen nicht erreichbaren Sensoren
  * mögliche Rate Limits
  * mögliche serverseitige Nutzungsbeschränkungen
  * langfristige Stabilität des Web-Endpoints
  * endgültige Health-State-Matrix für den OtterPi
  * direkter UI-Abgleich von `FormattedMeasurement` mit der tatsächlich gerenderten
    Dashboard-Anzeige

Nicht mehr offen sind dagegen:

  * automatische Device Discovery
  * vollständige Erfassung der aktuell vorhandenen 19 Geräte
  * praktische Abdeckung der ID-Typen `0E` und `01`
  * vollständiger Cross-Dump-Abgleich der 19 Sensoren
  * Zuordnung der beiden bekannten Sensorfamilien zu ihren beobachteten Kanalstrukturen

Diese Punkte sind keine grundlegende Blockade mehr für einen ersten automatisierten Abruf.

---

## 39.1 Abgrenzung: Research abgeschlossen vs. Engineering offen

Der grundlegende Reverse-Engineering- und Reproduktionsnachweis für den
SparkLine-Datenpfad ist abgeschlossen.

Als technisch verifiziert gelten:

- Login über `/Account/LogOn`
- authentifizierte `WebRequestSession`
- Authentifizierungsprüfung über `/Devices`
- automatische Device Discovery
- dynamische Ermittlung der aktuell vorhandenen Geräte
- Abruf aller aktuell vorhandenen Geräte über `SparkLineChartData`
- Base64-Dekodierung
- Dekodierung von `ChartData`, `ChartSeries` und `ChartDataset`
- Extraktion von Timestamp und Value
- Extraktion der bekannten Status-/Alert-Felder
- Erkennung der aktuell beobachteten ID-Typen `0E` und `01`
- Zuordnung der aktuell beobachteten Kanalstrukturen
- vollständiger Cross-Dump-Test mit 19/19 erfolgreichen Geräten

Damit liegt der Schwerpunkt der weiteren Entwicklung nicht mehr auf der
Ermittlung des proprietären Datenformats.

Offen sind primär Engineering-Themen:

- robuste Implementierung des HTTP-/Session-Clients
- robuste HTML-basierte Device Discovery
- Fehler- und Retry-Strategie
- Trennung von Decoder und Adapter
- ID-Typ-/Kanal-Konfiguration
- Normalisierung in das gemeinsame Data Model
- Persistenz
- Scheduler
- Monitoring und Alerting
- Regressionstests mit bereinigten Fixtures

---

## 40. Automatische Device Discovery

Die Device-Liste kann inzwischen direkt aus der authentifizierten
`/Devices`-Seite ermittelt werden.

Ein separater manueller Eintrag der 19 Device-IDs ist damit für den
produktiven Abruf nicht erforderlich.

Der erfolgreiche Ablauf ist:

    POST /Account/LogOn
        ↓
    authentifizierte WebRequestSession
        ↓
    GET /Devices
        ↓
    HTML der Geräteübersicht
        ↓
    Device Discovery
        ↓
    deviceID + name
        ↓
    SparkLineChartData

Beim Test vom 02.09.2026 wurden insgesamt:

    19 Devices

aus der `/Devices`-Seite extrahiert.

Damit ist die automatische Ermittlung der technischen Geräteidentitäten
praktisch nachgewiesen.

Die Device-ID wird als stabile technische Identität verwendet.

Der Anzeigename wird dagegen als veränderliches Metadatum behandelt und
bei jedem erfolgreichen Device-Abgleich aktualisiert.

---

## 40.1 Device Discovery – aktueller Test

Der reproduzierbare Test verwendet:

    GET https://www.wh-observer.de/Devices

mit der zuvor authentifizierten `$session`.

Ergebnis:

    Devices HTTP: 200
    Devices URL : https://www.wh-observer.de/Devices
    Authentication: OK

Anschließend wird die HTML-Seite analysiert und die vorhandene Device-Liste
ermittelt.

Der Test vom 02.09.2026 ergab:

    Devices gefunden: 19

Die extrahierten Informationen bestehen mindestens aus:

    DeviceId
    Name

Die technische ID wird anschließend direkt für den
`SparkLineChartData`-Request verwendet.

---

## 40.2 Vollständige Device-Liste vom 02.09.2026

Zum Zeitpunkt des Tests waren folgende 19 Geräte auf `/Devices` vorhanden:

| # | Device ID | Name |
|---:|---|---|
| 1 | `0E74A4597B54` | R1304 - DryAger - 17 °C, 80% rH |
| 2 | `016783F33A2A` | R1304 - DryAger - 17 °C, 80% rH |
| 3 | `01651662457B` | R1304 - Barbadensis rechts - 24 °C - 12/12h LD |
| 4 | `015A4FC910F4` | R1304 - Barbadensis links - 24 °C - 12/12h LD |
| 5 | `0167554C25BE` | R1308 - Tardiculture 2 - unten - (18 °C) - 08:00-20:00 h "Day" |
| 6 | `015E664F727F` | R1308 - Tardiculture 2 - oben - (18 °C) - 08:00-20:00 h "Day" |
| 7 | `015EB583B95C` | R1308 - Tardiculture 1 - unten - (18 °C) - 08:00-20:00 h "Night" |
| 8 | `015C32E3CED1` | R1308 - Tardiculture 1 - oben - (18 °C) - 08:00-20:00 h "Night" |
| 9 | `015D087CA01C` | Liza left - 19 °C - 12/12h LD day / 8:00-20:00 h |
| 10 | `0146471130BF` | Liza right - 19 °C - 12/12h LD night / 20:00-8:00 h |
| 11 | `015F9410F3EB` | R1306 - Molekularlab - Kombi |
| 12 | `017453BF9A79` | R1306 - Molekularlab - Tür |
| 13 | `0106CAF71038` | R1306 - Molekularlab - Fenster |
| 14 | `017262BF9016` | R1307 - Vorraum Kühlkammer |
| 15 | `0167CE8A9AF4` | R1309 - RNA-lab - Freezer |
| 16 | `010678C5AB4A` | R1310 - Histolab - Cryostat |
| 17 | `017A5CD3FC1C` | R1311 - Immunolab - Antibody - Freezer |
| 18 | `0101F89974E0` | R1311 - Immunolab - Antibody - Kühlschrank |
| 19 | `0169706EBE2C` | R1313 - Praktikumsraum |

Die Liste stellt eine Momentaufnahme des WeatherHub-Backends vom
02.09.2026 dar.

Die Namen dürfen daher nicht als unveränderliche Identitäten betrachtet
werden.

---

## 40.3 Vollständiger Cross-Dump-Abgleich der 19 Sensoren

Am 03.09.2026 wurden mit dem automatisierten Capture-Skript alle 19 aktuell
bekannten WeatherHub-Observer-Sensoren abgerufen und anschließend mit dem
vorhandenen Decoder vollständig dekodiert.

Der Capture-Lauf ist unter:

`docs/research/weatherhub-dumps/20260903-163837/`

archiviert.

Der zugehörige Index ist:

`docs/research/weatherhub-dumps/20260903-163837/index.json`

Ergebnis:

- erwartete Geräte: 19
- gefundene Geräte: 19
- HTTP-Erfolg: 19/19
- alle Responses dekodierbar
- alle Geräte liefern zwei Messreihen

Der Cross-Dump-Abgleich bestätigt zwei Sensorfamilien:

### ID-Typ 0E – TFA 30.3312.02

Genau ein Gerät verwendet diesen Sensortyp.

Der Sensor besitzt zwei Messkanäle:

- `Temperature`
- `Humidity`

Der Sensor wird im vorliegenden Bestand in einem Kühler eingesetzt.

Die Payload bestätigt damit nicht nur die Existenz des ID-Typs `0E`, sondern auch
die konkrete Kanalstruktur der Sensorfamilie.

### ID-Typ 01 – TFA 30.3313.02

Die übrigen 18 Geräte gehören zu dieser Sensorfamilie.

Jedes Gerät besitzt zwei Temperaturkanäle:

- `Temperature1` – interner Temperaturfühler des WeatherHub-Geräts. Dieser befindet
  sich außerhalb des überwachten Kühlschrank-/Gefrierraums und entspricht damit
  praktisch der Raum-/Umgebungstemperatur.
- `Temperature2` – externer Kabelfühler. Dieser befindet sich im überwachten
  Kühlschrank bzw. Gefrierschrank und liefert die eigentliche Geräte-/Innenraumtemperatur.

Damit ist die bisher nur anhand einzelner Sensoren angenommene Zuordnung der
ID-Typen über den vollständigen Bestand von 19 Geräten konsistent bestätigt.

Für die spätere Normalisierung sollte daher nicht nur der `SeriesID`, sondern auch
der Sensor-/ID-Typ berücksichtigt werden:

`ID-Typ 0E`
→ Temperature + Humidity

`ID-Typ 01`
→ Temperature1 (Umgebung) + Temperature2 (überwachter Innenraum)

Die konkrete fachliche Bezeichnung der Kanäle ist eine Interpretation aus
Sensorhardware, Einsatzort und Payload-Struktur. Die technischen `SeriesID`-Namen
bleiben die unmittelbar aus der Payload belegten Werte.

---

## 40.4 Device ID vs. Anzeigename

Die Untersuchung bestätigt die geplante Trennung zwischen technischer
Identität und Anzeigeinformationen.

Beispiel:

    Device ID:
        0169706EBE2C

    aktueller Name:
        R1313 - Praktikumsraum

Die `Device ID` wird als stabile Referenz für historische Messdaten
verwendet.

Der `Name` wird als veränderliches Metadatum behandelt.

Wenn der Name eines Sensors im WeatherHub-Backend geändert wird, bleiben
historische Messdaten dadurch weiterhin eindeutig demselben Gerät
zugeordnet.

Konzeptionell:

    device_id = stabile technische Identität

    name = aktueller Anzeigename

    series_id = Messreihe innerhalb des Geräts

Damit ergibt sich:

    device_id
        |
        +--> name
        |
        +--> series_id
        |      |
        |      +--> measurements
        |
        +--> health/status

---

## 40.5 Gleiche Namen sind zulässig

Die Device-Liste zeigt bereits, dass unterschiedliche Device-IDs denselben
Anzeigenamen besitzen können.

Beispiel:

    0E74A4597B54
        R1304 - DryAger - 17 °C, 80% rH

    016783F33A2A
        R1304 - DryAger - 17 °C, 80% rH

Damit ist zusätzlich praktisch bewiesen:

> Der Anzeigename darf nicht als Primary Key oder eindeutiger Identifier
> verwendet werden.

Ausschließlich die `deviceID` darf zur eindeutigen Identifikation eines
WeatherHub-Geräts verwendet werden.

---

## 40.6 Konsequenz für den automatisierten Abruf

Der produktive Ablauf kann damit vollständig dynamisch aufgebaut werden:

    LOGIN
      ↓
    GET /Devices
      ↓
    19 Devices
      ↓
    foreach Device
      |
      +--> deviceID
      +--> name
      |
      ↓
    POST /Devices/SparkLineChartData
      |
      ↓
    Base64
      ↓
    Decoder
      ↓
    normalisierte Messdaten

Die Anzahl der Sensoren muss dabei nicht fest auf `19` codiert werden.

Wenn später ein Sensor hinzugefügt oder entfernt wird, soll der nächste
Abrufzyklus automatisch die aktuelle Device-Liste übernehmen.

Damit wird aus:

    19 fest codierte Sensoren

ein:

    N dynamisch ermittelte Sensoren

---

## 40.7 Device Discovery und Persistenz

Für die spätere Datenhaltung empfiehlt sich eine Trennung zwischen
Gerätestammdaten und Messdaten.

Beispiel:

    devices
        device_id
        name
        first_seen
        last_seen

    measurements
        device_id
        series_id
        timestamp
        value

Bei jedem erfolgreichen `/Devices`-Abruf wird:

    device_id vorhanden?
        |
        +-- nein → neues Device anlegen
        |
        +-- ja  → name aktualisieren

Dadurch können Umbenennungen des Sensors automatisch übernommen werden.

Historische Messdaten benötigen keine Änderung.

---

## 40.8 Status der Device Discovery

Die Device Discovery ist technisch verifiziert und kein offener
Reverse-Engineering-Punkt mehr.

Der produktive Ablauf verwendet:

    POST /Account/LogOn
        ↓
    authentifizierte WebRequestSession
        ↓
    GET /Devices
        ↓
    HTML-Geräteübersicht
        ↓
    Device Discovery
        ↓
    deviceID + name
        ↓
    SparkLineChartData

Im Cross-Dump-Test vom 03.09.2026 wurden 19 von 19 erwarteten Geräten
erfolgreich ermittelt und anschließend abgefragt.

Für die produktive Implementierung bleibt ausschließlich die technische
Robustheit der HTML-Extraktion als Engineering-Aufgabe relevant.

Die Discovery muss deshalb mindestens:

- gültige Device-IDs validieren
- Duplikate erkennen
- die gefundene Geräteanzahl protokollieren
- unerwartete HTML-Strukturen erkennen
- den Anzeigenamen als veränderliches Metadatum behandeln
- die `deviceID` als technische Identität verwenden

Die Anzahl der Geräte darf nicht fest auf 19 codiert werden.

Die aktuelle Zahl 19 ist lediglich der zum Zeitpunkt des Tests beobachtete
Bestand.

---

## 41. Automatisierter N-Sensor-Abruf

Nach erfolgreicher Device Discovery werden alle aktuell auf `/Devices`
vorhandenen Geräte abgefragt.

Die Anzahl der Geräte wird nicht fest im Code hinterlegt.

Konzeptionell:

    GET /Devices
        ↓
    devices[]
        ↓
    foreach device
        |
        +--> deviceID
        +--> name
        |
        ↓
    POST /Devices/SparkLineChartData
        ↓
    Base64
        ↓
    Decoder
        ↓
    normalisierte Messdaten

Die gleiche authentifizierte `$session` wird für sämtliche Sensorrequests
verwendet.

Ein Fehler bei einem einzelnen Sensor darf den gesamten Abrufzyklus nicht
abbrechen.

Beispiel:

    Device 1  → OK
    Device 2  → OK
    Device 3  → Decode Error
    Device 4  → OK
    ...
    Device N  → OK

Der Adapter soll den Fehler von Device 3 separat erfassen und die übrigen
Geräte trotzdem weiterverarbeiten.

---

## 42. Speicherung

Für die Entwicklung können Rohresponses zunächst getrennt gespeichert
werden:

    WeatherHub\
        SparkLine\
            <deviceID>.txt

Für den produktiven Betrieb ist eine solche Rohdatenablage vermutlich nicht
bei jedem Zyklus notwendig.

Sinnvoller ist langfristig:

    HTTP Response
        ↓
    Decoder
        ↓
    normalisierte Messdaten
        ↓
    LoggerPi Data Model
        ↓
    persistente Speicherung

Rohpayloads können bei Debugging oder Fehlerfällen optional und zeitlich
begrenzt gespeichert werden.

---

## 43. Decoder als eigenständige Komponente

Der Decoder darf weder HTTP-Kommunikation noch Credentials,
Session-Verwaltung oder LoggerPi-spezifische Normalisierung enthalten.

Die Verantwortlichkeiten werden strikt getrennt.

### WeatherHubClient

Verantwortlich für:

- Login
- Session-Verwaltung
- Authentifizierungsprüfung
- Device Discovery
- Abruf von `SparkLineChartData`
- HTTP-Fehlerbehandlung auf Transportebene

Der Client kennt die WeatherHub-Endpunkte, aber nicht die interne
Bedeutung der Messreihen im LoggerPi Data Model.

### WeatherHubDecoder

Verantwortlich für:

- Base64-Dekodierung
- Binary Parsing
- Wire-Type-Verarbeitung
- `ChartData`
- `ChartSeries`
- `ChartDataset`
- Timestamp-/Value-Dekodierung
- bekannte Status-/Alert-Felder
- Erkennung unbekannter bzw. nicht unterstützter Felder

Der Decoder arbeitet idealerweise ausschließlich auf übergebenen
Payload-Daten und ist damit ohne Live-Server testbar.

### WeatherHubAdapter

Verantwortlich für:

- Kombination aus Device-Metadaten und Decoder-Ergebnis
- Zuordnung von ID-Typ und erwarteten Kanälen
- Normalisierung der Series
- Mapping von Statusinformationen
- Erzeugung des gemeinsamen LoggerPi Data Models

Der Adapter darf WeatherHub-spezifische Begriffe kennen.

Der Core darf diese Begriffe dagegen nicht benötigen.

Der Datenfluss lautet damit:

    WeatherHubClient
        ↓
    raw SparkLine payload
        ↓
    WeatherHubDecoder
        ↓
    decoded WeatherHub structure
        ↓
    WeatherHubAdapter
        ↓
    common LoggerPi Data Model

---

## 44. Vorgesehene Adapterstruktur

Konzeptionell:

    WeatherHubClient
        ├── Login()
        ├── GetDevices()
        └── GetSparkLineChartData(deviceID)

    WeatherHubDecoder
        ├── DecodeBase64()
        ├── DecodeChartData()
        ├── DecodeChartSeries()
        └── DecodeChartDataset()

    WeatherHubAdapter
        ├── Fetch()
        ├── Normalize()
        └── Return Data Model

Dadurch kann der Decoder mit gespeicherten Response-Dateien getestet werden,
ohne jedes Mal den WeatherHub-Server aufzurufen.

---

## 45. Gemeinsames Data Model

WeatherHub-spezifische Begriffe dürfen nicht in das allgemeine LoggerPi
Data Model übernommen werden.

Der Adapter transformiert die WeatherHub-Struktur in ein neutrales Modell.

Ein normalisiertes Sensorergebnis sollte mindestens folgende Informationen
enthalten:

    Sensor
      ├── sensor_id
      ├── name
      ├── source
      ├── measurements[]
      └── health

    Measurement
      ├── timestamp
      ├── type
      └── value

    Health
      ├── connection
      ├── battery
      ├── sensor_error
      └── status

Für WeatherHub gilt:

    sensor_id
        = deviceID

    name
        = aktueller Anzeigename aus `/Devices`

    source
        = WeatherHub

Die historische Messreihe wird über:

    sensor_id
    +
    measurement type
    +
    timestamp

identifiziert.

Die WeatherHub-spezifischen Begriffe:

    ChartData
    ChartSeries
    ChartDataset
    SeriesID
    LowBattery
    ConnectionLost
    AlertIsActive

dürfen nicht Bestandteil des allgemeinen Core-Modells werden.

Sie dürfen ausschließlich innerhalb des WeatherHub-Adapters bzw. seiner
internen Zwischenmodelle verwendet werden.

---

## 46. Monitoring- und Health-Logik

Der WeatherHub-Adapter übernimmt die Normalisierung der vom WeatherHub
gelieferten Statusinformationen.

Er entscheidet jedoch nicht über die endgültige Alarmierung.

Es wird zwischen direkt beobachteten Zuständen und lokal abgeleiteten
Zuständen unterschieden.

### Direkt aus WeatherHub

Beispielsweise:

    LowBattery = true
        ↓
    battery.status = "warning"

    ConnectionLost = true
        ↓
    connection.status = "lost"

Diese Informationen stammen direkt aus der WeatherHub-Payload.

### Lokal im LoggerPi abgeleitet

Zusätzlich kann der Core anhand eigener Informationen Zustände ableiten.

Beispielsweise:

    letzter gültiger Messpunkt zu alt
        ↓
    status = "stale"

oder:

    kompletter Abrufzyklus fehlgeschlagen
        ↓
    source / collection status = "error"

Damit bleibt die Verantwortlichkeit klar:

    WeatherHub Adapter
        ↓
    beobachtete und normalisierte Zustände

    Monitoring Core
        ↓
    Health-State
        ↓
    Alerting

---

## 47. Fehlerbehandlung

Der produktive Adapter muss mindestens folgende Fälle behandeln:

### Login-Fehler

    Login
      ↓
    nicht authentifiziert
      ↓
    Zyklus schlägt kontrolliert fehl

### Session-Ablauf

    Request
      ↓
    Authentifizierung nicht mehr gültig
      ↓
    neu einloggen
      ↓
    Request wiederholen

### Einzelner Sensor fehlerhaft

    Sensor 7
      ↓
    HTTP-/Decode-Fehler

Die anderen Sensoren sollen trotzdem verarbeitet werden.

### Ungültige Payload

    HTTP 200
      ↓
    Base64 ungültig
      ↓
    Decode-Fehler

Dieser Fehler muss pro Sensor protokolliert werden.

### Unbekannter ID-Typ

    Device
      ↓
    unbekannte Payload-Struktur

Der Adapter soll den Sensor nicht stillschweigend verwerfen, sondern einen
klaren Decode-/Compatibility-Status erzeugen.

### Ergebnis pro Device

Der Abrufzyklus soll für jedes entdeckte Gerät ein eigenes Ergebnis
erzeugen.

Beispiel:

    Device A → success
    Device B → success
    Device C → decode_error
    Device D → success

Ein Fehler bei Device C darf Device D und die folgenden Geräte nicht
verhindern.

Ein Device-Ergebnis sollte deshalb mindestens einen Status enthalten:

    success
    http_error
    authentication_error
    invalid_base64
    decode_error
    unsupported_id_type
    unexpected_payload
    stale_or_missing_data

Die konkrete Zuordnung zum Monitoring-State erfolgt anschließend im
Monitoring-Core.

---

## 48. Logging

Produktionslogs dürfen keine sensiblen Authentifizierungsinformationen
enthalten.

Insbesondere niemals loggen:

- Username
- Passwort
- `.ASPXAUTH`
- andere Session-Cookies
- vollständige Authorization-Header

Sinnvoll sind dagegen:

    timestamp
    deviceID
    HTTP status
    decode status
    measurement count
    last measurement timestamp
    health state
    error category

Bei Debugging können Rohpayloads gezielt lokal gespeichert werden, sofern
sie nicht unkontrolliert in ein Repository gelangen.

---

## 49. Sicherheit

Die Zugangsdaten müssen außerhalb des Quellcodes gespeichert werden.

Nicht in:

    Git
    Markdown
    Logs
    Beispielcode
    Response-Dateien
    Screenshots

Die lokale Konfiguration soll stattdessen über eine geeignete
Secret-/Credential-Quelle erfolgen.

Auch echte `.ASPXAUTH`- oder andere Session-Cookie-Werte dürfen niemals in
Repository-Dateien übernommen werden.

---

## 50. Teststrategie

Die weitere Entwicklung sollte in Stufen erfolgen.

### Test 1 – Login

    Login
      ↓
    Session
      ↓
    /Devices = HTTP 200

### Test 2 – ein Sensor

    deviceID
      ↓
    SparkLineChartData
      ↓
    HTTP 200
      ↓
    Base64
      ↓
    Decoder

### Test 3 – mehrere Sensoren

    deviceID[]
      ↓
    mehrere Requests
      ↓
    alle Responses dekodieren

### Test 4 – alle 19 Sensoren

    19 deviceIDs
      ↓
    19 Requests
      ↓
    19 Decodergebnisse

### Test 5 – Fehlerfälle

Gezielt testen:

- ungültige Zugangsdaten
- abgelaufene Session
- ungültige Device-ID
- HTTP-500-Response
- ungültige Base64-Payload
- unbekannte Payload-Struktur
- einzelner nicht erreichbarer Sensor

### Test 6 – Scheduler

    alle 15 Minuten
        ↓
    vollständiger Abrufzyklus
        ↓
    persistente Daten
        ↓
    Monitoring

---

## 51. 15-Minuten-Scheduler

Für den ersten produktiven Betrieb ist ein periodischer Prozess
ausreichend:

    ┌───────────────────────────────┐
    │ alle 15 Minuten               │
    └───────────────┬───────────────┘
                    ↓
                  Login
                    ↓
              Device-Liste
                    ↓
              Sensorabrufe
                    ↓
                 Decoder
                    ↓
              Normalisierung
                    ↓
              Data Model
                    ↓
             Monitoring/Storage
                    ↓
                  Ende

Beim nächsten Zyklus wird zunächst wieder eine frische Session verwendet.

---

## 52. Spätere Optimierung: Session-Reuse

Wenn der erste stabile Betrieb funktioniert, kann die Session-Wiederverwendung
optimiert werden.

Möglicher Ablauf:

    vorhandene Session
          ↓
       Requests
          ↓
    Session gültig?
       /       \
     ja         nein
     ↓           ↓
  weiter      Login
                ↓
            neue Session

Die Optimierung ist bewusst nachrangig.

Robustheit hat Vorrang vor der Einsparung einzelner Login-Requests.

---

## 53. Aktueller technischer Baseline-Test

Der derzeitige Baseline-Test lautet:

    # Session
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

    # Login
    $login = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri "https://www.wh-observer.de/Account/LogOn" `
        -Method POST `
        -WebSession $session `
        ...

    # Session prüfen
    $devices = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri "https://www.wh-observer.de/Devices" `
        -Method GET `
        -WebSession $session

    # Sensordaten
    $response = Invoke-WebRequest `
        -UseBasicParsing `
        -Uri "https://www.wh-observer.de/Devices/SparkLineChartData" `
        -Method POST `
        -WebSession $session `
        -ContentType "application/json; charset=utf-8" `
        -Body '{"deviceID":"016783F33A2A"}'

Erwartetes Ergebnis:

    Login       → erfolgreich
    /Devices    → HTTP 200
    Sparkline   → HTTP 200
    Payload     → Base64
    Decoder     → erfolgreich

Dieser Test ist die aktuelle technische Referenz.

---

## 54. Verifizierter End-to-End-Test vom 02.09.2026

Am 02.09.2026 wurde der komplette Zugriff auf WeatherHub-Observer
erfolgreich reproduziert.

### 54.1 Login

Der Login erfolgt über:

    POST https://www.wh-observer.de/Account/LogOn

Verwendete Formularfelder:

    Username
    Password
    Lang

Für Tests werden die Zugangsdaten interaktiv über PowerShell
`Get-Credential` bereitgestellt.

Es werden keine Zugangsdaten im Repository gespeichert.

Bei erfolgreichem Login liefert der Server HTTP 200 und leitet auf
`/devices` weiter.

Die für den Login verwendete `WebRequestSession` muss für die
folgenden Requests wiederverwendet werden.

### 54.2 Authentifizierte Session prüfen

Anschließend:

    GET https://www.wh-observer.de/Devices

liefert HTTP 200.

Die Response enthält die authentifizierte Geräteübersicht.

Eine nicht authentifizierte Session liefert stattdessen die
Sign-in-Seite mit:

    <title>WeatherHub-Observer | Sign in</title>

Damit kann der Authentifizierungsstatus ohne Zugriff auf Cookies
direkt anhand der Response geprüft werden.

### 54.3 Geräteidentität

Die `/Devices`-Seite enthält für jedes Gerät mindestens:

    deviceID
    Anzeigename
    Timestamp
    Sensor-/Messreiheninformationen

Beispiel eines erfolgreich ausgelesenen Geräts:

    Name: R1313 - Praktikumsraum
    ID:   0169706EBE2C

Die `deviceID` wird als stabile technische Identität verwendet.

Der Anzeigename ist dagegen veränderliches Metadatum und darf sich
im WeatherHub-Backend ändern.

Die historische Zuordnung von Messdaten erfolgt deshalb immer über
`deviceID` und nicht über den Anzeigenamen.

### 54.3 Device Discovery – 19 Geräte

Die authentifizierte `/Devices`-Seite wurde anschließend automatisch
ausgewertet.

Ergebnis:

    Devices gefunden: 19

Für jedes Gerät konnten mindestens folgende Informationen ermittelt werden:

    deviceID
    name

Damit ist die automatische Device Discovery praktisch verifiziert.

Die vollständige zum Testzeitpunkt ermittelte Liste ist in Abschnitt 40.2
dokumentiert.

Wichtig ist, dass die Liste nicht als statische Gerätekonfiguration
verstanden wird.

Die `/Devices`-Seite stellt den aktuellen Zustand des WeatherHub-Backends
dar und soll bei einem produktiven Abrufzyklus erneut ausgewertet werden.

Die Anzahl der Geräte ist daher dynamisch.

### 54.4 Device-ID als stabile Identität

Die Tests zeigen außerdem, dass Anzeigenamen nicht eindeutig sein müssen.

Beispielsweise besitzen:

    0E74A4597B54
    016783F33A2A

beide den Namen:

    R1304 - DryAger - 17 °C, 80% rH

Daraus folgt:

    deviceID → Primary Identifier
    name     → Display Metadata

Der Anzeigename darf jederzeit im WeatherHub-Backend geändert werden,
ohne dass dadurch die historische Zuordnung von Messdaten verändert wird.

### 54.5 Sparkline-Endpunkt

Die Sensordaten werden über:

    POST https://www.wh-observer.de/Devices/SparkLineChartData

abgerufen.

Request:

    Content-Type: application/json; charset=utf-8

Body:

    {"deviceID":"<DEVICE_ID>"}

Die Response wird in PowerShell als:

    System.Byte[]

geliefert.

Die enthaltenen Bytes stellen UTF-8-kodierte Base64-Daten dar.

Beispielanfang einer Response:

    CugHCgxUZW1wZXJhdHVyZTESEgkAgE/6HwZ6QhEzMzMz...

Die getestete Payload hatte eine Länge von 2676 Zeichen.

### 54.6 Base64-Decoder

Die Base64-Payload kann mit:

    Convert-WeatherHubBase64

aus `decode-weatherhub-v2.ps1` erfolgreich dekodiert werden.

Der Decoder liefert ein `PSCustomObject` mit einer `Series`-Collection.

Beim erfolgreichen Test:

    Chart type: System.Management.Automation.PSCustomObject
    Series count: 2

### 54.7 Dekodierte Messreihen

Der Test lieferte:

    SeriesID: Temperature1
    Datasets: 46

    SeriesID: Temperature2
    Datasets: 46

Beispielwerte:

    Temperature1:
        22.2
        22.3
        22.4
        22.6
        22.6

    Temperature2:
        -25.7
        -26.1
        -26.3
        -26.5
        -26.6

Jedes Dataset enthält unter anderem:

    Timestamp
    Value

Die Timestamps werden als Unix-Zeit in Millisekunden geliefert.

### 54.8 Aktueller technischer Datenfluss

Der derzeit verifizierte Datenfluss lautet:

    Get-Credential
        |
        v
    POST /Account/LogOn
        |
        v
    WebRequestSession
        |
        v
    GET /Devices
        |
        +--> deviceID
        +--> device name
        |
        v
    POST /Devices/SparkLineChartData
        |
        v
    Base64
        |
        v
    Convert-WeatherHubBase64
        |
        v
    ChartData
        |
        +--> Temperature1
        +--> Temperature2
        +--> Datasets
                 |
                 +--> Timestamp
                 +--> Value

Dieser Ablauf wurde am 02.09.2026 erfolgreich gegen den
WeatherHub-Observer-Server getestet.

### 54.9 Sicherheits-/Repository-Regeln

Nicht in das Repository aufnehmen:

- WeatherHub-Benutzername
- WeatherHub-Passwort
- Session-Cookies
- vollständige authentifizierte Responses
- vollständige reale Sensorpayloads

Für reproduzierbare Tests werden Credentials interaktiv über
`Get-Credential` bezogen.

### 54.10 Konsequenz für die spätere Datenhaltung

Die spätere Datenhaltung soll die technische Geräteidentität von
den veränderlichen Anzeigeinformationen trennen.

Empfohlene Struktur:

    devices
        device_id
        name
        last_seen

    measurements
        device_id
        series_id
        timestamp
        value

`device_id` ist die stabile technische Identität.

`name` wird bei jedem erfolgreichen Geräteabgleich aktualisiert.

`series_id` identifiziert die Messreihe innerhalb eines Geräts.

Eine Änderung des Anzeigenamens im WeatherHub-Backend erfordert
dadurch keine Änderung historischer Messdaten.

---

## 55. Reproduktionsmaterial

Eine konkrete Sparkline-Response wurde lokal gespeichert unter:

    C:\Users\Lorc\WeatherHub\sparkline-016783F33A2A.txt

Solche Dateien können reale Sensorwerte enthalten und gehören deshalb
nicht automatisch in das öffentliche Repository.

Insbesondere dürfen keine Zugangsdaten oder Session-Cookies gespeichert
werden.

Für automatisierte Unit-/Regressionstests sollen möglichst bereinigte,
nicht-sensitive Testproben verwendet werden.

Die Decoderlogik kann mit solchen Fixtures unabhängig vom Live-Server
getestet werden.

## 55.1 Decoder-Test-Fixtures

Der Decoder muss unabhängig vom Live-WeatherHub-Server testbar sein.

Die Research-Dumps unter:

    docs/research/weatherhub-dumps/

dienen als technische Referenz und Regressionstestmaterial.

Für automatisierte Tests sollen daraus jedoch gezielte, bereinigte Fixtures
abgeleitet werden.

Geeignete Fixtures sollten mindestens abdecken:

- ID-Typ `0E`
- ID-Typ `01`
- Temperatur-Series
- Humidity-Series
- mehrere Datasets
- Timestamp + Value
- optionale Bool-Felder
- fehlende optionale Felder
- unbekannte Felder
- ungültige Base64-Payload
- beschädigte Binärpayload
- unbekannter ID-Typ

Der Decoder-Test darf keinen Netzwerkzugriff benötigen.

Damit kann beispielsweise getestet werden:

    Fixture
        ↓
    Base64
        ↓
    WeatherHubDecoder
        ↓
    erwartete ChartData-Struktur

Der Live-Server wird ausschließlich für Integrationstests des
`WeatherHubClient` bzw. des vollständigen Adapters benötigt.

---

## 56. Status der ursprünglichen Untersuchung

Die ursprüngliche Untersuchung ging von folgendem Stand aus:

    Browser
        ↓
    ChartData
        ↓
    doppelte Base64-Dekodierung
        ↓
    unbekannte Binärstruktur
        ↓
    Timestamp noch offen

Dieser Stand ist inzwischen überholt.

Der aktuelle Stand ist:

    Login
        ↓
    authentifizierte WebSession
        ↓
    /Devices
        ↓
    SparkLineChartData
        ↓
    Base64
        ↓
    Binärdaten
        ↓
    ChartData
        ↓
    ChartSeries
        ↓
    ChartDataset
        ↓
    Timestamp / Value / Status
        ↓
    normalisierbare Sensordaten

Die Dokumentation wurde entsprechend von einer reinen Reverse-Engineering-
Untersuchung zu einer technischen Integrationsdokumentation erweitert.

---

## 57. Aktueller Gesamtstand

Der entscheidende Meilenstein ist erreicht:

> Der relevante WeatherHub-Observer-Datenpfad ist praktisch reproduziert.

Bewiesen ist die Kette:

    Login
      ↓
    authentifizierte $session
      ↓
    /Devices
      ↓
    Device-ID
      ↓
    /Devices/SparkLineChartData
      ↓
    HTTP 200
      ↓
    Base64
      ↓
    Binärdaten
      ↓
    vorhandener Decoder
      ↓
    Messwerte + Statusinformationen

Der nächste Entwicklungsabschnitt ist deshalb nicht mehr primär
Reverse Engineering.

Es geht jetzt um:

- saubere Client-/Adapterstruktur
- automatische Device-Liste
- Abruf aller 19 Sensoren
- robuste Fehlerbehandlung
- generische ID-Typ-/Kanalbehandlung
- Normalisierung in das gemeinsame Data Model
- Persistenz
- Scheduler
- Monitoring und Alerting

---

## 58. Nächste konkrete Schritte

Die Reverse-Engineering-Phase für den grundlegenden Sparkline-Datenpfad ist
abgeschlossen.

Die nächsten Schritte sind daher:

1. `WeatherHubClient` aus dem Referenzskript extrahieren.
2. Login und Session-Verwaltung kapseln.
3. Authentifizierungsstatus zuverlässig prüfen.
4. `GetDevices()` mit robuster HTML-Extraktion implementieren.
5. `GetSparkLineChartData(deviceID)` implementieren.
6. `WeatherHubDecoder` aus `decode-weatherhub-v2.ps1` herauslösen.
7. Decoder mit gespeicherten Test-Fixtures unabhängig vom Server testen.
8. WeatherHub-ID-Typ-/Kanal-Mapping als separate Konfiguration implementieren.
9. `WeatherHubAdapter` für die Normalisierung implementieren.
10. Health-/Statusinformationen in das neutrale Modell überführen.
11. Fehler pro Device isolieren und protokollieren.
12. Ergebnisse in das gemeinsame LoggerPi Data Model mappen.
13. Persistenz integrieren.
14. vollständigen End-to-End-Test mit allen aktuell vorhandenen Geräten durchführen.
15. 15-Minuten-Scheduler integrieren.
16. Retry-/Session-Recovery implementieren.
17. anschließend Monitoring und Alerting auf dem OtterPi integrieren.

Die bereits verifizierten Punkte:

- Login
- authentifizierte Session
- Device Discovery
- dynamische Device-Liste
- 19/19 Geräteabruf
- Base64-Dekodierung
- ChartData-Dekodierung
- ID-Typen `0E` und `01`

werden dabei nicht erneut als offene Forschungsaufgaben behandelt.

---

## 59. Wiedereinstiegspunkt

Der aktuelle Wiedereinstiegspunkt ist die verifizierte Referenzimplementierung
und nicht mehr die ursprüngliche Reverse-Engineering-Untersuchung.

Nicht mehr erforderlich für den grundlegenden Datenzugriff sind:

    Browser DevTools
    Curl-Experimente
    manuelles Kopieren von Cookies
    Suche nach dem Timestamp-Format
    manuelle Eingabe der Device-IDs

Der aktuelle technische Ausgangspunkt lautet:

    Get-Credential
          ↓
    POST /Account/LogOn
          ↓
    authentifizierte WebRequestSession
          ↓
    GET /Devices
          ↓
    automatische Device Discovery
          ↓
    N dynamisch ermittelte Geräte
          ↓
    POST /Devices/SparkLineChartData
          ↓
    Base64
          ↓
    WeatherHubDecoder
          ↓
    ChartData / ChartSeries / ChartDataset
          ↓
    WeatherHubAdapter
          ↓
    gemeinsames LoggerPi Data Model

Die nächste Implementierungsaufgabe ist damit die Überführung des bereits
funktionierenden PowerShell-Golden-Paths in produktiv nutzbare Komponenten.

Priorität:

    1. Client
    2. Decoder
    3. Adapter
    4. Tests
    5. Storage
    6. Scheduler
    7. Monitoring

---

## 60. Reproduktionsskript test-weatherhub-observer-v4.ps1

Das Skript:

    test-weatherhub-observer-v4.ps1

ist das aktuelle technische Reproduktionsskript für den
WeatherHub-Observer-Zugriff.

Es dient als Referenzimplementierung für den aktuell verifizierten Ablauf:

    Get-Credential
        ↓
    POST /Account/LogOn
        ↓
    authentifizierte WebRequestSession
        ↓
    GET /Devices
        ↓
    automatische Device Discovery
        ↓
    POST /Devices/SparkLineChartData
        ↓
    Base64-Payload
        ↓
    Convert-WeatherHubBase64
        ↓
    dekodierte ChartData

Das Skript ist von der späteren produktiven Adapterimplementierung
zu unterscheiden.

Es ist zunächst ein technisches Test-/Reproduktionsskript und dient dazu,
den funktionierenden Datenzugriff gegen den Live-Server nachvollziehbar
zu halten.

Die produktive Implementierung soll die darin verifizierte Logik später
in getrennte Komponenten überführen:

    WeatherHubClient
    WeatherHubDecoder
    WeatherHubAdapter

Das Testskript bleibt dabei als Regressionstest bzw. Referenz erhalten.

---

## 61. Vollständiger Cross-Dump-Test vom 03.09.2026

Am 03.09.2026 wurde der bisher wichtigste Regressionstest durchgeführt:

Das neue Capture-Skript

`docs/research/capture-weatherhub-research-all.ps1`

ruft automatisch die aktuell vorhandenen WeatherHub-Observer-Geräte ab und
speichert für jedes Gerät die Rohpayload sowie die dekodierten Ergebnisse.

Zusätzlich steht für die Untersuchung einzelner Sparkline-Payloads das Skript

`docs/research/dump-weatherhub-sparkline.ps1`

zur Verfügung.

### 61.1 Vollständiger Abruf

Der Testlauf:

`20260903-163837`

enthält:

- 19 erwartete Geräte
- 19 tatsächlich gefundene Geräte
- 19 erfolgreiche HTTP-Responses
- 19 dekodierte Ergebnisse
- jeweils zwei Messreihen pro Gerät

Die Ergebnisse sind unter:

`docs/research/weatherhub-dumps/20260903-163837/`

gespeichert.

Der maschinenlesbare Gesamtindex ist:

`docs/research/weatherhub-dumps/20260903-163837/index.json`

Damit ist der komplette Datenabruf nicht mehr nur für einzelne exemplarische
Sensoren reproduziert, sondern für den gesamten aktuell vorhandenen Sensorbestand.

### 61.2 Bestätigte Sensorfamilien

Der Cross-Dump-Abgleich bestätigt:

`ID-Typ 0E`
→ TFA 30.3312.02
→ `Temperature` + `Humidity`
→ 1 Sensor im aktuellen Bestand

`ID-Typ 01`
→ TFA 30.3313.02
→ `Temperature1` + `Temperature2`
→ 18 Sensoren im aktuellen Bestand

Bei ID-Typ `01` entspricht `Temperature1` dem internen Fühler des WeatherHub-
Geräts und damit praktisch der Umgebungstemperatur außerhalb des überwachten
Kühlschrank-/Gefrierraums.

`Temperature2` stammt vom externen Kabelfühler und entspricht der Temperatur
innerhalb des überwachten Kühlschranks bzw. Gefrierschranks.

### 61.3 FormattedMeasurement / ChartSeries.field 5

Die vollständigen Dumps liefern zusätzlich eine wichtige Bestätigung für
`ChartSeries.field 5`.

Das Feld ist als:

`FormattedMeasurement`

rekonstruiert.

Beobachtete Beispiele:

`Temperature` → `"17,0°C"`

`Humidity` → `"61 %"`

`Temperature1` → `"22,3°C"`

Das Feld enthält damit offenbar den serverseitig bereits formatierten aktuellen
Messwert der jeweiligen Series.

Die historischen numerischen Messpunkte liegen dagegen in:

`ChartDataset.field 2 = Value`

`FormattedMeasurement` ist daher nicht als Ersatz für `Value` zu betrachten.
Vielmehr handelt es sich sehr wahrscheinlich um einen für die Dashboard-/Card-
Darstellung vorbereiteten Anzeigewert inklusive Einheit und lokaler Formatierung.

Ein direkter Vergleich mit dem tatsächlich gerenderten Dashboard ist noch
ausstehend; deshalb bleibt die Bezeichnung „sehr wahrscheinlich“ bewusst erhalten.

### 61.4 Neuer technischer Status

Mit diesem Test ist der Reverse-Engineering-Teil für den grundlegenden
Sparkline-Datenabruf weitgehend abgeschlossen.

Bewiesen ist nun:

`Login`
→ `WebRequestSession`
→ `/Devices`
→ automatische Device Discovery
→ 19 Geräte
→ `SparkLineChartData`
→ Base64
→ Binärdaten
→ `ChartData`
→ `ChartSeries`
→ zwei Series pro Gerät
→ `Timestamp` + `Value`
→ Statusinformationen
→ `FormattedMeasurement`

Der nächste Arbeitsschritt ist damit nicht mehr die Suche nach weiteren
grundlegenden Datenstrukturen, sondern die saubere technische Normalisierung
der bereits bekannten Daten in den WeatherHub-Adapter.

### 61.5 Engineering-Meilenstein

Der Cross-Dump-Test vom 03.09.2026 markiert den Übergang von der
Reverse-Engineering-Phase in die Implementierungsphase.

Der WeatherHub-Sparkline-Datenpfad gilt für die aktuell untersuchten
Sensorfamilien als ausreichend verstanden, um mit der produktiven
Adapterimplementierung zu beginnen.

Die Implementierung muss dabei nicht die komplette historische
Untersuchung reproduzieren.

Sie benötigt lediglich die stabil verifizierten Schritte:

    Authentication
        ↓
    Device Discovery
        ↓
    SparkLine Request
        ↓
    Base64 Decode
        ↓
    Chart Decode
        ↓
    WeatherHub Mapping
        ↓
    LoggerPi Data Model

Nicht vollständig geklärte proprietäre Felder, insbesondere das
`Measurement`-Nested-Message und einzelne Alert-/Statusfelder, werden
zunächst nicht als Blockade behandelt.

Sie bleiben innerhalb des WeatherHub-Decoders optional und können später
ohne Änderung des grundlegenden Client-/Adapterdesigns ergänzt werden.

---

### 62. Trennung von SparkLineChartData und DeviceDetails/ChartData

Die erneute Analyse der bisherigen Reverse-Engineering-Ergebnisse
hat gezeigt, dass zwischen zwei WeatherHub-Endpunkten unterschieden
werden muss:

    POST /Devices/SparkLineChartData

und:

    POST /DeviceDetails/ChartData

Der aktuelle produktive Datenpfad basiert auf
`SparkLineChartData`.

Die aktuellen Dashboard-Captures zeigen für `ChartDataset` konsistent:

    field 1 = Timestamp
    field 2 = Value

Die früher dokumentierte Struktur mit `ChartDataset.field 1` bis
`ChartDataset.field 13` stammt möglicherweise aus der historischen
Untersuchung des `DeviceDetails/ChartData`-Pfads.

Alternativ ist möglich, dass die damaligen Fields 3–13 einem anderen
verschachtelten Message-Typ zugeordnet wurden.

Diese Zuordnung ist noch nicht abschließend bewiesen.

Daher gilt für die aktuelle Implementierung:

    SparkLineChartData
        → Field 1 = Timestamp
        → Field 2 = Value

Die historischen Fields 3–13 werden nicht in den Sparkline-Decoder
übernommen, solange ihre tatsächliche Herkunft nicht anhand der
historischen Dumps bestätigt wurde.

Als nächster Research-Schritt werden die beiden Payloads direkt
miteinander verglichen.

### 62.1 Realer Status-Cross-Check

Der Live-Capture unter:

    docs\research\weatherhub-dumps\20260904-014013\

enthält einen direkten Vergleich realer Dashboard-Zustände.

Beispiel OK:

    Device 0167554C25BE
        Dashboard: OK
        ConnectionLost: False
        CardStatus: NoAlert

Beispiel Warning:

    Device 0169706EBE2C
        Dashboard: Warning
        ConnectionLost: True
        CardStatus: Warning

Damit wurde die Zuordnung von `ConnectionLost` und `CardStatus` anhand
zweier realer Dashboard-Zustände gegengeprüft.

Die Beobachtung bestätigt die bisherige Interpretation für diese Fälle,
stellt aber noch keine vollständige Spezifikation aller möglichen
WeatherHub-Statuszustände dar.
