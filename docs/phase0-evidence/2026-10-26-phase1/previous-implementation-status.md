# Implementation Status

Updated: 2026-10-26 after Phase 0 completion work · version 0.1.0 · mode SIMULATED · live execution DENY_ALL.

**The shipped product is a Phase 0 foundation with outstanding acceptance gates. Phases 1–10 are
not accepted. It is not ready for shared/public deployment, autonomous code execution, paper trading,
demo broker execution or live trading.** See [PHASE0_COMPLETION_REPORT.md](PHASE0_COMPLETION_REPORT.md) for current evidence and
[AUDIT_REPORT.md](AUDIT_REPORT.md) for the earlier audit.

## Specification traceability and scope

The supplied original and `docs/PRODUCT_SPEC.md` are byte-identical (SHA-256
`c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085`).
The document labels §1 “consolidated … Q1–Q60” but does not provide the original 60 individually
numbered questions. **A01–A60 below are 60 derived audit criteria covering the supplied consolidated
requirements and detailed sections; they are not a reconstruction of the original Q numbers.**
An exact original question-by-question crosswalk needs the original questionnaire; no missing
question wording or numbering has been invented.

For these 60 derived criteria: **2 fully functional within the shipped boundary, 6 partially
implemented, 3 mocked/reference-only, 49 missing.** Counts describe this decomposition, not percentage
of effort completed. In particular, safe refusal of all orders does not implement risk, paper or brokers.

## Current acceptance

- PASSED: 75 Python foundation tests, 13 frontend logic tests, lint/format/types and frontend build.
- PASSED: fresh contract comparison, repository exclusions and source secret scan. Dependency scans,
  Compose syntax and actionlint retain their 2026-10-25 evidence; disposable Compose also ran successfully today.
- PASSED: real local API liveness/overview/denial smoke and strict readiness, HTTP 200.
- PASSED: make integration, one application readiness test plus three actual disposable-service
  cases in each of the write and restart-verification stages. No integration tests were skipped.
- PASSED: Docker bindings and host TCP connectivity before/after restart; isolated cleanup verified.
- FIXED: internal-only test network returned invalid IP:0; a project-scoped bridge now publishes
  dynamic loopback ports. Port discovery refreshes after restart. Exact evidence is in
  [the integration repair ledger](docs/phase0-evidence/2026-10-26-integration/README.md).
- BLOCKED: initial staging/commit because .git is read-only. No remote creation/push authorized.
- PASSED: local Docker engine available and existing API/Web/PostgreSQL/Redis/MinIO healthy;
  development containers and volumes were preserved. Fresh-machine rebuild remains unverified.
- BLOCKED: six browser tests collected but not executed because browser access was denied by policy.
- NOT RUN: remote CI, container vulnerability scan, load/fault/domain tests, any external broker/model/feed.

## Module inventory

Classification applies to the stated module scope. “Fully functional” is supported by local code/tests,
not a certification of the entire product. “Partially implemented” includes code whose external runtime
has not been verified. “Mocked” means explicit static reference/demo presentation, not a silently faked
integration. Documentation and installed dependencies do not count as implemented business behavior.

### Shipped backend, contracts and persistence

- **Fully functional — safe configuration parsing:** `apps/api/config.py`. Simulation-only literals,
  false execution flags, secret-redacted DSNs and object-store URL validation; unit/property tests pass.
  Only development/test environments exist. This is not a production secret store.
- **Fully functional — local API liveness and safety reporting:** `apps/api/main.py`.
  Liveness and safety are real local HTTP endpoints. Host validation and response headers are tested.
  Overview includes actual dependency observations plus explicitly planned services.
- **Fully functional — unconditional execution refusal:** `packages/domain/safety.py`,
  `workers/safety.py`, API order/activation routes. Both POSTs return 403; worker gate always raises,
  even when Settings validation is bypassed. There is no independent executor process.
