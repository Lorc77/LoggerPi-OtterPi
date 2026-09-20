"""Production runner for the LoggerPi runtime."""

import logging
import signal
import threading
import time
from types import FrameType
from typing import Optional

from runtime import LoggerRuntime

LOGGER = logging.getLogger(__name__)


class LoggerPiRunner:
    """Run LoggerRuntime cycles at a fixed interval."""

    def __init__(
        self,
        runtime: LoggerRuntime,
        interval_seconds: float = 60.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        self._runtime = runtime
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        """Request a graceful shutdown after the current cycle."""
        self._stop_event.set()

    def run(self) -> None:
        """Run runtime cycles until a stop is requested."""
        LOGGER.info(
            "LoggerPi runner started (interval=%ss)",
            self._interval_seconds,
        )

        while not self._stop_event.is_set():
            started = time.monotonic()

            try:
                self._runtime.run_once()
            except Exception:
                LOGGER.exception("LoggerRuntime cycle failed")

            elapsed = time.monotonic() - started
            delay = max(0.0, self._interval_seconds - elapsed)

            if delay > 0:
                # Blockiert ressourcenschonend bis zum Timeout ODER bis Stopp angefordert wird
                self._stop_event.wait(delay)

        LOGGER.info("LoggerPi runner stopped")


def _handle_signal(
    runner: LoggerPiRunner,
    signum: int,
    frame: Optional[FrameType],
) -> None:
    """Handle a termination signal."""
    del frame

    LOGGER.info("Received signal %s; requesting graceful shutdown", signum)
    runner.request_stop()


def run(
    runtime: LoggerRuntime,
    interval_seconds: float = 60.0,
) -> None:
    """Run a LoggerRuntime with process-level signal handling."""
    runner = LoggerPiRunner(
        runtime=runtime,
        interval_seconds=interval_seconds,
    )

    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: _handle_signal(runner, signum, frame),
    )
    signal.signal(
        signal.SIGINT,
        lambda signum, frame: _handle_signal(runner, signum, frame),
    )

    runner.run()
