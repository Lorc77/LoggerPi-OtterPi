"""Production entry point for the OtterPi HTTP server."""

import logging
import os

from .otterpi import create_server
from .otterpi_store import BatchStore

LOGGER = logging.getLogger(__name__)


def _required_environment(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")

    return value


def _int_environment(name: str) -> int:
    value = _required_environment(name)

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def main() -> None:
    """Start the OtterPi HTTP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    host = _required_environment("OTTERPI_HOST")
    port = _int_environment("OTTERPI_PORT")
    database = _required_environment("OTTERPI_DATABASE")

    store = BatchStore(database)
    server = create_server(host, port, store)

    LOGGER.info("OtterPi server starting on %s:%s", host, port)

    server.serve_forever()


if __name__ == "__main__":
    main()
