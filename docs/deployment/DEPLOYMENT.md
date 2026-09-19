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
pytest -q
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

---

## 3. LoggerPi Deployment

Auf dem LoggerPi:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update loggerpi
```

Der Wrapper:

1. klont den aktuellen `main`-Stand temporär,
2. bestimmt den Commit,
3. führt `deploy/loggerpi/install.sh` aus,
4. installiert bzw. aktualisiert die Anwendung unter
   `/opt/loggerpi-otterpi`,
5. installiert die systemd-Service-Datei,
6. aktiviert `loggerpi.observer.service`,
7. startet den Service neu,
8. prüft dessen Zustand,
9. schreibt den deployten Commit nach
   `/opt/loggerpi-otterpi/DEPLOYED_COMMIT`.

Service:

```text
loggerpi.observer.service
```

Konfiguration:

```text
/etc/loggerpi-otterpi/loggerpi.env
```

Installationsverzeichnis:

```text
/opt/loggerpi-otterpi
```

Persistenter Zustand:

```text
/var/lib/loggerpi-otterpi
```

---

## 4. OtterPi Deployment

Auf dem OtterPi:

```bash
sudo /usr/local/sbin/loggerpi-otterpi-update otterpi
```

Der Wrapper:

1. klont den aktuellen `main`-Stand temporär,
2. bestimmt den Commit,
3. führt `deploy/otterpi/install.sh` aus,
4. installiert die OtterPi-Anwendung,
5. installiert bzw. aktualisiert `otterpi.observer.service`,
6. aktiviert den Service,
7. startet ihn neu,
8. prüft dessen Zustand,
9. schreibt den deployten Commit nach
   `/opt/loggerpi-otterpi/DEPLOYED_COMMIT`.

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

## 6. Geplanter Produktionspfad

Der produktive HTTP-Weg soll über den bestehenden nginx/TLS-Stack
des OtterPi erfolgen:

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

## 12. Produktionsfreigabe

Der neue LoggerPi → OtterPi-Datenpfad gilt erst dann als praktisch
verifiziert, wenn mindestens folgende Kette erfolgreich getestet wurde:

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

Stand 2026-09-19:

```text
Repository:
    main

Letzter bekannter Release-Commit:
    1641d48

Application Deployment:
    implementiert

LoggerPi Deployment:
    noch nicht auf dem Raspberry Pi verifiziert

OtterPi Deployment:
    noch nicht auf dem Raspberry Pi verifiziert

OtterPi Anwendung:
    systemd-Service im Repository definiert

OtterPi Backend:
    127.0.0.1:8090

API:
    POST /api/v1/batches

nginx:
    bestehende Infrastruktur vorhanden
    LoggerPi-OtterPi-Reverse-Proxy noch nicht fertig eingerichtet

TLS:
    Zertifikate auf OtterPi vorhanden
    konkrete LoggerPi-OtterPi-nginx-Einbindung noch offen

End-to-End-Produktion:
    noch nicht verifiziert
```
