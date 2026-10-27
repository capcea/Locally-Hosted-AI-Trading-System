# Implementation Status

Updated: 2026-10-27 · API 0.1.0 · Phase 4 · SIMULATED · external DENY_ALL.

**Phase 4 is implemented and native-tested; full acceptance is BLOCKED by managed Chromium launch.**
Owner-reported Phase 3 local passes are OWNER_REPORTED_PASS, separate from current agent evidence.
No external demo/live execution, generated code, real broker credentials, promotion, publish/push or
Phase 5 started. See [PHASE4_COMPLETION_REPORT.md](PHASE4_COMPLETION_REPORT.md).

## Specification traceability

The original master and docs/PRODUCT_SPEC.md retain SHA-256
c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085.
A01–A60 below are derived audit criteria, not reconstructed original questionnaire numbering.
4 fully functional, 37 partially implemented, 0 mocked-only and 19 missing. These are scope labels, not effort percentages or acceptance percentages.
Earlier reports remain historical evidence; current Phase 4 status supersedes their missing-risk claims.

## Current acceptance

- PASSED: `make check`: lint/format, Python/TypeScript types, 179 portable Python and 16 frontend
  tests, production frontend build. 61 service/infrastructure cases are deselected and tested separately.
- PASSED: `make integration-services`: 60 actual disposable PostgreSQL/Redis/MinIO security/data/
  execution/risk cases per write and restart stage. Final `make integration` also passes one running-API readiness case and strict smoke200.
- PASSED: actual multiprocess reservation competition, SIGKILL before/after commit, durable STOP,
  UNKNOWN retention, partial releases, tamper/replay, cross-currency P&L, midnight gap and funding cases.
- PASSED: additive 0005 with fresh private backup; all data container IDs/mounts unchanged, 29 legacy
  hashes unchanged, session idle renewal verified field-by-field against backup. Owner/MFA retained.
- PASSED: no ORM drift; immutable-table runtime grants; API/web/market-worker/risk-monitor healthy,
  readiness200 and external flags false; isolated monitor packaging/key/network boundary verified.
- PASSED: generated OpenAPI/TS, Compose/Actions syntax, npm/Python dependency audits. Final fresh
  secret/repository scans and exact command outcomes are in the report/evidence ledger.
- FAILED/BLOCKED: focused risk desktop command failed at Chromium Permission denied (1100), before
  page creation. Full suite attempt: 3 desktop launch failures, 1 HTTP-only denial pass, 10 NOT RUN.
  All 14 desktop/mobile cases collect. No assertions weakened, browser protections bypassed or skips added.
- MOCKED/CONTRACT_FIXTURE: historical MT5 fake SDK and cTrader protocol/OAuth fixtures; actual external
  broker/Windows/deployed-service acceptance remains BLOCKED/unverified.
- NOT IMPLEMENTED: broker-capable independent executor/signing identity, live approvals, generated-code
  sandbox, AI/research/statistical/backtest/paper/promotion/notification modules. No external authority.
- NOT RUN: remote CI, Windows optional dependency/container vulnerability/SBOM, production scale and
  complete off-host backup restore. .git remains read-only; no commit/remote/push created.

## Phase 4 module inventory

- IMPLEMENTED/NATIVE TESTED: packages/risk contracts/clock/sizing/policy/ledger/authorization/gateway/
  monitor, ten models and additive 0005 migration; exact Decimal linear payoffs, conservative FX,
  reference/cost/exposure math, scoped policy/profile revisions and refusal on uncertainty.
- IMPLEMENTED/NATIVE TESTED: mandatory packages/execution journal/fill integration; exact account locks,
  grants/uses/reservations, rollback, duplicate receipts, actual process competition/kills and restart.
- IMPLEMENTED/NATIVE TESTED: apps/api/risk schemas/routes, bounded authenticated/MFA configuration,
  policy attestation, status/history/what-if/monitor and durable STOP/CLEAR/separate simulated FLATTEN.
- IMPLEMENTED/RUNTIME VERIFIED: fixed-code scripts/risk_monitor and Compose service; no broker/admin/
  root-storage/bootstrap keys, Docker socket, public port or generated-code capability. Current dev
  has zero configured risk accounts; `--once` verifies packaging/startup, native fixtures test behavior.
- IMPLEMENTED/BROWSER BLOCKED: RiskCenter/RiskBanner, BrokerCenter protection fields, generated types
  and phase3/phase4 E2E real-API workflows. Their source/build is verified; rendered behavior is unverified.
