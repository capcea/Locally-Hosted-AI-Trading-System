# Post-Implementation Audit Report

Date: 2026-10-25 · project version: 0.1.0 · audited local working tree, not a deployed release.

**Verdict: a working, simulation-only Phase 0 foundation exists; the requested end-to-end trading
research platform does not. Phase 0 itself has outstanding Docker, browser and remote-CI gates.
No live trading, real broker order or automated live promotion was enabled or performed.**

The current application refuses all orders. That protects the current incapable application; it does
not constitute an implemented risk engine, hostile-code sandbox, approval service or broker executor.

## Scope and evidence

Reviewed the supplied original master document, all shipped source/configuration/test modules and
architecture/runbooks; exercised available local tests, actual local API behavior and negative
infrastructure checks. The original and repository specification hashes match:
`c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085`.

[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) inventories modules and maps **60 derived audit
criteria** to specification sections: 2 fully functional within the current boundary, 6 partial,
3 explicitly mocked/reference-only and 49 missing. The source specification says Q1–Q60 were
consolidated but omits the individual questions. A01–A60 are audit identifiers, not invented original
question IDs. Exact original-Q traceability remains unavailable without the original questionnaire.

Evidence is under [docs/audit-evidence/2026-10-25](docs/audit-evidence/2026-10-25/README.md).
Each command record includes argv, UTC start, elapsed seconds, actual nested command exit code,
sanitized stdout/stderr log and SHA-256. The capture wrapper returns normally even for failing child
commands; this report uses the recorded child exit code. Earlier failures were preserved.
`source-review.json` is explicitly a mid-audit snapshot after initial edits; it is not a pristine
pre-change snapshot. The final source manifest identifies the delivered files. Git has no committed
baseline or configured remote; source was already untracked and no commit/PR/remote CI is claimed.

This is a source/test audit, not an external penetration test, financial performance validation,
broker certification or current prop-firm-rule review. No actual MT5, cTrader, Ollama, market-data,
calendar, email or Telegram service was tested successfully. No profitability assertion is made.

## Commands and exact results

All commands ran from the repository root unless the command includes an explicit prefix. The
quality command is a local aggregate; it intentionally excludes the infrastructure marker.

### Final local quality checks — PASS

`make check` — exit **0** ([final-check.txt](docs/audit-evidence/2026-10-25/final-check.txt)).
Its actual commands and results:

- `.venv/bin/python -m ruff check .` — all checks passed, including configured Ruff security rules.
- `.venv/bin/python -m ruff format --check .` — 41 files already formatted.
- `npm --prefix apps/web run lint` — ESLint with zero warnings and Prettier passed.
- `.venv/bin/python -m mypy` — no issues in 24 source files.
- `npm --prefix apps/web run typecheck` — TypeScript passed.
- `.venv/bin/python -m pytest -m 'not infrastructure'` — **45 passed, 1 deselected**.
  Breakdown: safety 27, health 7, bootstrap/fixture 2, SQLite migrations 2, audit regressions 7.
- `npm --prefix apps/web test` — **13 passed**, one Vitest file.
- `npm --prefix apps/web run build` — TypeScript/Vite production build passed; 2,031 modules
  transformed, output JS 336.50 kB (103.23 kB gzip), CSS 28.81 kB (6.74 kB gzip).

The Python run emits one upstream Starlette warning: the httpx TestClient transport is deprecated
in favor of httpx2. This is not a failed test. There is no measured code-coverage percentage and no
claim of coverage for absent trading modules.

### Full backend and actual infrastructure — FAIL / unavailable

- `.venv/bin/python -m pytest` — exit **1**, **45 passed, 1 failed**. The sole failure is
  `test_compose_dependencies_and_schema_readiness`; PostgreSQL, Redis and storage all report
  UNAVAILABLE. [Full output](docs/audit-evidence/2026-10-25/final-python-all.txt).
- `make integration` — exit **2**, **1 failed, 45 deselected** after the audit changes.
  The first pytest command failed; Make therefore did not execute its subsequent strict smoke.
  [Integration output](docs/audit-evidence/2026-10-25/fixed-integration.txt).
- `make dev` — exit **2**. The command
  `docker compose up --build -d --wait --wait-timeout 180` could not connect to
  `/Users/andy/.docker/run/docker.sock` (no such file). No image build/start succeeded.
  [Docker output](docs/audit-evidence/2026-10-25/docker-start.txt).
