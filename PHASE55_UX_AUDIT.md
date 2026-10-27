# Phase 5.5A — UX audit

Date: 2026-10-27. **AUDIT AND DESIGN ONLY. No application implementation or Phase 6.**
Companion decisions: [information architecture](PHASE55_INFORMATION_ARCHITECTURE.md),
[screen blueprint](PHASE55_UX_BLUEPRINT.md), [design system](PHASE55_DESIGN_SYSTEM.md),
[Romanian copy](PHASE55_UX_COPY.md), [implementation sequence](PHASE55_IMPLEMENTATION_PLAN.md).

## Evidence, scope and limits

The owner now reports Phases 0–5 locally validated. Record this as OWNER_REPORTED_PASS for the
starting product; no new command logs accompanied this statement. Earlier reports retain their dated
agent failures, including the corrected exact-label defect. They are historical evidence, not a reason
to disregard the owner's latest report. This audit does not certify current rendered acceptance.

Reviewed: docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md, IMPLEMENTATION_STATUS.md, Phase0–5 completion
reports and linked acceptance evidence; App, Management, MarketData, BrokerCenter, RiskCenter,
RiskBanner, StrategyLab, CSS, both locale files, API clients/contracts, API route handlers, nginx/Vite
routing and all six Playwright spec files plus risk fixtures/workflows/configuration.

Evidence classes used below:
- SOURCE: directly inspectable implementation, not a screenshot or a user-study finding.
- HISTORICAL: supplied artifacts and recorded command outcomes in Phase0–5 reports.
- OWNER_REPORTED: the owner's latest local validation statement.
- PROPOSED: a design decision requiring separate implementation and acceptance.
- NOT VISUALLY VALIDATED: current layout, keyboard, screen-reader and mobile behavior in this audit.

The browser tool selected the local application but denied opening http://127.0.0.1:5173 because a
saved permission/managed origin gate denied access. No alternate browser, raw automation or permission
bypass was attempted. Consequently **no current desktop/mobile screenshots or rendered interactions
were inspected**. Responsive findings are source risks, not measured visual defects. There was no user
research; comprehension and effort judgments are expert hypotheses to validate later.

