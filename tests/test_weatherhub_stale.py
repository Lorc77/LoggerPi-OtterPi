"""Tests für die WeatherHub-Stale-Logik."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from weatherhub import WeatherHubReader
from weatherhub_gateway_decoder import GatewayPacket


class TestWeatherHubStaleLogic:
    """Testet die Stale-Logik des WeatherHubReaders."""

    def _make_gateway_packet(
        self,
        sensor_id: str,
        sensor_type: int,
        decoded_values: Dict[str, Any],
        gateway_timestamp: int = 1000,
    ) -> GatewayPacket:
        """Erzeugt ein GatewayPacket mit den gegebenen Werten."""
        return GatewayPacket(
            gateway_timestamp=gateway_timestamp,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            decoded_values=decoded_values,
            raw_data=bytes(64),
        )

    def _make_id01_packet(self, sensor_id: str, temp1: float, temp2: float) -> GatewayPacket:
        """Erzeugt ein ID01-Paket mit zwei Temperaturen."""
        return self._make_gateway_packet(
            sensor_id=sensor_id,
            sensor_type=0x01,
            decoded_values={
                "temperature_1": {"value": temp1, "error": False, "overflow": False},
                "temperature_2": {"value": temp2, "error": False, "overflow": False},
            },
        )

    def test_fresh_sensor_is_valid(self) -> None:
        """Ein Sensor, der gerade gesendet hat, ist valid."""
        reader = WeatherHubReader(stale_after_seconds=1800)
        packet = self._make_id01_packet("017A5CD3FC1C", 23.4, -25.1)

        reader.update_from_packets([packet])
        measurements = reader.read_measurements()

        assert measurements["weatherhub_017a5cd3fc1c.temperature_1"].validity == "valid"
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].validity == "valid"
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].value == -25.1

    def test_stale_sensor_marks_measurements_as_stale(self, monkeypatch) -> None:
        """Ein Sensor, der zu lange nicht gesendet hat, wird als stale markiert."""
        reader = WeatherHubReader(stale_after_seconds=1800)
        packet = self._make_id01_packet("017A5CD3FC1C", 23.4, -25.1)

        reader.update_from_packets([packet])

        # Simuliere, dass 2 Stunden vergangen sind (länger als stale_after_seconds=1800)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        reader._reception_times["017A5CD3FC1C"] = old_time.isoformat()

        measurements = reader.read_measurements()

        assert measurements["weatherhub_017a5cd3fc1c.temperature_1"].validity == "stale"
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].validity == "stale"
        # Wert bleibt bei stale erhalten
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].value == -25.1

    def test_sensor_recovers_after_new_packet(self) -> None:
        """Nach einem neuen Paket wird der Sensor wieder valid."""
        reader = WeatherHubReader(stale_after_seconds=1800)
        packet = self._make_id01_packet("017A5CD3FC1C", 23.4, -25.1)

        reader.update_from_packets([packet])

        # Simuliere, dass 2 Stunden vergangen sind
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        reader._reception_times["017A5CD3FC1C"] = old_time.isoformat()

        measurements = reader.read_measurements()
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].validity == "stale"

        # Neues Paket kommt an
        new_packet = self._make_id01_packet("017A5CD3FC1C", 23.5, -25.0)
        reader.update_from_packets([new_packet])

        measurements = reader.read_measurements()
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].validity == "valid"
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].value == -25.0

    def test_sensor_never_received_is_unavailable(self) -> None:
        """Ein Sensor, der nie empfangen wurde, hat keine Measurements."""
        reader = WeatherHubReader(stale_after_seconds=1800)

        # Kein Packet empfangen
        measurements = reader.read_measurements()

        assert measurements == {}

    def test_custom_stale_threshold(self) -> None:
        """Der Stale-Schwellenwert ist konfigurierbar."""
        reader = WeatherHubReader(stale_after_seconds=60)  # Nur 60 Sekunden
        packet = self._make_id01_packet("017A5CD3FC1C", 23.4, -25.1)

        reader.update_from_packets([packet])

        # Simuliere, dass 2 Minuten vergangen sind (> 60 Sekunden)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        reader._reception_times["017A5CD3FC1C"] = old_time.isoformat()

        measurements = reader.read_measurements()
        assert measurements["weatherhub_017a5cd3fc1c.temperature_1"].validity == "stale"

    def test_stale_within_threshold_is_valid(self) -> None:
        """Ein Sensor innerhalb des Schwellenwerts bleibt valid."""
        reader = WeatherHubReader(stale_after_seconds=1800)
        packet = self._make_id01_packet("017A5CD3FC1C", 23.4, -25.1)

        reader.update_from_packets([packet])

        # Simuliere, dass nur 10 Minuten vergangen sind (< 1800 Sekunden)
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        reader._reception_times["017A5CD3FC1C"] = recent_time.isoformat()

        measurements = reader.read_measurements()
        assert measurements["weatherhub_017a5cd3fc1c.temperature_1"].validity == "valid"
        assert measurements["weatherhub_017a5cd3fc1c.temperature_2"].validity == "valid"

    def test_id03_sensor_stale_keeps_humidity(self) -> None:
        """ID03-Sensor: Auch Feuchte wird bei stale markiert und behält den Wert."""
        reader = WeatherHubReader(stale_after_seconds=1800)
        packet = self._make_gateway_packet(
            sensor_id="03469858AF14",
            sensor_type=0x03,
            decoded_values={
                "temperature": {"value": 23.4, "error": False, "overflow": False},
                "humidity": {"value": 42.0, "error": False, "overflow": False},
            },
        )

        reader.update_from_packets([packet])

        # Simuliere, dass 2 Stunden vergangen sind
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        reader._reception_times["03469858AF14"] = old_time.isoformat()

        measurements = reader.read_measurements()

        assert measurements["weatherhub_03469858af14.temperature"].validity == "stale"
        assert measurements["weatherhub_03469858af14.humidity"].validity == "stale"
        assert measurements["weatherhub_03469858af14.temperature"].value == 23.4
        assert measurements["weatherhub_03469858af14.humidity"].value == 42.0
