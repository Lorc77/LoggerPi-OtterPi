#!/usr/bin/env python3

"""
MEMMERT IPP300 – Complete Read-Only Communication Inventory

Purpose:
    Probe all documented MEMMERT IN_* read commands against all possible
    MEMMERT addresses on the specified serial ports.

Safety:
    This script ONLY sends documented IN_* read commands.
    It does NOT send any OUT_* command.
    It does NOT switch the device to REMOTE mode.
    It does NOT change setpoints or outputs.

Transport:
    2400 baud
    8 data bits
    no parity
    1 stop bit
    no hardware/software flow control

Address scan:
    0 ... F

The address scan uses IN_PV_{ADDR}1.

After finding a responding device, the complete documented
read-only command inventory is queried for that address.

This script is intentionally an INVENTORY tool.
It does not decide which values are useful for LoggerPi.
All responses are retained and displayed.
"""

import time
from datetime import datetime

import serial


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORTS = [
    "/dev/ttyUSB1",
    "/dev/ttyUSB2",
]

BAUDRATE = 2400
TIMEOUT = 1.0

ADDRESSES = "0123456789ABCDEF"

# Delay between requests.
REQUEST_DELAY = 0.2


# ---------------------------------------------------------------------------
# Complete documented IN_* inventory
#
# Address is inserted dynamically.
#
# Example for address 1:
#
#   IN_MODE_10
#   IN_PAR_11
#   IN_PV_11
#   IN_SP_11
#
# ---------------------------------------------------------------------------

COMMANDS = [

    # -----------------------------------------------------------------------
    # Operating mode
    # -----------------------------------------------------------------------

    ("IN_MODE_{addr}0", "Betriebsart"),

    # -----------------------------------------------------------------------
    # Configuration parameters
    # -----------------------------------------------------------------------

    ("IN_PAR_{addr}1", "Reglerauflösung"),
    ("IN_PAR_{addr}4", "Luftklappensteuerung"),
    ("IN_PAR_{addr}5", "Luftturbine"),
    ("IN_PAR_{addr}6", "Schaltkontakt 1"),
    ("IN_PAR_{addr}7", "Schaltkontakt 2"),
    ("IN_PAR_{addr}8", "Schaltkontakt 3"),
    ("IN_PAR_{addr}9", "2. Temperatur vorhanden"),
    ("IN_PAR_{addr}A", "Druck/Vakuum vorhanden"),

    # -----------------------------------------------------------------------
    # Actual values
    # -----------------------------------------------------------------------

    ("IN_PV_{addr}1", "Ist-Temperatur"),
    ("IN_PV_{addr}2", "CO2-Istwert"),
    ("IN_PV_{addr}3", "rh-Istwert"),
    ("IN_PV_{addr}5", "2. Ist-Temperatur"),
    ("IN_PV_{addr}A", "Druck/Vakuum-Istwert"),
    ("IN_PV_{addr}B", "3. Ist-Temperatur"),
    ("IN_PV_{addr}C", "4. Ist-Temperatur"),
    ("IN_PV_{addr}D", "O2-Istwert"),

    # -----------------------------------------------------------------------
    # Setpoints
    # -----------------------------------------------------------------------

    ("IN_SP_{addr}1", "Temperatur-Sollwert"),
    ("IN_SP_{addr}2", "CO2-Sollwert"),
    ("IN_SP_{addr}3", "rh-Sollwert"),
    ("IN_SP_{addr}4", "Luftklappen-Sollwert"),
    ("IN_SP_{addr}5", "Luftturbinen-Sollwert"),
    ("IN_SP_{addr}A", "Druck/Vakuum-Sollwert"),
    ("IN_SP_{addr}D", "O2-Sollwert"),
]


# ---------------------------------------------------------------------------
# Serial communication
# ---------------------------------------------------------------------------

def open_serial(port):
    """Open a MEMMERT serial connection."""

    return serial.Serial(
        port=port,
        baudrate=BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=TIMEOUT,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )


def send_command(ser, command):
    """
    Send one read-only command and collect the complete response.

    Typical successful response:

        OK\\r\\n
        14.7\\r\\n

    Typical error response:

        ERR_XX\\r\\n
    """

    ser.reset_input_buffer()

    raw_command = (command + "\r\n").encode("ascii")

    ser.write(raw_command)
    ser.flush()

    # Give the controller time to answer.
    time.sleep(0.2)

    response = ser.read_until(b"\n")

    if not response:
        return b""

    # Read additional response data already waiting.
    time.sleep(0.05)

    while ser.in_waiting:
        response += ser.read(ser.in_waiting)
        time.sleep(0.02)

    return response


