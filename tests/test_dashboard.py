"""Tests für das Dashboard."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from dashboard import (
    _render_climate_detail,
    _render_device_detail,
    _render_overview,
    _render_room_detail,
)
from dashboard_config import get_rooms
from dashboard_data import _device_current, _device_status, _room_climate, _series
from otterpi_store import BatchStore


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """Sorgt dafür, dass get_rooms() im Test auf _DEFAULT_ROOMS fällt."""
    monkeypatch.setenv("OTTERPI_CONFIG_DIR", str(tmp_path / "config"))


# ---------------------------------------------------------------------------
# Fixtures & Helper
# ---------------------------------------------------------------------------


def _make_measurement(value, unit="celsius", validity="valid", measured_at=None):
    """Erzeugt ein Measurement-Dict wie es im Batch vorkommt."""
    return {
        "value": value,
        "unit": unit,
        "measured_at": measured_at or "2026-10-27T12:00:00+00:00",
        "validity": validity,
        "source": "weatherhub",
    }


def _make_batch(measurements=None, created_at=None):
    """Erzeugt einen Batch-Dict für Tests."""
    return {
        "batch_id": "test-batch",
        "logger_id": "loggerpi-001",
        "sequence": 0,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "measurements": measurements or {},
        "system": {
            "cpu": {"temperature_celsius": 45.0},
        },
        "memory": {
            "total_bytes": 1000,
            "used_bytes": 500,
        },
    }


def _store_batches(tmp_path, batches):
    """Speichert Batches in einer SQLite-Datenbank."""
    store = BatchStore(tmp_path / "otter.db")
    with sqlite3.connect(store.path) as conn:
        for batch in batches:
            conn.execute(
                (
                    "INSERT INTO batches "
                    "(batch_id, logger_id, sequence, payload) "
                    "VALUES (?, ?, ?, ?)"
                ),
                (
                    batch["batch_id"],
                    batch["logger_id"],
                    batch["sequence"],
                    json.dumps(batch),
                ),
            )
    return store


@pytest.fixture
def sample_batches():
    """Erzeugt Beispiel-Batches mit allen Sensor-Typen."""
    measurements = {
        # AtmoWEB
        "atmoweb_101.temperature_1": _make_measurement(23.5),
        "atmoweb_101.humidity": _make_measurement(60.0, unit="percent"),
        # Freezer
        "freezer.temperature": _make_measurement(-80.0),
        # Memmert
        "memmert_ipp300_links.temperature": _make_measurement(10.0),
        "memmert_ipp300_rechts.temperature": _make_measurement(None, validity="unavailable"),
        # WeatherHub ID03 - R1304 (Raumklima)
        "weatherhub_03469858af14.temperature": _make_measurement(21.3),
        "weatherhub_03469858af14.humidity": _make_measurement(48.0, unit="percent"),
        # WeatherHub ID0E - R1304 (DryAger)
        "weatherhub_0e74a4597b54.temperature": _make_measurement(16.4),
        "weatherhub_0e74a4597b54.humidity": _make_measurement(70.0, unit="percent"),
        # WeatherHub ID01 - R1306 (3 Sensoren)
        "weatherhub_017453bf9a79.temperature_1": _make_measurement(21.8),
        "weatherhub_017453bf9a79.temperature_2": _make_measurement(-21.5),
        "weatherhub_0106caf71038.temperature_1": _make_measurement(22.0),
        "weatherhub_0106caf71038.temperature_2": _make_measurement(-25.4),
        "weatherhub_015f9410f3eb.temperature_1": _make_measurement(21.5),
        "weatherhub_015f9410f3eb.temperature_2": _make_measurement(-23.1),
        # WeatherHub ID01 - R1307
        "weatherhub_017262bf9016.temperature_1": _make_measurement(21.0),
        "weatherhub_017262bf9016.temperature_2": _make_measurement(-25.5),
        # WeatherHub ID01 - R1308 (4 Sensoren)
        "weatherhub_015c32e3ced1.temperature_1": _make_measurement(21.2),
        "weatherhub_015c32e3ced1.temperature_2": _make_measurement(13.8),
        "weatherhub_015eb583b95c.temperature_1": _make_measurement(21.8),
        "weatherhub_015eb583b95c.temperature_2": _make_measurement(15.5),
        "weatherhub_015e664f727f.temperature_1": _make_measurement(21.4),
        "weatherhub_015e664f727f.temperature_2": _make_measurement(13.5),
        "weatherhub_0167554c25be.temperature_1": _make_measurement(21.3),
        "weatherhub_0167554c25be.temperature_2": _make_measurement(15.8),
        # WeatherHub ID01 - R1309
        "weatherhub_0167ce8a9af4.temperature_1": _make_measurement(21.2),
        "weatherhub_0167ce8a9af4.temperature_2": _make_measurement(-25.2),
        # WeatherHub ID01 - R1310 (3 Sensoren)
        "weatherhub_015d087ca01c.temperature_1": _make_measurement(21.5),
        "weatherhub_015d087ca01c.temperature_2": _make_measurement(19.5),
        "weatherhub_0146471130bf.temperature_1": _make_measurement(21.1),
        "weatherhub_0146471130bf.temperature_2": _make_measurement(17.2),
        "weatherhub_010678c5ab4a.temperature_1": _make_measurement(21.6),
        "weatherhub_010678c5ab4a.temperature_2": _make_measurement(-22.9),
        # WeatherHub ID01 - R1311 (2 Sensoren)
        "weatherhub_0101f89974e0.temperature_1": _make_measurement(21.3),
        "weatherhub_0101f89974e0.temperature_2": _make_measurement(4.5),
        "weatherhub_017a5cd3fc1c.temperature_1": _make_measurement(21.1),
        "weatherhub_017a5cd3fc1c.temperature_2": _make_measurement(-24.8),
        # WeatherHub ID01 - R1313
        "weatherhub_0169706ebe2c.temperature_1": _make_measurement(20.2),
        "weatherhub_0169706ebe2c.temperature_2": _make_measurement(-25.3),
    }
    return [_make_batch(measurements)]


# ---------------------------------------------------------------------------
# ROOMS-Struktur
# ---------------------------------------------------------------------------


class TestRooms:
    """Testet die ROOMS-Struktur."""

    def test_all_rooms_present(self):
        """Alle 8 Räume müssen vorhanden sein."""
        expected_rooms = {
            "r1304",
            "r1306",
            "r1307",
            "r1308",
            "r1309",
            "r1310",
            "r1311",
            "r1313",
        }
        assert set(get_rooms().keys()) == expected_rooms

    def test_all_weatherhub_sensors_are_configured(self):
        """Alle 17 WeatherHub-Sensoren müssen in ROOMS konfiguriert sein."""
        all_devices = []
        for room in get_rooms().values():
            all_devices.extend(room["devices"])
            all_devices.extend(
                {"key": k, "type": "weatherhub_climate"} for k in room.get("weatherhub_climate", [])
            )

        sensor_keys = [d["key"] for d in all_devices if d["type"].startswith("weatherhub")]

        expected_sensors = {
            "weatherhub_0101f89974e0",
            "weatherhub_010678c5ab4a",
            "weatherhub_0106caf71038",
            "weatherhub_0146471130bf",
            "weatherhub_015c32e3ced1",
            "weatherhub_015d087ca01c",
            "weatherhub_015e664f727f",
            "weatherhub_015eb583b95c",
            "weatherhub_015f9410f3eb",
            "weatherhub_0167554c25be",
            "weatherhub_0167ce8a9af4",
            "weatherhub_0169706ebe2c",
            "weatherhub_017262bf9016",
            "weatherhub_017453bf9a79",
            "weatherhub_017a5cd3fc1c",
            "weatherhub_03469858af14",
            "weatherhub_0e74a4597b54",
        }

        assert set(sensor_keys) == expected_sensors

    def test_room_names_in_english(self):
        """Raumnamen müssen englisch sein."""
        rooms = get_rooms()
        assert rooms["r1304"]["name"] == "R1304 · Culture Room I"
        assert rooms["r1306"]["name"] == "R1306 · Molecular Lab"
        assert rooms["r1307"]["name"] == "R1307 · Cold Room Vestibule"
        assert rooms["r1308"]["name"] == "R1308 · Culture Room II"
        assert rooms["r1309"]["name"] == "R1309 · RNA Lab"
        assert rooms["r1310"]["name"] == "R1310 · Histology Lab"
        assert rooms["r1311"]["name"] == "R1311 · Immunology Lab"
        assert rooms["r1313"]["name"] == "R1313 · Teaching Lab"


# ---------------------------------------------------------------------------
# _room_climate
# ---------------------------------------------------------------------------


class TestRoomClimate:
    """Testet die Raumklima-Berechnung."""

    def test_room_climate_r1304_only_id03(self, sample_batches):
        """R1304 hat nur ID03 (keine ID01) → Raumtemp = ID03-Temp."""
        room = get_rooms()["r1304"]
        climate = _room_climate(sample_batches, room)

        assert climate["temp"] == pytest.approx(21.3, abs=0.01)
        assert climate["hum"] == pytest.approx(48.0, abs=0.01)

    def test_room_climate_r1306_with_id01(self, sample_batches):
        """R1306 hat nur ID01-Sensoren → Raumtemp = Mittelwert."""
        room = get_rooms()["r1306"]
        climate = _room_climate(sample_batches, room)

        assert climate["temp"] == pytest.approx(21.77, abs=0.01)
        assert climate["hum"] is None

    def test_room_climate_ignores_id0e(self, sample_batches):
        """ID0E (DryAger) darf nicht in die Raumtemperatur einfließen."""
        room = get_rooms()["r1304"]
        climate = _room_climate(sample_batches, room)

        assert climate["temp"] == pytest.approx(21.3, abs=0.01)

    def test_room_climate_empty_batches(self):
        """Ohne Batches gibt es kein Raumklima."""
        room = get_rooms()["r1304"]
        climate = _room_climate([], room)

        assert climate["temp"] is None
        assert climate["hum"] is None

    def test_room_climate_missing_values(self):
        """Fehlende Messwerte werden ignoriert."""
        measurements = {
            "weatherhub_0101f89974e0.temperature_1": _make_measurement(21.5),
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(4.5),
        }
        batches = [_make_batch(measurements)]
        room = get_rooms()["r1311"]

        climate = _room_climate(batches, room)

        assert climate["temp"] == pytest.approx(21.5, abs=0.01)


# ---------------------------------------------------------------------------
# _device_current
# ---------------------------------------------------------------------------


class TestDeviceCurrent:
    """Testet die aktuellen Gerätewerte."""

    def test_id01_shows_temperature_2(self, sample_batches):
        """ID01-Sensoren zeigen nur temperature_2 (Gerätetemperatur)."""
        result = _device_current(sample_batches, "weatherhub_0101f89974e0", "weatherhub_id01")

        assert result["temp"] == 4.5
        assert result["value"] == "4.5 °C"
        assert result["hum"] == 0.0

    def test_id0e_shows_temperature_and_humidity(self, sample_batches):
        """ID0E (DryAger) zeigt temperature + humidity."""
        result = _device_current(sample_batches, "weatherhub_0e74a4597b54", "weatherhub_id0e")

        assert result["temp"] == 16.4
        assert result["hum"] == 70.0
        assert result["value"] == "16.4 °C"

    def test_atmoweb_shows_temperature_1(self, sample_batches):
        """AtmoWEB zeigt temperature_1 + humidity."""
        result = _device_current(sample_batches, "atmoweb_101", "atmoweb")

        assert result["temp"] == 23.5
        assert result["hum"] == 60.0
        assert result["value"] == "23.5 °C"

    def test_freezer_shows_temperature(self, sample_batches):
        """Freezer zeigt temperature."""
        result = _device_current(sample_batches, "freezer", "freezer")

        assert result["temp"] == -80.0
        assert result["value"] == "-80.0 °C"

    def test_memmert_unavailable(self, sample_batches):
        """MEMMERT rechts ist unavailable (kein Wert)."""
        result = _device_current(sample_batches, "memmert_ipp300_rechts", "memmert")

        assert result["temp"] == 0.0
        assert result["value"] == "–"
        assert result["status"] == "lamp-off"

    def test_placeholder_returns_empty(self, sample_batches):
        """Platzhalter liefert keine Werte."""
        result = _device_current(sample_batches, "dryager", "placeholder")

        assert result["temp"] == 0.0
        assert result["value"] == "–"


# ---------------------------------------------------------------------------
# _device_status
# ---------------------------------------------------------------------------


class TestDeviceStatus:
    """Testet die Status-Berechnung."""

    def test_status_valid(self, sample_batches):
        """Gültige Werte → status-ok."""
        assert (
            _device_status(sample_batches, "weatherhub_0101f89974e0", "weatherhub_id01")
            == "status-ok"
        )
        assert (
            _device_status(sample_batches, "weatherhub_0e74a4597b54", "weatherhub_id0e")
            == "status-ok"
        )
        assert _device_status(sample_batches, "atmoweb_101", "atmoweb") == "status-ok"
        assert _device_status(sample_batches, "freezer", "freezer") == "status-ok"

    def test_status_unavailable(self, sample_batches):
        """Unavailable → status-off."""
        assert _device_status(sample_batches, "memmert_ipp300_rechts", "memmert") == "status-off"

    def test_status_invalid(self):
        """Invalid → status-critical."""
        measurements = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(None, validity="invalid"),
        }
        batches = [_make_batch(measurements)]
        assert (
            _device_status(batches, "weatherhub_0101f89974e0", "weatherhub_id01")
            == "status-critical"
        )

    def test_status_stale(self):
        """Stale → status-warn."""
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        measurements = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                4.5, validity="stale", measured_at=old_time
            ),
        }
        batches = [_make_batch(measurements)]
        assert (
            _device_status(batches, "weatherhub_0101f89974e0", "weatherhub_id01") == "status-warn"
        )

    def test_status_no_batches(self):
        """Ohne Batches → status-off."""
        assert _device_status([], "weatherhub_0101f89974e0", "weatherhub_id01") == "status-off"

    def test_status_placeholder(self, sample_batches):
        """Platzhalter → status-off."""
        assert _device_status(sample_batches, "dryager", "placeholder") == "status-off"


# ---------------------------------------------------------------------------
# _series
# ---------------------------------------------------------------------------


class TestSeries:
    """Testet die Messwert-Reihen-Extraktion."""

    def test_series_extracts_values(self):
        """Serie extrahiert nur Werte mit measured_at."""
        measurements = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                4.5, measured_at="2026-10-27T12:00:00+00:00"
            ),
        }
        batches = [_make_batch(measurements)]

        series = _series(batches, "weatherhub_0101f89974e0.temperature_2")

        assert len(series) == 1
        assert series[0]["value"] == 4.5
        assert series[0]["label"] == "13:00"
        assert series[0]["date"] == "2026-10-27"

    def test_series_skips_missing_values(self):
        """Serie überspringt Measurements ohne Wert."""
        measurements = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                None, validity="unavailable"
            ),
        }
        batches = [_make_batch(measurements)]

        series = _series(batches, "weatherhub_0101f89974e0.temperature_2")

        assert series == []

    def test_series_multiple_batches(self):
        """Serie aus mehreren Batches in chronologischer Reihenfolge."""
        measurements_1 = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                4.5, measured_at="2026-10-27T10:00:00+00:00"
            ),
        }
        measurements_2 = {
            "weatherhub_0101f89974e0.temperature_2": _make_measurement(
                5.0, measured_at="2026-10-27T11:00:00+00:00"
            ),
        }
        batches = [
            _make_batch(measurements_1, created_at="2026-10-27T10:00:00+00:00"),
            _make_batch(measurements_2, created_at="2026-10-27T11:00:00+00:00"),
        ]

        series = _series(batches, "weatherhub_0101f89974e0.temperature_2")

        assert len(series) == 2
        assert series[0]["value"] == 4.5
        assert series[1]["value"] == 5.0


# ---------------------------------------------------------------------------
# _render_overview
# ---------------------------------------------------------------------------


class TestRenderOverview:
    """Testet die Übersichtsseite."""

    def test_overview_contains_room_climate(self, sample_batches, tmp_path):
        """Übersicht enthält Raumklima in der Raum-Kopfzeile."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_overview(store)

        assert "🌡️ 21.3 °C" in html
        assert "💧 48 %" in html

    def test_overview_contains_english_texts(self, sample_batches, tmp_path):
        """Übersicht enthält englische Texte."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_overview(store)

        assert "Last measurement" in html


# ---------------------------------------------------------------------------
# _render_room_detail
# ---------------------------------------------------------------------------


class TestRenderRoomDetail:
    """Testet die Raum-Detailseite."""

    def test_room_detail_contains_climate(self, sample_batches, tmp_path):
        """Detailseite enthält Raumklima im Subtitle."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_room_detail(store, "r1304")

        assert "🌡️ Room temperature: 21.3 °C" in html
        assert "💧 Relative Humidity: 48.0 %" in html
        assert "Letzte 48 Stunden" not in html

    def test_room_detail_contains_english_back_button(self, sample_batches, tmp_path):
        """Detailseite enthält englischen Back-Button."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_room_detail(store, "r1304")

        assert "← Back to Overview" in html

    def test_room_detail_odd_number_cards_full_width(self, sample_batches, tmp_path):
        """Letzte Kachel bei ungerader Anzahl auf voller Breite."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_room_detail(store, "r1307")

        assert "device-card device-card-full" in html

    def test_room_detail_even_number_cards_no_full_width(self, sample_batches, tmp_path):
        """Bei gerader Anzahl keine volle Breite."""
        store = _store_batches(tmp_path, sample_batches)

        html = _render_room_detail(store, "r1311")

        assert "device-card device-card-full" not in html


