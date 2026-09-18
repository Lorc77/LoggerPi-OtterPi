import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from model.measurement import Measurement


@dataclass(frozen=True)
class AtmoWebDevice:
    host: str
    port: int
    serial_number: str
    device_type: str
    software_revision: Optional[str] = None


class AtmoWebError(RuntimeError):
    """Fehler bei der Kommunikation mit einem AtmoWEB-Gerät."""


class AtmoWebReader:
    """Read-only reader for Memmert AtmoWEB devices."""

    def __init__(self, host: str, port: int = 80, timeout: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _request(self, *keys: str) -> dict[str, Any]:
        query = urlencode({key: "" for key in keys})
        request = Request(
            f"{self.base_url}/atmoweb?{query}",
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except Exception as exc:
            raise AtmoWebError(
                f"AtmoWEB-Gerät {self.host}:{self.port} konnte nicht erreicht werden."
            ) from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise AtmoWebError("AtmoWEB hat keine gültige JSON-Antwort geliefert.") from exc

        if not isinstance(data, dict):
            raise AtmoWebError("AtmoWEB-Antwort muss ein JSON-Objekt sein.")

        return data

    def identify(self) -> AtmoWebDevice:
        data = self._request("SN", "DevType", "SWRev")

        serial_number = data.get("SN")
        device_type = data.get("DevType")

        if not isinstance(serial_number, str) or not serial_number:
            raise AtmoWebError("AtmoWEB liefert keine gültige Seriennummer (SN).")

        if not isinstance(device_type, str) or not device_type:
            raise AtmoWebError("AtmoWEB liefert keinen gültigen Gerätetyp (DevType).")

        software_revision = data.get("SWRev")
        if not isinstance(software_revision, str):
            software_revision = None

        return AtmoWebDevice(
            host=self.host,
            port=self.port,
            serial_number=serial_number,
            device_type=device_type,
            software_revision=software_revision,
        )

    def read_measurements(self) -> dict[str, Measurement]:
        data = self._request(
            "Time",
            "Temp1Read",
            "Temp2Read",
            "Temp3Read",
            "Temp4Read",
            "HumRead",
            "VacRead",
            "CO2Read",
            "O2Read",
            "FanRead",
        )

        measured_at = _parse_timestamp(data.get("Time"))

        measurements: dict[str, Measurement] = {}

        for key, name, unit in (
            ("Temp1Read", "temperature_1", "celsius"),
            ("Temp2Read", "temperature_2", "celsius"),
            ("Temp3Read", "temperature_3", "celsius"),
            ("Temp4Read", "temperature_4", "celsius"),
            ("HumRead", "humidity", "percent"),
            ("VacRead", "vacuum", "mbar"),
            ("CO2Read", "co2", "ppm"),
            ("O2Read", "o2", "percent"),
            ("FanRead", "fan_speed", "rpm"),
        ):
            measurements[name] = _measurement_from_atmoweb(
                key=key,
                value=data.get(key),
                unit=unit,
                measured_at=measured_at,
            )

        return measurements

    def read_state(self) -> tuple[dict[str, object], dict[str, str]]:
        data = self._request(
            "DoorOpen",
            "DoorLock",
            "LightDay",
            "LightUV",
            "LightLED",
            "SwASet",
            "SwBSet",
            "SwCSet",
            "SwDSet",
            "FlapSet",
            "Defrost",
            "CurOp",
        )

        states: dict[str, object] = {}

        for key, name in (
            ("DoorOpen", "door_open"),
            ("DoorLock", "door_locked"),
            ("FlapSet", "flap"),
            ("Defrost", "defrost"),
        ):
            value = _optional_bool(data.get(key))
            if value is not None:
                states[name] = value

        lights: dict[str, bool] = {}
        for key, name in (
            ("LightDay", "day"),
            ("LightUV", "uv"),
            ("LightLED", "led"),
        ):
            value = _optional_bool(data.get(key))
            if value is not None:
                lights[name] = value

        if lights:
            states["lights"] = lights

        switches: dict[str, bool] = {}
        for key, name in (
            ("SwASet", "a"),
            ("SwBSet", "b"),
            ("SwCSet", "c"),
            ("SwDSet", "d"),
        ):
            value = _optional_bool(data.get(key))
            if value is not None:
                switches[name] = value

        if switches:
            states["switches"] = switches

        operation: dict[str, str] = {}
        mode = {
            "Program": "program",
            "Idle": "idle",
            "Timer": "timer",
            "Manual": "manual",
        }.get(data.get("CurOp"))

        if mode is not None:
            operation["mode"] = mode

        return states, operation


def _parse_timestamp(value: object) -> Optional[str]:
    if value is None:
        return None

    if not isinstance(value, str):
        raise AtmoWebError("AtmoWEB liefert für Time keinen String.")

    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise AtmoWebError(f"Ungültiger AtmoWEB-Zeitstempel: {value!r}") from exc

    if timestamp.tzinfo is None:
        raise AtmoWebError("AtmoWEB Time muss eine Zeitzoneninformation enthalten.")

    return timestamp.isoformat()


def _measurement_from_atmoweb(
    *,
    key: str,
    value: object,
    unit: str,
    measured_at: Optional[str],
) -> Measurement:
    if value == "N/A":
        return Measurement(
            value=None,
            unit=unit,
            measured_at=None,
            validity="unavailable",
            source="atmoweb",
        )

    if value == "N/D":
        return Measurement(
            value=None,
            unit=unit,
            measured_at=None,
            validity="unknown",
            source="atmoweb",
        )

    if value == "PermissionDenied":
        return Measurement(
            value=None,
            unit=unit,
            measured_at=None,
            validity="unavailable",
            source="atmoweb",
        )

    if value is None:
        return Measurement(
            value=None,
            unit=unit,
            measured_at=None,
            validity="unavailable",
            source="atmoweb",
        )

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AtmoWebError(f"AtmoWEB liefert für {key} einen nicht numerischen Wert: {value!r}")

    return Measurement(
        value=value,
        unit=unit,
        measured_at=measured_at,
        validity="valid",
        source="atmoweb",
    )


def _optional_bool(value: object) -> Optional[bool]:
    if value in {"N/A", "N/D", None, "PermissionDenied"}:
        return None

    if value == 0 or value == 0.0:
        return False

    if value == 1 or value == 1.0:
        return True

    raise AtmoWebError(f"Ungültiger AtmoWEB-State-Wert: {value!r}")
