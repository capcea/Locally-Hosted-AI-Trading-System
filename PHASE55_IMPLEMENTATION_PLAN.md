# Phase 5.5A — implementation roadmap

> Phase 5.5B implementation update (2026-10-27): this approved design is now the migration basis.
> See [implementation/acceptance report](PHASE55B_COMPLETION_REPORT.md) and
> [S01–S42 / U01–U24 traceability](docs/ux-migration-coverage.md). Source/native implementation is
> present; browser, visual-baseline and manual accessibility acceptance remain BLOCKED.
> Descriptions below remain the approved design targets; they are not evidence of rendered acceptance.

Date: 2026-10-27. **DESIGN PROPOSAL ONLY. No steps below were implemented by this audit.**
Implementation requires a separate owner instruction. This is a UX migration of the existing
SIMULATED/DENY_ALL product, not Phase 6 or permission to add AI, live execution, broker credentials,
generated-code execution, automatic strategy promotion or new infrastructure.

Inputs: [audit and issue priorities](PHASE55_UX_AUDIT.md),
[feature/route coverage](PHASE55_INFORMATION_ARCHITECTURE.md),
[desktop/mobile screens](PHASE55_UX_BLUEPRINT.md), [design system](PHASE55_DESIGN_SYSTEM.md),
[Romanian copy](PHASE55_UX_COPY.md). S01–S42 identify existing audit units; B01–B10 identify designs.
S/M/L are relative implementation effort, not elapsed-time commitments or evidence of completion.

## Delivery rules and dependency order

Sequence: freeze evidence → primitives/copy → shell/auth/routes → independent safety → useful Home →
guided data setup → guided research/progress → results/comparison → complete account tools →
settings/security/audit → integrated acceptance. Accessibility and responsive checks accompany every
step, not only the final review. The ordering moves high-consequence ambiguity before visual polish.

Keep a feature coverage checklist for every S01–S42 action. A screen may move or split, but its
authorized operations, data, failure states and advanced controls must remain reachable. Temporary
legacy panels may remain behind an explicit advanced link until their replacements pass acceptance;
do not expose duplicate independent editors for the same mutable configuration.

Reuse installed React/TypeScript/Vite and generated contracts. No package upgrade or new routing,
charting, state or design-system dependency is assumed. Select a dependency only if a specific
requirement cannot be met responsibly with the existing stack; review its size, license and keyboard
behavior first. Do not pay for services or copy a reference product's visual identity.

### Step 0 — lock the migration baseline (S; prerequisite for implementation)