def clean_response(raw):
    """Convert raw bytes into readable protocol lines."""

    if not raw:
        return []

    text = raw.decode("ascii", errors="replace")

    return [
        line.strip()
        for line in text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
        if line.strip()
    ]


# ---------------------------------------------------------------------------
# Human-readable interpretation
# ---------------------------------------------------------------------------

def interpret(command, lines):
    """
    Provide a human-readable interpretation while retaining the
    original response separately.
    """

    if not lines:
        return "KEINE ANTWORT"

    if lines[0].startswith("ERR"):
        return f"GERÄTEFEHLER: {lines[0]}"

    if command.startswith("IN_MODE_") and len(lines) >= 2:
        if lines[1] == "0":
            return "LOCAL / manueller Betrieb"

        if lines[1] == "1":
            return "REMOTE / Schnittstellenbetrieb"

    if command.startswith("IN_PAR_") and len(lines) >= 2:

        parameter_binary = {
            "4": "Luftklappensteuerung",
            "5": "Luftturbine",
            "6": "Schaltkontakt 1",
            "7": "Schaltkontakt 2",
            "8": "Schaltkontakt 3",
            "9": "2. Temperatur",
            "A": "Druck/Vakuum",
        }

        # IN_PAR_x1 is the resolution parameter.
        if command.endswith("1"):
            if lines[1] == "0":
                return "Auflösung 0,1 °C"

            if lines[1] == "1":
                return "Auflösung 1 °C"

        # Extract parameter identifier.
        #
        # Example:
        #   IN_PAR_14 -> "4"
        #   IN_PAR_1A -> "A"
        #
        if command.startswith("IN_PAR_1"):
            parameter = command[-1]

            if parameter in parameter_binary:
                name = parameter_binary[parameter]

                if lines[1] == "0":
                    return f"{name}: nicht vorhanden"

                if lines[1] == "1":
                    return f"{name}: vorhanden"

    if len(lines) >= 2:
        return lines[1]

    return lines[0]


# ---------------------------------------------------------------------------
# Address scan
# ---------------------------------------------------------------------------

def scan_addresses(port):
    """
    Test all possible MEMMERT addresses using IN_PV_{ADDR}1.

    Returns:
        list of dictionaries describing responding addresses.
    """

    found = []

    print()
    print("-" * 72)
    print(f"ADRESS-SCAN: {port}")
    print("-" * 72)

    try:
        with open_serial(port) as ser:

            print("Serielle Schnittstelle geöffnet.")
            print()

            for address in ADDRESSES:

                command = f"IN_PV_{address}1"

                print(
                    f"  Teste Adresse {address}: "
                    f"{command} ... ",
                    end="",
                    flush=True,
                )

                raw = send_command(ser, command)
                lines = clean_response(raw)

                if lines:
                    print(f"ANTWORT: {lines}")

                    found.append(
                        {
                            "address": address,
                            "command": command,
                            "raw": raw,
                            "lines": lines,
                        }
                    )
                else:
                    print("keine Antwort")

                time.sleep(REQUEST_DELAY)

    except FileNotFoundError:
        print(f"FEHLER: Serielles Gerät nicht gefunden: {port}")

    except PermissionError:
        print(f"FEHLER: Keine Berechtigung für {port}")

    except serial.SerialException as exc:
        print(f"FEHLER bei {port}: {exc}")

    print()

    if found:
        print(f"Gefundene MEMMERT-Adresse(n) auf {port}:")

        for device in found:

            lines = device["lines"]

            value = lines[1] if len(lines) >= 2 else "?"

            print(
                f"  Adresse {device['address']} "
                f"-> IN_PV = {value} °C"
            )

    else:
        print(f"Keine antwortenden MEMMERT-Geräte auf {port}.")

    return found


# ---------------------------------------------------------------------------
# Complete inventory for one device
# ---------------------------------------------------------------------------