- PARTIAL/EXTERNAL NOT IMPLEMENTED: current SIM HMAC is trusted-host authority, not an independent
  broker executor. Owner financial/calendar evidence is explicit synthetic input; actual market truth,
  real margin/tradability/protection, current firm terms and broker orders are not certified.

## Prior modules retained

Phase 1 identity/governance/MFA/CSRF/role/account partitions and append-only HMAC audit remain intact.
Phase 2 bounded ingestion/quality/PIT/MinIO immutability, fixed worker/Redis outbox and actual ECB
reference adapter remain implemented and native-tested. Phase 3 deterministic simulator/journal,
immutable receipts, UNKNOWN/reconciliation, VALID dataset replay and read-only connector contracts
remain implemented. Actual MT5/cTrader connectivity is unverified; OAuth/fake-SDK tests are fixtures.
No source dataset, owner enrollment or persistent development volume was deleted.

## All 60 derived audit criteria

Each entry gives the master-spec sections, implementation evidence and the next acceptance gate.
“Missing” means no operational implementation was found, even when a design document exists.

### A01 — Personal/prop accounts, $25k reference and multi-account partitions

**PARTIALLY IMPLEMENTED.** Evidence: Persistent SIMULATED accounts, exact capital and owner partitions now have account-wide cash/equity/drawdown and risk reservations across runs; native tests pass.

Actual broker balances/accounts remain unverified; synthetic balances are never broker observations.

### A02 — Versioned exact firm/program/phase/platform policies

**PARTIALLY IMPLEMENTED.** Evidence: Immutable provenance/effective/scope policy versions now bind exact account/program revisions and typed risk semantics; latest unknown/expired/revoked policy blocks the journal gateway.

Owner attestation is not automatic certification of current official firm rules or external trading permission.

### A03 — Honest simulation, source and performance labels

**FULLY FUNCTIONAL.** Source: §0 invariants 7/10, §15. Evidence: packages/domain/contracts.py; scripts/seed_demo_data.py; tests/test_bootstrap.py; tests/test_health.py.

Source labels cover Phase 0 reference output, Phase 2 data provenance and Phase 3 synthetic fills/fixture observations. Real broker observations remain unverified.

### A04 — Forex/metals/indices/crypto and broker-specific tradability

**PARTIALLY IMPLEMENTED.** Evidence: Synthetic SymbolSpec and nullable observed BrokerSymbol include asset class, symbol/grid/volume/capabilities with pinned identity; packages/brokers/contracts.py; packages/execution/contracts.py.

Actual external symbols/tradability remain unverified; the catalog is not trading permission.

### A05 — Scalping/intraday profiles and prohibited-style filtering

**PARTIALLY IMPLEMENTED.** Evidence: Typed execution-style, automation, duration, overnight/weekend and permitted-symbol policy checks now gate simulated entries and monitor holdings.

Actual strategy families, calibrated scalping/intraday performance and external venue validation remain missing.

### A06 — Ticks and M1/M5/M15/H1/H4, optional D1

**PARTIALLY IMPLEMENTED.** Source: §1, §5. Evidence: CSV/Parquet ticks and M1/M5/M15/H1/H4/D1 contracts, exact normalized rows and deterministic complete-bar aggregation are implemented; actual ticks/bars/Parquet service tests pass.

Intraday/tick external provider coverage and browser acceptance remain unverified; no history is fabricated.

### A07 — UTC/DST, venue sessions, holidays, rollover/weekend handling

**PARTIALLY IMPLEMENTED.** Evidence: UTC/DST fold/nonexistent guards, explicit local daily resets, session/holiday validation, overnight/weekend/duration restrictions and pre-loss midnight references are implemented and tested.

Actual external calendar/rollover validation and future live scheduling remain unverified.

### A08 — Economic calendar freshness and event blackouts

**PARTIALLY IMPLEMENTED.** Evidence: Point-in-time release rows plus required fresh synthetic calendar evidence and currency/event blackout checks now gate the simulator; outage/blackout cases pass native tests.

An active external economic calendar provider is NOT IMPLEMENTED; imported assertions are not certified market facts.

### A09 — Market orders with confirmed broker-side SL/TP

**PARTIALLY IMPLEMENTED.** Evidence: Synthetic market orders with SL/TP, actual-fill protection geometry and adverse gap tests are implemented in packages/execution/engine.py.

