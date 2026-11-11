# LoggerPi → OtterPi Deployment

## Zweck

Dieses Dokument beschreibt den reproduzierbaren Deploymentweg des
LoggerPi-OtterPi-Projekts auf LoggerPi und OtterPi.

Die Anwendung wird aus dem GitHub-Repository `main` deployt.

Das Deployment der Anwendung ist von der Host-Infrastruktur
(nginx, TLS, DNS, Firewall und Routing) getrennt.

---

## 1. Voraussetzungen

### Entwicklungsrechner

Auf dem Entwicklungsrechner müssen vor einem Release mindestens
folgende Prüfungen erfolgreich sein:

```powershell
ruff check .
ruff format --check .
pytest
git diff --check
git status
```

Zusätzlich muss das gewünschte Commit nach GitHub gepusht worden sein.

---

## 2. Repository

Repository:

```text
https://github.com/Lorc77/LoggerPi-OtterPi.git
```

Produktiver Branch:

```text
main
```

Der Deployment-Wrapper verwendet immer den tatsächlich ausgecheckten
Commit und schreibt diesen nach erfolgreichem Deployment nach:

```text
/opt/loggerpi-otterpi/DEPLOYED_COMMIT
```

Zusätzlich werden folgende Dateien geschrieben:

```text
/opt/loggerpi-otterpi/DEPLOYED_VERSION   menschenlesbare Version (z. B. v1.0.0)
/opt/loggerpi-otterpi/VERSION            Version aus pyproject.toml (z. B. 1.0.0)
```

Die `DEPLOYED_*`-Dateien werden **nur bei erfolgreichem Update** geschrieben
(Fail-safe-Design). Schlägt der Service-Neustart fehl, bleibt die bisherige
Deployment-Version bestehen.

---

## 3. LoggerPi Deployment

