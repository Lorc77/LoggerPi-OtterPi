"""Production process entry point for LoggerPi."""

import os
from typing import Set

from atmoweb_config import create_atmoweb_readers
from batch_factory import SequenceStore
from batch_queue import BatchQueue
from delivery import BatchDelivery
from freezer_config import create_freezer_reader
from loggerpi_runner import run
from memmert_config import create_memmert_readers
from runtime import LoggerRuntime
from thingspeak_config import create_thingspeak_delivery
from weatherhub import WeatherHubReader
from weatherhub_gateway_listener import WeatherHubGatewayListener


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def _get_interval() -> float:
    value = _require_env("LOGGERPI_INTERVAL_SECONDS")
    try:
        interval = float(value)
    except ValueError as exc:
        raise RuntimeError("LOGGERPI_INTERVAL_SECONDS must be a number") from exc

    if interval <= 0:
        raise RuntimeError("LOGGERPI_INTERVAL_SECONDS must be greater than zero")

    return interval


def _enabled(name: str, default: str = "1") -> bool:
    """Liest ein optionales Enable-Flag."""
    return os.environ.get(name, default) == "1"


def _create_weatherhub_listener() -> tuple[WeatherHubGatewayListener, WeatherHubReader]:
    """Erstellt den WeatherHub-Listener und den zugehörigen Reader."""
    host = _require_env("WEATHERHUB_LISTENER_HOST")
    port = int(_require_env("WEATHERHUB_LISTENER_PORT"))
    allowlist_raw = _require_env("WEATHERHUB_GATEWAY_ALLOWLIST")
    allowlist: Set[str] = {ip.strip() for ip in allowlist_raw.split(",") if ip.strip()}
    cloud_forward_enabled = _enabled("WEATHERHUB_CLOUD_FORWARD_ENABLED", "0")

    reader = WeatherHubReader()
    listener = WeatherHubGatewayListener(
        host=host,
        port=port,
        allowlist=allowlist,
        on_packets_received=reader.update_from_packets,
        cloud_forward_enabled=cloud_forward_enabled,
    )

    return listener, reader


def main() -> None:
    logger_id = _require_env("LOGGERPI_ID")
    otterpi_url = _require_env("OTTERPI_URL")
    token = _require_env("LOGGERPI_TOKEN")
    queue_file = _require_env("LOGGERPI_QUEUE_FILE")
    sequence_file = _require_env("LOGGERPI_SEQUENCE_FILE")
    interval_seconds = _get_interval()

    freezer_reader = create_freezer_reader() if _enabled("LOGGERPI_FREEZER_ENABLED", "1") else None

    memmert_readers = (
        create_memmert_readers() if _enabled("LOGGERPI_MEMMERT_ENABLED", "0") else None
    )

    thingspeak_delivery = (
        create_thingspeak_delivery() if _enabled("LOGGERPI_THINGSPEAK_ENABLED", "0") else None
    )

    # WeatherHub initialisieren
    weatherhub_listener = None
    weatherhub_reader = None
    if _enabled("LOGGERPI_WEATHERHUB_ENABLED", "0"):
        weatherhub_listener, weatherhub_reader = _create_weatherhub_listener()

    runtime = LoggerRuntime(
        logger_id=logger_id,
        readers=create_atmoweb_readers(),
        sequence_store=SequenceStore(sequence_file),
        delivery=BatchDelivery(otterpi_url, token=token),
        queue=BatchQueue(queue_file),
        freezer_reader=freezer_reader,
        memmert_readers=memmert_readers,
        thingspeak_delivery=thingspeak_delivery,
        weatherhub_listener=weatherhub_listener,
        weatherhub_reader=weatherhub_reader,
    )

    run(
        runtime=runtime,
        interval_seconds=interval_seconds,
    )


if __name__ == "__main__":
    main()
