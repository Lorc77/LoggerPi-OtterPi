#!/usr/bin/env python3

"""
MEMMERT IPP300 – Read-only communication inventory

Purpose:
    Probe a MEMMERT IPP300 via the documented RS-232 protocol.

Safety:
    This script ONLY sends documented IN_* read commands.
    It does NOT send any OUT_* command.
    It does NOT switch the device to REMOTE mode.
    It does NOT change setpoints or outputs.

Tested transport:
    2400 baud
    8 data bits
    no parity
    1 stop bit
    no hardware/software flow control

Current device:
    /dev/ttyUSB1
    MEMMERT address: 1
"""

import time
from datetime import datetime

import serial

PORT = "/dev/ttyUSB1"
ADDRESS = "1"

BAUDRATE = 2400
TIMEOUT = 1.0

# Small pause between individual requests.
REQUEST_DELAY = 0.2


COMMANDS = [
    # Operating mode
    ("IN_MODE_10", "Betriebsart"),

    # Configuration parameters
    ("IN_PAR_11", "Reglerauflösung"),
    ("IN_PAR_14", "Luftklappensteuerung"),
    ("IN_PAR_15", "Luftturbine"),
    ("IN_PAR_16", "Schaltkontakt 1"),
    ("IN_PAR_17", "Schaltkontakt 2"),
    ("IN_PAR_18", "Schaltkontakt 3"),
    ("IN_PAR_19", "2. Temperatur vorhanden"),
    ("IN_PAR_1A", "Druck/Vakuum vorhanden"),

    # Actual values
    ("IN_PV_11", "Ist-Temperatur"),
    ("IN_PV_12", "CO2-Istwert"),
    ("IN_PV_13", "rh-Istwert"),
    ("IN_PV_15", "2. Ist-Temperatur"),
    ("IN_PV_1A", "Druck/Vakuum-Istwert"),
    ("IN_PV_1B", "3. Ist-Temperatur"),
    ("IN_PV_1C", "4. Ist-Temperatur"),
    ("IN_PV_1D", "O2-Istwert"),

    # Setpoints
    ("IN_SP_11", "Temperatur-Sollwert"),
    ("IN_SP_12", "CO2-Sollwert"),
    ("IN_SP_13", "rh-Sollwert"),
    ("IN_SP_14", "Luftklappen-Sollwert"),
    ("IN_SP_15", "Luftturbinen-Sollwert"),
    ("IN_SP_1A", "Druck/Vakuum-Sollwert"),
    ("IN_SP_1D", "O2-Sollwert"),
]


def send_command(ser, command):
    """
    Send one read-only command and collect the complete response.

    MEMMERT answers with lines such as:
        OK\\r\\n
        14.7\\r\\n

    or:
        ERR_XX\\r\\n
    """

    # Clear anything that might have arrived before this request.
    ser.reset_input_buffer()

    raw_command = (command + "\r\n").encode("ascii")

    print(f"  -> Sende: {command}")

    ser.write(raw_command)
    ser.flush()

    # Give the device time to respond.
    time.sleep(0.2)

    response = ser.read_until(b"\n")

    if not response:
        return b""

    # Usually the first line is OK / ERR.
    # Read additional lines that are already waiting.
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
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.strip()
    ]


def interpret(command, lines):
    """Provide a human-readable interpretation of known responses."""

    if not lines:
        return "Keine Antwort"

    if lines[0].startswith("ERR"):
        return f"Gerätefehler: {lines[0]}"

    if command == "IN_MODE_10" and len(lines) >= 2:
        if lines[1] == "0":
            return "LOCAL / manueller Betrieb"
        if lines[1] == "1":
            return "REMOTE / Schnittstellenbetrieb"

    if command == "IN_PAR_11" and len(lines) >= 2:
        if lines[1] == "0":
            return "Auflösung 0,1 °C"
        if lines[1] == "1":
            return "Auflösung 1 °C"

    parameter_binary = {
        "IN_PAR_14": ("Luftklappensteuerung", "nicht vorhanden", "vorhanden"),
        "IN_PAR_15": ("Luftturbine", "nicht vorhanden", "vorhanden"),
        "IN_PAR_16": ("Schaltkontakt 1", "nicht vorhanden", "vorhanden"),
        "IN_PAR_17": ("Schaltkontakt 2", "nicht vorhanden", "vorhanden"),
        "IN_PAR_18": ("Schaltkontakt 3", "nicht vorhanden", "vorhanden"),
        "IN_PAR_19": ("2. Temperatur", "nicht vorhanden", "vorhanden"),
        "IN_PAR_1A": ("Druck/Vakuum", "nicht vorhanden", "vorhanden"),
    }

    if command in parameter_binary and len(lines) >= 2:
        _, zero, one = parameter_binary[command]

        if lines[1] == "0":
            return zero

        if lines[1] == "1":
            return one

    if len(lines) >= 2:
        return lines[1]

    return lines[0]


def main():
    print()
    print("=" * 72)
    print("MEMMERT IPP300 – READ-ONLY INVENTUR")
    print("=" * 72)
    print()
    print(f"Zeitpunkt : {datetime.now().isoformat(timespec='seconds')}")
    print(f"Port      : {PORT}")
    print(f"Adresse   : {ADDRESS}")
    print(f"Baudrate  : {BAUDRATE}")
    print("Format    : 8N1")
    print("Flow Ctrl : none")
    print()
    print("SICHERHEIT: Es werden ausschließlich IN_* Befehle gesendet.")
    print("Keine OUT_* Befehle, kein REMOTE, keine Sollwertänderung.")
    print()

    results = []

    try:
        with serial.Serial(
            PORT,
            BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        ) as ser:

            print("Serielle Schnittstelle geöffnet.")
            print()

            for base_command, description in COMMANDS:

                # The address is already encoded into the command.
                command = base_command

                raw = send_command(ser, command)
                lines = clean_response(raw)
                interpretation = interpret(command, lines)

                print(f"     Beschreibung: {description}")

                if raw:
                    print(f"     Rohdaten    : {raw!r}")
                else:
                    print("     Rohdaten    : <keine Antwort>")

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
        print(f"FEHLER: Serielles Gerät nicht gefunden: {PORT}")
        return 1

    except PermissionError:
        print(f"FEHLER: Keine Berechtigung für {PORT}")
        return 1

    except serial.SerialException as exc:
        print("FEHLER beim Öffnen/Benutzen der seriellen Schnittstelle:")
        print(exc)
        return 1

    print("=" * 72)
    print("ZUSAMMENFASSUNG")
    print("=" * 72)
    print()

    for result in results:
        print(
            f"{result['command']:12} "
            f"{result['description']:<28} "
            f"=> {result['interpretation']}"
        )

    print()
    print("=" * 72)
    print("INVENTUR ABGESCHLOSSEN")
    print("=" * 72)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