Auf dem LoggerPi:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update loggerpi
```

Der Wrapper:

1. klont den aktuellen `main`-Stand temporär,
2. bestimmt den Commit,
3. setzt `chmod +x` für `install.sh`-Dateien,
4. führt `deploy/loggerpi/install.sh` aus,
5. installiert bzw. aktualisiert die Anwendung unter
   `/opt/loggerpi-otterpi`,
6. installiert die systemd-Service-Datei,
7. aktiviert `loggerpi.observer.service`,
8. startet den Service neu,
9. prüft dessen Zustand,
10. schreibt den deployten Commit und die Version nach
    `/opt/loggerpi-otterpi/DEPLOYED_COMMIT` und `/opt/loggerpi-otterpi/DEPLOYED_VERSION`.

Service:

```text
loggerpi.observer.service
```

Die Service-Datei `loggerpi.observer.service` enthält seit v1.3.x:

    After=network-online.target dhcpcd.service

Damit startet der Service erst, nachdem `dhcpcd` die Netzwerk-
Konfiguration (IP + Route) abgeschlossen hat – verhindert den
`Network is unreachable`-Fehler beim ersten Zyklus nach dem Boot LEIDER NOCH NICHT.

Konfiguration:

```text
/etc/loggerpi-otterpi/loggerpi.env
```

### Neue Umgebungsvariablen (seit v1.3.0 / v1.4.0)

| Variable | Bedeutung | Default |
|----------|-----------|---------|
| `LOGGERPI_FREEZER_ENABLED` | Freezer-Reader aktivieren | `1` |
| `LOGGERPI_THINGSPEAK_ENABLED` | ThingSpeak-Injektion aktivieren | `0` |
| `LOGGERPI_THINGSPEAK_CHANNEL_ID` | ThingSpeak Channel-ID | – |
| `LOGGERPI_THINGSPEAK_API_KEY` | ThingSpeak Write API Key | – |
| `LOGGERPI_MEMMERT_ENABLED` | MEMMERT-Reader aktivieren | `0` |
| `MEMMERT_IPP300_LINKS_PORT` | Seriell-Pfad MEMMERT links | – |
| `MEMMERT_IPP300_LINKS_ADDRESS` | MEMMERT-Adresse links | – |
| `MEMMERT_IPP300_RECHTS_PORT` | Seriell-Pfad MEMMERT rechts | – |
| `MEMMERT_IPP300_RECHTS_ADDRESS` | MEMMERT-Adresse rechts | – |

### Neue Umgebungsvariablen (seit v1.10.0)

| Variable | Bedeutung | Default |
|----------|-----------|---------|
| `OTTERPI_ALERT_DB` | SQLite-Pfad für Alerts | `/var/lib/loggerpi-otterpi/alerts.sqlite3` |
| `OTTERPI_ALERT_INTERVAL_SECONDS` | Prüfintervall der Alert-Engine | `300` |
| `SMTP_PASSWORD` | SMTP-Passwort (nur Secret) | – |

Installationsverzeichnis:

```text
/opt/loggerpi-otterpi
```

Persistenter Zustand:

```text
/var/lib/loggerpi-otterpi
```

### Flache Deploy-Struktur

Die Installation kopiert die Anwendungsdateien **flach** nach
`/opt/loggerpi-otterpi/`:

```text
/opt/loggerpi-otterpi/
├── atmoweb.py
├── atmoweb_config.py
├── batch_factory.py
├── batch_queue.py
├── composer.py
├── dashboard.py (nur OtterPi)
├── dashboard_config.py (nur OtterPi)
├── dashboard_constants.py (nur OtterPi)
├── dashboard_data.py (nur OtterPi)
├── dashboard_charts.py (nur OtterPi)
├── admin.py (nur OtterPi)
├── config_store.py (nur OtterPi)
├── notifier.py (nur OtterPi)
├── alert_store.py (nur OtterPi)
├── alert_engine.py (nur OtterPi)
├── heartbeat.py (nur OtterPi)
├── sensor_schemas.py (nur OtterPi)
├── archive_batches.py (nur OtterPi)
├── delivery.py
├── freezer.py
├── freezer_config.py
├── loggerpi_observer.py
├── loggerpi_runner.py
├── memmert.py
├── memmert_config.py
├── otter2.png (nur OtterPi)
├── otterpi.py (nur OtterPi)
├── otterpi_observer.py (nur OtterPi)
├── otterpi_store.py (nur OtterPi)
├── runtime.py
├── system_info.py
├── thingspeak_delivery.py
├── thingspeak_config.py
├── weatherhub.py
├── weatherhub_gateway_decoder.py
├── weatherhub_gateway_listener.py
└── model/
    ├── batch.py
    └── measurement.py
```

Da `model/` ein Unterverzeichnis ist und kein Python-Package-Setup
(`pip install -e .`) verwendet wird, muss `PYTHONPATH` explizit gesetzt
werden:

```bash
PYTHONPATH=/opt/loggerpi-otterpi:/opt/loggerpi-otterpi/model
```

Dies wird in den Service-Dateien und den `.env`-Dateien konfiguriert.

---

## 4. OtterPi Deployment

Auf dem OtterPi:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update otterpi
```

Der Wrapper:

1. klont den aktuellen `main`-Stand temporär,
2. bestimmt den Commit,
3. setzt `chmod +x` für `install.sh`-Dateien,
4. führt `deploy/otterpi/install.sh` aus,
5. installiert die OtterPi-Anwendung,
6. installiert bzw. aktualisiert `otterpi.observer.service`,
7. aktiviert den Service,
8. startet ihn neu,
9. prüft dessen Zustand,
10. schreibt den deployten Commit und die Version nach
    `/opt/loggerpi-otterpi/DEPLOYED_COMMIT` und `/opt/loggerpi-otterpi/DEPLOYED_VERSION`.

Service:

```text
otterpi.observer.service
```

Konfiguration:

```text
/etc/loggerpi-otterpi/otterpi.env
```

Installationsverzeichnis:

```text
/opt/loggerpi-otterpi
```

Persistenz:

