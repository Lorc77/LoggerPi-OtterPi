"""MEMMERT-Konfiguration für das LoggerPi-OtterPi-Datenmodell.

Hält die Gerätekonfiguration getrennt vom Reader –
analog zu atmoweb_config.py.
"""

import os
from dataclasses import dataclass

from memmert import MemmertReader


@dataclass(frozen=True)
class MemmertEndpoint:
    """Konfiguration eines MEMMERT-Geräts."""

    name: str
    port: str
    address: str


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def create_memmert_readers() -> dict[str, MemmertReader]:
    """Erzeugt die MEMMERT-Reader aus Umgebungsvariablen.

    Erwartet pro Gerät:
        MEMMERT_<NAME>_PORT
        MEMMERT_<NAME>_ADDRESS
    """
    devices = (
        MemmertEndpoint(
            name="memmert_ipp300_links",
            port=_require_env("MEMMERT_IPP300_LINKS_PORT"),
            address=_require_env("MEMMERT_IPP300_LINKS_ADDRESS"),
        ),
        MemmertEndpoint(
            name="memmert_ipp300_rechts",
            port=_require_env("MEMMERT_IPP300_RECHTS_PORT"),
            address=_require_env("MEMMERT_IPP300_RECHTS_ADDRESS"),
        ),
    )

    return {
        device.name: MemmertReader(
            port=device.port,
            address=device.address,
        )
        for device in devices
    }
