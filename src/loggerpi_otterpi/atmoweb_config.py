import os
from dataclasses import dataclass

from atmoweb import AtmoWebReader


@dataclass(frozen=True)
class AtmoWebEndpoint:
    name: str
    host: str
    port: int = 80


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def create_atmoweb_readers() -> dict[str, AtmoWebReader]:
    devices = (
        AtmoWebEndpoint(
            name="atmoweb_101",
            host=_require_env("ATMOWEB_101_HOST"),
        ),
        AtmoWebEndpoint(
            name="atmoweb_102",
            host=_require_env("ATMOWEB_102_HOST"),
        ),
    )
    return {device.name: AtmoWebReader(host=device.host, port=device.port) for device in devices}