No real broker orders or confirmed broker-side protection; external execution is DENY_ALL.

### A10 — Pending/modify/cancel/trailing/break-even/partial close/OCO

**PARTIALLY IMPLEMENTED.** Evidence: Synthetic limit/stop/cancel/expire/modify/partial-close and explicit modeled OCO pass exact lifecycle tests.

Real broker semantics and automated trailing/break-even are not implemented or certified.

### A11 — Continuous autonomous research bounded by resources

**MISSING.** Source: §1, §9. Evidence: workers/safety.py denies; no runner.

Implement durable scheduling with CPU/GPU/time/memory/budget quotas and recovery.

### A12 — Restricted web research, evidence and citations

**MISSING.** Source: §1, §9. Evidence: No research tool gateway.

Implement allowlisted tools, evidence snapshots, dates and prompt-injection containment.

### A13 — Nine research/review/orchestrator agent roles

**MISSING.** Source: §9. Evidence: No agents package.

Implement typed role outputs and independent review; test invalid/adversarial outputs.

### A14 — Isolated code branches and controlled release promotion

**MISSING.** Source: §0 invariant 4, §9, §15. Evidence: AGENTS.md describes future restrictions.

Implement artifact-specific write capabilities and a release manager outside agent control.

### A15 — Strategy families and non-ML baselines

**MISSING.** Source: §1, §6. Evidence: No strategy implementations.

Implement versioned deterministic baselines, stop/exit declarations and compliance filtering.

### A16 — XGBoost, LightGBM, HMM/clustering comparisons

**MISSING.** Source: §1, §6. Evidence: No ML training/evaluation module.

Implement fold-local training, reproducible artifacts and baseline/OOS comparisons.

### A17 — Time-available features and fold-local preprocessing

**MISSING.** Source: §5–6. Evidence: docs/EXPERIMENT_PROTOCOL.md only.

Enforce availability timestamps and fit transforms only within training folds; add leakage traps.

### A18 — vectorbt screening

**MISSING.** Source: §1, §3, §12 phase 5. Evidence: No vectorbt dependency or screening engine.

Implement cost-aware screening with versioned inputs; screening cannot authorize promotion alone.

### A19 — Event-driven backtest and executable signal parity

**PARTIALLY IMPLEMENTED.** Evidence: Deterministic execution events and pinned VALID Phase 2 bid/ask tick replay are native-tested.

Full strategy/backtest signal parity and independent research backtesting remain missing.

### A20 — Bid/ask, spread, fees, slippage, latency, partial/rejected fills

**PARTIALLY IMPLEMENTED.** Evidence: Explicit exact bid/ask, adverse slip/gaps, seeded latency, commission, optional continuous modeled funding and finite side-liquidity/partial/rejection cases pass.

These are documented synthetic assumptions; no measured real-world fill accuracy or verified broker rollover.

### A21 — Chronological OOS and untouched final holdout

**MISSING.** Source: §6. Evidence: docs/EXPERIMENT_PROTOCOL.md only.

Enforce separate discovery/calibration/validation/final evaluation with holdout-access audit.

### A22 — Walk-forward, purging/embargo and multiple-testing controls

**MISSING.** Source: §1, §6. Evidence: No statistical evaluation module.

Implement overlap-aware folds, trial registry and documented selection-bias controls.

### A23 — Bootstrap/Monte Carlo, regimes, metrics and confidence

**MISSING.** Source: §1, §6. Evidence: No metrics or backtest results.

Implement deterministic numerical tests, block resampling, sample-size limits and uncertainty reporting.

### A24 — Adaptive statistical/compliance gates for paper eligibility

**MISSING.** Source: §0 invariant 5, §6. Evidence: No StrategyGate.

Implement family/instrument thresholds outside candidate-agent authority with auditable decisions.

### A25 — Measured five-year coverage target and incomplete-data gates

**PARTIALLY IMPLEMENTED.** Source: §1, §5. Evidence: Per-dataset observed ranges/counts, explicit bar-grid coverage and unknown tick completeness are stored/displayed. Five actual ECB daily reference observations were measured.

Five-year/tick coverage remains unproven. Source entitlements and real history are required, not configured targets.

### A26 — MT5/broker and legitimate public/licensed historical ingestion

