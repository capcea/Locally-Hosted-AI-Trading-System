"""Versioned untrusted proposals and finite owner-authorized research domains."""

from typing import Any, Literal, get_args, get_origin
from uuid import UUID

from pydantic import Field, StrictInt, ValidationInfo, field_validator, model_validator

from packages.ai.contracts import Contract
from packages.research.contracts import ExperimentInput, Parameters, StrategyName
from packages.research.strategies import definition

Source = Literal["SYNTHETIC_FIXTURE", "AI_GATEWAY"]
ResearchCampaignState = Literal[
    "DRAFT",
    "AWAITING_APPROVAL",
    "QUEUED",
    "PLANNING",
    "TESTING",
    "EVALUATING",
    "CRITIQUING",
    "READY_FOR_NEXT_ITERATION",
    "COMPLETED",
    "STOPPED",
    "FAILED",
    "UNKNOWN",
]


class CampaignParameters(Parameters):
    @field_validator("*", mode="before")
    @classmethod
    def exact_types(cls, value: Any, info: ValidationInfo) -> Any:
        kind = cls.model_fields[info.field_name or ""].annotation
        if kind in (int, bool) and type(value) is not kind:
            raise ValueError("EXACT_PARAMETER_TYPE_REQUIRED")
        return value


class CampaignContract(Contract):
    @field_validator("*", mode="before")
    @classmethod
    def exact_literal_types(cls, value: Any, info: ValidationInfo) -> Any:
        annotation = cls.model_fields[info.field_name or ""].annotation
        if get_origin(annotation) is Literal and type(value) is not type(get_args(annotation)[0]):
            raise ValueError("EXACT_CAMPAIGN_LITERAL_TYPE_REQUIRED")
        return value


class Budgets(CampaignContract):
    candidate_proposals: StrictInt = Field(default=8, ge=1, le=8)
    experiments: StrictInt = Field(default=12, ge=1, le=12)
    iterations: StrictInt = Field(default=2, ge=1, le=2)
    active_experiments: Literal[1] = 1
    runtime_seconds: StrictInt = Field(default=1800, ge=60, le=7200)
    artifact_bytes: StrictInt = Field(default=201326592, ge=16777216, le=201326592)
    lineage_bytes: StrictInt = Field(default=524288, ge=65536, le=524288)


class EvaluationMethodology(CampaignContract):
    version: Literal["campaign-evaluation-v1"] = "campaign-evaluation-v1"
    minimum_trades: StrictInt = Field(default=30, ge=10, le=10000)
    maximum_drawdown_fraction: str = Field(default="0.03", pattern=r"^0\.[0-9]{1,6}$")
    stop_on_insufficient_evidence: Literal[True] = True
    independent_validation_required: Literal[True] = True


class ResearchObjective(CampaignContract):
    schema_version: Literal[1] = 1
    title: str = Field(min_length=3, max_length=120)
    objective: str = Field(min_length=10, max_length=2000)
    mode: Source
    template: ExperimentInput
    search_space: list[CampaignParameters] = Field(min_length=1, max_length=8)
    budgets: Budgets = Field(default_factory=Budgets)
    evaluation: EvaluationMethodology = Field(default_factory=EvaluationMethodology)
    research_role: Literal["RESEARCH"] = "RESEARCH"
    critic_role: Literal["CRITIC"] = "CRITIC"
    seed: StrictInt = Field(default=7, ge=0, le=2147483647)
    acknowledged_owner_handoffs: Literal[True]
    acknowledged_no_promotion: Literal[True]

    @model_validator(mode="after")
    def bounded(self) -> "ResearchObjective":
        plan = self.template
        if plan.phase == "FINAL_HOLDOUT" or plan.holdout_release_id is not None:
            raise ValueError("CAMPAIGN_FINAL_HOLDOUT_PROHIBITED")
        if plan.strategy_digest != definition(plan.strategy)["digest"]:
            raise ValueError("CAMPAIGN_REVIEWED_VERSION_REQUIRED")
        if (
            self.budgets.runtime_seconds < 3 * plan.max_seconds
            or self.budgets.artifact_bytes
            < 3 * 16 * 1024 * 1024 + self.budgets.lineage_bytes + 8192
        ):
            raise ValueError("CAMPAIGN_SINGLE_EXPERIMENT_CANNOT_FIT_BUDGET")
        if len(plan.parameters) != 1:
            raise ValueError("CAMPAIGN_ONE_PARAMETER_CANDIDATE_PER_EXPERIMENT")
        if plan.phase != "DISCOVERY" and (
            self.budgets.iterations != 1 or len(self.search_space) != 1
        ):
            raise ValueError("NO_ADAPTIVE_TUNING_ON_EVALUATION_DATA")
        if len({p.model_dump_json() for p in self.search_space}) != len(self.search_space):
            raise ValueError("DUPLICATE_AUTHORIZED_PARAMETER_CANDIDATE")
        for parameters in self.search_space:
            # Reuse Phase5's row/trial/fold/time/purge validation for EVERY allowed candidate.
            ExperimentInput.model_validate({**plan.model_dump(), "parameters": [parameters]})
        return self


