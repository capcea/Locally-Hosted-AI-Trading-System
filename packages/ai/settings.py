"""Worker-only connector configuration. Never reads the trading application's .env file."""

import ipaddress
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.ai.cloud_contracts import CLOUD_POLICY, OPENROUTER_URL
from packages.ai.contracts import Contract


def secret_path(logical: str, root: Path) -> Path:
    if not re.fullmatch(r"/run/secrets/ai-[a-z0-9_-]{1,64}", logical):
        raise ValueError("AI_SECRET_SCOPE_INVALID")
    path = root / Path(logical).name
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("AI_SECRET_SYMLINK_REFUSED")
    return path


class Endpoint(Contract):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    label: str = Field(min_length=1, max_length=100)
    url: str
    transport: Literal[
        "LOOPBACK", "PRIVATE_CONTAINER", "SSH_TUNNEL", "AUTHENTICATED_TLS", "OPENROUTER_PUBLIC"
    ]
    private_only_attested: bool = Field(default=True, strict=True)
    cloud_policy_version: Literal["openrouter-public-v1"] | None = None
    token_file: str | None = None
    ca_file: str | None = None
    client_cert_file: str | None = None
    client_key_file: str | None = None
    cost_per_million_input: str | None = None
    cost_per_million_output: str | None = None

    @model_validator(mode="after")
    def secure_destination(self) -> "Endpoint":
        if self.transport == "OPENROUTER_PUBLIC":
            if (
                self.url != OPENROUTER_URL
                or self.id != "openrouter"
                or self.private_only_attested
                or self.cloud_policy_version != CLOUD_POLICY
                or any((self.token_file, self.ca_file, self.client_cert_file, self.client_key_file))
            ):
                raise ValueError("AI_OPENROUTER_DESTINATION_REFUSED")
            return self
        if not self.private_only_attested or self.cloud_policy_version is not None:
            raise ValueError("AI_PRIVATE_ATTESTATION_REQUIRED")
        parsed = urlsplit(self.url)
        if (
            parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("Endpoint requires a bare origin without credentials")
        try:
            address = ipaddress.ip_address(parsed.hostname or "")
            if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
                address = address.ipv4_mapped
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError as exc:
            raise ValueError(
                "Use a pinned literal IP, never DNS or user-controlled resolution"
            ) from exc
        if address.is_multicast or address.is_link_local or address.is_unspecified:
            raise ValueError("Forbidden inference address")
        if port in {22, 80, 2375, 2376, 5432, 6379, 8000, 8080, 9000, 9001, 5173, 18000}:
            raise ValueError("Forbidden inference service port")
        if self.transport in {"LOOPBACK", "SSH_TUNNEL"}:
            if not address.is_loopback or parsed.scheme != "http" or port < 1024:
                raise ValueError("Local/tunnel inference requires non-privileged loopback HTTP")
        elif self.transport == "PRIVATE_CONTAINER":
            if (
                not address.is_private
                or address.is_loopback
                or parsed.scheme != "http"
                or port < 1024
            ):
                raise ValueError("Container inference requires an explicit private network address")
        elif parsed.scheme != "https" or not (self.token_file or self.client_cert_file):
            raise ValueError(
                "Remote inference requires authenticated TLS with verified server identity"
            )
        if bool(self.client_cert_file) != bool(self.client_key_file):
            raise ValueError("mTLS requires both client files")
        for name in (self.token_file, self.ca_file, self.client_cert_file, self.client_key_file):
            if name is not None and not re.fullmatch(r"/run/secrets/ai-[a-z0-9_-]{1,64}", name):
                raise ValueError("Connector secrets must use scoped AI secret mounts")
        for amount in (self.cost_per_million_input, self.cost_per_million_output):
            if amount is not None:
                from decimal import Decimal, InvalidOperation

                try:
                    value = Decimal(amount)
                except InvalidOperation as exc:
                    raise ValueError("Configured cost must be decimal") from exc
                if not value.is_finite() or value < 0:
                    raise ValueError("Configured cost must be a finite non-negative decimal")
        return self


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_", env_file=None, extra="ignore", hide_input_in_errors=True
    )
    database_url: SecretStr | None = None
    redis_url: SecretStr | None = None
    data_key: SecretStr | None = None
    data_key_file: str | None = None
    secret_root: Path = Path("/run/secrets")
    openrouter_enabled: bool = False
    endpoints: list[Endpoint] = Field(default_factory=list, max_length=10)
    egress_proxy: str | None = None
    global_concurrency: int = Field(default=2, ge=1, le=2)
    hourly_owner_limit: int = Field(default=40, ge=1, le=100)
    hourly_role_limit: int = Field(default=20, ge=1, le=40)
    metadata_limit: int = Field(default=1000, ge=1, le=10000)
    max_input_bytes: int = Field(default=12000, ge=1024, le=24000)
    max_output_bytes: int = Field(default=24000, ge=1024, le=32000)

    @field_validator("data_key")
    @classmethod
    def valid_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value:
            Fernet(value.get_secret_value().encode())
        return value

    @field_validator("egress_proxy")
    @classmethod
    def private_proxy(cls, value: str | None) -> str | None:
        if value is None:
            return None
        origin = urlsplit(value)
        address = ipaddress.ip_address(origin.hostname or "")
        if (
            origin.scheme != "http"
            or not address.is_private
            or address.is_link_local
            or address.is_unspecified
            or address.is_multicast
            or not origin.port
            or origin.port < 1024
            or origin.username
            or origin.password
            or origin.path not in {"", "/"}
            or origin.query
            or origin.fragment
        ):
            raise ValueError("AI proxy requires an explicit private literal origin")
        return value

    @model_validator(mode="after")
    def unique_endpoints(self) -> "GatewaySettings":
        public = [e for e in self.endpoints if e.transport == "OPENROUTER_PUBLIC"]
        if public and not self.openrouter_enabled:
            raise ValueError("AI_CLOUD_OPERATOR_OPT_IN_REQUIRED")
        if self.openrouter_enabled and not public:
            if len(self.endpoints) >= 10:
                raise ValueError("AI_ENDPOINT_LIMIT")
            self.endpoints.append(
                Endpoint(
                    id="openrouter",
                    label="OpenRouter · cloud public",
                    url=OPENROUTER_URL,
                    transport="OPENROUTER_PUBLIC",
                    private_only_attested=False,
                    cloud_policy_version=CLOUD_POLICY,
                )
            )
        if len({e.id for e in self.endpoints}) != len(self.endpoints):
            raise ValueError("Endpoint identifiers must be unique")
        if self.data_key_file and not re.fullmatch(
            r"/run/secrets/ai-[a-z0-9_-]{1,64}", self.data_key_file
        ):
            raise ValueError("AI key must use a scoped secret mount")
        return self

    def key_value(self) -> str:
        value = self.data_key.get_secret_value() if self.data_key else None
        if value is None and self.data_key_file:
            value = secret_path(self.data_key_file, self.secret_root).read_text().strip()
        if not value:
            raise ValueError("AI_NOT_CONFIGURED")
        return value

    def cipher(self) -> Fernet:
        return Fernet(self.key_value().encode())

    def endpoint(self, identifier: str) -> Endpoint:
        for endpoint in self.endpoints:
            if endpoint.id == identifier:
                return endpoint
        raise ValueError("AI_ENDPOINT_NOT_ALLOWLISTED")
