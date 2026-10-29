"""Versioned, bounded inference data. None of these schemas grants execution authority."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal["RESEARCH", "CODING", "CRITIC", "LIGHTWEIGHT"]
Provider = Literal["OLLAMA_NATIVE", "OLLAMA_OPENAI", "PRIVATE_OPENAI", "OPENROUTER"]
State = Literal["QUEUED", "RUNNING", "RETRY", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"]
Text = Annotated[str, Field(min_length=1, max_length=2000)]
References = Annotated[list[str], Field(max_length=20)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ResearchQuestion(Contract):
    schema_version: Literal[1] = 1
    question: str = Field(min_length=3, max_length=4000)


class MissingEvidenceReport(Contract):
    items: list[Text] = Field(min_length=1, max_length=20)


class HypothesisProposal(Contract):
    schema_version: Literal[1]
    title: Text
    hypothesis: Text
    test_plan: list[Text] = Field(min_length=1, max_length=12)
    evidence_refs: References
    missing_evidence: MissingEvidenceReport
    verified: Literal[False]


class EvidenceSummary(Contract):
    schema_version: Literal[1]
    summary: Text
    evidence_refs: References
    missing_evidence: MissingEvidenceReport
    verified: Literal[False]


class CritiqueReport(Contract):
    schema_version: Literal[1]
    summary: Text
    objections: list[Text] = Field(min_length=1, max_length=20)
    evidence_refs: References
    missing_evidence: MissingEvidenceReport
    certifies_strategy: Literal[False]


class CodeSuggestion(Contract):
    schema_version: Literal[1]
    summary: Text
    language: Literal["python", "text"]
    candidate_source: str = Field(min_length=1, max_length=16000)
    suggested_tests: list[Text] = Field(min_length=1, max_length=12)
    evidence_refs: References
    missing_evidence: MissingEvidenceReport
    executable: Literal[False]


Output = HypothesisProposal | EvidenceSummary | CritiqueReport | CodeSuggestion
OUTPUTS: dict[str, type[Contract]] = {
    "RESEARCH": HypothesisProposal,
    "CODING": CodeSuggestion,
    "CRITIC": CritiqueReport,
    "LIGHTWEIGHT": EvidenceSummary,
}


class Generation(Contract):
    context_tokens: int = Field(default=4096, ge=1024, le=32768)
    output_tokens: int = Field(default=768, ge=64, le=4096)
    temperature: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)
    top_p: float = Field(default=1, gt=0, le=1, allow_inf_nan=False)
    seed: int | None = Field(default=None, ge=0, le=2147483647)
    reasoning: Literal["DEFAULT", "DISABLED"] = "DEFAULT"
    max_seconds: int = Field(default=90, ge=5, le=180)


class ContextReference(Contract):
    kind: Literal["strategy", "experiment", "dataset", "documentation", "ai_artifact"]
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")


class PrivacyPolicy(Contract):
    cloud_processing_acknowledged: bool = Field(default=False, strict=True)
    remote_processing: bool = False
    account_context_remote: bool = False
    rights_confirmed: Literal[True]
    temporary_processing_minutes: int = Field(default=10, ge=1, le=30)
    structured_retention_hours: int = Field(default=1, ge=1, le=24)
    approved_processing: Literal[True]


class ConnectionInput(Contract):
    name: str = Field(min_length=1, max_length=100)
    endpoint_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    provider: Provider
    policy: PrivacyPolicy


class ModelInput(Contract):
    connection_id: UUID
    name: str = Field(min_length=1, max_length=150, pattern=r"^[A-Za-z0-9_./:@+-]+$")
    context_ceiling: int = Field(default=4096, ge=1024, le=32768)


class RouteInput(Contract):
    role: Role
    model_id: UUID
    fallback_ids: list[UUID] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def distinct(self) -> "RouteInput":
        if self.model_id in self.fallback_ids or len(set(self.fallback_ids)) != len(
            self.fallback_ids
        ):
            raise ValueError("Distinct model routing required")
        return self


class RequestInput(ResearchQuestion):
    cloud_cost_acknowledged: bool = Field(default=False, strict=True)
    key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    role: Role
    references: list[ContextReference] = Field(default_factory=list, max_length=10)
    parameters: Generation = Field(default_factory=Generation)
    allow_fallback: bool = False
    allow_remote: bool = False
    processing_acknowledged: Literal[True]
    retain_structured_output: Literal[True]


class ModelResponseMetadata(Contract):
    schema_version: Literal[1] = 1
    request_id: UUID
    model_id: UUID | None
    provider: Provider
    model_name: str
    model_digest: str | None
    provider_version: str | None = None
    quantization: str | None = None
    prompt_version: str
    input_refs: list[dict[str, str]]
    parameters: Generation
    started_at: datetime
    completed_at: datetime
    latency_ms: int = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    configured_cost_estimate: Decimal | None = Field(default=None, ge=0)
    usage_source: Literal["PROVIDER_REPORTED", "UNKNOWN"]
    output_sha256: str
    verified_evidence: Literal[False] = False
    trading_authority: Literal[False] = False


class AIJobView(Contract):
    id: UUID
    kind: str
    role: str
    state: State
    attempts: int
    cancel_requested: bool
    error: str | None
    created_at: datetime
    expires_at: datetime
    retain_until: datetime
    output: Output | dict[str, Any] | list[dict[str, Any]] | None = None
    metadata: ModelResponseMetadata | dict[str, Any] | None = None
    content_expired: bool = False
    context_available: bool = True
    model_output_verified_evidence: Literal[False] = False


class ActionKey(Contract):
    cloud_cost_acknowledged: bool = Field(default=False, strict=True)
    key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")


class EnabledInput(Contract):
    enabled: bool
