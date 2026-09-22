"""ThingSpeak-Konfiguration für die semi-redundante Injektion."""

import os

from thingspeak_delivery import ThingSpeakDelivery


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def create_thingspeak_delivery() -> ThingSpeakDelivery:
    """Erzeugt die ThingSpeak-Injektion aus Umgebungsvariablen."""
    return ThingSpeakDelivery(
        api_key=_require_env("LOGGERPI_THINGSPEAK_API_KEY"),
        channel_id=_require_env("LOGGERPI_THINGSPEAK_CHANNEL_ID"),
    )