- `make doctor` — exit **2** (inner doctor exits 1), installed prerequisites/config found,
  Docker engine UNAVAILABLE. [Doctor output](docs/audit-evidence/2026-10-25/baseline-doctor.txt).
- `docker compose config --quiet` — exit **0**, configuration syntax only.
- `bash -n scripts/setup.sh` — exit **0**, shell syntax only.

SQLite migration tests are actual temporary-file migrations, including up/down/up and rejection
of LIVE metadata. They are not PostgreSQL integration. The actual-service test now performs read-only
probes; it does not validate authenticated object PUT/GET, persistent queue recovery, PostgreSQL
business transactions, schema privilege separation or backup/restore.

### Actual local API smoke — bounded PASS, strict readiness FAIL

Started the supplied API using `make local-api` on loopback and restarted it after source changes.

- `make smoke-demo` — exit **0**: liveness/overview/safety valid; order and activation probes
  return 403; readiness explicitly **503**.
  [Smoke output](docs/audit-evidence/2026-10-25/final-smoke.txt).
- `.venv/bin/python -m scripts.smoke_demo --require-ready` — exit **1**,
  `Infrastructure readiness failed (HTTP 503)`.
  [Strict output](docs/audit-evidence/2026-10-25/final-smoke-ready.txt).

These were local denial probes against the verified simulation-only application, not broker order
submissions. Passing non-strict smoke means the API is alive and refuses execution; it does not mean
the stack is ready. Audit-owned preview/API processes are stopped at handoff.

### Frontend end-to-end — BLOCKED, not passed

`npm --prefix apps/web run test:e2e -- --list` — exit **0**, **six cases collected**:
browse/filter/governance/roadmap, outage labeling, order/activation refusal, each on desktop/mobile.

The actual command `npm --prefix apps/web run test:e2e` **was not executed**. The browser tool denied
access to `http://127.0.0.1:5173/` under a saved permission or managed policy. No alternate browser
or Playwright route was used to circumvent that denial. There are no browser screenshots, visual
acceptance, mobile/accessibility results or passing E2E counts.
[Block record](docs/audit-evidence/2026-10-25/browser-execution.json).

The test source is typechecked and now verifies the application contract before its denial probes.
It requires explicit `E2E_EXTERNAL_SERVERS=1` to use a separately started stack; otherwise it starts
its own servers and refuses to reuse an arbitrary listener.

### Dependency, source and contract checks

- `npm --prefix apps/web audit --audit-level=high` — exit **0**, **0 reported vulnerabilities**
  after adding pinned Zod 4.6.7. [Output](docs/audit-evidence/2026-10-25/final-npm-audit.txt).
- `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --progress-spinner off --cache-dir .cache/pip-audit`
  — exit **0**, no known vulnerabilities reported. Python dependency lock did not change during fixes.
  [Output](docs/audit-evidence/2026-10-25/baseline-pip-audit.txt).
- Gitleaks source scan: initial exit **1**, 11 candidates, all independently verified as source-file
  SHA-256 checksums beside API-related JSON keys, not credentials. Changed the metadata representation
  to separate path/sha256 fields; no rule/path allowlist was added. The raw failed scan and per-finding
  triage are retained. Rerun command/result: `final-secret-scan-clean.json` in the evidence index.
  Scope is Git-selected source files including untracked deliverables, excluding ignored runtime state;
  it is not a scan of external systems, arbitrary host secrets or nonexistent commit history.
- `make contracts` — exit **0**; OpenAPI and generated TypeScript SHA-256 values unchanged after
  regeneration. [Comparison](docs/audit-evidence/2026-10-25/contract-comparison.json).
- `make seed-demo` — exit **0**; only a labeled SYNTHETIC_TEST_FIXTURE reference configuration
  under ignored data/fixtures, with market_data=false and performance_data=false.
- No container vulnerability scan, remote CI run, standalone penetration test, live broker/demo
  integration, LLM eval, load benchmark or domain fault-injection test was performed. Those suites/
  integrations are missing or blocked, not skipped successes.

### Baseline and intermediate failures retained

Before fixes, `make check` passed 38 Python and 2 frontend tests. Baseline integration failed on a
refused PostgreSQL connection. Three added reproductions then failed as expected: an untrusted
Host was accepted, the smoke checker attempted an external URL, and readiness HTTP 500 printed PASS.
See `defect-reproductions.txt` (exit 1, three failures).

