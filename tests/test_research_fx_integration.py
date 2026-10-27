"""Actual admitted FX ticks refresh research conversion evidence beyond its freshness window."""

from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from test_execution_engine import START
from test_market_integration import market as market
from test_market_integration import run_worker, submit
from test_phase1_integration import System
from test_research_integration import prepared, submitted, work

pytestmark = pytest.mark.isolated_services


def test_research_cross_currency_uses_only_prior_actual_admitted_ticks(market: System) -> None:
    plan = prepared(market)
    venue = market.post(
        "/api/v1/records/venues",
        {"kind": "venues", "name": "Synthetic FX research", "venue_type": "CUSTOM"},
    )
    assert venue.status_code == 201, venue.text
    instrument = market.post(
        "/api/v1/records/instruments",
        {
            "kind": "instruments",
            "name": "Synthetic USDJPY",
            "symbol": "USDJPY",
            "asset_class": "FOREX",
            "venue_id": venue.json()["id"],
        },
    )
    assert instrument.status_code == 201, instrument.text
    from uuid import UUID

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from packages.market.models import MarketDataset

    engine = create_engine(market.runtime_url)
    with Session(engine) as db:
        original = db.get(MarketDataset, UUID(plan["datasets"][0]["dataset_id"]))
        assert original is not None
        spec: dict[str, Any] = dict(original.spec)
    engine.dispose()
    spec.update(
        instrument_id=instrument.json()["id"],
        source_symbol="USDJPY.fixture",
        end=(START + timedelta(seconds=101)).isoformat(),
        price_increment=".01",
    )
    lines = ["event_time,observed_at,available_at,bid,ask,sequence"]
    for i in range(101):
        at = (START + timedelta(seconds=i)).isoformat()
        bid = Decimal(110) + Decimal(i) / 100
        lines.append(f"{at},{at},{at},{bid},{bid + Decimal('.02')},{i}")
    upload = submit(market, spec, ("\n".join(lines) + "\n").encode())
    run_worker(market)
    data = market.client.get(f"/api/v1/market/datasets/{upload['dataset_id']}").json()
    assert data["status"] == "VALID", data
    pin = plan["datasets"][0]
    pin.update(dataset_id=data["id"], manifest_sha256=data["manifest_sha256"])
    pin["symbol"].update(
        symbol="USDJPY.fixture",
        canonical_symbol="USDJPY",
        profit_currency="JPY",
        tick_size=".01",
        digits=2,
    )
    pin["context"]["financial"].update(
        base_currency="USD", quote_currency="JPY", tick_value_profit_currency="1000", fx=[]
    )
    import hashlib
    import json

    from risk_setup import clear_stop

    path = f"/api/v1/risk/accounts/{plan['source_account_id']}/policies"
    prior = market.client.get(path).json()[0]
    terms = {**prior["terms"], "permitted_instruments": ["EURUSD", "USDJPY"]}
    document = hashlib.sha256(json.dumps(terms, sort_keys=True).encode()).hexdigest()
    approved = market.post(
        path,
        {
            "kind": "PERSONAL",
            "terms": terms,
            "effective_at": prior["effective_at"],
            "expires_at": prior["expires_at"],
            "document_digest": document,
            "source_references": ["owner://explicit-synthetic-USDJPY-research-permission"],
        },
    )
    assert approved.status_code == 201, approved.text
    attested = market.post(
        f"/api/v1/risk/policies/{approved.json()['id']}/attest",
        {
            "document_digest": document,
            "action": "VERIFY",
            "acknowledged_exact_program_and_effective_dates": True,
        },
    )
    assert attested.status_code == 200, attested.text
    clear_stop(market, plan["source_account_id"])
    plan["phase"] = "CALIBRATION"  # This begins after the initial 30-second FX window.
    run = submitted(market, plan)
    work(market)
    path = f"/api/v1/research/experiments/{run['id']}"
    report = market.client.get(path).json()
    assert report["job"]["state"] == "SUCCEEDED", report["job"]["error"]
    result = market.client.get(path + "/results").json()["trials"][0]
    assert result["metrics"]["trade_count"] > 0, result
    audit = market.client.get(
        "/api/v1/audit?event_type=research.fx_evidence_updated&limit=100"
    ).json()
    assert len(audit) >= 30
    assert market.client.get("/api/v1/audit/verify").json()["valid"]
