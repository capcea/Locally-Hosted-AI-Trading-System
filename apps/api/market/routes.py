"""Account-scoped, authenticated and bounded market data APIs."""

import hashlib
import json
from datetime import timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import AwareDatetime, ValidationError
from sqlalchemy import func, select

from apps.api.governance.routes import owned, writable
from apps.api.identity.dependencies import FullIdentity, Principal, settings
from apps.api.market.query_slots import QuerySlot
from packages.market.contracts import (
    CORE_SYMBOLS,
    AsOfRequest,
    AsOfResult,
    Comparison,
    DatasetPage,
    DatasetView,
    ImportSpec,
    JobView,
    ProviderInput,
    ProviderView,
    Row,
    Sample,
)
from packages.market.jobs import enqueue
from packages.market.models import IngestionJob, MarketDataset, MarketProvider
from packages.market.processing import QueryBudgetExceeded, read_rows, sample, verify_manifest
from packages.market.providers import CAPABILITIES, adapter_for
from packages.market.storage import DataIntegrityError, ObjectStore
from packages.market.time import visible
from packages.persistence.models import Instrument, TradingAccount, utcnow

router = APIRouter(prefix="/api/v1/market", tags=["Market data"])


def provider_view(row: MarketProvider) -> ProviderView:
    return ProviderView(
        id=row.id,
        name=row.name,
        adapter=row.adapter,
        rights_reference=row.rights_reference,
        attribution=row.attribution,
        capabilities=CAPABILITIES[row.adapter],
    )


def dataset_view(row: MarketDataset) -> DatasetView:
    return DatasetView(
        id=row.id,
        version=row.version,
        account_id=row.account_id,
        provider_id=row.provider_id,
        instrument_id=row.instrument_id,
        symbol=row.symbol,
        spec=ImportSpec.model_validate(row.spec),
        status=row.status,
        record_count=row.record_count,
        earliest=row.earliest,
        latest=row.latest,
        coverage_pct=row.coverage_pct,
        quality=row.quality,
        manifest_sha256=row.manifest_sha256,
        created_at=row.created_at,
        published_at=row.published_at,
    )


def job_view(row: IngestionJob) -> JobView:
    return JobView(
        id=row.id,
        dataset_id=row.dataset_id,
        state=row.state,
        attempts=row.attempts,
        progress_rows=row.progress_rows,
        error_code=row.error_code,
        next_attempt_at=row.next_attempt_at,
        created_at=row.created_at,
    )


def object_store(request: Request) -> ObjectStore:
    try:
        current = getattr(request.app.state, "market_objects", None)
        if current is None:
            current = ObjectStore(settings(request))
            request.app.state.market_objects = current
        return current
    except RuntimeError as error:
        raise HTTPException(503, "Market storage provisioning required") from error


def dataset_for(identity: Principal, dataset_id: UUID) -> MarketDataset:
    row = identity.db.scalar(
        select(MarketDataset).where(
            MarketDataset.id == dataset_id, MarketDataset.owner_id == identity.user.id
        )
    )
    if row is None:
        raise HTTPException(404, "Dataset not found")
    owned(identity, TradingAccount, row.account_id)
    from packages.research.access import sealed

    if sealed(identity.db, row):
        raise HTTPException(403, "FINAL_HOLDOUT_SEALED")
    return row


@router.get("/catalog")
def catalog(identity: FullIdentity) -> dict[str, object]:
    return {
        "suggested_symbols": list(CORE_SYMBOLS),
        "coverage_target_years": 5,
        "coverage_claim": "MEASURED_PER_DATASET_ONLY",
        "trading_enabled": False,
        "adapters": CAPABILITIES,
        "csv_columns": [
            "event_time",
            "observed_at",
            "available_at",
            "sequence",
            "bid",
            "ask",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "published_at",
            "event_id",
            "revision",
        ],
    }


@router.get("/providers", response_model=list[ProviderView])
def providers(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)
) -> list[ProviderView]:
    return [
        provider_view(r)
        for r in identity.db.scalars(
            select(MarketProvider)
            .where(MarketProvider.owner_id == identity.user.id)
            .order_by(MarketProvider.created_at, MarketProvider.id)
            .offset(offset)
            .limit(limit)
        )
    ]


