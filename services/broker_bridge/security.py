"""Connector-local credential storage and OAuth. This module is not in the research image."""

import json
import logging
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import httpx
from cryptography.fernet import Fernet
from pydantic import AwareDatetime, BaseModel, ConfigDict, SecretStr


def private_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise PermissionError("Private regular bounded file required")
    if sys.platform == "win32":
        check = Path(__file__).resolve().parents[1] / "windows" / "verify-private-acl.ps1"
        powershell = shutil.which("powershell.exe")
        if powershell is None:
            raise PermissionError("Windows ACL verifier unavailable")
        result = subprocess.run(  # noqa: S603 - fixed verifier script; path is a literal argument
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(check),
                "-Path",
                str(path.resolve()),
            ],
            capture_output=True,
            timeout=10,
        )
        if result.returncode:
            raise PermissionError("Windows private file ACL rejected")
    elif path.stat().st_mode & 0o077:
        raise PermissionError("Private file requires owner-only permissions")
    return path.read_bytes()


class Tokens(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    access: SecretStr
    refresh: SecretStr
    expires_at: AwareDatetime


class TokenVault:
    def __init__(self, path: Path, key_path: Path) -> None:
        self.path = path
        self.fernet = Fernet(private_file(key_path).strip())

    def read(self) -> Tokens:
        return Tokens.model_validate_json(self.fernet.decrypt(private_file(self.path), ttl=None))

    def write(self, tokens: Tokens) -> None:
        parent = self.path.parent
        if not parent.is_dir() or parent.is_symlink():
            raise PermissionError("Dedicated private credential directory required")
        if sys.platform != "win32" and parent.stat().st_mode & 0o077:
            raise PermissionError("Token directory requires owner-only permissions")
        data = {
            "access": tokens.access.get_secret_value(),
            "refresh": tokens.refresh.get_secret_value(),
            "expires_at": tokens.expires_at.isoformat(),
        }
        fd, temporary = tempfile.mkstemp(prefix=".token-", dir=parent)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(self.fernet.encrypt(json.dumps(data).encode()))
                file.flush()
                os.fsync(file.fileno())
            private_file(Path(temporary))
            os.replace(temporary, self.path)
        finally:
            if Path(temporary).exists():
                Path(temporary).unlink()


class OAuth:
    def __init__(
        self, client_id: str, client_secret: SecretStr, redirect: str, vault: TokenVault
    ) -> None:
        url = urlsplit(redirect)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError("Pinned HTTPS OAuth callback required")
        self.client_id, self.secret, self.redirect, self.vault = (
            client_id,
            client_secret,
            redirect,
            vault,
        )
        self.states: dict[str, float] = {}

    def start(self) -> str:
        self.states = {
            key: deadline for key, deadline in self.states.items() if deadline > time.monotonic()
        }
        if len(self.states) >= 10:
            raise PermissionError("OAuth pending-state quota reached")
        state = secrets.token_urlsafe(32)
        self.states[state] = time.monotonic() + 60
        return "https://id.ctrader.com/my/settings/openapi/grantingaccess/?" + urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect,
                "scope": "accounts",
                "product": "web",
                "state": state,
            }
        )

    def callback(self, code: str, state: str) -> None:
        from datetime import UTC, datetime, timedelta

        deadline = self.states.pop(state, None)
        if deadline is None or deadline < time.monotonic() or not 1 <= len(code) <= 1024:
            raise PermissionError("OAuth state expired, unknown or already used")
        data = self.exchange(
            {"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect}
        )
        self.vault.write(
            Tokens(
                access=SecretStr(str(data["accessToken"])),
                refresh=SecretStr(str(data["refreshToken"])),
                expires_at=datetime.now(UTC) + timedelta(seconds=int(str(data["expiresIn"]))),
            )
        )

    def exchange(self, fields: dict[str, str]) -> dict[str, object]:
        # Official GET carries secret parameters; never propagate URLs or exception details.
        logging.getLogger("httpx").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        try:
            with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
                response = client.get(
                    "https://openapi.ctrader.com/apps/token",
                    params={
                        **fields,
                        "client_id": self.client_id,
                        "client_secret": self.secret.get_secret_value(),
                    },
                )
                if response.status_code != 200 or len(response.content) > 16384:
                    raise PermissionError("OAuth exchange rejected")
                data = response.json()
                if (
                    not isinstance(data, dict)
                    or data.get("errorCode")
                    or not isinstance(data.get("expiresIn"), int)
                    or not 0 < data["expiresIn"] <= 31536000
                    or not all(
                        isinstance(data.get(k), str) and 8 <= len(data[k]) <= 4096
                        for k in ("accessToken", "refreshToken")
                    )
                ):
                    raise PermissionError("OAuth token response rejected")
                return data
        except (httpx.HTTPError, ValueError, KeyError):
            raise PermissionError("OAuth exchange failed; private details omitted") from None

    def current(self) -> Tokens:
        from datetime import UTC, datetime, timedelta

        tokens = self.vault.read()
        if tokens.expires_at <= datetime.now(UTC) + timedelta(seconds=60):
            data = self.exchange(
                {"grant_type": "refresh_token", "refresh_token": tokens.refresh.get_secret_value()}
            )
            tokens = Tokens(
                access=SecretStr(str(data["accessToken"])),
                refresh=SecretStr(str(data["refreshToken"])),
                expires_at=datetime.now(UTC) + timedelta(seconds=int(str(data["expiresIn"]))),
            )
            self.vault.write(tokens)
        return tokens
