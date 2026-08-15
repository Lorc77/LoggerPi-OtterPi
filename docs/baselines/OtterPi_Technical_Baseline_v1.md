# OtterPi – TECHNICAL BASELINE / EXPLORATION RECORD v1

**Stand:** 14.08.2026  
**Host:** otterpi  
**Zweck:** Technische Ausgangsbasis für künftige Projekte, Fehlersuche, Änderungen und Sicherheitsbewertungen.

**Wichtig:** Dieser Record dokumentiert den Ist-Zustand. Er enthält bewusst keine zuvor sichtbaren Secrets, Keys oder Passwörter.

---

## 1. Executive Summary

otterpi ist ein produktiver Raspberry-Pi-Host mit **Debian GNU/Linux 13 (trixie)**, ARM64 und Raspberry-Pi-Kernel.

### Netzwerkarchitektur

```text
                         INTERNET

                            │

              ┌─────────────┴─────────────┐

              │                           │

          IPv4 only                    IPv6

              │                           │

        CDN / Tunnel                     │

              │                           │

              └──────────────┬────────────┘

                             │

                       FRITZ!Box 6690

                        Cable / DS-Lite

                             │

                       192.168.178.0/24

                             │

                      192.168.178.100

                           otterpi

                ┌────────────┴────────────┐

                │                         │

              nginx                   interne

                │                     Dienste

             80 / 443

                │

       ┌────────┴─────────┐

       │                  │

   MeshCentral         Pi-hole

   localhost:4430      localhost:8080
```

### Öffentlich vorgesehen

- TCP 80
- TCP 443

### Intern vorgesehen

- SSH 22
- DNS 53 TCP/UDP
- Pi-hole Web 8080
- MeshCentral 4430
- MeshCentral 4433
- MeshCentral 1024
- MeshCentral UDP 16989
- rpcbind 111
- Avahi/mDNS 5353
- weitere lokale Dienste

### Aktueller wichtiger Sicherheitsbefund

Der Host besitzt eine **global routbare IPv6-Adresse** und hat **keine aktive lokale ufw/nftables-Firewall**.

Trotzdem wurde von einem externen IPv6-Scanner festgestellt:

| Port | Ergebnis |
|---|---|
| 80/TCP | **OPEN** |
| 443/TCP | **OPEN** |
| 22/TCP | **CLOSED** |
| 53/TCP | **CLOSED** |
| 111/TCP | **CLOSED** |
| 8080/TCP | **CLOSED** |
| 1024/TCP | **CLOSED** |
| 4430/TCP | **CLOSED** |
| 4433/TCP | **CLOSED** |

Damit ist **aktuell empirisch bestätigt**, dass die getesteten internen TCP-Ports von außen nicht erreichbar waren.

Das ist allerdings keine Aussage darüber, **warum** sie geschlossen sind. Genau das ist einer der noch offenen Punkte.

---

## 2. Hardware / Betriebssystem

### Host

Hostname:       otterpi

Architektur:    aarch64 / ARM64

CPU:            4 × Cortex-A72

OS:             Debian GNU/Linux 13 (trixie)

Debian:         13.6

Kernel:         6.18.39+rpt-rpi-v8

Kernel Build:   Debian 1:6.18.39-1+rpt1

Uptime zum Zeitpunkt der Erhebung:

9 Tage, 3:03

Load:

0,02 / 0,11 / 0,12

Keine CPU-Auslastungsprobleme erkennbar.

---

## 3. RAM / Swap

RAM gesamt:      ~905 MiB

RAM benutzt:     ~379 MiB

RAM verfügbar:   ~525 MiB

Swap gesamt:     ~904 MiB

Swap benutzt:    ~185 MiB

Swap:

- zram0
- zusätzlich rpi-swap als Loopdevice

Zum Zeitpunkt der Erhebung keine akute Speicherknappheit.

---

## 4. Storage

Medium:

mmcblk0

Kapazität:

~59,5 GB

Partitionen:

mmcblk0p1    512 MB    FAT32    /boot/firmware

mmcblk0p2    ~59 GB    ext4     /

Root:

58 GB

11 GB benutzt

45 GB frei

19 %

Inodes:

~7 % benutzt

Damit aktuell reichlich Platz vorhanden.

---

## 5. Netzwerk – IPv4

Interface:

eth0

Adresse:

192.168.178.100/24

Gateway:

192.168.178.1

Netz:

192.168.178.0/24