@router.post("/providers", response_model=ProviderView, status_code=201)
def create_provider(body: ProviderInput, identity: FullIdentity) -> ProviderView:
    writable(identity)
    row = MarketProvider(
        owner_id=identity.user.id, **body.model_dump(exclude={"usage_rights_acknowledged"})
    )
    identity.db.add(row)
    identity.db.flush()
    identity.audit(
        "market.provider_registered",
        entity_id=row.id,
        after={"adapter": row.adapter, "rights_reference": row.rights_reference},
    )
    return provider_view(row)


def create_job(
    spec: ImportSpec,
    content: bytes,
    identity: Principal,
    request: Request,
    *,
    download: bool = False,
) -> JobView:
    writable(identity)
    provider = identity.db.scalar(
        select(MarketProvider)
        .where(MarketProvider.id == spec.provider_id, MarketProvider.owner_id == identity.user.id)
        .with_for_update()
    )
    if provider is None:
        raise HTTPException(404, "Provider not found")
    account = owned(identity, TradingAccount, spec.account_id)
    instrument = owned(identity, Instrument, spec.instrument_id)
    if (
        not isinstance(account, TradingAccount)
        or account.archived
        or not isinstance(instrument, Instrument)
    ):
        raise HTTPException(409, "Active owned account and instrument required")
    if download:
        if not adapter_for(provider.adapter).network or spec.provenance != "PUBLIC_PROVIDER":
            raise HTTPException(409, "Only the allowlisted ECB public downloader is available")
    elif not adapter_for(provider.adapter).allows_upload or spec.provenance == "PUBLIC_PROVIDER":
        raise HTTPException(
            409, "Local/MT5 export imports require explicit user/fixture provenance"
        )
    data = spec.model_dump(mode="json")
    source_hash = hashlib.sha256(content).hexdigest()
    idempotency = hashlib.sha256(
        json.dumps([data, source_hash], sort_keys=True).encode()
    ).hexdigest()
    old = identity.db.scalar(
        select(IngestionJob).where(
            IngestionJob.owner_id == identity.user.id, IngestionJob.idempotency_key == idempotency
        )
    )
    if old:
        return job_view(old)
    count = (
        identity.db.scalar(
            select(func.count())
            .select_from(MarketDataset)
            .where(MarketDataset.owner_id == identity.user.id)
        )
        or 0
    )
    active = (
        identity.db.scalar(
            select(func.count())
            .select_from(IngestionJob)
            .where(
                IngestionJob.owner_id == identity.user.id,
                IngestionJob.state.in_(["QUEUED", "RUNNING", "RETRY"]),
            )
        )
        or 0
    )
    if count >= settings(request).market_max_datasets or active >= 5:
        raise HTTPException(429, "Dataset or concurrent-job quota reached")
    series_fields = {
        key: data[key]
        for key in (
            "provider_id",
            "account_id",
            "instrument_id",
            "source_symbol",
            "data_type",
            "timeframe",
            "start",
            "end",
            "transform_timeframe",
        )
    }
    series = hashlib.sha256(json.dumps(series_fields, sort_keys=True).encode()).hexdigest()
    version = (
        identity.db.scalar(
            select(func.max(MarketDataset.version)).where(MarketDataset.series_key == series)
        )
        or 0
    ) + 1
    row = MarketDataset(
        owner_id=identity.user.id,
        account_id=spec.account_id,
        provider_id=provider.id,
        instrument_id=instrument.id,
        symbol=instrument.symbol,
        series_key=series,
        version=version,
        spec=data,
        input_sha256=source_hash,
        input_key="",
        input_version="",
        input_size=len(content),
    )
    identity.db.add(row)
    identity.db.flush()
    info = object_store(request).put(f"uploads/{identity.user.id}/{row.id}/original", content)
    row.input_key, row.input_version = str(info["key"]), str(info["version"])
    job = IngestionJob(owner_id=identity.user.id, dataset_id=row.id, idempotency_key=idempotency)
    identity.db.add(job)
    identity.db.flush()
    identity.audit(
        "market.import_requested",
        entity_id=row.id,
        after={"sha256": source_hash, "version": version, "provenance": spec.provenance},
    )
    # Hint may arrive before commit; the worker always scans the durable DB outbox as well.
    enqueue(settings(request), job.id)
    return job_view(job)


