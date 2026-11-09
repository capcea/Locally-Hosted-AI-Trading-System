"""Actual product reads, eligibility refusals and immutable configuration."""

from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_password_auth_integration import bootstrap
from test_password_auth_integration import password_system as password_system
from test_phase1_integration import System

from packages.campaigns.models import CampaignLineage, CampaignRuntime, ResearchCampaign
from packages.persistence.models import TradingAccount
from packages.research.selections import StrategySelection

pytestmark = pytest.mark.isolated_services


def test_password_workspace_empty_library_and_unavailable_strategy_cannot_start(
    password_system: System,
) -> None:
    system = password_system
    bootstrap(system)
    library = system.client.get("/api/v1/workspace/library")
    assert library.status_code == 200
    assert library.json() == {
        "items": [],
        "has_more": False,
        "unavailable_count": 0,
        "external_execution_authorized": False,
    }
    account = system.account()
    path = f"/api/v1/workspace/accounts/{account['id']}"
    assert system.client.get(path + "/strategy").json()["selection"] is None
    assert system.post(path + "/strategy", {"decision_id": str(uuid4())}).status_code == 404
    assert (
        system.post(path + "/strategy", {"decision_id": str(uuid4()), "mode": "LIVE"}).status_code
        == 422
    )
    assert (
        system.post(
            path + "/simulate", {"key": uuid4().hex, "acknowledged_historical_simulation": True}
        ).status_code
        == 409
    )
    assert system.client.get(f"/api/v1/workspace/accounts/{uuid4()}/strategy").status_code == 404
    assert system.client.get("/api/v1/safety").json()["executor_capability"] == "DENY_ALL"


def test_synthetic_claim_and_direct_stale_selection_never_become_eligible(
    password_system: System,
) -> None:
    system = password_system
    bootstrap(system)
    account = system.account()
    app = cast(FastAPI, system.client.app)
    with app.state.store.session() as db, db.begin():
        owned = db.get(TradingAccount, UUID(account["id"]))
        campaign = ResearchCampaign(
            owner_id=owned.owner_id,
            account_id=owned.id,
            key=uuid4().hex,
            digest="0" * 64,
            specification={"source": "SYNTHETIC_TEST_FIXTURE"},
        )
        db.add(campaign)
        db.flush()
        row = CampaignLineage(
            owner_id=owned.owner_id,
            campaign_id=campaign.id,
            sequence=1,
            kind="EVALUATION",
            source="SYNTHETIC_FIXTURE",
            payload={"decision": "RESEARCH_CANDIDATE"},
            previous_digest="0" * 64,
            digest="0" * 64,
        )
        db.add(row)
        db.flush()
        decision = row.id
        # Adversarial persisted configuration: reads must still recheck eligibility.
        choice = StrategySelection(
            owner_id=owned.owner_id,
            account_id=owned.id,
            decision_id=decision,
            revision=1,
            mode="SIMULATED",
        )
        db.add(choice)
        db.flush()
        identifier = choice.id
    path = f"/api/v1/workspace/accounts/{account['id']}"
    assert system.post(path + "/strategy", {"decision_id": str(decision)}).status_code == 409
    assert system.client.get("/api/v1/workspace/library").json()["items"] == []
    status = system.client.get(path + "/strategy").json()
    assert status["selection"]["available"] is False
    assert status["external_execution_authorized"] is False
    assert (
        system.post(
            path + "/simulate", {"key": uuid4().hex, "acknowledged_historical_simulation": True}
        ).status_code
        == 409
    )
    with app.state.store.session() as db:
        with pytest.raises(DBAPIError):
            db.execute(
                text("UPDATE workspace_strategy_selections SET mode='LIVE' WHERE id=:id"),
                {"id": identifier},
            )
        db.rollback()


