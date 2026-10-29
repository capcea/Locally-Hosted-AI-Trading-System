"""Literal-destination CONNECT proxy. No DNS, redirects, HTTP forwarding or arbitrary ports."""

import ipaddress
import json
import os
import select
import socket
import socketserver
import threading
import time


def destinations(raw: str) -> frozenset[tuple[str, int]]:
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) > 10:
        raise ValueError("AI_EGRESS_ALLOWLIST_INVALID")
    allowed: set[tuple[str, int]] = set()
    for row in rows:
        if "host" in row:
            if row != {
                "host": "openrouter.ai",
                "port": 443,
                "cloud_policy": "openrouter-public-v1",
            }:
                raise ValueError("AI_EGRESS_CLOUD_DESTINATION_REFUSED")
            allowed.add(("openrouter.ai", 443))
            continue
        address = ipaddress.ip_address(row["ip"])
        port = row["port"]
        if (
            address.is_link_local
            or address.is_loopback
            or address.is_multicast
            or address.is_unspecified
            or not isinstance(port, int)
            or port not in {443, 8443}
        ):
            raise ValueError("AI_EGRESS_DESTINATION_REFUSED")
        allowed.add((str(address), port))
    return frozenset(allowed)


def pinned_address(target: str, port: int) -> str:
    if target != "openrouter.ai":
        return str(ipaddress.ip_address(target.strip("[]")))
    addresses = {
        str(row[4][0]) for row in socket.getaddrinfo(target, port, type=socket.SOCK_STREAM)
    }
    if not addresses or any(
        not ipaddress.ip_address(a).is_global
        or ipaddress.ip_address(a).is_multicast
        or ipaddress.ip_address(a).is_reserved
        for a in addresses
    ):
        raise ValueError("AI_PUBLIC_DNS_ADDRESS_REFUSED")
    # Connect using this literal only: never resolve again after validation.
    return sorted(addresses)[0]


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], allowed: frozenset[tuple[str, int]]):
        self.allowed = allowed
        self.slots = threading.BoundedSemaphore(2)
        super().__init__(address, Handler)


class Handler(socketserver.StreamRequestHandler):
    server: Server

    def handle(self) -> None:
        if not self.server.slots.acquire(blocking=False):
            return
        try:
            self.connection.settimeout(5)
            line = self.rfile.readline(2048)
            parts = line.decode("ascii").strip().split()
            if len(parts) != 3 or parts[0] != "CONNECT" or parts[2] != "HTTP/1.1":
                self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                return
            target, port_text = parts[1].rsplit(":", 1)
            target = (
                target
                if target == "openrouter.ai"
                else str(ipaddress.ip_address(target.strip("[]")))
            )
            port = int(port_text)
            if (target, port) not in self.server.allowed:
                self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                return
            for _ in range(32):
                header = self.rfile.readline(2048)
                if header == b"\r\n":
                    break
            else:
                return
            with socket.create_connection(
                (pinned_address(target, port), port), timeout=3
            ) as upstream:
                self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                self.wfile.flush()
                deadline, transferred = time.monotonic() + 180, 0
                while time.monotonic() < deadline and transferred <= 2_000_000:
                    readable, _, _ = select.select([self.connection, upstream], [], [], 1)
                    for source in readable:
                        data = source.recv(16384)
                        if not data:
                            return
                        transferred += len(data)
                        (upstream if source is self.connection else self.connection).sendall(data)
        except (OSError, ValueError, UnicodeError):
            return  # No destination/header/output logging.
        finally:
            self.server.slots.release()


def main() -> None:
    allowed = destinations(os.environ.get("AI_EGRESS_DESTINATIONS", "[]"))
    with Server(("0.0.0.0", 8888), allowed) as server:  # noqa: S104 -- internal-only container
        server.serve_forever()


if __name__ == "__main__":
    main()
