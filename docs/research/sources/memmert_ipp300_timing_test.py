#!/usr/bin/env python3

"""
MEMMERT IPP300 – Read-only timing test

Fragt die Ist-Temperatur (IN_PV_11) mehrfach ab und misst:
- Zeit pro Request
- Antwortzeit
- Antwortinhalt
- Erfolgsquote

SICHERHEIT:
    Ausschließlich IN_PV_11.
    Kein OUT_*-Befehl.
    Kein REMOTE-Modus.
    Keine Änderung von Sollwerten oder Gerätezuständen.
"""

import time
from datetime import datetime

import serial

PORT = "/dev/ttyUSB1"
BAUDRATE = 2400
ADDRESS = "1"

TIMEOUT = 2.0
REQUESTS = 20
PAUSE_BETWEEN_REQUESTS = 1.0


def main():
    print()
    print("=" * 72)
    print("MEMMERT IPP300 – READ-ONLY TIMING TEST")
    print("=" * 72)
    print()
    print(f"Zeitpunkt : {datetime.now().isoformat(timespec='seconds')}")
    print(f"Port      : {PORT}")
    print(f"Adresse   : {ADDRESS}")
    print(f"Baudrate  : {BAUDRATE}")
    print("Format    : 8N1")
    print(f"Requests  : {REQUESTS}")
    print()

    command = f"IN_PV_{ADDRESS}1\r\n".encode("ascii")

    timings = []
    successful = 0

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

            for i in range(1, REQUESTS + 1):
                ser.reset_input_buffer()

                start = time.monotonic()

                ser.write(command)
                ser.flush()

                data = ser.read_until(b"\n")

                # MEMMERT antwortet normalerweise mit:
                # OK\r\n
                # wert\r\n
                #
                # Falls nach der ersten Zeile noch Daten warten,
                # kurz warten und diese ebenfalls einsammeln.
                time.sleep(0.05)

                while ser.in_waiting:
                    data += ser.read(ser.in_waiting)
                    time.sleep(0.01)

                elapsed = time.monotonic() - start
                elapsed_ms = elapsed * 1000

                timings.append(elapsed_ms)

                text = data.decode("ascii", errors="replace")
                lines = [
                    line.strip()
                    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
                    if line.strip()
                ]

                if lines and lines[0] == "OK":
                    successful += 1

                print(f"{i:02d}: {elapsed_ms:8.2f} ms   {data!r}")

                if i < REQUESTS:
                    time.sleep(PAUSE_BETWEEN_REQUESTS)

    except FileNotFoundError:
        print(f"FEHLER: Serielles Gerät nicht gefunden: {PORT}")
        return 1

    except PermissionError:
        print(f"FEHLER: Keine Berechtigung für {PORT}")
        return 1

    except serial.SerialException as exc:
        print("FEHLER bei der seriellen Kommunikation:")
        print(exc)
        return 1

    print()
    print("=" * 72)
    print("AUSWERTUNG")
    print("=" * 72)
    print()

    if not timings:
        print("Keine Messungen vorhanden.")
        return 1

    minimum = min(timings)
    maximum = max(timings)
    average = sum(timings) / len(timings)

    sorted_timings = sorted(timings)
    median = sorted_timings[len(sorted_timings) // 2]

    print(f"Erfolgreiche Antworten : {successful}/{REQUESTS}")
    print(f"Minimum                : {minimum:.2f} ms")
    print(f"Maximum                : {maximum:.2f} ms")
    print(f"Mittelwert             : {average:.2f} ms")
    print(f"Median                 : {median:.2f} ms")
    print()

    print("=" * 72)
    print("TEST ABGESCHLOSSEN")
    print("=" * 72)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
