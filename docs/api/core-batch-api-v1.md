# LoggerPi → OtterPi

## Core Batch API v1

**Data Model:** v1  
**Core Batch:** v1  
**API:** v1  
**Status:** technische Definition  
**Basis:** `core-batch-v1.md` und `core-batch-v1-json.md`

---

## 1. Zweck

Dieses Dokument definiert die HTTP-Schnittstelle für die Übertragung des
Core Batch vom LoggerPi zum OtterPi.

Der LoggerPi initiiert die Verbindung.

Der OtterPi stellt den HTTP-Endpunkt bereit und nimmt Core Batches entgegen.

Der LoggerPi muss für den OtterPi nicht von außen erreichbar sein.

Insbesondere darf das API-Design keine eingehende Verbindung vom OtterPi zum
LoggerPi voraussetzen.

---

## 2. Kommunikationsmodell

Die Kommunikation ist grundsätzlich:

```text
LoggerPi
    │
    │ HTTP request
    │ Core Batch JSON
    ▼
OtterPi
    │
    │ HTTP response
    ▼
LoggerPi
```

Die HTTP-Response wird über dieselbe vom LoggerPi initiierte Verbindung
zurückgegeben.

Es ist kein separater Rückkanal erforderlich.

### 2.1 Push-Modell

Der LoggerPi überträgt einen Core Batch aktiv an den OtterPi.

Der OtterPi ruft den LoggerPi nicht ab.

Insbesondere ist nicht vorgesehen:

```text
OtterPi → LoggerPi → "gib mir den nächsten Batch"
```

sondern:

```text
LoggerPi → OtterPi → Batch
```

---

# 3. Endpoint

Der Core Batch wird über folgenden Endpoint übertragen:

```text
POST /api/v1/batches
```

Der Endpoint nimmt genau einen Core Batch pro HTTP Request entgegen.

---

# 4. HTTP Request

## 4.1 Methode

```text
POST
```

## 4.2 Content-Type

Der Request verwendet:

```text
Content-Type: application/json
```

Eine andere Payload-Darstellung ist für den Core Batch v1 nicht definiert.

## 4.3 Request Body

Der Request Body ist unmittelbar der in
`core-batch-v1-json.md` definierte Core Batch.

Es wird kein zusätzlicher HTTP-spezifischer Envelope um den Core Batch gelegt.

Damit gilt:

```text
HTTP Request
└── JSON Body
    └── Core Batch
        ├── schema_version
        ├── batch_id
        ├── logger_id
        ├── sequence
        ├── created_at
        └── ...
```

Der bereits definierte Batch Envelope ist Bestandteil des Core Batch und
bleibt erhalten.

---

# 5. HTTP Headers

Für v1 werden folgende Header benötigt:

```text
Content-Type: application/json
```

Weitere für die fachliche Identität des Batches erforderliche Informationen
werden nicht zusätzlich über HTTP Header übertragen.

Insbesondere werden nicht redundant übertragen:

```text
batch_id
logger_id
sequence
schema_version
```

Diese Werte sind Bestandteil des JSON-Bodys.

Authentication bzw. Authorization wird separat spezifiziert.

---

# 6. Erfolgreiche Annahme

Der OtterPi bestätigt die erfolgreiche technische Annahme eines Requests
durch eine HTTP Response.

Für eine erfolgreiche Annahme wird verwendet:

```text
HTTP 202 Accepted
```

`202 Accepted` bedeutet:

> Der Request wurde vom OtterPi akzeptiert und der enthaltene Batch wurde
> zur weiteren Verarbeitung angenommen.

Die Antwort bedeutet nicht, dass sämtliche nachgelagerten fachlichen
Auswertungen bereits abgeschlossen sind.

---

# 7. Erfolgreiche Response

Bei erfolgreicher Annahme enthält die Response ein JSON-Objekt.

Beispiel:

```json
{
  "status": "accepted",
  "batch_id": "01J...",
  "sequence": 1842
}
```

### Felder

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `status` | string | required | Ergebnis der Annahme |
| `batch_id` | string | required | Identität des empfangenen Batches |
| `sequence` | integer | required | Sequence des empfangenen Batches |

Für die erfolgreiche Annahme gilt:

```text
status = accepted
```

`batch_id` und `sequence` werden aus dem empfangenen Batch übernommen.

---

# 8. HTTP Fehler

HTTP-Fehler zeigen an, dass der Request nicht erfolgreich als neuer
Core-Batch angenommen wurde.

Die wichtigsten Kategorien sind:

| Status | Bedeutung |
|---|---|
| `400 Bad Request` | Request syntaktisch oder strukturell ungültig |
| `401 Unauthorized` | Authentication fehlt oder ist ungültig |
| `403 Forbidden` | Request ist authentifiziert, aber nicht zugelassen |
| `404 Not Found` | Endpoint nicht vorhanden |
| `409 Conflict` | Request steht in Konflikt mit dem bekannten Batch-Zustand |
| `413 Payload Too Large` | Request ist zu groß |
| `415 Unsupported Media Type` | falscher Content-Type |
| `422 Unprocessable Content` | JSON ist syntaktisch gültig, entspricht aber nicht dem definierten Contract |
| `429 Too Many Requests` | Request wird wegen Rate Limiting abgewiesen |
| `500 Internal Server Error` | interner Fehler des OtterPi |
| `503 Service Unavailable` | Endpoint momentan nicht verfügbar |

Die konkrete Behandlung dieser Fehler durch Queue und Retry wird separat
definiert.

---

# 9. Fehler-Response

Fehler werden als JSON zurückgegeben, sofern der OtterPi den Request soweit
verarbeiten kann, dass eine strukturierte Fehlerantwort möglich ist.

Grundstruktur:

```json
{
  "status": "error",
  "error": {
    "code": "invalid_payload",
    "message": "Request body does not conform to Core Batch v1."
  }
}
```

### Felder

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `status` | string | required | muss `error` sein |
| `error` | object | required | Fehlerbeschreibung |
| `error.code` | string | required | maschinenlesbarer Fehlercode |
| `error.message` | string | required | menschenlesbare Fehlerbeschreibung |

`error.message` ist nicht Teil der fachlichen Batch-Semantik und darf sich
zwischen Implementierungen ändern.

Der maschinenlesbare `error.code` ist für die technische Fehlerbehandlung
maßgeblich.

---

# 10. Authentication

Authentication ist Bestandteil des API-Designs, wird aber nicht durch die
fachliche Core-Batch-Payload abgebildet.

Die konkrete Authentication-Methode wird separat spezifiziert.

Insbesondere werden keine Authentication-Daten in den Core Batch
aufgenommen.

---

# 11. Batch Identity

Die Identität eines Core Batch wird durch die im Batch Envelope definierten
Felder bestimmt.

Relevant sind insbesondere:

```text
batch_id
logger_id
sequence
```

`batch_id` identifiziert den konkreten Batch.

`logger_id` identifiziert den LoggerPi.

`sequence` identifiziert die Position des Batches innerhalb der persistenten
Batch-Folge eines LoggerPi.

Ein Zustellversuch verändert diese Werte nicht.

---

# 12. Retry-Grundprinzip

Ein Retry eines bereits erzeugten Batches erzeugt keinen neuen Batch.

Beispiel:

```text
Erster Versuch

batch_id = A
sequence = 1842

        ↓ Fehler

Retry

batch_id = A
sequence = 1842
```

Der LoggerPi darf für denselben fachlichen Batch nicht bei jedem
Zustellversuch eine neue `batch_id` oder `sequence` erzeugen.

Die detaillierte Retry-Policy wird separat definiert.

---

# 13. Duplicate Handling

Der OtterPi muss damit rechnen, dass derselbe Batch mehr als einmal
übertragen wird.

