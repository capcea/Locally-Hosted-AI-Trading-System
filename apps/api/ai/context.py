"""Trusted read-only context broker. This module is excluded from the inference worker image."""

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.ai.contracts import ContextReference
from packages.ai.models import AIArtifact, AIContent, AIRequest
from packages.ai.prompts import digest
from packages.ai.settings import GatewaySettings
from packages.market.models import MarketDataset
from packages.persistence.models import utcnow
from packages.research.access import sealed
from packages.research.models import ResearchJob, ResearchResult, ResearchRun
from packages.research.strategies import NAMES, definition


@dataclass(frozen=True)
class ContextScope:
    db: Session
    owner_id: UUID


DOCUMENTS = {
    "research-limits-v1": (
        "Stored historical simulation results describe only their pinned data, costs and protocol. "
        "In-sample, subsequent OOS and the separately protected final holdout are different. "
        "Small samples, repeated trials, gaps and uncertain costs limit conclusions. "
        "Model analysis is not verified evidence or permission to trade."
    ),
    "ai-boundaries-v1": (
        "AI can explain authorized summaries and suggest hypotheses or inert code. It cannot "
        "read credentials, execute commands, fetch arbitrary URLs, reveal sealed holdouts, "
        "verify a policy, change an account, approve risk or place an order."
    ),
}


def numeric_metrics(values: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    if not isinstance(values, dict):
        return result
    for key in (
        "net_profit",
        "max_drawdown",
        "trade_count",
        "win_rate",
        "profit_factor",
        "sharpe",
        "sortino",
    ):
        value = values.get(key)
        if isinstance(value, bool) or not isinstance(value, str | int | float):
            continue
        text = str(value)
        if len(text) > 80:
            continue
        try:
            if Decimal(text).is_finite():
                result[key] = text
        except InvalidOperation:
            continue
    return result


def dataset_for(identity: ContextScope, identifier: UUID) -> MarketDataset:
    row = identity.db.scalar(
        select(MarketDataset).where(
            MarketDataset.id == identifier, MarketDataset.owner_id == identity.owner_id
        )
    )
    if row is None or sealed(identity.db, row):
        raise HTTPException(404, "AI_CONTEXT_NOT_AVAILABLE")
    return row


def assemble(
    identity: ContextScope,
    references: list[ContextReference],
    config: GatewaySettings,
    *,
    depth: int = 0,
) -> list[dict[str, Any]]:
    if depth > 2:
        raise HTTPException(422, "AI_CONTEXT_DEPTH_LIMIT")
    context: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reference in references:
        ref = reference.kind + ":" + reference.id
        if ref in seen:
            raise HTTPException(422, "AI_DUPLICATE_CONTEXT_REFERENCE")
        seen.add(ref)
        item: dict[str, Any] = {
            "reference": ref,
            "kind": reference.kind,
            "source": "SIMULATED",
            "untrusted_content": True,
        }
        if reference.kind == "strategy":
            if reference.id not in NAMES:
                raise HTTPException(404, "AI_CONTEXT_NOT_AVAILABLE")
            current = definition(reference.id)
            item["summary"] = {
                k: current[k]
                for k in ("id", "version", "digest", "entry", "exit", "assumptions")
                if k in current
            }
        elif reference.kind == "documentation":
            if reference.id not in DOCUMENTS:
                raise HTTPException(404, "AI_CONTEXT_NOT_AVAILABLE")
            item.update({"source": "REVIEWED_DOCUMENTATION", "summary": DOCUMENTS[reference.id]})
        else:
            try:
                identifier = UUID(reference.id)
            except ValueError as exc:
                raise HTTPException(422, "AI_CONTEXT_ID_INVALID") from exc
            if reference.kind == "dataset":
                row = dataset_for(identity, identifier)
                counts = row.quality.get("counts", {})
                item.update(
                    {
                        "account_id": str(row.account_id),
                        "summary": {
                            "version": row.version,
                            "status": row.status,
                            "record_count": row.record_count,
                            "source": row.spec.get("provenance"),
                            "coverage_pct": row.coverage_pct,
                            "quality_counts": {
                                str(k)[:80]: v
                                for k, v in counts.items()
                                if isinstance(v, int) and 0 <= v <= 1000000
                            }
                            if isinstance(counts, dict)
                            else {},
                            "manifest_sha256": row.manifest_sha256,
                        },
                    }
                )
            elif reference.kind == "experiment":
                run = identity.db.scalar(
                    select(ResearchRun).where(
                        ResearchRun.id == identifier, ResearchRun.owner_id == identity.owner_id
                    )
                )
                if run is None or run.plan.get("phase") == "FINAL_HOLDOUT":
                    raise HTTPException(404, "AI_CONTEXT_NOT_AVAILABLE")
                for pin in run.plan.get("datasets", []):
                    dataset_for(identity, UUID(pin["dataset_id"]))
                job = identity.db.scalar(select(ResearchJob).where(ResearchJob.run_id == run.id))
                stored = identity.db.get(ResearchResult, run.id)
                if job is None or job.state != "SUCCEEDED" or stored is None:
                    raise HTTPException(409, "AI_CONTEXT_REQUIRES_COMPLETED_EXPERIMENT")
                trials = stored.artifact.get("trials", [])
                item.update(
                    {
                        "account_id": str(run.source_account_id),
                        "summary": {
                            "phase": run.plan.get("phase"),
                            "engine": run.plan.get("engine"),
                            "strategy": run.plan.get("strategy"),
                            "semantic_digest": stored.semantic_digest,
                            "trials": [
                                {
                                    "ordinal": trial.get("ordinal"),
                                    "metrics": numeric_metrics(trial.get("metrics")),
                                    "risk_validated": trial.get("risk_validated") is True,
                                }
                                for trial in trials[:5]
                                if isinstance(trial, dict)
                            ],
                            "uncertainty": (
                                "SIMULATED; sample/cost/multiple-testing limitations remain; "
                                "no profitability certification"
                            ),
                        },
                    }
                )
            else:
                previous = identity.db.scalar(
                    select(AIRequest).where(
                        AIRequest.id == identifier, AIRequest.owner_id == identity.owner_id
                    )
                )
                artifact = identity.db.get(AIArtifact, identifier) if previous else None
                content = identity.db.get(AIContent, identifier) if previous else None
                if (
                    previous is None
                    or artifact is None
                    or content is None
                    or previous.retain_until <= utcnow()
                    or not content.output_ciphertext
                ):
                    raise HTTPException(404, "AI_CONTEXT_NOT_AVAILABLE")
                # A later seal also invalidates cached/retrieved AI summaries of those inputs.
                originals = [
                    ContextReference.model_validate(r)
                    for r in previous.specification.get("references", [])
                ]
                assemble(identity, originals, config, depth=depth + 1)
                decoded = json.loads(config.cipher().decrypt(content.output_ciphertext.encode()))
                if digest(decoded) != artifact.digest:
                    raise HTTPException(409, "AI_CONTEXT_ARTIFACT_INTEGRITY")
                item.update(
                    {
                        "source": "UNVERIFIED_MODEL_OUTPUT",
                        "summary": decoded,
                        "artifact_sha256": artifact.digest,
                    }
                )
        item["sha256"] = digest(item)
        context.append(item)
    if len(json.dumps(context).encode()) > config.max_input_bytes:
        raise HTTPException(422, "AI_CONTEXT_BYTE_LIMIT")
    return context
