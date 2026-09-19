"""Production process entry point for LoggerPi."""

import os

from atmoweb_config import create_atmoweb_readers
from batch_factory import SequenceStore
from batch_queue import BatchQueue
from delivery import BatchDelivery
from loggerpi_runner import run
from runtime import LoggerRuntime


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


def main() -> None:
    logger_id = _require_env("LOGGERPI_ID")
    otterpi_url = _require_env("OTTERPI_URL")
    queue_file = _require_env("LOGGERPI_QUEUE_FILE")
    sequence_file = _require_env("LOGGERPI_SEQUENCE_FILE")
    interval_seconds = _get_interval()

    runtime = LoggerRuntime(
        logger_id=logger_id,
        readers=create_atmoweb_readers(),
        sequence_store=SequenceStore(sequence_file),
        delivery=BatchDelivery(otterpi_url),
        queue=BatchQueue(queue_file),
    )

    run(
        runtime=runtime,
        interval_seconds=interval_seconds,
    )


if __name__ == "__main__":
    main()