Dies kann beispielsweise durch einen Retry nach einer unklaren
Verbindungsunterbrechung entstehen:

```text
LoggerPi
    │
    │ POST batch A
    ▼
OtterPi
    │
    │ Batch verarbeitet
    │
    X Response geht verloren
    │
    ▼
LoggerPi

        ↓ Retry

LoggerPi
    │
    │ POST batch A
    ▼
OtterPi
```

Die API muss daher idempotente Annahme bereits über die Batch-Identität
ermöglichen.

Die vollständige Duplicate-Handling-Semantik wird separat spezifiziert.

---

# 14. HTTP Response und Netzwerktopologie

Eine erfolgreiche HTTP Response stellt keinen separaten Rückkanal zum
LoggerPi dar.

Die Kommunikation bleibt:

```text
LoggerPi ───── HTTP request ─────> OtterPi
LoggerPi <──── HTTP response ───── OtterPi
```

Die Response erfolgt ausschließlich innerhalb der vom LoggerPi aufgebauten
HTTP-Verbindung.

Der OtterPi benötigt daher keine eingehende Netzwerkverbindung zum LoggerPi.

Insbesondere darf das API-Design nicht voraussetzen:

```text
OtterPi ─────> LoggerPi
```

Dies ist aufgrund der Netzwerktopologie des LoggerPi nicht zuverlässig
möglich.

---

# 15. Kein Mesh-Agent als API-Abhängigkeit

Der Core Batch API Contract verwendet keine Mesh-Agent-Verbindung als
Transport- oder Rückkanal.

`meshagent` ist insbesondere nicht erforderlich, damit:

- ein Core Batch übertragen wird
- eine HTTP Response zurückgegeben wird
- eine erfolgreiche technische Annahme erfolgt
- Retry technisch möglich ist

Der reguläre Datenweg bleibt:

```text
LoggerPi → OtterPi
```

---

# 16. Abgrenzung zu Delivery

Dieses Dokument definiert den HTTP API Contract.

Nicht abschließend definiert werden hier:

- lokale Queue-Implementierung
- Retry-Backoff
- Retry-Grenzen
- Verhalten bei dauerhaftem OtterPi-Ausfall
- Duplicate-Handling-Algorithmus
- Persistenz vor bzw. nach HTTP-Annahme
- Persistenz-/Annahme-Semantik
- Event-Protokoll
- Metadata-Change-Protokoll

Diese Punkte werden in den entsprechenden Delivery-/Protokollspezifikationen
definiert.

---

# 17. Minimaler Request

Ein Request folgt grundsätzlich diesem Muster:

```http
POST /api/v1/batches HTTP/1.1
Content-Type: application/json

{
  "schema_version": "1.0",
  "batch_id": "01J...",
  "logger_id": "loggerpi-01",
  "sequence": 1842,
  "created_at": "2026-08-15T10:45:00+02:00",
  "...": "Core Batch v1"
}
```

Der tatsächliche Request Body muss dem vollständigen Core-Batch-v1-JSON-
Contract entsprechen.

---

# 18. Status

Mit diesem Dokument ist der grundlegende HTTP Contract für die Übertragung
des Core Batch v1 definiert.

Festgelegt sind:

- Push-Richtung LoggerPi → OtterPi
- `POST /api/v1/batches`
- JSON als Request Body
- Core Batch als unmittelbarer Request Body
- bestehender Batch Envelope bleibt Bestandteil des Batches
- HTTP Response über die vom LoggerPi initiierte Verbindung
- `202 Accepted` für erfolgreiche technische Annahme
- grundlegende Fehlerstatus
- strukturierte Fehlerantwort
- Batch Identity über `batch_id`, `logger_id` und `sequence`
- kein separater Rückkanal zum LoggerPi
- keine Mesh-Agent-Abhängigkeit

Noch separat zu definieren sind:

  * Authentication
