# LoggerPi – Systeminventar

## Zweck

Dieses Dokument erfasst die aktuell beobachtete Laufzeitkonfiguration des
LoggerPi Raspberry Pi vor weiteren Migrations- oder Bereinigungsarbeiten.

Das Inventar ist bewusst beschreibend. Daraus folgt nicht, dass alle
aufgeführten Services oder Komponenten benötigt werden.

Dieser Snapshot soll verhindern, dass während der laufenden Migration von der
Legacy-Implementierung `observer.py` hin zum neuen Datenmodell und der neuen
Service-Architektur bereits gewonnene Erkenntnisse verloren gehen.

---

## 1. System-Services

### Wichtige Anwendungs- und Zugriffs-Services

| Service | Aktiviert | Läuft | Hinweise |
|---|---:|---:|---|
| `meshagent.service` | ja | ja | Mesh-Remote-Management-Agent |
| `ssh.service` | ja | ja | Primärer Remote-Shell-Zugriff |
| `lightdm.service` | ja | ja | Lokale grafische Anmeldung / LXDE-Umgebung |
| `teamviewerd.service` | nein | nein | Installiert, derzeit aber inaktiv |
| `rsync.service` | ja | nein | Aktiviert, aber inaktiv, da `/etc/rsyncd.conf` nicht existiert |
| `sshswitch.service` | ja | — | Aktiviert SSH, wenn `/boot/ssh` oder `/boot/ssh.txt` vorhanden ist |
| `rc-local.service` | ja | ja | Kompatibilitäts-Service für `/etc/rc.local` |

### Netzwerkbezogene Services

| Service | Aktiviert | Läuft | Hinweise |
|---|---:|---:|---|
| `dhcpcd.service` | ja | ja | DHCP-/Netzwerkkonfiguration |
| `networking.service` | ja | — | ifup/ifdown-basiertes Netzwerk |
| `wpa_supplicant.service` | ja | ja | WLAN-Supplicant |
| `raspberrypi-net-mods.service` | ja | — | Kopiert `/boot/wpa_supplicant.conf`, wenn vorhanden |
| `avahi-daemon.service` | ja | ja | mDNS / lokale Service-Erkennung |
| `ModemManager.service` | ja | ja | Derzeit kein Modem erkannt |
| `bluetooth.service` | ja | ja | Bluetooth-Stack |

### Weitere relevante aktivierte Services

Das System verfügt außerdem über aktivierte Services für:

- AppArmor
- Bluetooth / HCI UART
- CUPS / Druckererkennung
- cron
- Konsolen- und Tastaturkonfiguration
- Fake-Hardware-Uhr
- Raspberry-Pi-Display-Backlight
- Raspberry-Pi-EEPROM-Update
- rsyslog
- systemd-Zeitsynchronisation
- triggerhappy
- udisks2

Das vollständige Service-Inventar wurde am **15.08.2026** direkt auf dem
laufenden System erfasst.

---

## 2. Grafische Umgebung

Eine vollständige grafische Umgebung ist bewusst installiert und aktiviert.

Aktueller Display Manager:

```text
lightdm.service
```

Der Zweck ist die betriebliche Wiederherstellung:

> Ein lokal angeschlossener Monitor und eine Tastatur sollen weiterhin als
> Fallback-Konfigurations- und Wiederherstellungsweg zur Verfügung stehen,
> falls der Remote-Zugriff über SSH / Mesh nicht mehr verfügbar ist.

Die grafische Umgebung darf daher im Rahmen der aktuellen Migration
**nicht entfernt werden**.

### Aktuelle HDMI-Beobachtung

Zum Zeitpunkt der Hardwareprüfung war kein Monitor angeschlossen.

DRM meldet:

```text
card0-HDMI-A-1/status = disconnected
```

Der Raspberry Pi meldet daher aktuell kein angeschlossenes HDMI-Display.

Folgende Grafikkonfiguration ist in `/boot/config.txt` vorhanden:

```text
framebuffer_width=1280
framebuffer_height=720
dtparam=audio=on
camera_auto_detect=1
display_auto_detect=1
dtoverlay=vc4-kms-v3d
max_framebuffers=2
```

Es konnte aus der Root-Shell kein aktives X11-Display abgefragt werden, da:

```text
xrandr --display :0
No protocol specified
Can't open display :0
```

Dies bedeutet **nicht automatisch**, dass Xorg/LXDE nicht läuft. Der Befehl
wurde ohne die Autorisierungsumgebung der X-Sitzung ausgeführt.

Die HDMI-Konfiguration sollte separat untersucht werden, sobald wieder ein
physischer Monitor zur Verfügung steht.

---

## 3. Netzwerkschnittstellen

Aktuelle Schnittstellen:

```text
lo       UNKNOWN   127.0.0.1/8
eth0     UP        141.51.190.103/24
wlan0    DOWN
```

Standardroute:

```text
default via 141.51.190.1 dev eth0
```

Das System arbeitet derzeit daher über kabelgebundenes Ethernet.

WLAN ist vorhanden, aber derzeit deaktiviert bzw. nicht aktiv.

---

## 4. Netzwerk-Services mit offenen Ports

Aktuell offene TCP-Ports:

```text
0.0.0.0:22       sshd
127.0.0.1:631     CUPS
[::]:22          sshd
[::1]:631         CUPS
```

Der wichtigste von außen erreichbare TCP-Service ist SSH auf Port 22.

Für den `meshagent` wurde in diesem Snapshot kein TCP-Listener beobachtet.

Der `meshagent` besitzt jedoch einen UDP-Socket:

```text
0.0.0.0:56448
```

---

## 5. USB- und serielle Hardware

Zu den USB-Geräten gehören:

