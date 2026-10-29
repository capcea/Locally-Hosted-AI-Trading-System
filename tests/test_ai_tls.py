"""Actual TLS identity/authentication checks; certificates and tokens are disposable."""

import ipaddress
import secrets
import ssl
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from packages.ai.providers import Adapter, ProviderFailure
from packages.ai.settings import Endpoint
from testing.ai_fixture import NAME, running_fixture


def test_actual_authenticated_tls_verifies_identity_and_refuses_untrusted_server(
    tmp_path: Path,
) -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Synthetic HTTP fixture CA")])
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(private, hashes.SHA256())
    )
    ca = tmp_path / "ai-ca"
    ca.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key = tmp_path / "ai-key"
    key.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    token = secrets.token_urlsafe(24)
    (tmp_path / "ai-token").write_text(token)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(ca, key)
    with running_fixture() as fixture:
        fixture.socket = tls.wrap_socket(fixture.socket, server_side=True)
        fixture.expected_authorization = "Bearer " + token
        endpoint = Endpoint(
            id="tls-fixture",
            label="Actual TLS synthetic fixture",
            url=fixture.url.replace("http:", "https:"),
            transport="AUTHENTICATED_TLS",
            private_only_attested=True,
            token_file="/run/secrets/ai-token",  # noqa: S106 -- scoped path; token is random
            ca_file="/run/secrets/ai-ca",
        )
        client = Adapter(endpoint, "PRIVATE_OPENAI", secret_root=tmp_path)
        try:
            assert client.discover()[0]["name"] == NAME
        finally:
            client.close()
        untrusted = Adapter(
            endpoint.model_copy(update={"ca_file": None}), "PRIVATE_OPENAI", secret_root=tmp_path
        )
        try:
            with pytest.raises(ProviderFailure, match="AI_PROVIDER_UNAVAILABLE"):
                untrusted.discover()
        finally:
            untrusted.close()
