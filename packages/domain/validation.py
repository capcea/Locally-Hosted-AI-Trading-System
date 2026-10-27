"""Shared bounded data input base; independent of API authentication and SDKs."""

from pydantic import BaseModel, ConfigDict


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