@router.post("/imports", response_model=JobView, status_code=202)
async def import_file(
    request: Request,
    identity: FullIdentity,
    spec_json: Annotated[str, Form(max_length=200000)],
    file: Annotated[UploadFile, File()],
) -> JobView:
    try:
        spec = ImportSpec.model_validate_json(spec_json)
    except (ValidationError, ValueError) as error:
        raise HTTPException(422, "Invalid import metadata") from error
    content = bytearray()
    try:
        while chunk := await file.read(65536):
            content.extend(chunk)
            if len(content) > settings(request).market_upload_bytes:
                raise HTTPException(413, "Import exceeds byte quota")
    finally:
        await file.close()
    if not content:
        raise HTTPException(422, "Empty imports are prohibited")
    return create_job(spec, bytes(content), identity, request)


@router.post("/jobs", response_model=JobView, status_code=202)
def download_job(body: ImportSpec, identity: FullIdentity, request: Request) -> JobView:
    return create_job(body, b"", identity, request, download=True)


@router.get("/jobs", response_model=list[JobView])
def list_jobs(
    identity: FullIdentity, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)
) -> list[JobView]:
    return [
        job_view(r)
        for r in identity.db.scalars(
            select(IngestionJob)
            .where(IngestionJob.owner_id == identity.user.id)
            .order_by(IngestionJob.created_at.desc(), IngestionJob.id)
            .offset(offset)
            .limit(limit)
        )
    ]


@router.post("/jobs/{job_id}/cancel", response_model=JobView)
def cancel_job(job_id: UUID, identity: FullIdentity) -> JobView:
    writable(identity)
    row = identity.db.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == job_id, IngestionJob.owner_id == identity.user.id)
        .with_for_update()
    )
    if row is None:
        raise HTTPException(404, "Job not found")
    if row.state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
        raise HTTPException(409, "Job is already terminal")
    row.cancel_requested = True
    if row.state in {"QUEUED", "RETRY"}:
        row.state = "CANCELLED"
        data = dataset_for(identity, row.dataset_id)
        data.status = "REJECTED"
    identity.audit("market.job_cancel_requested", entity_id=row.id)
    return job_view(row)


@router.get("/datasets", response_model=DatasetPage)
def datasets(
    identity: FullIdentity,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    account_id: UUID | None = None,
    q: str = Query("", max_length=80),
    status: str | None = None,
) -> DatasetPage:
    from packages.research.access import public_query

    query = public_query(identity.user.id)
    if account_id:
        owned(identity, TradingAccount, account_id)
        query = query.where(MarketDataset.account_id == account_id)
    if q:
        query = query.where(MarketDataset.symbol.contains(q, autoescape=True))
    if status:
        query = query.where(MarketDataset.status == status)
    total = identity.db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = identity.db.scalars(
        query.order_by(MarketDataset.created_at.desc(), MarketDataset.id)
        .offset(offset)
        .limit(limit)
    )
    return DatasetPage(
        items=[dataset_view(r) for r in rows], offset=offset, limit=limit, total=total
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetView)
def dataset(dataset_id: UUID, identity: FullIdentity) -> DatasetView:
    return dataset_view(dataset_for(identity, dataset_id))


@router.get("/datasets/{dataset_id}/provenance")
def provenance(dataset_id: UUID, identity: FullIdentity, request: Request) -> dict[str, Any]:
    row = dataset_for(identity, dataset_id)
    if not row.manifest_key or not row.manifest_version or not row.manifest_sha256:
        raise HTTPException(409, "Dataset has not been atomically published")
    return verify_manifest(
        object_store(request), row.manifest_key, row.manifest_version, row.manifest_sha256
    )


