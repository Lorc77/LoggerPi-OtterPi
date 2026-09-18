from unittest.mock import Mock, patch

import pytest

from loggerpi_otterpi import loggerpi_observer


def test_main_builds_runtime_and_starts_runner(monkeypatch) -> None:
    monkeypatch.setenv("LOGGERPI_ID", "loggerpi-test")
    monkeypatch.setenv("OTTERPI_URL", "http://otterpi:8080/api/v1/batches")
    monkeypatch.setenv("LOGGERPI_INTERVAL_SECONDS", "30")
    monkeypatch.setenv("LOGGERPI_QUEUE_FILE", "/tmp/loggerpi/queue.jsonl")
    monkeypatch.setenv("LOGGERPI_SEQUENCE_FILE", "/tmp/loggerpi/sequence")

    readers = {"atmoweb_101": Mock()}

    with (
        patch(
            "loggerpi_otterpi.loggerpi_observer.create_atmoweb_readers",
            return_value=readers,
        ),
        patch("loggerpi_otterpi.loggerpi_observer.run") as run,
    ):
        loggerpi_observer.main()

    run.assert_called_once()

    runtime = run.call_args.kwargs["runtime"]

    assert runtime.logger_id == "loggerpi-test"
    assert runtime.readers is readers
    assert runtime.delivery.endpoint == ("http://otterpi:8080/api/v1/batches")
    assert runtime.queue.path.as_posix() == "/tmp/loggerpi/queue.jsonl"
    assert runtime.sequence_store.path.as_posix() == "/tmp/loggerpi/sequence"
    assert run.call_args.kwargs["interval_seconds"] == 30.0


@pytest.mark.parametrize(
    "variable",
    [
        "LOGGERPI_ID",
        "OTTERPI_URL",
        "LOGGERPI_INTERVAL_SECONDS",
        "LOGGERPI_QUEUE_FILE",
        "LOGGERPI_SEQUENCE_FILE",
    ],
)
def test_main_requires_environment_variable(monkeypatch, variable: str) -> None:
    values = {
        "LOGGERPI_ID": "loggerpi-test",
        "OTTERPI_URL": "http://otterpi:8080/api/v1/batches",
        "LOGGERPI_INTERVAL_SECONDS": "30",
        "LOGGERPI_QUEUE_FILE": "/tmp/loggerpi/queue.jsonl",
        "LOGGERPI_SEQUENCE_FILE": "/tmp/loggerpi/sequence",
    }

    for name, value in values.items():
        monkeypatch.setenv(name, value)

    monkeypatch.delenv(variable)

    with pytest.raises(
        RuntimeError,
        match="Required environment variable",
    ):
        loggerpi_observer.main()


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_main_rejects_invalid_interval(monkeypatch, value: str) -> None:
    monkeypatch.setenv("LOGGERPI_ID", "loggerpi-test")
    monkeypatch.setenv("OTTERPI_URL", "http://otterpi:8080/api/v1/batches")
    monkeypatch.setenv("LOGGERPI_INTERVAL_SECONDS", value)
    monkeypatch.setenv("LOGGERPI_QUEUE_FILE", "/tmp/loggerpi/queue.jsonl")
    monkeypatch.setenv("LOGGERPI_SEQUENCE_FILE", "/tmp/loggerpi/sequence")

    with pytest.raises(RuntimeError):
        loggerpi_observer.main()