**PARTIALLY IMPLEMENTED.** Source: §2, §5. Evidence: Local CSV/Parquet and actual ECB reference downloads pass native service tests; read-only authorized-Windows MT5 export code is present.

MT5 terminal connectivity, premium feeds and external intraday/metals/index/crypto datasets are blocked or unimplemented, not certified.

### A27 — Immutable Parquet/raw/derived manifests and PostgreSQL metadata

**FULLY FUNCTIONAL.** Source: §3–5. Evidence: Within the local data boundary, immutable original/raw/normalized/derived Parquet, pinned MinIO versions/retention, SHA-256 manifests, PostgreSQL registry and atomic publication are implemented and native-tested.

Production archival/backup/restore, external anchors and storage/orphan capacity operations remain separate gates.

### A28 — Data QC: ordering, duplicates, collisions, gaps, prices and scaling

**PARTIALLY IMPLEMENTED.** Source: §5. Evidence: Structured quality detects schema/time/duplicates/order/crossed quotes/nonpositive prices/spread/increment/session/revision issues, reports gaps/spikes/distributions and blocks admission.

Validation uses declared calendars/specs; independent provider correctness and production-scale/hostile-parser QC are not certified.

### A29 — As-of cross-asset joins and realistic publication delays

**PARTIALLY IMPLEMENTED.** Source: §5–6. Evidence: Server-side historical samples and account-scoped as-of joins enforce event/publication/observation/availability plus optional source-sequence cutoffs; adversarial tests pass.

Upstream availability assertions still require trustworthy evidence. Future-calendar scheduling and full feature-engine/fold-local processing remain unimplemented.

### A30 — Paper trading and adaptive observation window

**MISSING.** Source: §1, §4, §6, §12 phase 8. Evidence: No paper engine or lifecycle persistence.

Implement paper fills, independent-trade counts, regime coverage, confidence and indefinitely pending eligibility.

### A31 — Degradation auto-pause and manual live reactivation

**MISSING.** Source: §1, §6, §14. Evidence: No strategy monitoring or state transitions.

Implement drift/cost/risk monitors and owner-only reactivation with audit.

### A32 — Account/strategy risk caps and conservative reference profile

**PARTIALLY IMPLEMENTED.** Evidence: Scoped versioned profiles and strictest account/strategy/instrument/asset/firm/program caps now enforce per-trade/day/total/aggregate/group/headroom/position limits in the simulated gateway.

External broker enforcement and complete browser acceptance remain unresolved.

### A33 — Decimal sizing, legal volume steps, FX conversion and margin

**PARTIALLY IMPLEMENTED.** Evidence: Exact Decimal linear-contract/tick sizing, conservative timestamped FX conversion, legal step/minimum volume, commissions/slippage/funding and explicit fixed margin are unit/property/native tested.

Inverse/unknown conventions fail closed; real broker payoff/margin/specification certification is unverified.

### A34 — Portfolio/correlation/concentration including pending exposure

**PARTIALLY IMPLEMENTED.** Evidence: Durable account ledger includes open/pending/UNKNOWN/group/strategy allocations and atomic reservations; actual multiprocess competition, partial release and process-kill rollback pass.

External portfolio-margin and broker-truth acceptance remain unimplemented.

### A35 — Prop headroom, loss basis, timezone resets and exposure reductions

**PARTIALLY IMPLEMENTED.** Evidence: Static/trailing balance/equity floors, floating treatment, explicit daily timezone/DST references, fees, headroom buffers and predetermined warning risk reduction are implemented and tested.

Exact real firm/program contractual facts require owner review; no official brand-wide numeric defaults are invented.

### A36 — Independent near-broker freshness/spread/calendar/margin checks

**PARTIALLY IMPLEMENTED.** Evidence: Mandatory deterministic journal gateway validates fresh quote/spec/session/calendar/FX, spread/slippage, stops, margin, exact policies and account scope, with fresh per-fill grants.

Shared trusted host/key is not an independently secured external broker-side executor; all external methods remain denied.

### A37 — GPU/cloud outage independence, broker truth and protective stops

**PARTIALLY IMPLEMENTED.** Evidence: Separate read-only bridge source, signed observation checks and synthetic UNKNOWN/reconciliation/outage recovery are implemented.

Actual broker protection, Windows deployment and control/GPU outage demo acceptance remain blocked.

### A38 — Authenticated stop-new-entries versus separate flatten operation