```text
FTDI FT232 Serial (UART) IC
SMSC9512/9514 Fast Ethernet Adapter
SMSC9514 USB Hub
```

Das FTDI-Gerät wird als

```text
/dev/ttyUSB0
```

bereitgestellt.

Es wird aktuell aktiv von der Legacy-Freezer-Protokollierung verwendet.

Aktueller Prozess:

```text
minicom -C /home/ZOOLOGY-observ/Programs/freezer.log
```

PID zum Zeitpunkt der Inventarisierung:

```text
1349
```

Das Gerät ist damit aktuell wie folgt belegt:

```text
/dev/ttyUSB0 -> minicom -> freezer.log
```

Dies ist eine wichtige Legacy-Abhängigkeit und darf nicht entfernt oder für
andere Zwecke verwendet werden, ohne zuvor die serielle Datenquelle des
Freezers ausdrücklich zu migrieren.

---

## 6. Legacy-Freezer-Logger

Der Legacy-Freezer-Logger schreibt nach:

```text
/home/ZOOLOGY-observ/Programs/freezer.log
```

Aktuelle Datei:

```text
-rw-r--r-- 1 ZOOLOGY-observ ZOOLOGY-observ ...
```

Zuletzt beobachtete Werte:

```text
- 80 C
- 80 C
- 82 C
- 82 C
```

Die Legacy-`observer.py` liest den jeweils neuesten Freezer-Wert aus dieser
Datei.

Damit besteht folgende direkte Abhängigkeit:

```text
serielles Gerät /dev/ttyUSB0
         |
         v
      minicom
         |
         v
    freezer.log
         |
         v
  Legacy observer.py
         |
         v
     ThingSpeak
```

Diese Abhängigkeit soll erhalten bleiben, bis die Freezer-Datenquelle
ausdrücklich in das neue Datenmodell migriert wurde.

---

## 7. RSYNC

`rsync.service` ist aktiviert, läuft derzeit aber nicht.

Der Grund ist:

```text
/etc/rsyncd.conf
```

existiert nicht.

Der installierte systemd-Service ist für den rsync-Daemon-Modus
konfiguriert.

Dies sollte derzeit **nicht** als aktiver Datentransfer-Service interpretiert
werden.

---

## 8. TeamViewer

Ein eigener systemd-Service existiert unter:

```text
/etc/systemd/system/teamviewerd.service
```

Er befindet sich derzeit im Zustand:

```text
disabled
inactive (dead)
```

Der Service startet:

```text
/opt/teamviewer/tv_bin/teamviewerd -d
```

Es wurde kein aktiver TeamViewer-Prozess beobachtet.

Der Service enthält noch einen Legacy-Verweis auf:

```text
/var/run/teamviewerd.pid
```

den systemd aktuell auf den entsprechenden `/run/...`-Pfad normalisiert.

TeamViewer ist als obsolette, inaktive Legacy-Komponente eingestuft und
soll aus der LoggerPi-Installation entfernt werden.

---

## 9. Modem und Bluetooth

ModemManager ist installiert und läuft, aber:

```text
mmcli -L
No modems were found
```

Aktuell waren keine Bluetooth-Geräte gekoppelt bzw. aufgelistet.

Bluetooth selbst läuft und besitzt eine aktive HCI-bezogene Abhängigkeit.

Keines der beiden Subsysteme sollte allein aufgrund dieses Snapshots entfernt
werden. Ihre tatsächliche Notwendigkeit sollte separat bewertet werden.

---

## 10. Dateisysteme

Das Root-Dateisystem ist:

```text
/dev/mmcblk0p2 ext4 rw,noatime
```

Das Boot-Dateisystem ist:

```text
/dev/mmcblk0p1 vfat rw
```

Das System arbeitet derzeit mit einem beschreibbaren Root-Dateisystem.

---

## 11. Architektonische Bedeutung für den aktuellen Stand

Die wichtigsten Erkenntnisse für die laufende Migration von LoggerPi → OtterPi
sind:

1. `lightdm` und die grafische Umgebung bleiben bewusst als lokaler
   Wiederherstellungsweg erhalten.
2. SSH ist aktiviert und läuft derzeit.
3. Ethernet ist der aktive Netzwerkpfad.
4. `/dev/ttyUSB0` wird aktuell von `minicom` verwendet.
5. `freezer.log` ist weiterhin eine aktive Legacy-Datenquelle.
6. Die Legacy-`observer.py` hängt vom Freezer-Log und mehreren externen
   HTTP-Endpunkten ab.
7. `rsync` ist installiert und aktiviert, aber aufgrund der fehlenden
   Konfigurationsdatei nicht aktiv.
8. TeamViewer ist installiert, aber inaktiv und soll aus der
   LoggerPi-Installation entfernt werden.
9. ModemManager und Bluetooth laufen, es wurde jedoch derzeit keine
   Anwendungsebene-Nutzung dieser Geräte beobachtet.
10. Kein Service darf allein aufgrund dieses Inventars deaktiviert oder
    entfernt werden.

---

## 12. Migrationsregel

Bevor eine Legacy-Komponente entfernt oder deaktiviert wird, muss festgestellt
werden, ob sie:

- weiterhin für den aktuellen Datenerfassungspfad benötigt wird,
- für die lokale Wiederherstellung benötigt wird,
- für die neue OtterPi-Architektur benötigt wird,
- lediglich installiert, aber ungenutzt ist,
- oder nur noch historischer Überrest ist.

Änderungen sollen schrittweise durchgeführt und im Repository dokumentiert
werden.

Die Repository-Dokumentation ist die maßgebliche Quelle für
Architekturentscheidungen und erkannte Abhängigkeiten; der laufende
Raspberry Pi ist die maßgebliche Quelle für den aktuellen Laufzeitstatus.
