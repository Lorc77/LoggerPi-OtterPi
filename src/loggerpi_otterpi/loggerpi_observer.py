"""Production process entry point for LoggerPi."""

import os

from atmoweb_config import create_atmoweb_readers
from batch_factory import SequenceStore
from batch_queue import BatchQueue
from delivery import BatchDelivery
from freezer_config import create_freezer_reader
from loggerpi_runner import run
from runtime import LoggerRuntime
from thingspeak_config import create_thingspeak_delivery


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
    """Liest ein optionales Enable-Flag.

    Freezer ist standardmäßig aktiviert (Default "1").
    ThingSpeak ist standardmäßig deaktiviert (Default "0").
    """
    return os.environ.get(name, default) == "1"


def main() -> None:
    logger_id = _require_env("LOGGERPI_ID")
    otterpi_url = _require_env("OTTERPI_URL")
    token = _require_env("LOGGERPI_TOKEN")
    queue_file = _require_env("LOGGERPI_QUEUE_FILE")
    sequence_file = _require_env("LOGGERPI_SEQUENCE_FILE")
    interval_seconds = _get_interval()

    freezer_reader = create_freezer_reader() if _enabled("LOGGERPI_FREEZER_ENABLED", "1") else None

    thingspeak_delivery = (
        create_thingspeak_delivery() if _enabled("LOGGERPI_THINGSPEAK_ENABLED", "0") else None
    )

    runtime = LoggerRuntime(
        logger_id=logger_id,
        readers=create_atmoweb_readers(),
        sequence_store=SequenceStore(sequence_file),
        delivery=BatchDelivery(otterpi_url, token=token),
        queue=BatchQueue(queue_file),
        freezer_reader=freezer_reader,
        thingspeak_delivery=thingspeak_delivery,
    )

    run(
        runtime=runtime,
        interval_seconds=interval_seconds,
    )


if __name__ == "__main__":
    main()
