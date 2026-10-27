"""Admitted pinned inputs only; shared Phase2 deserialization and content verification."""

from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from packages.market.contracts import TIMEFRAMES
from packages.market.models import MarketDataset
from packages.market.processing import read_rows, verify_manifest
from packages.market.storage import ObjectStore
from packages.persistence.models import Instrument
from packages.research.access import seal_for
from packages.research.contracts import ExperimentInput
from packages.research.models import HoldoutRelease


def frozen_digest(plan: ExperimentInput) -> str:
    from packages.execution.journal import digest

    body = plan.model_dump(mode="json")
    for name in ("key", "name", "holdout_release_id"):
        body.pop(name)
    return digest(body)


def pinned(
    db: Session, plan: ExperimentInput, owner: Any, objects: ObjectStore, *, read: bool = True
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    count = 0
    for pin in plan.datasets:
        dataset = db.get(MarketDataset, pin.dataset_id)
        if (
            dataset is None
            or dataset.owner_id != owner
            or dataset.account_id != plan.source_account_id
        ):
            raise ValueError("DATASET_ACCOUNT_SCOPE_MISMATCH")
        if (
            dataset.status != "VALID"
            or dataset.manifest_sha256 != pin.manifest_sha256
            or not dataset.manifest_key
            or not dataset.manifest_version
        ):
            raise ValueError("DATASET_NOT_VALID_OR_PIN_CHANGED")
        seal = seal_for(db, dataset)
        if seal:
            release = (
                db.get(HoldoutRelease, plan.holdout_release_id) if plan.holdout_release_id else None
            )
            if (
                plan.phase != "FINAL_HOLDOUT"
                or release is None
                or release.seal_id != seal.id
                or release.owner_id != owner
                or release.frozen_digest != frozen_digest(plan)
            ):
                raise ValueError("FINAL_HOLDOUT_ACCESS_DENIED")
        elif plan.phase == "FINAL_HOLDOUT":
            raise ValueError("FINAL_EVALUATION_REQUIRES_SEALED_DATA")
        if (
            dataset.spec["data_type"] not in {"TICK", "BAR"}
            or dataset.instrument_id != dataset.spec.get("instrument_id")
            and str(dataset.instrument_id) != str(dataset.spec.get("instrument_id"))
        ):
            raise ValueError("RESEARCH_REQUIRES_PRICE_DATA_AND_MATCHING_INSTRUMENT")
        if (
            dataset.spec["source_symbol"] != pin.symbol.symbol
            or dataset.spec.get("calendar") is None
        ):
            raise ValueError("REPLAY_SYMBOL_OR_CALENDAR_UNVERIFIED")
        instrument = db.get(Instrument, dataset.instrument_id)
        if (
            instrument is None
            or instrument.symbol != pin.symbol.canonical_symbol
            or instrument.asset_class != pin.symbol.asset_class
        ):
            raise ValueError("CANONICAL_INSTRUMENT_SPEC_MISMATCH")
        from packages.risk.sizing import loss_conversion, payoff_multiplier

        payoff_multiplier(pin.symbol, pin.context.financial, plan.chronology.start)
        loss_conversion(
            pin.symbol.profit_currency,
            plan.assumptions.account_currency,
            pin.context.financial.fx,
            plan.chronology.start,
        )
        if (
            not pin.context.financial.automated
            or pin.context.financial.execution_style != "INTRADAY_BENCHMARK"
        ):
            raise ValueError("REVIEWED_BASELINES_MUST_DECLARE_AUTOMATED_EXECUTION_STYLE")
        if pin.context.financial.margin_per_unit is None:
            raise ValueError("RESEARCH_MARGIN_UNVERIFIED")
        if dataset.spec["data_type"] == "BAR" and pin.role == "EXECUTION":
            interval = TIMEFRAMES[str(dataset.spec["timeframe"])]
            if any(
                p.max_hold_seconds < interval or p.max_hold_seconds % interval
                for p in plan.parameters
            ):
                raise ValueError("BAR_HOLDING_HORIZON_MUST_ALIGN_WITH_OBSERVABLE_BAR_INTERVAL")
        if pin.symbol.calendar is None:
            raise ValueError("SYMBOL_SESSION_CALENDAR_UNVERIFIED")
        dataset_calendar = dataset.spec["calendar"]
        if not isinstance(dataset_calendar, dict):
            raise ValueError("DATASET_CALENDAR_INVALID")
        for field in ("timezone", "weekdays", "holidays", "opens", "closes"):
            if pin.symbol.calendar.model_dump(mode="json")[field] != dataset_calendar[field]:
                raise ValueError("DATASET_AND_EXECUTION_SESSION_CALENDARS_CONFLICT")
        if any(
            p.volume < pin.symbol.min_volume
            or p.volume > pin.symbol.max_volume
            or p.volume % pin.symbol.volume_step
            for p in plan.parameters
        ):
            raise ValueError("STRATEGY_VOLUME_OFF_VERIFIED_GRID")
        manifest = verify_manifest(
            objects, dataset.manifest_key, dataset.manifest_version, pin.manifest_sha256
        )
        if manifest["artifacts"] != dataset.artifacts or str(manifest["dataset_id"]) != str(
            dataset.id
        ):
            raise ValueError("DATASET_MANIFEST_REGISTRY_MISMATCH")
        rows = []
        if read:
            for row in read_rows(
                objects,
                dataset.artifacts,
                start=plan.chronology.start,
                end=min(plan.chronology.end, phase_range(plan)[1] + timedelta(microseconds=1)),
            ):
                if not row.event_time <= row.observed_at <= row.available_at:
                    raise ValueError("FUTURE_OR_UNAVAILABLE_MARKET_OBSERVATION")
                if dataset.spec[
                    "data_type"
                ] == "BAR" and row.available_at < row.event_time + timedelta(
                    seconds=TIMEFRAMES[str(dataset.spec["timeframe"])]
                ):
                    raise ValueError("BAR_HIGH_LOW_NOT_YET_AVAILABLE")
                count += 1
                if count > plan.max_rows:
                    raise ValueError("RESEARCH_ROW_QUOTA_EXCEEDED")
                if row.available_at > phase_range(plan)[1]:
                    continue
                rows.append(row)
            if not rows:
                raise ValueError("MISSING_RESEARCH_DATA")
        result.append(
            {
                "pin": pin,
                "dataset_id": str(dataset.id),
                "instrument_id": dataset.instrument_id,
                "type": dataset.spec["data_type"],
                "timeframe": dataset.spec["timeframe"],
                "provenance": dataset.spec["provenance"],
                "coverage": dataset.coverage_pct,
                "manifest": manifest,
                "rows": rows,
            }
        )
    execution = [d for d in result if d["pin"].role == "EXECUTION"]
    if not execution or len({d["instrument_id"] for d in execution}) != len(execution):
        raise ValueError("ONE_EXECUTION_STREAM_PER_INSTRUMENT_REQUIRED")
    if any(d["type"] == "BAR" for d in execution) and plan.bar_spread is None:
        raise ValueError("OHLC_REQUIRES_EXPLICIT_SYNTHETIC_SPREAD")
    return result


def phase_range(plan: ExperimentInput) -> tuple[Any, Any]:
    c = plan.chronology
    return {
        "DISCOVERY": (c.start, c.discovery_end),
        "CALIBRATION": (c.discovery_end, c.calibration_end),
        "VALIDATION": (c.calibration_end, c.validation_end),
        "FINAL_HOLDOUT": (c.validation_end, c.end),
    }[plan.phase]
