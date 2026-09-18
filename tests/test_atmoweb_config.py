from atmoweb_config import (
    ATMOWEB_DEVICES,
    AtmoWebEndpoint,
    create_atmoweb_readers,
)


def test_atmoweb_devices_have_expected_addresses() -> None:
    assert ATMOWEB_DEVICES == (
        AtmoWebEndpoint(
            name="atmoweb_101",
            host="141.51.190.101",
        ),
        AtmoWebEndpoint(
            name="atmoweb_102",
            host="141.51.190.102",
        ),
    )


def test_create_atmoweb_readers() -> None:
    readers = create_atmoweb_readers()

    assert set(readers) == {"atmoweb_101", "atmoweb_102"}
    assert readers["atmoweb_101"].host == "141.51.190.101"
    assert readers["atmoweb_102"].host == "141.51.190.102"
