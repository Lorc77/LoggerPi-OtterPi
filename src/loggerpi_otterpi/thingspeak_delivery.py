"""ThingSpeak-Injektion für semi-redundante Speicherung.

Sendet ausgewählte Werte aus dem Core Batch im Legacy-Format
an ThingSpeak (Bulk-Update).

Dieser Code ist bewusst als separat entfernbare Komponente gehalten.
Sobald ThingSpeak obsolet ist, kann diese Datei gelöscht werden –
ohne Änderungen am restlichen System.

Konformität:
    - Der Batch bleibt unverändert (keine ThingSpeak-Felder darin).
    - Die Injektion liest ausschließlich aus dem Batch.
    - API-Key/Channel-ID kommen aus der Umgebung (.env).
"""

import json
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from model.batch import Batch


class ThingSpeakDelivery:
    """Sendet Batch-Werte im Legacy-Format an ThingSpeak."""

    def __init__(
        self,
        api_key: str,
        channel_id: str,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.channel_id = channel_id
        self.timeout = timeout
        self._last_sent_at: Optional[float] = None

    @property
    def endpoint(self) -> str:
        return f"https://api.thingspeak.com/channels/{self.channel_id}/bulk_update.json"

    def send(self, batch: Batch) -> bool:
        """Sendet die relevanten Werte als einen ThingSpeak-Update.

        Verwendet `delta_t` aus der Zeit seit dem letzten Sendevorgang.
        """
        payload = _build_thingspeak_payload(
            batch=batch,
            api_key=self.api_key,
            delta_t=self._delta_t(),
        )

        if not payload["updates"]:
            return False

        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "User-Agent": "mw.doc.bulk-update (Raspberry Pi)",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                # ThingSpeak bulk_update liefert HTTP 202 bei Erfolg
                success = response.status == 202

                if success:
                    self._last_sent_at = time.monotonic()

                return success

        except (HTTPError, URLError):
            return False

    def _delta_t(self) -> int:
        """Relative Zeit seit dem letzten erfolgreichen Senden."""
        if self._last_sent_at is None:
            return 0

        return int(round(time.monotonic() - self._last_sent_at))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build_thingspeak_payload(
    *,
    batch: Batch,
    api_key: str,
    delta_t: int,
) -> dict:
    """Erzeugt das ThingSpeak-Bulk-Update-Payload aus dem Batch."""

    measurements = batch.measurements

    # Feldwerte aus dem Batch holen (String-Format wie im Legacy!)
    update = {
        "delta_t": delta_t,
        "field1": _measurement_value(measurements, "atmoweb_101.temperature_1"),
        "field2": _measurement_value(measurements, "atmoweb_101.humidity"),
        "field3": _measurement_value(measurements, "atmoweb_102.temperature_1"),
        "field4": _measurement_value(measurements, "atmoweb_102.humidity"),
        "field7": _freezer_value(measurements),
    }

    # System-Werte aus dem Batch
    system = batch.system or {}
    cpu = system.get("cpu", {})

    if isinstance(cpu, dict):
        if "temperature_celsius" in cpu and cpu["temperature_celsius"] is not None:
            update["field5"] = _format_number(cpu["temperature_celsius"])

        if "usage_percent" in cpu and cpu["usage_percent"] is not None:
            update["field6"] = _format_number(cpu["usage_percent"])

    # Nur Felder mit Wert aufnehmen (Legacy: alle Felder sind immer da,
    # aber bei fehlenden Werten senden wir nichts statt falscher Werte)
    update = {k: v for k, v in update.items() if v is not None}

    return {
        "write_api_key": api_key,
        "updates": [update],
    }


def _measurement_value(measurements: dict, key: str) -> Optional[str]:
    """Liest den Wert aus einem Measurement und formatiert ihn wie Legacy."""
    measurement = measurements.get(key)
    if measurement is None or measurement.value is None:
        return None

    return _format_number(measurement.value)


def _freezer_value(measurements: dict) -> Optional[int]:
    """Freezer-Wert: negativer Integer (Legacy: `-int(Freezer)`).
    Der neue Freezer-Reader liefert die Temperatur bereits negativ
    (z.B. -82.0), daher wird der Wert direkt übernommen."""

    measurement = measurements.get("freezer.temperature")
    if measurement is None or measurement.value is None:
        return None

    # Legacy: field7 = -int(Freezer)
    return int(round(measurement.value))


def _format_number(value: float) -> str:
    """Formatiert eine Zahl mit sinnvoller Genauigkeit (1 Nachkommastelle)."""
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"