An intermediate `make check` failed two regressions because strict Python-object validation rejected
the tuple-backed safety reason list decoded from JSON. The implementation was corrected to strict
JSON validation; the final 45-test run passes. `fixed-check.txt` preserves that failure rather than
presenting only a green history. Initial/final npm audit and test-list commands are also retained.

## Defects fixed during this audit

### B01 — P1: smoke test could report success on readiness HTTP 500

The old check accepted any non-200 readiness in its optional-infrastructure path. A mocked HTTP 500
reproduction printed PASS. Fixed in `scripts/smoke_demo.py`: accept only 200/503, parse the service
contract, require the expected three identities, match aggregate health to status, and fail strict
mode on 503. Regression and actual local degraded/strict smoke results confirm the intended behavior.

### B02 — P1: smoke probes could target an arbitrary service

The old --base-url accepted arbitrary URLs and sent denial POSTs without establishing the target's
complete safe contract. Restricted to literal HTTP loopback addresses, no credentials/path/query,
no environment proxy or redirects, and verify liveness, complete safety and Phase 0 identity before
POST. Requests contain only SIMULATED audit probes. Tests prove rejected external/incomplete targets
receive no mutation probe. This is a local testing guard, not cryptographic server authentication.

### B03 — P1: frontend trusted unchecked JSON and could assert an unverified safety state

A TypeScript cast did not validate runtime responses. Added pinned Zod schemas in
`apps/web/src/schema.ts`; unsafe booleans/modes, incomplete payloads, malformed amounts and false
performance provenance are rejected by `getOverview`. The safety notice appears only with a
validated, non-stale snapshot. Thirteen logic tests pass; rendered behavior is still unverified.
The schema validates shape/literals, not signed provenance or semantic completeness of every future
service inventory; extend it together with future backend contracts.

### B04 — P1: local API accepted arbitrary Host headers

Added `TrustedHostMiddleware` allowing loopback/local Compose names and testserver only in test
configuration. A pre-fix request with Host attacker.invalid returned 200; now it returns 400 and
the regression passes. This limits one browser/local-server exposure path; it does not add owner
authentication, authorization or network isolation.

### B05 — P1: infrastructure test migrated the ambient configured database

The former integration test invoked Alembic upgrade on the database selected by Settings. This made
a nominal test capable of changing an operator's configured schema. Removed migration side effects;
the test now requires PostgreSQL configuration and checks readiness only. Compose's dedicated
migration service still applies deliberate local migrations. The repaired integration test fails
honestly on unavailable services. Actual PostgreSQL migration/round-trip validation remains open.

### B06 — P2: routine proxy access logs could include query secrets

Disabled Nginx access logging of full request URIs. API structured logs already omit paths, query
strings, bodies and headers, with a passing redaction test. Nginx has not run in this environment;
this is a configuration change validated by inspection, not a container log test. Future error-log,
proxy/auth telemetry and secret-redaction policies still need end-to-end validation.

### B07 — P2: E2E could reuse an unrelated existing server

Disabled implicit reuse; external-server use is explicit, and beforeEach verifies the application's
runtime contract. Browser tests are collected/typechecked only. No execution proof is inferred.

### B08 — P2: sample host ports did not match the Compose stack

Corrected `.env.example` from default service ports to host ports 15432/16379/19000, matching
bootstrap and Compose. Container-to-container ports remain 5432/6379/9000. Inspected configuration
and Compose syntax pass; actual connectivity remains blocked by Docker.

### B09 — P2: security checks were placed after the infrastructure startup gate

Moved existing dependency/secret checks before Docker startup in CI so a startup failure will not
hide those checks. Excluded .env patterns from the frontend image context and audit evidence from
the root context. Remote CI, image context contents and container scans still require actual execution.

## Security boundary assessment

### Actual application paths

The API exposes GET liveness, readiness, safety and overview, plus FastAPI's docs/OpenAPI routes.
Its only two product POST routes deny unconditionally. No mutable credential/settings/promotion
endpoint exists. Unit tests also check unsupported methods and missing sensitive routes.