WLAN:

wlan0 DOWN

Die FRITZ!Box ist damit Gateway für das lokale IPv4-Netz.

---

## 6. Netzwerk – IPv6

Global:

2a02:908:1a66:ecc0:da3a:ddff:fe91:f971/64

ULA:

fdb7:145b:1d9f:0:da3a:ddff:fe91:f971/64

Link-local:

fe80::da3a:ddff:fe91:f971/64

Default Gateway:

fe80::8223:95ff:fe8d:dce

IPv6 Default Route ist vorhanden.

Kernel:

net.ipv6.conf.all.forwarding = 0

net.ipv6.conf.all.accept_ra = 1

Das bedeutet:

- otterpi ist **kein IPv6-Router**
- er akzeptiert Router Advertisements
- er besitzt eine **global routbare IPv6-Adresse**
- IPv6-Inbound ist daher grundsätzlich relevant

---

## 7. DS-Lite / IPv4-Erreichbarkeit

Der Anschluss läuft über **DS-Lite**.

Deshalb:

- keine normale direkte eingehende IPv4-Erreichbarkeit zum Pi
- öffentliche IPv4-Erreichbarkeit wird für relevante Dienste über **CDN/Tunnel** bereitgestellt

Für makki.route64.de ist daher die IPv4-Sicht nicht identisch mit der IPv6-Sicht.

Das ist für zukünftige Tests wichtig:

Ein IPv4-Portscan gegen die öffentliche Domain testet nicht zwangsläufig direkt otterpi.

---

## 8. FRITZ!Box

Gerät:

**FRITZ!Box 6690 Cable**

Bekannter IPv4-Portforwarding-Stand:

TCP 80 → otterpi

TCP 443 → otterpi

Nach bisheriger Aussage sind keine weiteren IPv4-Ports weitergeleitet.

### Wichtige Einschränkung

Diese IPv4-Regeln sagen **nicht**, welche IPv6-Ports erreichbar sind.

IPv6 besitzt eine andere Erreichbarkeits-/Filterlogik.

Deshalb war der externe IPv6-Test notwendig.

---

## 9. Externer IPv6-Test

Getestete globale IPv6:

2a02:908:1a66:ecc0:da3a:ddff:fe91:f971

### Ergebnis

| TCP | Ergebnis |
|---|---|
| 80 | 🟢 OPEN |
| 443 | 🟢 OPEN |
| 22 | 🔴 CLOSED |
| 53 | 🔴 CLOSED |
| 111 | 🔴 CLOSED |
| 8080 | 🔴 CLOSED |
| 1024 | 🔴 CLOSED |
| 4430 | 🔴 CLOSED |
| 4433 | 🔴 CLOSED |

### Interpretation

Das gewünschte Modell ist damit zumindest für die getesteten TCP-Ports erfüllt:

```text
INTERNET

   │

   ├── 80   → erreichbar

   ├── 443  → erreichbar

   │

   └── alles getestete Interne → nicht erreichbar
```

Aber:

**UDP wurde noch nicht extern getestet.**

Insbesondere relevant:

- UDP 53
- UDP 111
- UDP 5353
- UDP 16989
- weitere UDP-Listener

---

## 10. Listening Ports

Aus:

```text
sudo ss -lntup
```

### TCP

| Bind | Port | Prozess | Zweck |
|---|---:|---|---|
| 0.0.0.0 / [::] | 80 | nginx | HTTP |
| 0.0.0.0 / [::] | 443 | nginx | HTTPS |
| 0.0.0.0 / [::] | 22 | sshd | SSH |
| 0.0.0.0 / [::] | 53 | pihole-FTL | DNS |
| 0.0.0.0 / [::] | 8080 | pihole-FTL | Pi-hole Web |
| 0.0.0.0 / [::] | 111 | rpcbind | RPC |
| * | 1024 | Node/MeshCentral | MeshCentral |
| * | 4430 | Node/MeshCentral | MeshCentral |
| * | 4433 | Node/MeshCentral | MeshCentral |
| 127.0.0.1 / ::1 | 6010 | sshd-session | lokal |

### UDP

| Port | Prozess | Zweck |
|---:|---|---|
| 53 | pihole-FTL | DNS |
| 123 | pihole-FTL | NTP |
| 111 | rpcbind | RPC |
| 5353 | avahi-daemon | mDNS |
| 16989 | Node/MeshCentral | MeshCentral |
| 546 | NetworkManager | DHCPv6 |
| 48833 | avahi-daemon | dynamisch |
| 42626 | avahi-daemon | dynamisch |