The optional [YouTube reference](https://www.youtube.com/watch?v=NbOJ8_1Xij8) could not be fetched
(online fetch throttled). No transcript, workflow, visual style or interaction is attributed to it.
The proposed workflow comes from this product's requirements and actual implemented contracts.

Read-only repository baseline:1,008 existing selected files were hashed before the audit. Only the six
requested PHASE55 documents may be added. Verification and final hash comparison are recorded at the
end. No broker credentials, real orders, data mutation, deployment or app-code refactor is in scope.

## Executive diagnosis

The product exposes its module structure more clearly than its user tasks. App.tsx has nine primary
navigation buttons plus three planned-feature buttons; authenticated Management adds nine more tabs.
There are useful safety boundaries, real persistence and honest source labels, but a person must
understand their relationships before completing a simple test. The redesign should reduce navigation
choices, not remove functionality or authority checks.

Most urgent: distinguish descriptive metadata from enforced risk, make safety reachable independently
of public overview loading, and explain why a test cannot start. Next: replace technical setup chains
and JSON-first results with guided setup, plain-language outcomes and inspectable evidence. Visual
polish follows these decisions rather than concealing them.

## Existing screen and action inventory

IDs S01–S42 are audit units: some are complete screens, others are panels/flows embedded in a screen.
They are not42 existing URL routes. All currently run beneath the SPA root `/` with local React page/
tab state. Each ID has a destination in the IA document. Every item below is SOURCE unless marked.
Mobile/accessibility notes inherit the cross-cutting checks in S42; no rendered pass is implied.

### Shell and public pages — App.tsx, locale.ts, api.ts, schema.ts

**S01 — Shell/navigation/theme.** Purpose: switch modules, refresh status and choose light/dark.
Friction: nine peers, three future links and duplicate management destinations; navigation loses its
meaning on reload/Back because it is state-only. Feedback: selected item exists, but no durable page
address. Mobile: off-canvas menu has no explicit Escape/focus containment/return implementation.
Safety: simulation badge and safety entry must survive consolidation. Simplify to five destinations,
real URLs, one account context and a persistent safety strip; keep technical links in Settings.

**S02 — Home/overview.** Purpose: public readiness, reference capital, research concept and instruments.
Friction: decorative hero, roadmap CTA and static example metrics outrank useful next actions; static
“no experiments” presentation is not the authenticated research registry. “Checkpoint02” and locked
Backtesting conflict with Phase5. Mobile: many small7–12px labels in CSS; reading burden is a source
risk. Safety: example capital is not a broker balance; service health is not trading permission.
Replace with real task/readiness/result summaries, preserving explicit unknown and synthetic states.

**S03 — Infrastructure/service search.** Purpose: direct service health and planned integrations.
Friction: API/PostgreSQL/Redis/storage and engineering startup commands dominate ordinary use.
Feedback: stale/outage handling and filtering are useful; no healthy count should certify job capacity.
Mobile: service details compete in rows. Safety: preserve dependency uncertainty. Move full diagnostics
to Settings; Home receives a short capability-specific status with last verification time.

**S04 — Safety/governance explanation.** Purpose: explain DENY_ALL, MFA, sandbox absence and policies.
Friction: engineering vocabulary and static “never verified” wording can contradict verified account
policies elsewhere. Mobile: repeated rule cards are long. Safety: no external execution or hostile-code
runner exists. Keep a clear mode explanation under Accounts & Safety, linked policy-specific status and
advanced trust-boundary documentation; never turn a static explanation into an authorization badge.

**S05 — Roadmap/future links.** Purpose: planned/current stages and acceptance descriptions.
Friction: multiple phases labelled CURRENT and stale future Backtesting links compete with available
work. Feedback: no task can be completed here. Safety: future AI/paper/live must not appear active.
Move to Settings → About → Development; label delivered, owner-validated, unverified integration and
planned states separately. No fictional agents, activity or financial outcomes.

### Identity and administration — Management.tsx, management-locale.ts

**S06 — Login/session loading.** Purpose: password then MFA; session expiry/revocation.
Friction: login is inside administration; navigating between keyed Management instances rechecks and
can discard local work. Feedback: errors exist, destination/progress recovery is weak. Mobile/access:
shared password Field sets autocomplete off; no contextual credential-purpose tokens. Safety: keep
FULL-session, CSRF and ownership enforcement. Use one auth provider, return destination and accessible
password-manager/paste support; no auto-resubmission of a sensitive action after reauthentication.

**S07 — Owner bootstrap.** Purpose: one-time owner setup with private bootstrap code and long password.
Friction: ordinary first-use work and technical server provisioning share a page. Feedback: unavailable
setup can disable the button without a task-level explanation. Mobile: long secrets/manual setup.
Safety: never auto-read private bootstrap material or open public signup. Separate administrator setup
from ordinary sign-in; explain where the owner obtains the private code and why setup may be unavailable.

**S08 — MFA enrollment/recovery-code saving.** Purpose: enroll TOTP and retain one-use recovery codes.
Friction: manual secret entry; provisioning URI is returned but QR presentation is absent. Feedback:
“Am salvat codurile” clears local recovery display. Mobile/access: seed copying/manual transcription is
burdensome. Safety: no screenshots/traces of secrets, no remote QR generation or automatic credential
storage. Offer local QR plus manual fallback, copy/download only by explicit user action and a clear
saved-codes checkpoint; retain backend enrollment and recovery semantics.

**S09 — MFA verification/recovery.** Purpose: complete login or use a recovery code.
Friction: raw MFA terminology and transition between modes needs explanation. Feedback: errors are
not mapped to next steps. Mobile: numeric OTP assistance differs from alphanumeric recovery input.
Safety: no bypass or invented backup code. Use “Cod din aplicația de autentificare”, allow paste,
explain expiry/one-use recovery and keep the correct input mode for each mode.

**S10 — Account list/search/create/edit.** Purpose: owned simulated accounts, capital/currency and
optional program. Friction: generic record cards expose revisions and source metadata without an
account-purpose summary. Feedback: PostgreSQL success copy explains storage rather than outcome;
VIEWER disabled edit lacks a reason. Mobile: stacked metadata is long. Safety: capital is declared
simulation capital, never a broker balance. Offer clear account summaries, role explanations and
version/conflict recovery; preserve ownership, source, program links and archive semantics.

**S11 — Legacy descriptive risk-profile records.** Purpose: editable governance metadata.
Friction: “Profiluri de risc” resembles the enforced independent Risk Center. Generic disclaimer says
limits are not applied, while other modules do apply verified limits. Feedback: unclear effect of save.
Mobile: duplicate forms. Safety: this ambiguity can cause misplaced trust. Retain records under
Advanced → Descriptive records, explicitly “not applied”; direct ordinary users to enforced versions.
Do not migrate, attest or enforce these records automatically.

**S12 — Firm/program/source-policy records and attestation.** Purpose: create firm/program metadata,
version source documents and manually attest exact account/program/date scope. Friction: digests,
source URLs and dates precede a plain description of the rule; separate RiskPolicy attestation has a
different meaning. Feedback: verification impact is easy to confuse. Mobile: long hashes/JSON.
Safety: brands are not permissions. Present document review and effective account limits as distinct,
linked steps; keep every source hash, revision, expiry, scope and acknowledgement inspectable.

**S13 — Security/reauth/password/session revocation.** Purpose: recent MFA, password change and session
revocation. Friction: several sensitive forms at once; reconfirmation is remote from the action needing
it. Feedback: consequences/session invalidation need a review step. Mobile: password fields and errors
need keyboard/scroll checks. Safety: retain credential/session rotation and recent-MFA requirement.
Provide contextual reauth plus a dedicated Security page; confirm scope and never persist secrets.

**S14 — Owner user management.** Purpose: create OPERATOR/VIEWER, suspend/reactivate and change roles.
Friction: broad admin actions share Security with personal authentication. Feedback: role change and
suspension have immediate effects without a separate consequence summary in the source. Mobile:
multiple actions per card. Safety: no permission expansion or cross-owner access through UI design.
Separate Users; show permissions and affected sessions before owner-confirmed changes.

**S15 — Immutable audit timeline/integrity check.** Purpose: ordered events, actor/MFA, correlation and
HMAC verification with pagination. Friction: raw event enums/IDs; cryptographic integrity is hard to
interpret. Feedback: no plain event narrative/filter context in the screen. Mobile: long identifiers.
Safety: no deletion/editing, no claim of protection against a trusted host holding the key. Add readable
event summaries with exact original payload/IDs in details; keep integrity state and actor/account scope.

### Data — MarketData.tsx and apps/api/market/

**S16 — Dataset catalog/filter/pagination.** Purpose: owned imports, instrument filtering and status.
Friction: technical statuses and version numbers lead rather than available markets/periods.
Feedback: “no data” needs different actions for empty, filtered-empty and forbidden/sealed data.
Mobile: long dataset cards. Safety: VALID and accessible ownership are distinct prerequisites.
Group by market/time range; show source/quality/freshness and an explicit next setup action.

**S17 — Point-in-time sample/price chart/table.** Purpose: inspect available rows at a decision time.
Friction: UTC/decision-time inputs before a plain preview. Source chart spaces points by row index,
which can visually conceal irregular time gaps; axis/unit labeling is limited. Feedback: truncated
samples are disclosed but not front-and-center. Safety: never show future/unavailable prices or imply
full coverage from a sample. Use time-based axes, explicit gaps, sample scope and accessible exact rows.

**S18 — Quality/provenance/version comparison.** Purpose: quality report, immutable hashes, source and
version diff. Friction: JSON-first presentation and a long manifest hash as the main explanation.
Feedback: user must discover which issue blocks research. Mobile/access: long pre blocks require local
scrolling. Safety: retain validity, exact hashes/source/availability and sealed-window restrictions.
Lead with “usable for this test / needs review / blocked”, actionable quality reasons, then full evidence.

**S19 — Import jobs/cancellation.** Purpose: durable import state, error/cancel and published data.
Friction: jobs are mixed with provider/import setup. Feedback: status names lack outcome/next-step
explanations; cancellation is not the same as confirmed cancellation. Mobile: history is a long stack.
Safety: partial objects must not appear as accepted datasets. Provide a task detail with real progress,
explicit cancellation request/confirmation and a link to the published version only on completion.

**S20 — CSV/Parquet/ECB import.** Purpose: import entitled history or daily ECB reference data.
Friction: provider/account/instrument/source symbol/type/timeframe/IANA/provenance/calendar/schema fields
are upfront; source declares weekday sessions explicitly. Feedback: generic HTTP import errors do not
identify a column or timezone issue. Mobile: a long single form. Safety: no inferred timestamps,
calendar, bid/ask, entitlement or tradability; ECB reference rates are not execution ticks.
Use a guided import and reviewed source setup once; keep unresolved required facts blocking.

**S21 — Provider/instrument/venue registration.** Purpose: establish owned metadata and permitted
provider adapter, rights reference and attribution. Friction: ordinary importers must understand the
technical dependency chain. Feedback: source configured is not history available. Mobile: competing
forms. Safety: preserve entitlement acknowledgement and exact symbol/calendar mapping. Move reusable
configuration to Settings → Sources/Catalog; contextually link missing setup from the import flow.

### Connections and manual simulator — BrokerCenter.tsx

**S22 — Connection identities/status/observations.** Purpose: register simulator or read-only demo
connection and inspect signed observations. Friction: public-key/server vocabulary shares default
space with ordinary account inspection. Feedback: registration versus verified connectivity is easy
to confuse. Mobile: reported symbols/orders are dense. Safety: no broker passwords/OAuth tokens in
this app; real connectivity remains evidence-dependent. Separate identity, observed state and execution
permission; use a status checklist and advanced connector setup without a misleading “connected” label.

**S23 — Signed snapshot import/demo observation detail.** Purpose: accept signed connector evidence
and inspect symbols/quotes/reported orders/positions. Friction: manual JSON/signature troubleshooting.
Feedback: verification, staleness and incomplete snapshots need distinct explanations. Mobile: raw
payloads. Safety: no signature bypass; a valid observation never authorizes an order. Keep an advanced
read-only-evidence workflow; label demo observations separately from simulated fills and unknown data.

**S24 — Manual synthetic scenario/template creation.** Purpose: configure immutable symbol/cost/
liquidity/session assumptions and optionally bind VALID ticks. Friction: extensive contract parameters
are a prerequisite for a first research test. Feedback: assumed versus independently observed facts
need a compact review. Mobile: long form. Safety: no invented margin/tick/payoff or automatic approval.
Provide an owner-reviewed reusable setup flow; a wizard may select an existing reviewed template, not
fabricate a broker specification. Keep all manual scenario capabilities in Advanced simulator tools.

**S25 — Synthetic ticks/admitted tick replay.** Purpose: advance the manual scenario clock from
explicit quotes or VALID replay. Friction: sequence/clock/idempotency concepts exposed immediately.
Feedback: “new quote” is not market connectivity. Mobile: time fields and table require reflow checks.
Safety: preserve monotonic clock, point-in-time decisions and finite liquidity. Keep in Advanced;
show a read-only timeline and exact source/mode before manual clock actions.

**S26 — Simulated order lifecycle/fault controls.** Purpose: submit/retry/cancel/modify/close simulated
orders with SL/TP, pending/OCO/fault behavior. Friction: debugging controls compete with real research;
“send order” can sound like broker execution. Feedback: UNKNOWN/partial is not a final fill. Mobile:
many nearby mutation buttons. Safety: actual Risk Gateway, no direct research-journal mutation,
idempotency and external DENY_ALL. Keep full controls in an explicitly manual SIMULATED tool with
separate inspection, fault injection and consequence reviews; never expose them as normal trading.

**S27 — Manual journal/positions/reconciliation.** Purpose: inspect durable events, fills, positions
and reconcile synthetic truth. Friction: JSON before a causal explanation. Feedback: match a proposal,
risk decision and actual fill rather than equating ALLOW with execution. Mobile: dense records.
Safety: immutable journal and unresolved exposure remain visible. Read-only timeline belongs in Results;
mutating manual reconciliation links back to the correctly scoped Advanced simulator.

### Safety — RiskBanner.tsx, RiskCenter.tsx, apps/api/risk/

**S28 — Global/account safety status.** Purpose: configured/headroom/monitor/stop state across accounts.
Friction: one failing Promise.all request can withhold useful per-account status; initial authentication
failure can hide the banner. App mounts all authenticated tools only when overview data exists.
Feedback: no overview data must not mean “safe” or “nothing running”. Mobile: wrap state and action
without hiding STOP. Keep authenticated safety independently reachable; display unknown explicitly.
The current account read is limited to100 records: any future all-account summary must handle paging
or explicitly name its partial scope; an unlisted account cannot be assumed safe or nonexistent.

**S29 — Enforced scoped profile/version history.** Purpose: account/strategy/instrument/asset/firm/
program limits and immutable revisions. Friction: raw percentages/scopes and JSON history precede
monetary meaning. Feedback: no estimate should replace exact gateway sizing. Mobile: many controls.
Safety: all restrictive scopes remain applied; internal defaults require owner review. Use a monetary
preview with basis/currency/reset explanation and an expandable exact scope/version summary.

**S30 — Applicable risk-policy creation/attestation.** Purpose: exact personal/prop policy, automation,
calendar/session/symbol restrictions and owner verification. Friction: large rule set and source review
mixed with experimentation. Feedback: verified source is not paper/live approval; new policy can
invalidate an old experiment scope. Mobile: confirmations are long. Keep a guided exact-scope review,
visible expiry/change impact, explicit permission checks and immutable evidence in Advanced details.

**S31 — Financial/FX/calendar execution context.** Purpose: explicit payoff, tick value, margin,
funding/group/style, observed/valid dates and evidence files. Friction: expert financial assumptions
are required before ordinary testing. Feedback: unknown is frequently represented by technical errors.
Mobile: JSON uploads/long strings. Safety: source assertions are not broker-certified facts; inverse/
unverified contracts refuse. Keep expert setup, plain status and versioned owner review; never infer
missing facts merely to make a beginner flow shorter.

**S32 — What-if sizing/decision history.** Purpose: ask the actual gateway about a hypothetical proposal
and inspect ALLOW/DENY/INDETERMINATE with evidence. Friction: geometry/volume and raw result objects.
Feedback: ALLOW can be mistaken for a submitted order. Mobile: cards/tables need a readable hierarchy.
Safety: no authorization or order is created by what-if. Use monetary examples and “allowed by these
simulation limits” wording; retain complete calculation/evidence and uncertainty reasons.

**S33 — Risk already allocated/incidents.** Purpose: durable open/pending/UNKNOWN risk and incidents.
Friction: “reservation” and raw ledger objects do not explain money unavailable to another proposal.
Feedback: explain retained risk after an ambiguous state; no optimistic release. Mobile: dense IDs.
Safety: unresolved exposure, group allocations and incidents cannot be hidden in Advanced only.
Show a concise allocation breakdown and a clear incident action, with exact ledger details available.

**S34 — MONITOR/STOP/CLEAR/FLATTEN.** Purpose: poll, persistently stop new entries, reviewed clear,
and separate simulated liquidation. Friction: one enum select plus one generic apply button groups
very different consequences. Feedback: incomplete closure must name remaining exposure. Mobile:
accidental selection/confirmation risk. Safety: per-account scope, fresh owner MFA, revisions,
acknowledgements and actual confirmation. Give STOP, review/clear and simulated close separate actions;
no global STOP_ALL endpoint, offline success, automatic clear or implied real-broker liquidation.

### Research and results — StrategyLab.tsx, apps/api/research/

**S35 — Reviewed strategy library.** Purpose: select eight fixed baselines and inspect immutable
version/parameter contracts. Friction: IDs and JSON contracts before plain entry/exit descriptions.
Feedback: experimental benchmark is not an endorsed profitable strategy. Mobile: long pre blocks.
Safety: no generated code/ML/LLM judges. Present a short behavior/risk description, supported data and
version; preserve exact definition and reviewed source digest in details.

**S36 — Backtest configuration/sweeps/portfolios.** Purpose: pin data/context, chronology, costs,
parameters, random controls and quotas. Friction: a simulator template plus dozens of fields and
advanced JSON before a first test; imported JSON is processed after basic template work. Feedback:
preconditions are not a guided checklist. Mobile: long forms and lost state on navigation. Safety:
reviewed policy, immutable pins, sample/row/time limits, causal splits and explicit assumptions.
Use Market → Strategy → Period → Reviewed setup → Review → Start; retain every advanced parameter.

**S37 — Experiment history/progress/cancel.** Purpose: submit idempotent durable jobs and inspect
state/attempt/progress/error. Friction: all runs stack on the same configuration page; backend job
state is not a trustworthy ETA or worker heartbeat. Feedback: cancellation request needs a distinct
acknowledgement while waiting for CANCELLED. Mobile: verbose UUID actions. Keep stable task URLs,
readable activity/history, safe refresh/resume and actual attempts; never fabricate progress.

**S38 — Stored result/equity/metrics.** Purpose: read immutable account marks and summary metrics.
Friction: approximate SVG with minimal axis labels and a JSON metrics dump; no plain “what this means”
layer. Feedback: null ratios, costs/sample sufficiency and uncertainty need first-class explanation.
Mobile: every metric has similar prominence. Safety: exact monetary strings, source/mode, actual costs,
phase and insufficient data must lead. Use net simulated change, peak-to-trough decline, trade count
and limitations before advanced ratios; never manufacture a success/confidence score.

**S39 — Trades/replay/OOS/walk-forward/provenance.** Purpose: page through stored causal events,
folds/exposure/signals and immutable source manifests. Friction: section selector plus JSON; same
“details” output also hosts provenance and comparisons. Feedback: selected context and sampling are
hard to retain. Mobile: narrow raw-data panes. Safety: no reconstructed fills, leaked holdout rows or
new metrics from chart samples. Separate read-only result tabs with plain explanations and full exact
records/export; retain genuine fold/attempt/cost/source boundaries.

**S40 — Strategy/run comparison.** Purpose: compare completed runs under matched conditions.
Friction: two UUID dropdowns and a later409 rather than an explanation of matching eligibility.
Feedback: no side-by-side plain differences. Mobile: comparative meaning cannot rely on a wide table.
Safety: same data/chronology/risk/cost/software conditions; ML/LLM unimplemented. Explain incompatible
pairs and show stored outcomes/limits; strategy/parameter differences are allowed only as the API permits.

**S41 — Final window sealing/release.** Purpose: owner-authorized seal and one frozen final experiment.
Friction: placed beside ordinary research; raw JSON and technical “holdout” language. Feedback:
restriction/one-use consequences need a dedicated review. Mobile: long acknowledgements.
Safety: prior exposure UNKNOWN, ordinary reads/aliases blocked, exact frozen scope, recent MFA,
one release and immutable audit. Isolate in a deliberate advanced flow; never hide the consequences
or call existing data untouched. No automatic resealing, tuning or exposure of protected contents.

**S42 — Responsive/themes/accessibility across every unit.** Purpose: same capability across viewport,
input method and theme. Existing strengths: skip link, explicit select labels, focus rules, source
badges, reduced-motion CSS, wrapping grids and local table scroll. Risks:7–12px text, missing explicit
mobile menu focus management, no chart value axes, duplicated Field/Select components, disabled
reasons absent, and --border used twice without a definition (only --line is declared). These are
source findings, not a WCAG failure certificate. Consolidate tokens/controls; manually validate both
themes, keyboard/VoiceOver, zoom and safe-area layouts before any conformance claim.

## API-only functionality is not an existing screen

Governance exposes13 record kinds: firms, programs, venues, instruments, accounts, brokers,
risk-profiles, policies, strategies, strategy-versions, experiments, approvals and incidents.
Some appear only as related selectors or API metadata, not dedicated editable UI pages. In particular,
generic strategy/version/experiment/approval metadata is not the Phase5 trusted strategy/experiment
registry and never grants execution authority. Preserve all endpoints and authorization. The IA gives
an Advanced registry/API-contract access path; do not claim these pages already exist.
The DSR endpoint is another advanced API capability, not a currently complete statistical UI form.

## Journey assessment and dependency chains

- J01 First use: administrator bootstrap → owner/password → TOTP → recovery saving → owned account.
  Current: secure but technical; new journey explains each step and preserves MFA, not fewer factors.
- J02 First historical test: account → instrument/venue/provider → VALID data → simulator contract/cost
  template → risk context → verified applicable automation policy/profile → StrategyLab plan → worker.
  Current: weak discoverability between modules. New wizard surfaces this as a readiness checklist;
  expert configuration is once per reviewed version, not silently removed.
- J03 Repeat test: choose existing admitted setup → review period/split/costs → idempotent submit →
  actual job → immutable result. Current: good backend boundaries, overloaded form and little saved context.
- J04 Understand/compare: completed stored result → plain outcome/limitations → folds/trades/costs →
  matched comparison. Current: JSON-first. New flow keeps uncertainty and the server matching gate.
- J05 Data import: rights/source → mapping/timezone/calendar review → import job → quality → version.
  Current: expert-first, generic errors. New flow never invents unavailable timestamps or sessions.
- J06 Risk/incident: select account → inspect uncertainty/allocated money → STOP or separately reviewed
  FLATTEN/CLEAR → actual acknowledgement → audit. Current: disparate entries and generic action select.
- J07 Failure/recovery: distinguish auth, invalid data, risk refusal, dependency outage, cancellation and
  failed job. Current: HTTP strings/raw codes. New flow states what/impact/next action, with safe diagnostics.
- J08 Mobile/read-only use: overview → authenticate → inspect owned results/safety → allowed action.
  Current: numerous wrapped tabs/forms; VIEWER reasons and menu/focus need manual verification.
- J09 Final evaluation: intentional owner-only entry → seal consequences → frozen scope/MFA → one release.
  Current: too close to ordinary test form. New flow retains restricted custody and UNKNOWN prior exposure.

All journeys require a clear purpose, one task-level primary action, eligibility explanation, separate
loading/empty/filtered-empty/error/success states, safe draft handling and exact source/mode labels.
S01–S42 identify where those requirements are weak today; none is deemed unnecessary merely for being technical.

## Prioritized backlog — impact and relative effort

P0 = safety comprehension/reachability; P1 = core task success and accessibility; P2 = consistency/polish.
S/M/L = small/local, cross-component, cross-module effort; these are planning estimates, not measured days.

- U01 P0/M: overview-dependent auth/safety mounting (S01,S28). Decouple protected shell and safety queries;
  acceptance: overview fails while reachable authenticated risk can still be inspected/STOP requested.
- U02 P0/M: descriptive versus enforced risk/policy ambiguity (S11,S12,S29,S30). Separate labels and
  link versions; acceptance: a saved descriptive record never appears as an applied limit or permission.
- U03 P0/M: combined STOP/CLEAR/FLATTEN selector (S34). Separate scope/consequence reviews and outcomes.
- U04 P0/M: mode/source/custody confusion (S02,S22,S38,S41). Persist independent data and execution labels.
- U05 P0/M: safety scope/age can be ambiguous (S03,S28): limited account read and monitor freshness
  checked on render, alongside separate service health. Show exact scope, age and unknown state;
  never let service availability imply risk permission.
- U06 P1/L: first-test prerequisite chain (S20,S24,S31,S36). Reviewed reusable setup and six-step wizard.
- U07 P1/M: no task URLs/Back/reload/resume (S01,S37,S39). Typed routes and safe draft/context handling.
- U08 P1/M: metrics/replay/provenance JSON-first (S18,S38,S39). Plain summaries plus exact advanced views.
- U09 P1/M: unclear cancellation/error recovery (S19,S37). Acknowledge request, await actual final status.
- U10 P1/M: unrelated API failure can block whole panel (S28,S36). Isolate read states, preserve unknowns.
- U11 P1/M: importer needs schema/provenance expertise (S20,S21). Guided mapping and once-only source review.
- U12 P1/M: matched-comparison refusal discovered late (S40). Eligibility explanation; server remains final.
- U13 P1/S: stale checkpoint/planned labels/static empty state (S02,S05). Account-aware real summaries,
  “not configured” versus “not implemented”; no claims about current AI/paper/live activity.
- U14 P1/M: errors lack field/action context (all forms). Allowlisted explanation plus correlation details;
  no raw exceptions or secrets, no blind retry of an ambiguous mutation.
- U15 P1/M: settings/catalog dependencies hard to find (S12,S21,S24). Contextual setup links and return path.
- U16 P1/M: final release beside routine tests (S41). Separate owner-only review, no accidental consumption.
- U17 P1/M: chart semantics/axes/gaps and sampled-value interpretation (S17,S38). Time/currency labels,
  exact data alternative and explicit sampling; keep authoritative stored drawdown.
- U18 P1/M: tiny typography and mobile control density (S42).16px body,44px design targets, measured reflow.
- U19 P1/M: menu/dialog keyboard/focus behavior (S01,S13,S34). Semantic focus/escape/return and screen-reader QA.
- U20 P2/S: duplicate primitive styling/undefined border token (S42). One token and component vocabulary.
- U21 P1/M: MFA onboarding/password-manager assistance (S06–S09). Local QR/manual fallback, paste, correct tokens.
- U22 P2/M: disconnected locale/raw enums and ID-heavy actions (all). Copy keys, proper nouns and exact diagnostics.
- U23 P1/M: disabled controls give no reason (all). Persistent eligibility text and allowed next action.
- U24 P2/M: sanitized visual baselines are absent; adding blanket capture would expose auth-secret
  states. Preserve current capture restrictions; use dedicated non-secret fixtures, both themes and
  manual assistive-tech review.

## Validation and non-changes

During this audit, make check exited0:208 Python and16 frontend unit tests, lint/type/build;77 service/
infrastructure cases deselected, not counted as passed. make smoke-demo exited0: readiness200 and
external-order refusal. Outputs: .cache/phase55/make-check.txt and smoke-demo.txt. These are regression/
readiness checks, **not UX, browser or WCAG acceptance**. No integration/E2E rerun or browser bypass.
Existing Playwright has16 cases across six spec files and desktop/Chromium-mobile projects; mobile
emulation is not proof of real iOS Safari/VoiceOver acceptance. Owner validation is separate evidence.

Final document/source verification: `python3 .cache/phase55/verify_documents.py` exited0. All1,008
pre-existing selected files match their starting SHA-256 hashes; the six requested Markdown files
are the only additions to the Git-selected file set. Existing dirty/untracked work from earlier
phases was preserved. The check confirms42/42 inventory-to-route mappings,10 desktop/mobile
wireframe pairs,11 sequential implementation steps, balanced fences, local document links and list
markers. Output: .cache/phase55/document-verification.json. This checks document completeness and
non-modification, not whether proposed interfaces work. An initial checker matched the shared Desktop
preamble as an extra wireframe; its matcher was corrected to count exact section labels and rerun.

Audit-stage outcome: **six design deliverables complete; implementation NOT STARTED; rendered/browser
and assistive-tech validation BLOCKED in this environment; optional video UNAVAILABLE**. No Phase6.