def inventory_device(port, address):
    """
    Query every documented read-only IN_* command for one device.
    """

    print()
    print()
    print("=" * 72)
    print(
        f"VOLLSTÄNDIGE DETAILINVENTUR: "
        f"{port} / Adresse {address}"
    )
    print("=" * 72)
    print()

    results = []

    try:

        with open_serial(port) as ser:

            print("Serielle Schnittstelle geöffnet.")
            print()

            for template, description in COMMANDS:

                command = template.format(addr=address)

                print(f"  -> Sende: {command}")
                print(f"     Beschreibung: {description}")

                raw = send_command(ser, command)
                lines = clean_response(raw)
                interpretation = interpret(command, lines)

                if raw:
                    print(f"     Rohdaten    : {raw!r}")
                    print(
                        "     Rohdaten HEX: "
                        + " ".join(f"{b:02x}" for b in raw)
                    )
                else:
                    print("     Rohdaten    : <keine Antwort>")

                print(f"     Antwort     : {lines}")
                print(f"     Ergebnis    : {interpretation}")
                print()

                results.append(
                    {
                        "command": command,
                        "description": description,
                        "raw": raw,
                        "lines": lines,
                        "interpretation": interpretation,
                    }
                )

                time.sleep(REQUEST_DELAY)

    except FileNotFoundError:
        print(f"FEHLER: Serielles Gerät nicht gefunden: {port}")
        return []

    except PermissionError:
        print(f"FEHLER: Keine Berechtigung für {port}")
        return []

    except serial.SerialException as exc:
        print("FEHLER beim Öffnen/Benutzen der seriellen Schnittstelle:")
        print(exc)
        return []

    return results


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_device_summary(port, address, results):
    """Print a compact summary of all responses."""

    print()
    print("-" * 72)
    print(f"ZUSAMMENFASSUNG: {port} / Adresse {address}")
    print("-" * 72)
    print()

    for result in results:

        status = "OK" if result["lines"] else "NO RESPONSE"

        print(
            f"{status:12} "
            f"{result['command']:16} "
            f"{result['description']:<30} "
            f"=> {result['interpretation']}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    print()
    print("=" * 72)
    print("MEMMERT IPP300 – COMPLETE READ-ONLY INVENTUR")
    print("=" * 72)
    print()

    print(
        f"Zeitpunkt : "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )

    print(f"Ports     : {', '.join(PORTS)}")
    print(f"Baudrate  : {BAUDRATE}")
    print("Format    : 8N1")
    print("Flow Ctrl : none")
    print("Adressen  : 0 ... F")
    print()

    print("SICHERHEIT:")
    print("  Es werden ausschließlich IN_* Befehle gesendet.")
    print("  Keine OUT_* Befehle.")
    print("  Kein REMOTE.")
    print("  Keine Sollwertänderung.")
    print("  Keine Konfigurationsänderung.")
    print()

    # -----------------------------------------------------------------------
    # Phase 1: Find devices
    # -----------------------------------------------------------------------

    print("=" * 72)
    print("PHASE 1 – ADRESS-SCAN")
    print("=" * 72)

    devices = []

    for port in PORTS:

        found = scan_addresses(port)

        for device in found:

            devices.append(
                {
                    "port": port,
                    "address": device["address"],
                }
            )

    # -----------------------------------------------------------------------
    # Phase 2: Complete read-only inventory
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 2 – VOLLSTÄNDIGE IN_* INVENTUR")
    print("=" * 72)

    all_results = []

    if not devices:

        print()
        print("Keine MEMMERT-Geräte gefunden.")
        print()

    else:

        for device in devices:

            port = device["port"]
            address = device["address"]

            results = inventory_device(
                port,
                address,
            )

            all_results.append(
                {
                    "port": port,
                    "address": address,
                    "results": results,
                }
            )

            print_device_summary(
                port,
                address,
                results,
            )

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------

    print()
    print()
    print("=" * 72)
    print("GESAMTÜBERSICHT")
    print("=" * 72)
    print()

    if not all_results:

        print("Keine Geräte gefunden.")

    else:

        for device in all_results:

            print(
                f"{device['port']} / "
                f"MEMMERT-Adresse {device['address']}"
            )

            successful = 0
            errors = 0
            no_response = 0

            for result in device["results"]:

                lines = result["lines"]

                if not lines:
                    no_response += 1

                elif lines[0].startswith("ERR"):
                    errors += 1

                else:
                    successful += 1

            print(
                f"  Erfolgreiche Antworten : {successful}"
            )

            print(
                f"  ERR-Antworten           : {errors}"
            )

            print(
                f"  Keine Antwort           : {no_response}"
            )

            print()

    print("=" * 72)
    print("INVENTUR ABGESCHLOSSEN")
    print("=" * 72)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