```text
/var/lib/loggerpi-otterpi
```

SQLite:

```text
/var/lib/loggerpi-otterpi/batches.sqlite3
```

Config:

```text
/var/lib/loggerpi-otterpi/config
```

Die Config wird über `OTTERPI_CONFIG_DIR` gesetzt (Default:
`/var/lib/loggerpi-otterpi/config`). Sie enthält `rooms.json`,
`alarm_limits.json`, `mail.json`, `notifications.json`.

Die Datei `dashboard_config.py` (Raum- und Sensor-Zuordnung) wird
automatisch mit deployt und liegt danach unter:

```text
/opt/loggerpi-otterpi/dashboard_config.py
```

### Sensor-Umzüge / Dashboard-Konfiguration ändern

Wenn Sensoren umziehen oder neue Geräte hinzukommen:

**Variante 1: Deployment (empfohlen)**

1. `dashboard_config.py` im Repository anpassen
2. Committen und pushen
3. Auf dem OtterPi:
   ```bash
   sudo /usr/local/sbin/loggerpi-otterpi-update otterpi
   ```

**Variante 2: Direkte Änderung auf dem OtterPi (ohne Deployment)**

1. Datei direkt bearbeiten:
   ```bash
   sudo nano /opt/loggerpi-otterpi/dashboard_config.py
   ```
2. Service neu starten:
   ```bash
   sudo systemctl restart otterpi.observer.service
   ```

**Wichtig:** Bei Variante 2 ist die Änderung nicht im Git-Repository
dokumentiert. Sie geht beim nächsten Deployment verloren.

### Batch-Archivierung

Der OtterPi archiviert monatlich Batches älter als 12 Monate.

**Automatisch:**

```text
archive-batches.timer (1. des Monats, 03:00 Uhr)
```

**Manuell:**

```bash
# Test-Export (löscht NICHT die DB)
sudo -u makki python3 /opt/loggerpi-otterpi/archive_batches.py \
    --output /tmp/loggerpi-otterpi_batches_TEST.json.gz \
    --force \
    --no-delete

# Normaler Lauf
sudo systemctl start archive-batches.service

# Status prüfen
systemctl status archive-batches.timer --no-pager
```

**Archiv-Dateien:**

```text
/var/lib/loggerpi-otterpi/archive/loggerpi-otterpi_batches_YYYY-MM.json.gz
```

**Retention:** 12 Monate in der Live-Datenbank. Ältere Batches werden
nach erfolgreichem Export gelöscht.

### Alert-Engine

Die Alert-Engine läuft als Thread im `otterpi.observer.service`. Sie prüft
nach jedem Batch (und alle 300 s) die Regeln aus `alarm_limits.json`
(`system` + `sensors` + `states`). Alerts werden in `alerts.sqlite3`
gespeichert und über die konfigurierten Notifier versendet.

Konfiguration:
- `alarm_limits.json` (system + sensors + states)
- `mail.json` (SMTP, Empfänger, Routing, Dedup, Quiet Hours)
- `notifications.json` (ntfy, webhook)
- `SMTP_PASSWORD` in `otterpi.env`

Die `system`-Sektion steuert die LoggerPi-Offline-Erkennung:

```json
{
  "system": {
    "loggerpi_offline_warning_seconds": 1800,
    "loggerpi_offline_critical_seconds": 3600,
    "loggerpi_offline_warning_alert_enabled": false
  }
}
```

Bei Offline (Warnschwelle erreicht) werden Sensor-/State-Checks ausgesetzt.

### Phase C – Komfort (v1.11.0)

- **Admin-UI:** Formular-UI in allen Tabs (Rooms, Alarm Limits, Mail, Notifications), JSON-Editor als „Advanced"-Toggle.
- **Rate-of-Change:** `rate_of_change_max_per_hour` in der Alert-Engine.
- **Routing:** `EmailNotifier` nutzt `routing[severity]`.
- **`contact_open`:** In der Alert-Engine (für zukünftige `weatherhub_id10`-Sensoren).
- **Door-Open-Dauer:** geparkt (HPP260 unterstützt `door_open` nicht).
- **Service-Restart:** nicht nötig (JSON-Configs automatisch gelesen).

