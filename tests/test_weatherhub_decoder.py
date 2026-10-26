"""Test decoding of captured WeatherHub gateway payloads."""

import json
from pathlib import Path

from weatherhub_gateway_decoder import (
    BootPacket,
    GatewayPacket,
    WeatherHubDecoderError,
    decode_packet,
    decode_payload,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def decode_file_and_save(filepath: Path, output_name: str):
    """Decode a file and save the results as JSON."""
    body = filepath.read_bytes()
    packets = decode_payload(body)

    results = []
    for packet in packets:
        if isinstance(packet, GatewayPacket):
            results.append(
                {
                    "sensor_id": packet.sensor_id,
                    "sensor_type": packet.sensor_type,
                    "gateway_timestamp": packet.gateway_timestamp,
                    "decoded_values": packet.decoded_values,
                    "raw_hex": packet.raw_data.hex(),
                }
            )
        elif isinstance(packet, BootPacket):
            results.append(
                {
                    "type": "boot_packet",
                    "raw_hex": packet.raw_data.hex(),
                }
            )

    output_path = FIXTURES_DIR / output_name
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Gespeichert: {output_path}")
    print(f"Enthält {len(results)} dekodierte Pakete")

    return results


def test_decode_large_payload():
    """Decode the captured 684736-byte payload and analyze all blocks."""
    filepath = FIXTURES_DIR / "weatherhub_large_payload.bin"
    body = filepath.read_bytes()

    # Analysiere alle 64-Byte-Blöcke
    total_blocks = len(body) // 64
    valid_packets = 0
    crc_errors = 0
    other_errors = 0
    error_details = []

    for offset in range(0, len(body), 64):
        packet_bytes = body[offset : offset + 64]
        try:
            decode_packet(packet_bytes)  # Nur validieren, Wert nicht benötigt
            valid_packets += 1
        except WeatherHubDecoderError as exc:
            if "CRC" in str(exc):
                crc_errors += 1
            else:
                other_errors += 1
                if len(error_details) < 5:
                    error_details.append(f"  Offset {offset}: {exc}")

    print("\n=== Analyse der großen Payload ===")
    print(f"Gesamt: {total_blocks} Pakete")
    print(f"Gültig: {valid_packets}")
    print(f"CRC-Fehler: {crc_errors}")
    print(f"Andere Fehler: {other_errors}")

    if error_details:
        print("Beispiele für andere Fehler:")
        for detail in error_details:
            print(detail)

    # Der Decoder sollte die meisten Pakete verarbeiten können
    assert valid_packets > 10000  # Mindestens 10000 sollten gültig sein
    assert crc_errors <= 100  # Maximal 100 CRC-Fehler sind tolerierbar


def test_decode_single_packet():
    """Decode the captured 64-byte single packet."""
    filepath = FIXTURES_DIR / "weatherhub_single_packet.bin"
    body = filepath.read_bytes()

    packets = decode_payload(body)

    assert len(packets) == 1
    assert isinstance(packets[0], GatewayPacket)
    assert packets[0].decoded_values

    print("\n=== Einzelnes Paket ===")
    print(f"Sensor: {packets[0].sensor_id}")
    print(f"Typ: {packets[0].sensor_type:02X}")
    print(f"Werte: {packets[0].decoded_values}")


def test_generate_decoded_output():
    """Generate a JSON output file with all decoded values."""
    # Große Payload dekodieren und speichern
    large_file = FIXTURES_DIR / "weatherhub_large_payload.bin"
    results = decode_file_and_save(large_file, "weatherhub_large_payload_decoded.json")

    # Single packet dekodieren und speichern (Ergebnis nicht benötigt)
    single_file = FIXTURES_DIR / "weatherhub_single_packet.bin"
    decode_file_and_save(single_file, "weatherhub_single_packet_decoded.json")

    # Ein paar Statistiken anzeigen
    sensor_types = {}
    sensor_ids = {}
    for r in results:
        st = r["sensor_type"]
        sensor_types[st] = sensor_types.get(st, 0) + 1
        sensor_ids[r["sensor_id"]] = sensor_ids.get(r["sensor_id"], 0) + 1

    print("\n=== Sensor-Typen in der großen Payload ===")
    for st, count in sorted(sensor_types.items()):
        print(f"  ID{st:02X}: {count} Pakete")

    print(f"\n=== Eindeutige Sensoren: {len(sensor_ids)} ===")
    for sensor_id, count in sorted(sensor_ids.items()):
        print(f"  {sensor_id}: {count} Pakete")
