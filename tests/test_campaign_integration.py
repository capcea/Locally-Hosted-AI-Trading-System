"""Real campaign/Phase5/MinIO/Redis acceptance, including guarded owner handoffs."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_ai_integration import ai as ai
from test_market_integration import market as market
from test_market_integration import run_worker, submit
from test_phase1_integration import System
from test_research_integration import prepared
from test_research_integration import work as research_work

from packages.campaigns.contracts import ParameterCandidate, StrategyHypothesis
from packages.campaigns.models import CampaignRuntime, ResearchCampaign
from packages.campaigns.service import admit_candidate, objective
from packages.campaigns.worker import Worker
from packages.persistence.models import LoginSession, utcnow
from packages.research.models import ResearchRun

pytestmark = pytest.mark.isolated_services


def body(system: System, **changes: Any) -> dict[str, Any]:
    plan = prepared(system)
    objective = {
        "title": "Synthetic bounded campaign",
        "objective": "Investigate a reviewed baseline using synthetic ticks.",
        "mode": "SYNTHETIC_FIXTURE",
        "template": plan,
        "search_space": plan["parameters"],
        "evaluation": {"minimum_trades": 10},
        "acknowledged_owner_handoffs": True,
        "acknowledged_no_promotion": True,
        **changes,
    }
    return {"key": "campaign-" + uuid4().hex, "objective": objective}


def create(system: System, data: dict[str, Any]) -> dict[str, Any]:
    response = system.post("/api/v1/campaigns", data)
    assert response.status_code == 201, response.text
    return dict(response.json())


def authorize(system: System, row: dict[str, Any]) -> None:
    path = "/api/v1/campaigns/" + row["id"]
    assert system.post(path + "/control", {"action": "REQUEST_APPROVAL"}).status_code == 200
    accepted = system.post(
        path + "/approve",
        {
            "expected_digest": row["digest"],
            "acknowledged_bounded_research": True,
            "acknowledged_no_promotion": True,
        },
    )
    assert accepted.status_code == 200, accepted.text


def step(system: System) -> bool:
    worker = Worker(system.config)
    try:
        return worker.once()
    finally:
        worker.close()


def plan_ready(system: System, row: dict[str, Any]) -> str:
    authorize(system, row)
    assert step(system)  # QUEUED -> PLANNING
    assert step(system)  # finite candidate + immutable plan -> owner review
    path = "/api/v1/campaigns/" + row["id"]
    result = system.client.get(path).json()
    assert result["pending"] == "SUBMIT_EXPERIMENT", result
    return str(path)


def handoff(system: System, path: str) -> Any:
    plans = [r for r in system.client.get(path + "/lineage").json() if r["kind"] == "PLAN"]
    assert plans
    plan = plans[-1]
    return system.post(
        path + "/submit-plan",
        {"plan_id": plan["id"], "expected_digest": plan["digest"], "acknowledged_exact_plan": True},
    )


def test_real_fixture_campaign_reuses_risk_backtest_stores_lineage_and_stops_on_insufficient_sample(
    market: System,
) -> None:
    data = body(market)
    row = create(market, data)
    assert create(market, data)["id"] == row["id"]
    conflict = {**data, "objective": {**data["objective"], "title": "Changed objective"}}
    assert market.post("/api/v1/campaigns", conflict).status_code == 409
    path = plan_ready(market, row)
    before = market.client.get("/api/v1/research/experiments").json()
    assert not before  # A worker cannot impersonate owner submission.
    response = handoff(market, path)
    assert response.status_code == 202, response.text
    run = response.json()["experiment_id"]
    assert handoff(market, path).json()["experiment_id"] == run
    research_work(market)
    for _ in range(3):
        assert step(market)  # actual completion -> evidence -> deterministic critique
    result = market.client.get(path).json()
    assert result["state"] == "STOPPED" and result["reason"] == "INSUFFICIENT_EVIDENCE", result
    lineage = market.client.get(path + "/lineage").json()
    assert all(
        item["source"] == "SYNTHETIC_FIXTURE" and not item["paper_eligible"] for item in lineage
    )
    assert {
        "HYPOTHESIS",
        "CANDIDATE",
        "PLAN",
        "EXPERIMENT",
        "EVIDENCE",
        "EVALUATION",
        "CRITIQUE",
        "FEEDBACK",
    } <= {item["kind"] for item in lineage}
    evidence = next(item for item in lineage if item["kind"] == "EVIDENCE")["payload"]
    canonical = market.client.get(f"/api/v1/research/experiments/{run}/results").json()
    evaluation = next(item for item in lineage if item["kind"] == "EVALUATION")["payload"]
    assert (
        evaluation["observations"][0]["metrics"]["net_profit"]
        == canonical["trials"][0]["metrics"]["net_profit"]
    )
    assert evidence["attempted_trials_owner"] >= evidence["attempted_trials_campaign"] == 1
    assert market.client.get("/api/v1/audit/verify").json()["valid"]
    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        with pytest.raises(DBAPIError):
            db.execute(text("UPDATE campaign_lineage SET digest=:d"), {"d": "0" * 64})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM research_campaigns"))
            db.commit()
        db.rollback()
        assert len(db.scalars(select(ResearchRun)).all()) == 1
    engine.dispose()


def test_atomic_duplicate_handoffs_pause_and_cancellation_acknowledgement(market: System) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    assert market.post(path + "/control", {"action": "PAUSE"}).status_code == 200
    assert handoff(market, path).status_code == 409
    assert market.post(path + "/control", {"action": "RESUME"}).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: handoff(market, path), range(2)))
    assert all(r.status_code == 202 for r in responses)
    assert len({r.json()["experiment_id"] for r in responses}) == 1
    requested = market.post(path + "/control", {"action": "CANCEL"}).json()
    assert requested["cancel_requested"] and not requested["cancellation_acknowledged"]
    assert not market.client.get(path).json()["cancellation_acknowledged"]
    assert step(market)
    research_work(market)  # actual queued research cancellation
    assert step(market)
    assert market.client.get(path).json()["cancellation_acknowledged"]
    assert market.client.get(path).json()["counts"]["experiments"] == 1


def test_campaign_concurrency_approval_digest_mfa_and_scope_are_not_bypassed(
    market: System,
) -> None:
    data = body(market)
    first = create(market, data)
    second = create(market, {**data, "key": "second-" + uuid4().hex})
    authorize(market, first)
    path = "/api/v1/campaigns/" + second["id"]
    assert market.post(path + "/control", {"action": "REQUEST_APPROVAL"}).status_code == 200
    payload = {
        "expected_digest": second["digest"],
        "acknowledged_bounded_research": True,
        "acknowledged_no_promotion": True,
    }
    denied = market.post(path + "/approve", payload)
    assert denied.status_code == 409 and "CONCURRENCY" in denied.text
    viewer, _ = market.peer("campaign-viewer", "VIEWER")
    assert market.post("/api/v1/campaigns", data, viewer).status_code == 403
    assert viewer.get("/api/v1/campaigns/" + first["id"]).status_code == 404
    assert viewer.get("/api/v1/campaigns").json() == []
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        for session in db.scalars(select(LoginSession)):
            session.mfa_at = utcnow() - timedelta(minutes=6)
    assert market.post(path + "/approve", payload).status_code == 403
    engine.dispose()


def test_missing_real_model_no_silent_fixture_fallback_and_holdout_refusal(market: System) -> None:
    data = body(market, mode="AI_GATEWAY")
    row = create(market, data)
    path = "/api/v1/campaigns/" + row["id"]
    market.post(path + "/control", {"action": "REQUEST_APPROVAL"})
    response = market.post(
        path + "/approve",
        {
            "expected_digest": row["digest"],
            "acknowledged_bounded_research": True,
            "acknowledged_no_promotion": True,
        },
    )
    assert response.status_code == 409 and "MODEL_UNAVAILABLE" in response.text
    assert not step(market)
    dataset = data["objective"]["template"]["datasets"][0]["dataset_id"]
    seal = market.post(
        "/api/v1/research/holdouts",
        {
            "dataset_id": dataset,
            "reason": "Protected synthetic interval remains excluded",
            "acknowledged_prior_exposure_unknown": True,
        },
    )
    assert seal.status_code == 201
    data["key"] = "sealed-" + uuid4().hex
    blocked = market.post("/api/v1/campaigns", data)
    assert blocked.status_code == 409 and "HOLDOUT" in blocked.text


def test_revoked_policy_stops_without_new_experiment_and_expired_lease_is_fenced(
    market: System,
) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        runtime = db.get(CampaignRuntime, UUID(row["id"]))
        assert runtime
        runtime.worker_token = uuid4()
        runtime.lease_until = utcnow() - timedelta(seconds=1)
        runtime.attempts = 1
    # A new worker reclaims the expired metadata lease without submitting anything.
    step(market)
    assert market.client.get(path).json()["counts"]["experiments"] == 0
    account = row["objective"]["template"]["source_account_id"]
    revision = market.client.get(f"/api/v1/risk/accounts/{account}/status").json()["revision"]
    stop = market.post(
        f"/api/v1/risk/accounts/{account}/emergency",
        {
            "key": "campaign-stop-" + uuid4().hex,
            "action": "STOP_NEW_ENTRIES",
            "expected_revision": revision,
            "acknowledged_simulated_only": True,
        },
    )
    assert stop.status_code == 200, stop.text
    # Advance only this disposable polling lease; never use arbitrary wall-clock sleeps.
    with Session(engine) as db, db.begin():
        runtime = db.get(CampaignRuntime, UUID(row["id"]))
        assert runtime
        runtime.lease_until = utcnow() - timedelta(seconds=1)
    assert step(market)
    assert market.client.get(path).json()["state"] == "STOPPED"
    assert market.client.get(path).json()["counts"]["experiments"] == 0
    engine.dispose()


def test_two_real_bounded_training_iterations_retain_feedback_and_never_promote(
    market: System,
) -> None:
    data = body(market)
    from test_execution_engine import START

    plan = data["objective"]["template"]
    # Ticks have UNKNOWN coverage and correctly stop the earlier acceptance case.
    # This follow-up fixture imports a genuinely complete, scheduled M1 series instead.
    old = market.client.get(f"/api/v1/market/datasets/{plan['datasets'][0]['dataset_id']}").json()

    def at(i: int) -> str:
        return (START + timedelta(minutes=i)).isoformat()

    bars = {**old["spec"], "data_type": "BAR", "timeframe": "M1", "start": at(0), "end": at(101)}
    lines = ["event_time,observed_at,available_at,open,high,low,close,volume,sequence"]
    from decimal import Decimal

    for i in range(101):
        price = Decimal("1.1000") + Decimal(i) * Decimal(".0005")
        lines.append(
            f"{at(i)},{at(i + 1)},{at(i + 1)},{price},{price + Decimal('.0006')},"
            f"{price - Decimal('.0001')},{price + Decimal('.0005')},10,{i}"
        )
    imported = submit(market, bars, ("\n".join(lines) + "\n").encode())
    run_worker(market)
    admitted = market.client.get(f"/api/v1/market/datasets/{imported['dataset_id']}").json()
    assert admitted["status"] == "VALID", admitted
    assert Decimal(admitted["coverage_pct"]) == 100
    plan["datasets"][0].update(
        dataset_id=admitted["id"], manifest_sha256=admitted["manifest_sha256"]
    )
    plan["bar_spread"] = ".0002"
    plan["parameters"][0]["max_hold_seconds"] = 120
    plan["chronology"].update(
        discovery_end=at(80),
        calibration_end=at(86),
        validation_end=at(94),
        end=at(101),
        purge_seconds=120,
    )
    data["objective"]["search_space"] = [
        plan["parameters"][0],
        {**plan["parameters"][0], "slow": 4},
    ]
    row = create(market, data)
    path = plan_ready(market, row)
    for iteration in (1, 2):
        submitted = handoff(market, path)
        assert submitted.status_code == 202, submitted.text
        research_work(market)
        for _ in range(3):
            assert step(market)
        state = market.client.get(path).json()
        if iteration == 1:
            assert state["state"] == "READY_FOR_NEXT_ITERATION", market.client.get(
                path + "/lineage"
            ).json()
            assert step(market)
            assert step(market)
        else:
            assert state["state"] == "COMPLETED", state
    assert state["counts"]["experiments"] == state["counts"]["proposals"] == 2
    entries = market.client.get(path + "/lineage").json()
    feedback = [e["payload"] for e in entries if e["kind"] == "FEEDBACK"]
    assert [f["justified"] for f in feedback] == [True, False]
    assert all(
        e["payload"]["decision"] != "RESEARCH_CANDIDATE"
        for e in entries
        if e["kind"] == "EVALUATION"
    )
    assert state["paper_eligible"] is False and state["external_execution"] == "DENY_ALL"


def test_candidate_dedup_domain_and_proposal_budget_are_server_enforced(market: System) -> None:
    data = body(market, budgets={"candidate_proposals": 1, "experiments": 1})
    row = create(market, data)
    plan_ready(market, row)
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        campaign = db.get(ResearchCampaign, UUID(row["id"]))
        runtime = db.get(CampaignRuntime, UUID(row["id"]), with_for_update=True)
        assert campaign and runtime
        spec = objective(campaign)
        hypothesis = StrategyHypothesis(
            title="Untrusted fixture idea",
            rationale=spec.objective,
            strategy=spec.template.strategy,
            strategy_digest=spec.template.strategy_digest,
            source=spec.mode,
        )
        candidate = ParameterCandidate(
            strategy=spec.template.strategy,
            strategy_digest=spec.template.strategy_digest,
            parameters=spec.search_space[0],
            source=spec.mode,
        )
        with pytest.raises(ValueError, match="DUPLICATE"):
            admit_candidate(db, campaign, runtime, hypothesis, candidate)
        changed = candidate.model_copy(
            update={"parameters": candidate.parameters.model_copy(update={"slow": 30})}
        )
        with pytest.raises(ValueError, match="OUTSIDE_OWNER"):
            admit_candidate(db, campaign, runtime, hypothesis, changed)
        assert runtime.proposals == 1
    engine.dispose()


def test_validation_interval_cannot_be_reused_for_adaptive_feedback(market: System) -> None:
    data = body(market, budgets={"iterations": 1})
    data["objective"]["template"]["phase"] = "VALIDATION"
    first = create(market, data)
    path = plan_ready(market, first)
    assert handoff(market, path).status_code == 202
    research_work(market)
    for _ in range(3):
        assert step(market)
    assert market.client.get(path).json()["state"] in {"COMPLETED", "STOPPED"}
    second = create(market, {**data, "key": "reuse-" + uuid4().hex})
    path = plan_ready(market, second)
    response = handoff(market, path)
    assert response.status_code == 409 and "ALREADY_EXPOSED" in response.text


def test_sealing_after_authorization_revokes_campaign_data_access(market: System) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    dataset = row["objective"]["template"]["datasets"][0]["dataset_id"]
    seal = market.post(
        "/api/v1/research/holdouts",
        {
            "dataset_id": dataset,
            "reason": "Seal after authorization; campaign must not read cached data",
            "acknowledged_prior_exposure_unknown": True,
        },
    )
    assert seal.status_code == 201, seal.text
    assert step(market)
    state = market.client.get(path).json()
    assert state["state"] == "STOPPED" and "HOLDOUT" in state["reason"]
    assert state["counts"]["experiments"] == 0


def test_deadline_enforced_by_phase5_even_if_campaign_worker_is_offline(market: System) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    assert market.post(path + "/submit-plan", {}).status_code == 422
    response = handoff(market, path)
    assert response.status_code == 202
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        runtime = db.get(CampaignRuntime, UUID(row["id"]))
        assert runtime
        runtime.deadline = utcnow() - timedelta(seconds=1)
    research_work(market)
    report = market.client.get(
        f"/api/v1/research/experiments/{response.json()['experiment_id']}"
    ).json()
    assert report["job"]["state"] == "FAILED"
    assert report["job"]["error"] == "CAMPAIGN_AUTHORITY_EXPIRED_OR_STOPPED"
    assert report["result"] is None
    engine.dispose()


def test_transient_storage_failure_recovers_metadata_without_a_second_experiment(
    market: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    response = handoff(market, path)
    assert response.status_code == 202
    research_work(market)
    assert step(market)  # EVALUATING, before immutable evidence publication.
    worker = Worker(market.config)
    original = worker.objects.get

    def unavailable(artifact: Any) -> bytes:
        raise OSError("Synthetic bounded dependency fault")

    monkeypatch.setattr(worker.objects, "get", unavailable)
    try:
        with pytest.raises(OSError, match="dependency fault"):
            worker.once()
    finally:
        monkeypatch.setattr(worker.objects, "get", original)
        worker.close()
    assert market.client.get(path).json()["state"] == "UNKNOWN"
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        runtime = db.get(CampaignRuntime, UUID(row["id"]))
        assert runtime
        runtime.lease_until = utcnow() - timedelta(seconds=1)
    assert step(market)  # Recover the rolled-back EVALUATING state; no submission.
    assert step(market)  # Fetch the actual MinIO result and publish canonical evidence once.
    assert step(market)
    events = market.client.get(path + "/lineage").json()
    assert len([e for e in events if e["kind"] == "EVIDENCE"]) == 1
    assert market.client.get(path).json()["counts"]["experiments"] == 1
    engine.dispose()


def test_campaign_cancellation_reaches_restricted_gateway_authority_without_granting_campaign_reads(
    ai: Any,
) -> None:
    # Measured synthetic HTTP transport, explicitly NOT a real-model acceptance test.
    ai.setup()
    data = body(ai.owner, mode="AI_GATEWAY")
    row = create(ai.owner, data)
    authorize(ai.owner, row)
    assert step(ai.owner)
    assert step(ai.owner)
    path = "/api/v1/campaigns/" + row["id"]
    response = ai.owner.post(
        path + "/gateway",
        {"role": "RESEARCH", "processing_acknowledged": True, "retain_structured_output": True},
    )
    assert response.status_code == 202, response.text
    request = response.json()["request_id"]
    for query in (
        "SELECT * FROM research_campaigns",
        "SELECT * FROM campaign_runtime",
        "SELECT * FROM campaign_lineage",
        "SELECT * FROM trading_accounts",
    ):
        with ai.worker.store.engine.connect() as db, pytest.raises(DBAPIError):
            db.execute(text(query))
    cancel = ai.owner.post(path + "/control", {"action": "CANCEL"})
    assert cancel.status_code == 200 and not cancel.json()["cancellation_acknowledged"]
    with ai.worker.store.session() as db:
        permitted = db.scalar(
            text("SELECT authorized FROM ai_request_authority WHERE request_id=:id"),
            {"id": UUID(request)},
        )
        assert permitted is False
    assert step(ai.owner)  # Propagate the explicit cancellation request to the existing AIJob.
    assert not ai.owner.client.get(path).json()["cancellation_acknowledged"]
    assert ai.worker.once()
    job = ai.owner.client.get("/api/v1/ai/requests/" + request).json()
    assert job["state"] == "CANCELLED", job
    assert job["output"] is None
    assert step(ai.owner)
    assert ai.owner.client.get(path).json()["cancellation_acknowledged"]


def test_persistent_storage_failures_stop_bounded_recovery_without_duplicate_experiments(
    market: System, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = create(market, body(market))
    path = plan_ready(market, row)
    assert handoff(market, path).status_code == 202
    research_work(market)
    assert step(market)  # EVALUATING, with an actual complete stored Phase5 result.
    worker = Worker(market.config)
    original = worker.objects.get

    def unavailable(artifact: Any) -> bytes:
        if str(artifact["key"]).startswith("research/"):
            raise OSError("Synthetic persistent storage dependency fault")
        return original(artifact)

    monkeypatch.setattr(worker.objects, "get", unavailable)
    try:
        with pytest.raises(OSError):
            worker.once()
        engine = create_engine(market.runtime_url)
        for _ in range(2):
            with Session(engine) as db, db.begin():
                runtime = db.get(CampaignRuntime, UUID(row["id"]))
                assert runtime
                runtime.lease_until = utcnow() - timedelta(seconds=1)
            if _ == 0:
                assert worker.once()  # Recovery alone must not reset the failure counter.
                with pytest.raises(OSError):
                    worker.once()
            else:
                assert worker.once()  # Three claims exhausted; requires owner review.
        result = market.client.get(path).json()
        assert result["state"] == "UNKNOWN"
        assert result["reason"] == "CAMPAIGN_WORKER_CRASH_LIMIT_REVIEW_REQUIRED"
        assert result["counts"]["experiments"] == 1
        assert not worker.once()
        assert market.post(path + "/control", {"action": "CANCEL"}).status_code == 200
        assert worker.once()
        assert market.client.get(path).json()["cancellation_acknowledged"]
        engine.dispose()
    finally:
        worker.close()


def test_full_ordinary_lineage_budget_preserves_space_for_idempotent_cancellation(
    market: System,
) -> None:
    from packages.campaigns.service import record

    row = create(market, body(market))
    path = plan_ready(market, row)
    engine = create_engine(market.runtime_url)
    with Session(engine) as db, db.begin():
        campaign = db.get(ResearchCampaign, UUID(row["id"]))
        runtime = db.get(CampaignRuntime, UUID(row["id"]), with_for_update=True)
        assert campaign and runtime
        budget = objective(campaign).budgets.lineage_bytes
        while runtime.lineage_bytes + 61000 < budget:
            record(db, campaign, runtime, "TEST_BUDGET_EVIDENCE", {"padding": "x" * 60000})
        record(
            db,
            campaign,
            runtime,
            "TEST_BUDGET_EVIDENCE",
            {"padding": "x" * (budget - runtime.lineage_bytes - 100)},
        )
        with pytest.raises(ValueError, match="STORAGE_BUDGET_EXHAUSTED"):
            record(db, campaign, runtime, "CONTROL", {"action": "PAUSE", "padding": "x" * 200})
    cancelled = market.post(path + "/control", {"action": "CANCEL"})
    assert cancelled.status_code == 200 and not cancelled.json()["cancellation_acknowledged"]
    repeated = market.post(path + "/control", {"action": "CANCEL"})
    assert repeated.status_code == 200
    assert repeated.json()["lineage_head"] == cancelled.json()["lineage_head"]
    assert step(market)
    assert market.client.get(path).json()["cancellation_acknowledged"]
    engine.dispose()