- **Partially implemented — dependency health:** `apps/api/health.py`.
  Real PostgreSQL schema-version, Redis PING and MinIO readiness probes exist, run concurrently with
  timeouts and sanitized errors. Missing/degraded behavior and actual service readiness pass.
  MinIO health is not authenticated bucket read/write verification; Redis PING is not queue durability.
- **Fully functional — bounded Phase 0 contracts:** `packages/domain/contracts.py`,
  `docs/openapi.json`, `apps/web/src/generated/api.ts`, `scripts/export_openapi.py`.
  Frozen/extra-forbidden backend schemas and generated frontend types; regeneration is byte-identical.
  These cover overview/status/reference data only, not the §4 trading domain.
- **Mocked — reference account/risk values:** `ReferenceProfile` and `scripts/seed_demo_data.py`.
  $25k and 0.25/1/3/1 percent examples are labeled, Decimal-backed, and explicitly unenforced.
  Fixture generation works; no account exists, no P&L is calculated.
- **Mocked — future integration and phase catalog:** `apps/api/catalog.py`.
  Static phase descriptions and planned broker/model status, not service integrations.
- **Partially implemented — relational persistence/migrations:** `migrations/env.py`,
  `migrations/versions/0001_foundation.py`, `migrations/script.py.mako`, `alembic.ini`.
  Only `platform_metadata` plus Alembic version metadata exists. SQLite up/down/up and simulation
  constraint tests pass; actual isolated PostgreSQL upgrade/downgrade/upgrade, transaction rollback,
  simulation constraint and graceful-restart persistence now pass.
- **Fully functional — bounded request logging:** `apps/api/main.py`.
  UTC/request ID/method/status/duration JSON, no raw URL/query/body/credential values in these logs.
  This is neither a durable audit trail nor proof all future server/error logs are secret-safe.
- **Missing — §4 business entities and repositories:** User/Role/MFAEnrollment, Approval/Challenge,
  Account/BrokerConnection/Venue/PropFirm/Program/PolicyPack/RiskProfile/SymbolSpec/Session/Event/
  CalendarStatus; all dataset, experiment, strategy, paper, trade, order, fill, position, reconciliation,
  risk snapshot, equity reference, incident, kill-switch and notification persistence.

### Shipped frontend

- **Partially implemented — application shell:** `apps/web/src/App.tsx`, `main.tsx`,
  `styles.css`, `locale.ts`, `index.html`, `public/favicon.svg`.
  Romanian overview, infrastructure search, governance explanation, roadmap, theme and mobile menu
  are implemented in source and build. No rendered-browser/accessibility acceptance was obtained.
  English i18n is not implemented beyond a locale file that can be extended.
- **Fully functional — API response shape/safety validation and stale-state helpers:**
  `apps/web/src/api.ts`, `schema.ts`. Strict runtime schema rejects unsafe flags, malformed JSON
  contracts and false provenance. Logic tests pass; full browser interaction remains unverified.
  This schema is not a broker or agent authorization boundary.
- **Mocked — dashboard reference/watchlist/research-plan presentation:** `App.tsx`.
  Reference amounts and planned instruments/research stages are explanatory/static. No live charts,
  quotes, balances, experiments, broker connectivity or performance are inferred from them.
- **Missing — functional financial/product screens:** account/policy CRUD, Strategy Lab, backtest
  submission/results, agent tasks/costs, Data Quality/News, execution journal, risk/kill/flatten,
  approvals, secure settings, audit replay and emergency mobile actions. Navigation for future work
  does not supply these workflows.
- **Partially implemented — frontend serving:** `vite.config.ts`, `nginx.conf`,
  `apps/web/Dockerfile`, `.dockerignore`. Build passes and the existing Web container is healthy;
  CSP behavior, container routing and browser interactions still require browser acceptance.

### Development, deployment and test modules

