"""Production entry point for the OtterPi HTTP server."""

import logging
import os

from alert_engine import AlertEngine
from alert_store import AlertStore
from otterpi import create_server
from otterpi_store import BatchStore

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
    token = _required_environment("OTTERPI_TOKEN")
    alert_db = os.environ.get("OTTERPI_ALERT_DB", "/var/lib/loggerpi-otterpi/alerts.sqlite3")
    alert_interval = int(os.environ.get("OTTERPI_ALERT_INTERVAL_SECONDS", "300"))
    smtp_password = os.environ.get("SMTP_PASSWORD")

    store = BatchStore(database)
    alert_store = AlertStore(alert_db)
    alert_engine = AlertEngine(
        store=store,
        alert_store=alert_store,
        smtp_password=smtp_password,
        interval_seconds=alert_interval,
    )
    alert_engine.start()

    server = create_server(
        host,
        port,
        store,
        token=token,
        alert_engine=alert_engine,
        alert_store=alert_store,
    )

    LOGGER.info("OtterPi server starting on %s:%s", host, port)

    try:
        server.serve_forever()
    finally:
        alert_engine.stop()
        alert_engine.join(timeout=5.0)


if __name__ == "__main__":
    main()
