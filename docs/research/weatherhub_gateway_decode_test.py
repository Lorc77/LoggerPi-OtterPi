#!/usr/bin/env python3
"""Read-only decoder for captured MOBILE-ALERTS gateway payloads.

This is a temporary research tool.

It:
- reads captured .bin files,
- recognizes 15-byte boot packets,
- splits 64-byte sensor packets,
- validates the 7-bit checksum,
- decodes the known current sensor values,
- writes no data,
- opens no network connection.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, dict, list

CAPTURE_DIR = Path("/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test_output")


SENSOR_TYPES = {
    0x01: {
        "name": "ID01",
        "header": 0xD2,
        "packet_length": 0x16,
        "payload_length": 10,
    },
    0x02: {
        "name": "ID02",
        "header": 0xCE,
        "packet_length": 0x12,
        "payload_length": 6,
    },
    0x03: {
        "name": "ID03",
        "header": 0xD2,
        "packet_length": 0x16,
        "payload_length": 10,
    },
    0x04: {
        "name": "ID04",
        "header": 0xD4,
        "packet_length": 0x18,
        "payload_length": 12,
    },
    0x06: {
        "name": "ID06",
        "header": 0xD6,
        "packet_length": 0x1A,
        "payload_length": 14,
    },
    0x07: {
        "name": "ID07",
        "header": 0xDA,
        "packet_length": 0x1E,
        "payload_length": 18,
    },
    0x08: {
        "name": "ID08",
        "header": 0xE1,
        "packet_length": 0x25,
        "payload_length": 25,
    },
    0x0B: {
        "name": "ID0B",
        "header": 0xE2,
        "packet_length": 0x26,
        "payload_length": 26,
    },
    0x0E: {
        "name": "ID0E",
        "header": 0xD8,
        "packet_length": 0x1C,
        "payload_length": 16,
    },
    0x10: {
        "name": "ID10",
        "header": 0xD3,
        "packet_length": 0x17,
        "payload_length": 11,
    },
    0x11: {
        "name": "ID11",
        "header": 0xEA,
        "packet_length": 0x2E,
        "payload_length": 34,
    },
}


def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp as UTC ISO-8601."""
    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


def decode_temperature(data: bytes) -> dict[str, Any]:
    """Decode the repository's signed 11-bit temperature format."""
    if len(data) < 2:
        raise ValueError("Temperaturdaten sind zu kurz.")

    first = data[0]
    second = data[1]

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
    """Decode standard integer-percent humidity."""
    if len(data) < 2:
        raise ValueError("Feuchtedaten sind zu kurz.")

    first = data[0]
    second = data[1]

    return {
        "value": second & 0x7F,
        "up05": bool(first & 0x80),
        "down05": bool(first & 0x40),
        "sensor_id": first & 0x0F,
        "average": bool(second & 0x80),
    }


def decode_humidity_decimal(data: bytes) -> dict[str, Any]:
    """Decode humidity with one decimal place."""
    if len(data) < 2:
        raise ValueError("Dezimal-Feuchtedaten sind zu kurz.")

    raw = ((data[0] & 0x03) << 8) | data[1]

    return {
        "value": raw / 10.0,
    }


def decode_sensor_status(data: bytes) -> dict[str, Any]:
    """Decode battery, event flag and 2-byte transmission counter."""
    if len(data) < 2:
        raise ValueError("Statusdaten sind zu kurz.")

    return {
        "battery_low": bool(data[0] & 0x80),
        "event_transmission": bool(data[0] & 0x40),
        "counter": ((data[0] & 0x3F) << 8) | data[1],
    }


def decode_wind(data: bytes) -> dict[str, Any]:
    """Decode current ID0B wind data."""
    if len(data) < 4:
        raise ValueError("Winddaten sind zu kurz.")

    first = data[0]

    direction_index = (first & 0xF0) >> 4
    direction_degrees = direction_index * 22.5

    wind_high_bit = (first & 0x02) >> 1
    gust_high_bit = first & 0x01

    wind_speed = ((wind_high_bit << 8) | data[1]) / 10.0
    gust_speed = ((gust_high_bit << 8) | data[2]) / 10.0
    last_transmit = data[3] * 2

    return {
        "wind_direction_degrees": direction_degrees,
        "wind_speed_mps": wind_speed,
        "gust_speed_mps": gust_speed,
        "last_transmit_seconds": last_transmit,
    }


