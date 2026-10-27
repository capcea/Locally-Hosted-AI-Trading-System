# Implementation Status

Updated: 2026-10-26 · API version 0.1.0 · Phase 1 · SIMULATED · DENY_ALL.

**Phase 1 has working native identity/governance persistence and management UI source, but is not
accepted: actual browser workflows are BLOCKED by OS Chromium launch permissions.** No Phase 2
work, live trading, broker execution, generated-code execution or public deployment was started.
See [PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md) for exact evidence and limits.

## Specification traceability

The original master and docs/PRODUCT_SPEC.md have SHA-256
c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085.
A01–A60 below are derived audit criteria covering the consolidated specification, not invented
reconstructions of the unavailable original individually numbered questionnaire. Counts now are
3 fully functional, 12 partially implemented, 0 mocked-only and 45 missing. These are scope labels,
not percentages of effort. Individual demo/reference modules remain explicitly mocked below.
The prior inventory is preserved in the Phase 1 evidence directory.

## Current acceptance

- PASSED: 81 Python portable/unit tests and 16 frontend logic tests; lint/format/types/build.
- PASSED: full native integration: one application readiness case, then 20 disposable cases before
  and 20 after graceful restart (3 Phase 0 service cases plus 17 Phase 1 security/domain cases).
- PASSED: local Docker build/start, migration 0002, real readiness 200, order-denial smoke; database,
  Redis and MinIO container identity/start time/mounts preserved. Private pre-migration dump saved.
- PASSED: generated contract comparison, local actionlint/Compose syntax and dependency scans.
- FAILED / BLOCKED: browser command exits 2; desktop has three Chromium permission failures before
  page creation and one passing HTTP-only denial case. Mobile was not run after desktop failure.
  User authorized testing; OS bootstrap_check_in still returned Permission denied (1100).
- BLOCKED: initial commit (.git read-only); no remote repository/push authorized or attempted.
- NOT RUN: remote CI, container vulnerability scan, fresh-machine install, public deployment,
  load/fault/backup-restore acceptance, any broker/model/feed integration.

## Module inventory

### Functional within the tested local boundary

- Configuration/execution gates: apps/api/config.py, packages/domain/safety.py, workers/safety.py.
  SIMULATED and DENY_ALL are unconditional; no dynamic execution or order path exists.
- Health/status/contracts: apps/api/main.py, health.py, packages/domain/contracts.py, openapi.json,
  generated/api.ts. Dependency probes use actual services; legacy status routes remain public.
- Identity: apps/api/identity/{schemas,crypto,dependencies,routes}.py. One owner, mandatory MFA,
  private bootstrap, roles, secure password hashes, expiring/revocable sessions, CSRF, rate/replay
  controls and recovery are tested against actual PostgreSQL.
- Persistence/repositories: packages/persistence/{models,store}.py and apps/api/governance. All 13
  management record kinds have scoped create/list/get routes; mutable records support revisioned
  updates. Immutable versions/reviews use explicit operations. Native constraints/rollback tests pass.
- Audit: packages/persistence/audit.py plus migration triggers/runtime grants. Ordered transactional
  events, HMAC verification and application-role immutability pass native tamper/concurrency tests.
- Migrations/role setup: 0001_foundation and 0002_identity_governance; scripts/{identity_setup,
  migrate_runtime,provision_runtime}.py. Upgrade/downgrade/upgrade tested only on disposable resources;
  development upgrade additive, no persistent-volume deletion. API refuses privileged DB identities.
- Developer verification: doctor, smoke_demo, integration_services, repository_check, scan_secrets,
  check_contracts, locked toolchain and Make targets. Native tests use fresh unique service projects,
  temporary credentials, actual loopback bindings/TCP and scoped cleanup.

### Partially implemented / acceptance outstanding

- React management: Management.tsx, management-api.ts, management-locale.ts, styles.css and existing
  App/schema. Login/MFA/account/risk/policy/user/security/audit interfaces call real APIs. Unit/type/
  build checks pass; browser interactions/layout/accessibility remain unverified due launch denial.
- Policy: versioned provenance/scope/expiry/manual verification works; no current firm permissions,
  policy-language interpreter or independent trading enforcement. FTMO/FundedNext/The5ers are names.
- Risk: exact persistent percentages/configuration; no sizing, market validation or loss/exposure ledger.
- Broker/venue/instrument: metadata with scoped references; no credentials, broker calls or tradability.
- Strategy/version/experiment/approval: persistent metadata and immutable artifact digests; no
  strategy execution, experiment results, lifecycle engine, signed live approval or auto-promotion.
