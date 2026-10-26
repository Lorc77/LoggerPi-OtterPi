# WeatherHub Gateway Proxy – Implementierungsentscheidungen

Dieses Dokument ergänzt die technische Spezifikation in:

`docs/research/weatherhub-gateway-proxy.md`

Es dokumentiert die fachlichen und architektonischen Entscheidungen für die
erste produktive Implementierung des WeatherHub Gateway Proxy.

Die hier dokumentierten Entscheidungen gelten als verbindlich, sofern sie
nicht ausdrücklich geändert werden.

---

# Herkunft und Zweck

Die ursprünglichen offenen Punkte wurden während der Analyse der
Spezifikation und der relevanten bestehenden Codebasis als OF-1 bis OF-7
identifiziert.

Die OF-Nummern werden zur Nachvollziehbarkeit beibehalten.

Die ursprüngliche Analyse ist **kein verbindlicher Implementierungsplan**.
Verbindlich sind die in diesem Dokument unter „Entscheidung“ festgehaltenen
Festlegungen.

Technische Detailfragen, die noch nicht ausreichend geklärt sind, werden
unter „Noch technisch zu klären“ dokumentiert.

---

# Entscheidungsübersicht

| ID | Thema | Entscheidung | Status |
|---|---|---|---|
| OF-1 | Cloud-Forward | Wird implementiert | Implementiert (optional) |
| OF-2 | Mehrere Gateways | Ja, mit robuster Deduplizierung | Entschieden |
| OF-3 | Sensor-Allowlist | Keine | Entschieden |
| OF-4 | Sensorfamilien | Nur ID01, ID02, ID03, ID04, ID07, ID0E, ID10 | Implementiert |
| OF-5 | ID04/ID10 | Kein Measurement, spätere State/Event-Verarbeitung | Entschieden |
| OF-6 | Stale-Logik | Konfigurierbar über `.env` | Noch offen |
| OF-7 | Service/Thread | Thread innerhalb bestehender Runtime bevorzugt | Implementiert |

---

# OF-1 – Cloud-Forward

## Ursprüngliche offene Frage

Der optionale Forward der Gateway-Payload an `www.data199.com` war laut
Spezifikation zunächst nicht implementiert und praktisch nicht verifiziert.

Offen war, ob der Cloud-Forward bereits in der ersten Implementierung
berücksichtigt werden soll oder zunächst vollständig entfällt.

## Entscheidung

Der Cloud-Forward wird bereits in der ersten produktiven Implementierung
berücksichtigt und implementiert.

Der lokale Empfang und die lokale Verarbeitung der WeatherHub-Gateway-Daten
dürfen dabei **nicht von der Erreichbarkeit des Cloud-Dienstes abhängig
sein**.

Ein Fehler, Timeout oder eine Nicht-Erreichbarkeit von
`www.data199.com` darf weder den lokalen Gateway-Empfang noch die lokale
Measurement-Verarbeitung blockieren.

## Anforderungen

- Gateway-Daten werden lokal unabhängig vom Cloud-Forward verarbeitet.
- Das Cloud-Forwarding darf den lokalen Empfang nicht blockieren.
- HTTP-Timeouts müssen begrenzt sein.
- Fehler beim Cloud-Forward dürfen die lokale Measurement-Pipeline nicht
  unterbrechen.
- Die erforderliche Konfiguration soll über `.env` bzw. die bestehende
  Konfigurationsmechanik erfolgen.
- Das Verhalten bei nicht erreichbarem Cloud-Dienst muss definiert und
  testbar sein.

## Noch technisch zu klären

- synchrones oder asynchrones Forwarding
- konkreter Timeout
- Retry-Verhalten
- Verhalten bei dauerhaft nicht erreichbarem Cloud-Dienst
- ob und wie Forwarding-Fehler geloggt werden
- ob Forwarding-Fehler dedupliziert bzw. rate-limitiert geloggt werden
  müssen

---

# OF-2 – Mehrere WeatherHub-Gateways

## Ursprüngliche offene Frage

Die Spezifikation beschreibt mehrere Gateways, insbesondere Gateway `.121`
und Gateway `.132`.

Offen war, ob der Listener gleichzeitig Verbindungen von mehreren
Gateway-IPs akzeptieren soll.

## Entscheidung

Mehrere WeatherHub-Gateways werden gleichzeitig unterstützt.

