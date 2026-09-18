import json

import pytest
from atmoweb import AtmoWebError, AtmoWebReader


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self.body


def test_identify_reads_serial_number_and_device_type(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "SN": "S618.0005",
                "DevType": "VO101",
                "SWRev": "02.04.23",
            }
        )

    monkeypatch.setattr("atmoweb.urlopen", fake_urlopen)

    reader = AtmoWebReader("192.168.100.101")

    device = reader.identify()

    assert device.host == "192.168.100.101"
    assert device.port == 80
    assert device.serial_number == "S618.0005"
    assert device.device_type == "VO101"
    assert device.software_revision == "02.04.23"

    assert captured["url"] == ("http://192.168.100.101:80/atmoweb?SN=&DevType=&SWRev=")
    assert captured["timeout"] == 5.0


def test_read_measurements_maps_atmoweb_values(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "Time": "2026-08-30T18:00:00+00:00",
                "Temp1Read": 23.1,
                "Temp2Read": "N/A",
                "Temp3Read": "N/A",
                "Temp4Read": "N/A",
                "HumRead": 45.2,
                "VacRead": 966.9,
                "CO2Read": "N/A",
                "O2Read": "N/A",
                "FanRead": "N/A",
            }
        )

    monkeypatch.setattr("atmoweb.urlopen", fake_urlopen)

    measurements = AtmoWebReader("192.168.100.101").read_measurements()

    assert measurements["temperature_1"].to_dict() == {
        "value": 23.1,
        "unit": "celsius",
        "measured_at": "2026-08-30T18:00:00+00:00",
        "validity": "valid",
        "source": "atmoweb",
    }

    assert measurements["temperature_2"].to_dict() == {
        "value": None,
        "unit": "celsius",
        "measured_at": None,
        "validity": "unavailable",
        "source": "atmoweb",
    }

    assert measurements["humidity"].value == 45.2
    assert measurements["humidity"].unit == "percent"

    assert measurements["vacuum"].value == 966.9
    assert measurements["vacuum"].unit == "mbar"


def test_read_measurements_maps_nd_to_unknown(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "Time": "2026-08-30T18:00:00+00:00",
                "Temp1Read": "N/D",
                "Temp2Read": "N/A",
                "Temp3Read": "N/A",
                "Temp4Read": "N/A",
                "HumRead": "N/A",
                "VacRead": "N/A",
                "CO2Read": "N/A",
                "O2Read": "N/A",
                "FanRead": "N/A",
            }
        )

    monkeypatch.setattr("atmoweb.urlopen", fake_urlopen)

    measurement = AtmoWebReader("192.168.100.101").read_measurements()["temperature_1"]

    assert measurement.value is None
    assert measurement.validity == "unknown"


def test_read_state_maps_atmoweb_states(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "DoorOpen": 1,
                "DoorLock": 0,
                "LightDay": 1,
                "LightUV": 0,
                "LightLED": 1,
                "SwASet": 0,
                "SwBSet": 1,
                "SwCSet": 0,
                "SwDSet": 1,
                "FlapSet": 0,
                "Defrost": 0,
                "CurOp": "Manual",
            }
        )

    monkeypatch.setattr("atmoweb.urlopen", fake_urlopen)

    states, operation = AtmoWebReader("192.168.100.101").read_state()

    assert states == {
        "door_open": True,
        "door_locked": False,
        "lights": {
            "day": True,
            "uv": False,
            "led": True,
        },
        "switches": {
            "a": False,
            "b": True,
            "c": False,
            "d": True,
        },
        "flap": False,
        "defrost": False,
    }

    assert operation == {"mode": "manual"}


def test_invalid_json_raises_atmoweb_error(monkeypatch) -> None:
    class InvalidResponse(FakeResponse):
        def __init__(self):
            self.body = b"not json"

    monkeypatch.setattr(
        "atmoweb.urlopen",
        lambda request, timeout: InvalidResponse(),
    )

    with pytest.raises(AtmoWebError):
        AtmoWebReader("192.168.100.101").identify()
