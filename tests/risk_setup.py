"""Explicit owner/MFA risk admission for synthetic integration fixtures, through real APIs."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from test_phase1_integration import System
from test_risk_math import financial, policy


def post(system: System, path: str, body: dict[str, Any], status: int = 200) -> dict[str, Any]:
    response = system.post(path, body)
    assert response.status_code == status, response.text
    return dict(response.json())


def clear_stop(system: System, account_id: str) -> dict[str, Any]:
    report = post(system, f"/api/v1/risk/accounts/{account_id}/monitor", {})
    return post(
        system,
        f"/api/v1/risk/accounts/{account_id}/emergency",
        {
            "key": "owner-clear-" + uuid4().hex,
            "action": "CLEAR_STOP",
            "expected_revision": report["revision"],
            "acknowledged_simulated_only": True,
        },
    )


def configure_run(system: System, run: dict[str, Any]) -> None:
    account_id = run["account_id"]
    base = f"/api/v1/risk/accounts/{account_id}"
    if not system.client.get(base + "/profiles").json():
        post(
            system,
            base + "/profiles",
            {
                "name": "Explicit synthetic risk profile",
                "scope": "ACCOUNT",
                "acknowledged_internal_defaults": True,
            },
            201,
        )
    if not system.client.get(base + "/policies").json():
        terms = policy(
            currency=run["state"]["model"]["account_currency"],
            permitted_instruments=[run["state"]["spec"]["canonical_symbol"]],
        )
        created = post(
            system,
            base + "/policies",
            {
                "kind": "PERSONAL",
                "terms": terms.model_dump(mode="json"),
                "effective_at": datetime(2020, 1, 1, tzinfo=UTC).isoformat(),
                "expires_at": datetime(2035, 1, 1, tzinfo=UTC).isoformat(),
                "document_digest": "5" * 64,
                "source_references": ["owner://synthetic-test-policy"],
            },
            201,
        )
        post(
            system,
            f"/api/v1/risk/policies/{created['id']}/attest",
            {
                "document_digest": created["document_digest"],
                "action": "VERIFY",
                "acknowledged_exact_program_and_effective_dates": True,
            },
        )
    spec = run["state"]["spec"]
    at = datetime.fromisoformat(run["state"]["clock"])
    financial_terms = financial(
        quote_currency=spec["profit_currency"],
        tick_value_profit_currency=str(Decimal(spec["tick_size"]) * Decimal(spec["contract_size"])),
        verified_at=at,
        valid_until=at + timedelta(days=10),
    )
    post(
        system,
        f"/api/v1/risk/runs/{run['id']}/contexts",
        {
            "financial": financial_terms.model_dump(mode="json"),
            "owner_acknowledged_synthetic_assumptions": True,
        },
        201,
    )
    clear_stop(system, account_id)
