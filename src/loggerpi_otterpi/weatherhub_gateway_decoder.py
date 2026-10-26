"""Decoder for WeatherHub Gateway payloads.

Provides protocol parsing and payload decoding for supported WeatherHub sensors.
Does not have any dependencies on the runtime, storage, or network.
"""

import logging
from dataclasses import dataclass
from typing import Any, Union

LOGGER = logging.getLogger(__name__)


class WeatherHubDecoderError(ValueError):
    """Base error for invalid WeatherHub packets or decoding failures."""


@dataclass(frozen=True)
class BootPacket:
    """Represents a 15-byte gateway boot/control packet."""

    raw_data: bytes


@dataclass(frozen=True)
class GatewayPacket:
    """Represents a decoded 64-byte sensor packet."""

    gateway_timestamp: int
    sensor_id: str
    sensor_type: int
    decoded_values: dict[str, Any]
    raw_data: bytes


# Supported sensor families for production processing
SUPPORTED_SENSOR_TYPES = {
    0x01: {"name": "ID01", "header": 0xD2, "packet_length": 0x16, "payload_length": 10},
    0x02: {"name": "ID02", "header": 0xCE, "packet_length": 0x12, "payload_length": 6},
    0x03: {"name": "ID03", "header": 0xD2, "packet_length": 0x16, "payload_length": 10},
    0x04: {"name": "ID04", "header": 0xD4, "packet_length": 0x18, "payload_length": 12},
    0x07: {"name": "ID07", "header": 0xDA, "packet_length": 0x1E, "payload_length": 18},
    0x0E: {"name": "ID0E", "header": 0xD8, "packet_length": 0x1C, "payload_length": 16},
    0x10: {"name": "ID10", "header": 0xD3, "packet_length": 0x17, "payload_length": 11},
}


def decode_temperature(data: bytes) -> dict[str, Any]:
    if len(data) < 2:
        raise WeatherHubDecoderError("Temperature data too short.")

    first, second = data[0], data[1]
    raw = ((first & 0x07) << 8) | second

    if 0 <= raw <= 1023:
        value = raw * 0.1
    else:
        value = (2048 - raw) * -0.1

    return {
        "value": value,
        "overflow": bool(first & 0x20),
        "error": bool(first & 0x10),
        "up05": bool(first & 0x80),
        "down05": bool(first & 0x40),
    }


def decode_humidity(data: bytes) -> dict[str, Any]:
    if len(data) < 2:
        raise WeatherHubDecoderError("Humidity data too short.")

    first, second = data[0], data[1]

    return {
        "value": second & 0x7F,
        "up05": bool(first & 0x80),
        "down05": bool(first & 0x40),
        "sensor_id": first & 0x0F,
        "average": bool(second & 0x80),
    }


def decode_humidity_decimal(data: bytes) -> dict[str, Any]:
    if len(data) < 2:
        raise WeatherHubDecoderError("Decimal humidity data too short.")

    raw = ((data[0] & 0x03) << 8) | data[1]

    return {
        "value": raw / 10.0,
    }


def decode_sensor_status(data: bytes) -> dict[str, Any]:
    if len(data) < 2:
        raise WeatherHubDecoderError("Status data too short.")

    return {
        "battery_low": bool(data[0] & 0x80),
        "event_transmission": bool(data[0] & 0x40),
        "counter": ((data[0] & 0x3F) << 8) | data[1],
    }


def decode_door_window(data: bytes) -> dict[str, Any]:
    if len(data) < 2:
        raise WeatherHubDecoderError("Door/window data too short.")

    first, second = data[0], data[1]
    unit = (first & 0x60) >> 5
    elapsed = ((first & 0x1F) << 8) | second

    return {
        "open": bool(first & 0x80),
        "time_unit": unit,
        "elapsed_value": elapsed,
    }


