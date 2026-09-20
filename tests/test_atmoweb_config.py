from atmoweb_config import (
    create_atmoweb_readers,
)


def test_atmoweb_devices_have_expected_addresses(monkeypatch) -> None:
    monkeypatch.setenv("ATMOWEB_101_HOST", "141.51.190.101")
    monkeypatch.setenv("ATMOWEB_102_HOST", "141.51.190.102")

    readers = create_atmoweb_readers()

    assert set(readers) == {"atmoweb_101", "atmoweb_102"}
    assert readers["atmoweb_101"].host == "141.51.190.101"
    assert readers["atmoweb_102"].host == "141.51.190.102"


def test_create_atmoweb_readers(monkeypatch) -> None:
    monkeypatch.setenv("ATMOWEB_101_HOST", "141.51.190.101")
    monkeypatch.setenv("ATMOWEB_102_HOST", "141.51.190.102")

    readers = create_atmoweb_readers()

    assert set(readers) == {"atmoweb_101", "atmoweb_102"}
    assert readers["atmoweb_101"].host == "141.51.190.101"
    assert readers["atmoweb_102"].host == "141.51.190.102"
