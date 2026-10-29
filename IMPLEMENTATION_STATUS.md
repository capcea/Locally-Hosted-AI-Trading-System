# Implementation Status

## Current sidebar health repair — 2026-10-29

Actual API/proxy overview200 payloads parse correctly and explicitly report all four stable
infrastructure IDs HEALTHY. The shell compared a pre-request clock with a later completion time,
repeatedly marking valid observations future/stale. Atomic completion timestamps, independent age
updates, backend timestamp validation and response fencing correct this. Status/retry feedback
retains the V1 design and separates infrastructure from trading/AI/broker capability.
Native check294 Python/186 frontend, focused67, contracts and deployed API smoke pass.28 browser
cases collect only; managed browser execution remains BLOCKED. Running nginx Web still needs the
targeted owner-local rebuild; no Docker or persistent data was changed in this task. Public phase6 /
Phase7 PLANNED are static coarse metadata, not evidence that the partially accepted Phase7A source
is absent or that broader Phase7 is accepted. Read
[the repair report](SIDEBAR_SYSTEM_HEALTH_FIX_REPORT.md) for evidence and verification commands.

## Current MFA/session repair — 2026-10-29

IMPLEMENTED / NATIVE PASSED / API AND WEB UPDATED / BROWSER BLOCKED. Invalid MFA401 was
incorrectly clearing valid frontend authentication; late responses could discard a rotated session;
and the new session row could be invisible when its cookie headers were sent. Each defect was
reproduced before correction. In-place password/new-TOTP step-up now preserves the original form,
atomically commits rotation before response, refreshes CSRF and fences stale responses. Genuine
expiration still requires password login and MFA. No automatic sensitive-action replay occurs.

`make check` passes294 Python/160 frontend cases; focused actual-service auth27+27 and full
`make integration-services`117+117 pass across graceful restart. Contracts, deployed API smoke and
secret/repository checks pass. API/Web were rebuilt and restarted alone; other containers and
development volume identities are unchanged. All1357 pre-task source/evidence files are retained.
The new browser scenario collects with the28-case desktop/mobile suite; execution is BLOCKED by
managed browser policy, not claimed passed. No owner enrollment/session reset, financial logic,
accepted visual reference, paid provider call or trading authority changed. Five-minute recent MFA,
RBAC, CSRF, revocation, holdouts and SIMULATED/DENY_ALL remain enforced. Read
[the repair report](MFA_SESSION_FLOW_FIX_REPORT.md) for exact evidence and owner-local acceptance.

## Current risk-monitor recovery — 2026-10-28

The owner's next Compose run recreated PostgreSQL while risk-monitor was polling; its uncaught
connection-refused error exited the daemon. This is separate from the corrected campaign packaging.
The monitor now reconnects within a finite six-failure budget, withdraws readiness on database loss,
rechecks restricted identity before every scan and keeps non-transient refusals fatal. The original
per-account scan, risk math, manual stops, authorization and freshness thresholds are unchanged.
Actual restricted-role service startup is healthy; only risk-monitor was recreated and all
persistent mount identities are unchanged. Native check290 Python/153 frontend and focused real
risk27+27 across restart pass. A real disposable connection-termination test preserves the owner's
STOP, refuses an order and validates audit integrity after recovery. Full `make integration` passes
(exit0): readiness,108+108 across restart, final API/execution-denial smoke200. Contracts and secret/
repository checks pass. See [the recovery report](RISK_MONITOR_RECOVERY_REPORT.md). No paid/model/browser/trading
activity was introduced. Earlier current-phase entries below retain their checkpoint evidence.

## Current local startup repair — 2026-10-28

