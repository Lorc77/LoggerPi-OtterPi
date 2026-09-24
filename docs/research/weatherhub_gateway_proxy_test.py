#!/usr/bin/env python3
"""Manueller WeatherHub-Gateway-Proxy-Testlistener.

Dieser Listener ist ausschließlich für einen kontrollierten Research-Test
vorgesehen.

Er:
- lauscht manuell auf 141.51.190.103:3778,
- nimmt HTTP-ähnliche PUT-Requests entgegen,
- speichert Header und Body unverändert,
- gibt die empfangenen Bytes als Hex aus,
- antwortet mit der bekannten Gateway-HTTP-200-Antwort,
- verändert keine System- oder Gateway-Konfiguration.

Kein systemd-Service, keine Batch-Erzeugung, keine Cloud-Weiterleitung.
"""

import socket
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LISTEN_HOST = "141.51.190.103"
LISTEN_PORT = 3778

OUTPUT_DIR = Path("/home/ZOOLOGY-observ/weatherhub_gateway_proxy_test_output")

MAX_HEADER_BYTES = 16 * 1024
MAX_BODY_BYTES = 64 * 1024
SOCKET_TIMEOUT_SECONDS = 10.0

# Für den künstlichen Test zunächst None.
# Vor einem echten Gateway-Test gemeinsam auf
# "141.51.190.121" ändern.
ALLOWED_CLIENT_IP: Optional[str] = "141.51.190.121"
# ALLOWED_CLIENT_IP: Optional[str] = None


def log(message: str) -> None:
    timestamp = datetime.now().astimezone().isoformat()
    print(f"[{timestamp}] {message}", flush=True)


def read_until_header_end(connection: socket.socket) -> bytes:
    """Liest bis zum Ende des HTTP-Headers."""
    data = bytearray()

    while b"\r\n\r\n" not in data:
        chunk = connection.recv(4096)

        if not chunk:
            break

        data.extend(chunk)

        if len(data) > MAX_HEADER_BYTES:
            raise ValueError("HTTP-Header ist zu groß.")

    return bytes(data)


def parse_content_length(headers: bytes) -> int:
    """Liest und validiert Content-Length aus den Headern."""
    header_text = headers.decode("iso-8859-1")

    for line in header_text.split("\r\n"):
        name, separator, value = line.partition(":")

        if separator and name.lower() == "content-length":
            try:
                length = int(value.strip())
            except ValueError as exc:
                raise ValueError("Content-Length ist ungültig.") from exc

            if length < 0 or length > MAX_BODY_BYTES:
                raise ValueError("Content-Length ist zu groß.")

            return length

    raise ValueError("Content-Length fehlt.")


def read_exact(
    connection: socket.socket,
    initial: bytes,
    length: int,
) -> bytes:
    """Liest exakt length Bytes einschließlich bereits gelesener Daten."""
    data = bytearray(initial)

    if len(data) > length:
        raise ValueError("Mehr Body-Daten als angekündigt empfangen.")

    while len(data) < length:
        chunk = connection.recv(min(4096, length - len(data)))

        if not chunk:
            raise ConnectionError("Verbindung vor vollständigem Body beendet.")

        data.extend(chunk)

    return bytes(data)


def build_gateway_response() -> bytes:
    """Erzeugt die bekannte 24-Byte-Antwort an das Gateway."""
    response_body = bytearray(
        (
            0x00,
            0x00,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x01,
            0x17,
            0x61,
            0xD4,
            0x80,
            0x00,
            0x00,
            0x00,
            0x01,
        )
    )

    timestamp = int(datetime.now(timezone.utc).timestamp())
    response_body[8:12] = struct.pack(">I", timestamp)

    headers = (
        b"HTTP/1.1 200 OK\r\n"
        b"Pragma: no-cache\r\n"
        b"Content-Length: 24\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Expires: -1\r\n"
        b"Connection: close\r\n"
        b"\r\n"
    )

    return headers + bytes(response_body)


def save_capture(
    headers: bytes,
    body: bytes,
) -> tuple[Path, Path]:
    """Speichert Header und Body unverändert."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")

    headers_path = OUTPUT_DIR / f"{timestamp}.headers"
    body_path = OUTPUT_DIR / f"{timestamp}.bin"

    headers_path.write_bytes(headers)
    body_path.write_bytes(body)

    return headers_path, body_path


def handle_connection(
    connection: socket.socket,
    client_address: tuple[str, int],
) -> None:
    """Verarbeitet genau eine Gateway-Verbindung."""
    client_ip, client_port = client_address

    if ALLOWED_CLIENT_IP is not None and client_ip != ALLOWED_CLIENT_IP:
        log(f"Verbindung abgelehnt: {client_ip}:{client_port}")
        return

    connection.settimeout(SOCKET_TIMEOUT_SECONDS)

    request = read_until_header_end(connection)
    header_end = request.find(b"\r\n\r\n")

    if header_end < 0:
        raise ValueError("HTTP-Headerabschluss fehlt.")

    headers = request[:header_end]
    body_prefix = request[header_end + 4 :]

    header_text = headers.decode("iso-8859-1")
    header_lines = header_text.split("\r\n")
    request_line = header_lines[0] if header_lines else ""

    log(f"Request von {client_ip}:{client_port}: {request_line}")

    for line in header_lines[1:]:
        if line:
            log(f"Header: {line}")

    if not request_line.startswith("PUT "):
        raise ValueError("Request verwendet nicht PUT.")

    content_length = parse_content_length(headers)
    body = read_exact(connection, body_prefix, content_length)

    headers_path, body_path = save_capture(headers, body)

    log(f"Body empfangen: {len(body)} Bytes")
    log(f"Header gespeichert: {headers_path}")
    log(f"Body gespeichert: {body_path}")
    log(f"Body-Hex: {body.hex(' ')}")

    connection.sendall(build_gateway_response())

    log("Gateway-HTTP-200-Antwort gesendet.")


def main() -> None:
    """Startet den manuellen Testlistener."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LISTEN_HOST, LISTEN_PORT))
        server.listen(5)

        log(f"Listener läuft auf {LISTEN_HOST}:{LISTEN_PORT}")
        log(f"Capture-Ausgabe: {OUTPUT_DIR}")
        log("Strg+C beendet den Listener.")

        while True:
            connection, client_address = server.accept()

            try:
                with connection:
                    handle_connection(
                        connection,
                        client_address,
                    )
            except Exception as exc:
                log(f"Verarbeitungsfehler von {client_address}: {exc}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Listener beendet.")
