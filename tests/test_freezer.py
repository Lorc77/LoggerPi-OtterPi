"""Tests für den Freezer-Reader.

Deckt ab:
- Frame-Parsing (normal, T_ERR, Alarme)
- read_measurements (unavailable, valid, stale, invalid)
- read_state (connected/disconnected, Alarme)
- Alarm-Mapping vollständig
- close() bei Fehlern
"""

from datetime import datetime, timezone

import pytest
from freezer import (
    FREEZER_ALARMS,
    FreezerError,
    FreezerReader,
    FreezerReading,
    _extract_frames,
    _parse_frame,
)

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def reader():
    """FreezerReader ohne reale Hardware (Timeout minimiert)."""
    return FreezerReader(
        port="/dev/test/freezer",
        baudrate=1200,
        stopbits=2,
        timeout=0.1,
        stale_after_seconds=90 * 60,
    )


# ---------------------------------------------------------------------------
# _extract_frames
# ---------------------------------------------------------------------------


class TestExtractFrames:
    """Extraktion einzelner Frames aus einem Puffer."""

    def test_single_frame(self):
        data = b"\x00- 82 C               \n\r\x04"

        frames = _extract_frames(data)

        assert len(frames) == 1
        assert frames[0] == data

    def test_multiple_frames(self):
        frame1 = b"\x00- 82 C               \n\r\x04"
        frame2 = b"\x00- 79 C               \n\r\x04"

        data = frame1 + frame2

        frames = _extract_frames(data)

        assert len(frames) == 2
        assert frames[0] == frame1
        assert frames[1] == frame2

    def test_empty_data(self):
        assert _extract_frames(b"") == []

    def test_incomplete_frame_no_eot(self):
        data = b"\x00- 82 C               \n"
        frames = _extract_frames(data)
        assert frames == []


# ---------------------------------------------------------------------------
# _parse_frame – normale Temperatur
# ---------------------------------------------------------------------------


class TestParseFrameNormal:
    """Parsen eines normalen Frames."""

    def test_negative_temperature(self):
        raw = b"\x00- 82 C               \n\r\x04"

        reading = _parse_frame(raw)

        assert reading.temperature == -82.0
        assert reading.has_temp_error is False
        assert reading.alarms == ()
        assert reading.measured_at.endswith("+00:00")

    def test_positive_temperature(self):
        raw = b"\x00 25 C               \n\r\x04"

        reading = _parse_frame(raw)

        assert reading.temperature == 25.0
        assert reading.alarms == ()

    def test_three_digit_temperature(self):
        raw = b"\x00- 108 C             \n\r\x04"

        reading = _parse_frame(raw)

        assert reading.temperature == -108.0
        assert reading.alarms == ()


# ---------------------------------------------------------------------------
# _parse_frame – Fehler-/Alarmfälle
# ---------------------------------------------------------------------------


class TestParseFrameErrors:
    """Parsen von Frames mit T_ERR oder Alarmmeldungen."""

    def test_temp_err_control_probe_fault(self):
        raw = b"\x00T_ERR C CNTRFAIL     \n\r\x04"

        reading = _parse_frame(raw)

        assert reading.temperature is None
        assert reading.has_temp_error is True
        assert "control_probe_fault" in reading.alarms

    def test_undertemp_alarm(self):
        raw = b"\x00- 82 C UNDERTEMP     \n\r\x04"

        reading = _parse_frame(raw)

        assert reading.temperature == -82.0
        assert "temperature_below_low_alarm" in reading.alarms

    def test_ovetemp_alarm(self):
        raw = b"\x00- 82 C OVERTEMP      \n\r\x04"

        reading = _parse_frame(raw)

        assert "temperature_above_high_alarm" in reading.alarms

    def test_multiple_alarms(self):
        raw = b"\x00- 82 C PWRFAIL CNTRFAIL\n\r\x04"

        reading = _parse_frame(raw)

        assert "ac_power_failure" in reading.alarms
        assert "control_probe_fault" in reading.alarms

    def test_invalid_frame_raises(self):
        raw = b"\x00GARBAGE\n\r\x04"

        with pytest.raises(FreezerError):
            _parse_frame(raw)


# ---------------------------------------------------------------------------
# read_measurements
# ---------------------------------------------------------------------------


