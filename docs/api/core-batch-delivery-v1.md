# LoggerPi → OtterPi

## Core Batch Delivery v1

**Data Model:** v1  
**Core Batch:** v1  
**API:** v1  
**Delivery:** v1  
**Status:** technische Definition  
**Basis:** `core-batch-v1.md`, `core-batch-v1-json.md`,
`core-batch-api-v1.md`

---

## 1. Zweck

Dieses Dokument definiert die Zustellsemantik für Core Batches zwischen
LoggerPi und OtterPi.

Insbesondere werden festgelegt:

- Bedeutung der erfolgreichen HTTP-Annahme
- ACK-/Acceptance-Semantik
- Verhalten bei Verbindungsfehlern
- Retry-Grundprinzip
- Retry-fähige und nicht retry-fähige Fehler
- Duplicate Handling
- Beziehung zwischen `batch_id`, `logger_id` und `sequence`
- Voraussetzungen für das Entfernen eines Batches aus der lokalen Queue

Die fachliche Struktur des Core Batch wird nicht erneut definiert.

Der HTTP Endpoint wird in `core-batch-api-v1.md` definiert.

---

# 2. Kommunikationsmodell

Die Zustellung erfolgt ausschließlich als vom LoggerPi initiierter Push:

```text
LoggerPi
    │
    │ HTTP POST
    │ Core Batch
    ▼
OtterPi
    │
    │ HTTP Response
    ▼
LoggerPi
```

Die HTTP Response wird über dieselbe Verbindung zurückgegeben.

Ein separater Rückkanal vom OtterPi zum LoggerPi ist nicht erforderlich
und nicht vorgesehen.

---

# 3. Grundprinzip der Zustellung

Ein Core Batch wird auf dem LoggerPi zunächst lokal als noch nicht
bestätigt betrachtet.

Grundsätzlich gilt:

```text
Batch erzeugt
    ↓
lokal persistent gespeichert
    ↓
Zustellversuch
    ↓
OtterPi
    ↓
erfolgreiche Annahme
    ↓
HTTP 202
    ↓
LoggerPi darf Batch als bestätigt markieren
    ↓
Batch kann aus der lokalen Zustell-Queue entfernt werden
```

Ein Batch darf **nicht** allein deshalb aus der lokalen Queue entfernt
werden, weil der HTTP Request erfolgreich aufgebaut oder vollständig
gesendet wurde.

---

# 4. ACK-/Acceptance-Semantik

## 4.1 HTTP 202 als technische Annahmebestätigung

Der OtterPi antwortet mit:

```text
HTTP 202 Accepted
```

wenn der Batch erfolgreich angenommen wurde.

Für die Delivery-Semantik bedeutet `202`:

> Der OtterPi hat den Batch dauerhaft angenommen und so persistiert, dass
> ein Verlust des Batches durch einen unmittelbaren Neustart des OtterPi
> nicht zu erwarten ist.

Damit ist die Zustellung für den LoggerPi bestätigt.

---

## 4.2 `202` bedeutet nicht vollständige Verarbeitung

`202 Accepted` bedeutet ausdrücklich nicht:

```text
Batch vollständig ausgewertet
Batch vollständig verarbeitet
Health berechnet
Dashboard aktualisiert
Eventverarbeitung abgeschlossen
```

Es bedeutet nur:

```text
Batch dauerhaft angenommen
```

Die nachgelagerte Verarbeitung kann asynchron erfolgen.

---

## 4.3 Voraussetzung für `202`

Der OtterPi darf `202 Accepted` erst zurückgeben, wenn der Batch die für
die Delivery-Annahme erforderliche Persistenz erreicht hat.

Insbesondere darf folgende Reihenfolge nicht verwendet werden:

```text
Request empfangen
    ↓
202 senden
    ↓
Batch erst danach speichern
```

wenn ein OtterPi-Neustart zwischen diesen Schritten zu einem Verlust des
Batches führen könnte.

Stattdessen gilt:

```text
Request empfangen
    ↓
Batch validieren
    ↓
Batch dauerhaft annehmen / persistieren
    ↓
202 senden
```

Die konkrete interne Persistenztechnologie ist nicht Bestandteil dieses
Dokuments.

---

# 5. Verhalten des LoggerPi nach erfolgreicher Annahme

Nach Erhalt einer gültigen erfolgreichen Response:

```text
HTTP 202 Accepted
```

darf der LoggerPi den entsprechenden Batch als erfolgreich zugestellt
markieren.

Der Batch muss danach nicht erneut übertragen werden.

Beispiel:

```text
batch_id = A
sequence = 1842

POST
    ↓
202 Accepted
    ↓
Batch A bestätigt
    ↓
Batch A kann aus der Pending-Queue entfernt werden
```

---

# 6. Keine Response / unklare Zustellung

Ein besonders wichtiger Fall ist eine unterbrochene Verbindung nach oder
während der Übertragung.

Beispiel:

```text
LoggerPi
    │
    │ POST batch A
    ▼
OtterPi
    │
    │ Batch möglicherweise bereits gespeichert
    │
    X Verbindung unterbrochen
    │
    ▼
LoggerPi
```

Der LoggerPi kann in diesem Fall nicht sicher wissen, ob der OtterPi den
Batch bereits angenommen hat.

Der Batch bleibt deshalb lokal als nicht bestätigt erhalten.

Der LoggerPi darf ihn erneut übertragen.

```text
Batch A
    ↓
Retry
    ↓
OtterPi erkennt Duplicate
    ↓
Batch A ist bereits angenommen
    ↓
202 Accepted
    ↓
LoggerPi bestätigt Batch A
```

Damit wird verhindert, dass ein verlorener HTTP Response zu einem
dauerhaft hängenbleibenden Batch führt.

---

# 7. Retry-Grundprinzip

Ein Retry bezieht sich immer auf denselben bereits erzeugten Batch.

Dabei bleiben unverändert:

```text
batch_id
logger_id
sequence
created_at
```

Insbesondere darf ein Retry keine neue `batch_id` und keine neue
`sequence` erzeugen.

Beispiel:

```text
Erster Versuch:

batch_id = 01JABC...
logger_id = loggerpi-01
sequence = 1842

        ↓ Timeout

Retry:

batch_id = 01JABC...
logger_id = loggerpi-01
sequence = 1842
```

---

# 8. Retry bei Transportfehlern

Wenn keine gültige erfolgreiche HTTP Response erhalten wurde, bleibt der
Batch pending.

Typische Fälle:

- DNS-/Verbindungsfehler
- Connection Refused
- Connection Timeout
- Read Timeout
- Connection Reset
- Netzwerkunterbrechung
- OtterPi nicht erreichbar

Diese Fälle sind retry-fähig.

Der LoggerPi darf den Batch später erneut übertragen.

---

# 9. Retry bei HTTP-Fehlern

Nicht jeder HTTP-Fehler ist retry-fähig.

### Retry-fähig

Grundsätzlich retry-fähig sind:

```text
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

Bei diesen Fehlern darf der LoggerPi den Batch später erneut übertragen.

---

## 9.1 Nicht retry-fähig

Folgende Fehler sind grundsätzlich nicht durch einen unveränderten
erneuten Zustellversuch lösbar:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
413 Payload Too Large
415 Unsupported Media Type
422 Unprocessable Content
```

Der Batch darf in diesem Fall nicht einfach in einer Endlosschleife
erneut übertragen werden.

Die konkrete lokale Fehlerbehandlung wird separat durch das
LoggerPi-Delivery-Verhalten festgelegt.

---

# 10. HTTP 409 Conflict

`409 Conflict` wird für einen erkannten Konflikt der Batch-Identität
verwendet.

Ein solcher Konflikt ist nicht als gewöhnlicher transienter Fehler
zu behandeln.

Beispiele:

```text
gleiche batch_id
aber unterschiedlicher Batch-Inhalt
```

oder:

```text
gleicher logger_id
gleiche sequence
aber unterschiedliche batch_id
```

Diese Fälle weisen auf einen Inkonsistenzfehler hin.

Ein unveränderter Retry ist daher nicht sinnvoll.

---

# 11. Duplicate Handling

Der OtterPi muss denselben Batch mehrfach empfangen können.

Ein Duplicate kann insbesondere durch einen verlorenen HTTP Response
entstehen.

Der OtterPi muss deshalb die Annahme eines bereits bekannten Batches
idempotent behandeln.

---

# 12. Identität eines Batches

Für die Delivery-Semantik werden folgende Felder betrachtet:

```text
logger_id
batch_id
sequence
```

Ihre Rollen sind:

### `logger_id`

Identifiziert den LoggerPi, von dem der Batch stammt.

### `batch_id`

Identifiziert den konkreten Batch.

### `sequence`

Identifiziert die Position des Batches in der persistenten Batch-Folge
des jeweiligen LoggerPi.

---

# 13. Exakter Duplicate

Wenn ein bereits angenommener Batch erneut übertragen wird und seine
Identität sowie sein Inhalt dem bereits gespeicherten Batch entsprechen,
wird er als Duplicate erkannt.

Beispiel:

