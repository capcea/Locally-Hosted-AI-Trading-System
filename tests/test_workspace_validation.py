"""Workspace trust-boundary regressions; mocked reads are unit tests, not service acceptance."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request

from apps.api.identity.dependencies import Principal
from apps.api.workspace import routes
from packages.campaigns.models import CampaignLineage, CampaignRuntime, ResearchCampaign


def lineage(payload: dict[str, Any]) -> tuple[Principal, Request, Any]:
    owner, campaign_id, evidence_id, decision_id, account = (uuid4() for _ in range(5))
    evidence = SimpleNamespace(
        id=evidence_id,
        owner_id=owner,
        campaign_id=campaign_id,
        kind="EVIDENCE",
        source="AI_GATEWAY",
        payload=payload,
        parent_id=uuid4(),
    )
    decision = SimpleNamespace(
        id=decision_id,
        owner_id=owner,
        campaign_id=campaign_id,
        parent_id=evidence_id,
        kind="EVALUATION",
        source="AI_GATEWAY",
        payload={
            "decision": "RESEARCH_CANDIDATE",
            "evidence_id": str(evidence_id),
            "reasons": ["Unit boundary test"],
            "observations": [],
            "unknown": [],
            "source": "AI_GATEWAY",
        },
    )
    campaign = SimpleNamespace(owner_id=owner, account_id=account)
    runtime = SimpleNamespace(owner_id=owner, state="COMPLETED")
    critique = SimpleNamespace(
        payload={
            "summary": "Unit boundary critique",
            "objections": ["Not acceptance evidence"],
            "source": "AI_GATEWAY",
        }
    )
    db = Mock()
    db.get.side_effect = lambda model, key: {
        (CampaignLineage, decision_id): decision,
        (CampaignLineage, evidence_id): evidence,
        (ResearchCampaign, campaign_id): campaign,
        (CampaignRuntime, campaign_id): runtime,
    }.get((model, key))
    db.scalar.return_value = critique
    return (
        cast(Principal, SimpleNamespace(db=db, user=SimpleNamespace(id=owner))),
        Mock(spec=Request),
        decision,
    )


@pytest.mark.parametrize("payload", [{}, {"experiment_id": "not-a-uuid"}])
def test_malformed_evidence_returns_bounded_refusal_instead_of_crashing_library(
    payload: dict[str, Any],
) -> None:
    identity, request, row = lineage(payload)
    with pytest.raises(HTTPException) as refused:
        routes.candidate_for(row.id, identity, request)
    assert refused.value.status_code == 409
    assert refused.value.detail == "WORKSPACE_LINEAGE_INVALID"


def test_persisted_cross_account_selection_is_not_shown_as_available(monkeypatch: Any) -> None:
    account = uuid4()
    selected = SimpleNamespace(id=uuid4(), decision_id=uuid4(), revision=1)
    monkeypatch.setattr(routes, "selection_for", lambda *args: selected)
    monkeypatch.setattr(routes, "candidate_for", lambda *args: ({"account_id": str(uuid4())}, None))
    result = routes.selection(account, Mock(), Mock())
    assert result["selection"]["available"] is False
    assert result["selection"]["candidate"] is None
    assert result["selection"]["reason"] == "WORKSPACE_ACCOUNT_VALIDATION_REQUIRED"


@pytest.mark.parametrize("change", ["plan", "account", "matching"])
def test_run_must_match_its_exact_account_and_campaign_plan(change: str, monkeypatch: Any) -> None:
    from test_campaigns import spec

    from packages.campaigns.contracts import ExperimentPlan, ResearchObjective
    from packages.research.models import ResearchResult

    experiment_id = uuid4()
    identity, request, row = lineage(
        {
            "experiment_id": str(experiment_id),
            "semantic_digest": "0" * 64,
            "artifact": {},
            "attempted_trials_owner": 1,
            "attempted_trials_campaign": 1,
            "source": "AI_GATEWAY",
        }
    )
    db = cast(Any, identity.db)
    campaign = db.get(ResearchCampaign, row.campaign_id)
    campaign.id = row.campaign_id
    data = {**spec(), "mode": "AI_GATEWAY"}
    data["template"]["source_account_id"] = str(campaign.account_id)
    campaign.specification = data
    template = ResearchObjective.model_validate(data).template
    evidence = db.get(CampaignLineage, row.parent_id)
    proposal_id = uuid4()
    original = ExperimentPlan(
        iteration=1,
        parent_proposal=proposal_id,
        experiment=template,
        source="AI_GATEWAY",
    )
    planned = SimpleNamespace(
        owner_id=identity.user.id,
        campaign_id=campaign.id,
        kind="PLAN",
        source="AI_GATEWAY",
        payload=original.model_dump(mode="json"),
        parent_id=proposal_id,
    )
    get = db.get.side_effect
    db.get.side_effect = lambda model, key: (
        planned
        if model is CampaignLineage and key == evidence.parent_id
        else SimpleNamespace(semantic_digest="0" * 64, artifact={})
        if model is ResearchResult
        else get(model, key)
    )
    critique = db.scalar.return_value
    db.scalar.side_effect = [
        critique,
        SimpleNamespace(),
        SimpleNamespace(state="SUCCEEDED"),
    ]
    run = SimpleNamespace(
        id=experiment_id,
        source_account_id=uuid4() if change == "account" else campaign.account_id,
        plan={
            **template.model_dump(mode="json"),
            **({"name": "Changed immutable plan"} if change == "plan" else {}),
        },
    )
    monkeypatch.setattr(routes, "run_for", lambda *args: run)
    with pytest.raises(HTTPException) as refused:
        routes.candidate_for(row.id, identity, request)
    assert refused.value.status_code == 409
    # Matching bindings pass lineage validation but this unit fixture is still in-sample.
    assert refused.value.detail == (
        "WORKSPACE_COMPLETE_VALIDATION_REQUIRED"
        if change == "matching"
        else "WORKSPACE_LINEAGE_INVALID"
    )
