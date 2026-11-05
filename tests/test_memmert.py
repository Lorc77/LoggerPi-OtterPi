"""Tests für den MEMMERT-Reader."""

import pytest
from memmert import (
    ALL_MEASUREMENT_COMMANDS,
    ALL_SETPOINT_COMMANDS,
    ALL_STATE_COMMANDS,
    IPP300_MEASUREMENT_COMMANDS,
    IPP300_SETPOINT_COMMANDS,
    IPP300_STATE_COMMANDS,
    MemmertReader,
    _parse_response_lines,
    _query_value,
)


@pytest.fixture
def reader():
    """MemmertReader ohne reale Hardware."""
    return MemmertReader(
        port="/dev/test/memmert",
        address="1",
    )


# ---------------------------------------------------------------------------
# _parse_response_lines
# ---------------------------------------------------------------------------


class TestParseResponseLines:
    """Testet das Parsen der MEMMERT-Antwort."""

    def test_normal_response(self):
        raw = b"OK\r\n14.7\r\n"

        lines = _parse_response_lines(raw)

        assert lines == ["OK", "14.7"]

    def test_error_response(self):
        raw = b"ERR_03\r\n"

        lines = _parse_response_lines(raw)

        assert lines == ["ERR_03"]

    def test_empty_response(self):
        assert _parse_response_lines(b"") == []

    def test_response_with_extra_lines(self):
        raw = b"OK\r\n14.7\r\n\r\n"

        lines = _parse_response_lines(raw)

        assert lines == ["OK", "14.7"]

    def test_comma_decimal(self):
        raw = b"OK\r\n14,7\r\n"

        lines = _parse_response_lines(raw)

        assert lines == ["OK", "14,7"]


# ---------------------------------------------------------------------------
# _query_value (mit gemockter Seriell-Schnittstelle)
# ---------------------------------------------------------------------------


class TestQueryValue:
    """Testet die Wert-Abfrage mit gemockter Seriell-Schnittstelle."""

    def test_valid_value(self):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\n14.7\r\n"

            def read(self, n):
                return b""

        value = _query_value(FakeSerial(), "IN_PV_11")

        assert value == 14.7

    def test_comma_value(self):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\n14,7\r\n"

            def read(self, n):
                return b""

        value = _query_value(FakeSerial(), "IN_PV_11")

        assert value == 14.7

    def test_error_response_returns_none(self):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"ERR_03\r\n"

            def read(self, n):
                return b""

        value = _query_value(FakeSerial(), "IN_PV_11")

        assert value is None

    def test_no_response_returns_none(self):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b""

            def read(self, n):
                return b""

        value = _query_value(FakeSerial(), "IN_PV_11")

        assert value is None

    def test_invalid_value_returns_none(self):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\nN/A\r\n"

            def read(self, n):
                return b""

        value = _query_value(FakeSerial(), "IN_PV_11")

        assert value is None


# ---------------------------------------------------------------------------
# read_measurements
# ---------------------------------------------------------------------------


class TestReadMeasurements:
    """Testet read_measurements mit gemockter Seriell-Schnittstelle."""

    def test_measurements_valid(self, reader, monkeypatch):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\n14.7\r\n"

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(
            reader,
            "_open_serial",
            lambda: FakeSerial(),
        )

        measurements = reader.read_measurements()

        assert "temperature" in measurements
        assert measurements["temperature"].value == 14.7
        assert measurements["temperature"].unit == "celsius"
        assert measurements["temperature"].validity == "valid"
        assert measurements["temperature"].source == "memmert"
        assert measurements["temperature"].measured_at.endswith("+00:00")

    def test_measurements_error_all_unavailable(self, reader, monkeypatch):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                raise OSError("Port nicht verfügbar")

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(
            reader,
            "_open_serial",
            lambda: FakeSerial(),
        )

        measurements = reader.read_measurements()

        assert "temperature" in measurements
        assert measurements["temperature"].value is None
        assert measurements["temperature"].validity == "unavailable"


