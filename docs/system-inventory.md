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

    `/dev/ttyUSB0`

bereitgestellt.

Die Schnittstelle ist die serielle Datenquelle des Freezers.

Der aktuelle Logger-Prozess ist nicht mehr an ein grafisches Terminal gebunden. Die serielle Freezer-Protokollierung wird über einen dedizierten User-Service betrieben:

    `freezer-log.service`

Der Runtime-Pfad lautet:

    `/dev/ttyUSB0`
            ↓
         minicom
            ↓
      freezer.log

Der Service läuft unter dem Benutzer `ZOOLOGY-observ` und wird über systemd User Units verwaltet.

Die frühere XDG/LXDE-Autostart-Lösung über `lxterminal` wurde deaktiviert.

Die serielle Schnittstelle darf weiterhin nicht für andere Anwendungen verwendet werden, solange die Freezer-Datenquelle noch über diesen Legacy-Datenpfad betrieben wird.

---

### 5.1 MEMMERT IPP300 – serielle USB-Verbindungen

Auf dem LoggerPi sind zwei MEMMERT IPP300 über USB-Seriell-Adapter
angeschlossen.

Beide Adapter werden als Prolific USB-Serial Controller erkannt:

```text
Vendor:  Prolific Technology Inc.
VID:     067b
PID:     2303
Driver:  pl2303
```

Die beiden Adapter besitzen keine individuelle USB-Seriennummer.

Die physische Zuordnung erfolgt deshalb über die USB-Porttopologie.

| Funktion | USB-Pfad | aktuelles Device | stabiler udev-Pfad | MEMMERT-Adresse |
|---|---|---|---|---:|
| IPP300 links | `1-1.4` | `/dev/ttyUSB1` | `/dev/memmert_ipp300_links` | `1` |
| IPP300 rechts | `1-1.5` | `/dev/ttyUSB2` | `/dev/memmert_ipp300_rechts` | `2` |

Die aktuelle praktische Verifikation ergab:

```text
IPP300 links:
    /dev/memmert_ipp300_links
    MEMMERT address 1
    Testwert: 14,1 °C

IPP300 rechts:
    /dev/memmert_ipp300_rechts
    MEMMERT address 2
    Testwert: 24,0 °C
```

Die verwendeten udev-Symlinks sind:

```text
/dev/memmert_ipp300_links
/dev/memmert_ipp300_rechts
```

Die beiden Adapter sollen für die bestehende Verdrahtung nicht
zwischen den definierten USB-Buchsen vertauscht werden.

Eine Änderung der physischen USB-Buchse würde die Zuordnung der
portbasierten udev-Namen verändern und muss anschließend erneut
dokumentiert bzw. angepasst werden.

Die vollständige Untersuchung ist unter
`docs/research/memmert-ipp300-linux-usb-identity.md` dokumentiert.

---

### 5.2 Freezer – stabile USB-Identität

Der vorhandene Freezer verwendet einen FTDI FT232R USB-UART-Adapter.

Der Adapter besitzt eine individuelle Seriennummer:

```text
A9NX8YRE
```

Der stabile Linux-Pfad lautet:

```text
/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9NX8YRE-if00-port0
```

Dieser Pfad basiert auf der USB-Geräteidentität einschließlich der
Seriennummer und ist daher nicht an eine bestimmte `ttyUSB`-Nummer
gebunden.

Das aktuelle dynamische Device `/dev/ttyUSB0` kann sich bei einer
anderen Enumeration ändern. Der `by-id`-Pfad bleibt dagegen für
diesen konkreten Adapter grundsätzlich identisch, solange der
Adapter selbst derselbe bleibt.

Für eine spätere Migration des Freezer-Readers sollte daher der
seriennummernbasierte `by-id`-Pfad bzw. ein darauf basierender udev-
Alias verwendet werden.

---

## 6. Legacy-Freezer-Logger

Der Legacy-Freezer-Logger schreibt nach:

    `/home/ZOOLOGY-observ/Programs/freezer.log`

Die serielle Quelle ist:

    `/dev/ttyUSB0`

Der Logger wird inzwischen über einen dedizierten `systemd --user`-Service gestartet:

    `freezer-log.service`

Service-Datei:

    `/home/ZOOLOGY-observ/.config/systemd/user/freezer-log.service`

In /docs/baseline/freezer-log.service findet sich zur Dokumentation eine Kopie der aktuell produktiv laufenden Service-Datei.

Der Service ist für den Benutzer `ZOOLOGY-observ` aktiviert und startet automatisch über:

    `default.target`

Der technische Runtime-Pfad lautet:

    systemd --user
          |
          v
    freezer-log.service
          |
          v
       script
          |
          v
      minicom
          |
          v
     /dev/ttyUSB0
          |
          v
     freezer.log

Für `minicom` wird `/usr/bin/script` verwendet, um eine virtuelle PTY-/Terminalumgebung bereitzustellen. Dadurch kann `minicom` als dauerhafter systemd User-Service betrieben werden, obwohl kein grafisches Terminalfenster geöffnet sein muss.

Die bisherige XDG-Autostart-Datei

    `/home/ZOOLOGY-observ/.config/autostart/TerminalAutostart.desktop`

wurde deaktiviert und ist nicht mehr der aktive Startmechanismus.

Die grafische Umgebung bleibt davon unabhängig erhalten. Sie wird weiterhin als lokaler Recovery- und Konfigurationsweg benötigt, ist aber für die kontinuierliche Freezer-Protokollierung nicht erforderlich.

Die Legacy-`observer.py` liest weiterhin den jeweils neuesten Freezer-Wert aus:

    `/home/ZOOLOGY-observ/Programs/freezer.log`

Damit bleibt folgende fachliche Abhängigkeit bestehen:

    serielles Gerät
          |
          v
      minicom
          |
          v
    freezer.log
          |
          v
    observer.py
          |
          v
    ThingSpeak

Der neue systemd-basierte Startmechanismus ändert nicht die fachliche Legacy-Datenquelle. Er macht deren Betrieb lediglich unabhängig von einer aktiven grafischen Terminal-Sitzung und stellt einen reproduzierbaren automatischen Start nach einem Reboot sicher.

Der Freezer-Logger bleibt bis zur ausdrücklichen Migration auf einen neuen Freezer-Adapter Bestandteil des Legacy-Datenpfades.

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