---

## 11. MeshCentral

Installationspfad:

```text
/opt/meshcentral
```

Prozess:

```text
/usr/bin/node --disable-proto=delete \
/opt/meshcentral/node_modules/meshcentral \
--launch 53193
```

PID zum Zeitpunkt der Erhebung:

53211

User:

meshcentral

Systemd:

meshcentral.service

### Version

Direkt aus package.json verifiziert:

MeshCentral 1.2.4

Node:

v20.19.2

npm:

9.2.0

---

## 12. MeshCentral Architektur

Konfiguration:

```text
cert: mesh.makki.route64.de

port:       4430

aliasPort:  443

redirPort:  80

trustedProxy: 127.0.0.1

tlsoffload: true
```

Die relevante Architektur ist:

```text
Internet

   │

   ├── :80

   └── :443

       │

       ▼

      nginx

       │

       ▼

127.0.0.1:4430

       │

       ▼

 MeshCentral
```

Damit sind 4430/4433/1024 etc. nicht als öffentliche Webports gedacht.

---

## 13. MeshCentral weitere Listener

MeshCentral/Node lauscht:

TCP 1024

TCP 4430

TCP 4433

UDP 16989

Die Ports wurden extern bereits getestet:

```text
1024  CLOSED
4430  CLOSED
4433  CLOSED
```

Damit sind diese MeshCentral-Ports momentan nicht direkt aus dem IPv6-Internet erreichbar.

---

## 14. nginx

Version:

nginx 1.26.3

Listener:

80

443

jeweils IPv4 und IPv6.

### Ermittelte Servernamen

- makki.route64.de
- mesh.makki.route64.de
- pihole.makki.route64.de
- status
- status.makki.route64.de

### Bekannte Proxy-Ziele

MeshCentral:

```text
127.0.0.1:4430
```

Pi-hole:

```text
127.0.0.1:8080
```

nginx ist damit die zentrale HTTP/HTTPS-Einstiegsschicht.

---

## 15. Pi-hole

Direkt über `pihole -v` ermittelt:

```text
Core:  v6.4.3
Web:   v6.6
FTL:   v6.7
```

Listener:

- TCP 53
- UDP 53
- TCP 8080

auf IPv4 und IPv6.

Pi-hole wird außerdem über nginx unter:

```text
pihole.makki.route64.de
```

bereitgestellt.

Externer IPv6-Test:

```text
TCP 53    CLOSED
TCP 8080  CLOSED
```

---

## 16. rpcbind / NFS

Aktiv:

```text
rpcbind.service
nfs-blkmap.service
```

Installiert:

```text
nfs-common
rpcbind
```

`rpcinfo -p` zeigt aktuell ausschließlich:

```text
program 100000
portmapper
```

auf:

```text
TCP 111
UDP 111
```

Keine weiteren NFS-RPC-Dienste wurden gefunden.

### Bewertung

Das ist kein akuter externer Befund, weil:

```text
TCP 111 → extern CLOSED
```

Trotzdem ist rpcbind auf einem öffentlich adressierten Host eine zu prüfende Angriffsfläche, **falls es nicht benötigt wird**.

**Nicht einfach deaktivieren.**

---

## 17. SSH

Version:

OpenSSH 10.0p1-7+deb13u4

Listener:

```text
0.0.0.0:22
[::]:22
```

Extern:

```text
IPv6 TCP 22 → CLOSED
```

Damit ist SSH derzeit nicht öffentlich über IPv6 erreichbar.

---

## 18. Avahi

Aktiv:

```text
avahi-daemon.service
```

Listener:

- UDP 5353
- sowie dynamische UDP-Ports

Zweck:

mDNS / DNS-SD

Das ist grundsätzlich LAN-orientiert.

Eine externe UDP-Prüfung steht noch aus.

---

## 19. Firewall

Installiert:

```text
nftables 1.1.3-1
```

Aber:

```text
nftables.service → inactive
```

UFW:

nicht installiert

iptables:

kein entsprechendes Kommando vorhanden

Die bisherigen Abfragen lieferten daher keine aktive Host-Firewall.

### Sehr wichtiger Baseline-Punkt

Aktuell gibt es **keine bewusst konfigurierte Host-Firewall**, auf die wir uns als primären Schutzmechanismus verlassen.