- Incidents: scoped persisted severity/status; no detection/notification/response automation.
- Local deployment: healthy Compose services and restricted API DB role; private .env still holds
  trusted host secrets. Redis/MinIO identity hardening, TLS, secrets manager, restore and production
  operational security remain outstanding.
- CI/E2E: Actions pinned and statically validated; eight Playwright cases and disposable browser
  harness prepared. Remote CI has not run; browser launch is blocked by managed macOS permissions.

### Mocked/reference presentation

The public $25k reference profile/percentages, watchlist and future-service catalog remain explicit
configuration examples/plans. They are separate from USER_ENTERED and SYNTHETIC_TEST_FIXTURE records.
No reference value is a balance, performance claim, broker capability or actual policy permission.

### Missing operational modules

Data/calendar ingestion, immutable dataset manifests/Parquet, temporal QC/as-of controls, backtesting,
fill/cost models, statistics/ML, independent risk and broker execution, order idempotency/reconciliation,
paper engine, autonomous agents/queues, hostile-code sandbox, model gateway/GPU quotas, signed live
promotion, kill/flatten, notifications, metrics/tracing, external audit anchors and verified off-host
backup/restore are NOT IMPLEMENTED. Package markers/design documents do not implement these modules.

## All 60 derived audit criteria

Each entry gives the master-spec sections, implementation evidence and the next acceptance gate.
“Missing” means no operational implementation was found, even when a design document exists.

### A01 — Personal/prop accounts, $25k reference and multi-account partitions

**PARTIALLY IMPLEMENTED.** Source: §1, §4. Evidence: Persistent SIMULATED account configuration, exact capital, revision checks and ownership partitions in packages/persistence/models.py and apps/api/governance; native PostgreSQL authorization/persistence tests pass.

Balances, personal/prop execution semantics and broker accounts remain unimplemented; browser acceptance is blocked.

### A02 — Versioned exact firm/program/phase/platform policies

**PARTIALLY IMPLEMENTED.** Source: §1–2, §4, §7. Evidence: Firm/program metadata and immutable policy content versions have source/digest/effective/expiry/scope, manual verification and revision binding; latest missing/unverified/expired/changed scope denies eligibility.

Actual firm rules are neither imported nor interpreted. No policy can authorize trading; independent enforcement remains future work.

### A03 — Honest simulation, source and performance labels

**FULLY FUNCTIONAL.** Source: §0 invariants 7/10, §15. Evidence: packages/domain/contracts.py; scripts/seed_demo_data.py; tests/test_bootstrap.py; tests/test_health.py.

Verified for shipped Phase 0 outputs only. Extend provenance enforcement when real datasets, fills and results exist.

### A04 — Forex/metals/indices/crypto and broker-specific tradability

**PARTIALLY IMPLEMENTED.** Source: §1, §4, §14. Evidence: Venue/instrument metadata and asset-class constraints persist with ownership checks; the public watchlist remains illustrative.

No live symbol specifications, tradability mapping or broker capability verification.

### A05 — Scalping/intraday profiles and prohibited-style filtering

**MISSING.** Source: §1, §6–8. Evidence: No strategy/execution profile module.

Implement deterministic timing profiles, duration constraints and policy exclusions; keep LLM inference off the order path.

### A06 — Ticks and M1/M5/M15/H1/H4, optional D1

**MISSING.** Source: §1, §5. Evidence: No ingestion/resampling module.

Implement timestamp-correct tick/bar ingestion and deterministic aggregation tests.

### A07 — UTC/DST, venue sessions, holidays, rollover/weekend handling

**MISSING.** Source: §1, §5, §7. Evidence: docs/DATA_PROVENANCE.md only.

Implement source zones, unambiguous conversion and venue calendars; test DST boundaries and closed sessions.

### A08 — Economic calendar freshness and event blackouts

**MISSING.** Source: §1, §5, §14. Evidence: No calendar provider or gate.

Integrate permitted calendar data, publication/ingestion timestamps and stale/missing calendar denial.

### A09 — Market orders with confirmed broker-side SL/TP

**MISSING.** Source: §1, §7–8. Evidence: All order submissions are denied.

Implement only in isolated demo executor after risk controls; test missing/rejected protection and partial fills.

### A10 — Pending/modify/cancel/trailing/break-even/partial close/OCO

**MISSING.** Source: §1, §7–8. Evidence: No BrokerAdapter or order state machine.

Capability-gate every operation, enforce monotonic risk and reject unsupported OCO/emulation.

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

**MISSING.** Source: §1, §6, §12 phase 5. Evidence: No event-driven simulation engine.

Implement ordered event replay and identical deterministic signal/risk contracts in backtest and paper.