@router.get("/datasets/{dataset_id}/sample", response_model=Sample)
def historical(
    dataset_id: UUID,
    identity: FullIdentity,
    request: Request,
    start: AwareDatetime,
    end: AwareDatetime,
    decision_at: AwareDatetime,
    slot: QuerySlot,
    limit: int = Query(500, ge=1, le=2000),
    layer: str = Query("normalized", pattern="^(normalized|derived)$"),
    preview: bool = False,
    sequence_cutoff: int | None = Query(None, ge=0),
) -> Sample:
    row = dataset_for(identity, dataset_id)
    if end <= start or (end - start).days > 3660:
        raise HTTPException(422, "Bounded positive range required")
    if row.status not in {"VALID", "DEGRADED"} or (row.status != "VALID" and not preview):
        raise HTTPException(409, "Quality gate denies research use; explicit degraded preview only")
    if decision_at > utcnow():
        raise HTTPException(422, "Historical decision cutoff cannot be in the future")
    if not row.manifest_key or not row.manifest_sha256 or not row.manifest_version:
        raise DataIntegrityError("Manifest missing")
    store = object_store(request)
    manifest = verify_manifest(store, row.manifest_key, row.manifest_version, row.manifest_sha256)
    try:
        rows, truncated = sample(
            store, manifest["artifacts"], start, end, decision_at, limit, layer, sequence_cutoff
        )
    except QueryBudgetExceeded as error:
        raise HTTPException(422, "Narrow the historical range; scan budget reached") from error
    return Sample(
        items=rows,
        truncated=truncated,
        limit=limit,
        dataset_id=row.id,
        decision_at=decision_at,
        quality_status=row.status,
        provenance=str(row.spec["provenance"]),
        research_eligible=row.status == "VALID",
    )


@router.get("/datasets/{dataset_id}/compare/{other_id}", response_model=Comparison)
def compare(dataset_id: UUID, other_id: UUID, identity: FullIdentity) -> Comparison:
    left, right = dataset_for(identity, dataset_id), dataset_for(identity, other_id)
    return Comparison(
        left=left.id,
        right=right.id,
        same_series=left.series_key == right.series_key,
        same_input=left.input_sha256 == right.input_sha256,
        row_count_delta=right.record_count - left.record_count,
        left_status=left.status,
        right_status=right.status,
    )


@router.post("/asof", response_model=AsOfResult)
def point_in_time(
    body: AsOfRequest, identity: FullIdentity, request: Request, slot: QuerySlot
) -> AsOfResult:
    owned(identity, TradingAccount, body.account_id)
    if body.decision_at > utcnow() or body.start >= body.decision_at:
        raise HTTPException(422, "Positive historical decision window required")
    observations: dict[str, Row | None] = {}
    store = object_store(request)
    for dataset_id in body.dataset_ids:
        row = dataset_for(identity, dataset_id)
        if row.account_id != body.account_id or row.status != "VALID":
            raise HTTPException(
                409, "As-of research requires VALID datasets in this account partition"
            )
        if not row.manifest_key or not row.manifest_version or not row.manifest_sha256:
            raise DataIntegrityError("Manifest unavailable")
        manifest = verify_manifest(
            store, row.manifest_key, row.manifest_version, row.manifest_sha256
        )
        values: list[Row] = []
        for number, record in enumerate(
            read_rows(
                store,
                manifest["artifacts"],
                start=body.start,
                end=body.decision_at + timedelta(microseconds=1),
            )
        ):
            if number >= 100000:
                raise HTTPException(422, "Narrow the as-of range; scan budget reached")
            if visible(record, body.decision_at, body.sequence_cutoffs.get(dataset_id)) and (
                not values
                or (record.event_time, record.available_at, record.revision, record.sequence)
                > (
                    values[0].event_time,
                    values[0].available_at,
                    values[0].revision,
                    values[0].sequence,
                )
            ):
                values = [record]
        observations[str(dataset_id)] = values[0] if values else None
    return AsOfResult(decision_at=body.decision_at, observations=observations)