# ---------------------------------------------------------------------------
# read_state
# ---------------------------------------------------------------------------


class TestReadState:
    """Testet read_state mit gemockter Seriell-Schnittstelle."""

    def test_state_values(self, reader, monkeypatch):
        responses = iter([b"OK\r\n0\r\n"])  # IN_MODE_10

        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return next(responses)

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(reader, "_open_serial", lambda: FakeSerial())

        states, operation = reader.read_state()

        assert states == {"operation_mode": 0}
        assert operation == {}

    def test_read_setpoints(self, reader, monkeypatch):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\n14.7\r\n"

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(reader, "_open_serial", lambda: FakeSerial())

        setpoints = reader.read_setpoints()

        assert setpoints == {"temperature": 14.7}

    def test_read_device_info(self, reader, monkeypatch):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                return b"OK\r\n0\r\n"

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(reader, "_open_serial", lambda: FakeSerial())
        monkeypatch.setattr(
            "memmert._usb_ids",
            lambda port: {"usb_vid": "067b", "usb_pid": "2303"},
        )

        info = reader.read_device_info()

        assert info["address"] == "1"
        assert info["port"] == "/dev/test/memmert"
        assert info["resolution"] == 0
        assert info["usb_vid"] == "067b"
        assert info["usb_pid"] == "2303"

    def test_state_error_returns_empty(self, reader, monkeypatch):
        class FakeSerial:
            def __init__(self):
                self.in_waiting = 0

            def reset_input_buffer(self):
                pass

            def write(self, data):
                pass

            def flush(self):
                pass

            def read_until(self, terminator):
                raise OSError("Port nicht verfügbar")

            def read(self, n):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(
            reader,
            "_open_serial",
            lambda: FakeSerial(),
        )

        states, operation = reader.read_state()

        assert states == {}
        assert operation == {}


# ---------------------------------------------------------------------------
# identify
# ---------------------------------------------------------------------------


class TestIdentify:
    """Testet die Geräteidentität."""

    def test_identify(self, reader):
        device = reader.identify()

        assert device.port == "/dev/test/memmert"
        assert device.address == "1"


# ---------------------------------------------------------------------------
# Befehlskonfiguration
# ---------------------------------------------------------------------------


class TestCommandConfiguration:
    """Prüft, dass die Befehlssätze korrekt definiert sind."""

    def test_ipp300_measurement_commands(self):
        assert IPP300_MEASUREMENT_COMMANDS == (("IN_PV_{addr}1", "temperature", "celsius"),)

    def test_ipp300_state_commands(self):
        assert IPP300_STATE_COMMANDS == (("IN_MODE_{addr}0", "operation_mode"),)

    def test_ipp300_setpoint_commands(self):
        assert IPP300_SETPOINT_COMMANDS == (("IN_SP_{addr}1", "temperature"),)

    def test_all_measurement_commands_complete(self):
        names = [name for _, name, _ in ALL_MEASUREMENT_COMMANDS]

        assert names == [
            "temperature",
            "co2",
            "humidity",
            "temperature_2",
            "vacuum",
            "temperature_3",
            "temperature_4",
            "o2",
        ]

    def test_all_state_commands_complete(self):
        names = [name for _, name in ALL_STATE_COMMANDS]

        assert names == [
            "operation_mode",
            "resolution",
            "flap_control",
            "air_turbine",
            "switch_1",
            "switch_2",
            "switch_3",
            "temperature_2_present",
            "vacuum_present",
        ]

    def test_all_setpoint_commands_complete(self):
        names = [name for _, name in ALL_SETPOINT_COMMANDS]

        assert names == [
            "temperature_setpoint",
            "co2_setpoint",
            "humidity_setpoint",
            "flap_setpoint",
            "air_turbine_setpoint",
            "vacuum_setpoint",
            "o2_setpoint",
        ]
