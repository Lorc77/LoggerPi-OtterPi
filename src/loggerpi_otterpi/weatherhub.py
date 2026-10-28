"""WeatherHub measurement adapter.

Provides the WeatherHubReader to convert decoded Gateway packets
into Core Measurement objects.
"""

from datetime import datetime, timezone
from typing import Union

from model.measurement import Measurement
from weatherhub_gateway_decoder import BootPacket, GatewayPacket


class WeatherHubReader:
    """Adapter between WeatherHub Gateway packets and Core Measurements."""

    def __init__(self, stale_after_seconds: float = 1800.0) -> None:
        self.stale_after_seconds = stale_after_seconds
        self._latest_packets: dict[str, GatewayPacket] = {}
        self._reception_times: dict[str, str] = {}

    def update_from_packets(self, packets: list[Union[BootPacket, GatewayPacket]]) -> None:
        """Process new decoded packets and update the internal state."""
        received_at = datetime.now(timezone.utc).isoformat()

        for packet in packets:
            # Skip BootPackets or packets without decoded values
            if not isinstance(packet, GatewayPacket):
                continue
            if not packet.decoded_values:
                continue

            self._latest_packets[packet.sensor_id] = packet
            self._reception_times[packet.sensor_id] = received_at

    def _is_stale(self, sensor_id: str) -> bool:
        """True, wenn der letzte Empfang für diesen Sensor zu lange her ist."""
        if sensor_id not in self._reception_times:
            return True

        received_at = datetime.fromisoformat(self._reception_times[sensor_id])
        age_seconds = (datetime.now(timezone.utc) - received_at).total_seconds()
        return age_seconds > self.stale_after_seconds

    @property
    def gateway_timestamps(self) -> dict[str, int]:
        """Return the latest gateway timestamp for each known sensor.

        Preserves the Gateway timestamp separately from the LoggerPi reception time,
        similar to how AtmoWebReader exposes device_time.
        """
        return {
            sensor_id: packet.gateway_timestamp
            for sensor_id, packet in self._latest_packets.items()
        }

    def read_measurements(self) -> dict[str, Measurement]:
        """Return all current valid measurements from known sensors."""
        measurements: dict[str, Measurement] = {}

        for sensor_id, packet in self._latest_packets.items():
            received_at = self._reception_times[sensor_id]
            sensor_type = packet.sensor_type
            decoded = packet.decoded_values

            prefix = f"weatherhub_{sensor_id.lower()}"

            fields_to_extract = {}

            if sensor_type == 0x01:
                fields_to_extract = {
                    "temperature_1": ("celsius", decoded.get("temperature_1")),
                    "temperature_2": ("celsius", decoded.get("temperature_2")),
                }
            elif sensor_type == 0x02:
                fields_to_extract = {
                    "temperature": ("celsius", decoded.get("temperature")),
                }
            elif sensor_type == 0x03:
                fields_to_extract = {
                    "temperature": ("celsius", decoded.get("temperature")),
                    "humidity": ("percent", decoded.get("humidity")),
                }
            elif sensor_type == 0x04:
                # water_contact_raw is intentionally ignored here
                fields_to_extract = {
                    "temperature": ("celsius", decoded.get("temperature")),
                    "humidity": ("percent", decoded.get("humidity")),
                }
            elif sensor_type == 0x07:
                fields_to_extract = {
                    "temperature_indoor": (
                        "celsius",
                        decoded.get("temperature_indoor"),
                    ),
                    "humidity_indoor": (
                        "percent",
                        decoded.get("humidity_indoor"),
                    ),
                    "temperature_outdoor": (
                        "celsius",
                        decoded.get("temperature_outdoor"),
                    ),
                    "humidity_outdoor": (
                        "percent",
                        decoded.get("humidity_outdoor"),
                    ),
                }
            elif sensor_type == 0x0E:
                fields_to_extract = {
                    "temperature": ("celsius", decoded.get("temperature")),
                    "humidity": ("percent", decoded.get("humidity")),
                }
            elif sensor_type == 0x10:
                # ID10 contact is intentionally ignored here (no measurements)
                pass

            for field_name, config in fields_to_extract.items():
                unit = config[0]
                value_dict = config[1]

                if not isinstance(value_dict, dict):
                    continue

                validity = "valid"
                # If the sensor reported an error or overflow,
                # it forms a factual basis for invalidity
                if value_dict.get("error") or value_dict.get("overflow"):
                    validity = "invalid"

                # Stale-Logik: Wenn der Sensor zu lange nicht gesendet hat,
                # wird der letzte bekannte Wert als "stale" markiert.
                if self._is_stale(sensor_id):
                    validity = "stale"

                value = value_dict.get("value")

                measurement = Measurement(
                    value=value if validity == "valid" or validity == "stale" else None,
                    unit=unit,
                    measured_at=received_at,
                    validity=validity,
                    source="weatherhub",
                )

                measurements[f"{prefix}.{field_name}"] = measurement

        return measurements
