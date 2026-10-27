"""Causal immutable FX evidence updates from explicitly admitted Forex tick streams only."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.execution.journal import digest
from packages.execution.models import SimulationRun
from packages.persistence.audit import append_event
from packages.research.contracts import ExperimentInput
from packages.risk.contracts import Context, FXQuote
from packages.risk.models import RunContext


def update(
    db: Session,
    plan: ExperimentInput,
    datasets: list[dict[str, Any]],
    observations: list[tuple[dict[str, Any], Any]],
    runs: dict[str, SimulationRun],
    at: datetime,
    key: str,
) -> None:
    latest: dict[tuple[str, str], tuple[dict[str, Any], Any]] = {}
    for source, row in observations:
        terms = source["pin"].context.financial
        if (
            row.available_at >= at
            or source["type"] != "TICK"
            or source["pin"].symbol.asset_class != "FOREX"
            or not terms.base_currency
        ):
            continue
        pair = (terms.base_currency, terms.quote_currency)
        old = latest.get(pair)
        if old is None or (row.available_at, row.sequence) > (old[1].available_at, old[1].sequence):
            latest[pair] = (source, row)
    for dataset_id, run in runs.items():
        base = next(d["pin"].context for d in datasets if d["dataset_id"] == dataset_id)
        profit = next(
            d["pin"].symbol.profit_currency for d in datasets if d["dataset_id"] == dataset_id
        )
        if profit == plan.assumptions.account_currency:
            continue
        edges = {(q.base, q.quote) for q in base.financial.fx}
        if not edges:
            edges = {
                pair for pair in latest if set(pair) == {profit, plan.assumptions.account_currency}
            }
        quotes = list(base.financial.fx)
        for pair in edges:
            known = latest.get(pair)
            if known is None:
                continue
            source, row = known
            if row.bid is None or row.ask is None:
                raise ValueError("FX_TICKS_REQUIRE_OBSERVED_BID_ASK")
            quote = FXQuote(
                base=pair[0],
                quote=pair[1],
                bid=row.bid,
                ask=row.ask,
                observed_at=row.event_time,
                available_at=row.available_at,
                valid_until=row.available_at + timedelta(seconds=30),
                source_reference=f"dataset:{source['dataset_id']}:sha256:{source['pin'].manifest_sha256}:sequence:{row.sequence}",
            )
            quotes = [q for q in quotes if (q.base, q.quote) != pair] + [quote]
        previous = db.scalar(
            select(RunContext)
            .where(RunContext.run_id == run.id)
            .order_by(RunContext.version.desc())
            .limit(1)
        )
        if previous is None:
            raise ValueError("FROZEN_RESEARCH_CONTEXT_MISSING")
        context = Context.model_validate(previous.body)
        candidate = context.model_copy(deep=True)
        candidate.financial.fx = sorted(quotes, key=lambda q: (q.base, q.quote))
        body = candidate.model_dump(mode="json")
        if body == previous.body:
            continue
        # All payoff, margin, policy and grouping facts remain the explicitly frozen assumptions.
        original = context.model_dump(mode="json")
        original["financial"].pop("fx")
        unchanged = candidate.model_dump(mode="json")
        unchanged["financial"].pop("fx")
        if original != unchanged:
            raise ValueError("RESEARCH_MARKET_DATA_UPDATE_CHANGED_FINANCIAL_SCOPE")
        db.add(
            RunContext(
                owner_id=run.owner_id,
                run_id=run.id,
                version=previous.version + 1,
                spec_digest=previous.spec_digest,
                body=body,
            )
        )
        db.flush()
        append_event(
            db,
            key,
            "research.fx_evidence_updated",
            entity_id=run.id,
            after={
                "context_digest": digest(body),
                "source": "SIMULATED",
                "evidence": (
                    "admitted immutable tick observations only; strictly earlier availability"
                ),
            },
        )
    db.commit()