Die Gateway-Allowlist muss daher mehrere erlaubte Gateway-IPs aufnehmen
können.

Beispiel:

```text
WEATHERHUB_GATEWAY_ALLOWLIST=192.168.x.121,192.168.x.132
```

Das konkrete Format richtet sich nach der bestehenden
Konfigurationsmechanik.

## Deduplizierung

Da dasselbe Funktelegramm bzw. dieselbe Messung von mehreren Gateways
empfangen werden kann, muss eine robuste Deduplizierung redundanter
Empfänge implementiert werden.

Wichtig:

**Messungen dürfen nicht allein anhand ihres Messwertes dedupliziert
werden.**

Beispielsweise dürfen zwei zeitlich unterschiedliche Messungen eines
Sensors mit identischem Temperaturwert nicht als Duplikat verworfen
werden.

Die Deduplizierung muss stattdessen anhand der im WeatherHub-Protokoll
verfügbaren eindeutigen bzw. ausreichend eindeutigen Informationen
erfolgen.

Mögliche Kriterien können abhängig vom tatsächlichen Protokoll sein:

- Raw-Payload
- Sensor-ID
- Gateway-Payload
- Timestamp
- Sequenznummer
- weitere Protokollmerkmale
- Kombination mehrerer dieser Merkmale

Die konkrete Strategie muss anhand der Spezifikation und der tatsächlich
vorhandenen Daten festgelegt werden.

## Ziel

Wenn dasselbe Funktelegramm über Gateway `.121` und Gateway `.132`
ankommt, darf daraus nicht zweimal dasselbe Measurement entstehen.

Wenn dagegen zwei tatsächlich unterschiedliche Messungen desselben
Sensors vorliegen, müssen beide erhalten bleiben.

## Noch technisch zu klären

- Welche Felder des WeatherHub-Protokolls ermöglichen eine zuverlässige
  Identifikation desselben Funktelegramms?
- Gibt es eine Sequenznummer oder einen eindeutigen Paket-Identifier?
- Falls nicht: Welche Kombination aus Payload, Sensor-ID und Zeitstempel
  ist ausreichend?
- Wie lange müssen bereits verarbeitete Pakete für die Deduplizierung
  vorgehalten werden?
- Wie groß darf der Speicherbedarf des Deduplizierungs-Caches auf dem
  Raspberry Pi werden?
- Wie soll sich die Deduplizierung bei Neustart des Prozesses verhalten?

---

# OF-3 – Sensor-Allowlist

## Ursprüngliche offene Frage

Offen war, ob alle Sensorfamilien mit gültigem CRC automatisch
Measurements erzeugen oder ob eine konfigurierbare Sensor-Allowlist
eingeführt werden soll.

## Entscheidung

Es wird **keine konfigurierbare Sensor-ID-Allowlist** eingeführt.

Die produktive Verarbeitung wird stattdessen durch die explizit
definierten unterstützten Sensorfamilien bestimmt.

Damit entsteht keine zusätzliche Konfiguration für einzelne Sensor-IDs.

---

# OF-4 – Unterstützte Sensorfamilien

## Ursprüngliche offene Frage

Offen war insbesondere, wie mit Sensorfamilien umgegangen werden soll,
die zwar dekodierbar sind, aber für die erste produktive Implementierung
nicht benötigt werden.

## Entscheidung

In der ersten produktiven Implementierung werden ausschließlich folgende
Sensorfamilien berücksichtigt:

```text
ID01
ID02
ID03
ID04
ID07
ID0E
ID10
```

Alle anderen Sensorfamilien werden für die produktive
Measurement-Verarbeitung ignoriert.

Insbesondere gilt:

```text
ID08 → nicht produktiv verarbeiten
```

Für ID08 wird in dieser Implementierungsphase weder der Regenzähler noch
die Temperatur als produktives Measurement übernommen.

## Decoder vs. produktive Verarbeitung

Decoder und Adapter sollen möglichst sauber zwischen folgenden Ebenen
unterscheiden:

1. Sensorfamilie/Protokoll erkennen
2. Payload technisch dekodieren
3. Prüfen, ob die Sensorfamilie produktiv unterstützt wird
4. Nur unterstützte Sensorfamilien in die Measurement-Pipeline übernehmen

