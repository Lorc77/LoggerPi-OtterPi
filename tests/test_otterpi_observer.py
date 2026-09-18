from unittest.mock import Mock, patch

import otterpi_observer
import pytest


def test_main_builds_store_and_starts_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OTTERPI_HOST", "127.0.0.1")
    monkeypatch.setenv("OTTERPI_PORT", "8080")
    monkeypatch.setenv("OTTERPI_DATABASE", "/tmp/otterpi.sqlite3")

    store = Mock()
    server = Mock()

    with (
        patch(
            "otterpi_observer.BatchStore",
            return_value=store,
        ) as batch_store,
        patch(
            "otterpi_observer.create_server",
            return_value=server,
        ) as create_server,
    ):
        otterpi_observer.main()

    batch_store.assert_called_once_with("/tmp/otterpi.sqlite3")
    create_server.assert_called_once_with("127.0.0.1", 8080, store)
    server.serve_forever.assert_called_once_with()


@pytest.mark.parametrize(
    "missing",
    [
        "OTTERPI_HOST",
        "OTTERPI_PORT",
        "OTTERPI_DATABASE",
    ],
)
def test_main_requires_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    monkeypatch.setenv("OTTERPI_HOST", "127.0.0.1")
    monkeypatch.setenv("OTTERPI_PORT", "8080")
    monkeypatch.setenv("OTTERPI_DATABASE", "/tmp/otterpi.sqlite3")
    monkeypatch.delenv(missing)

    with pytest.raises(
        RuntimeError,
        match=f"Required environment variable is missing: {missing}",
    ):
        otterpi_observer.main()