```text
bereits gespeichert:

logger_id = loggerpi-01
batch_id  = A
sequence  = 1842

erneut empfangen:

logger_id = loggerpi-01
batch_id  = A
sequence  = 1842
```

Wenn der Inhalt identisch ist:

```text
→ kein zweiter fachlicher Batch
→ keine doppelte Verarbeitung
→ erfolgreiche Annahme
→ HTTP 202
```

Der OtterPi darf den bereits angenommenen Batch dabei erneut bestätigen.

---

# 14. Duplicate darf keinen zweiten fachlichen Batch erzeugen

Ein Duplicate darf nicht zu:

```text
Batch A
Batch A erneut
```

führen.

Stattdessen bleibt es bei:

```text
Batch A
```

Die erneute Zustellung ist ausschließlich ein technischer
Zustellversuch desselben Batches.

---

# 15. Gleiche `batch_id`, unterschiedlicher Inhalt

Eine bereits bekannte `batch_id` darf nicht mit einem anderen Batch-Inhalt
wiederverwendet werden.

Beispiel:

```text
bereits gespeichert:

batch_id = A
sequence = 1842
```

erneut empfangen:

```text
batch_id = A
sequence = 1842
```

aber mit verändertem Payload.

Das ist kein Duplicate.

Es ist ein Identitätskonflikt.

Der OtterPi antwortet:

```text
HTTP 409 Conflict
```

Der LoggerPi darf diesen Batch nicht einfach unverändert weiter
retryen.

---

# 16. Gleiche Sequence, unterschiedliche `batch_id`

Innerhalb eines LoggerPi muss eine `sequence` eindeutig sein.

Daher ist auch folgender Fall ein Konflikt:

```text
logger_id = loggerpi-01
sequence = 1842
batch_id = A
```

und später:

```text
logger_id = loggerpi-01
sequence = 1842
batch_id = B
```

Dies ist kein gültiger neuer Batch.

Der OtterPi antwortet:

```text
HTTP 409 Conflict
```

---

# 17. Reihenfolge der Sequences

Die `sequence` ist persistent und monoton fortlaufend.

Der OtterPi muss jedoch nicht voraussetzen, dass Batches immer in
Netzwerk-Reihenfolge eintreffen.

Beispiel:

```text
sequence 1842
sequence 1843
sequence 1844
```

kann beim OtterPi auch als:

```text
1842
1844
1843
```

eintreffen.

Ein später eintreffender Batch mit einer höheren oder niedrigeren
Sequence ist deshalb nicht automatisch ein Fehler.

Die `sequence` dient insbesondere der Identität, Erkennung von
Lücken/Duplikaten und späterer Zustandsbewertung.

---

# 18. Keine künstliche Lücken-Rejection

Der OtterPi darf einen Batch nicht allein deshalb ablehnen, weil die
vorherige Sequence noch nicht eingetroffen ist.

Beispiel:

```text
1842 fehlt noch
1843 kommt an
```

`1843` darf deshalb nicht automatisch mit:

```text
409 Conflict
```

abgelehnt werden.

Der OtterPi kann die Lücke separat erkennen und bewerten.

---

# 19. Retry und Duplicate zusammen

Die Kombination aus Retry und idempotenter Duplicate-Behandlung ist
notwendig, weil eine HTTP-Zustellung nicht immer eindeutig abgeschlossen
werden kann.

Beispiel:

```text
1. LoggerPi erzeugt Batch A
2. Batch A wird lokal persistent gespeichert
3. LoggerPi sendet Batch A
4. OtterPi persistiert Batch A
5. HTTP Response geht verloren
6. LoggerPi erkennt keinen Erfolg
7. LoggerPi sendet Batch A erneut
8. OtterPi erkennt Duplicate
9. OtterPi antwortet mit 202
10. LoggerPi markiert Batch A als bestätigt
```

Damit bleibt die Zustellung robust gegenüber verlorenen Responses.

---

# 20. Zustandsmodell des LoggerPi

Für die Delivery-Semantik reichen fachlich mindestens diese Zustände:

```text
pending
    ↓
sending
    ↓
accepted
```

Bei einem transienten Fehler:

```text
pending
    ↓
sending
    ↓
retry_wait
    ↓
sending
```

Bei einer erfolgreichen Annahme:

```text
sending
    ↓
accepted
    ↓
Entfernung aus Pending-Queue
```

Bei einem permanenten Fehler:

```text
sending
    ↓
rejected
```

Die konkrete interne Queue-Implementierung ist nicht Bestandteil dieses
Dokuments.

---

# 21. Batch-Löschung auf dem LoggerPi

