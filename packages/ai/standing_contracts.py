"""Owner-scoped standing consent; never financial execution authority."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from packages.ai.contracts import Contract, Role

DataCategory = Literal["strategy", "experiment", "dataset", "documentation", "ai_artifact"]
Operation = Literal["INFER", "PROBE", "DISCOVER"]


class StandingInput(Contract):
    version: Literal["ai-standing-v1"] = "ai-standing-v1"
    connection_ids: list[UUID] = Field(min_length=1, max_length=20)
    roles: list[Role] = Field(min_length=1, max_length=4)
    data_categories: list[DataCategory] = Field(min_length=1, max_length=5)
    operations: list[Operation] = Field(min_length=1, max_length=3)
    request_usd: str = Field(pattern=r"^0\.[0-9]{1,6}$")
    daily_usd: str = Field(pattern=r"^[0-5](\.[0-9]{1,6})?$")
    monthly_usd: str = Field(pattern=r"^[0-9]{1,3}(\.[0-9]{1,6})?$")

    @model_validator(mode="after")
    def bounded(self) -> "StandingInput":
        for values in (self.connection_ids, self.roles, self.data_categories, self.operations):
            if len(values) != len(set(values)):
                raise ValueError("AI_STANDING_SCOPE_INVALID")
        if not (
            Decimal(0) < Decimal(self.request_usd) <= Decimal("0.10")
            and Decimal(self.request_usd) <= Decimal(self.daily_usd) <= Decimal(5)
            and Decimal(self.daily_usd) <= Decimal(self.monthly_usd) <= Decimal(150)
        ):
            raise ValueError("AI_STANDING_BUDGET_INVALID")
        return self
