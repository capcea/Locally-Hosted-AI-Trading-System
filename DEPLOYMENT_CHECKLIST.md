# Deployment Checklist

Updated: 2026-10-26. **Current decision: local foundation only; no public/shared, autonomous
research, paper, demo-execution or live deployment is accepted.** This checklist is a record of
gates, not authorization to connect a broker, submit an order, buy infrastructure or enable LIVE.

Legend: checked means evidence exists for the exact statement; unchecked means unresolved.
Never convert a blocked or not-run item into a pass.

## Gate 0 — reproducible local foundation

- [x] Original supplied specification matches docs/PRODUCT_SPEC.md by SHA-256.
- [x] Python/npm locks and runtime pins exist; installed environment passes lint/types/build.
- [x] 98 portable/unit Python tests (including the foundation tests) and 16 frontend tests pass.
- [x] Invalid LIVE/worker capability configuration is rejected; API/worker execution remains denied.
- [x] Actual local API smoke validates safety and receives 403 for both refusal endpoints.
- [x] Existing local .env observed as 0600; secret values not included in reports.
- [x] Development and disposable Compose syntax validate; this does not establish running containers.
- [x] Repository exclusions, source secret/dependency scans, generated contract check and actionlint pass.
- [x] Disposable migration/storage/queue test harness prepared with scoped cleanup and guard tests.
- [x] Actual disposable harness write/restart/verify stages run successfully.
- [ ] Local initial commit created; current managed .git access is read-only.
- [ ] Owner explicitly approves private GitHub repository creation and push; neither has occurred.
- [x] Docker engine available; existing API/Web/PostgreSQL/Redis/MinIO containers healthy.
- [x] Disposable services start and the custom MinIO image build succeeds using cached layers.
- [x] Migration upgrade/downgrade/upgrade succeeds against disposable PostgreSQL.
- [x] PostgreSQL schema/transaction, Redis graceful-restart persistence and authenticated MinIO PUT/GET
      round-trips pass with disposable test data and explicit test service identities.
- [x] make integration and strict readiness smoke pass against those real local services.
- [x] Dynamic 127.0.0.1 bindings and actual TCP connectivity verified before/after restart.
- [x] Disposable cleanup verified; existing development data container identities/mounts preserved.
      Stopped data services were resumed during Phase 2; their start times changed as expected.
- [ ] All ten Phase 0/1/2 desktop/mobile Playwright tests execute and pass after the OS permits Chromium.
- [ ] Rendered desktop/mobile, keyboard/focus/contrast, theme and outage states are inspected.
- [ ] Remote CI passes from a committed source snapshot; container vulnerability scans are clean
      or findings are explicitly triaged, not hidden by a startup failure.
- [ ] Fresh-machine install/build/restart is reproduced using locked versions.

Phase 1 update, 2026-10-26: identity/governance migration and local API/Web build/start pass;
20 disposable native cases pass before and after restart, including the three original service tests.
The owner authorized browser testing, but Chromium launch still failed with OS Permission denied
(1100). Three desktop browser cases failed; one HTTP-only case passed; mobile was not run.
Phase 1 acceptance remains BLOCKED. See [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md).

Verified on 2026-10-26: Docker 29.7.2 is available, the existing stack is healthy, and the complete
integration suite passes. The internal-only disposable network was replaced with a project-scoped
bridge; host ports are dynamic and exclusively bound to 127.0.0.1. See the
[integration evidence](docs/phase0-evidence/2026-10-26-integration/README.md).
For later verification with the development stack already running:

```sh
docker info --format '{{.ServerVersion}}'
make doctor
make integration
.venv/bin/python -m scripts.smoke_demo --require-ready
```

The new `make integration-services` also runs independently and creates/removes only its unique
disposable project. `make integration` requires application readiness, this isolated suite and strict
API readiness. These service commands passed in the recorded run. make dev applies migrations
deliberately; Phase 1 was additively migrated after a private pg_dump. Verify .env targets intended services.
Never use these development credentials or database defaults for production.