def decode_current_values(sensor_type: int, payload: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {}

    # Status bytes are present in these sensor families
    if sensor_type in {0x01, 0x02, 0x03, 0x04, 0x07, 0x0E}:
        result["status"] = decode_sensor_status(payload[0:2])

    if sensor_type == 0x01:
        result["temperature_1"] = decode_temperature(payload[2:4])
        result["temperature_2"] = decode_temperature(payload[4:6])

    elif sensor_type == 0x02:
        result["temperature"] = decode_temperature(payload[2:4])

    elif sensor_type == 0x03:
        result["temperature"] = decode_temperature(payload[2:4])
        result["humidity"] = decode_humidity(payload[4:6])

    elif sensor_type == 0x04:
        result["temperature"] = decode_temperature(payload[2:4])
        result["humidity"] = decode_humidity(payload[4:6])
        result["water_contact_raw"] = payload[6]

    elif sensor_type == 0x07:
        result["temperature_indoor"] = decode_temperature(payload[2:4])
        result["humidity_indoor"] = decode_humidity(payload[4:6])
        result["temperature_outdoor"] = decode_temperature(payload[6:8])
        result["humidity_outdoor"] = decode_humidity(payload[8:10])

    elif sensor_type == 0x0E:
        result["temperature"] = decode_temperature(payload[2:4])
        result["humidity"] = decode_humidity_decimal(payload[4:6])

    elif sensor_type == 0x10:
        result["contact"] = decode_door_window(payload[2:4])

    return result


def decode_packet(packet: bytes) -> GatewayPacket:
    """Decode a single 64-byte sensor packet and validate its structure."""
    if len(packet) != 64:
        raise WeatherHubDecoderError(f"Sensor packet must be 64 bytes, got {len(packet)}.")

    checksum_expected = sum(packet[:63]) & 0x7F
    checksum_actual = packet[63]
    if checksum_expected != checksum_actual:
        raise WeatherHubDecoderError(
            f"CRC mismatch: expected {checksum_expected}, got {checksum_actual}."
        )

    package_header = packet[0]
    timestamp = int.from_bytes(packet[1:5], byteorder="big")
    packet_length = packet[5]
    sensor_id = packet[6:12].hex().upper()
    sensor_type = packet[6]

    payload_length = packet_length - 12
    if payload_length < 0 or payload_length > 52:
        raise WeatherHubDecoderError(f"Invalid payload length {payload_length}.")

    payload = packet[12 : 12 + payload_length]

    sensor_def = SUPPORTED_SENSOR_TYPES.get(sensor_type)
    if sensor_def is None:
        # We successfully parsed the CRC, but it's an unsupported sensor type.
        # We return it without decoded values.
        return GatewayPacket(
            gateway_timestamp=timestamp,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            decoded_values={},
            raw_data=packet,
        )

    if package_header != sensor_def["header"]:
        raise WeatherHubDecoderError(
            f"Header mismatch for {sensor_def['name']}: "
            f"expected {sensor_def['header']}, got {package_header}."
        )

    if (
        packet_length != sensor_def["packet_length"]
        or payload_length != sensor_def["payload_length"]
    ):
        raise WeatherHubDecoderError(f"Length mismatch for {sensor_def['name']}.")

    try:
        decoded_values = decode_current_values(sensor_type, payload)
    except Exception as exc:
        raise WeatherHubDecoderError(
            f"Failed to decode values for {sensor_def['name']}: {exc}"
        ) from exc

    return GatewayPacket(
        gateway_timestamp=timestamp,
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        decoded_values=decoded_values,
        raw_data=packet,
    )


def decode_payload(body: bytes) -> list[Union[BootPacket, GatewayPacket]]:
    """Decode an entire HTTP PUT body from the Gateway.

    Silently skips invalid 64-byte packets (e.g. CRC error) but parses the rest,
    as required by the robustness strategy.
    Only supported sensor families will have `decoded_values` populated.
    """
    if len(body) == 15:
        return [BootPacket(raw_data=body)]

    if len(body) == 0 or len(body) % 64 != 0:
        raise WeatherHubDecoderError(
            f"Invalid total payload length: {len(body)} (must be 15 or a multiple of 64)"
        )

    results: list[Union[BootPacket, GatewayPacket]] = []

    for offset in range(0, len(body), 64):
        packet_bytes = body[offset : offset + 64]
        try:
            packet = decode_packet(packet_bytes)
            if packet.sensor_type in SUPPORTED_SENSOR_TYPES:
                results.append(packet)
            else:
                LOGGER.debug("Skipped unsupported sensor type: %02X", packet.sensor_type)
        except WeatherHubDecoderError as exc:
            LOGGER.warning("Skipped invalid 64-byte packet: %s", exc)

    return results