Trotzdem sind die getesteten internen IPv6-TCP-Ports von außen geschlossen.

Die Ursache dafür muss nicht zwingend auf otterpi liegen.

Mögliche Schutzebenen sind beispielsweise:

```text
Internet

   ↓

Provider / IPv6

   ↓

FRITZ!Box IPv6 Firewall

   ↓

otterpi

   ↓

Dienst
```

Genau diese Kette ist noch nicht vollständig dokumentiert.

---

## 20. Systemd

Zum Zeitpunkt der Erhebung aktiv:

```text
accounts-daemon
avahi-daemon
bluetooth
cron
dbus
fcgiwrap
getty@tty1
lightdm
meshcentral
NetworkManager
nfs-blkmap
nginx
pihole-FTL
polkit
rpcbind
serial-getty@ttyS0
ssh
systemd-hostnamed
systemd-journald
systemd-logind
systemd-timesyncd
systemd-udevd
udisks2
user@1000
wpa_supplicant
```

Fehlgeschlagene Units:

```text
keine
```

---

## 21. Dienste, die später auf Notwendigkeit geprüft werden sollten

**Keine unmittelbare Abschaltung!**

Nur Kandidaten für eine spätere Bestandsaufnahme:

### Bluetooth

```text
bluetooth.service
```

### Desktop

```text
lightdm.service
```

### CGI

```text
fcgiwrap.service
```

### mDNS

```text
avahi-daemon.service
```

### RPC/NFS

```text
rpcbind.service
nfs-blkmap.service
```

Die Frage ist jeweils:

**Wird dieser Dienst auf dem produktiven otterpi tatsächlich benötigt?**

---

## 22. Systemd Timer

Vorhanden:

```text
apt-daily.timer
apt-daily-upgrade.timer
meshcentral-cert-check.timer
certbot.timer
man-db.timer
systemd-tmpfiles-clean.timer
dpkg-db-backup.timer
logrotate.timer
rpi-zram-writeback.timer
e2scrub_all.timer
fstrim.timer
```

Das System besitzt damit automatische Wartungsmechanismen.

Besonders relevant:

- apt-daily
- apt-daily-upgrade
- certbot
- meshcentral-cert-check

---

## 23. Benutzer

Nicht-systemischer Benutzer:

```text
makki
```

UID 1000

Home:

```text
/home/makki
```

Shell:

```text
/bin/bash
```

Weitere relevante Ausgabe:

```text
nobody
```

Keine weiteren normalen Benutzer gefunden.

---

## 24. sudo

makki besitzt:

```text
(ALL : ALL) ALL
```

also vollständige sudo-Rechte.

Das ist für einen administrierten Einzelhost nicht ungewöhnlich.

Für die Sicherheitsbetrachtung bedeutet es allerdings:

**Wer makki übernehmen kann, hat grundsätzlich vollständige Kontrolle über den Host.**

---

## 25. Cron

`/etc/cron.d`:

```text
certbot
e2scrub_all
pihole
.placeholder
```

`cron.daily`:

```text
apt-compat
dpkg
logrotate
man-db
.placeholder
```

Keine ungewöhnlichen zusätzlichen Cronjobs in der gezeigten Liste.

---

## 26. Container

Keine laufenden/registrierten Docker- oder Podman-Container festgestellt.

---

## 27. Storage / Mounts – Sicherheitsmerkmale

Viele virtuelle Dateisysteme verwenden:

```text
nosuid
nodev
noexec
```

wo sinnvoll.

Beispiele:

```text
/run
/dev/shm
/tmp
/sys
/proc
/run/credentials/...
```

Root:

```text
/dev/mmcblk0p2

rw,noatime
```

Keine offensichtliche ungewöhnliche Mount-Struktur festgestellt.

---

## 28. Paketstand

Relevante Versionen:

```text
Debian             13.6
Kernel             6.18.39+rpt-rpi-v8

nginx              1.26.3
Node.js            20.19.2
npm                 9.2.0
OpenSSH             10.0p1
certbot              4.0.0
nftables             1.1.3
rpcbind              1.2.7
nfs-common           2.8.3
avahi-daemon         0.8

MeshCentral          1.2.4

Pi-hole Core         6.4.3
Pi-hole Web          6.6
Pi-hole FTL          6.7
```

### Achtung bei APT

Die erste Suche nach:

```text
grep -RhsE '^[[:space:]]*deb '
```