**PARTIALLY IMPLEMENTED.** Evidence: Owner/recent-MFA STOP persists across actual restart; separate idempotent simulated FLATTEN reports only verified synthetic closes and UNKNOWN/incomplete outcomes.

External flattening and rendered desktop/mobile acceptance remain unverified.

### A39 — Durable intent IDs, UNKNOWN state and retry idempotency

**PARTIALLY IMPLEMENTED.** Evidence: Atomic account-locked journal/grant/consumption/reservation/HMAC audit, unique idempotency receipts, UNKNOWN retention and actual crash/restart/concurrent process tests pass.

This proves local synthetic consistency, not exactly-once external broker delivery.

### A40 — MT5 Windows bridge and actual demo integration

**PARTIALLY IMPLEMENTED.** Evidence: Official SDK read-only MT5 adapter and independent mTLS Windows SCM source implement demo/investor/terminal/account/server checks; fake SDK contracts pass.

Actual authorized Windows terminal, SCM/ACL/Job, quotes and history connectivity remain BLOCKED/NOT RUN.

### A41 — cTrader OAuth, refresh, rates and actual demo integration

**PARTIALLY IMPLEMENTED.** Evidence: Official cTrader demo JSON transport, accounts OAuth/refresh/private vault, verified VIEW scope, heartbeat/rates/bounded reconnect and protocol fixtures pass.

OAuth HTTP tests are MOCKED; actual authorized application/account/demo connectivity remains BLOCKED.

### A42 — Broker capability matrix, safe OCO and reconnect reconciliation

**PARTIALLY IMPLEMENTED.** Evidence: Shared adapter contracts/capability registry and explicit synthetic OCO, signed snapshot sequence/diff checks and uncertainty incidents are implemented/tested.

No real venue capability certification, live reconciliation or automatic central polling is claimed.

### A43 — Broker secrets isolated from research/GPU/control plane

**PARTIALLY IMPLEMENTED.** Evidence: Primary images exclude bridge/MT5 SDK; no broker credentials/socket/admin identities reach API/worker. Separate private-file/vault/mTLS connector source and local transport checks pass.

Actual deployed executor identities/network/Windows credential isolation are unverified; no generated-code runner exists.

### A44 — Execution disabled across all shipped entry points

**FULLY FUNCTIONAL.** Evidence: Config, legacy and new API routes, shared adapter mutation methods and bridge transport allowlists deny every external order. SIMULATED/DEMO_READ_ONLY only; unit/native denial tests pass.

Verified for this release only. The simulated gateway grants no external authority; no signed live approval exists.

### A45 — Owner MFA, two acknowledgements, immutable signed scoped approvals

**PARTIALLY IMPLEMENTED.** Source: §0 invariants 1/5, §4, §10. Evidence: Owner MFA and metadata approval requests with PENDING/REVIEWED/REJECTED are implemented; live activation is still unconditionally 403.

No two-acknowledgement live flow, signed/expiring/revocable execution approval or independent executor capability exists.

### A46 — LLM output validation and no critical monetary/order authority

**MISSING.** Source: §0 invariants 2/9, §9. Evidence: No LLM gateway or agent runtime.

Implement typed proposal-only interfaces and capability tests. Frontend response validation is not an LLM security boundary.

### A47 — Hardened hostile-code sandbox with quotas and immutable inputs

**MISSING.** Source: §0 invariant 4, §3, §15. Evidence: workers/safety.py refuses execution; docs/THREAT_MODEL.md.

Implement VM/microVM isolation, denied egress/mounts/credentials and escape/exfiltration/quota tests before any generated code runs.

### A48 — Mandatory independent deterministic risk gateway, no bypass

**PARTIALLY IMPLEMENTED.** Evidence: Every durable simulated entry and actual fill passes the gateway; missing service identity, changed scope, signature tamper/replay and absent allocation refuse. Independent fixed-code monitoring runs separately.

A broker-capable independently secured executor, separate signing identities and external approval/capability checks are NOT IMPLEMENTED.

### A49 — Identity, RBAC, MFA, sessions, CSRF, rates and authenticated streams

**PARTIALLY IMPLEMENTED.** Source: §3–4, §10, §12 phase 1. Evidence: apps/api/identity implements owner bootstrap, Argon2id, TOTP/recovery/replay, sessions, RBAC, CSRF, rate limiting and revocation; real PostgreSQL security tests pass.

