"""Freezer-Konfiguration für das LoggerPi-OtterPi-Datenmodell.

Hält alle Geräte- und Kommunikationsparameter getrennt vom Reader –
analog zu atmoweb_config.py.
"""

from dataclasses import dataclass
from typing import Optional

from freezer import FreezerReader


@dataclass(frozen=True)
class FreezerEndpoint:
    """Konfiguration einer Freezer-Serielverbindung."""

    name: str
    port: str
    baudrate: int = 1200
    stopbits: int = 2
    timeout: float = 5.0
    stale_after_seconds: float = 90 * 60


# Stabile Seriell-Identität des vorhandenen Freezers
# (FTDI FT232R mit Seriennummer A9NX8YRE)
FREEZER_DEFAULT_PORT = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9NX8YRE-if00-port0"


def create_freezer_reader(
    name: str = "freezer",
    port: Optional[str] = None,
) -> FreezerReader:
    """Erzeugt den Freezer-Reader mit den Standard-Parametern."""
    endpoint = FreezerEndpoint(
        name=name,
        port=port if port is not None else FREEZER_DEFAULT_PORT,
    )

    return FreezerReader(
        port=endpoint.port,
        baudrate=endpoint.baudrate,
        stopbits=endpoint.stopbits,
        timeout=endpoint.timeout,
        stale_after_seconds=endpoint.stale_after_seconds,
    )