Ein Batch darf erst dann endgültig aus der lokalen Pending-Queue entfernt
werden, wenn eine erfolgreiche Annahme bestätigt wurde.

Insbesondere nicht ausreichend sind:

```text
HTTP Request erfolgreich gesendet
```

oder:

```text
TCP-Verbindung aufgebaut
```

oder:

```text
HTTP Response unbekannt
```

Maßgeblich ist:

```text
HTTP 202 Accepted
```

für diesen Batch.

---

# 22. Verhalten bei OtterPi-Ausfall

Wenn der OtterPi nicht erreichbar ist, bleiben noch nicht bestätigte
Batches lokal persistent erhalten.

Der LoggerPi versucht die Zustellung später erneut.

Beispiel:

```text
LoggerPi
    │
    │ Batch A
    X
    │
    │ OtterPi nicht erreichbar
    ▼
lokale Queue

        später

LoggerPi
    │
    │ Batch A
    ▼
OtterPi
```

Die lokale Queue dient damit als Store-and-Forward-Mechanismus.

Die konkrete Queue-Größe, Aufbewahrungsdauer und Löschstrategie werden
separat definiert.

---

# 23. Keine Rückverbindung

Alle in diesem Dokument beschriebenen Bestätigungen und Fehlerantworten
erfolgen innerhalb der vom LoggerPi initiierten HTTP-Verbindung.

Es gibt keinen Mechanismus:

```text
OtterPi → LoggerPi
```

für nachträgliche ACKs oder Retry-Anweisungen.

Ein verlorener Response wird ausschließlich dadurch behandelt, dass der
LoggerPi den ursprünglichen Batch erneut sendet.

---

# 24. Authentication

Authentication ist für die Zustellentscheidung relevant, wird aber in
einem separaten Dokument definiert.

Authentication-Fehler gelten in diesem Delivery-Modell als nicht
retry-fähig, solange sich die Authentifizierungsbedingungen nicht ändern.

Der Batch selbst enthält keine Authentication-Daten.

---

# 25. Zusammenfassung der Zustellentscheidungen

| Situation | OtterPi | LoggerPi |
|---|---|---|
| Batch neu und gültig | `202 Accepted` | Batch bestätigt |
| Batch bereits identisch angenommen | `202 Accepted` | Batch bestätigt |
| gleiche `batch_id`, anderer Inhalt | `409 Conflict` | nicht unverändert retryen |
| gleiche `logger_id` + `sequence`, andere `batch_id` | `409 Conflict` | nicht unverändert retryen |
| `400` | Ablehnung | nicht automatisch retryen |
| `401` | Ablehnung | nicht automatisch retryen |
| `403` | Ablehnung | nicht automatisch retryen |
| `413` | Ablehnung | nicht automatisch retryen |
| `415` | Ablehnung | nicht automatisch retryen |
| `422` | Ablehnung | nicht automatisch retryen |
| `429` | temporäre Ablehnung | retry |
| `500` | temporärer Serverfehler | retry |
| `502` | temporärer Gatewayfehler | retry |
| `503` | temporäre Nichtverfügbarkeit | retry |
| `504` | temporärer Timeout | retry |
| Connection Timeout | keine sichere Annahme | retry |
| Response verloren | Annahme unbekannt | retry |
| HTTP 202 | dauerhaft angenommen | Queue-Eintrag kann entfernt werden |

---

# 26. Status

Mit diesem Dokument sind die grundlegenden Delivery-Regeln für Core Batch
v1 definiert.

Festgelegt sind:

- `202 Accepted` als erfolgreiche technische Annahme
- dauerhafte Annahme vor `202`
- Batch bleibt bei unklarer Zustellung lokal erhalten
- Retry mit unveränderter Batch-Identität
- idempotente Duplicate-Behandlung
- exakter Duplicate wird erneut mit `202` bestätigt
- Identitätskonflikte werden mit `409 Conflict` abgewiesen
- Sequences müssen nicht in Netzwerk-Reihenfolge eintreffen
- fehlende vorherige Sequences sind kein automatischer Fehler
- nur bestätigte Batches dürfen aus der Pending-Queue entfernt werden
- Transport-/Serverfehler können Retry auslösen
- permanente Validierungs-/Authentifizierungsfehler lösen keinen
  automatischen Endlos-Retry aus
- kein separater Rückkanal zum LoggerPi

Noch separat zu definieren sind:

- konkrete Retry-Intervalle und Backoff
- maximale Retry-Anzahl
- Queue-Größe
- Queue-Aufbewahrungsdauer
- Verhalten bei dauerhaft nicht zustellbaren Batches
- Authentication
- konkrete OtterPi-Persistenz
