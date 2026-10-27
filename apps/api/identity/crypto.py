"""Standard password hashing and authenticated encryption; no custom cipher."""

import hashlib
import hmac
import secrets
from datetime import datetime

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet

PASSWORDS = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
# Used for unknown usernames to avoid the fast no-user path.
DUMMY_HASH = PASSWORDS.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return PASSWORDS.hash(password)


def password_matches(encoded: str, password: str) -> bool:
    try:
        return PASSWORDS.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def keyed_digest(key: str, purpose: str, value: str) -> str:
    return hmac.new(key.encode(), f"{purpose}:{value}".encode(), hashlib.sha256).hexdigest()


def encrypt_secret(key: str, secret: str) -> str:
    return Fernet(key.encode()).encrypt(secret.encode()).decode()


def decrypt_secret(key: str, encrypted: str) -> str:
    return Fernet(key.encode()).decrypt(encrypted.encode()).decode()


def accepted_totp_step(secret: str, code: str, now: datetime, last_step: int) -> int | None:
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    current = int(now.timestamp()) // 30
    totp = pyotp.TOTP(secret)
    for step in (current - 1, current, current + 1):
        if step > last_step and hmac.compare_digest(totp.at(step * 30), code):
            return step
    return None