The code contains no strategy upload, dynamic import of strategy artifacts, eval/exec runner,
research job consumer, broker SDK import or broker network client. The only reviewed Python
subprocess call in shipped tooling is the prerequisite doctor's fixed Docker-info command.
The declared Arq dependency is unused. The worker safety function is a denial stub, not a worker.

Therefore **no experimental generated code can reach a broker through any implemented application
entry point today**. However, **the required hostile-code isolation guarantee is NOT verified or
implemented**. A program manually run as the same host user could read that user's development
files or change source; AGENTS.md is guidance, not an OS security boundary. No sandbox was launched
and no credential-exfiltration/escape/host-mount/network-isolation test exists. No independent risk
gateway exists to prove non-bypass. Introducing a runner or broker client before those boundaries
would invalidate the current safety argument.

### Credentials and infrastructure identities

The existing ignored .env is mode 0600. A scoped check found no known MT5/cTrader/broker-secret
variable names in that file; no credential values are included in evidence. This is not a scan of
the user's entire machine or proof that all possible naming conventions are absent.

Bootstrap uses random local development secrets and exclusive creation; Pydantic SecretStr reduces
accidental DSN exposure, and health exceptions are sanitized. Actual API responses do not return
DSNs. These controls do not isolate secrets from code running with the same user/service identity.

Compose gives API and migrator the same database identity created by POSTGRES_USER, which is
privileged in this development setup. Redis has no auth and is bound on loopback plus the internal
network. MinIO uses root credentials in container environment. Docker users and trusted local
processes are inside this development boundary. Production needs separate least-privilege runtime/
migration/bucket identities, authenticated encrypted channels, executor-only broker secret storage,
rotation, revocation and restrictive network policies.

No Docker socket is mounted and no broker/research/GPU container is defined. App containers have
nonroot users, read-only filesystems, capability drops and no-new-privileges in configuration.
Those settings are not a hostile-code sandbox and have not been runtime-tested here.

### Approvals, risk, order safety and kill switch

- LIVE configuration is rejected, the API refuses activation, and no capable executor exists.
- No owner identity/MFA/two-step challenge, signed approval, immutable strategy hash binding, expiry,
  revocation store or replay protection exists. No activation can currently succeed.
- No authoritative Decimal sizing, SymbolSpec, FX conversion, margin check, risk reservation,
  portfolio cap, firm limit/reset semantics, calendar freshness or final broker-side risk check exists.
  Decimal-formatted reference values must never be called enforced risk.
- No order intent/journal/idempotency key/UNKNOWN state, outbox, partial-fill handling, broker truth
  reconciliation or retry recovery exists. Repeat 403 responses do not test order idempotency.
- No broker-native SL/TP confirmation, OCO, emergency stop-new-entries or distinct authorized flatten
  flow exists. There are no real positions to protect and no outage-survival evidence.
- API request UUIDs are log correlation IDs, not durable trade event sequences or idempotency keys.
- Auth, RBAC, MFA, CSRF-sensitive session design, rate limits and authenticated WS/SSE are missing.
  There is no owner account; do not expose the development app on a shared/public network.

### Supply chain and operational limits

Python/npm vulnerability scans pass against the advisory data retrieved in this audit. They do not
establish container/OS security or absence of unknown vulnerabilities. Image digests and MinIO source
checksum are pinned, but the custom image build and container scan remain untested. CI Actions use
version tags rather than immutable commit SHAs. There is no SBOM/attestation, protected release
pipeline, full threat-driven SAST review, durable audit sink or tested restore procedure.

## Data integrity, quant validity and promotion

There are **no imported market datasets, backtests, strategy signals, paper fills or performance
series** to validate. Coverage is zero. Seed data is a test/reference configuration, not market data.
Thus no backtest assumption, profitability statistic, cost model or promotion result can be
certified. Absence of a backtester is not evidence of absence of look-ahead bias.

Required acceptance work remains:

- Data: licensed source/entitlement, raw immutable Parquet, checksums, schema/version manifests,
  symbol/account mapping, original timezone and timestamps, observed/published/ingested/available
  times, same-ms sequences, gaps/duplicates/crossed prices/unit/spike/session checks and measured coverage.
- Information timing: decision-time cutoffs, backward/as-of joins, realistic publication delays,
  fold-local scaling/feature fitting, corporate/symbol changes and survivorship where relevant.
  Add adversarial future-bar, same-timestamp and cross-asset-delay fixtures.