### Phase C – Offline-Erkennung (v1.11.11)

- **`received_at` in der Batch-Tabelle:** OtterPi-seitiger Empfangszeitpunkt
  wird persistiert (`BatchStore.latest_received_at()`). Fallback auf
  `created_at` für bestehende Zeilen.
- **`heartbeat.py`:** Gemeinsame Offline-Status-Logik für Admin und Dashboard.
- **`alarm_limits.json` → `system`-Sektion:** Konfigurierbare Schwellenwerte
  (`loggerpi_offline_warning_seconds`, `loggerpi_offline_critical_seconds`)
  und optionale Warnstufe (`loggerpi_offline_warning_alert_enabled`).
- **Alert-Engine:** Heartbeat-Prüfung vor den Sensor-/State-Checks. Bei
  Offline werden Sensor-/State-Checks ausgesetzt (Suppression).
- **Admin:** Statusleuchte im Header, System-Karte im Alarm Limits-Tab.
- **Dashboard:** Statusleuchte im Header, „Last measurement" statt „Last update".
- **`deploy/otterpi/install.sh`:** `heartbeat.py` in der Dateiliste.

**Konfiguration:** Die Offline-Schwellenwerte liegen in `alarm_limits.json`
unter `system`. Die Admin-UI bietet dafür eine System-Karte im Alarm
Limits-Tab (Schwellenwerte in Minuten, Checkbox für Warn-Alert).

### Phase C – Acknowledge + Resolve (v1.11.12)

- **Acknowledge-Verhalten:** Acknowledged Alerts werden nicht erneut gesendet,
  solange der Zustand kritisch bleibt. Reset bei Normalisierung.
- **Alert-Resolve:** Neue Spalte `resolved_at` in `alerts.sqlite3`. Alle
  offenen Alerts mit demselben `dedup_key` werden resolved, wenn der Zustand
  normal wird.
- **Bugfix:** Reset/Resolve nur bei tatsächlich normalem Wert (nicht schon
  bei `validity == "valid"`).
- **Admin:** Alerts-Tab mit Status-Chip („Active" / „Resolved"), Filter
  „Only active".
- **`otterpi.py`:** Query-Parameter `only_active` für `/api/admin/alerts`.

### Phase C – Message-Templates (v1.11.13)

- **`messages.json`:** Neue Config-Datei mit globalen Regel-Texten. Defaults
  werden verwendet, wenn die Datei fehlt.
- **`MEASUREMENT_DISPLAY_NAMES`:** Festes Mapping von Measurement-Key zu
  Anzeigename.
- **Alert-Engine:** Message und Subject mit Raum, Gerät, Measurement-Name
  und Regel-Text.
- **`Alert`-Dataclass:** Neues Feld `subject`. `EmailNotifier` und
  `NtfyNotifier` nutzen es.
- **Admin:** Neuer Messages-Tab mit Formular-UI.
- **`otterpi.py`:** `GET /api/admin/messages`, `PUT /api/admin/messages`.

### Phase C – Resolve-Button + UI-Polish (v1.11.14)

- **Resolve-Button:** Manuelles Resolven eines Alerts im Admin-Alerts-Tab.
- **Alert-Tab als Default:** Der Alerts-Tab ist jetzt der erste Tab.
- **Toast-Notification:** Alle Save-/Delete-/Acknowledge-/Resolve-Aktionen
  zeigen eine kurze Toast-Benachrichtigung.
- **Bugfixes:** Stale-/Invalid-Alerts werden resolved, wenn der Sensor wieder
  `valid` ist. `is_acknowledged()` prüft nur aktive Alerts.

### Phase C – Severity-Auswahl + Rate-of-Change (v1.11.15)