- Existing files to review, not rewrite: docs/PRODUCT_SPEC.md, docs/IMPLEMENTATION_STATUS.md,
  PHASE0_COMPLETION_REPORT.md through PHASE5_COMPLETION_REPORT.md where present, docs/openapi.json,
  apps/web/playwright.config.ts, apps/web/e2e/*.spec.ts, compose.test.yaml,
  scripts/integration_services.py, Makefile and all six Phase 5.5A documents.
- Proposed new engineering artifact: docs/ux-migration-coverage.md, mapping S01–S42, old control,
  new route/control, authorization, contract and regression case. Record API-only capabilities as
  API-only rather than inventing an existing screen. Confirm actual report filenames from the repo.
- Dependencies: the owner reports Phases 0–5 locally validated; retain dated evidence separately.
  Capture a reproducible current baseline in an authorized environment before changing the shell.
- Gate: all 16 current desktop/mobile Playwright scenarios are accounted for; source/data ownership,
  immutable results and denied external execution are explicit invariants. No accepted gate is
  inferred from a roadmap checkbox, screenshot or owner's report alone.

### Step 1 — tokens, accessible primitives and Romanian language (M; depends on 0)

- Existing source: apps/web/src/styles.css, locale.ts, management-locale.ts, App.tsx,
  Management.tsx, MarketData.tsx, BrokerCenter.tsx, RiskCenter.tsx, RiskBanner.tsx and StrategyLab.tsx.
  All paths after styles.css in this bullet share the apps/web/src/ prefix.
- Proposed new files: apps/web/src/ui/{Button,Field,StatusBadge,Notice,Disclosure,Dialog,PageHeader}.tsx,
  apps/web/src/ui/tokens.css, apps/web/src/copy/ro.ts and focused primitive/copy tests.
- Apply light/dark semantic tokens, readable typography, focus, spacing, reduced motion and minimum
  target dimensions. Replace the undefined --border usage with the agreed border token. Preserve
  existing explicit theme preference and OS default; do not reset the user's choice.
- Introduce input IDs, labels/help/error associations, input-purpose/autocomplete tokens and shared
  pending/disabled-reason patterns. Keep exact technical terms in advanced details and exports.
  Migrate copy incrementally; Romanian is the shipped language, not a promise of an English catalog.
- Backend dependencies: none. Preserve request/response names and all generated enums.
- Gate: current behavior and tests remain intact, token contrast calculation plus rendered checks in
  both themes, keyboard primitives, readable 320px reflow. Design values alone do not certify WCAG.

### Step 2 — five-destination shell, shared session and real task URLs (L; depends on 1)

- Existing source/config: apps/web/src/App.tsx, Management.tsx, RiskBanner.tsx, main.tsx, api.ts,
  management-api.ts, schema.ts, styles.css; apps/web/nginx.conf and apps/web/vite.config.ts.
- Proposed new files: apps/web/src/navigation/{routes,history}.ts,
  apps/web/src/shell/{AppShell,PrimaryNavigation,RouteOutlet}.tsx,
  apps/web/src/auth/{AuthProvider,RequireSession}.tsx and routing/session tests.
- Separate session, route, account context and per-resource loading state. Move auth out of repeated
  Management mounts without changing password → MFA → full-session requirements. A session endpoint
  response remains authoritative; context is not a permission grant.
- Implement the IA's native-link, typed-history adapter, Back/Forward/popstate, not-found and
  session-return behavior. Current app only routes at `/`; do not invent legacy URL aliases.
  Preserve `/` and deployment proxy handling for `/api/*`, `/health/*`, `/openapi.json`; test direct
  refresh of every proposed client route through nginx, not only Vite's fallback.
- Preserve query-independent account ownership checks; handle 401/403/404 safely. Restrict any return
  destination to validated local routes. Do not place MFA, passwords, recovery keys or auth tokens in
  URLs, browser history, persisted drafts or analytics.
- Backend reuse: auth/status, auth/me and existing authenticated clients; no new auth policy/API.
- Gate: every legacy module reachable in its new location; direct-link reload and history work;
  session loss removes protected state; overview failure does not unmount auth or safety routes.

### Step 3 — independent, scoped safety and unambiguous risk controls (L; depends on 2)

- Existing source: apps/web/src/RiskBanner.tsx, RiskCenter.tsx, Management.tsx, management-api.ts,
  schema.ts; apps/web/e2e/phase4.spec.ts, risk-fixture.ts and risk-workflow.ts.
- Proposed new files: apps/web/src/safety/{SafetyStrip,AccountSafety,EmergencyActions,
  AppliedLimits,PolicyReview}.tsx and apps/web/src/state/account-safety.ts.
- Persist simulation/external-denial information in the shell. Load account safety independently of
  overview and other accounts; one failed response yields a visible unknown state for that account,
  not a global healthy badge. Show last successful observation and stale/unavailable reasons.
  Handle account pagination or label the exact partial scope; the current100-record read cannot
  substantiate a claim about every owned account.
- Split current combined action selection into separate STOP_NEW_ENTRIES, CLEAR_STOP and FLATTEN
  workflows, with scope and consequences before confirmation. STOP does not close positions;
  clearing a stop does not authorize execution; FLATTEN remains simulated and separately confirmed.
  Preserve actual step-up/MFA requirements; do not add a fictional atomic STOP-all endpoint.
- Distinguish editable legacy risk metadata from immutable enforced profile versions. Editing a
  catalog label cannot change an applied gateway limit. Explain monetary examples without silently
  calculating an enforceable limit from incomplete broker/FX/context data.
- Backend reuse: risk account status/profiles/policies, attest, monitor, emergency, contexts,
  decisions/reservations/ledger; governance policy review is a different authority from gateway policy.
- Gate: unknown/stale/partial failure, correct account/scope, MFA denial, owner isolation, STOP/CLEAR
  and FLATTEN semantics, immutable profile binding and fail-closed entry decisions preserved.

### Step 4 — Home driven by actual available state (M; depends on 2–3)

- Existing source: apps/web/src/App.tsx, api.ts, management-api.ts, locale.ts and styles.css;
  apps/web/e2e/platform.spec.ts. Read existing overview contract in apps/api/catalog.py.
- Proposed new files: apps/web/src/home/{HomePage,ActivitySummary,NextAction,AttentionList}.tsx.
- Replace stale checkpoint, planned pipeline and static empty-experiment copy with distinct actual
  states: no data, no tests, loading, failed read, active job and available stored result. Offer one
  primary next action based on missing prerequisites; never claim the system is learning/trading.
- Use independent overview/auth/account/job/result read states. Do not translate readiness200 into
  “all workers active”, historical gain into profitability, or registration into broker connectivity.
  Keep detailed service diagnostics in Settings with a contextual link from actual failures.
- Backend reuse: overview, research experiment list/detail, market jobs, account safety. Avoid a new
  orchestration endpoint initially; deduplicate client reads without inventing aggregated authority.
- Gate: Home answers all five user questions with timestamped/qualified data; failures never become
  zero results; unavailable jobs do not erase the safety strip or other known information.

### Step 5 — guided historical data and quality feedback (L; depends on 1–2,4)

- Existing source: apps/web/src/MarketData.tsx, Management.tsx, management-api.ts, schema.ts;
  apps/web/e2e/phase2.spec.ts; read apps/api/market/routes.py and packages/market implementation.
- Proposed new files: apps/web/src/data/{DataPage,ImportWizard,ImportProgress,QualitySummary,
  DataPreview,SourceDetails}.tsx and importer form-state tests.
- Guide source choice → instrument/period → adapter-specific format → rights/calendar review →
  submit → actual quality/admission outcome. Reuse reviewed source definitions where valid; disclose
  timezone, observations/availability and missing fields at the point they affect correctness.
- Preserve all currently required fields and explicit rights, original timestamps, provider-specific
  limits, ECB reference-data constraints, version comparisons and immutable raw-object provenance.
  Never infer unavailable bid/ask prices, volume, trading hours or a point-in-time availability claim.
- Replace JSON-only quality output with observed counts, blocking reasons and repair guidance, while
  keeping exact report/provenance and download/sample access. Chart x positions represent time and
  visibly identify gaps; label units and truncation. Reimport creates a version, not an overwrite.
- Backend reuse: market/catalog, providers, imports, jobs/cancel, datasets/detail/sample/provenance/
  compare and asof. Do not replace real PostgreSQL/MinIO/Redis behavior with frontend fixtures.
- Gate: valid import persists and is selectable; invalid/incomplete data cannot start research;
  cancellation/errors retain truthful job state; timezone/availability and source labels survive.

### Step 6 — guided test, advanced setup and truthful progress (L; depends on 3,5)

- Existing source: apps/web/src/StrategyLab.tsx, BrokerCenter.tsx, RiskCenter.tsx, management-api.ts,
  schema.ts; apps/web/e2e/phase5.spec.ts, risk-fixture.ts, risk-workflow.ts.
- Proposed new files: apps/web/src/research/{ResearchPage,ResearchWizard,SetupReview,AdvancedSetup,
  ExperimentProgress,ExperimentHistory}.tsx and apps/web/src/state/research-draft.ts.
- Default flow: market → reviewed strategy → historical period → reviewed account/risk setup →
  inspect data/costs/limits → start once. A suitable default exists only if reviewed source records
  actually exist. If missing, show guided setup/owner review and return, not an invented safe preset.
- Preserve all eight fixed benchmarks, explicit account selection, immutable source/symbol/context/
  policy/profile/software pins, execution/signal/confirmation/FX dataset roles, portfolio/sweep/random
  parameters, seed, quotas and cancellation. Advanced controls remain accessible and typed.
- Keep separate field state and dependent API reads. Revalidate account-dependent choices after
  account/version changes; no stale option may be submitted merely because it was selected earlier.
  Stage/review source simulation setup before mutation; explain any prerequisite record creation.
- Keep draft state in memory by default. Optional allowlisted nonsecret session storage may retain
  route/step/reference IDs, not full account/financial/source payloads. Clear on logout and ownership
  change. A lost POST response must reconcile with a known submission key/record before retry;
  do not assume an API has idempotency if its contract does not provide it.
- Poll actual state/progress with bounded lifecycle/cancellation and independent errors. No sleeps,
  manufactured ETA, false completion after cancel request, automatic retry storm or worker heartbeat.
  Re-enter progress by owned experiment URL; rerun is a new immutable experiment.
- Backend reuse: strategies, experiments/create/list/detail/cancel; current reviewed simulation/risk
  setup endpoints. General preset and eligibility contracts are gaps below, not existing features.
- Gate: real admitted-data lifecycle, gateway-approved trades, causal replay/provenance, risk failure,
  cancellation and all current experiment invariants still pass. Ordinary tests never consume a
  sealed holdout or silently certify untouched data.

### Step 7 — understandable results, fair comparison and separate final evaluation (L; depends on 6)

- Existing source: apps/web/src/StrategyLab.tsx, MarketData.tsx, management-api.ts, schema.ts,
  styles.css; apps/web/e2e/phase5.spec.ts; read apps/api/research/routes.py and
  packages/research/{statistics,screening,contracts}.py.
- Proposed new files: apps/web/src/results/{ResultsPage,ResultSummary,EquityChart,TradeJournal,
  CausalReplay,ValidationDetails,ProvenanceDetails,ComparisonPage}.tsx;
  apps/web/src/research/FinalEvaluation.tsx and result-formatting tests.
- Show stored monetary gain/loss, largest decline, number of trades, cost assumptions, coverage,
  evaluation split and insufficient-evidence warnings before advanced statistics. Distinguish actual
  observed inputs from model assumptions. Null/undefined statistics stay unavailable, never zero.
- Plot labeled time/currency/baseline and give a keyboard-readable data alternative. Preserve exact
  stored metrics separately from limited/sampled chart points. Do not derive authoritative drawdown
  or new performance claims from the 500-point chart response.
- Preserve full accessible trade/risk-decision/replay/exposure/walk-forward/holdout/provenance detail.
  No cross-run data blending, hidden excluded trades, revised historical results or leaderboard score.
- Comparison keeps server eligibility final; 409 becomes an explanation and setup link, not forced
  normalization. Same market/period alone is insufficient to assert identical experimental conditions.
- Final holdout release has its own owner-only, step-up review, exact seal/scope/consequences and
  one-use semantics. Retain prior-exposure uncertainty and conditional Deflated Sharpe access rather
  than treating the measure as a probability of making money. No automatic promotion.
- Backend reuse: result sections/chart/pagination, provenance, compare, holdouts/release and explicit
  statistics endpoint. Downloads may reflect authorized existing data, not a fictional signed report.
- Gate: exact Decimal/money presentation, missing/negative values, unequal conditions, causal dataset
  availability, protected holdouts, owner isolation and audit linkage retain backend enforcement.

### Step 8 — complete Accounts and advanced broker tools (M/L; depends on 3,7)

- Existing source: apps/web/src/Management.tsx, BrokerCenter.tsx, RiskCenter.tsx, management-api.ts,
  schema.ts; apps/web/e2e/phase1.spec.ts, phase3.spec.ts, phase4.spec.ts and risk fixtures.
- Proposed new files: apps/web/src/accounts/{AccountsPage,AccountDetails,ConnectionsPage,
  ObservationImport,ManualSimulator,SimulationJournal,CatalogRecords}.tsx.
- Finish consolidation of account/firm/program metadata, applied limits and policies. Keep all 13
  generic record kinds reachable according to current API permissions, without conflating legacy
  metadata with trusted strategy registry, actual experiments or enforceable approvals.
- Clearly separate SIMULATED identities from DEMO_READ_ONLY observations and unverified connectivity.
  Retain public signing key/signed snapshot review; do not introduce broker credentials or an order
  transport. Mark policy-document/firm references and specific account/program policy scope precisely.
- Preserve advanced manual symbol/economic assumptions, reviewed contexts, ticks/VALID replay,
  SUBMIT+SL/TP, pending/OCO, idempotent repeat, modify/cancel/close, fault injection and reconciliation.
  Label these simulator actions and keep ambiguous execution states visible. Read-only results link
  to a journal; mutating simulator tools live in Advanced account tools. Research-created internal
  journals remain protected against manual mutation, including direct API requests.
- Backend reuse: governance records/policy verification, execution connections/observations,
  simulations/commands/replay/events and risk routes. External orders/modify/cancel remain denied.
- Gate: all old operations remain findable, ownership/filtering survives and no UI shortcut bypasses
  risk, idempotency, immutable contexts or external execution denial.

### Step 9 — security, owner onboarding, audit and diagnostics (M; depends on 2,8)

- Existing source: apps/web/src/Management.tsx, App.tsx, locale.ts, management-locale.ts,
  management-api.ts, styles.css; apps/web/e2e/phase1.spec.ts, platform.spec.ts;
  read apps/api/identity/routes.py and apps/api/governance/routes.py.
- Proposed new files: apps/web/src/settings/{SettingsPage,SecurityPage,UsersPage,AuditPage,
  DiagnosticsPage,AboutPage}.tsx and apps/web/src/auth/{OwnerSetup,MfaEnrollment,MfaChallenge}.tsx.
- Make bootstrap, MFA enrollment/confirmation and recovery-code saving a clear sequence with paste,
  password-manager support, local-only QR if a vetted renderer is selected, and manual-key fallback.
  Never send provisioning secrets to a remote QR service or persist them in draft storage/logs.
- Preserve reauthentication, password change, revoke sessions, role changes, suspend/reactivate,
  account isolation and owner-only verification. Explicit consequences precede destructive actions.
- Explain immutable actor/action/time/scope/audit verification without displaying auth secrets or
  pretending a verified chain proves the truth of every imported external observation. Preserve
  after_sequence/limit paging and existing server event_type filtering; label any additional local
  filter's limited scope.
- Move infrastructure diagnostics, API reference, roadmap and governance explanation under Settings.
  Display unavailable/not implemented honestly; a planned Phase 6 card cannot look like active AI.
- Backend reuse: all existing auth methods and governance audit/verify. No weakened MFA/RBAC or
  added recovery factor; broader audit search/export contracts, if desired, are separate work.
- Gate: complete old owner/user/security/audit flows, accessible auth, no secret capture, accurate
  operational messages and all diagnostic evidence retained behind appropriate authorization.

### Step 10 — integrated acceptance and migration release (M; depends on all earlier steps)

- Impacted existing verification: apps/web/e2e/{platform,phase1,phase2,phase3,phase4,phase5}.spec.ts,
  risk-fixture.ts, risk-workflow.ts; apps/web/playwright.config.ts, apps/web/src/*.test.ts,
  scripts/integration_services.py, Makefile and existing CI validation configuration.
- Proposed new tests: apps/web/e2e/ux-workflows.spec.ts, apps/web/e2e/ux-visual.spec.ts and
  apps/web/src/navigation/history.test.ts. New tests increase the case count; the current 16 are a
  minimum behavioral baseline, not a reason to cap coverage at 16.
- Run the real-service commands below. Adapt old locators to intentional Romanian copy/routes and
  accessible labels while preserving assertions about persisted data, authorization and risk.
  Do not leave invisible legacy controls solely to satisfy tests, loosen assertions, mock successful
  authenticated responses, skip cases or extend timeouts to conceal a lifecycle problem.
- Manual checks: both themes; 320px/400% reflow; keyboard-only, VoiceOver and at least actual Safari
  plus a real mobile browser. Current Chromium iPhone emulation is useful but not iOS certification.
  Conduct a small adult comprehension review of the five Home questions, first-test setup and result
  explanation. This is planned research, not evidence that users have already understood the design.
- Release gate: 42/42 coverage, no lost actions, approved behavior differences documented, all required
  tests actually passed, no unresolved critical safety/accessibility defects. Do not call Phase 6 or
  live trading ready. Owner separately decides whether to deploy the UX revision.

## API reuse and explicitly missing contracts

The routes below are existing API families, not a proposed rewrite. See docs/openapi.json for exact
methods, fields, enums, paging and access requirements. Maintain apps/web/src/generated/api.ts via
the repository's exporter if and only if an approved API contract changes; never hand-edit it.

- Authentication: /api/v1/auth/status, me, bootstrap, login/logout, mfa/enroll/confirm/verify/recover,
  reauthenticate, password, sessions/revoke-all and users/{user_id}. All existing gates remain server
  enforced; presentation mode and client routes cannot grant a capability.
- Governance: /api/v1/records/{kind}, record detail and revision-checked updates, policy verification and audit/verify.
  Display catalogs separately from validated execution/research records.
- Data: /api/v1/market/catalog, providers, imports, jobs and cancellation, datasets/sample/provenance/
  comparison, asof. Preserve admitted data and raw/normalized immutable storage.
- Accounts/execution: /api/v1/execution/connections/observations and simulations/commands/replay/events.
  Orders on external connections, including modify/cancel, stay DENY_ALL.
- Risk: /api/v1/risk/accounts/{account_id}/profiles, policies/status/monitor/decisions/reservations/
  ledger/emergency; policies/{policy_id}/attest, runs/{run_id}/contexts and what-if. Preserve Decimal,
  verified facts, per-scope applicability and unknown-state refusal.
- Research: /api/v1/research/strategies, experiments/list/detail/cancel/results/provenance/compare,
  holdouts/release, statistics/deflated-sharpe. Existing limits and immutable versions stay final.

Known gaps and fallback decisions:

- G01: job view lacks an exported cancellation-request flag/update timestamp and there is no current
  worker-heartbeat/ETA contract. Initial UI tracks its own acknowledged request and actual terminal
  state, labels last client check, and promises no heartbeat/ETA. If persistent request visibility is
  needed, add read fields via apps/api/research/routes.py, packages/research/contracts.py and generated
  types with contract/integration tests. Do not fake a worker readiness result.
- G02: no unified reviewed-setup/eligible-period preflight API. Compose existing read facts as advisory,
  display unknowns and retain server validation on submit. A future read-only eligibility endpoint
  needs exact account/data/policy/version scope; it cannot grant an execution approval.
- G03: no general reviewed-preset entity. Reuse existing reviewed template/context/policy records
  initially. A new saved preset requires a separately designed versioned lifecycle and review
  contract; never auto-attest owner facts or silently add a backend risk default.
- G04: incompatible comparisons return 409, without a complete structured condition-difference
  object. Show a safe explanation and known request differences, not an invented server diagnosis.
  Optional structured read-only details belong in apps/api/research/routes.py and contract tests.
- G05: limited chart equity points cannot support an exact full-resolution drawdown curve. Show
  stored authoritative summary plus labeled equity sampling initially. A new drawdown/full-series
  endpoint requires result-size/performance/access review and exact statistical integration tests.
- G06: there is no general arbitrary-CSV mapping/preview transformation service. Start with guided
  help for current adapters and exact required fields. Any later mapping must preserve original
  objects, timestamp semantics, adapter/version manifest and rejection behavior; no synthetic repair.
- G07: audit API supports after_sequence/limit and event_type filtering, not general actor/time/full-text
  search or a signed-report service. Use existing server filtering and honest loaded-page filters. A broader search or report export needs an authorized,
  bounded contract and verification model, not a UI claim of a signed or complete compliance report.

Optional contracts are not prerequisites for starting the shell/copy work if their fallbacks remain
truthful. Contract changes require separate scope, generated schemas and real integration tests.
No database migration is expected for the baseline presentation redesign. Any later persisted
preset/schema addition must use Alembic; never rewrite immutable experiments or development volumes.

## State, failure and mutation discipline

- Separate session, navigation, safe draft, server records and transient mutation state. Reuse API
  clients; introduce small typed resource hooks before adopting a new global cache library.
- Cancel/ignore obsolete reads after account/route changes. Do not let a slower old response repopulate
  the new account view. Invalidate affected reads after actual successful mutations.
- A failed request is not empty data; stale data has visible age and cannot authorize an action.
  Preserve safe user inputs while marking facts requiring review. Never persist OTP/recovery/password.
- Financial mutations are deliberate, version-bound and server validated. Do not retry an ambiguous
  submission with a new key. Lookup/reconcile according to the actual endpoint contract; if no safe
  reconciliation exists, show uncertainty and instructions rather than promise idempotency.
- Advanced disclosure never grants RBAC, holdout, policy or execution authority. Use the same backend
  paths for beginner and advanced views; no parallel simplified financial calculation engine.

## Regression and UX test strategy

The existing suite contains eight scenarios per viewport, 16 total across desktop and mobile:
three in platform.spec.ts and one each in phase1–phase5.spec.ts. Keep every behavior, including owner
MFA/onboarding, persistent governance, real imports/quality/stored prices, simulator/replay/idempotency,
independent gateway/policy/emergency behavior and admitted-data research/results/cancellation.
Preserve the explicit overview-outage fault injection; it tests a failure, not fabricated integration.

Add focused coverage for:

- Every route, native Back/reload, guarded direct links and safe post-MFA return.
- Independent safety during overview failure, per-account partial failure and stale-monitor state.
- Missing reviewed defaults, visible blocker/reason, keyboard wizard flow and account-switch invalidation.
- Import invalidity/rights/availability issues, repair guidance and immutable reimport version.
- Pending/cancelled/failed experiments and reconciling uncertain submission without duplicate mutation.
- Result null/negative/cost/coverage warnings, sampled-chart labeling, comparison refusal and accessible
  table equivalents. Verify with stored results, not fabricated gain/loss success fixtures.
- Role/ownership denials, internal-journal mutation refusal, STOP versus FLATTEN, owner-only final
  holdout release and immutable audit/version links.
- Dialog focus/Escape/return, meaningful accessible labels, error summaries and disabled explanations.

Visual regression is additive, not a substitute for assertions or service integration. Use sanitized
non-secret states from disposable owned service data, both themes and key widths. Never blanket-enable
screenshots/traces for MFA/password/recovery screens: current secret-protective settings stay default.
Dedicated safe visual tests may opt in after review. Stabilize clocks/IDs only where incidental;
do not mask safety status, source labels, meaningful prices, risk decisions or error evidence.

Future implementation commands, **not claimed run for this redesign**:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO make browser-integration
make check
make integration
make contracts-check
make smoke-demo
make repository-check
make secret-scan
```

Use the existing isolated test project, temporary credentials, loopback ports and automatic cleanup
for actual PostgreSQL, Redis and MinIO. Cleanup may touch only that disposable project's resources;
no development volume deletion, compose down of the owner's stack or broker connection is authorized.
Record command, revision/config, exit code, counts, failures and fixes. If managed browser access is
blocked, record BLOCKED, preserve the restriction and provide local owner commands; no bypass or
claimed browser acceptance. Current audit command results are in PHASE55_UX_AUDIT.md.

## Rollout, rollback and unresolved decisions

Use small runnable changes in sequence; retain a tested prior shell revision until coverage is proven.
An optional UI-only rollout flag may choose old/new navigation, never disable MFA/risk checks or
authorize live behavior. The rollback is a UI revision with the same API/data contracts, not restoring
an old database over new records. Keep historical results, evidence and all owner data intact.

Defaults requiring no new infrastructure: five destinations; Romanian only; system theme with explicit
override; no new router dependency; in-memory drafts; existing reviewed configurations; stored exact
metrics and honest chart sampling; research comparison warnings instead of a synthetic success score.
Trade-offs to validate later: all five mobile destinations must fit with labels, account setup remains
an owner responsibility, broad statistical interpretation needs careful helper text, and advanced
simulator controls remain dense even after moving behind purposeful tasks. Use adult comprehension
sessions and actual browser/assistive-tech checks to refine these, not unsupported research claims.

Stop at this blueprint. No redesign implementation, deployment, automated promotion or Phase 6 begins
without the owner's separate instruction.

## Phase 5.5B execution record

Steps0–9 have source implementations, preserving the order/dependencies and all42 mapped units;
P0 auth/safety changes preceded visual polish. Step10 has passing native/build/contract checks and
20-case collection; browser/manual/visual acceptance is BLOCKED, not completed. See the completion
report and coverage map for exact changes and each issue status. G01 now exports cancellation-request
flags; import progress also has a new owned GET job route. Other optional contracts were not invented.
A local QR renderer remains deferred with manual TOTP preserved. No Phase6 begins.