class TestRenderClimateDetail:
    """Smoke-Tests für die Raumklima-Detailseite."""

    def test_climate_detail_renders(self, sample_batches, tmp_path):
        store = _store_batches(tmp_path, sample_batches)
        html = _render_climate_detail(store, "r1304")
        assert "Room Climate" in html
        assert "Average Temperature" in html

    def test_climate_detail_not_found(self, sample_batches, tmp_path):
        store = _store_batches(tmp_path, sample_batches)
        html = _render_climate_detail(store, "unknown")
        assert "Not Found" in html


class TestRenderDeviceDetail:
    """Smoke-Tests für die Geräte-Detailseite."""

    def test_device_detail_renders(self, sample_batches, tmp_path):
        store = _store_batches(tmp_path, sample_batches)
        html = _render_device_detail(store, "atmoweb_101")
        assert "Statistics" in html
        assert "atmoweb_101" in html

    def test_device_detail_not_found(self, sample_batches, tmp_path):
        store = _store_batches(tmp_path, sample_batches)
        html = _render_device_detail(store, "unknown")
        assert "Not Found" in html


def test_render_led_svg_on():
    from dashboard import _render_led_svg

    html = _render_led_svg(2)
    assert "led-on" in html
    assert "2%" in html


def test_render_led_svg_off():
    from dashboard import _render_led_svg

    html = _render_led_svg(0)
    assert "led-off" in html
    assert "0%" in html


def test_render_led_svg_none():
    from dashboard import _render_led_svg

    assert _render_led_svg(None) == ""


def test_render_chips():
    from dashboard import _render_chips

    html = _render_chips([("OK", "chip-ok"), ("Door open", "chip-info")])
    assert 'class="chip chip-ok"' in html
    assert "OK" in html
    assert "Door open" in html


class TestRenderOverviewStatus:
    def test_overview_shows_status_lamp(self, sample_batches, tmp_path):
        store = _store_batches(tmp_path, sample_batches)
        html = _render_overview(store)
        assert 'class="lamp status-ok"' in html
        assert "Last batch" in html

    def test_overview_shows_offline_status(self, tmp_path):
        old = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
        batches = [_make_batch(created_at=old)]
        store = _store_batches(tmp_path, batches)
        html = _render_overview(store)
        assert "LoggerPi offline" in html
        assert "status-critical" in html
