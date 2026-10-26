"""HTTP Listener for WeatherHub Gateway payloads.

Listens for incoming HTTP PUT requests from configured gateways,
reads the binary payload, decodes it using the payload decoder,
and passes the decoded packets to a callback.
"""

import logging
import socket
import struct
import threading
import urllib.request
from datetime import datetime, timezone
from typing import Callable, List, Optional, Set, Union

from weatherhub_gateway_decoder import (
    BootPacket,
    GatewayPacket,
    WeatherHubDecoderError,
    decode_payload,
)

LOGGER = logging.getLogger(__name__)

MAX_HEADER_BYTES = 16 * 1024
MAX_BODY_BYTES = 64 * 1024
SOCKET_TIMEOUT_SECONDS = 10.0


class WeatherHubGatewayListener(threading.Thread):
    """Background thread running a TCP server to receive WeatherHub Gateway payloads."""

    def __init__(
        self,
        host: str,
        port: int,
        allowlist: Set[str],
        on_packets_received: Callable[[List[Union[BootPacket, GatewayPacket]]], None],
        cloud_forward_enabled: bool = False,
    ) -> None:
        super().__init__(name="WeatherHubGatewayListener")
        self.host = host
        self.port = port
        self.allowlist = allowlist
        self.on_packets_received = on_packets_received
        self.cloud_forward_enabled = cloud_forward_enabled

        self._stop_event = threading.Event()
        self._server_socket: Optional[socket.socket] = None

    def stop(self) -> None:
        """Request the listener thread to stop and wait for it to finish."""
        self._stop_event.set()

    def run(self) -> None:
        """Main listener loop."""
        LOGGER.info(
            "Starting WeatherHubGatewayListener on %s:%s (allowlist: %s)",
            self.host,
            self.port,
            ",".join(sorted(self.allowlist)) if self.allowlist else "NONE (ALLOW ALL)",
        )

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self._server_socket = server
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self.host, self.port))
                server.listen(5)
                # Timeout allows periodic checking of _stop_event
                server.settimeout(1.0)

                while not self._stop_event.is_set():
                    try:
                        connection, client_address = server.accept()
                    except socket.timeout:
                        continue
                    except Exception as exc:
                        if not self._stop_event.is_set():
                            LOGGER.error("WeatherHubGatewayListener accept failed: %s", exc)
                        continue

                    try:
                        with connection:
                            self._handle_connection(connection, client_address)
                    except Exception as exc:
                        LOGGER.warning("Error handling connection from %s: %s", client_address, exc)

        except Exception as exc:
            LOGGER.exception("WeatherHubGatewayListener failed: %s", exc)
        finally:
            self._server_socket = None
            LOGGER.info("WeatherHubGatewayListener stopped.")

    def _handle_connection(self, connection: socket.socket, client_address: tuple[str, int]) -> None:
        client_ip, client_port = client_address

        # Check IP Allowlist
        if self.allowlist and client_ip not in self.allowlist:
            LOGGER.warning("Connection rejected from %s:%s (IP not in allowlist)", client_ip, client_port)
            return

        connection.settimeout(SOCKET_TIMEOUT_SECONDS)

        # Read HTTP headers
        request = self._read_until_header_end(connection)
        header_end = request.find(b"\r\n\r\n")
        if header_end < 0:
            raise ValueError("HTTP header end missing.")

        headers = request[:header_end]
        body_prefix = request[header_end + 4 :]

        header_text = headers.decode("iso-8859-1")
        header_lines = header_text.split("\r\n")
        request_line = header_lines[0] if header_lines else ""

        if not request_line.startswith("PUT "):
            raise ValueError(f"Request does not use PUT: {request_line}")

        # Optional: Extract HTTP_IDENTIFY for logging and forwarding
        identify = next((line for line in header_lines if line.lower().startswith("http_identify:")), None)
        identify_value = ""
        if identify:
            identify_value = identify[len("HTTP_IDENTIFY:"):].strip()
            LOGGER.debug("Gateway identify: %s", identify_value)
        else:
            LOGGER.debug("Gateway identify header missing")

        content_length = self._parse_content_length(header_text)
        body = self._read_exact(connection, body_prefix, content_length)

        # Cloud Forwarding (asynchronous)
        if self.cloud_forward_enabled:
            self._forward_to_cloud(identify_value, body)

        # Decode payload
        try:
            packets = decode_payload(body)
        except WeatherHubDecoderError as exc:
            raise ValueError(f"Payload decoding failed: {exc}") from exc

        # Pass decoded packets to callback
        if packets:
            try:
                self.on_packets_received(packets)
            except Exception as exc:
                LOGGER.error("Error in on_packets_received callback: %s", exc)

        # Gateway requires this specific binary HTTP 200 response to confirm receipt
        connection.sendall(self._build_gateway_response())

    def _forward_to_cloud(self, identify_value: str, body: bytes) -> None:
        """Asynchronously forwards the raw payload to the WeatherHub cloud."""
        def _do_forward():
            try:
                url = "http://www.data199.com/gateway/put"
                headers = {
                    "Host": "www.data199.com",
                    "Connection": "close",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(body)),
                }
                if identify_value:
                    headers["HTTP_IDENTIFY"] = identify_value

                request = urllib.request.Request(url, data=body, headers=headers, method="PUT")
                with urllib.request.urlopen(request, timeout=SOCKET_TIMEOUT_SECONDS) as response:
                    status = response.getcode()
                    if status != 200:
                        LOGGER.warning("Cloud-Forward returned HTTP %s", status)
                    else:
                        LOGGER.debug("Cloud-Forward successful.")
            except Exception as exc:
                LOGGER.warning("Cloud-Forward failed: %s", exc)

        thread = threading.Thread(target=_do_forward, name="CloudForwarderThread")
        thread.daemon = True
        thread.start()

    def _read_until_header_end(self, connection: socket.socket) -> bytes:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = connection.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > MAX_HEADER_BYTES:
                raise ValueError("HTTP header is too large.")
        return bytes(data)

    def _parse_content_length(self, header_text: str) -> int:
        for line in header_text.split("\r\n"):
            name, separator, value = line.partition(":")
            if separator and name.lower() == "content-length":
                try:
                    length = int(value.strip())
                except ValueError as exc:
                    raise ValueError("Content-Length is invalid.") from exc

                if length < 0 or length > MAX_BODY_BYTES:
                    raise ValueError("Content-Length is too large.")
                return length
        raise ValueError("Content-Length is missing.")

    def _read_exact(self, connection: socket.socket, initial: bytes, length: int) -> bytes:
        data = bytearray(initial)
        if len(data) > length:
            raise ValueError("Received more body data than announced.")

        while len(data) < length:
            chunk = connection.recv(min(4096, length - len(data)))
            if not chunk:
                raise ConnectionError("Connection closed before body was completely received.")
            data.extend(chunk)
        return bytes(data)

    def _build_gateway_response(self) -> bytes:
        """Build the required 24-byte binary response with current timestamp."""
        response_body = bytearray(
            (
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
                0x17, 0x61, 0xD4, 0x80, 0x00, 0x00, 0x00, 0x01,
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