### A20 — Bid/ask, spread, fees, slippage, latency, partial/rejected fills

**MISSING.** Source: §5–7. Evidence: No cost/fill model or trade data.

Define side-aware fills, adverse gaps, conservative ambiguous-bar rules and cost stress tests.

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

**MISSING.** Source: §1, §5. Evidence: docs/DATA_PROVENANCE.md says no dataset.

Implement per-source/symbol coverage reports and gap rejection; current zero coverage is honestly disclosed.

### A26 — MT5/broker and legitimate public/licensed historical ingestion

**MISSING.** Source: §2, §5. Evidence: No data connectors.

Implement entitlement/provenance checks, resumable ingestion and separate actual-service tests.

### A27 — Immutable Parquet/raw/derived manifests and PostgreSQL metadata

**PARTIALLY IMPLEMENTED.** Source: §3–5. Evidence: PostgreSQL governance metadata and native restart/migration tests work; MinIO object integrity is tested with explicit synthetic fixtures.

Raw/derived Parquet, real dataset manifests and time-availability semantics remain missing.

### A28 — Data QC: ordering, duplicates, collisions, gaps, prices and scaling

**MISSING.** Source: §5. Evidence: No data-QC implementation.

Build adversarial fixtures for crossed/negative quotes, same-ms sequences, spikes, units, sessions and suffix changes.

### A29 — As-of cross-asset joins and realistic publication delays

**MISSING.** Source: §5–6. Evidence: No feature/event timestamp enforcement.

Reject future information using decision/availability timestamps and explicit delayed-data tests.

### A30 — Paper trading and adaptive observation window

**MISSING.** Source: §1, §4, §6, §12 phase 8. Evidence: No paper engine or lifecycle persistence.

Implement paper fills, independent-trade counts, regime coverage, confidence and indefinitely pending eligibility.

### A31 — Degradation auto-pause and manual live reactivation

**MISSING.** Source: §1, §6, §14. Evidence: No strategy monitoring or state transitions.

Implement drift/cost/risk monitors and owner-only reactivation with audit.

### A32 — Account/strategy risk caps and conservative reference profile

**PARTIALLY IMPLEMENTED.** Source: §1, §7. Evidence: Exact account-scoped RiskProfile percentages persist with bounds/order constraints and transactional audit. The reference profile is still unenforced.

No sizing, account-loss ledger, exposure reservation or portfolio enforcement; configuration does not grant risk capacity.

### A33 — Decimal sizing, legal volume steps, FX conversion and margin

**MISSING.** Source: §0 invariant 9, §7. Evidence: No sizing or monetary execution logic.

Implement verified SymbolSpec and FX timestamps; property-test rounding down, minimum size, currency and stop distance.

### A34 — Portfolio/correlation/concentration including pending exposure

**MISSING.** Source: §1, §7. Evidence: No portfolio ledger or reservations.

Implement transactional risk reservations and concurrency tests across accounts/strategies/pending orders.

### A35 — Prop headroom, loss basis, timezone resets and exposure reductions

**MISSING.** Source: §1–2, §7. Evidence: No policy/risk ledger.

Implement exact account/program rules, floating P&L/balance/high-water bases and DST reset tests.

### A36 — Independent near-broker freshness/spread/calendar/margin checks

**MISSING.** Source: §0 invariants 3/6, §7. Evidence: packages/domain/safety.py only denies every order.

Implement a deterministic fail-closed gateway; generic refusal is not a risk evaluation.

### A37 — GPU/cloud outage independence, broker truth and protective stops

**MISSING.** Source: §1, §7, §14. Evidence: No independent broker executor or reconciliation.

Test demo protection and reconciliation through GPU/control-plane outages and rejected SL acknowledgements.

### A38 — Authenticated stop-new-entries versus separate flatten operation

**MISSING.** Source: §7, §10, §14. Evidence: No operational kill/flatten endpoints.

Implement durable kill state, distinct authorized flatten, replay defense and mid-flow interruption tests.

### A39 — Durable intent IDs, UNKNOWN state and retry idempotency

**MISSING.** Source: §7–8, §14. Evidence: No orders/journal/outbox tables.

Implement atomic intent/risk/audit state, uniqueness and reconciliation before retry; fault-test submit-before-ack crashes.

### A40 — MT5 Windows bridge and actual demo integration

**MISSING.** Source: §2, §8, §12 phase 3. Evidence: apps/api/catalog.py explicitly pending.

Implement authenticated Windows service, terminal capability checks, symbol metadata and recorded demo integration evidence.

### A41 — cTrader OAuth, refresh, rates and actual demo integration

