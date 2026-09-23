"""Tests für die ThingSpeak-Injektion."""

from model.batch import Batch
from model.measurement import Measurement
from thingspeak_delivery import (
    ThingSpeakDelivery,
    _build_thingspeak_payload,
    _freezer_value,
    _measurement_value,
)


def _make_measurement(
    value,
    unit="celsius",
    validity="valid",
    source="atmoweb",
):
    return Measurement(
        value=value,
        unit=unit,
        measured_at="2026-09-22T12:00:00+00:00",
        validity=validity,
        source=source,
    )


def _make_batch(
    measurements=None,
    system=None,
):
    return Batch(
        batch_id="batch-001",
        logger_id="logger-001",
        sequence=0,
        created_at="2026-09-22T12:00:00+00:00",
        measurements=measurements or {},
        system=system,
    )


class TestBuildThingSpeakPayload:
    """Testet die Payload-Erzeugung."""

    def test_payload_with_measurements(self):
        batch = _make_batch(
            measurements={
                "atmoweb_101.temperature_1": _make_measurement(20.5),
                "atmoweb_101.humidity": _make_measurement(60.4, unit="percent"),
                "atmoweb_102.temperature_1": _make_measurement(21.5),
                "atmoweb_102.humidity": _make_measurement(62.7, unit="percent"),
                "freezer.temperature": _make_measurement(-82.0, source="freezer_serial"),
            },
            system={
                "cpu": {
                    "temperature_celsius": 48.2,
                    "usage_percent": 12.4,
                }
            },
        )

        payload = _build_thingspeak_payload(
            batch=batch,
            api_key="secret-key",
            delta_t=900,
        )

        assert payload["write_api_key"] == "secret-key"

        update = payload["updates"][0]

        assert update["delta_t"] == 900
        assert update["field1"] == "20.50"
        assert update["field2"] == "60.40"
        assert update["field3"] == "21.50"
        assert update["field4"] == "62.70"
        assert update["field5"] == "48.20"
        assert update["field6"] == "12.40"
        assert update["field7"] == -82

    def test_payload_omits_missing_fields(self):
        batch = _make_batch(
            measurements={
                "atmoweb_101.temperature_1": _make_measurement(20.5),
            },
            system={},
        )

        payload = _build_thingspeak_payload(
            batch=batch,
            api_key="secret-key",
            delta_t=0,
        )

        update = payload["updates"][0]

        assert "field1" in update
        assert "field2" not in update
        assert "field3" not in update
        assert "field4" not in update
        assert "field5" not in update
        assert "field6" not in update
        assert "field7" not in update

    def test_payload_empty_when_no_fields(self):
        batch = _make_batch(
            measurements={},
            system={},
        )

        payload = _build_thingspeak_payload(
            batch=batch,
            api_key="secret-key",
            delta_t=0,
        )

        assert payload["updates"] == [{"delta_t": 0}]

    def test_payload_integer_formatting(self):
        """Ganze Zahlen werden ohne Nachkommastelle formatiert."""
        batch = _make_batch(
            measurements={
                "atmoweb_101.temperature_1": _make_measurement(20.0),
            },
            system={
                "cpu": {
                    "temperature_celsius": 48.0,
                    "usage_percent": 12.0,
                }
            },
        )

        payload = _build_thingspeak_payload(
            batch=batch,
            api_key="secret-key",
            delta_t=0,
        )

        update = payload["updates"][0]

        assert update["field1"] == "20"
        assert update["field5"] == "48"
        assert update["field6"] == "12"


class TestFreezerValue:
    """Testet die negative Freezer-Konvertierung."""

    def test_negative_value(self):
        measurements = {"freezer.temperature": _make_measurement(-82.0, source="freezer_serial")}

        assert _freezer_value(measurements) == -82

    def test_value_none(self):
        assert _freezer_value({}) is None

    def test_missing_measurement(self):
        assert _freezer_value({"other.key": _make_measurement(1.0)}) is None


class TestMeasurementValue:
    """Testet die Wert-Extraktion mit String-Formatierung."""

    def test_float_value(self):
        measurements = {
            "key": _make_measurement(20.5),
        }

        assert _measurement_value(measurements, "key") == "20.50"

    def test_integer_value(self):
        measurements = {
            "key": _make_measurement(20.0),
        }

        assert _measurement_value(measurements, "key") == "20"

    def test_missing(self):
        assert _measurement_value({}, "key") is None

    def test_value_none(self):
        measurements = {
            "key": _make_measurement(None, validity="unavailable"),
        }

        assert _measurement_value(measurements, "key") is None


class TestThingSpeakDelivery:
    """Testet die Delivery-Klasse (ohne echten HTTP-Request)."""

    def test_endpoint(self):
        delivery = ThingSpeakDelivery(
            api_key="secret",
            channel_id="2068639",
        )

        assert delivery.endpoint == "https://api.thingspeak.com/channels/2068639/bulk_update.json"

    def test_send_no_fields_returns_false(self, monkeypatch):
        batch = _make_batch(measurements={}, system={})

        delivery = ThingSpeakDelivery(
            api_key="secret",
            channel_id="2068639",
        )

        # Kein urlopen-Aufruf, weil Updates leer sind
        assert delivery.send(batch) is False

    def test_send_success(self, monkeypatch):
        batch = _make_batch(
            measurements={
                "atmoweb_101.temperature_1": _make_measurement(20.5),
            },
            system={},
        )

        class FakeResponse:
            status = 202

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(request, timeout):
            return FakeResponse()

        monkeypatch.setattr(
            "thingspeak_delivery.urlopen",
            fake_urlopen,
        )

        delivery = ThingSpeakDelivery(
            api_key="secret",
            channel_id="2068639",
        )

        assert delivery.send(batch) is True

    def test_send_failure(self, monkeypatch):
        from urllib.error import HTTPError

        batch = _make_batch(
            measurements={
                "atmoweb_101.temperature_1": _make_measurement(20.5),
            },
            system={},
        )

        def fake_urlopen(request, timeout):
            raise HTTPError(
                "url",
                500,
                "Internal Server Error",
                None,
                None,
            )

        monkeypatch.setattr(
            "thingspeak_delivery.urlopen",
            fake_urlopen,
        )

        delivery = ThingSpeakDelivery(
            api_key="secret",
            channel_id="2068639",
        )

        assert delivery.send(batch) is False