@pytest.mark.parametrize("state", ["CRITIQUING", "COMPLETED"])
def test_candidate_claim_without_completed_critique_is_not_selectable(
    password_system: System, state: str
) -> None:
    system = password_system
    bootstrap(system)
    account = system.account()
    app = cast(FastAPI, system.client.app)
    with app.state.store.session() as db, db.begin():
        owned = db.get(TradingAccount, UUID(account["id"]))
        campaign = ResearchCampaign(
            owner_id=owned.owner_id,
            account_id=owned.id,
            key=uuid4().hex,
            digest="0" * 64,
            specification={"test_only_adversarial_claim": True},
        )
        db.add(campaign)
        db.flush()
        db.add(CampaignRuntime(campaign_id=campaign.id, owner_id=owned.owner_id, state=state))
        # Deliberately inconsistent persisted claim: never a genuine model acceptance result.
        row = CampaignLineage(
            owner_id=owned.owner_id,
            campaign_id=campaign.id,
            sequence=1,
            kind="EVALUATION",
            source="AI_GATEWAY",
            payload={"decision": "RESEARCH_CANDIDATE"},
            previous_digest="0" * 64,
            digest="0" * 64,
        )
        db.add(row)
        db.flush()
        identifier = row.id
    refused = system.post(
        f"/api/v1/workspace/accounts/{account['id']}/strategy",
        {"decision_id": str(identifier)},
    )
    assert refused.status_code == 409
    assert refused.json()["detail"] == "WORKSPACE_COMPLETED_REVIEW_REQUIRED"
    library = system.client.get("/api/v1/workspace/library").json()
    assert library["items"] == []
    assert library["unavailable_count"] == 1


@pytest.mark.parametrize("shape", ["missing", "invalid_uuid", "unlinked"])
def test_invalid_lineage_is_refused_without_breaking_the_entire_library(
    password_system: System, shape: str
) -> None:
    from test_campaigns import spec

    from packages.campaigns.contracts import Critique, EvaluationDecision

    system = password_system
    bootstrap(system)
    account = system.account()
    app = cast(FastAPI, system.client.app)
    with app.state.store.session() as db, db.begin():
        owned = db.get(TradingAccount, UUID(account["id"]))
        objective = {**spec(), "mode": "AI_GATEWAY"}
        objective["template"]["source_account_id"] = str(owned.id)
        campaign = ResearchCampaign(
            owner_id=owned.owner_id,
            account_id=owned.id,
            key=uuid4().hex,
            digest="0" * 64,
            specification=objective,
        )
        db.add(campaign)
        db.flush()
        db.add(CampaignRuntime(campaign_id=campaign.id, owner_id=owned.owner_id, state="COMPLETED"))
        payload = (
            {}
            if shape == "missing"
            else {
                "experiment_id": "invalid" if shape == "invalid_uuid" else str(uuid4()),
                "semantic_digest": "0" * 64,
                "artifact": {},
                "attempted_trials_owner": 1,
                "attempted_trials_campaign": 1,
                "source": "AI_GATEWAY",
            }
        )
        evidence = CampaignLineage(
            owner_id=owned.owner_id,
            campaign_id=campaign.id,
            sequence=1,
            kind="EVIDENCE",
            source="AI_GATEWAY",
            payload=payload,
            previous_digest="0" * 64,
            digest="0" * 64,
        )
        db.add(evidence)
        db.flush()
        decision = CampaignLineage(
            owner_id=owned.owner_id,
            campaign_id=campaign.id,
            parent_id=evidence.id,
            sequence=2,
            kind="EVALUATION",
            source="AI_GATEWAY",
            payload=EvaluationDecision(
                decision="RESEARCH_CANDIDATE",
                reasons=["Adversarial test claim only"],
                observations=[],
                unknown=[],
                evidence_id=evidence.id,
                source="AI_GATEWAY",
            ).model_dump(mode="json"),
            previous_digest="0" * 64,
            digest="0" * 64,
        )
        db.add(decision)
        db.flush()
        db.add(
            CampaignLineage(
                owner_id=owned.owner_id,
                campaign_id=campaign.id,
                parent_id=decision.id,
                sequence=3,
                kind="CRITIQUE",
                source="AI_GATEWAY",
                payload=Critique(
                    summary="Adversarial test critique",
                    objections=["No actual evidence"],
                    source="AI_GATEWAY",
                ).model_dump(mode="json"),
                previous_digest="0" * 64,
                digest="0" * 64,
            )
        )
        decision_id = decision.id
    response = system.post(
        f"/api/v1/workspace/accounts/{account['id']}/strategy",
        {"decision_id": str(decision_id)},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "WORKSPACE_LINEAGE_INVALID"
    library = system.client.get("/api/v1/workspace/library")
    assert library.status_code == 200
    assert library.json()["items"] == [] and library.json()["unavailable_count"] == 1
