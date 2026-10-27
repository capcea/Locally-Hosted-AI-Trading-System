"""Public Phase 3 API contracts contain no broker credential fields."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from packages.brokers.contracts import BrokerSnapshot
from packages.execution.contracts import Contract, SimState, SimulationModel, SymbolSpec


class ConnectionInput(Contract):
    broker_connection_id: UUID
    provider: Literal["SIMULATOR", "MT5", "CTRADER"]
    mode: Literal["SIMULATED", "DEMO_READ_ONLY"]
    external_account: str | None = Field(default=None, min_length=1, max_length=100)
    server: str | None = Field(default=None, min_length=1, max_length=120)
    public_key: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def safety(self) -> "ConnectionInput":
        if self.provider == "SIMULATOR":
            if self.mode != "SIMULATED" or any(
                (self.external_account, self.server, self.public_key)
            ):
                raise ValueError("Simulator cannot bind an external identity")
        elif self.mode != "DEMO_READ_ONLY" or not all(
            (self.external_account, self.server, self.public_key)
        ):
            raise ValueError("External demo observations require pinned identity and public key")
        return self


class ConnectionView(Contract):
    id: UUID
    account_id: UUID
    name: str
    provider: str
    mode: str
    status: str
    last_synced_at: AwareDatetime | None
    snapshot: BrokerSnapshot | None
    external_execution_enabled: Literal[False] = False


class RunInput(Contract):
    connection_id: UUID
    instrument_id: UUID
    name: str = Field(min_length=1, max_length=120)
    start_at: AwareDatetime
    spec: SymbolSpec
    assumptions: SimulationModel
    dataset_id: UUID | None = None


class RunView(Contract):
    id: UUID
    account_id: UUID
    connection_id: UUID
    instrument_id: UUID
    name: str
    sequence: int
    digest: str
    state: SimState
    source_binding: dict[str, object] | None
    source: Literal["SIMULATED"] = "SIMULATED"


class RunSummary(Contract):
    id: UUID
    name: str
    account_id: UUID
    connection_id: UUID
    instrument_id: UUID
    clock: AwareDatetime
    symbol: str
    account_mode: str
    order_count: int
    fill_count: int
    source: Literal["SIMULATED"] = "SIMULATED"


class ReplayInput(Contract):
    key: str = Field(min_length=8, max_length=80)
    decision_at: AwareDatetime
    start: AwareDatetime
    end: AwareDatetime
    limit: int = Field(default=100, ge=1, le=500)