Dadurch bleibt eine spätere Erweiterung um weitere Sensorfamilien möglich,
ohne die bestehende Architektur unnötig umzubauen.

---

# OF-5 – ID04 Wasserkontakt und ID10 Tür/Fenster

## Ursprüngliche offene Frage

Offen war, ob ID10 (Tür-/Fensterkontakt) und der Wasserkontakt aus ID04
als Measurements, als `unavailable`-Platzhalter oder überhaupt nicht in
den Measurement-Batch aufgenommen werden sollen.

## Entscheidung

ID04-Wasserkontakt und ID10 werden in der ersten Implementierungsphase
**nicht als normale Measurements** in den Measurement-Batch aufgenommen.

Es werden auch keine

```text
validity = "unavailable"
```

Platzhalter erzeugt.

## Zukünftige State/Event-Verarbeitung

Die Informationen sollen jedoch nicht konzeptionell verworfen werden.

Das interne Design soll eine spätere Erweiterung um State/Event-
Verarbeitung ermöglichen.

Ziel ist beispielsweise eine spätere Modellierung von:

```text
ID04 → Wasserkontakt State/Event
ID10 → Tür-/Fenster State/Event
```

ohne die bestehende Measurement-Pipeline grundlegend umbauen zu müssen.

## Aktuelle Measurement-Regel

```text
ID04 Wasserkontakt → kein Measurement
ID10              → kein Measurement
```

Die Informationen dürfen intern trotzdem so verarbeitet bzw. gespeichert
werden, dass eine spätere State/Event-Implementierung möglich ist.

---

# OF-6 – Stale-Logik

## Ursprüngliche offene Frage

WeatherHub-Sensoren senden typischerweise in einem mehrminütigen Intervall.

Offen war, ob die bestehende Stale-Logik des `FreezerReader` übernommen
werden soll und welcher Schwellenwert gelten soll.

## Entscheidung

WeatherHub-Sensoren erhalten eine Stale-Logik.

Der Schwellenwert wird **nicht fest im Code auf 600 Sekunden begrenzt**.

Er soll über die bestehende Konfigurationsmechanik bzw. `.env`
konfigurierbar sein.

Vorgesehene Konfiguration:

```text
WEATHERHUB_STALE_AFTER_SECONDS
```

Der konkrete Defaultwert muss anhand der tatsächlichen
WeatherHub-Sendeintervalle und der Spezifikation festgelegt werden.

Der Wert muss ausdrücklich auch deutlich größer als zehn Minuten gewählt
werden können.

## Anforderungen

- Der Schwellenwert ist konfigurierbar.
- Der Wert darf nicht im Code fest verdrahtet sein.
- Die bestehende Stale-/Validity-Logik des Projekts soll soweit sinnvoll
  wiederverwendet werden.
- Ein länger nicht aktualisierter Sensor darf nicht dauerhaft als
  uneingeschränkt aktuell erscheinen.

## Noch technisch zu klären

- sinnvoller Defaultwert
- genaue Darstellung von `stale`
- ob ein stale Sensor im Batch verbleibt oder entfernt wird
- welche bestehende `Measurement`-/`validity`-Semantik dafür verwendet
  werden soll
- Verhalten nach Neustart, bevor der erste neue Messwert empfangen wurde

---

# OF-7 – Service-Architektur

## Ursprüngliche offene Frage

Soll der WeatherHub-Listener als eigenständiger systemd-Service laufen
oder als Background-Thread innerhalb des bestehenden
`loggerpi.observer.service`?

## Entscheidung

Die WeatherHub-Integration soll **bevorzugt als Background-Thread innerhalb
des bestehenden `loggerpi.observer.service`** umgesetzt werden.

Ein separater systemd-Service soll nur eingesetzt werden, wenn sich bei
der konkreten Implementierung ein wesentlicher technischer Vorteil ergibt.

## Begründung

Die bevorzugte Thread-Variante soll insbesondere:

- RAM-Verbrauch reduzieren
- unnötige zusätzliche Prozesse vermeiden
- unnötige IPC-Kommunikation vermeiden
- die bestehende Runtime-Architektur möglichst wenig verändern
- die gemeinsame State-/Runtime-Integration vereinfachen
- Deployment-Komplexität reduzieren

Gleichzeitig darf die Thread-Integration kein Overengineering erzeugen.