- **Partially implemented — local secret bootstrap:** `scripts/bootstrap.py`, `.env.example`.
  Random local secrets and exclusive 0600 creation tested; existing configuration is preserved.
  Existing insecure permissions, symlinks, nonregular/wrong-owner files are now rejected and tested.
  Actual local file is 0600. Production secret management remains unimplemented.
- **Fully functional — prerequisite doctor:** `scripts/doctor.py`. Reports available Docker and local
  prerequisites; make doctor now passes. It does not certify data licensing or deployment.
- **Fully functional — bounded local smoke:** `scripts/smoke_demo.py`. Loopback-only, validates
  app/safety contracts before denial probes; now rejects unexpected/inconsistent readiness. Actual
  local API smoke and strict readiness now pass with HTTP 200 and execution denial.
- **Partially implemented — dependency/bootstrap toolchain:** `scripts/setup.sh`, `Makefile`,
  `pyproject.toml`, `uv.lock`, `apps/web/package.json`, `package-lock.json`, runtime pins,
  `.npmrc`, `.gitignore`. Installed environment, lock-based checks/build and shell syntax work;
  fresh-machine reproducibility remains unverified; the disposable MinIO image build passed.
- **Partially implemented — service topology:** `compose.yaml`, root `Dockerfile`,
  root `.dockerignore`, `deploy/minio/Dockerfile`, `compose.test.yaml`. Loopback ports, scoped networks, volumes,
  digest-pinned images, checksum-pinned MinIO source, nonroot app/container settings. Compose syntax
  passes; the existing development stack is healthy and actual disposable integrations pass.
  Test services use a regular bridge for host port publishing; this is not an untrusted-code sandbox.
- **Fully functional — available foundation unit/property/migration tests:** `tests/conftest.py`,
  `test_safety.py`, `test_health.py`, `test_bootstrap.py`, `test_migrations.py`,
  `test_audit_regressions.py`, `test_integration_guards.py`. 75 selected tests pass; coverage is
  limited to the foundation. Six mocked command-lifecycle cases are not service acceptance.
- **Partially implemented — actual-service integration test:** `tests/test_infrastructure.py`.
  Read-only readiness checks pass against the running stack. `scripts/integration_services.py` and
  `tests/test_service_roundtrips.py` now provide isolated PostgreSQL migration/transaction, Redis
  Streams and authenticated object-storage tests across graceful restart. Both real-service stages
  pass; no production queue, broker job or power-loss recovery is implemented.
- **Fully functional — local repository/contract/secret checks:** `scripts/repository_check.py`,
  `scripts/check_contracts.py`, `scripts/scan_secrets.py`. Actual checks pass; Git writes and remote
  publication remain blocked/pending. See `docs/GITHUB_PREPARATION.md`.
- **Fully functional — frontend logic tests/tooling:** `src/api.test.ts`, `vitest.config.ts`,
  `eslint.config.js`, `tsconfig.json`, Prettier configuration. 13 tests and lint/types/build pass.
  There are no React component interaction tests outside the blocked Playwright suite.
- **Partially implemented — E2E suite:** `e2e/platform.spec.ts`, `playwright.config.ts`.
  Three scenarios × desktop/mobile = six collected cases; execution blocked. These cover only
  foundation browse/outage/denial paths, not the unimplemented trading workflows.
- **Partially implemented — CI and pre-commit:** `.github/workflows/ci.yml`,
  `.pre-commit-config.yaml`. Local constituent checks pass; remote CI has never run in this
  repository. Action revisions are pinned, credentials are not persisted, and actionlint passes.
  No configured container scan, complete fault/load suite or approved release pipeline.
- **Fully functional — documentation artifacts:** `docs/PRODUCT_SPEC.md`,
  `ARCHITECTURE.md`, `THREAT_MODEL.md`, `ROADMAP.md`, `RUNBOOKS.md`,
  `RISK_POLICY.md`, `DATA_PROVENANCE.md`, `EXPERIMENT_PROTOCOL.md`,
  `RULES_AND_LIMITATIONS.md`, `external-sources.md`, ADR, README and this audit set.
  They state design/limitations; they do not implement the systems described.
