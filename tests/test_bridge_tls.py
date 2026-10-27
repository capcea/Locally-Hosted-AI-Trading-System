"""Real local TLS/mTLS handshake. This is not an external broker connection test."""

import ipaddress
import secrets
import socket
import ssl
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from services.broker_bridge.app import BridgeConfig, server_for


def certificate_files(folder: Path) -> tuple[Path, Path, Path, Path, Path]:
    now = datetime.now(UTC)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Disposable broker bridge test CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    ca_path = folder / "ca.pem"
    ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    files: list[Path] = []
    for label, usage in (
        ("server", ExtendedKeyUsageOID.SERVER_AUTH),
        ("client", ExtendedKeyUsageOID.CLIENT_AUTH),
    ):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, label)])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([usage]), critical=False)
            .add_extension(
                x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )
        cert_path, key_path = folder / (label + ".pem"), folder / (label + ".key")
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_path.touch(mode=0o600)
        key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        files.extend((cert_path, key_path))
    return ca_path, files[0], files[1], files[2], files[3]


def test_real_mutual_tls_refuses_missing_client_certificate(tmp_path: Path) -> None:
    ca, server_cert, server_key, client_cert, client_key = certificate_files(tmp_path)
    token = secrets.token_urlsafe(32)
    token_path, signing_path = tmp_path / "token.txt", tmp_path / "signing.key"
    token_path.write_text(token)
    signing_path.write_bytes(Ed25519PrivateKey.generate().private_bytes_raw())
    token_path.chmod(0o600)
    signing_path.chmod(0o600)
    config = BridgeConfig(
        provider="MT5",
        authorized_demo_reads=True,
        connection_id=uuid4(),
        account_id="fixture",
        server="fixture-demo",
        authorization_token_file=token_path,
        signing_key_file=signing_path,
        tls_cert=server_cert,
        tls_key=server_key,
        client_ca=ca,
    )
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    assert port >= 1024
    server = server_for(config, port)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    context = ssl.create_default_context(cafile=str(ca))
    context.load_cert_chain(str(client_cert), str(client_key))
    url = f"https://127.0.0.1:{port}/health"
    try:
        deadline = time.monotonic() + 5
        while not server.started and time.monotonic() < deadline:
            thread.join(timeout=0.01)
        assert server.started
        with httpx.Client(verify=context, trust_env=False, timeout=3) as client:
            assert client.get(url).status_code == 403
            client.headers.update({"Authorization": "Bearer " + token})
            response = client.get(url)
            assert response.status_code == 200 and response.json()["external_execution"] is False
            assert client.post(url.replace("/health", "/orders"), json={}).status_code == 404
        with (
            httpx.Client(
                verify=ssl.create_default_context(cafile=str(ca)), trust_env=False, timeout=3
            ) as anonymous,
            pytest.raises(httpx.HTTPError),
        ):
            anonymous.get(url)
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
        assert not thread.is_alive()