When the execution environment permits Chromium, use disposable Phase 1 identities:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" make browser-integration
```

The existing browser suite needs Chromium installed. Without external servers, the test config
starts its own API/Vite processes and refuses to reuse existing ones. Do not bypass a browser
security denial by changing port, browser tool or execution route.

## Gate 1 — shared control plane, identity and persistence

- [x] Owner account, Argon2id, roles, persistent sessions and scoped authorization pass native tests.
- [x] Owner TOTP/recovery/replay, rotation/revocation, CSRF and persistent rate limits pass native tests.
- [ ] Browser identity/management acceptance; authenticated streaming if later introduced.
- [x] Separate restricted API database role from migration/admin identity; audit rewrites denied.
- [ ] Independent audit-writer identity/service and scoped object-storage credentials for production.
- [ ] Authenticate Redis/internal services; use private networks and TLS/mTLS where appropriate.
- [ ] Reject secret-bearing URLs; verify app/proxy/error logs and traces cannot disclose credentials.
- [ ] Adopt secret manager, scoped deployment identities, rotation/revocation and recovery runbooks.
- [x] Account ownership/SIMULATED partitions, immutable policy/strategy content and audit identifiers.
- [x] Durable append-only audit, HMAC chain/head verification and transactionally coupled events.
- [ ] Independent audit anchor, retention and full causal decision replay.
- [x] Pin CI Actions to verified immutable revisions and disable persisted checkout credentials.
- [ ] Run remote CI, scan built containers and generate provenance/SBOM.
- [ ] Configure encrypted off-host backups and demonstrate restore with checksums and measured RPO/RTO.
- [ ] Verify no development service or unauthenticated control endpoint is publicly exposed.

Required infrastructure: dedicated control host, private DNS/TLS or equivalent, PostgreSQL/Redis/
object storage identities, off-host backup destination and a secrets service. These production
services are not provisioned or validated. Local keys/runtime role are provisioned.
No external broker credential is needed for Gate 0 or 1.

## Gate 2 — data and deterministic simulation

- [ ] Approve actual data/calendar sources, entitlements, retention rights and budgets.
- [ ] Implement immutable raw/derived Parquet, manifests, checksums and coverage/QC reports.
- [ ] Test source sequences, publication/availability times, UTC/DST, sessions and stale calendars.
- [ ] Verify feature cutoffs/as-of joins, fold-local fitting, purging/embargo and frozen holdouts.
- [ ] Implement event-driven fill/cost engine and validate deterministic expected trade ledgers.
- [ ] Measure spread/fee/latency/slippage assumptions and label estimated/missing data explicitly.
- [ ] Implement statistical gates, trial registry, confidence bounds and regime/sample adequacy.
- [ ] Keep five-year coverage incomplete until actual source/symbol coverage demonstrates it.

External inputs: licensed or permitted historical feeds, symbol metadata and economic-calendar
access; API keys only if the chosen source requires them. Sources/providers are not selected or
certified yet. Do not manufacture datasets or claim coverage from configuration fixtures.

## Gate 3 — isolated AI research

- [ ] Provision a private authenticated LLM gateway; verify actual model/runtime/quantization digests.
- [ ] Implement VM/microVM hostile-code isolation, immutable inputs and resource/time quotas.
- [ ] Deny broker/deployment secrets, host mounts, Docker socket and non-allowlisted egress.
- [ ] Prevent agent writes to auth/risk/governance/executor/release code and protected branches.
- [ ] Run escape, exfiltration, prompt-injection, filesystem and resource-exhaustion tests.
- [ ] Validate every agent/tool response; model outputs remain proposal-only.
- [ ] Implement persistent jobs, retries/idempotency, crash recovery, priorities and cost ceilings.
- [ ] Measure model VRAM/context switching and cloud/local reproducibility before continuous usage.

External dependencies: appropriately isolated compute, private gateway identity/certificate and
pinned model artifacts. Paid GPU hosting, continuous runs and deployment credentials require
separate owner scope. No broker credentials belong on this host.

## Gate 4 — independent execution and future demo validation

- [x] Implement shared broker contract and deterministic fault-injectable simulator (Phase 3 native-tested).
- [ ] Implement independent risk gateway with Decimal sizing, verified FX/symbol specs, transactional
      exposure reservations, exact policy packs, fresh quotes/calendars and fail-closed uncertainty.
- [ ] Complete future external intent/risk outbox; synthetic journal and duplicate/submit-before-ack crash tests now pass.
- [ ] Certify external UNKNOWN/native protection; synthetic UNKNOWN/partial/rejection reconciliation now passes.
- [ ] Separate durable stop-new-entries from expressly authorized flatten.
- [ ] Confine broker credentials and broker egress to executor identities and hosts.
- [ ] Verify signed/capability-limited control-to-executor messages; deny every unapproved strategy.
- [ ] Supply and separately authorize actual demo access only after adapter/risk boundaries exist.
- [ ] Run actual MT5 and cTrader demo contract/reconnect/protection tests; retain redacted service
      responses and timestamps. Mock or simulator results never certify these integrations.
- [ ] Verify exact firm/program/platform/account policy and broker instrument availability manually.
- [ ] Test GPU/control-plane outage while an authorized future demo scenario remains protected.

Future credentials/infrastructure, **not requested or inserted during this audit**:

- MT5: Windows host/terminal, demo-only login/server/password and terminal path, stored only on the
  Windows connector; authenticated private bridge identity. Read-only adapter source exists; actual connectivity is unverified.
- cTrader: registered application/client identity and secret, authorized callback and scoped OAuth
  access/refresh tokens for an explicit demo account, stored only on its connector. Read-only adapter source exists; actual connectivity is unverified.
- Program policies: exact firm, program, phase, platform, account size and verified source/effective
  dates. A brand name or dated master-spec example is not account authorization.
- Private channels: short-lived executor identities/certificates and restrictive firewall policy.
  Tokens or broker credentials must not be pasted into chat, source, GPU config or control-plane .env.

The current request prohibits real broker orders. This checklist does not authorize even a
demo-service order test in the current audit; any later service interaction must have appropriate
scope and the required implemented safety boundaries.

## Gate 5 — paper and operational acceptance

- [ ] Implement immutable strategy lifecycle, reproducible paper logic and adaptive observation gates.
- [ ] Prevent candidates/agents from relaxing their own thresholds or promoting to live.
- [ ] Implement degradation auto-pause and owner-only reactivation.
- [ ] Implement complete functional UI with permissioned emergency actions and causal replay.
- [ ] Configure notification delivery with actual receipt tests, redaction, retry and deduplication.
- [ ] Implement tracing/metrics/incidents, dependency outage handling and cost circuit breakers.
- [ ] Run load/fault/restart/backup-restore tests and reversible cloud-to-local migration rehearsal.

Future notification secrets: SMTP/API credentials and verified sender/recipient for email; Telegram
bot token and owner-approved destination for notifications. Authenticated/replay-protected emergency
commands need separate implementation and authorization. No messages were sent during this audit.

## LIVE remains blocked

- [ ] Owner identity/MFA plus two explicit acknowledgements implemented and tested.
- [ ] Durable signed approval binds immutable strategy/config/model-dependent logic, account, broker,
      program, symbols, risk profile and expiry; changes invalidate it.
- [ ] Revocation, signature tamper, replay, expiry, policy updates and risk bypass tests pass.
- [ ] Independent executor verifies the same approved scope and preserves kill state across restart.
- [ ] Complete security/risk/operations review performed against actual deployed identities/services.
- [ ] Owner separately authorizes any future live-readiness decision.

**No step in this audit activates LIVE. Do not replace DENY_ALL, insert real-money credentials,
submit real orders or enable automated live promotion as part of resolving this checklist.**


## Phase 2 local data gate — 2026-10-26

- [x] Migration 0003, scoped dataset/provider/job metadata and immutable published records.
- [x] Actual CSV/Parquet input, Zstandard parts, pinned MinIO versions/COMPLIANCE and SHA-256 checks.
- [x] Declared timezone/DST, availability, release-vintage and as-of guards; quality refusal.
- [x] Durable DB job outbox, Redis hints, backoff/cancellation and real killed-worker recovery.
- [x] Actual ECB reference-rate access; no tick/OHLC/spread/volume capability inferred from it.
- [x] Private backup before additive development migration; existing Phase 1 records/volumes preserved.
- [x] Market Data API/UI source, contracts, bounded imports/queries and measured native benchmarks.
- [ ] All ten Phase 0/1/2 desktop/mobile browser cases pass in an administrator-permitted environment.
- [ ] Multi-year production/tick-scale performance, licensed coverage and calendar/provider acceptance.
- [ ] MT5 Windows terminal integration tested with separately authorized connectivity; premium sources.
- [ ] Retention/orphan capacity management, off-host backups and full restore validated.

The data worker executes fixed ingestion code while generated-code execution remains prohibited.
It receives no broker credentials, MinIO root identity or PostgreSQL admin identity. New data objects
use default 30-day COMPLIANCE retention; a protected object's retention cannot be shortened. Plan
capacity before importing valuable/large files. No public deployment, broker execution or Phase 3 is
part of this gate. See PHASE2_COMPLETION_REPORT.md and docs/DATA_PROVENANCE.md for exact limitations.

## Phase 3 local simulation/read-only gate — 2026-10-27

This section supersedes earlier statements that no broker contract or fill engine exists. The
historical Phase 2 gate remains evidence for that phase; it is not a claim that Phase 3 was already
accepted. See PHASE3_COMPLETION_REPORT.md and docs/phase3-evidence/2026-10-27/README.md.

- [x] Shared exact broker/simulation/future risk contracts without execution authority.
- [x] Synthetic market/limit/stop/protection/partial/netting/hedging/OCO/funding assumptions documented.
- [x] Additive 0004 journal migration; immutable events/receipts/observations and atomic HMAC audit.
- [x] Duplicate/concurrent processing, UNKNOWN/reconcile, real process kills and DB restart tests.
- [x] Actual VALID Phase 2 MinIO tick replay, manifest/time/sequence checks; no invented spreads/ticks.
- [x] Existing owner/MFA/role/CSRF/account isolation and every external execution denial preserved.
- [x] Main images exclude bridge source/MT5 SDK, broker credentials and Docker socket mounts.
- [x] Separate connector image builds/starts help with no network; real local mTLS/bearer test passes.
- [x] Windows MT5 and cTrader read-only source/contracts present; fixtures explicitly labeled.
- [x] `make check`, real-service `make integration`, smoke and generated API contracts pass.
- [x] Local services healthy, revision0004; original data IDs/mounts retained. Identity enrollment
      since the early backup is explicitly accounted for; no blanket unchanged-record claim.
- [ ] All 12 desktop/mobile cases pass in an administrator-permitted environment. Current managed
      Chromium launch is denied (1100); no launch restriction was bypassed.
- [ ] Authorized real Windows MT5 demo terminal, investor access, API-trading-disabled identity and
      actual metadata/quote/history/reconnect tests. SCM/NTFS ACL/Job runtime still NOT TESTED.
- [ ] Authorized registered cTrader app/callback, verified accounts-only OAuth scope and demo account;
      actual token refresh/revocation/quote/reconnect tests. HTTP OAuth tests currently MOCKED.
- [ ] Private PKI/service identities, secret provisioning/rotation, scoped connector egress and actual
      deployed-host isolation acceptance. Credentials belong only on their connector host.
- [ ] Continuous central bridge polling/automatic synchronization (currently signed owner upload).
- [ ] Remote CI, connector/container vulnerability/SBOM, Windows optional dependency audit, full
      backup restore and fresh-machine/production-load acceptance.
- [ ] Independent Phase 4 risk sizing/exposure/policy/calendar authorization gateway, separately scoped.

No checkbox authorizes DEMO_EXECUTION or LIVE. All external submission/cancel/modify remains denied.
Do not introduce broker credentials to central .env, change safety flags, run generated code or
start Phase 4 automatically. Controlled future read-only setup is in docs/BROKER_RUNBOOK.md.

## Phase 4 simulated risk gate — 2026-10-27

This section supersedes earlier claims that the independent simulated risk gateway does not exist.
It grants no external demo/live order authority. See PHASE4_COMPLETION_REPORT.md and its evidence ledger.

- [x] Exact Decimal sizing for explicitly verified linear payoff/tick/margin/FX contracts; unsupported
      inverse/missing/conflicting/stale facts fail closed. No approximate pip or actual broker proof.
- [x] Versioned account/strategy/instrument/asset/firm/program profiles; latest verified personal/prop
      policy, exact revision/effective period/provenance, owner recent MFA and strictest ceilings.
- [x] Persistent account equity/drawdown/reservation ledger; explicit midnight/DST/high-water rules,
      fees/funding and conservative UNKNOWN/partial exposure accounting.
- [x] Mandatory journal risk assessment and actual-fill reevaluation; signed consumed scopes and atomic
      allocations. Real multiprocess competition, process kills, rollback and service restart tested.
- [x] Durable STOP and separate privileged simulated FLATTEN, replay/scope/MFA protection and incidents.
- [x] Fixed-code independent monitor container, restricted DB role, control-only network/no public port,
      no broker/admin/storage-root/bootstrap credentials or Docker socket, bounded resources.
- [x] Fresh private pre-migration backup, additive revision0005, no ORM drift; existing data container IDs
      and mounts preserved. All 29 other legacy hashes match; session idle renewal verified separately.
- [x] Local images/stack built and healthy; strict readiness200, safe overview Phase4; execution flagsfalse.
- [x] Romanian real-API Risk Center, global emergency banner, generated contract and E2E source present.
- [ ] All 14 desktop/mobile browser workflows execute and pass in the authorized local environment.
      Current managed Chromium still fails before page creation with Permission denied (1100).
- [ ] Separate actual broker-side executor/signing identity/capability checks, real margin/protection,
      external account/service integration and production load/restore/rotation acceptance.
- [ ] Remote CI/committed source, container vulnerabilities/SBOM and fully reviewed public deployment.

Reproduce without changing safety flags or owner records:

```sh
make check
make contracts-check
make smoke-demo
make integration
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=risk make browser-integration
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" make browser-integration
make secret-scan
```

The disposable harness cleans only its UUID-owned test resources. Do not delete development volumes,
introduce credentials, publish/push, bypass managed browser protections or start Phase 5 automatically.