Browser acceptance remains blocked by Chromium OS permission denial. Authenticated streams are not introduced; public deployment security is not accepted.

### A50 — Append-only audit, ordered events and causal decision replay

**PARTIALLY IMPLEMENTED.** Source: §3–4, §10, §15. Evidence: Durable ordered audit uses runtime append-only permissions/triggers and HMAC chain/head verification with UTC/actor/correlation/before-after. Native tamper/rollback/concurrency/restart tests pass.

No external anchor, full causal decision replay, retention service or verified backup restore. Host/DB admins holding the key remain trusted.

### A51 — Typed modular monolith, OpenAPI, generated TS and full domain models

**PARTIALLY IMPLEMENTED.** Source: §3–4, §11, §15. Evidence: Typed Phase 1 identity and governance schemas, scoped repositories, PostgreSQL models/migration and generated OpenAPI/TypeScript are implemented.

Dataset, trading, order/fill/reconciliation, risk ledger and later domain models remain absent.

### A52 — PostgreSQL/Alembic, Redis, MinIO and runnable local containers

**FULLY FUNCTIONAL.** Source: §3, §12 phase 0. Evidence: Actual local PostgreSQL/Redis/MinIO/API/Web healthy; additive migration applied; runtime DB role separated. Native up/down/up, queue/object/database round trips and restart persistence pass with dynamic loopback binding/TCP checks and scoped cleanup.

This classification covers the runnable local stack. Fresh-machine rebuild, production identities, power-loss recovery and restore remain unverified.

### A53 — Durable jobs, retries, orchestration, quotas and crash recovery

**PARTIALLY IMPLEMENTED.** Source: §3, §9, §12. Evidence: Fixed ingestion jobs use PostgreSQL durable outbox, Redis hints, idempotency, bounded slots, progress/cancel/backoff and tested process-kill/lease recovery.

This is a data pipeline, not arbitrary research-job orchestration, GPU quotas or generated-code execution.

### A54 — Private Ollama gateway, exact model digests and provider portability

**MISSING.** Source: §2–3, §9, §13. Evidence: Planned Ollama status only.

Implement authenticated private gateway, pinned models/prompts/runtime and schema/tool behavior evals.

### A55 — GPU allocation, sequential model loading and enforceable cost budgets

**MISSING.** Source: §1, §9, §13. Evidence: No GPU host, scheduler or cost telemetry.

Measure VRAM/context limits and cost rates; enforce per-agent/monthly quotas before any paid continuous operation.

### A56 — Complete Romanian dashboard, labs, execution/replay/settings and mobile UX

**PARTIALLY IMPLEMENTED.** Evidence: Romanian real-API Risk Center now includes scoped profiles, exact policy verification, financial/calendar context, what-if, headrooms/decisions/reservations/incidents and STOP/CLEAR/FLATTEN; global emergency banner added.

Full 14-case desktop/mobile acceptance is BLOCKED at managed Chromium launch; other future labs remain absent.

### A57 — Telegram/email incidents and authenticated emergency commands

**PARTIALLY IMPLEMENTED.** Evidence: Authenticated owner-MFA idempotent emergency commands and durable risk incidents are implemented/native-tested.

Telegram/email delivery and notification credentials/receipt tests are NOT IMPLEMENTED; no messages sent.

### A58 — JSON logs, tracing, metrics, incidents and cost observability

**PARTIALLY IMPLEMENTED.** Source: §3, §9–10, §13. Evidence: Sanitized request logs/readiness, durable incident records and governance audit exist.

Data job progress and synthetic native ingestion/query benchmarks are measured. No tracing/metrics pipeline, cost service, notification delivery or operational incident automation.

### A59 — Cloud/local deployment, private channels, backups and restore

**MISSING.** Source: §9, §12 phase 10, §13. Evidence: Only deploy/minio exists; docs/RUNBOOKS.md describes future work.

Implement cloud/local/Windows runbooks and scripts, private TLS identities, encrypted off-host backups and measured restore/migration rehearsal.

### A60 — Release gates, property/fault/integration/E2E/security tests and documentation

**PARTIALLY IMPLEMENTED.** Evidence: Phase 4 quality/contracts and real-service property/adversarial/risk/execution regression tests pass; exact commands and failures remain in PHASE4_COMPLETION_REPORT.md and the execution ledger.

Current managed browser launch remains blocked; remote CI, container vulnerability/SBOM, production-load and full restore acceptance remain NOT RUN.
