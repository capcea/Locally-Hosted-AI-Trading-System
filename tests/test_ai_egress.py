"""Actual proxy refusal, not a claim of deployed network/firewall acceptance."""

import socket
import threading

import pytest

from services.ai_egress.proxy import Server, destinations


def test_connect_proxy_denies_any_unlisted_target_and_non_connect_method() -> None:
    with Server(("127.0.0.1", 0), frozenset()) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for request in (
                b"CONNECT 127.0.0.1:5432 HTTP/1.1\r\n\r\n",
                b"GET http://169.254.169.254/ HTTP/1.1\r\n\r\n",
            ):
                with socket.create_connection(
                    ("127.0.0.1", server.server_address[1]), timeout=2
                ) as client:
                    client.sendall(request)
                    assert client.recv(1024).startswith(b"HTTP/1.1 403")
        finally:
            server.shutdown()
            thread.join(3)


@pytest.mark.parametrize(
    "raw",
    [
        '[{"ip":"169.254.169.254","port":443}]',
        '[{"ip":"127.0.0.1","port":443}]',
        '[{"ip":"example.com","port":443}]',
        '[{"ip":"192.0.2.1","port":5432}]',
    ],
)
def test_connect_proxy_refuses_dns_metadata_and_service_ports(raw: str) -> None:
    with pytest.raises(ValueError):
        destinations(raw)