hat keine Quellen ausgegeben.

Das bedeutet **nicht**, dass keine APT-Quellen vorhanden sind.

Debian 13 verwendet häufig `.sources`/deb822-Dateien.

Das muss separat geprüft werden.

---

## 29. DNS

NetworkManager:

```text
search fritz.box

nameserver 192.168.178.100

nameserver 2a02:908:1a66:ecc0:da3a:ddff:fe91:f971
```

Der Pi verwendet sich also selbst als DNS-Resolver.

Das passt zur Pi-hole-Konfiguration.

---

## 30. Secrets / bereits exponierte Werte

Während der Exploration wurden zuvor Konfigurationswerte ausgegeben, die als Secrets einzustufen sind.

Sie werden hier **absichtlich nicht wiederholt**.

Insbesondere betrifft das Werte aus der MeshCentral-Konfiguration.

### Baseline-Regel

Diese Werte sollten als potentiell kompromittiert behandelt werden.

Bei Gelegenheit:

- Session-/Secret-Werte rotieren
- Backup-Passwort rotieren
- sonstige API-/Service-Keys prüfen
- künftig keine vollständigen Secrets mehr per Terminalausgabe in den Chat kopieren

Das gilt unabhängig davon, ob tatsächlich ein Missbrauch stattgefunden hat.

---

## 31. Was aktuell sicher bekannt ist

### Verifiziert

1. otterpi ist ein produktiver Raspberry Pi.
2. Debian 13.6 / ARM64.
3. IPv4-Adresse 192.168.178.100.
4. FRITZ!Box 6690 Cable davor.
5. DS-Lite.
6. Globales IPv6 direkt am Host.
7. IPv4-Publikation teilweise über CDN/Tunnel.
8. nginx auf 80/443.
9. MeshCentral 1.2.4.
10. MeshCentral intern auf 4430 etc.
11. Pi-hole Core 6.4.3 / Web 6.6 / FTL 6.7.
12. SSH auf 22.
13. Pi-hole DNS auf 53.
14. Pi-hole Web auf 8080.
15. rpcbind auf 111.
16. Keine aktive ufw/nftables-Hostfirewall.
17. IPv6 TCP 80/443 extern offen.
18. Die getesteten internen TCP-Ports extern geschlossen.
19. Keine failed systemd units.
20. Keine Docker-/Podman-Container.
21. makki besitzt sudo-Rechte.

---

## 32. Noch nicht abschließend geklärt

### Netzwerk

- Warum genau die IPv6-Ports 22/53/111/8080/1024/4430/4433 extern geschlossen sind.
- Welche IPv6-Firewall-/Freigaberegeln die FRITZ!Box tatsächlich verwendet.
- Ob UDP von außen erreichbar ist.
- Ob alle gewünschten Domains ausschließlich über 80/443 erreichbar sind.

### nginx

- vollständige Serverblock-Konfiguration
- Redirects
- Access-Control
- Header
- TLS-Konfiguration
- alle Proxy-Ziele

### Dienste

- Wird rpcbind benötigt?
- Wird NFS benötigt?
- Wird Avahi benötigt?
- Wird Bluetooth benötigt?
- Wird fcgiwrap benötigt?
- Wird LightDM benötigt?

### Infrastruktur

- vollständige APT-Quellen
- ausstehende Updates
- genaue CDN-/Tunnel-Komponente
- vollständige Zertifikatsstruktur

---

## 33. Gewünschtes Sicherheitsmodell

Das Ziel für otterpi lautet:

```text
                         INTERNET

                            │

                     ┌──────┴──────┐

                     │             │

                   IPv4          IPv6

                     │             │

                CDN/Tunnel         │

                     │             │

                     └──────┬──────┘

                            │

                           80

                           443

                            │

                          nginx

                            │

                ┌───────────┴───────────┐

                │                       │

          MeshCentral              Pi-hole

          127.0.0.1:4430          127.0.0.1:8080
```

Direkte öffentliche Erreichbarkeit:

```text
TCP 80
TCP 443
```

Alles andere:

```text
LAN / localhost / intern
```

---

## 34. Was wir ausdrücklich NICHT gemacht haben

Im Rahmen der Baseline:

- ❌ keine Firewall installiert
- ❌ nftables nicht aktiviert
- ❌ keine iptables-Regeln angelegt
- ❌ keine Routingänderung
- ❌ keine IPv6-Konfiguration verändert
- ❌ keine FRITZ!Box-Konfiguration verändert
- ❌ keine Dienste deaktiviert
- ❌ keine Pakete entfernt
- ❌ keine Ports geschlossen
- ❌ keine MeshCentral-Konfiguration geändert
- ❌ nginx nicht verändert

Die Erfassung war grundsätzlich **read-only**.

---

## 35. Empfohlene nächste Untersuchung

Ohne Änderungen am Produktivsystem.

### Phase A – IPv6 vollständig verstehen

Nur lesen bzw. extern testen:

1. FRITZ!Box IPv6-Freigaben prüfen.
2. IPv6-Firewall-Einstellungen dokumentieren.
3. Extern UDP testen.
4. Optional zweiter externer IPv6-Anschluss.

Ziel:

Warum ist 80/443 offen,

aber 22/53/111/8080/... geschlossen?

### Phase B – nginx vollständig dokumentieren

Komplette Serverblöcke erfassen.

Ziel:

Welche Domain

→ welcher nginx `server{}`

→ welches Backend?

### Phase C – Dienste klassifizieren

Für jeden Dienst:

```text
NOTWENDIG
OPTIONAL
UNBEKANNT
```

Insbesondere:

```text
rpcbind
nfs-blkmap
fcgiwrap
avahi
bluetooth
lightdm
```

### Phase D – Update-/Repository-Baseline

Erfassen:

- `.sources`
- installierte Updates
- ausstehende Updates
- Fremd-Repositories
- Node/MeshCentral-Installationsquelle

### Phase E – Secret-Hygiene

Separat:

Welche Secrets wurden bisher sichtbar?

Welche müssen rotiert werden?

Welche Services müssen danach neu gestartet werden?

Das sollte **nicht** zusammen mit Netzwerkänderungen gemacht werden.

---

## 36. Referenz für zukünftige Projekte

Für zukünftige Gespräche über otterpi können wir diesen Zustand als Ausgangspunkt verwenden:

**otterpi ist ein produktiver Debian-13-ARM64-Raspberry-Pi hinter einer FRITZ!Box 6690 Cable mit DS-Lite. IPv4-Publikation erfolgt für relevante Dienste über CDN/Tunnel. IPv6 ist direkt global am Host vorhanden. nginx stellt 80/443 bereit und proxied u. a. MeshCentral auf localhost:4430 und Pi-hole auf localhost:8080. MeshCentral 1.2.4 läuft als eigener systemd-Dienst. Pi-hole Core 6.4.3 / Web 6.6 / FTL 6.7 läuft lokal. SSH, DNS, rpcbind und weitere Dienste lauschen intern auf allen Interfaces. Es gibt derzeit keine aktive Host-Firewall via ufw/nftables. Externe IPv6-Tests haben 80/443 als OPEN und die getesteten internen TCP-Ports als CLOSED gezeigt. Änderungen müssen daher zunächst lesend geplant und besonders vorsichtig umgesetzt werden; Firewall-/Routingänderungen sind nicht Teil der Baseline-Erstellung.**

---

## 37. Änderungslog

### v1 – 14.08.2026

Erfasst:

- Hardware
- CPU/RAM/Storage
- Betriebssystem
- Kernel
- IPv4
- IPv6
- Routing
- DS-Lite-Kontext
- FRITZ!Box-Kontext
- CDN/Tunnel-Kontext
- externe IPv6-Erreichbarkeit
- TCP/UDP-Listener
- nginx
- MeshCentral
- MeshCentral-Version **1.2.4**
- Pi-hole-Versionen
- SSH
- rpcbind/NFS
- Avahi
- Systemd
- Timer
- Cron
- Benutzer
- sudo
- Container
- Mounts
- Paketbestand
- Firewall-Situation
- bekannte Unsicherheiten
- zukünftige Untersuchungsbereiche
- Secret-Hygiene

**Keine Systemänderungen durchgeführt.**

---

## Kurzfassung für uns beide

Der wichtigste Satz für die Zukunft ist eigentlich:

**Wir haben einen produktiven Pi ohne lokale Host-Firewall, aber die externe IPv6-Messung zeigt aktuell genau das gewünschte TCP-Bild: 80/443 offen, die getesteten internen Ports geschlossen. Jetzt dokumentieren wir erst, warum das so ist, bevor wir irgendetwas anfassen.**

Damit ist die **Baseline v1 abgeschlossen**.
