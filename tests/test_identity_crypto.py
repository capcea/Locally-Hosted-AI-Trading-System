"""Cryptographic primitives and validation, independent of service acceptance."""

from datetime import UTC, datetime

import pyotp
import pytest
from cryptography.fernet import Fernet, InvalidToken
from pydantic import ValidationError

from apps.api.governance.schemas import AccountInput
from apps.api.identity.crypto import (
    accepted_totp_step,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    password_matches,
)


def test_argon2_unique_salts_and_password_verification() -> None:
    first, second = (hash_password("Fixture-only long passphrase") for _ in range(2))
    assert first.startswith("$argon2id$") and first != second
    assert password_matches(first, "Fixture-only long passphrase")
    assert not password_matches(first, "wrong")
    assert not password_matches("invalid hash", "wrong")


def test_totp_window_and_replay_are_explicit() -> None:
    secret = pyotp.random_base32()
    now = datetime.now(UTC)
    step = int(now.timestamp()) // 30
    totp = pyotp.TOTP(secret)
    assert accepted_totp_step(secret, totp.at(now), now, -1) == step
    assert accepted_totp_step(secret, totp.at(now), now, step) is None
    assert accepted_totp_step(secret, totp.at((step - 2) * 30), now, -1) is None
    assert accepted_totp_step(secret, "abcdef", now, -1) is None


def test_mfa_encryption_authenticates_ciphertext() -> None:
    key = Fernet.generate_key().decode()
    encrypted = encrypt_secret(key, "test secret")
    assert "test secret" not in encrypted
    assert decrypt_secret(key, encrypted) == "test secret"
    with pytest.raises(InvalidToken):
        decrypt_secret(Fernet.generate_key().decode(), encrypted)


def test_financial_inputs_reject_floating_point_and_live_mode() -> None:
    fields = {"kind": "accounts", "name": "Test", "currency": "USD", "initial_capital": "25000.01"}
    assert str(AccountInput.model_validate(fields).initial_capital) == "25000.01"
    for change in (
        {"initial_capital": 0.1},
        {"environment": "LIVE"},
        {"broker_password": "forbidden"},
    ):
        with pytest.raises(ValidationError):
            AccountInput.model_validate({**fields, **change})