class TestReadMeasurements:
    """Testet read_measurements mit gemockter Seriell-Schnittstelle."""

    def _mock_reader(self, reader, monkeypatch):
        """Mockt die Serial-Öffnung, sodass keine echte Hardware nötig ist."""
        monkeypatch.setattr(
            reader,
            "_ensure_open",
            lambda: None,
        )
        monkeypatch.setattr(
            reader,
            "_drain_pending",
            lambda: None,
        )

    def test_no_data_yet(self, reader, monkeypatch):
        self._mock_reader(reader, monkeypatch)

        measurements = reader.read_measurements()

        assert "freezer.temperature" in measurements
        measurement = measurements["freezer.temperature"]

        assert measurement.value is None
        assert measurement.validity == "unavailable"
        assert measurement.source == "freezer_serial"

    def test_valid_temperature(self, reader, monkeypatch):
        self._mock_reader(reader, monkeypatch)

        reader._latest = FreezerReading(
            temperature=-82.0,
            has_temp_error=False,
            alarms=(),
            measured_at=datetime.now(timezone.utc).isoformat(),
        )

        measurements = reader.read_measurements()

        measurement = measurements["freezer.temperature"]

        assert measurement.value == -82.0
        assert measurement.unit == "celsius"
        assert measurement.validity == "valid"

    def test_stale_temperature(self, reader, monkeypatch):
        self._mock_reader(reader, monkeypatch)

        from datetime import timedelta

        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        reader._latest = FreezerReading(
            temperature=-82.0,
            has_temp_error=False,
            alarms=(),
            measured_at=old_time.isoformat(),
        )

        measurements = reader.read_measurements()

        measurement = measurements["freezer.temperature"]

        assert measurement.value == -82.0
        assert measurement.validity == "stale"

    def test_temp_error_invalid(self, reader, monkeypatch):
        self._mock_reader(reader, monkeypatch)

        reader._latest = FreezerReading(
            temperature=None,
            has_temp_error=True,
            alarms=("control_probe_fault",),
            measured_at=datetime.now(timezone.utc).isoformat(),
        )

        measurements = reader.read_measurements()

        measurement = measurements["freezer.temperature"]

        assert measurement.value is None
        assert measurement.validity == "invalid"


# ---------------------------------------------------------------------------
# read_state
# ---------------------------------------------------------------------------


class TestReadState:
    """Testet read_state und die serial-Property."""

    def test_state_no_data(self, reader, monkeypatch):
        monkeypatch.setattr(reader, "_serial_present", lambda: False)
        reader._latest = None

        states, operation = reader.read_state()

        assert states == {}
        assert operation == {}
        assert reader.serial == {"device": "/dev/test/freezer", "state": "disconnected"}

    def test_state_connected_no_alarm(self, reader, monkeypatch):
        monkeypatch.setattr(reader, "_serial_present", lambda: True)
        reader._latest = FreezerReading(
            temperature=-82.0,
            has_temp_error=False,
            alarms=(),
            measured_at=datetime.now(timezone.utc).isoformat(),
        )

        states, operation = reader.read_state()

        assert states == {}
        assert operation == {}
        assert reader.serial["state"] == "connected"

    def test_state_with_alarm(self, reader, monkeypatch):
        monkeypatch.setattr(reader, "_serial_present", lambda: True)
        reader._latest = FreezerReading(
            temperature=None,
            has_temp_error=True,
            alarms=("ac_power_failure",),
            measured_at=datetime.now(timezone.utc).isoformat(),
        )

        states, operation = reader.read_state()

        assert states == {"alarms": ["ac_power_failure"]}
        assert operation == {}
        assert reader.serial["state"] == "connected"

    def test_state_unknown(self, reader, monkeypatch):
        monkeypatch.setattr(reader, "_serial_present", lambda: True)
        reader._latest = None

        assert reader.serial["state"] == "unknown"

    def test_state_degraded(self, reader, monkeypatch):
        from datetime import timedelta

        monkeypatch.setattr(reader, "_serial_present", lambda: True)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        reader._latest = FreezerReading(
            temperature=-82.0,
            has_temp_error=False,
            alarms=(),
            measured_at=old_time.isoformat(),
        )

        assert reader.serial["state"] == "degraded"


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    """Testet das Schließen der Verbindung."""

    def test_close_without_open(self, reader):
        # Kein Fehler, wenn nie geöffnet wurde
        reader.close()
        assert reader._ser is None

    def test_close_after_open(self, reader):
        # Simuliere geöffnete Verbindung

        class FakeSerial:
            is_open = True

            def close(self):
                self.is_open = False

        reader._ser = FakeSerial()
        reader.close()

        assert reader._ser is None


# ---------------------------------------------------------------------------
# Alarm-Mapping vollständig
# ---------------------------------------------------------------------------


class TestAlarmMapping:
    """Prüft, dass alle Hersteller-Alarme gemappt sind."""

    def test_all_alarm_codes_present(self):
        expected = {
            "temperature_below_low_alarm",
            "temperature_above_high_alarm",
            "ac_power_failure",
            "control_probe_fault",
            "microprocessor_fault",
            "heat_exchanger_fault",
            "hot_condenser",
        }

        assert set(FREEZER_ALARMS.values()) == expected


class TestReadDeviceInfo:
    def test_device_info(self, reader, monkeypatch):
        monkeypatch.setattr(
            "freezer._usb_ids",
            lambda port: {"usb_vid": "0403", "usb_pid": "6001"},
        )
        reader.port = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9NX8YRE-if00-port0"

        info = reader.read_device_info()

        assert info["port"] == reader.port
        assert info["usb_serial"] == "A9NX8YRE"
        assert info["usb_vid"] == "0403"
        assert info["usb_pid"] == "6001"