- **Structural only — package initializers:** `apps/__init__.py`, `apps/api/__init__.py`,
  `packages/__init__.py`, `packages/domain/__init__.py`, `workers/__init__.py`,
  `scripts/__init__.py` contain package markers/docstrings, no additional business capability.

### Entirely missing operational modules

- **Missing:** owner authentication, RBAC, MFA, sessions, CSRF/rate/stream authorization.
- **Missing:** account partitioning, program policy verification, instrument capability registry.
- **Missing:** data/calendar ingestion, Parquet manifests, QC, UTC/DST/as-of feature controls.
- **Missing:** strategy library, vectorbt screening, event replay, costs, metrics, statistical gates, ML.
- **Missing:** strategy lifecycle/registry, paper trading, degradation monitoring and signed approvals.
- **Missing:** deterministic risk sizing/reservations, independent gateway, kill/flatten and audit replay.
- **Missing:** broker contract/simulator, MT5 bridge, cTrader OAuth adapter, durable order/reconciliation manager.
- **Missing:** hardened sandbox, research tools/agents, persistent queue/orchestrator, private LLM gateway.
- **Missing:** GPU management, quotas, measured costs, cloud/local model migration.
- **Missing:** notification delivery, tracing/metrics/incident system, backup/restore and deployment identities.

The machine-readable source inventory and hashes are in the audit evidence directory. Namespace
markers are explicitly listed rather than counted as functional trading modules.

## All 60 derived audit criteria

Each entry gives the master-spec sections, implementation evidence and the next acceptance gate.
“Missing” means no operational implementation was found, even when a design document exists.

### A01 — Personal/prop accounts, $25k reference and multi-account partitions

**MOCKED.** Source: §1, §4. Evidence: packages/domain/contracts.py; migrations/versions/0001_foundation.py.

Only a labeled reference profile; implement account/broker/program entities and account-scoped authorization.

### A02 — Versioned exact firm/program/phase/platform policies

**MISSING.** Source: §1–2, §4, §7. Evidence: docs/RISK_POLICY.md; no policy engine.

Implement signed/versioned PolicyPacks with source, validity, human verification and unknown/expired deny tests.

### A03 — Honest simulation, source and performance labels

**FULLY FUNCTIONAL.** Source: §0 invariants 7/10, §15. Evidence: packages/domain/contracts.py; scripts/seed_demo_data.py; tests/test_bootstrap.py; tests/test_health.py.

Verified for shipped Phase 0 outputs only. Extend provenance enforcement when real datasets, fills and results exist.

### A04 — Forex/metals/indices/crypto and broker-specific tradability

**MOCKED.** Source: §1, §4, §14. Evidence: apps/web/src/App.tsx; apps/api/catalog.py.

Static planned instruments/status cards are not broker capabilities; query and validate per-account symbol mappings.

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

**PARTIALLY IMPLEMENTED.** Source: §3–5. Evidence: migrations/versions/0001_foundation.py; compose.yaml.

Only platform metadata migration and storage configuration; no dataset schema, Parquet, hashes or bucket operations.

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

**MOCKED.** Source: §1, §7. Evidence: ReferenceProfile.enforced=False; apps/web/src/App.tsx.

Displayed Decimal strings are examples only; implement configurable enforced profiles and strict firm headroom.

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

**MISSING.** Source: §0 invariants 1/5, §4, §10. Evidence: POST /api/v1/live/activate always returns 403.

Implement hash/account/broker/program/symbol/risk/expiry binding, revocation and tamper/replay tests; do not enable live.

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

**MISSING.** Source: §3–4, §10, §12 phase 1. Evidence: apps/api/main.py explicitly unauthenticated/read-only.