The owner applied migration0009 and rebuilt the stack. A campaign-container packaging defect is
now repaired: the control Dockerfile omitted `scripts.campaign_worker.py`. It now copies the
entrypoint and runs packaged `--help` during build. Actual non-root/no-network image smoke,
targeted service start, fresh heartbeat, database read and AI isolation checks pass. Only the
campaign worker was recreated; other container IDs and development volume identities are unchanged.
`make check`283 Python/153 frontend, contracts, secret/repository scans and current API smoke pass.
Full `make integration` now passes (exit0): development readiness,107 cases before/107 after restart
and final API readiness200/execution-denial smoke. Earlier migration0008 failure/pending-deployment
statements below preserve the prior implementation run. Real provider/browser/V1 visual acceptance
remain open. No key entry, provider inference or trading activation occurred. See
[startup evidence](OPENROUTER_INTEGRATION_REPORT.md#follow-up-campaign-container-startup-repair--2026-10-28).

## Current follow-up — OpenRouter integration and AI settings (2026-10-28)

IMPLEMENTED / ISOLATED NATIVE CHECKS PASSED / DEVELOPMENT UPGRADE PENDING / BROWSER BLOCKED /
REAL PROVIDER NOT VERIFIED. Read [OPENROUTER_INTEGRATION_REPORT.md](OPENROUTER_INTEGRATION_REPORT.md)
for the root cause, exact setup sequence and minimal-cost real-call approval gate.

Read-only inspection confirms zero approved endpoints/connections/models, so the empty selectors
primarily reflect missing configuration. Secondary registry loading, placeholder, protocol and
verification-expiry defects are repaired. The existing compatible adapter now supports exact
OpenRouter HTTPS behind independent operator opt-in, owner-MFA cloud consent, encrypted write-only
keys, fixed egress/DNS/TLS checks, atomic spend reservations and explicit per-request cost approval.
Private Ollama/private-compatible providers remain the default. No real provider request was made.

Final `make check`:283 Python +153 frontend cases, strict native/build checks pass. Focused cloud
services:7 before/7 after restart; full isolated services:107 before/107 after restart. Contracts,
existing deployed API smoke and secret/repository checks pass. `make integration` remains FAILED
(exit2): source schema0009 versus retained development0008. No development data, key files, operator
configuration or running services were changed.26 browser cases collect; managed localhost policy
still blocks execution. Real-model, cloud UX, network deployment and existing V1 manual/visual gates
remain open. All1328 original source/evidence files are retained; accepted goldens unchanged.
SIMULATED/DENY_ALL, MFA/RBAC/CSRF, holdouts, financial calculations and Phase7 research limits remain.
No next phase, automatic code execution or broker orders.

## Current phase — Phase7A bounded research foundation (2026-10-28)

IMPLEMENTED / ISOLATED NATIVE CHECKS PASSED / DEVELOPMENT READINESS FAILED / EXTERNAL ACCEPTANCE OPEN. The owner explicitly
authorized Phase7A and postponed V1 final visual acceptance. Earlier no-Phase7 statements below
are historical evidence, superseded only for this bounded research foundation. Campaign creation,
immutable authorization/lineage, finite candidate domains, durable budgets/leases, owner-reviewed
Phase5/6 handoffs, canonical evidence evaluation and bounded training feedback are source-implemented.
Testează → Campanii de cercetare adds guarded stable routes without changing primary navigation.
There is no unattended session impersonation: original recent-MFA requirements remain.

Synthetic campaigns reuse actual PostgreSQL/Redis/MinIO and original reviewed backtests/Risk Gateway.
Fixture labels prohibit real candidacy and promotion. Actual AI mode refuses unavailable/unverified
models; real-model inference is not accepted. Existing development services/data were not migrated,
rebuilt or reset for this phase. Browser execution remains blocked by the prior explicit managed
localhost-origin restriction;26 scenarios collect, which is not execution success. V1 visual/manual
acceptance remains postponed. SIMULATED/DENY_ALL; no code runner, paper/live orders or Phase7B.

Final checks pass263 Python +152 frontend cases; focused campaigns pass14 before/14 after restart;
full isolated services pass100 before/100 after. Contracts, existing API smoke and secret/repository
checks pass. The full `make integration` target fails its first development schema probe (expected0008,
retained0007); it is not reported as passed. A prior MinIO clock-skew restart failure is preserved;
the final fresh full isolated rerun passed without weakening clock checks. Exact commands and
intermediate failures are retained in the report/evidence package.

Read [the Phase7A report](PHASE7A_COMPLETION_REPORT.md),
[architecture](AUTONOMOUS_RESEARCH_ARCHITECTURE.md), [lifecycle](RESEARCH_CAMPAIGN_LIFECYCLE.md),
[evaluation](RESEARCH_EVALUATION_POLICY.md) and [security](RESEARCH_SECURITY_BOUNDARIES.md).


Owner-local browser follow-up at16:33 reaches the Home visual assertion and fails against the
old Phase5.5 reference (1280×1047 versus V1 1280×1684;237080 pixels). Available PNGs exactly match
previously preserved pre-polish artifacts; current rendered fidelity and the full26-case suite
remain unverified. No golden was replaced. Read the V1 final audit follow-up for fresh review
capture commands and the required exact-image approval gate.

## Current UI — V1 visual polish (2026-10-28)

SOURCE REFINED / NATIVE CHECKS PASSED / FINAL VISUAL ACCEPTANCE OPEN. All nine source compositions,
five primary destinations, S01–S42 and Phase6 routes remain. All11 approved reference PNGs were
reinspected and14 handoff entries hash-verified. The designated nine-screen capture directory is
missing. One genuine public Home before image in owner Playwright artifacts was inspected:
UNKNOWN split mid-word, tall AI suggestions stretched the chart row, and heading focus spanned the
header. Independent Home columns, a status-value style, compact suggestions, title-sized visible
focus and shared header insets are corrected in source. No after/browser/mobile/dark acceptance.

Fresh make check passes243 Python +149 frontend tests; integration passes one readiness case and86
real isolated cases before and86 after restart. Contracts, strict readiness/order-refusal smoke,
secret/repository checks pass.24 browser cases collect; no browser execution is claimed. A fresh
managed localhost-origin denial prevents captures and focused/full browser execution. Preserved
owner failure reports237080 changed pixels against an older UI golden, not against the V1 mockup.
All four goldens remain unchanged; exact future public candidates need owner review. Web is refreshed
and healthy. All12 non-web container identities/images/mounts and162 backend/infrastructure files
are unchanged. No development data deletion, rule change, external orders or Phase7 implementation.
Optional AI worker was already unhealthy; a UI change does not establish runtime connectivity.

See [final audit and exact results](REDESIGN_V1_FINAL_VISUAL_AUDIT.md),
[visual review package](docs/redesign-v1-evidence/2026-10-28/final-visual-review/index.html),
[implementation history](REDESIGN_V1_IMPLEMENTATION_REPORT.md) and
[visual fidelity ledger](REDESIGN_V1_VISUAL_FIDELITY.md). Remaining gates: genuine after/nine-screen
captures, manual responsive/accessibility review, exact golden approval and all24 browser cases
without snapshot rewriting. SIMULATED/DENY_ALL and all security/research boundaries remain.
Earlier sections below preserve historical evidence, not current V1 rendered acceptance.

## Current phase — Phase6 private AI gateway (2026-10-28)

IMPLEMENTED / ACCEPTANCE PARTIAL. The owner explicitly authorized Phase6 and reports Phases0–5.5
local automated acceptance passed (OWNER_REPORTED_PASS, not agent verification). Earlier sections
below remain historical evidence; their previous no-Phase6 gate is superseded by that authorization.

Private adapters, expiring model registry/role routing, bounded durable encrypted requests,
read-only owner-scoped context, strict inert output contracts, separate worker SQL/Redis identities,
additive Alembic0007, Romanian AI Center and isolated deployment templates are implemented.
SIMULATED/DENY_ALL, MFA/CSRF/ownership, enforced risk and holdout boundaries remain. No generated-code
execution, trading authority, broker credentials or Phase7 agents.

The owner-local Phase6 desktop browser run now supplies an actual UI failure: the exact
`Destinație aprobată` label did not resolve because nested option text polluted Playwright's label
text. Eight AI dropdowns now have stable explicit accessible names matching their visible labels.
Four new native regression cases fail before the correction and pass after it; the real-service
registry test also checks authenticated approved-endpoint discovery. The browser test retains its
exact locator and adds endpoint/value and actual HTTP201 creation assertions. No timeout, API,
authorization, endpoint allowlist, model verification or safety rule changed. Current browser
acceptance still requires a fresh owner-local run; see the
[correction report](PHASE6_COMPLETION_REPORT.md#ai-dropdown-accessible-name-correction--2026-10-28).

Latest portable checks pass243 Python and121 frontend tests; full native integration passes one
readiness case and86 cases before and86 after restart. Earlier focused AI revalidation passed8 before
and8 after restart, including actual SIGKILL and holdout/cached-context refusal. Contracts, smoke,
secret/repository scans and22-case Playwright collection pass. Browser execution remains BLOCKED
by the managed localhost-origin restriction. No real Ollama runtime/model is reachable; fixture
transport evidence is explicitly SYNTHETIC, not AI model validation. Optional AI services now run locally; actual worker SQL/Redis/network isolation checks pass,
including after queue restart. Initial create delays, stateless API-name conflict and Redis chown
failure were recovered without restoring capabilities. All eight normal development services are healthy. Existing data mounts are unchanged; PostgreSQL container
was recreated to add a private network. Read [the complete report](PHASE6_COMPLETION_REPORT.md),
[architecture](AI_GATEWAY_ARCHITECTURE.md) and [deployment guide](AI_DEPLOYMENT_GUIDE.md).

## Current follow-up — whole-interface tidy-up (2026-10-28)

IMPLEMENTED; current rendered/browser/manual acceptance remains NOT COMPLETE. The owner requested
a modest whole-interface refinement after the research-screen screenshot. Shared spacing/forms/
tables/cards, task navigation and Settings grouping are tidied; research opens directly into one
wizard. Safety presentation retains unknown/stale states, account scope and observation age, and
calls out last-known stops. Every existing destination, owner/MFA/role guard, reviewed research
configuration and backend rule remains. No backend/API/schema or Phase 6 change.

make check passes 212 Python + 114 frontend tests; integration passes one readiness case and 78
isolated cases before restart and 78 after. Contracts, strict readiness/execution-denial smoke and
20-case browser collection pass (exit 0). The local web image is refreshed and its HTML/
CSS/JS hashes match the production build. All seven non-web service identities/images/mounts and
all four prior approved PNGs remain unchanged. Full actual verification is in the
[UI tidy-up report](docs/UI_POLISH.md) and
[completion follow-up](PHASE55B_COMPLETION_REPORT.md#whole-interface-uiux-tidy-up--2026-10-28).
The earlier screenshot approvals apply to the previous presentation. Fresh actual captures need
review for these intentional changes; no references were rewritten or browser success inferred.
SIMULATED/DENY_ALL remains active. No Phase 6 or external execution.

## Previous gate — mobile visual references (2026-10-28)

MOBILE REFERENCES APPROVED; overall acceptance remains NOT COMPLETE. The latest owner run reports
one mobile visual failure and one other passing case. The actual error-context identifies both
home-light-mobile-darwin.png and home-dark-mobile-darwin.png as missing, not mismatched. Both
genuine actual PNGs were inspected offline (390×1317). Generated reference files now exist and are
byte-identical to their respective actual captures. The owner subsequently explicitly approved both
mobile references; exact hashes and adoption scope are recorded in
[approval.json](docs/phase55b-evidence/2026-10-28/mobile-reference-review/approval.json).
No PNG copy or rewrite was needed. Approval is separate from a fresh passing browser comparison.
Review copies and exact hashes are retained in the
[mobile reference review](docs/phase55b-evidence/2026-10-28/mobile-reference-review/review.json).
No app/test code, tolerance or desktop reference changed. make check passes 212 Python + 98
frontend tests; smoke passes HTTP 200 (exit 0). No full service-suite rerun was needed for this
evidence-only review. The prior real-service results below remain historical evidence. All four
current reference hashes are verified unchanged. Current rendered
interaction, all 20 scenarios and manual gates are still not verified here. SIMULATED/DENY_ALL.
See the [current report](PHASE55B_COMPLETION_REPORT.md#mobile-visual-reference-review--2026-10-28).

## Previous correction — market browser synchronization (2026-10-28)

FIXED IN TEST SOURCE; full browser acceptance remains BLOCKED / NOT COMPLETE. The owner's next
run reports four foundation passes, then a Phase 2 desktop 120-second global timeout. The actual
error-context contains no active locator, call stack or DOM; the exact original timed-out await is
unknown. Source inspection found two missing completion boundaries: navigating away before the
instrument save completes and navigating to datasets before the accepted import redirects to its
job. The test now requires actual response statuses, instrument persistence, the job redirect and
real worker success. Ten fixed, non-secret workflow step names improve future failure diagnosis.
All 16 original assertions and the global timeout remain unchanged. No application/backend,
financial, authorization, provenance or screenshot-reference changes. Focused service tests pass
three cases before and three after restart. Final make check passes 212 Python + 98 frontend tests;
integration passes one readiness case and 78 isolated cases before and 78 after restart, with strict
readiness/smoke. Contracts, smoke, secret/repository/whitespace checks pass (exit 0); 20 browser cases
collect only. Eight development containers/mounts/images and approved PNG hashes remain unchanged.
Actual verification, initial check failures and the
remaining owner-local commands are in the
[market browser correction report](PHASE55B_COMPLETION_REPORT.md#market-import-browser-synchronization-correction--2026-10-28).
Native integration does not establish Chromium acceptance. All 20 desktop/mobile cases still require
a successful local run. SIMULATED/DENY_ALL remains active. No Phase 6.

## Previous correction — returning-owner MFA/navigation (2026-10-27)

FIXED IN TEST SOURCE; browser acceptance remains BLOCKED / NOT COMPLETE. The owner failure at
phase1.spec.ts:156 shows the login form after the test immediately hard-navigated following an
async MFA click. The test now awaits the exact verification response/completion, FULL authenticated
UI and auth/me owner state before navigation. Existing account/persistence/reload/security assertions
remain intact. Native PostgreSQL tests confirm account persistence, actual rotated-cookie access
and rejection of the revoked challenge cookie. Two focused tests pass before and two after restart;
make check passes 212 Python + 98 frontend tests; full integration passes 78 cases before and 78
after restart, plus readiness/strict smoke. Contracts, secret/repository/whitespace checks pass
(exit 0). All development container identities/mounts and approved reference hashes are preserved.
Complete current evidence is
in the [MFA/navigation correction report](PHASE55B_COMPLETION_REPORT.md#returning-owner-mfanavigation-correction--2026-10-27).
No app/backend rules, MFA window, RBAC, financial logic or approved visual references changed.
All 20 desktop/mobile browser cases still require a successful owner-local run. No Phase 6.

## Previous visual-reference review — Phase 5.5B (2026-10-27)

Owner post-fix PNGs inspected: 336 pixels differ only in the intended fixed clock-mask expansion
(16×21 at inclusive x=1177–1192/y=962–982); every other RGBA pixel is identical. Old reference 55px
versus fixed-slot 71px. The owner explicitly approved the genuine light-desktop candidate; only that reference was replaced
byte-for-byte and its previous version retained as evidence. The next owner run reached dark after light. Actual dark PNGs also show only the same 336 mask pixels;
the owner explicitly approved it and only the dark-desktop reference was replaced byte-for-byte.
Both approved desktop reference hashes are verified. Mobile captures and full 20 acceptance remain
unverified; rerun focused UX and then the complete suite without snapshot rewriting. No source, tolerance or financial/security change
in this review. See [the concrete review](PHASE55B_COMPLETION_REPORT.md#owner-post-fix-visual-reference-review--2026-10-27).

## Previous source correction — Phase 5.5B visual timestamp mask (2026-10-27)

FIXED IN SOURCE; references/browser/manual acceptance NOT COMPLETE. Inspected the owner's actual
expected/received/diff PNGs: all 84 differing pixels form a 4×21 footer-clock mask strip at inclusive
x=1189–1192/y=962–982; every other RGBA pixel is identical. Proportional timestamp text changed the
intrinsic mask width from 55 to 59px. A fixed 8ch, tabular HH:MM:SS component now preserves the actual
observation with semantic datetime; strict comparisons and timestamp-only masking remain unchanged.
No tolerances or baselines were changed. Owner review is required for new stable-slot references.
make check passes 212 Python + 98 frontend tests; focused clock tests, contracts and smoke pass.
All 20 browser cases collect; actual reruns remain blocked for this agent by the saved managed-origin
restriction. See the [visual correction report](PHASE55B_COMPLETION_REPORT.md#visual-timestamp-mask-correction--2026-10-27)
for genuine image evidence, exact commands and owner review steps. No Phase 6 or external orders.

## Previous correction — Phase 5.5B risk-policy HTTP 503 (2026-10-27)

FIXED IN SOURCE; overall acceptance BLOCKED / NOT COMPLETE. A deterministic actual-PostgreSQL
regression reproduced POST /api/v1/risk/accounts/{account_id}/policies returning 503 with SQLSTATE 40P01:
owner→account locks in authenticated requests conflicted with account→owner-FK locks in the independent
monitor. The monitor now locks owner before account; both transactions commit, the policy remains
UNVERIFIED and stops/authorization/audit remain enforced. Safe correlated diagnostics were added.
Focused native policy tests pass 4 cases before and 4 after restart. make check passes 212 Python + 94
frontend tests; make integration passes 77 before and 77 after restart plus readiness/smoke. Contract,
smoke, secret and repository checks pass (exit 0). Final evidence is tracked in the
[correction report](PHASE55B_COMPLETION_REPORT.md#risk-policy-503-correction--2026-10-27). The owner's
actual browser503 artifact was inspected; its body/request ID/server log were unavailable. Browser
execution remains blocked for this agent by the saved managed-origin restriction;20 cases collect,
not 20 passing executions. No snapshots changed, Phase 6 or external orders enabled.

## Initial UI migration evidence — Phase 5.5B (2026-10-27)

Implementation delivered; acceptance **BLOCKED / NOT COMPLETE**. Five destinations, independent
auth/safety, separate reviewed emergency actions, guided data/research, understandable stored results,
scoped account tools and Settings are implemented.208 Python +94 frontend checks pass; real service
integration passes76 cases before and76 after restart.20 Playwright cases collect; current execution
and manual/visual acceptance are blocked by the managed origin permission. No browser/WCAG success
is inferred. See [PHASE55B_COMPLETION_REPORT.md](PHASE55B_COMPLETION_REPORT.md) and
[coverage](docs/ux-migration-coverage.md). SIMULATED/DENY_ALL and all financial/security gates remain.
No Phase6. Prior phase evidence and all60 criteria below are retained as historical implementation status.


## Historical Phase 5 evidence — retained from before this migration

The following records the agent verification at that revision. The owner subsequently reported
Phases 0–5 locally validated; original local logs were not supplied. This historical record does not
replace the current Phase 5.5B acceptance gate above.

Updated: 2026-10-27 · API 0.1.0 · Phase 5 · SIMULATED · external DENY_ALL.

**Phase5 remains NOT fully accepted.** The owner reproduced an actual UI exact-label timeout after
Chromium launched. The Strategy Lab select labels are corrected; the agent's latest focused rerun
separately fails at managed Chromium bootstrap1100 before UI assertions. Do not confuse the two.
Exact cause, source files, owner artifact, commands/exits and remaining gates:
[PHASE5_COMPLETION_REPORT.md](PHASE5_COMPLETION_REPORT.md#strategy-lab-exact-label-correction--current-revision-2026-10-27).
No Phase6, generated code, broker credentials/orders or paper/live promotion. Prior Phase4 browser
acceptance remains owner-reported, without supplied original commands/logs.

## Specification traceability

The original master and docs/PRODUCT_SPEC.md retain SHA-256
c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085.
A01–A60 below are derived audit criteria, not reconstructed original questionnaire numbering.
4 fully functional, 43 partially implemented, 0 mocked-only and 13 missing. These classify the full
master scope, not Phase 5 acceptance or effort. Earlier dated reports remain historical evidence.

## Current verification — exact-label correction

- FIXED IN SOURCE: implicit label text included option text, preventing exact Playwright lookup.
  StrategyLab now gives selects explicit matching Romanian labels; original exact locator retained.
  E2E additionally asserts visibility and the fixture account option. MFA/RBAC/risk/data unchanged.
- PASSED: make check,208 Python +16 frontend tests, lint/types/build; make contracts-check and smoke.
- PASSED: make integration,1 readiness case +76 actual disposable cases in each write/restart stage,
  then strict smoke200. No skipped tests or fake service acceptance.
- PASSED: rebuilt/recreated Web matches latest image; served JS includes corrected labels. API
  ready200/phase5/schema0006 and all external execution flags false. This is not browser acceptance.
- FAILED/BLOCKED: current focused desktop command exit2,76/76 native stages pass then Chromium
  bootstrap1100 before page creation. Original owner UI assertion failure is recorded separately.
- NOT RUN FOR THIS FIX: full16-case execution, pending focused success. All16 still collect. Earlier
  full command had3 launch failures,1 HTTP-only pass and12 NOT RUN; that is historical, not a new pass.
- PRESERVATION:3 data container IDs/mounts unchanged. Old whole-DB equality guard fails on5 auth/audit
  tables versus the earlier private snapshot;35 other legacy hashes match. Read-only comparison finds
  only last_totp_step changed on existing users; passwords/MFA/identities unchanged, original audit/
  sessions retained and authentication rows appended. The three new auth events predate this patch.
  HMAC chain valid; no guard weakened, data rollback or dev-volume removal.

## Phase 5 module inventory

- IMPLEMENTED: eight fixed reviewed baselines, immutable source/version/parameter definitions,
  causal features and explicit automation/session/holding/protection requests; no dynamic code loading.
- IMPLEMENTED: bounded PyArrow vectorized exploratory screening and actual event-journal/risk-gateway
  validation, isolated accounts/clocks, portfolio/MTF inputs, observed ticks and explicit OHLC uncertainty,
  pending/partial orders, fees/funding/stress and terminal inventory refusal.
- IMPLEMENTED: Decimal monetary metrics, descriptive ratios with sample/calendar guards, chronological
  walk-forward training/OOS, purged intervals/embargo, seeded bootstrap/block/permutation robustness,
  causal regimes, registered hypothesis counts and conditional owner-declared DSR assumptions.
- IMPLEMENTED: seven additive PostgreSQL research tables, immutable MinIO artifacts and provenance,
  semantic reproduction digest, fenced durable jobs, cancel/retry/SIGKILL recovery and quotas.
- IMPLEMENTED: authenticated owner-MFA APIs and Romanian real-API Strategy Lab library/configuration/
  jobs/results/curve/replay/walk-forward/comparison/provenance and one-use final evaluation release.
- PARTIAL: ordinary API holdout custody is protected, including owner-wide overlapping aliases;
  prior exposure remains UNKNOWN and never certified untouched. Independent custodian secrecy,
  real historical coverage, production scale and external broker facts remain unverified.
- NOT IMPLEMENTED: AI/ML/LLM judges, hostile-code sandbox, research-to-paper eligibility, paper engine,
  external order executor, independent broker signing authority, live approvals and promotion.
- MOCKED/CONTRACT_FIXTURE: prior fake MT5 SDK/cTrader protocol tests are still fixtures; actual service
  connectivity is not established by backtests. Phase 5 service fixtures use real PG/Redis/MinIO and
  explicitly synthetic market observations. No manufactured profitability or five-year history claim.

## Previous phases

Identity, owner/MFA/CSRF/account partitions, Phase 2 immutable data/quality, Phase 3 deterministic
simulator/journal and Phase 4 gateway/ledger/reservations/monitor are reused. No dev volumes are removed.
The current local/runtime/preservation and test evidence is in the Phase 5 report and execution ledger.
Remote CI and Git writes remain NOT RUN; managed .git is read-only. No workaround or push occurred.

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

Eight trusted intraday research baselines are implemented; calibrated performance, broader families and external venue validation remain unverified.

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

**PARTIALLY IMPLEMENTED.** Phase6 provides independently configured RESEARCH/CODING/CRITIC/LIGHTWEIGHT
proposal roles, strict versioned untrusted outputs and measured provider capabilities. No autonomous
agent runtime, nine-role orchestration or scheduler is implemented. Real-model and browser gates
remain open; see PHASE6_COMPLETION_REPORT.md.

### A14 — Isolated code branches and controlled release promotion

**MISSING.** Source: §0 invariant 4, §9, §15. Evidence: AGENTS.md describes future restrictions.

Implement artifact-specific write capabilities and a release manager outside agent control.

### A15 — Strategy families and non-ML baselines

**PARTIALLY IMPLEMENTED.** Evidence: Eight reviewed causal non-ML strategies, immutable registry and typed sizing/exit/session contracts are implemented in packages/research/strategies.py.

Broader autonomous/ML strategy families and real historical validation remain future work.

### A16 — XGBoost, LightGBM, HMM/clustering comparisons

**MISSING.** Source: §1, §6. Evidence: No ML training/evaluation module.

Implement fold-local training, reproducible artifacts and baseline/OOS comparisons.

### A17 — Time-available features and fold-local preprocessing

**PARTIALLY IMPLEMENTED.** Evidence: Visible-only features, strict prior-availability MTF/as-of joins and fold-local train/OOS execution are implemented; future-window guards and native closed-bar/tick tests apply.

ML preprocessing/training remains NOT IMPLEMENTED; no fitted-transform claim.

### A18 — vectorbt screening

**PARTIALLY IMPLEMENTED.** Evidence: packages/research/screening.py uses existing PyArrow compute as the vectorized equivalent, lagged exposure, explicit costs, batching and deterministic random controls.

Bounded exploratory screening is not execution validation, paper eligibility or proven large-scale capacity; pending/cross-currency/MTF require EVENT.

### A19 — Event-driven backtest and executable signal parity

**PARTIALLY IMPLEMENTED.** Evidence: packages/research/engine.py reuses the actual execution journal and Phase 4 gateway with isolated accounts, immutable inputs, costs and causal signals.

Future paper/live parity and actual broker execution remain unverified/unimplemented.

### A20 — Bid/ask, spread, fees, slippage, latency, partial/rejected fills

**PARTIALLY IMPLEMENTED.** Evidence: Explicit exact bid/ask, adverse slip/gaps, seeded latency, commission, optional continuous modeled funding and finite side-liquidity/partial/rejection cases pass.

These are documented synthetic assumptions; no measured real-world fill accuracy or verified broker rollover.

### A21 — Chronological OOS and untouched final holdout

**PARTIALLY IMPLEMENTED.** Evidence: Chronological phases, owner-MFA seals, ordinary-read/alias exclusion and one frozen audited final release are implemented.

Prior exposure is UNKNOWN, never certified untouched; independent custodian/host-admin-resistant secrecy is not implemented.

### A22 — Walk-forward, purging/embargo and multiple-testing controls

**PARTIALLY IMPLEMENTED.** Evidence: Actual train-only parameter selection, independent OOS accounts, purge/embargo, interval CV and immutable attempted hypotheses are implemented.

DSR requires explicit owner-declared independent count/variance model; correlated sweeps do not prove independence or authorize promotion.

### A23 — Bootstrap/Monte Carlo, regimes, metrics and confidence

**PARTIALLY IMPLEMENTED.** Evidence: Stored-fill/equity Decimal metrics, sample-safe ratios, seeded bootstrap/block/permutation uncertainty and causal regimes are implemented.

Synthetic tests establish arithmetic/behavior, not empirical profitability, stationarity or adequacy of real history.

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

**PARTIALLY IMPLEMENTED.** Phase6 implements independently validated versioned structured proposals,
exact JSON authority/version types, bounded references, missing evidence, inert coding text, no tools
or broker/risk authority, actual HTTP/TLS/adversarial/native isolation tests. Real installed-model
behavior remains BLOCKED; schema validity never certifies financial truth. See AI_SECURITY_BOUNDARIES.md.

### A47 — Hardened hostile-code sandbox with quotas and immutable inputs

**MISSING.** Source: §0 invariant 4, §3, §15. Evidence: workers/safety.py refuses execution; docs/THREAT_MODEL.md.

Implement VM/microVM isolation, denied egress/mounts/credentials and escape/exfiltration/quota tests before any generated code runs.

### A48 — Mandatory independent deterministic risk gateway, no bypass

**PARTIALLY IMPLEMENTED.** Evidence: Every durable simulated entry and actual fill passes the gateway; missing service identity, changed scope, signature tamper/replay and absent allocation refuse. Independent fixed-code monitoring runs separately.

A broker-capable independently secured executor, separate signing identities and external approval/capability checks are NOT IMPLEMENTED.

### A49 — Identity, RBAC, MFA, sessions, CSRF, rates and authenticated streams

**PARTIALLY IMPLEMENTED.** Existing owner bootstrap, Argon2id, TOTP/recovery/replay, sessions,
CSRF/RBAC/rates remain. Phase6 adds bounded AI-only SSE/wait with rechecked revocation and released
identity locks. Previous local automated acceptance is owner-reported; new managed browser execution
is blocked by the localhost-origin restriction. Public deployment security is not accepted.

### A50 — Append-only audit, ordered events and causal decision replay

**PARTIALLY IMPLEMENTED.** Source: §3–4, §10, §15. Evidence: Durable ordered audit uses runtime append-only permissions/triggers and HMAC chain/head verification with UTC/actor/correlation/before-after. Native tamper/rollback/concurrency/restart tests pass.

Stored research signal/decision/journal/fill replay is implemented; external anchoring, full retention service and verified off-host restore remain missing. Host/DB admins holding the key remain trusted.

### A51 — Typed modular monolith, OpenAPI, generated TS and full domain models

**PARTIALLY IMPLEMENTED.** Typed modular APIs, scoped repositories, immutable versions and generated
OpenAPI/TypeScript now include Phase6 question/proposal/critique/inert-code/metadata schemas and nine
AI lifecycle tables. Dataset, execution/journal, risk/reservation and research/experiment models remain.
Paper/live lifecycle models and autonomous agents remain future scope.

### A52 — PostgreSQL/Alembic, Redis, MinIO and runnable local containers

**FULLY FUNCTIONAL.** Source: §3, §12 phase 0. Evidence: Actual local PostgreSQL/Redis/MinIO/API/Web healthy; additive migration applied; runtime DB role separated. Native up/down/up, queue/object/database round trips and restart persistence pass with dynamic loopback binding/TCP checks and scoped cleanup.

This classification covers the runnable local stack. Fresh-machine rebuild, production identities, power-loss recovery and restore remain unverified.

### A53 — Durable jobs, retries, orchestration, quotas and crash recovery

**PARTIALLY IMPLEMENTED.** Fixed ingestion/research jobs retain durable claims, immutable inputs,
cancellation and crash tests. Phase6 adds separate AI SQL/Redis identities, quotas, bounded retries,
lease fencing and UNKNOWN after uncertain dispatch; actual worker SIGKILL does not repeat inference.
No autonomous research graph or generated-code executor is implemented.

### A54 — Private Ollama gateway, exact model digests and provider portability

**MISSING.** Source: §2–3, §9, §13. Evidence: Planned Ollama status only.

Implement authenticated private gateway, pinned models/prompts/runtime and schema/tool behavior evals.

### A55 — GPU allocation, sequential model loading and enforceable cost budgets

**PARTIALLY IMPLEMENTED.** Phase6 enforces at most two global inference slots, context/output/time/
byte/request quotas and optional cost estimates from actual usage plus configured rates. GPU/VRAM,
monthly monetary enforcement, model unloading/scheduling and real GPU cost telemetry are NOT VERIFIED
or NOT IMPLEMENTED; unknown remains unknown. No paid infrastructure was started.

### A56 — Complete Romanian dashboard, labs, execution/replay/settings and mobile UX

**PARTIALLY IMPLEMENTED.** Five-destination Romanian UX preserves real research, data, broker
observation and risk controls. Phase6 adds AI question/registry/role/status/structured result/critic/
cancel/privacy views under Testează and Setări. Previous Phases0–5.5 automated acceptance is
OWNER_REPORTED_PASS; current22 desktop/mobile cases collect but are not executed here. Manual
accessibility, rendered AI and visual review remain open. Paper/live labs remain absent.

### A57 — Telegram/email incidents and authenticated emergency commands

**PARTIALLY IMPLEMENTED.** Evidence: Authenticated owner-MFA idempotent emergency commands and durable risk incidents are implemented/native-tested.

Telegram/email delivery and notification credentials/receipt tests are NOT IMPLEMENTED; no messages sent.

### A58 — JSON logs, tracing, metrics, incidents and cost observability

**PARTIALLY IMPLEMENTED.** Sanitized logs/readiness, ordered governance audit and risk incidents
remain. AI adds immutable events/provenance, measured latency, provider-reported usage and explicitly
unknown cost/GPU fields. No general tracing/metrics pipeline, billing service or notification delivery.
Real-model metrics and deployed GPU monitoring remain unverified.

### A59 — Cloud/local deployment, private channels, backups and restore

**PARTIALLY IMPLEMENTED.** Phase6 adds whitelist worker/proxy images, internal-network Compose
overlay, scoped secrets/queue, private TLS/SSH portability guide and private pre-migration local backup.
Image/configuration/native TLS and running-container/queue-restart checks pass. Initial startup
failures were fixed; private local AI services are running with no model. Vast/remote deployment, full live firewall and off-host encrypted restore remain unverified. No paid
host was provisioned. See AI_DEPLOYMENT_GUIDE.md.

### A60 — Release gates, property/fault/integration/E2E/security tests and documentation

**PARTIALLY IMPLEMENTED.** Phase6 portable/frontend/contracts, actual isolated service regressions,
strict smoke, source secret scan and repository checks pass.22 Playwright cases collect; execution is
BLOCKED by managed localhost-origin permissions. Owner-reported earlier acceptance is retained
separately. Real Ollama, remote CI/SBOM/vulnerability/load and off-host
restore acceptance remain open. Exact commands/exits: PHASE6_COMPLETION_REPORT.md.
