"""MEMMERT-Reader für das LoggerPi-OtterPi-Datenmodell.

Liest Messwerte und Zustände von MEMMERT-Geräten über die
serielle Schnittstelle (MEMMERT-Protokoll nach NAMUR).

Protokoll (verifiziert 2026-09-04):
    - 2400 Baud, 8N1, keine Flow-Control
    - Request:  Befehl<CR><LF>
    - Response: OK<CR><LF>Wert<CR><LF>  (oder ERR_##)

Der Reader unterstützt alle dokumentierten IN_*-Befehle.
Die konkrete Auswahl der abzufragenden Befehle pro Gerät
erfolgt über die Konfiguration (memmert_config.py).

`measured_at` wird einheitlich auf die LoggerPi-Empfangszeit (UTC)
gesetzt (siehe DEC-032).
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import serial
from model.measurement import Measurement


class MemmertError(RuntimeError):
    """Fehler bei der Kommunikation mit einem MEMMERT-Gerät."""


# ---------------------------------------------------------------------------
# Alle möglichen Measurement-Befehle (offen für neue Geräte)
# ---------------------------------------------------------------------------

ALL_MEASUREMENT_COMMANDS = (
    ("IN_PV_{addr}1", "temperature", "celsius"),
    ("IN_PV_{addr}2", "co2", "ppm"),
    ("IN_PV_{addr}3", "humidity", "percent"),
    ("IN_PV_{addr}5", "temperature_2", "celsius"),
    ("IN_PV_{addr}A", "vacuum", "mbar"),
    ("IN_PV_{addr}B", "temperature_3", "celsius"),
    ("IN_PV_{addr}C", "temperature_4", "celsius"),
    ("IN_PV_{addr}D", "o2", "percent"),
)

# ---------------------------------------------------------------------------
# Alle möglichen State-Befehle
# ---------------------------------------------------------------------------

ALL_STATE_COMMANDS = (
    ("IN_MODE_{addr}0", "operation_mode"),
    ("IN_PAR_{addr}1", "resolution"),
    ("IN_PAR_{addr}4", "flap_control"),
    ("IN_PAR_{addr}5", "air_turbine"),
    ("IN_PAR_{addr}6", "switch_1"),
    ("IN_PAR_{addr}7", "switch_2"),
    ("IN_PAR_{addr}8", "switch_3"),
    ("IN_PAR_{addr}9", "temperature_2_present"),
    ("IN_PAR_{addr}A", "vacuum_present"),
)

# ---------------------------------------------------------------------------
# Alle möglichen Setpoint-Befehle (als States, keine Measurements)
# ---------------------------------------------------------------------------

ALL_SETPOINT_COMMANDS = (
    ("IN_SP_{addr}1", "temperature_setpoint"),
    ("IN_SP_{addr}2", "co2_setpoint"),
    ("IN_SP_{addr}3", "humidity_setpoint"),
    ("IN_SP_{addr}4", "flap_setpoint"),
    ("IN_SP_{addr}5", "air_turbine_setpoint"),
    ("IN_SP_{addr}A", "vacuum_setpoint"),
    ("IN_SP_{addr}D", "o2_setpoint"),
)

# ---------------------------------------------------------------------------
# Für das konkrete IPP300 relevante Befehle
# ---------------------------------------------------------------------------

IPP300_MEASUREMENT_COMMANDS = (("IN_PV_{addr}1", "temperature", "celsius"),)

IPP300_STATE_COMMANDS = (("IN_MODE_{addr}0", "operation_mode"),)

IPP300_SETPOINT_COMMANDS = (("IN_SP_{addr}1", "temperature"),)


@dataclass(frozen=True)
class MemmertDevice:
    """Identität eines MEMMERT-Geräts."""

    port: str
    address: str
    device_type: Optional[str] = None


class MemmertReader:
    """Read-only reader für MEMMERT-Geräte über serielle Schnittstelle."""

    def __init__(
        self,
        port: str,
        address: str,
        baudrate: int = 2400,
        timeout: float = 1.0,
        measurement_commands: tuple[tuple[str, str, str], ...] = IPP300_MEASUREMENT_COMMANDS,
        state_commands: tuple[tuple[str, str], ...] = IPP300_STATE_COMMANDS,
        setpoint_commands: tuple[tuple[str, str], ...] = IPP300_SETPOINT_COMMANDS,
    ) -> None:
        self.port = port
        self.address = address
        self.baudrate = baudrate
        self.timeout = timeout
        self.measurement_commands = measurement_commands
        self.state_commands = state_commands
        self.setpoint_commands = setpoint_commands

    def read_measurements(self) -> dict[str, Measurement]:
        """Liefert die Messwerte des MEMMERT-Geräts.

        `measured_at` = LoggerPi-Empfangszeit (UTC), einheitlich
        für alle Messwerte (siehe DEC-032).
        """
        measured_at = datetime.now(timezone.utc).isoformat()

        measurements: dict[str, Measurement] = {}

        try:
            with self._open_serial() as ser:
                for command_template, name, unit in self.measurement_commands:
                    command = command_template.format(addr=self.address)
                    value = _query_value(ser, command)

                    measurements[name] = Measurement(
                        value=value,
                        unit=unit,
                        measured_at=measured_at,
                        validity="valid" if value is not None else "unavailable",
                        source="memmert",
                    )
        except (serial.SerialException, OSError, MemmertError):
            # Kommunikationsfehler → alle Measurements als unavailable
            for _, name, unit in self.measurement_commands:
                measurements[name] = Measurement(
                    value=None,
                    unit=unit,
                    measured_at=None,
                    validity="unavailable",
                    source="memmert",
                )

        return measurements

    def read_state(self) -> tuple[dict[str, object], dict[str, str]]:
        """Liefert die Betriebsart als State."""
        states: dict[str, object] = {}
        operation: dict[str, str] = {}

        try:
            with self._open_serial() as ser:
                for command_template, name in self.state_commands:
                    command = command_template.format(addr=self.address)
                    value = _query_value(ser, command)
                    if value is not None:
                        states[name] = value
        except (serial.SerialException, OSError, MemmertError):
            pass

        return states, operation

    def read_setpoints(self) -> dict[str, float]:
        setpoints: dict[str, float] = {}
        try:
            with self._open_serial() as ser:
                for command_template, name in self.setpoint_commands:
                    command = command_template.format(addr=self.address)
                    value = _query_value(ser, command)
                    if value is not None:
                        setpoints[name] = value
        except (serial.SerialException, OSError, MemmertError):
            pass
        return setpoints

    def read_device_info(self) -> dict[str, object]:
        info: dict[str, object] = {
            "address": self.address,
            "port": self.port,
        }
        try:
            with self._open_serial() as ser:
                command = f"IN_PAR_{self.address}1"
                value = _query_value(ser, command)
                if value is not None:
                    info["resolution"] = value
        except (serial.SerialException, OSError, MemmertError):
            pass
        info.update(_usb_ids(self.port))
        return info

    def identify(self) -> MemmertDevice:
        """Liefert die Geräteidentität (port + adresse)."""
        return MemmertDevice(
            port=self.port,
            address=self.address,
        )

    def _open_serial(self) -> serial.Serial:
        """Öffnet die serielle Verbindung mit MEMMERT-Parametern."""
        return serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )


# ---------------------------------------------------------------------------
# Modul-Level-Helper
# ---------------------------------------------------------------------------


def _query_value(ser: serial.Serial, command: str) -> Optional[float]:
    """Sendet einen MEMMERT-Befehl und liest den Wert.

    Erwartet die Antwort:
        OK<CR><LF>
        <Wert><CR><LF>

    Bei ERR_## oder fehlender Antwort wird None zurückgegeben.
    """
    ser.reset_input_buffer()

    raw_command = (command + "\r\n").encode("ascii")
    ser.write(raw_command)
    ser.flush()

    # Kurz warten, bis die Antwort ankommt (MEMMERT antwortet ~122ms)
    time.sleep(0.2)

    response = ser.read_until(b"\n")

    if not response:
        return None

    # Weitere Zeilen einsammeln
    time.sleep(0.05)
    while ser.in_waiting:
        response += ser.read(ser.in_waiting)
        time.sleep(0.02)

    lines = _parse_response_lines(response)

    if not lines:
        return None

    if lines[0].startswith("ERR"):
        return None

    if lines[0] != "OK" or len(lines) < 2:
        return None

    # Wert parsen (Komma → Punkt für float)
    try:
        return float(lines[1].replace(",", "."))
    except ValueError:
        return None


def _parse_response_lines(raw: bytes) -> list[str]:
    """Konvertiert rohe Bytes in Protokoll-Zeilen."""
    if not raw:
        return []

    text = raw.decode("ascii", errors="replace")

    return [
        line.strip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.strip()
    ]


def _usb_ids(port: str) -> dict:
    try:
        tty_name = Path(port).resolve().name
    except OSError:
        return {}
    iface = Path("/sys/class/tty") / tty_name / "device"
    try:
        usb = iface.resolve().parent.parent
        return {
            "usb_vid": (usb / "idVendor").read_text().strip(),
            "usb_pid": (usb / "idProduct").read_text().strip(),
        }
    except OSError:
        return {}
