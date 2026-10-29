"""Explicit public-cloud authorization, separate from private processing consent."""

import re
from decimal import Decimal
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator

from packages.ai.contracts import Contract

OPENROUTER_URL = "https://openrouter.ai/api/v1"
CLOUD_POLICY: Literal["openrouter-public-v1"] = "openrouter-public-v1"


class CloudPolicy(Contract):
    version: Literal["openrouter-public-v1"] = "openrouter-public-v1"
    upstream_provider: str = Field(pattern=r"^[a-z0-9][a-z0-9_/-]{1,79}$")
    input_usd_per_million: str = Field(default="1", pattern=r"^[0-9]{1,3}(\.[0-9]{1,6})?$")
    output_usd_per_million: str = Field(default="4", pattern=r"^[0-9]{1,3}(\.[0-9]{1,6})?$")
    request_usd: str = Field(default="0.01", pattern=r"^0\.[0-9]{1,6}$")
    daily_usd: str = Field(default="0.50", pattern=r"^[0-5](\.[0-9]{1,6})?$")
    acknowledged_public_cloud: Literal[True]
    acknowledged_upstream_processing: Literal[True]
    acknowledged_cost: Literal[True]
    acknowledged_provider_policy_limits: Literal[True]

    @field_validator(
        "acknowledged_public_cloud",
        "acknowledged_upstream_processing",
        "acknowledged_cost",
        "acknowledged_provider_policy_limits",
        mode="before",
    )
    @classmethod
    def explicit(cls, value: object) -> object:
        if value is not True:
            raise ValueError("AI_CLOUD_EXPLICIT_CONSENT_REQUIRED")
        return value

    @model_validator(mode="after")
    def bounds(self) -> "CloudPolicy":
        if not Decimal("0") < Decimal(self.request_usd) <= Decimal("0.10"):
            raise ValueError("AI_CLOUD_REQUEST_BUDGET_INVALID")
        if not Decimal(self.request_usd) <= Decimal(self.daily_usd) <= Decimal("5"):
            raise ValueError("AI_CLOUD_DAILY_BUDGET_INVALID")
        return self

    def routing(self) -> dict[str, object]:
        return {
            "only": [self.upstream_provider],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
            "zdr": True,
            "max_price": {
                "prompt": self.input_usd_per_million,
                "completion": self.output_usd_per_million,
                "request": "0",
                "image": "0",
                "audio": "0",
            },
        }


class CredentialInput(Contract):
    api_key: SecretStr = Field(min_length=16, max_length=4096, repr=False)

    @field_validator("api_key")
    @classmethod
    def token(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not re.fullmatch(r"[A-Za-z0-9._-]{16,4096}", raw):
            raise ValueError("AI_CREDENTIAL_INVALID")
        return value
