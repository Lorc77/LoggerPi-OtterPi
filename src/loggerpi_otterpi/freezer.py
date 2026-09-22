"""Freezer-Reader für das LoggerPi-OtterPi-Datenmodell.

Liest die Freezer-Temperatur direkt von der seriellen Schnittstelle
des HFC-Serie Freezers (Thermo Scientific).

Der Freezer sendet selbstständig alle ~60 Minuten eine Meldung.
Dieser Reader hält die Seriell-Verbindung dauerhaft offen (ein offenes
FD, kein CPU-Verbrauch im Idle) und liest beim Aufruf alle seit dem
letzten Mal angekommenen Meldungen. Damit werden auch Alarmmeldungen
zwischen den Batch-Zyklen erkannt.

Datenformat (praktisch verifiziert 2026-09-22):

    NUL  -  Spc  8  2  Spc  C  Spc*11  LF  CR  EOT
    0x00 0x2d 0x20 0x38 0x32 0x20 0x43 0x20*11 0x0a 0x0d 0x04

    → -82 °C, keine Alarmmeldung

Laut Hersteller-Doku bei Alarm:

    T_ERR  →  Sensor-/Kontrollsondenfehler (kein numerischer Wert)
    UNDERTEMP, OVERTEMP, PWRFAIL, CNTRFAIL, Er07,
    HSHX FAIL, HOT COND  →  Alarmmeldung im Fehlerfeld

Zeitmodell:

    Der Freezer sendet KEINE Zeit in seiner Meldung.
    Daher wird `measured_at` auf den Empfangszeitpunkt auf dem
    LoggerPi (UTC) gesetzt.
    `received_at` ist ausschließlich OtterPi-seitig und wird
    hier nicht gesetzt.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import serial
from model.measurement import Measurement


class FreezerError(RuntimeError):
    """Fehler bei der Kommunikation mit einem Freezer-Gerät."""


@dataclass(frozen=True)
class FreezerReading:
    """Ein dekodierter Freezer-Datensatz.

    Enthält die Roh-Fakten aus dem Frame.
    Die `validity` wird erst beim Erzeugen eines `Measurement`
    bestimmt (siehe `_measurement_from_reading`).
    """

    temperature: Optional[float]  # None bei T_ERR
    has_temp_error: bool  # T_ERR statt numerischer Wert
    alarms: tuple[str, ...]  # fachliche Alarm-Codes (leer bei OK)
    measured_at: str  # Empfangszeit auf dem LoggerPi (UTC)


# Alarmcodes laut Hersteller-Doku
FREEZER_ALARMS = {
    "UNDERTEMP": "temperature_below_low_alarm",
    "OVERTEMP": "temperature_above_high_alarm",
    "PWRFAIL": "ac_power_failure",
    "CNTRFAIL": "control_probe_fault",
    "Er07": "microprocessor_fault",
    "HSHX FAIL": "heat_exchanger_fault",
    "HOT COND": "hot_condenser",
}


# Frame-Regex (verifiziert):
#   \x00                     → NUL (Frame-Start)
#   (-?\s?\d{2,3}|T_ERR)     → Temperatur oder T_ERR
#   (?: ?C ?)                → " C " (Einheit + Space)
#   ([A-Z_ ]*?)              → optionaler Alarmtext / Padding
#   (?:[\r\n]+\x04|\x04)     → LF/CR + EOT (Frame-Ende)
_FRAME_RE = re.compile(
    r"\x00"
    r"(-?\s?\d{2,3}|T_ERR)"
    r"(?: ?C ?)"
    r"([A-Z_ ]*?)"
    r"(?:[\r\n]+\x04|\x04)"
)


class FreezerReader:
    """Read-only reader for Thermo Scientific HFC-Serie Freezers.

    Die Seriell-Verbindung wird beim ersten Aufruf geöffnet und
    bleibt dauerhaft offen. Der Kernel puffert ankommende Bytes,
    sodass der Reader beim nächsten Aufruf alle seit dem letzten
    Mal angekommenen Meldungen verarbeiten kann.
    """

    def __init__(
        self,
        port: str,
        baudrate: int,
        stopbits: int,
        timeout: float,
        stale_after_seconds: float,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.stopbits = stopbits
        self.timeout = timeout
        self.stale_after_seconds = stale_after_seconds

        self._ser: Optional[serial.Serial] = None
        self._latest: Optional[FreezerReading] = None

    def read_measurements(self) -> dict[str, Measurement]:
        """Liefert die Freezer-Temperatur als Measurement.

        Der Schlüssel folgt dem Data Model: `freezer.temperature`.
        """
        self._ensure_open()
        self._drain_pending()

        measurement = self._measurement_from_latest()

        return {"freezer.temperature": measurement}

    def read_state(self) -> tuple[dict[str, object], dict[str, str]]:
        """Liefert den aktuellen Freezer-Gerätezustand.

        Analog zu `AtmoWebReader.read_state()`.

        Gibt ein Tupel (states, operation) zurück.
        Die `operation` ist beim Freezer immer leer (kein Betriebsmodus).
        """
        if self._latest is None:
            states: dict[str, object] = {
                "serial": {
                    "device": self.port,
                    "state": "disconnected",
                }
            }
        else:
            states = {
                "serial": {
                    "device": self.port,
                    "state": "connected",
                }
            }

        # Alarm-Zustände (falls vorhanden)
        if self._latest is not None and self._latest.alarms:
            states["alarms"] = list(self._latest.alarms)

        # Freezer hat keinen Betriebsmodus
        operation: dict[str, str] = {}

        return states, operation

    def close(self) -> None:
        """Schließt die Seriell-Verbindung."""
        if self._ser is not None and self._ser.is_open:
            self._ser.close()
        self._ser = None

    # ------------------------------------------------------------------
    # Interne Logik
    # ------------------------------------------------------------------

    def _ensure_open(self) -> None:
        """Öffnet die Verbindung beim ersten Aufruf (lazy)."""
        if self._ser is None:
            self._ser = self._open_serial()

    def _drain_pending(self) -> None:
        """Liest alle seit dem letzten Mal angekommenen Meldungen."""
        if self._ser is None:
            return

        try:
            if self._ser.in_waiting:
                data = self._ser.read(self._ser.in_waiting)

                for frame in _extract_frames(data):
                    reading = _parse_frame(frame)
                    if reading is not None:
                        self._latest = reading

        except (serial.SerialException, OSError, FreezerError):
            # Kommunikationsfehler → Verbindung beim nächsten Mal neu aufbauen
            self.close()

    def _open_serial(self) -> serial.Serial:
        """Öffnet die serielle Verbindung mit Freezer-Parametern."""
        return serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=self.stopbits,
            timeout=self.timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )

    def _is_stale(self) -> bool:
        """True, wenn der letzte Empfang zu lange her ist."""
        if self._latest is None:
            return True

        measured_at = datetime.fromisoformat(self._latest.measured_at)
        age_seconds = (datetime.now(timezone.utc) - measured_at).total_seconds()
        return age_seconds > self.stale_after_seconds

    def _measurement_from_latest(self) -> Measurement:
        """Erzeugt das Measurement aus dem letzten bekannten Reading."""
        if self._latest is None:
            return Measurement(
                value=None,
                unit="celsius",
                measured_at=None,
                validity="unavailable",
                source="freezer_serial",
            )

        reading = self._latest

        if reading.has_temp_error:
            # T_ERR → Sensorfehler, kein gültiger Wert
            return Measurement(
                value=None,
                unit="celsius",
                measured_at=reading.measured_at,
                validity="invalid",
                source="freezer_serial",
            )

        if reading.temperature is None:
            return Measurement(
                value=None,
                unit="celsius",
                measured_at=None,
                validity="unavailable",
                source="freezer_serial",
            )

        # valid oder stale
        validity = "stale" if self._is_stale() else "valid"

        return Measurement(
            value=reading.temperature,
            unit="celsius",
            measured_at=reading.measured_at,
            validity=validity,
            source="freezer_serial",
        )


# ---------------------------------------------------------------------------
# Modul-Level-Helper (analog zu atmoWEB)
# ---------------------------------------------------------------------------


def _extract_frames(data: bytes) -> list[bytes]:
    """Extrahiert einzelne Frames aus einem gelesenen Datenpuffer.

    Ein Frame beginnt mit NUL (\\x00) und endet mit EOT (\\x04).
    Mehrere Frames können in einem Puffer enthalten sein.
    """
    frames: list[bytes] = []
    start = None

    for i, byte in enumerate(data):
        if byte == 0x00 and start is None:
            start = i
        elif byte == 0x04 and start is not None:
            frames.append(data[start : i + 1])
            start = None

    return frames


def _parse_frame(raw: bytes) -> Optional[FreezerReading]:
    """Parst einen rohen Freezer-Frame (Modul-Level-Helper).

    setzt `measured_at` auf den aktuellen Empfangszeitpunkt (UTC),
    da der Freezer keine eigene Zeit in der Meldung sendet.
    """

    text = raw.decode("ascii", errors="replace")

    match = _FRAME_RE.search(text)
    if not match:
        raise FreezerError(f"Freezer-Frame konnte nicht geparst werden: {text!r}")

    temp_token = match.group(1)
    alarm_text = match.group(2)

    has_temp_error = temp_token == "T_ERR"

    temperature = None
    if not has_temp_error:
        # "- 82" → "-82" (Space zwischen Minus und Zahl entfernen)
        temperature = float(temp_token.replace(" ", ""))

    # Alarm-Texte in fachliche Codes übersetzen
    alarms = tuple(meaning for code, meaning in FREEZER_ALARMS.items() if code in alarm_text)

    # Empfangszeit auf dem LoggerPi (UTC)
    measured_at = datetime.now(timezone.utc).isoformat()

    return FreezerReading(
        temperature=temperature,
        has_temp_error=has_temp_error,
        alarms=alarms,
        measured_at=measured_at,
    )