Der WeatherHub-Listener muss sauber in den bestehenden
`LoggerRuntime`-Lifecycle integriert werden.

## Vergleichskriterien

Vor der endgültigen Implementierung sind insbesondere folgende Punkte zu
berücksichtigen:

- RAM-Verbrauch auf dem Raspberry Pi
- CPU-Overhead
- Anzahl zusätzlicher Prozesse
- IPC-Bedarf
- Fehlerisolierung
- Restart-Verhalten
- Logging
- Wartbarkeit
- Lifecycle und Shutdown
- Auswirkungen auf die bestehende LoggerRuntime
- Verhalten bei Netzwerkfehlern
- Verhalten bei einem Fehler im WeatherHub-Listener

## Grundsatz

Wenn die Thread-Integration technisch sauber möglich ist und gegenüber
einem separaten Service keinen wesentlichen betrieblichen Vorteil verliert,
wird die Thread-Variante bevorzugt.

Ein separater Service soll nicht nur aus Gründen einer vermeintlich
„saubereren“ Architektur eingeführt werden.

---

# Implementierungsgrundsätze

## Lokale Funktionalität hat Priorität

Der lokale Empfang und die lokale Verarbeitung der WeatherHub-Daten müssen
unabhängig von externen Diensten funktionieren.

Insbesondere darf ein Ausfall von `www.data199.com` nicht den lokalen
LoggerPi-Betrieb blockieren.

## Keine unnötige Konfiguration

Konfiguration soll nur dort eingeführt werden, wo sie tatsächlich
betriebsrelevant ist.

Insbesondere wird keine Sensor-ID-Allowlist eingeführt.

## Erweiterbarkeit ohne Overengineering

Die erste Implementierung soll die aktuell benötigten
Sensorfamilien und Funktionen sauber unterstützen.

Gleichzeitig sollen erkennbare zukünftige Erweiterungen, insbesondere:

- weitere Sensorfamilien
- State/Event-Verarbeitung
- weitere Gateways
- Cloud-Forwarding

nicht durch unnötig starre Architektur verhindert werden.

Es sollen jedoch keine zukünftigen Funktionen vollständig implementiert
werden, nur weil sie später möglicherweise benötigt werden.

---

# Noch offene technische Detailentscheidungen

Vor Beginn bzw. während der Implementierung müssen insbesondere folgende
Punkte anhand der Spec und der bestehenden Codebasis konkretisiert werden:

1. **Deduplizierung**
   - eindeutige Identifikation desselben Funktelegramms
   - Cache-/TTL-Strategie
   - Speicherbedarf
   - Verhalten nach Neustart

2. **Cloud-Forward**
   - synchron/asynchron
   - Timeout
   - Retry
   - Fehlerbehandlung
   - Logging
   - Konfiguration

3. **Stale**
   - Defaultwert für `WEATHERHUB_STALE_AFTER_SECONDS`
   - genaue Darstellung im Measurement-Modell
   - Verhalten im Batch

4. **Thread-Integration**
   - Start/Stop-Lifecycle
   - Exception-Handling
   - sauberer Shutdown
   - Interaktion mit `LoggerRuntime`

5. **State/Event-Vorbereitung**
   - welche ID04-/ID10-Informationen intern erhalten bleiben müssen
   - ohne diese bereits als Measurement zu modellieren

Diese Punkte sind technische Detailentscheidungen.

Sie dürfen die oben dokumentierten fachlichen Entscheidungen nicht
unbeabsichtigt wieder aufheben.

---

# Implementierungsstatus

Aktuell:

```text
[x] Decoder
[x] Adapter (WeatherHubReader)
[ ] WeatherHub State
[x] WeatherHub Reader/Listener
[ ] Gateway-Deduplizierung (nur wenn .132 auch in Proxymodus)
[ ] Cloud-Forward (optional, WEATHERHUB_CLOUD_FORWARD_ENABLED)
[ ] Stale-Logik (noch offen)
[x] Runtime-Integration
[x] Tests
[x] Deployment (v1.5.0)
```

Dieses Dokument beschreibt die Entscheidungen vor Beginn der eigentlichen
Implementierung.

Nach Abschluss einzelner Implementierungsschritte kann dieser Abschnitt
ergänzt werden, ohne die ursprünglichen Entscheidungen rückwirkend zu
überschreiben.
