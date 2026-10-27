"""Explicit public identity contracts; credential inputs never appear in responses."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, SecretStr

from packages.domain.validation import Input as Input

Username = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_.-]{2,63}$")]
Password = Annotated[SecretStr, Field(min_length=15, max_length=128)]


class Credentials(Input):
    username: Username
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class Bootstrap(Input):
    username: Username
    display_name: Annotated[str, Field(min_length=1, max_length=120)]
    password: Password
    bootstrap_token: Annotated[SecretStr, Field(min_length=43, max_length=256)]


class UserCreate(Input):
    username: Username
    display_name: Annotated[str, Field(min_length=1, max_length=120)]
    password: Password
    role: Literal["OPERATOR", "VIEWER"]


class UserUpdate(Input):
    role: Literal["OPERATOR", "VIEWER"]
    active: bool


class UserView(Input):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: UUID
    username: str
    display_name: str
    role: Literal["OWNER", "OPERATOR", "VIEWER"]
    active: bool


class SessionView(Input):
    user: UserView
    state: Literal["ENROLLMENT", "MFA", "FULL"]
    csrf_token: str
    expires_at: datetime
    session_id: UUID


class Code(Input):
    code: Annotated[SecretStr, Field(min_length=6, max_length=80)]


class Reauthenticate(Code):
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class ChangePassword(Input):
    current_password: Annotated[SecretStr, Field(min_length=1, max_length=128)]
    new_password: Password


class Enrollment(Input):
    secret: str
    provisioning_uri: str


class RecoveryResult(Input):
    session: SessionView
    recovery_codes: list[str]


class BootstrapStatus(Input):
    initialized: bool
    setup_available: bool
