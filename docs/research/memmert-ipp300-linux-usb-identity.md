# Research: MEMMERT IPP300 – Linux USB-Identität und Adapterzuordnung

## Status

**Stand:** 2026-09-08

**System:** LoggerPi / Raspberry Pi

**Geräte:**
- MEMMERT IPP300 links
- MEMMERT IPP300 rechts
- MEMMERT USB Interface B04118

**Zweck:**  
Ermittlung einer stabilen Linux-seitigen Identifikation der beiden
MEMMERT-USB-Verbindungen für den späteren LoggerPi-Dauerbetrieb.

---

## 1. Ausgangssituation

Die beiden vorhandenen MEMMERT IPP300 werden über das MEMMERT
USB Interface B04118 an den LoggerPi angeschlossen.

Das B04118 stellt die interne RS-232-Kommunikation des MEMMERT-Controllers
als USB-Seriell-Verbindung bereit.

Die MEMMERT-Protokollkommunikation wurde bereits separat in
`docs/research/memmert-ipp300.md` dokumentiert.

Diese Untersuchung betrifft ausschließlich die Identifikation der
USB-Seriell-Adapter unter Linux.

---

## 2. Tatsächliche Linux-Erkennung

Beide MEMMERT-Verbindungen werden unter Linux über einen Prolific
USB-Seriell-Controller erkannt.

Für beide Geräte wurden folgende USB-Eigenschaften festgestellt:

| Eigenschaft | Wert |
|---|---|
| Hersteller | Prolific Technology Inc. |
| VID | `067b` |
| PID | `2303` |
| Produkt | `USB-Serial Controller` |
| Kernel-Treiber | `pl2303` |
| USB-Geschwindigkeit | 12 Mbit/s |
| USB-Version | 1.10 |
| USB-Geräteklasse | `00` |
| Interface Class | `ff` |
| Interface Number | `00` |

Beide Adapter verwenden damit dieselbe USB-Hardwarekennung.

---

## 3. Keine individuelle USB-Seriennummer

Die normale udev-Eigenschaftsermittlung liefert für beide Adapter:

```text
ID_MODEL=USB-Serial_Controller
ID_MODEL_ID=2303
ID_SERIAL=Prolific_Technology_Inc._USB-Serial_Controller
ID_VENDOR=Prolific_Technology_Inc.
ID_VENDOR_ID=067b
```

Eine individuelle `ID_SERIAL_SHORT` ist nicht vorhanden.

Damit kann Linux die beiden Adapter nicht anhand einer
individuellen USB-Seriennummer unterscheiden.

Insbesondere darf nicht angenommen werden, dass

```text
067b:2303 + Prolific Technology Inc.
```

einen der beiden Adapter eindeutig identifiziert.

Diese Kennung ist bei beiden Geräten identisch.

---

## 4. Physische USB-Topologie

Die beiden Adapter unterscheiden sich jedoch eindeutig durch ihren
physischen USB-Anschluss am Raspberry Pi.

### Linker MEMMERT

Das Gerät `/dev/ttyUSB1` befindet sich an:

```text
USB device path: 1-1.4
```

Die relevante udev-Kette enthält:

```text
/devices/platform/soc/3f980000.usb/usb1/1-1/1-1.4/1-1.4:1.0/ttyUSB1
```

Damit ist der Adapter eindeutig dem USB-Port

```text
1-1.4
```

zugeordnet.

Die praktische MEMMERT-Inventur ergab für diesen Adapter:

```text
MEMMERT-Adresse: 1
Ist-Temperatur: 14,1 °C
```

Für die LoggerPi-Verdrahtungsdokumentation wird dieser Adapter daher
als

```text
memmert_ipp300_links
```

bezeichnet.

---

### Rechter MEMMERT

Das Gerät `/dev/ttyUSB2` befindet sich an:

```text
USB device path: 1-1.5
```

Die relevante udev-Kette enthält:

```text
/devices/platform/soc/3f980000.usb/usb1/1-1/1-1.5/1-1.5:1.0/ttyUSB2
```

Damit ist der Adapter eindeutig dem USB-Port

```text
1-1.5
```

zugeordnet.

Die praktische MEMMERT-Inventur ergab für diesen Adapter:

```text
MEMMERT-Adresse: 2
Ist-Temperatur: 24,0 °C
```

Für die LoggerPi-Verdrahtungsdokumentation wird dieser Adapter daher
als

```text
memmert_ipp300_rechts
```

bezeichnet.

---

## 5. Stabile udev-Namen

Auf dem LoggerPi wurden folgende udev-Regeln eingerichtet:

```text
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", KERNELS=="1-1.4", SYMLINK+="memmert_ipp300_links"
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", KERNELS=="1-1.5", SYMLINK+="memmert_ipp300_rechts"
```

Die resultierenden Gerätepfade sind:

```text
/dev/memmert_ipp300_links
/dev/memmert_ipp300_rechts
```

Aktueller Zustand:

```text
/dev/memmert_ipp300_links -> ttyUSB1
/dev/memmert_ipp300_rechts -> ttyUSB2
```

Die Zuordnung wurde zusätzlich mit `readlink -f` verifiziert:

```text
/dev/memmert_ipp300_links -> /dev/ttyUSB1
/dev/memmert_ipp300_rechts -> /dev/ttyUSB2
```

---

## 6. Bedeutung der Stabilität

Die Linux-Namen

```text
/dev/ttyUSB1
/dev/ttyUSB2
```

sind keine geeignete dauerhafte Geräteidentität.

Die Nummerierung von `ttyUSB*` kann sich durch Enumeration,
Anschlussreihenfolge oder Neustarts verändern.

Die verwendeten udev-Symlinks basieren dagegen auf dem physischen
USB-Gerätepfad:

```text
1-1.4
1-1.5
```

Dadurch kann die Zuordnung zu den beiden festen USB-Buchsen des
LoggerPi unabhängig von der jeweiligen `ttyUSB`-Nummer hergestellt
werden.

Wichtig:

Diese Identität ist **portstabil**, aber nicht **adapterstabil**.

Wenn die beiden Prolific-Adapter untereinander an andere USB-Buchsen
umgesteckt werden, ändert sich ihre USB-Topologie und damit die
Zuordnung.

Die physische Verdrahtung darf daher nicht ohne anschließende
Anpassung der udev-Zuordnung verändert werden.

---

## 7. Aktuelle endgültige Zuordnung

| Funktion | USB-Topologie | aktuelles Device | udev-Name | MEMMERT-Adresse | Testwert |
|---|---|---|---|---:|---:|
| IPP300 links | `1-1.4` | `/dev/ttyUSB1` | `/dev/memmert_ipp300_links` | `1` | 14,1 °C |
| IPP300 rechts | `1-1.5` | `/dev/ttyUSB2` | `/dev/memmert_ipp300_rechts` | `2` | 24,0 °C |

Die Bezeichnungen `links` und `rechts` sind dabei eine
betriebliche/physische Verdrahtungszuordnung und keine Eigenschaft,
die der MEMMERT-Controller selbst über das Protokoll meldet.

---

## 8. Abgrenzung zur Freezer-Schnittstelle

Der vorhandene Freezer verwendet einen separaten FTDI FT232R USB-UART.

Dieser Adapter besitzt eine individuelle Seriennummer:

```text
A9NX8YRE
```

und wird über folgenden persistenten Linux-Pfad identifiziert:

```text
/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9NX8YRE-if00-port0
```

Damit unterscheidet sich die Identifikationssituation:

```text
Freezer
    ↓
FTDI FT232R
    ↓
Seriennummer A9NX8YRE
    ↓
seriennummernbasierte Identifikation
```

gegenüber:

```text
MEMMERT links
    ↓
Prolific PL2303
    ↓
keine individuelle USB-Seriennummer
    ↓
physischer USB-Port 1-1.4
    ↓
udev-Symlink /dev/memmert_ipp300_links
```

und:

```text
MEMMERT rechts
    ↓
Prolific PL2303
    ↓
keine individuelle USB-Seriennummer
    ↓
physischer USB-Port 1-1.5
    ↓
udev-Symlink /dev/memmert_ipp300_rechts
```

---

## 9. Konsequenz für den späteren LoggerPi-Adapter

Der spätere LoggerPi-MemmertAdapter soll nicht von

```text
/dev/ttyUSB1
/dev/ttyUSB2
```

abhängen.

Stattdessen sollen die persistenten udev-Namen verwendet werden:

```text
/dev/memmert_ipp300_links
/dev/memmert_ipp300_rechts
```

Die MEMMERT-Adresse bleibt zusätzlich Bestandteil der
Gerätekonfiguration.

Empfohlene logische Zuordnung:

```text
memmert_ipp300_links
    port: /dev/memmert_ipp300_links
    address: 1

memmert_ipp300_rechts
    port: /dev/memmert_ipp300_rechts
    address: 2
```

Damit werden Transportidentität und MEMMERT-Protokolladresse
getrennt behandelt.

---

## 10. Sicherheitsstatus

Die Ermittlung der USB-Identität hat keinerlei Schreiboperation
gegen die MEMMERT-Geräte durchgeführt.

Die praktische Kommunikationsprüfung erfolgte ausschließlich mit
dokumentierten `IN_*`-Befehlen.

Es wurden insbesondere keine

```text
OUT_MODE_*
OUT_SP_*
```

Befehle ausgeführt.

Es wurde kein REMOTE-Modus aktiviert und kein Sollwert verändert.

---

## 11. Schlussfolgerung

Die beiden vorhandenen MEMMERT-USB-Verbindungen sind unter Linux
technisch eindeutig über ihre physische USB-Topologie unterscheidbar.

Eine individuelle Identifikation über USB-Seriennummer ist bei den
beiden vorhandenen Prolific-Adaptern nicht möglich, da beide dieselben
USB-Kennungen besitzen und keine individuelle Seriennummer melden.

Für den aktuellen LoggerPi wird daher folgende stabile
Host-seitige Identifikation verwendet:

```text
1-1.4 -> memmert_ipp300_links
1-1.5 -> memmert_ipp300_rechts
```

Diese Zuordnung ist für die bestehende feste Verdrahtung geeignet.

Die USB-Portzuordnung muss bei einem späteren physischen Umstecken der
Adapter erneut überprüft bzw. angepasst werden.