- **Severity-Auswahl pro Kanal:** `notifications.json` → `severities` pro
  Channel. Admin-UI: Checkboxen im Notifications-Tab.
- **Rate-of-Change im Admin:** Spalte „Rate/h" im „Edit Limits"-Formular.
- **Message-Text bei stale/invalid:** Measurement-Key in Klammern.
- **Resolve-Zeitstempel im Alert-Tab.**
- **ntfy-Logging:** `_dispatch` loggt fehlgeschlagene Notifier.

### Phase C – Alarm Limits UI-Umbau (v1.11.16)

- **Alarm Limits-Tab:** Raum-Kacheln mit Geräte-Kacheln, Limits als farbige
  Chips (Warning gelb, Critical rot, Rate blau, not configured grau).
- **Severity-Checkboxen im Notifications-Tab:** Flex-Layout, klickbare Labels.
- **States-Tabelle im Edit-Limits-Formular:** Linksbündig, `width: auto`.
- **ntfy ASCII-safe Title:** `NtfyNotifier` ersetzt Nicht-ASCII-Zeichen im
  `Title`-Header.

### Phase C – Alarm Limits Polish (v1.11.17)

- **Letzte Messwerte:** Aktuelle Werte pro Measurement im Alarm Limits-Tab.
- **„Show all"-Filter:** Checkbox unten im Tab.
- **Stale/Invalid pro Gerät:** Neue `device`-Sektion in `alarm_limits.json`.
  Ein Alert pro Gerät, nicht pro Measurement.
- **Nicht-Alarm-Trigger-States entfernt:** `door_locked`, `defrost`, `flap`,
  `lights.*`, `switches.*` aus `sensor_schemas.py`.
- **`operation_mode` entfernt:** Aus `sensor_schemas.py` für `memmert`.
- **Nested State Keys Fix:** Regex erlaubt mehrere Punkte.
- **Chip-Texte gekürzt:** „Warn", „Crit", „not conf.".
- **Einheiten:** „celsius" → „°C", „percent" → „%".

### Phase C – Alert-Message + Chip-Polish (v1.11.18)

- **Alert-Messages:** Werte auf 1 Nachkommastelle gerundet, Einheiten
  umgewandelt (`°C`, `%`).
- **Chip-Texte:** Pfeile für Min/Max (`Warn ↓ 20 °C · ↑ 23 °C`,
  `Crit ↓ 18 °C · ↑ 28 °C`, `Rate ↕ 1 °C/h`). Nicht konfiguriert:
  `Warn n/c`, `Crit n/c`, `Rate n/c`.
- **`resolve`-Fix:** Alert bleibt aktiv, wenn mindestens ein Channel
  `invalid`/`stale` ist.
- **`UNIT_LABELS`/`unitLabel` in `admin.py`.**
- **`max-content` für State-Chips.**
- **„not applicable" für leere States.**

---

### Phase C – How-to-Texte + Delete-Sicherheit (v1.11.19)

- **How-to-Texte in allen Tabs** (Rooms, Alarm Limits, Mail, Notifications,
  Messages, Alerts).
- **Delete-Sicherheit:** Doppelte Abfrage, Räume mit Sensoren können nicht
  gelöscht werden, Limits werden mit dem Sensor gelöscht.

---

### Phase C – Dashboard-Limits (v1.12.0)

- **Limit-Chips:** Rechtsbündig im Header der Metric-Zellen (Raumdetail +
  Device-Detail). Nur wenn Limits gesetzt und enabled.
- **Statusleuchte:** Rot bei Crit-Verletzung, Gelb bei Warn-Verletzung.
- **Status-Chips:** `[Warning: temperature above limit]`, etc.
- **Graphen-Linien:** Horizontale Linien für Warn/Crit Min/Max als separate
  Datasets.

---

## 5. OtterPi HTTP Listener

Der OtterPi-Anwendungsserver lauscht derzeit nicht öffentlich.

Die produktive Konfiguration ist:

```text
OTTERPI_HOST=127.0.0.1
OTTERPI_PORT=8090
```

Damit ist der direkte Anwendungslistener:

```text
127.0.0.1:8090
```

Der API-Endpunkt ist:

```text
POST /api/v1/batches
```

Der LoggerPi soll nicht direkt auf Port 8090 zugreifen.

---

## 6. Produktionspfad (verifiziert 2026-09-20)

Der produktive HTTP-Weg erfolgt über den bestehenden nginx/TLS-Stack
des OtterPi:

```text
LoggerPi
    │
    │ HTTPS :443
    ▼
nginx
    │
    │ reverse proxy
    ▼
127.0.0.1:8090
    │
    ▼
OtterPi Observer
    │
    ▼
BatchStore
    │
    ▼
SQLite
```

Port 8090 bleibt dabei lokal.

---

## 7. nginx

Die bestehende OtterPi-Installation verwendet nginx bereits als
zentrale HTTP-/HTTPS-Einstiegsschicht.

Vorhandene Infrastruktur darf nicht durch das LoggerPi-OtterPi-
Deployment überschrieben werden.

Insbesondere sind bestehende Serverblöcke für:

```text
MeshCentral
Pi-hole
sonstige bestehende Domains
```

zu erhalten.

Die LoggerPi-OtterPi-Proxy-Konfiguration soll deshalb als eigener
nginx-Serverblock bzw. als eindeutig abgegrenzte Konfiguration
hinzugefügt werden.

Die konkrete produktive Domain muss vor Aktivierung festgelegt und
dokumentiert werden.

### Verifikation (2026-09-20)

Der nginx-Reverse-Proxy für `loggerpi.makki.route64.de` ist eingerichtet
und verifiziert:

```nginx
location /api/v1/batches {
    proxy_pass http://127.0.0.1:8090;
    ...
}
```

Die Konfiguration wurde mit `sudo nginx -t` geprüft und funktioniert
im produktiven Betrieb.

---

### Admin (LAN-only)

Der Admin ist Teil des OtterPi-Service und wird über nginx auf das LAN
beschränkt. Die Admin-UI bietet Formular-UI in allen Tabs (Rooms, Alarm
Limits, Mail, Notifications) mit JSON-Editor als „Advanced"-Toggle.

```nginx
location /admin {
    allow 192.168.178.0/24;
    deny all;
    proxy_pass http://127.0.0.1:8090;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
}

location /api/admin/ {
    allow 192.168.178.0/24;
    deny all;
    proxy_pass http://127.0.0.1:8090;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
}
```

Nach Änderung:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Der Handler macht keine IP-Prüfung. Öffnen nach öffentlich = nginx + Auth,
kein Code-Umbau.

---

## 8. TLS

Die TLS-Zertifikate werden auf dem OtterPi durch die bestehende
Zertifikatsverwaltung bereitgestellt.

Das Projekt-Deployment darf vorhandene Zertifikate nicht ersetzen
oder löschen.

Vor Aktivierung des neuen Proxy-Blocks muss geprüft werden:

```bash
sudo certbot certificates
```

und:

```bash
sudo nginx -t
```

Nach Änderungen:

```bash
sudo systemctl reload nginx
```

Ein Reload ist einem unnötigen vollständigen Restart vorzuziehen.

---

## 9. nginx-Verifikation

Nach Einrichtung des Proxy-Blocks:

```bash
sudo nginx -t
```

Danach:

```bash
sudo systemctl reload nginx
```

Lokaler Backend-Test:

```bash
curl -i http://127.0.0.1:8090/
```

Dabei ist ein HTTP-404 für einen nicht vorhandenen GET-Endpunkt
nicht automatisch ein Fehler. Entscheidend ist, dass der Listener
erreichbar ist.

Der API-Endpunkt muss mit einem gültigen Core-Batch getestet werden.

Extern soll ausschließlich die definierte HTTPS-Adresse verwendet
werden.

Port 8090 darf nicht als öffentlicher Service exponiert werden.

