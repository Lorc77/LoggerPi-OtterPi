from dataclasses import dataclass

from atmoweb import AtmoWebReader


@dataclass(frozen=True)
class AtmoWebEndpoint:
    name: str
    host: str
    port: int = 80


ATMOWEB_DEVICES = (
    AtmoWebEndpoint(
        name="atmoweb_101",
        host="141.51.190.101",
    ),
    AtmoWebEndpoint(
        name="atmoweb_102",
        host="141.51.190.102",
    ),
)


def create_atmoweb_readers() -> dict[str, AtmoWebReader]:
    return {
        device.name: AtmoWebReader(
            host=device.host,
            port=device.port,
        )
        for device in ATMOWEB_DEVICES
    }