Implement owner identity and authorization before shared hosting; protect all future sensitive mutations and streams.

### A50 — Append-only audit, ordered events and causal decision replay

**MISSING.** Source: §3–4, §10, §15. Evidence: Request JSON logs only; one platform_metadata table.

Implement durable append-only events, source sequences, correlation/idempotency/version IDs and tamper-detection/restore tests.

### A51 — Typed modular monolith, OpenAPI, generated TS and full domain models

**PARTIALLY IMPLEMENTED.** Source: §3–4, §11, §15. Evidence: apps/api; packages/domain; docs/openapi.json; apps/web/src/generated/api.ts.

Foundation contracts/build work; almost all §4 business entities and transaction boundaries are absent.

### A52 — PostgreSQL/Alembic, Redis, MinIO and runnable local containers

**PARTIALLY IMPLEMENTED.** Source: §3, §12 phase 0. Evidence: compose.yaml; Dockerfiles; migrations; tests/test_infrastructure.py.

Development services are healthy. Actual disposable PostgreSQL migrations/transactions, Redis Streams and MinIO integrity pass across graceful restart, with verified dynamic loopback bindings and cleanup. Fresh-machine build and production domain persistence remain unverified/unimplemented.

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

**PARTIALLY IMPLEMENTED.** Source: §3, §10, §12 phase 9. Evidence: apps/web/src/App.tsx; locale.ts; styles.css; e2e/platform.spec.ts.

Four foundation views only; build/unit checks pass, six browser cases not executed, secure financial workflows and English UI absent.

### A57 — Telegram/email incidents and authenticated emergency commands

**MISSING.** Source: §1, §10, §12 phase 9. Evidence: No notifications module.

Implement owner-authorized delivery, redaction and actual-service receipt tests; commands require distinct signed/replay-protected authorization.

### A58 — JSON logs, tracing, metrics, incidents and cost observability

**PARTIALLY IMPLEMENTED.** Source: §3, §9–10, §13. Evidence: apps/api/main.py; apps/api/health.py.

Sanitized request logs and dependency checks exist; no OpenTelemetry, Prometheus, durable incidents, cost data or alert delivery.

### A59 — Cloud/local deployment, private channels, backups and restore

**MISSING.** Source: §9, §12 phase 10, §13. Evidence: Only deploy/minio exists; docs/RUNBOOKS.md describes future work.

Implement cloud/local/Windows runbooks and scripts, private TLS identities, encrypted off-host backups and measured restore/migration rehearsal.

### A60 — Release gates, property/fault/integration/E2E/security tests and documentation

**PARTIALLY IMPLEMENTED.** Source: §12 release gates, §15–16. Evidence: tests; apps/web/e2e; .github/workflows/ci.yml; audit documents.

Local quality, contracts and actual infrastructure/isolated-service integration pass. Browser runs remain blocked; remote CI/container scan/fault/load/real broker suites remain absent or unrun. Previous repository/actionlint/dependency scan evidence is retained with its original dates.

## Phase gates

- Phase 0: partially implemented; local quality and real service checks pass; browser/remote CI gates remain open.
- Phase 1: missing identity, roles, MFA, domain persistence and protected audit.
- Phase 2: missing ingestion, data quality and time correctness.
- Phase 3: missing broker contract, simulator and actual MT5/cTrader demo integrations.
- Phase 4: missing independent risk and firm policy engines.
- Phase 5: missing backtest/simulation/statistical evaluation.
- Phase 6: missing private AI gateway, agents and isolated execution.
- Phase 7: missing autonomous research/ML/evaluation governance.
- Phase 8: missing paper lifecycle and immutable approvals.
- Phase 9: missing full dashboard, secure operations, alerts and recovery.
- Phase 10: missing cloud/local deployment, migration and live-readiness review.

Execution-order changes must preserve the independent risk boundary: no order-capable demo executor
is enabled merely because its adapter compiles. The current audit did not authorize broker connections.

