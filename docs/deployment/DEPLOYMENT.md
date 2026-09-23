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

### Neue Umgebungsvariablen (seit v1.3.0)

| Variable | Bedeutung | Default |
|----------|-----------|---------|
| `LOGGERPI_FREEZER_ENABLED` | Freezer-Reader aktivieren | `1` |
| `LOGGERPI_THINGSPEAK_ENABLED` | ThingSpeak-Injektion aktivieren | `0` |
| `LOGGERPI_THINGSPEAK_CHANNEL_ID` | ThingSpeak Channel-ID | – |
| `LOGGERPI_THINGSPEAK_API_KEY` | ThingSpeak Write API Key | – |

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
├── delivery.py
├── freezer.py
├── freezer_config.py
├── loggerpi_observer.py
├── loggerpi_runner.py
├── otter2.png (nur OtterPi)
├── otterpi.py (nur OtterPi)
├── otterpi_observer.py (nur OtterPi)
├── otterpi_store.py (nur OtterPi)
├── runtime.py
├── system_info.py
├── thingspeak_delivery.py
├── thingspeak_config.py
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

Stand 2026-09-21:

```text
Repository:
    main

Version:
    v1.2.3

Letzter bekannter Release-Commit:
    61cd803

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
    https://zoology.makki.route64.de (seit v1.2.0)

nginx:
    Reverse-Proxy für loggerpi.makki.route64.de eingerichtet und verifiziert
    Reverse-Proxy für zoology.makki.route64.de eingerichtet und verifiziert

TLS:
    Zertifikate auf OtterPi vorhanden
    LoggerPi-OtterPi-nginx-Einbindung aktiv

End-to-End-Produktion:
    verifiziert (2026-09-20)
    LoggerPi sendet Batches alle 15 Minuten
    OtterPi speichert in SQLite
```
