# LoggerPi – System Inventory

## Purpose

This document records the currently observed runtime configuration of the
LoggerPi Raspberry Pi before further migration or cleanup work.

The inventory is intentionally descriptive. It does not imply that all
listed services or components are required.

This snapshot is intended to prevent loss of knowledge during the ongoing
migration from the legacy `observer.py` implementation toward the new
data model and service architecture.

---

## 1. System services

### Important application / access services

| Service | Enabled | Running | Notes |
|---|---:|---:|---|
| `meshagent.service` | yes | yes | Mesh remote-management agent |
| `ssh.service` | yes | yes | Primary remote shell access |
| `lightdm.service` | yes | yes | Local graphical login / LXDE environment |
| `teamviewerd.service` | no | no | Installed but currently inactive |
| `rsync.service` | yes | no | Enabled, but inactive because `/etc/rsyncd.conf` does not exist |
| `sshswitch.service` | yes | — | Enables SSH when `/boot/ssh` or `/boot/ssh.txt` exists |
| `rc-local.service` | yes | yes | `/etc/rc.local` compatibility service |

### Network-related services

| Service | Enabled | Running | Notes |
|---|---:|---:|---|
| `dhcpcd.service` | yes | yes | DHCP/network configuration |
| `networking.service` | yes | — | ifup/ifdown based networking |
| `wpa_supplicant.service` | yes | yes | Wi-Fi supplicant |
| `raspberrypi-net-mods.service` | yes | — | Copies `/boot/wpa_supplicant.conf` when present |
| `avahi-daemon.service` | yes | yes | mDNS / local service discovery |
| `ModemManager.service` | yes | yes | No modem currently detected |
| `bluetooth.service` | yes | yes | Bluetooth stack |

### Other notable enabled services

The system also has enabled services for:

- AppArmor
- Bluetooth / HCI UART
- CUPS / printer discovery
- cron
- console / keyboard setup
- fake hardware clock
- Raspberry Pi display backlight
- Raspberry Pi EEPROM update
- rsyslog
- systemd time synchronization
- triggerhappy
- udisks2

The full service inventory was captured directly from the running system on
2026-08-15.

---

## 2. Graphical environment

A complete graphical environment is intentionally kept installed and enabled.

Current display manager:

```text
lightdm.service
```

The purpose is operational recovery:

> A locally connected monitor and keyboard should remain available as a
> fallback configuration and recovery path if remote SSH / mesh access
> becomes unavailable.

The graphical environment must therefore **not be removed as part of the
current migration**.

### Current HDMI observation

At the time of the hardware check no monitor was connected.

DRM reports:

```text
card0-HDMI-A-1/status = disconnected
```

The Raspberry Pi therefore currently reports no connected HDMI display.

The following graphics configuration is present in `/boot/config.txt`:

```text
framebuffer_width=1280
framebuffer_height=720
dtparam=audio=on
camera_auto_detect=1
display_auto_detect=1
dtoverlay=vc4-kms-v3d
max_framebuffers=2
```

No active X11 display could be queried from the root shell because:

```text
xrandr --display :0
No protocol specified
Can't open display :0
```

This does **not** by itself indicate that Xorg/LXDE is not running. The
command was executed without the X session's authorization environment.

The HDMI configuration should be investigated separately when a physical
monitor is available.

---

## 3. Network interfaces

Current interfaces:

```text
lo       UNKNOWN   127.0.0.1/8
eth0     UP        141.51.190.103/24
wlan0    DOWN
```

Default route:

```text
default via 141.51.190.1 dev eth0
```

The system is therefore currently operating through wired Ethernet.

Wi-Fi is present but currently down.

---

## 4. Listening network services

Currently listening TCP ports:

```text
0.0.0.0:22       sshd
127.0.0.1:631     CUPS
[::]:22          sshd
[::1]:631         CUPS
```

The most important externally reachable TCP service is SSH on port 22.

No TCP listener for the meshagent was observed in this snapshot.

The meshagent does have a UDP socket:

```text
0.0.0.0:56448
```

---

## 5. USB and serial hardware

USB devices include:

```text
FTDI FT232 Serial (UART) IC
SMSC9512/9514 Fast Ethernet Adapter
SMSC9514 USB Hub
```

The FTDI device is exposed as:

```text
/dev/ttyUSB0
```

It is actively used by the legacy freezer logging setup.

Current process:

```text
minicom -C /home/ZOOLOGY-observ/Programs/freezer.log
```

PID at the time of inventory:

```text
1349
```

The device is therefore currently opened by:

```text
/dev/ttyUSB0 -> minicom -> freezer.log
```

This is an important legacy dependency and must not be removed or repurposed
without explicitly migrating the freezer serial data source.

---

## 6. Legacy freezer logger

The legacy freezer logger writes to:

```text
/home/ZOOLOGY-observ/Programs/freezer.log
```

Current file:

```text
-rw-r--r-- 1 ZOOLOGY-observ ZOOLOGY-observ ...
```

Recent values observed:

```text
- 80 C
- 80 C
- 82 C
- 82 C
```

The legacy `observer.py` reads the most recent freezer value from this file.

This establishes a direct dependency:

```text
serial device /dev/ttyUSB0
        |
        v
     minicom
        |
        v
freezer.log
        |
        v
legacy observer.py
        |
        v
ThingSpeak
```

This dependency should be preserved until the freezer data source has been
explicitly migrated into the new data model.

---

## 7. RSYNC

`rsync.service` is enabled but currently not running.

The reason is that:

```text
/etc/rsyncd.conf
```

does not exist.

The installed systemd unit is configured for rsync daemon mode.

This should not currently be interpreted as an active data-transfer service.

---

## 8. TeamViewer

A custom systemd unit exists:

```text
/etc/systemd/system/teamviewerd.service
```

It is currently:

```text
disabled
inactive (dead)
```

The unit starts:

```text
/opt/teamviewer/tv_bin/teamviewerd -d
```

No active TeamViewer process was observed.

The unit contains a legacy `/var/run/teamviewerd.pid` reference, which systemd
currently normalizes to the corresponding `/run/...` path.

TeamViewer should be considered an installed but inactive legacy/recovery
component until its role is explicitly decided.

---

## 9. Modem and Bluetooth

ModemManager is installed and running, but:

```text
mmcli -L
No modems were found
```

No Bluetooth devices were currently paired / listed.

Bluetooth itself is running and has an active HCI-related dependency.

Neither subsystem should be removed solely based on this snapshot; their
necessity should be evaluated separately.

---

## 10. Filesystems

The root filesystem is:

```text
/dev/mmcblk0p2 ext4 rw,noatime
```

The boot filesystem is:

```text
/dev/mmcblk0p1 vfat rw
```

The system is currently operating with a writable root filesystem.

---

## 11. Current architectural significance

The most important findings for the ongoing LoggerPi → OtterPi migration are:

1. `lightdm` and the graphical environment are intentionally retained as a
   local recovery mechanism.
2. SSH is enabled and currently running.
3. Ethernet is the active network path.
4. `/dev/ttyUSB0` is actively occupied by `minicom`.
5. `freezer.log` is still a live legacy data source.
6. The legacy `observer.py` depends on the freezer log and several external
   HTTP endpoints.
7. `rsync` is installed/enabled but not operational because its configuration
   file is absent.
8. TeamViewer is installed but inactive.
9. ModemManager and Bluetooth are active but currently have no observed
   application-level device usage.
10. No service should be disabled or removed solely on the basis of this
    inventory.

---

## 12. Migration rule

Before removing or disabling any legacy component, establish whether it is:

- still required by the current data acquisition path,
- required for local recovery,
- required by the new OtterPi architecture,
- merely installed but unused,
- or historical residue.

Changes should be made incrementally and documented in the repository.

The repository documentation is the authoritative record of architectural
decisions and discovered dependencies; the running Raspberry Pi is the
authoritative source for the current runtime state.
