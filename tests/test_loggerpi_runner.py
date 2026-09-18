from unittest.mock import Mock, patch

import pytest

from loggerpi_otterpi.loggerpi_runner import LoggerPiRunner


def test_runner_rejects_non_positive_interval() -> None:
    runtime = Mock()

    with pytest.raises(ValueError, match="greater than zero"):
        LoggerPiRunner(runtime, interval_seconds=0)


def test_runner_does_not_run_when_stop_was_requested() -> None:
    runtime = Mock()
    runner = LoggerPiRunner(runtime, interval_seconds=60)

    def sleep_and_stop(_: float) -> None:
        runner.request_stop()

    with patch(
        "loggerpi_otterpi.loggerpi_runner.time.sleep",
        side_effect=sleep_and_stop,
    ) as sleep:
        runner.run()

    runtime.run_once.assert_called_once_with()
    sleep.assert_called_once()


def test_runner_continues_after_runtime_error() -> None:
    runtime = Mock()
    runtime.run_once.side_effect = [RuntimeError("test"), None]

    runner = LoggerPiRunner(runtime, interval_seconds=60)

    sleep_calls = 0

    def sleep_and_stop(_: float) -> None:
        nonlocal sleep_calls
        sleep_calls += 1

        if sleep_calls >= 2:
            runner.request_stop()

    with patch(
        "loggerpi_otterpi.loggerpi_runner.time.sleep",
        side_effect=sleep_and_stop,
    ):
        runner.run()

    assert runtime.run_once.call_count == 2


def test_runner_does_not_sleep_when_cycle_takes_longer_than_interval() -> None:
    runtime = Mock()
    runner = LoggerPiRunner(runtime, interval_seconds=60)

    monotonic_values = iter([0.0, 61.0])

    def monotonic() -> float:
        return next(monotonic_values)

    def run_once_and_stop() -> None:
        runner.request_stop()

    runtime.run_once.side_effect = run_once_and_stop

    with (
        patch(
            "loggerpi_otterpi.loggerpi_runner.time.monotonic",
            side_effect=monotonic,
        ),
        patch("loggerpi_otterpi.loggerpi_runner.time.sleep") as sleep,
    ):
        runner.run()

    runtime.run_once.assert_called_once_with()
    sleep.assert_not_called()