**MISSING.** Source: §2, §8, §12 phase 3. Evidence: apps/api/catalog.py explicitly pending.

Implement Linux adapter with scoped OAuth, environment separation, rate limits and real demo tests after authorization.

### A42 — Broker capability matrix, safe OCO and reconnect reconciliation

**MISSING.** Source: §8, §14. Evidence: No shared broker contract or simulator.

Implement deterministic fault-injectable simulator and adapter contract suite; do not certify capabilities from mocks.

### A43 — Broker secrets isolated from research/GPU/control plane

**MISSING.** Source: §0 invariants 2/4, §3, §15. Evidence: compose.yaml has no broker or research service; no known broker keys in local .env.

Provision executor-only secret identities and network boundaries before adding credentials; absence of credentials is not an isolation test.

### A44 — Execution disabled across all shipped entry points

**FULLY FUNCTIONAL.** Source: §0 invariant 1, §16. Evidence: apps/api/config.py; apps/api/main.py; packages/domain/safety.py; workers/safety.py; tests/test_safety.py.

Verified only for the current incapable Phase 0 application. No separate broker executor exists; preserve denial while implementing later capabilities.

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

**MISSING.** Source: §0 invariants 2/3/6, §7. Evidence: No signed trade-intent channel or executor.

Make broker network/credentials reachable only by independently validating executor; adversarially test all entry paths.

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

**MISSING.** Source: §3, §9, §12. Evidence: arq pinned in pyproject.toml; no queue implementation.

Implement persisted jobs, idempotent handlers, priorities, resource quotas and forced-crash recovery tests.

### A54 — Private Ollama gateway, exact model digests and provider portability

**MISSING.** Source: §2–3, §9, §13. Evidence: Planned Ollama status only.

Implement authenticated private gateway, pinned models/prompts/runtime and schema/tool behavior evals.

### A55 — GPU allocation, sequential model loading and enforceable cost budgets

**MISSING.** Source: §1, §9, §13. Evidence: No GPU host, scheduler or cost telemetry.

Measure VRAM/context limits and cost rates; enforce per-agent/monthly quotas before any paid continuous operation.

### A56 — Complete Romanian dashboard, labs, execution/replay/settings and mobile UX

**PARTIALLY IMPLEMENTED.** Source: §3, §10, §12 phase 9. Evidence: Existing Romanian health/safety shell plus real-API login/MFA, accounts/risk/policies/security/audit screens in Management.tsx; build/types/unit checks pass.

Eight desktop/mobile browser cases collected. Three desktop page launches failed due OS permissions; one HTTP-only case passed; mobile was not run. No rendered workflow acceptance or later trading/lab/English UI is claimed.

### A57 — Telegram/email incidents and authenticated emergency commands

**MISSING.** Source: §1, §10, §12 phase 9. Evidence: No notifications module.

Implement owner-authorized delivery, redaction and actual-service receipt tests; commands require distinct signed/replay-protected authorization.

### A58 — JSON logs, tracing, metrics, incidents and cost observability

**PARTIALLY IMPLEMENTED.** Source: §3, §9–10, §13. Evidence: Sanitized request logs/readiness, durable incident records and governance audit exist.

No tracing/metrics pipeline, incident notification delivery, measured costs or operational incident automation.

### A59 — Cloud/local deployment, private channels, backups and restore

**MISSING.** Source: §9, §12 phase 10, §13. Evidence: Only deploy/minio exists; docs/RUNBOOKS.md describes future work.

Implement cloud/local/Windows runbooks and scripts, private TLS identities, encrypted off-host backups and measured restore/migration rehearsal.

### A60 — Release gates, property/fault/integration/E2E/security tests and documentation

**PARTIALLY IMPLEMENTED.** Source: §12 release gates, §15–16. Evidence: Phase 1 quality, contracts and native service/security tests pass; browser execution attempted honestly and failed at OS permission boundary. Exact commands/results are in PHASE1_COMPLETION_REPORT.md.

Remote CI, container scan, browser acceptance, sustained load/fault/restore and actual broker suites remain unrun or blocked.

## Phase gates

- Phase 0: native foundation, quality and services pass locally; owner reported earlier browser success.
  This run cannot independently close browser/remote CI/fresh-machine gates.
- Phase 1: implemented and native-tested; acceptance BLOCKED on browser workflows.
- Phase 2: not started; recommended next module after Phase 1 acceptance and owner scope.
- Phases 3–10: broker/risk/backtest/AI/paper/operations remain unimplemented beyond metadata.

No external broker/model/feed integration, live authorization or experimental runner is claimed.