def decode_rain(data: bytes) -> dict[str, Any]:
    """Decode the current ID08 rain-related values."""
    if len(data) < 8:
        raise ValueError("Regendaten sind zu kurz.")

    temperature = decode_temperature(data[0:2])

    rain_counter = (data[2] << 8) | data[3]

    event_raw = (data[4] << 8) | data[5]
    event_unit = (event_raw & 0xC000) >> 14
    event_value = event_raw & 0x3FFF

    position_raw = (data[0] & 0xC0) >> 6
    position_names = {
        0: "idle",
        1: "right",
        2: "left",
        3: "unknown",
    }

    return {
        "temperature": temperature,
        "rain_counter": rain_counter,
        "event_unit": event_unit,
        "event_value": event_value,
        "position": position_names.get(position_raw, "unknown"),
    }


def decode_door_window(data: bytes) -> dict[str, Any]:
    """Decode the current ID10 contact state."""
    if len(data) < 2:
        raise ValueError("Tür-/Fensterdaten sind zu kurz.")

    first = data[0]
    second = data[1]

    unit = (first & 0x60) >> 5
    elapsed = ((first & 0x1F) << 8) | second

    return {
        "open": bool(first & 0x80),
        "time_unit": unit,
        "elapsed_value": elapsed,
    }


def decode_current_values(
    sensor_type: int,
    payload: bytes,
) -> dict[str, Any]:
    """Decode currently relevant values for a known sensor family."""
    result: dict[str, Any] = {}

    if sensor_type in {0x01, 0x02, 0x03, 0x04, 0x06, 0x07, 0x0E, 0x11}:
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
        result["water_payload_byte"] = payload[6]

    elif sensor_type == 0x06:
        result["temperature"] = decode_temperature(payload[2:4])
        result["pool_temperature"] = decode_temperature(payload[4:6])
        result["humidity"] = decode_humidity(payload[6:8])

    elif sensor_type == 0x07:
        result["temperature_indoor"] = decode_temperature(payload[2:4])
        result["humidity_indoor"] = decode_humidity(payload[4:6])
        result["temperature_outdoor"] = decode_temperature(payload[6:8])
        result["humidity_outdoor"] = decode_humidity(payload[8:10])

    elif sensor_type == 0x08:
        result.update(decode_rain(payload[2:]))

    elif sensor_type == 0x0B:
        result["wind"] = decode_wind(payload[3:7])

    elif sensor_type == 0x0E:
        result["temperature"] = decode_temperature(payload[2:4])
        result["humidity"] = decode_humidity_decimal(payload[4:6])

    elif sensor_type == 0x10:
        result["contact"] = decode_door_window(payload[2:4])

    elif sensor_type == 0x11:
        result["temperature_1"] = decode_temperature(payload[2:4])
        result["humidity_1"] = decode_humidity(payload[4:6])
        result["temperature_2"] = decode_temperature(payload[6:8])
        result["humidity_2"] = decode_humidity(payload[8:10])
        result["temperature_3"] = decode_temperature(payload[10:12])
        result["humidity_3"] = decode_humidity(payload[12:14])
        result["temperature_indoor"] = decode_temperature(payload[14:16])
        result["humidity_indoor"] = decode_humidity(payload[16:18])

    return result