---

## 10. Deployment-Verifikation

Nach jedem Application Deployment:

```bash
systemctl status loggerpi.observer.service --no-pager
```

bzw.:

```bash
systemctl status otterpi.observer.service --no-pager
```

Commit prüfen:

```bash
cat /opt/loggerpi-otterpi/DEPLOYED_COMMIT
```

Version prüfen:

```bash
cat /opt/loggerpi-otterpi/DEPLOYED_VERSION
cat /opt/loggerpi-otterpi/VERSION
```

Zusätzlich:

```bash
journalctl -u loggerpi.observer.service -n 100 --no-pager
```

bzw.:

```bash
journalctl -u otterpi.observer.service -n 100 --no-pager
```

---

## 11. Wichtige Trennung

Das Application Deployment aktualisiert derzeit:

```text
Python-Anwendung
systemd-Service
Deployment-Wrapper
```

Es aktualisiert derzeit nicht automatisch:

```text
nginx
TLS-Zertifikate
DNS
Firewall
FRITZ!Box
IPv6-Freigaben
CDN/Tunnel
```

Diese Trennung ist absichtlich.

---

## 12. Produktionsfreigabe (erfüllt 2026-09-20)

Der neue LoggerPi → OtterPi-Datenpfad ist praktisch verifiziert.
Die folgende Kette wurde erfolgreich getestet:

```text
LoggerPi
    ↓
Core Batch
    ↓
lokale Queue
    ↓
HTTPS
    ↓
nginx
    ↓
127.0.0.1:8090
    ↓
OtterPi Observer
    ↓
BatchStore
    ↓
SQLite
    ↓
HTTP 202
    ↓
LoggerPi entfernt Queue-Eintrag
```

Dabei müssen insbesondere geprüft werden:

- erfolgreicher Batch
- ungültiger Batch
- Duplicate Batch
- Netzwerkunterbrechung
- Queue-Replay
- Neustart des OtterPi
- Neustart des LoggerPi
- nginx reload
- Zertifikatsstatus
- Persistenz der SQLite-Datenbank

---

## 13. Aktueller Stand

Stand 2026-11-08:

```text
Repository:
    main

Version:
    v1.12.0

Letzter bekannter Release-Commit:
    (wird beim Deploy gesetzt)

Application Deployment:
    implementiert

LoggerPi Deployment:
    auf dem Raspberry Pi verifiziert (2026-09-20)

OtterPi Deployment:
    auf dem Raspberry Pi verifiziert (2026-09-20)

OtterPi Anwendung:
    systemd-Service im Repository definiert

OtterPi Backend:
    127.0.0.1:8090

API:
    POST /api/v1/batches

Authentication:
    Bearer Token (seit v1.1.0)

Dashboard:
    https://observer.makki.route64.de (seit v1.2.0)

Einstiegsseite:
    https://zoology.makki.route64.de

nginx:
    Reverse-Proxy für loggerpi.makki.route64.de eingerichtet und verifiziert
    Reverse-Proxy für observer.makki.route64.de eingerichtet und verifiziert

TLS:
    Zertifikate auf OtterPi vorhanden
    LoggerPi-OtterPi-nginx-Einbindung aktiv

End-to-End-Produktion:
    verifiziert (2026-09-20)
    LoggerPi sendet Batches alle 15 Minuten
    OtterPi speichert in SQLite

Dashboard:
    https://observer.makki.route64.de (seit v1.2.0)
    Raumdetailseiten: /room/<id>
    Gerätedetailseiten: /device/<sensor_id>
    Raumklima-Detailseiten: /climate/<room_id>
    URL-Umbenennung: /raum/ → /room/ (301-Redirect)

Archivierung:
    Monatlich (1. des Monats, 03:00 Uhr)
    Pfad: /var/lib/loggerpi-otterpi/archive/
    Format: loggerpi-otterpi_batches_YYYY-MM.json.gz
    Retention: 12 Monate in Live-DB
```