class StrategyHypothesis(CampaignContract):
    schema_version: Literal[1] = 1
    title: str = Field(min_length=3, max_length=120)
    rationale: str = Field(min_length=10, max_length=2000)
    strategy: StrategyName
    strategy_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source: Source
    verified: Literal[False] = False


class ParameterCandidate(CampaignContract):
    schema_version: Literal[1] = 1
    strategy: StrategyName
    strategy_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameters: CampaignParameters
    source: Source


class ExperimentPlan(CampaignContract):
    schema_version: Literal[1] = 1
    iteration: int = Field(ge=1, le=2)
    parent_proposal: UUID
    experiment: ExperimentInput
    methodology: Literal["campaign-evaluation-v1"] = "campaign-evaluation-v1"
    source: Source


class ExperimentEvidence(CampaignContract):
    schema_version: Literal[1] = 1
    experiment_id: UUID
    semantic_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact: dict[str, Any]
    attempted_trials_owner: int = Field(ge=1)
    attempted_trials_campaign: int = Field(ge=1)
    source: Source


class EvaluationDecision(CampaignContract):
    schema_version: Literal[1] = 1
    decision: Literal[
        "INSUFFICIENT_EVIDENCE", "REJECTED", "NEEDS_MORE_VALIDATION", "RESEARCH_CANDIDATE"
    ]
    reasons: list[str] = Field(min_length=1, max_length=30)
    observations: list[dict[str, Any]] = Field(max_length=24)
    unknown: list[str] = Field(max_length=30)
    evidence_id: UUID
    source: Source
    paper_eligible: Literal[False] = False
    trading_authority: Literal[False] = False


class Critique(CampaignContract):
    schema_version: Literal[1] = 1
    summary: str = Field(min_length=3, max_length=2000)
    objections: list[str] = Field(min_length=1, max_length=20)
    source: Source
    certifies_strategy: Literal[False] = False


class FollowUpProposal(CampaignContract):
    schema_version: Literal[1] = 1
    tested_plan: UUID
    evaluation: UUID
    critique: UUID
    justified: bool
    reason: str = Field(min_length=3, max_length=2000)
    allowed_next_candidate: ParameterCandidate | None
    source: Source


class ResearchLineage(CampaignContract):
    schema_version: Literal[1] = 1
    id: UUID
    parent_id: UUID | None
    sequence: int = Field(ge=1)
    kind: str
    payload: dict[str, Any]
    previous_digest: str
    digest: str
    source: Source


class CreateCampaign(CampaignContract):
    key: str = Field(min_length=16, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    objective: ResearchObjective


class Approval(CampaignContract):
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    acknowledged_bounded_research: Literal[True]
    acknowledged_no_promotion: Literal[True]


class CampaignAction(CampaignContract):
    action: Literal["REQUEST_APPROVAL", "PAUSE", "RESUME", "CANCEL"]


class GatewayAction(CampaignContract):
    cloud_cost_acknowledged: bool = Field(default=False, strict=True)
    role: Literal["RESEARCH", "CRITIC"]
    allow_remote: bool = False
    processing_acknowledged: Literal[True]
    retain_structured_output: Literal[True]


class PlanReview(CampaignContract):
    plan_id: UUID
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    acknowledged_exact_plan: Literal[True]