def decode_packet(packet: bytes) -> dict[str, Any]:
    """Decode one complete 64-byte gateway sensor packet."""
    if len(packet) != 64:
        raise ValueError(f"Sensorpaket muss 64 Bytes haben, hat {len(packet)}.")

    checksum_expected = sum(packet[:63]) & 0x7F
    checksum_actual = packet[63]

    package_header = packet[0]
    timestamp = int.from_bytes(packet[1:5], byteorder="big")
    packet_length = packet[5]
    sensor_id = packet[6:12].hex().upper()
    sensor_type = packet[6]

    payload_length = packet_length - 12

    if payload_length < 0 or payload_length > 52:
        raise ValueError(f"Ungültige Payload-Länge {payload_length}.")

    payload = packet[12 : 12 + payload_length]

    sensor_definition = SENSOR_TYPES.get(sensor_type)

    result: dict[str, Any] = {
        "package_header": f"0x{package_header:02X}",
        "packet_length": packet_length,
        "payload_length": payload_length,
        "sensor_id": sensor_id,
        "sensor_type": f"{sensor_type:02X}",
        "gateway_timestamp": timestamp,
        "gateway_timestamp_utc": format_timestamp(timestamp),
        "checksum_expected": checksum_expected,
        "checksum_actual": checksum_actual,
        "checksum_valid": checksum_expected == checksum_actual,
        "payload_hex": payload.hex(" "),
    }

    if sensor_definition is None:
        result["sensor_name"] = "unknown"
        result["decoded"] = {}
        return result

    result["sensor_name"] = sensor_definition["name"]
    result["expected_header"] = f"0x{sensor_definition['header']:02X}"
    result["expected_packet_length"] = sensor_definition["packet_length"]
    result["expected_payload_length"] = sensor_definition["payload_length"]

    result["header_valid"] = package_header == sensor_definition["header"]
    result["length_valid"] = (
        packet_length == sensor_definition["packet_length"]
        and payload_length == sensor_definition["payload_length"]
    )

    if result["checksum_valid"] and result["header_valid"] and result["length_valid"]:
        result["decoded"] = decode_current_values(
            sensor_type,
            payload,
        )
    else:
        result["decoded"] = {}

    return result


def decode_file(path: Path) -> list[dict[str, Any]]:
    """Decode one capture file."""
    data = path.read_bytes()

    if len(data) == 15:
        return [
            {
                "file": str(path),
                "kind": "boot_packet",
                "length": len(data),
                "hex": data.hex(" "),
            }
        ]

    if len(data) == 0 or len(data) % 64 != 0:
        return [
            {
                "file": str(path),
                "kind": "unknown",
                "length": len(data),
                "hex": data.hex(" "),
            }
        ]

    results = []

    for offset in range(0, len(data), 64):
        packet = data[offset : offset + 64]
        decoded = decode_packet(packet)
        decoded["file"] = str(path)
        decoded["packet_offset"] = offset
        decoded["kind"] = "sensor_packet"
        results.append(decoded)

    return results


def print_result(result: dict[str, Any]) -> None:
    """Print one decoded result."""
    print("=" * 72)
    print(f"Datei:       {result.get('file')}")
    print(f"Typ:         {result.get('kind')}")
    print(f"Länge:       {result.get('length', '-')}")

    if result.get("kind") != "sensor_packet":
        print(f"Hex:         {result.get('hex', '')}")
        return

    print(f"Offset:      {result.get('packet_offset')}")
    print(f"Sensor-ID:   {result.get('sensor_id')}")
    print(f"Sensor-Typ:  {result.get('sensor_type')}")
    print(f"Sensor:      {result.get('sensor_name')}")
    print(f"Header:      {result.get('package_header')}")
    print(f"Paketlänge:  {result.get('packet_length')}")
    print(f"Payload:     {result.get('payload_length')}")
    print(f"Timestamp:   {result.get('gateway_timestamp_utc')}")
    print(
        "CRC:         "
        f"{result.get('checksum_actual'):02X} "
        f"(erwartet {result.get('checksum_expected'):02X}) "
        f"gültig={result.get('checksum_valid')}"
    )
    print(f"Header OK:   {result.get('header_valid')}")
    print(f"Länge OK:    {result.get('length_valid')}")
    print(f"Payload-Hex: {result.get('payload_hex')}")

    decoded = result.get("decoded", {})
    print("Dekodiert:")

    for name, value in decoded.items():
        print(f"  {name}: {value}")


def main() -> int:
    capture_dir = Path(sys.argv[1] if len(sys.argv) > 1 else str(CAPTURE_DIR))

    if not capture_dir.exists():
        print(f"Capture-Verzeichnis fehlt: {capture_dir}")
        return 1

    files = sorted(
        capture_dir.glob("*.bin"),
        key=lambda path: path.stat().st_mtime,
    )

    if not files:
        print(f"Keine .bin-Dateien gefunden: {capture_dir}")
        return 1

    print(f"Capture-Verzeichnis: {capture_dir}")
    print(f"Binärdateien:        {len(files)}")

    for path in files:
        try:
            results = decode_file(path)

            for result in results:
                print_result(result)

        except Exception as exc:
            print("=" * 72)
            print(f"Datei: {path}")
            print(f"FEHLER: {exc}")

    print("=" * 72)
    print("Decode-Test abgeschlossen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