- Simulation: executable signal/event parity, bid versus ask, actual/estimated historical spread,
  commissions/fees/swaps, rollover, latency, gaps, rejected and partial fills, stop distance and
  volume steps. Define conservative intrabar SL/TP ordering when tick evidence is unavailable.
  Block HFT/scalping claims from unsuitable coarse or spread-free data.
- Statistics: locked chronological OOS/final holdout, walk-forward purging/embargo, trial registry
  and multiple-testing adjustment, independent sample counts/regimes, block bootstrap/Monte Carlo,
  uncertainty and costs stress, documented drawdown/underwater/PF/expectancy/Sharpe/Sortino conventions.
- Governance: immutable strategy/data/model/config hashes, reproducible seeds and experiment records,
  thresholds controlled outside the proposing agent, controlled paper eligibility, adaptive observation,
  automatic degradation pause, manual reactivation and owner-only signed/expiring live approvals.
  A config/strategy/risk/account/program/symbol change must invalidate prior approval.
- Lifecycle and failure scenarios in master §§4–9/14 remain untested as operational systems;
  no auto-promotion path was added during this audit.

The design documents describe many of these controls. None supplies execution evidence. Current
firm permissions and broker symbol availability must be reverified against official sources for the
exact account/program at implementation time; this audit did not confirm the dated policy examples.

## Prioritized open findings

Priorities refer to enabling the intended product, not to an active live compromise.

- **P0 release gate G01 — generated-code and broker trust boundaries missing.**
  Keep runners and order-capable executors absent/disabled. Build isolated research execution and
  executor-only credentials/network capability, independent risk validation and durable order ledger.
  Require sandbox escape/exfiltration, duplicate-submit, submit-before-ack crash and bypass tests.
- **P0 release gate G02 — live authorization missing.**
  Preserve unconditional refusal. Add owner identity/MFA, immutable scope-bound signatures, expiry/
  revocation and two acknowledgements before any later readiness review. No audit item authorizes live.
- **P1 G03 — Phase 0 infrastructure/browser acceptance unresolved.**
  Start a permitted local Docker engine, build images, exercise PostgreSQL/Redis/MinIO and strict API
  readiness; obtain browser access and run all six cases. Add actual storage/queue/DB round-trips.
- **P1 G04 — identity, durable audit and least-privilege storage missing.**
  Implement Phase 1 before shared hosting. Separate migration/API identities and validate unauthorized
  access, MFA/session/CSRF/replay behavior and audit integrity.
- **P1 G05 — deterministic risk, policy, broker contract and order lifecycle missing.**
  Implement property/fault tests before any order-capable demo deployment. Actual MT5/cTrader demo
  connectivity will need isolated infrastructure and separately authorized demo access.
- **P1 G06 — real data, time semantics, backtests and promotion governance missing.**
  Implement the quant acceptance work above; retain zero-coverage/no-results labels until measured.
- **P1 G07 — research/ML/LLM/scheduler/paper systems missing.**
  Implement only after data/risk contracts and sandbox boundary; controlled paper promotion cannot
  grant live authority.
- **P2 G08 — CI/operations validation incomplete.**
  Run remote CI, pin Action SHAs, add container scan/SBOM, fault/load tests, metrics, alerts and tested
  encrypted off-host backups. The MinIO source image is an unverified build dependency.
- **P2 G09 — bootstrap existing-file permissions and local-user trust.**
  Bootstrap preserves existing files without rejecting insecure modes/symlinks. Current .env is 0600;
  before shared operation validate ownership/type/mode and use managed secrets. Do not infer privacy
  merely from a successful bootstrap rerun.
- **P2 G10 — UI/runtime contract acceptance incomplete.**
  Run browser/accessibility/outage tests, validate semantic service completeness and clock-freshness
  behavior, then implement the missing functional screens and localization.
- **P3 G11 — TestClient transport deprecation.**
  Evaluate the supported replacement with the pinned FastAPI/Starlette versions and rerun API tests.
- **Traceability dependency G12 — original Q1–Q60 not supplied individually.**
  Attach the original questions later for an exact ID crosswalk; the supplied consolidated document
  has been audited without inventing its missing numbering.

[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) contains gates and credentials by environment.
[NEXT_STEPS.md](NEXT_STEPS.md) supplies ordered, testable work packages. Completing this audit does
not complete the implementation or close any blocked acceptance gate.

