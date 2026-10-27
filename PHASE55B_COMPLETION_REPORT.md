# Phase 5.5B — UI/UX implementation and acceptance report

Date: 2026-10-27. **Implementation delivered; overall acceptance BLOCKED / NOT COMPLETE.**
Latest gate: 2026-10-28 — [mobile visual reference review](#mobile-visual-reference-review--2026-10-28).
The redesigned source builds and native integration passes. The managed browser denies the local
origin, so no current rendered, desktop/mobile E2E, visual-baseline, VoiceOver or WCAG acceptance is
claimed. Phases0–5 remain OWNER_REPORTED_PASS as the starting point; that statement does not prove
acceptance of this redesign. No Phase6 functionality or external execution was introduced.

The later owner-reproduced policy HTTP 503 and its native regression fix are documented in
[Risk policy 503 correction](#risk-policy-503-correction--2026-10-27). Initial acceptance evidence below
is retained; it does not establish browser success after this correction.

The later [visual timestamp-mask correction](#visual-timestamp-mask-correction--2026-10-27)
uses the owner's actual PNGs. Those supplied public screenshots were inspected; the new rendering
has not been browser-validated here. Earlier no-visual-inspection statements describe their dated
agent runs, not the later supplied artifacts.

Read alongside [feature/issue coverage](docs/ux-migration-coverage.md),
[current frontend architecture](docs/FRONTEND_UX.md),
[manual acceptance checklist](docs/PHASE55B_ACCESSIBILITY_CHECKLIST.md) and the approved Phase5.5A
[audit](PHASE55_UX_AUDIT.md), [IA](PHASE55_INFORMATION_ARCHITECTURE.md),
[blueprints](PHASE55_UX_BLUEPRINT.md), [tokens](PHASE55_DESIGN_SYSTEM.md),
[copy](PHASE55_UX_COPY.md), [sequence](PHASE55_IMPLEMENTATION_PLAN.md).

## Protected starting state

Before editing,1014 Git-selected existing files, including uncommitted/untracked Phase0–5 work, were
hashed and archived privately under .cache/phase55b/source-before.tar.gz (mode0600), with a SHA-256
manifest and initial status. No reset, stash, checkout replacement, commit or push was performed.
Only the task's source/docs/contracts/tests were changed. The original Phase5.5A audit remains
unchanged; implementation notes were added to its companion design documents rather than replacing
historical evidence. Financial engine/risk/storage/governance/auth implementation boundaries are
preserved; additive task reads are described below. Final scope verification is in the evidence ledger.

No development volume was deleted, reset or migrated. Native suites used their own random isolated
Compose projects, temporary credentials and actual PostgreSQL/Redis/MinIO. Cleanup logs identify only
those disposable projects. The local API/Web image refresh is separate from browser acceptance; the
container/mount preservation check and readiness result are recorded in the final evidence ledger.

## Changes by requested stage

### A — authentication and safety architecture

- AuthProvider now owns session state above navigation. Authenticated tools and safety are mounted
  independently of getOverview; a public outage cannot withhold their routes.
- Account pagination is read completely within a bounded helper, or explicitly refused. Duplicate/
  changing/incomplete pages do not certify coverage. Per-account failures do not hide other readings.
- Safety distinguishes UNKNOWN, UNAVAILABLE, STALE, stopped and unconfigured; monitor age advances
  independently of successful polling. Last-known stops are retained through read failures. Unknown
  revisions cannot authorize a confirmation. HTTP readiness is not permission or worker health.
- Descriptive governance risk and document-source verification have explicit non-enforcement labels;
  actual immutable Risk Gateway profiles and effective policies remain separate. Nothing is converted.
- STOP_NEW_ENTRIES, reviewed CLEAR_STOP and simulated-only FLATTEN have distinct consequence dialogs,
  account/revision scope and required acknowledgements. Owner/recent-MFA and final gateway checks stay
  on the existing server. MONITOR remains an explicit separate action; no global emergency endpoint.

### B — shell, routes and task context

Five native-link destinations: **Acasă, Testează, Rezultate, Conturi și siguranță, Setări**. The finite
route resolver supports direct URLs, Back/Forward/popstate, reload and protected return to the current
route. Account context is identity-scoped and synchronized with research/safety; old-owner names are
not displayed while a new identity's account read is pending. Unknown routes are explicit, not API
fallbacks. Existing nginx API/health/OpenAPI proxies and SPA fallback were preserved.

Non-sensitive research selections/inputs/review are retained in memory. No secret, arbitrary JSON,
file or acknowledgement is persisted in browser storage. Logout clears drafts. Unknown submissions
retain a frozen request/key rather than generating an optimistic second experiment. The default mobile
navigation is permanently visible; no modal menu is required to reach one of the five destinations.

### C — shared visual/interaction system

Semantic light/dark tokens, compatibility aliases and a defined --border; system theme plus existing
explicit preference; readable body/helper text, consistent field/button/panel geometry,44px controls,
focus and reduced-motion rules. Shared Input/Select, Evidence and native modal consequence patterns
replace repeated primitives. Specialized typed forms remain available; no new design framework,
font service or dependency was installed. Palette/source rules are not WCAG certification.

### D — Home

Home now answers availability, actual work, stored results, attention and next action using separate
public and authenticated reads. It does not aggregate unrelated backtests as wealth, invent capital,
claim AI activity or infer worker availability from a green API. Empty, failed and bounded-page states
are distinct. Infrastructure details and development roadmap moved into Settings.

### E — guided research

Market/data → reviewed strategy → chronology/evaluation → existing reviewed setup → review → explicit
Start. The five form steps retain all advanced controls: strategy parameters/sweeps, portfolio JSON,
EXECUTION/SIGNAL/CONFIRMATION/FX roles, random controls, seeds, costs, walk-forward, purge/embargo and
quotas. Exact accessible names remain explicit; old account/form/region labels were intentionally
renamed in the migrated tests to “Contul testului”, “Configurează testul istoric”, “Testează strategii”.

The wizard reads admitted data, compatible symbol template, existing monetary context, actual ACCOUNT
profile, verified automation policy covering the selected period and current source safety. Missing
facts link to setup instead of being invented or auto-attested. Final API/worker validation still
binds immutable pins/software/policy/risk and performs final financial checks. No general fake preset,
policy relaxation, protected-row preview or generated strategy source was added.

### F — results, comparison and evidence

Stored canonical net change, maximum historical decline and trade count lead, followed by period,
cost assumptions, origin/coverage limitations and statistical uncertainty. Null is not zero; screening
is not risk validation. No profitability badge, guaranteed score or probability-of-profit substitute.

Actual timestamps drive plotted observations, with currency/time axes, sampled-point counts and exact
value tables. Points do not invent interpolated history. The drawdown view is explicitly approximate
and never replaces the engine's stored maximum. Readable stored trade/fill/replay/exposure/fold rows,
exact provenance and server-matched side-by-side comparison remain available. A409 comparison refusal
is explained without forced normalization. Owner-MFA Deflated Sharpe uses the existing endpoint and
explicit independence assumptions, not an inferred certification.

### G — accounts and applied safety

Declared capital is labelled separately from broker balance. Applied limits, actual allocated risk,
hypothetical calculations, stops, source documents and policy versions remain distinct. Account/program/
date-specific attestations and immutable revisions remain accessible. VIEWER/OPERATOR/OWNER roles and
ownership are still enforced by the API. Familiar prop-firm names do not grant permission.

### H — data import and quality

Guided permitted source → instrument/account → file/timestamps → rights/calendar → review → actual
import/quality outcome. Existing format, provenance, timezone, source symbol, immutable revision and
session contracts are retained. Opening/closing minutes are explicitly reviewable. Missing/invalid
moments, symbols, gaps and degraded data are explained without repairing facts. Upload success does
not mean VALID or authentic history; ECB is daily reference-only, never executable bid/ask data.

### I — Settings and advanced tools

Sources, instrument/catalog creation, descriptive records, document review, manual simulator, read-only
observations/journals, financial context, policy evidence, security/MFA, users, audit, diagnostics,
roadmap and all13 API registry kinds retain destinations. API-only operations are labelled API-only.
Manual commands/ticks/replay/OCO/fault/reconcile remain in advanced simulation; internal research
journals remain mutation-prohibited. Result journal routes are read-only. No AI/paper/live controls.

### J — Romanian language and task states

Shared source/phase/job/strategy/error terms and glossary-aligned primary copy. Permanent prerequisites,
role reasons, pending/unknown outcomes and cancellation requests are distinguished from confirmation.
Server errors use an explicit allowlist; arbitrary uppercase bodies and raw exceptions are not echoed.
The previous fabricated15-minute429 timer was removed. No automatic uncertain-write retry was added.

### K — responsive and accessibility work

Source implements responsive columns, permanent mobile navigation/safe areas, skip/heading focus,
label/help semantics, keyboard-scrollable technical evidence, native modal focus/return, validation
opening advanced details and non-color state labels. Existing trace/screenshot/auth-context capture
restrictions remain. Sanitized public Home visual comparisons were added for both viewports/themes,
masking only the public read clock. **No actual baseline or manual observation was manufactured.**
See the manual checklist for320px, zoom, Safari/VoiceOver, real mobile, focus, contrast and all42 units.

## Old → new navigation

- Overview → Acasă; infrastructure → Setări/Diagnostic; governance explanation → About + scoped safety;
  roadmap/future buttons → Setări/Despre/Plan, with implemented/planned distinction.
- Management/accounts → Conturi; descriptive risk records → Conturi/Avansat; document policies/firms/
  programs → Documente și programe; actual profiles/policies/context → scoped account Safety.
- Market → Testează/Date; provider and instrument creation → Setări/Surse and Catalog.
- Broker → account Connections + Advanced manual simulator; inspection journal → Results/Simulations.
- Strategy Lab → guided Testează, Activity/Progress and Results; comparison → Results/Compare;
  sealing/release → separate owner Final Evaluation.
- Security/users/audit → separate Settings destinations. Original tab aliases in test helpers now
  resolve canonical URLs, not invisible legacy controls. All16 original behavior scenarios remain.

The full S01–S42 mapping and every U01–U24 closure status are in docs/ux-migration-coverage.md.
Implemented does not mean a blocked browser gate is closed. U21 retains the approved manual MFA
fallback without an optional local QR renderer. U24 genuine baselines/manual review remains OPEN.

## Minimal backend changes and safety preservation

Only additive task reads were needed: owner-scoped GET market/jobs/{job_id}, market job cancel_requested
and the research job's existing cancel_requested flag. No new table/migration or risk/financial rule.
Generated OpenAPI and TypeScript were regenerated and checked. Real service tests cover lookup,
unknown/unowned404, persisted flag and queue cancellation. Research/execution/storage math is reused.

SIMULATED/DENY_ALL, external real/demo order denial, CSRF, MFA/recent-MFA, RBAC/ownership, deterministic
Decimal gateway checks, profile/policy revisions, unknown reservations, STOP/FLATTEN distinction,
immutable datasets/results/audit, point-in-time access, one-use final holds and no automatic promotion
remain intact. No broker credential, generated-code execution, live switch or Phase6 feature added.
External broker connectivity remains unverified; protocol/simulation tests do not prove service access.

## Initial redesign verification — retained

Machine-readable exact commands, exit codes, timings and log references are collected in
[the evidence ledger](docs/phase55b-evidence/2026-10-27/verification.json). Raw local logs are under
.cache/phase55b/; they are not user-study or screenshot evidence.

- PASSED: make check, current final run: 208 Python + 94 frontend tests; Ruff/format, ESLint/Prettier,
  mypy, TypeScript and production build. 77 service cases deselected here are not counted as passes.
- PASSED: make integration twice: one running-API readiness case and 76 actual isolated cases in each
  pre/post-restart stage, plus strict readiness/execution-denial smoke. Final run includes the new
  cross-owner job lookup assertion. Both disposable projects were cleaned by their own harness.
- PASSED (exit 0): make contracts-check, make smoke-demo, make secret-scan and make repository-check.
- PASSED (exit 0): local API/Web image builds and dependency-free container refreshes. Final API/Web
  health is healthy; read-only API validation returned readiness HTTP 200, exact served OpenAPI parity,
  unauthenticated job-read HTTP 401 and SIMULATED/DENY_ALL with execution flags disabled.
- PRESERVED: PostgreSQL, Redis, MinIO, market-worker, research-worker and risk-monitor retained their
  original container IDs and mounts, all healthy. This establishes resource preservation, not byte-for-byte
  database row equality. The 1,014-file starting manifest found no unexpected existing-file changes;
  51 protected core files remained identical, with all 42 inventory items and 24 issue statuses present.
- COLLECTION ONLY: npm --prefix apps/web run test:e2e -- --list: 20 cases in 8 files, 10 per viewport.
  This preserves 16 old cases and adds 4 UX/visual viewport cases. Collection is not browser success.
- FAILED, FIXED: first make check exited2 on an exhaustive-dependencies lint error in the account read
  effect. It now depends on the stable owner ID; subsequent full checks pass. Intermediate TypeScript
  errors during module extraction/generation were fixed without disabling checks or relaxing assertions.
- BLOCKED: managed browser rejected opening http://127.0.0.1:5173 because the saved origin permission
  denied network egress. No current page/DOM/screenshot was inspected. No alternate browser, raw CDP,
  CLI launch or proxy workaround was attempted. make browser-integration execution is NOT RUN under
  that restriction, with no fabricated process exit code; the ledger records null for this gate.
- NOT RUN: real Safari/iOS/VoiceOver, manual keyboard/zoom/contrast and adult comprehension review;
  visual baseline creation/review; remote CI. No accessibility or complete UX acceptance is asserted.

## Remaining gates and sensible limits

1. On an authorized local host, run focused research, create/review genuine non-secret visual baseline
   candidates, then all 20 desktop/mobile cases without baseline updates. Fix any real failure before
   accepting. The new flows have compiled and collected but remain unexecuted here.
2. Complete the manual accessibility/mobile/comprehension checklist. Token calculations and source
   dimensions do not establish actual contrast, focus, reflow or novice understanding.
3. Optional local QR display remains absent; manual TOTP enrollment remains functional. Do not send
   provisioning secrets to a remote QR service. No new package/framework was added just for this.
4. Advanced JSON/files/acknowledgements are intentionally not persisted. A lost final-release response
   can require owner audit inspection and exact-plan resumption; do not issue a new release to hide
   uncertainty. Current limited lists disclose their scope; no global search/ETA/worker heartbeat,
   general saved-preset entity or arbitrary CSV mapper is falsely offered.
5. Chart drawdown is approximate from displayed samples. Authoritative figures are stored results;
   no new full-resolution statistical series or stronger independent holdout custody was invented.

No external credentials or paid infrastructure are needed for the remaining simulation acceptance.
The development database volumes are not a test reset target. Phase5.5B is **not accepted as complete**
until the browser and manual gates pass. Stop here; no Phase6, live activation, publication or push.

## Owner-local verification commands

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration
# Initial baseline CANDIDATES only; inspect the genuine public PNGs before accepting:
E2E_ONLY_SCENARIO=ux E2E_UPDATE_SNAPSHOTS=1 make browser-integration
# Actual full regression gate, with no selection or baseline rewriting:
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
make check
make integration
make contracts-check
make smoke-demo
make secret-scan
make repository-check
```

These use isolated services and real MFA/data/risk workflows. They must run in an administrator-
authorized environment; do not bypass managed browser permissions. Retain exact output, failures and
baseline/manual review notes. Candidate generation alone cannot satisfy the acceptance gate.


## Risk policy 503 correction — 2026-10-27

**FIXED IN SOURCE; browser acceptance remains BLOCKED / NOT COMPLETE.** This is the owner's actual
backend HTTP 503, not a Chromium launch problem or a missing locator. The supplied on-disk
apps/web/test-results/ux-workflows-independent-s-ef53e-review-and-viewer-isolation-desktop/error-context.md
was inspected. It records expected 201 / received 503 at risk-workflow.ts:77 but has no response body,
request ID, DOM state or retained server log. The previous harness deleted its temporary server log
and disposable database. No original owner response/correlation ID or persisted state is invented.
Sanitized assertion metadata and exact new command records are in
[policy-503 evidence](docs/phase55b-evidence/2026-10-27/policy-503/verification.json).

### Endpoint, cause and reproduced evidence

savedPolicy is the actual authenticated POST /api/v1/risk/accounts/{account_id}/policies from the
RiskCenter policy form. Its body includes PERSONAL/PROP kind, account-linked document ID when
applicable, validated monetary/policy terms, effective/expiry dates, digest and source references.
The fixture creates a personal account, actual simulator and enforced profile through real APIs.
No payload correction, fabricated prop document or policy attestation was needed.

The reproducible defect is an inverted PostgreSQL row-lock order between authenticated requests and
the independent risk monitor:

1. authenticated locks the User row, then owned/account_for locks the trading account.
2. risk_monitor.once previously locked the account in poll before taking any owner lock.
3. A missing/revoked/unverified policy or unverified exposure can cause the monitor to insert an
   incident/ledger record. Its owner foreign key needs a key-share lock on the same User row.
4. The request waits for the account while the monitor waits for the owner. PostgreSQL aborts a
   deadlocked transaction with SQLSTATE 40P01. The existing SQLAlchemyError handler returns 503 and
   rolls back; this is a persistence failure, not a policy validation refusal.

A deterministic native regression used actual disposable PostgreSQL and the restricted runtime
identity, real owner MFA/CSRF, real policy/revocation and actual monitor incident/ledger persistence.
It coordinated on observed PostgreSQL lock contention with events; no arbitrary sleep, mocked
policy response or retry hides the race. Before the fix it reproduced status 503, SQLSTATE 40P01,
body {"detail":"Persistent service unavailable; no change accepted"}, request ID
02366e5f-e29c-4173-9a45-2c20af3f26e4, while the monitor committed. That ID belongs to this native
reproduction, not the owner's unavailable response. After the fix both transactions commit, the
POST returns 201, the new policy persists as UNVERIFIED, stops remain set, and audit verification
passes. This establishes a concrete underlying defect matching the owner failure; the original
owner transaction cannot be retrospectively correlated without its deleted log.

### Small fix and changed files

- scripts/risk_monitor.py: acquire the owner User lock before loading mutable account/control state
  and before poll takes the account lock. This matches existing authenticated owner→account→audit
  ordering. No risk threshold, Decimal calculation, monitor freshness bound or authorization changes.
- apps/api/main.py: preserve 503 and the generic response body, add a fixed X-Error-Category header
  and structured request-ID/allowlisted-SQLSTATE logging. No SQL text/parameters or raw exceptions.
- scripts/browser_acceptance.py: on browser failure emit only bounded, allowlisted structured
  persistence diagnostics before deleting temporary logs. Raw server logs are still not retained.
- apps/web/e2e/risk-workflow.ts: narrow savedPolicy to the risk-account policy route; keep expected 201
  and all policy verification assertions. Failure messages include only the route template, status,
  validated request ID and fixed category, without payloads, cookies or raw error bodies.
- tests/test_risk_integration.py: deterministic real-monitor/policy race regression; verify both
  commits, immutable version/digest, persisted UNVERIFIED state, stops and audit chain.
- tests/test_health.py and tests/test_integration_guards.py: verify correlated503 sanitization,
  log-field allowlisting and bounded diagnostic output. These portable fixtures are not service
  acceptance evidence; the native race test is.
- This report, IMPLEMENTATION_STATUS.md and the new sanitized evidence supplement. Earlier evidence
  files and design/inventory documents remain unchanged.

Risk-policy validation still returns 422 for invalid period/currency and 409 for personal/prop or
exact program/provenance mismatch. Owner/recent-MFA/CSRF/RBAC/ownership checks remain in place.
No automatic retries, forced verification, widened permissions or changed success assertions.
SIMULATED/DENY_ALL remains active. No schema migration, dev-volume reset or Phase 6 work.

### Correction verification and remaining acceptance gate

The evidence supplement records every executed command and final exit code. Focused native commands
use .cache/phase55b-policy503/focused_services.py, a private filter around the unchanged disposable
harness: only pytest node IDs are selected; real ports/credentials/services/restart/cleanup remain.
The expanded pytest commands are also captured in its private output.

- Before-fix native race reproduction: exit 1; actual201 assertion failed with503 / 40P01. Only that
  invocation's random isolated Compose project was cleaned; no development resources were removed.
- After-fix focused policy/concurrency suite: exit 0; 4 cases before and 4 after service restart,
  including exact prop-program/provenance/cap refusals and the concurrent monitor/policy case.
- .venv/bin/python -m pytest tests/test_risk_math.py tests/test_health.py
  tests/test_integration_guards.py -q: exit 0, 72 passed.
- First make check: exit 2 on four strict typing errors in new test annotations; fixed using typed
  FastAPI casts and the direct poll import. No check was disabled. Subsequent make check: exit 0,
  212 Python and 94 frontend tests plus lint, format, mypy, TypeScript and build. 78 deselected service
  cases are not counted as portable passes.
- npm --prefix apps/web run test:e2e -- --list: exit 0, 20 cases collected; execution not implied.
- make contracts-check: exit 0, generated contracts still match.
- make integration: exit 0; one running-API readiness check, 77 actual isolated-service tests before
  and 77 after graceful restart, then strict readiness/execution-denial smoke HTTP 200. The new race
  regression is included in both stages. Cleanup removed only the invocation's disposable project.
- make smoke-demo, make secret-scan and make repository-check: exit 0. Final post-report scan results
  are in the evidence supplement. git diff --check is also recorded there.
- Local builds for API/risk-monitor and dependency-free refresh: exit 0. Both services are healthy;
  served OpenAPI matches source, readiness is 200 and external execution flags remain disabled.
- PostgreSQL, Redis, MinIO, market-worker, research-worker and Web retained their original container
  IDs/mounts and remain healthy. Only API/risk-monitor were intentionally recreated. No migration
  or development volume deletion occurred. Operational row equality was not asserted.
- Starting-state hashes cover 1,043 existing files. Exactly nine existing files changed within this
  correction; the other 1,034 remain identical. The actual RiskCenter request payload, risk routes/
  schemas, financial engine, authorization logic, migrations and Compose definitions are unchanged.
- An initial Prettier invocation used the wrong relative path and exited2; corrected repository-relative
  invocation exited0. No visual snapshot baseline was changed or generated.

The focused command E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ux make browser-integration is
**BLOCKED / NOT EXECUTED HERE**, exit code null. The existing managed-browser origin denial remains
a constraint; an alternate CLI browser launch is not used to bypass it. Owner-local Chromium success
is separate evidence and is not relabeled as a launch failure. Full 20-case browser acceptance remains
NOT RUN for this correction. Run on the owner's authorized host:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ux make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
make check
make integration
make contracts-check
make smoke-demo
make secret-scan
make repository-check
```

Do not update snapshots to hide a regression. Previously missing baselines still require genuine
non-secret candidate generation and explicit human review under the earlier documented process;
no candidate or visual acceptance is claimed here. All 20 browser scenarios and the outstanding
manual accessibility gates must pass before Phase 5.5B can be fully accepted.


## Visual timestamp-mask correction — 2026-10-27

**FIXED IN SOURCE; baseline review and browser acceptance remain BLOCKED / NOT COMPLETE.**
This is an actual captured-page mismatch, not a Chromium launch failure. The owner reports one UX
case passed, one visual case failed, and backend_failures was empty. That is owner-reported evidence
for this local run, not an agent execution of the full 20-case acceptance suite.

### Actual images and exact region

The actual expected, received and diff PNGs were viewed directly and decoded for exact RGBA
comparison. Byte-identical, signed-out public copies are preserved here:

- [Expected](docs/phase55b-evidence/2026-10-27/visual-mask/owner-home-light-expected.png).
- [Received](docs/phase55b-evidence/2026-10-27/visual-mask/owner-home-light-actual.png).
- [Diff](docs/phase55b-evidence/2026-10-27/visual-mask/owner-home-light-diff.png).
- [Exact pixel counts, bounds and hashes](docs/phase55b-evidence/2026-10-27/visual-mask/pixel-analysis.json).
- [Command, source and preservation evidence](docs/phase55b-evidence/2026-10-27/visual-mask/verification.json).

Both PNGs are 1280×1047. All coordinates below are zero-based PNG pixels, inclusive bounds.
Exactly 84 RGBA pixels differ, confined to x=1189–1192 / y=962–982: a 4×21 strip at the left edge of
the footer clock mask. The expected mask is x=1193–1247 / y=962–982, 55×21; the received mask is
x=1189–1247 / y=962–982, 59×21. The right edge and height are identical. The 84 changed pixels are
background RGBA (245,247,250,255), hex #F5F7FA, becoming the screenshot mask's opaque magenta
RGBA (255,0,255,255), hex #FF00FF. Every pixel outside that strip is byte-identical. The expected
artifact also matches home-light-desktop-darwin.png byte-for-byte, SHA256
437e527602f416199fc5624afabced6dc010b0b0fbd35bb6223d2d07b0c0e5a4.

### Root cause and classification

Playwright masks the element's bounding box, not only the timestamp characters. App rendered the
actual lastSuccess with locale-formatted text in an intrinsic-width time element. The system font
uses proportional digits; the time had no reserved inline width or tabular numeral rule. Different
clock digits can therefore change the width of the mask even after screenshot stabilization.
The clock is right-aligned by the flex footer, so widening it shifts the mask's left edge.

This is a timestamp/mask geometry determinism defect, with minor clock layout jitter, not an
antialiasing mismatch, changed heading/card/navigation or financial regression. The exact underlying
time values cannot be recovered from masked PNGs and are not invented. The evidence proves the
mask width difference; the source identifies why this region was allowed to vary. Waiting longer,
loosening a pixel threshold, masking more content or replacing the backend would not fix it.

### Source correction and preserved behavior

- apps/web/src/ui/PublicReadTime.tsx: typed public observation component, actual lastSuccess instant,
  semantic ISO datetime and Romanian two-digit HH:MM:SS/h23 display. No fake/frozen time, API override,
  fabricated availability or changed safety age/authorization.
- apps/web/src/App.tsx: use the component at the existing footer clock only.
- apps/web/src/ui/product.css: reserve 8ch for HH:MM:SS, use tabular numerals, no wrapping, no flex
  shrink and end alignment. The dimension is based on the clock format, not on the failing image's
 55px width. Font size, readable real timestamp, responsive footer wrapping and safety copy remain.
- apps/web/src/ui/PublicReadTime.test.tsx: four real instant/leading-zero/late-hour presentation cases
  verify exact ISO provenance and padded eight-character Romanian display. These are portable SSR
  tests; they do not establish actual browser geometry.
- apps/web/e2e/ux-visual.spec.ts: retain strict existing screenshot comparisons, both themes, the
  exact same timestamp-only mask, no-horizontal-scroll and 44px navigation assertions. Add clock
  text/datetime assertions and a real GET overview refresh that must return 200, update the observation
  and preserve mask dimensions. Compare dimensions rather than viewport y because clicking can scroll.
- This report, IMPLEMENTATION_STATUS.md, docs/FRONTEND_UX.md and the public evidence supplement.

No maxDiffPixels, maxDiffPixelRatio, threshold, timeout increase or arbitrary sleep was introduced.
No screenshots/trace were enabled for authentication or recovery. No financial/safety/backend/DB
code, MFA/RBAC/CSRF checks, risk policy logic, immutable storage, or execution-denial tests changed.
No baseline file was changed, generated or silently accepted. SIMULATED/DENY_ALL remains active.

### Reference approval and verification gate

The existing reference encodes an unstable 55px mask. The corrected format-based slot intentionally
changes that mask's geometry; existing light/dark references need explicit owner visual review.
The post-fix pixel bounds have not been measured here and are not fabricated. Existing on-disk
references are desktop-darwin light/dark only; complete mobile reference coverage is not claimed.

Run the focused command below on the owner's authorized host with snapshot rewriting disabled.
The comparison may fail against the unchanged old mask: inspect its genuine actual/diff files,
verify the expected timestamp-region change and investigate any unrelated pixels. Only after that
review should the owner replace the corresponding reference. Repeat for themes/viewports as needed.
Do not approve reference changes from source inspection alone. This task does not itself approve
new visual references. No update-snapshots command was executed here.

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ux make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Both browser commands are BLOCKED / NOT EXECUTED HERE, process exit code null: the existing saved
managed-origin denial remains in force. No alternate CLI/browser/raw-CDP/proxy workaround was used.
The owner's working Chromium and supplied PNGs are acknowledged separately. Current full 20-case
execution remains unverified. New visual/manual/mobile rendering is not accepted from compilation.

Executed on the corrected source:

- npm --prefix apps/web test -- src/ui/PublicReadTime.test.tsx: exit 0, 4 tests passed.
- make check: exit 0, 212 Python and 98 frontend tests; lint/format/mypy/types/production build pass.
 78 service cases deselected by the portable target are not counted as passes.
- npm --prefix apps/web run test:e2e -- --list: exit 0, 20 cases collected. Collection is not execution.
- make contracts-check and make smoke-demo: exit 0.
- Web image build and dependency-free Web refresh: exit 0; Web is healthy. API, risk monitor, market/
  research workers and PostgreSQL/Redis/MinIO retain their original container IDs/mounts, all healthy.
  No development volumes were removed or migrated; operational DB row equality was not measured.
- make secret-scan, make repository-check and git diff --check: exit 0. Source hashes show only this
  correction's six existing frontend/docs files changed; earlier unrelated work and owner PNGs,
  including both desktop reference hashes, are unchanged. No backend changes or schema migrations.
- The first post-evidence combined scan exited 2 after Gitleaks reported one generic-key false
  positive in the generated ledger's public safety prose. A diagnostic scan exited 1 and located
  that sentence; the same safety state was represented as structured booleans. No rule/allowlist/
  exclusion was relaxed. The repeated make secret-scan repository-check exited 0.
- The prior risk-correction native 77-before/77-after integration result is retained historically;
  it was not rerun or relabeled as visual acceptance for this frontend-only correction.

Phase 5.5B is not complete until all 20 desktop/mobile browser cases, reviewed references and the
outstanding manual gates pass. Stop after this correction; no Phase 6 or external order capabilities.


## Owner post-fix visual reference review — 2026-10-27

The owner's later terminal screenshot and actual failure PNGs now show 336 differing pixels, one
passed/one failed and backend_failures empty. The new actual/diff PNGs were directly viewed and
decoded; this is post-fix owner-rendered evidence, not a new agent browser run.

Both 1280×1047 images are identical outside the clock-mask expansion. The old reference mask is 55×21
at x=1193–1247/y=962–982; the fixed clock-slot mask is 71×21 at x=1177–1247/y=962–982. Exactly 336
pixels in the 16×21 strip x=1177–1192/y=962–982 change from background #F5F7FA to mask #FF00FF.
All bounds are inclusive, zero-based PNG coordinates. This is the intentional format-sized slot
compared with the unchanged old intrinsic-width reference; it is not a new application regression.
At review time, the expected artifact exactly matched the original reference SHA256 recorded above.

A concrete, byte-identical candidate is prepared from the genuine owner actual image:
[light desktop candidate](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-light-desktop-darwin.candidate.png),
[previous reference](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-light-desktop-darwin.current.png),
[diff](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-light-desktop-darwin.diff.png),
[exact review metadata](docs/phase55b-evidence/2026-10-27/visual-reference-review/review.json).

OWNER APPROVED AND APPLIED: the owner explicitly replied “Approve light desktop reference”. Only
home-light-desktop-darwin.png was replaced with the exact inspected candidate. Its new SHA256 is
1da590a97f8d145e94a08efb7f218fad35f4ab1e844909fc5d564bee005bd30a. The old reference remains
preserved in the review evidence. [Approval and copy verification](docs/phase55b-evidence/2026-10-27/visual-reference-review/approval.json)
record both hashes, the exact scope and unchanged dark-reference hash. Initial review.json retains
the earlier pending state as history; approval.json records its subsequent authorization/application.
No update-snapshots command, source or tolerance change occurred. The copied reference is byte-identical
to the owner's captured actual image (offline zero-pixel difference), which is not a fresh browser pass.
Dark/mobile references are not inferred, generated or approved from this light image.
The visual case stops at its first light comparison, so later dark capture and the real-refresh
dimension assertion remain unexecuted in that case. The passing UX case does not establish full 20
acceptance. With this one approved reference applied, rerun the focused UX command and complete 20-case command
above without snapshot rewriting. The dark theme can still report its own old-reference mismatch;
review its genuine artifacts separately. No new unit/integration/browser pass is claimed for this
image-only review. Fresh secret/repository/whitespace and baseline-copy verification are recorded
in the approval evidence after execution.
SIMULATED/DENY_ALL remains unchanged; no application, backend or development-volume mutation.


## Owner dark-reference review — 2026-10-27

The next owner run reaches home-dark.png after the approved light comparison. Its actual dark
expected/received/diff PNGs were viewed and decoded. Again, all 336 changed pixels form only the
16×21 clock-mask expansion at inclusive x=1177–1192/y=962–982: dark background #10151D becomes
mask #FF00FF. Expected mask 55×21 versus actual 71×21; both images 1280×1047. Every other RGBA
pixel is identical. Expected PNG still matches the old dark reference SHA256
a92222f6683c78800603bb230b1b2b26f98719ca1d6dcab12b204e46d9919e63. This is the same intentional
clock-slot reference change, not an additional application regression or a backend 503.

[Inspected dark candidate](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-dark-desktop-darwin.candidate.png),
[previous dark reference](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-dark-desktop-darwin.current.png),
[dark diff](docs/phase55b-evidence/2026-10-27/visual-reference-review/home-dark-desktop-darwin.diff.png),
[exact pixel/hash evidence](docs/phase55b-evidence/2026-10-27/visual-reference-review/review-dark.json).

OWNER APPROVED AND APPLIED: the owner explicitly replied “Approve dark desktop reference”. Only
home-dark-desktop-darwin.png was replaced byte-for-byte with the inspected genuine candidate, SHA256
181f7df4fa1f7e315b0ab793694915f14129fae5dc1ebcbe22a76801a875deb9. The earlier approved light
reference is unchanged, SHA256 1da590a97f8d145e94a08efb7f218fad35f4ab1e844909fc5d564bee005bd30a.
[Dark approval/copy evidence](docs/phase55b-evidence/2026-10-27/visual-reference-review/approval-dark.json)
records the exact scope and both reference hashes. review-dark.json retains the prior pending state
as history. The old dark reference is preserved in the public evidence. Offline comparison against
the owner's captured actual is byte-identical, not a newly executed browser pass. No source, tolerance,
security rule or development resource was changed; no update-snapshots command was run. No dark/mobile image was inferred from the light screenshot. The
failed dark comparison prevents the later refresh-dimension/reflow checks in this visual case from
completing. One passing UX case and progress past light do not establish a full visual-case or 20-case
pass. The agent did not launch a browser; the existing managed-origin restriction remains in force.
Only offline pixel analysis and repository/secret/whitespace checks are claimed for this review.
SIMULATED/DENY_ALL, security/risk/provenance and development volumes remain untouched.


Both desktop light/dark references now contain only individually inspected and explicitly owner-
approved clock-mask geometry changes. Rerun locally, without rewriting:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ux make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

The managed agent cannot execute these browser runs under the existing saved-origin restriction.
No mobile baseline was approved or fabricated. All 20 desktop/mobile cases and the outstanding
manual checks remain required before Phase 5.5B acceptance. No Phase 6 or external order capability.


## Returning-owner MFA/navigation correction — 2026-10-27

FIXED IN TEST SOURCE; complete browser acceptance remains BLOCKED / NOT COMPLETE. The owner's
next foundation run reports three passing cases and one failure at phase1.spec.ts:156: the exact
“Cont persistent E2E” heading is absent after logout/password login/MFA and hard navigation. This is
a functional authentication-workflow failure, separate from the approved visual references.

### Evidence and diagnosis

The actual on-disk phase1 error-context was inspected through sanitized predicates. The failed page
contains the password-login form and lacks the FULL-only logout button and account heading. No
raw DOM/input values, OTPs, seeds, passwords, cookies or session payloads were copied into evidence.
The account had already been created and renamed successfully earlier in this same test. There is
no evidence that PostgreSQL deleted it or that its accessible heading was renamed.

The test clicked “Verifică MFA” then immediately executed page.goto('/conturi'). Playwright click
waits for the interaction, not the async onSubmit promise. That navigation can discard the verification
response while the server revokes the MFA-challenge session and issues its replacement cookie. A new
page retaining the revoked cookie is unauthenticated, so the route guard correctly shows login.
This is a definite missing authentication-completion boundary in the test. The original MFA status/
network abort/server correlation log are unavailable; the artifact alone cannot distinguish an
aborted rotation response from an MFA rejection. No original request outcome is invented. The new
assertions expose any rejection at MFA itself, rather than reporting a misleading account timeout.
backend_failures:[] covers persistence diagnostics and does not prove authentication succeeded.

A new native actual-PostgreSQL regression reproduces the relevant cookie lifecycle: create/rename
the account, logout, password login, verify real MFA, then read it in a new app/request context using
the returned cookie. The record name and exact capital persist. A second context retaining the old
MFA-challenge cookie receives 401 on auth/me and the account route. Before MFA, the valid challenge
session receives 403 on the protected account route. This validates the loss-of-response mechanism
and fail-closed auth behavior; it is not a reproduction of the original Chromium navigation timing.

### Small correction and unchanged safety

- apps/web/e2e/phase1.spec.ts: register an exact POST /api/v1/auth/mfa/verify response wait before
  clicking, require 200 and complete response delivery, assert FULL/OWNER/the expected username,
  wait for the FULL-only Deconectare control, then require auth/me 200/FULL with the same owner ID.
  Only then navigate to /conturi. Both original exact-heading/persistence/reload assertions remain,
  along with HttpOnly, browser-storage, responsive and external-order denial assertions.
- tests/test_phase1_integration.py: add actual owner/account/session-rotation/read-back acceptance,
  including explicit old-cookie rejection, pre-MFA refusal and audit-chain verification. Private
  cookie comparisons assert booleans only; no raw secrets are attached to failures.
- This report, IMPLEMENTATION_STATUS.md and the sanitized evidence supplement.

No application/backend code, authentication rules, CSRF, RBAC, owner isolation, TOTP acceptance
window/counter, Risk Gateway, financial calculations, data provenance or visual reference changed.
No sleep, increased timeout, retry, mocked auth response, skipped test or relaxed locator. Existing
future-step TOTP fixture behavior is retained; production replay prevention remains unchanged.
No dev-volume mutation or Phase 6/external execution. SIMULATED/DENY_ALL remains enforced.

### Actual verification

Exact commands, process exits and sanitized facts are collected in
[auth-navigation evidence](docs/phase55b-evidence/2026-10-27/auth-navigation/verification.json).
Raw local command logs stay private under .cache/phase55b-auth-navigation/.

- Focused actual-service selector: two owner/session tests pass before restart and two after; exit 0.
  It uses the unchanged disposable harness and changes only the pytest node list. The filtered
  command is recorded; these auth tests use PostgreSQL and do not claim Redis/MinIO round trips.
- make check: exit 0, 212 Python + 98 frontend tests; lint, formatting, mypy, TypeScript and build pass.
 79 service cases deselected by the portable target are not counted as passes.
- npm --prefix apps/web run test:e2e -- --list: exit 0, 20 cases collected, not browser execution.
- make contracts-check and make smoke-demo: exit 0.
- make integration: exit 0; one running-API readiness test, 78 actual isolated-service cases before
  restart and 78 after restart, then strict readiness/execution-denial smoke HTTP 200. This includes
  the new session/account regression and existing risk/storage/research acceptance. Only its own
  random Compose project/databases/volumes were cleaned.
- make secret-scan, make repository-check and git diff --check: exit 0. Final post-evidence results
  are retained in the ledger. No test or scanner rule was disabled.
- All eight development service containers and mounts retain their starting identities and remain
  healthy. No development resource recreation or schema migration. Operational row equality was
  not measured. Both approved desktop reference hashes remain identical.

The managed-origin restriction still prevents agent browser execution. These commands are NOT
EXECUTED HERE, exit code null; no CLI/alternate browser workaround was attempted. Run locally:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=foundation make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Require all 20 desktop/mobile scenarios and the remaining manual gates before Phase 5.5B acceptance.
Both individually owner-approved desktop references remain untouched by this correction.


## Market import browser synchronization correction — 2026-10-28

FIXED IN TEST SOURCE; browser acceptance remains BLOCKED / NOT COMPLETE. The owner's subsequent
local screenshot shows the foundation desktop group passing all four cases, then phase2.spec.ts:13
timing out after 120000ms. No browser launch problem is inferred from this actual UI run.

### Evidence, diagnosis and limits

The actual Phase 2 error-context.md contains only the scenario and global timeout: no locator,
active await, call stack, DOM snapshot, request/response details or correlation ID. The original
blocked operation cannot be determined from that artifact. backend_failures:[] only reports no
collected persistence diagnostics; it does not prove successful UI setup or all API requests.
No original HTTP status, worker failure or precise timing is fabricated.

Inspecting phase2.spec.ts against MarketData.tsx reveals two definite synchronization defects:

- Instrument creation first awaits POST /api/v1/records/venues when needed, then POST
  /api/v1/records/instruments. The test clicked save and immediately hard-navigated to source
  registration. A Playwright click does not await the asynchronous React submit handler; navigation
  can interrupt this chain, leaving the later EURUSD selection without a persisted instrument.
- The import handler awaits the multipart POST /api/v1/market/imports, parses its job, then navigates
  to /testeaza/date/importuri/{job.id}. The test immediately clicked the dataset catalog after
  submission, racing that delayed redirect and subsequent catalog assertions.

These are supported source defects, not proof of which one caused the original global timeout.
The revised workflow exposes the actual failing stage and request boundary in the next local run.
No response bodies, passwords, MFA enrollment/recovery values or cookies are printed or retained.
Automatic authentication traces/screenshots/DOM attachments remain disabled.

### Correction and preserved behavior

Only apps/web/e2e/phase2.spec.ts changes executable source in this correction:

- Register the exact instrument POST response wait before save; require 201 and complete delivery,
  then require the exact persisted EURUSD heading before leaving the editor.
- Register the exact import POST response wait before submit; require 202, complete delivery and
  returned job/dataset IDs. Wait for that job's actual redirect, then poll the authenticated job
  endpoint for SUCCEEDED before opening the catalog. The poll has a 30-second bound matching the
  existing quality assertion; the overall 120-second limit is unchanged. No arbitrary sleeps or
  hidden retry of writes.
- Add ten named test steps and fixed stage-only console markers. A future global timeout can be
  localized without capturing authentication or imported source data. Capture already-validated
  fixture environment values into constants for TypeScript narrowing across step closures.

All 16 original assertion expressions are preserved (checked with a formatting-independent
TypeScript AST comparison). Original quality, actual stored chart, exact manifest equality and
zero observations before availability remain mandatory. The five explicitly synthetic CSV bars,
UTC/source-rights declarations, real authentication, CSRF, account ownership and service APIs remain.
No request mocking, data fabrication, relaxed validation, assertion removal or snapshot update.
No React, backend, worker, risk math, migration, Compose or authentication rule was changed.
This report, IMPLEMENTATION_STATUS.md and a sanitized evidence supplement are also updated.

### Verification and remaining gate

Exact commands, exit codes, initial failures and final checks are recorded in
[market-browser evidence](docs/phase55b-evidence/2026-10-28/market-browser/verification.json).
Raw command logs remain private under .cache/phase55b-market-browser/.

- Focused real-service market selector: exit 0, three cases before restart and three after. It
  changes only the pytest node list in the unchanged disposable harness. Actual PostgreSQL,
  Redis and MinIO support import/manifest/checksum/immutability, point-in-time availability,
  quality rejection, queue recovery, cancellation and ownership tests. No external provider or
  broker integration success is claimed.
- make check: initial exit 2 on TypeScript environment-value narrowing after introducing step
  closures; fixed with validated local constants. The next attempt exited 2 on Prettier formatting;
  formatted the file. Final exit 0: 212 Python tests and 98 frontend tests, lint/format/types/build.
  The 79 portable-target deselections are not counted as passes. Existing Starlette TestClient
  deprecation warnings remain; no dependency change was needed for this E2E-only correction.
- make integration: exit 0, one readiness test and 78 isolated cases before restart plus 78 after,
  then strict API readiness/execution-denial smoke HTTP 200. Actual loopback port inspection and
  TCP connectivity pass. The random test project alone is cleaned up.
- make contracts-check and make smoke-demo: exit 0; generated contracts match byte-for-byte.
- npm --prefix apps/web run test:e2e -- --list: exit 0, 20 cases in eight files collected;
  collection does not launch Chromium or execute assertions.
- make secret-scan, make repository-check and git diff --check: exit 0. Final evidence scan results
  are recorded in the ledger; no scanner rules or test assertions were weakened.
- All eight development containers retain their IDs, images and mounts and report healthy. No
  development recreation or migration. Operational database row equality was not measured.
  Both owner-approved desktop reference hashes remain unchanged. Source snapshot comparison
  finds only this test and the two reports changed among 1,067 existing files.

The agent's existing managed localhost-origin restriction remains in force. Browser commands below
are BLOCKED / NOT EXECUTED HERE (exit code null); no CLI/alternate browser workaround was attempted.
Owner-local verification, without rewriting references:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Require the focused desktop market case and then all 20 desktop/mobile cases, plus outstanding
manual gates, before Phase 5.5B acceptance. A passing native suite or test collection is not browser
acceptance. Both individually approved desktop references are preserved. No Phase 6 or external
execution; SIMULATED/DENY_ALL, MFA, risk enforcement and immutable provenance remain in force.


## Mobile visual reference review — 2026-10-28

MOBILE REFERENCES NOW APPROVED; Phase 5.5B acceptance remains NOT COMPLETE. The latest owner screenshot
shows one mobile visual failure and one other passing case, with backend_failures:[] and disposable
cleanup. It does not supply a complete 20-case passing summary. No earlier failed case is silently
reclassified as passed.

### Exact cause and image evidence

The actual mobile error-context lists missing reference files for BOTH themes:
apps/web/e2e/ux-visual.spec.ts-snapshots/home-light-mobile-darwin.png and
home-dark-mobile-darwin.png. This is a reference-coverage gap, not a reported pixel mismatch,
Chromium launch failure or HTTP 503. There was no prior mobile expected image to compare, so no
changed-pixel region or font/CSS regression can be inferred. Earlier owner approvals explicitly
covered desktop light and desktop dark only.

Both actual PNGs from that run were inspected offline. Each is 390×1317 and depicts the signed-out
public Home with Romanian copy, five mobile navigation items, SIMULATED / DENY_ALL and honest UNKNOWN
system state. No authentication, enrollment or recovery fields are visible. The timestamp mask is
71×21 at inclusive x=16–86/y=1164–1184 (1,491 magenta pixels), matching the fixed clock slot. The heading
focus outline is visible. The fixed bottom navigation appears at the 390×664 emulated viewport's
bottom within the longer full-page capture; interactive scroll/occlusion and accessibility are not
validated by inspecting a PNG. No visual or WCAG compliance claim is made.

The two reference files now exist and are byte-identical to their corresponding actual PNGs,
consistent with the owner's “snapshot doesn't exist ... writing actual” output. The agent did not
write, replace or delete these canonical reference files, and their presence does not grant approval.
Exact genuine candidate copies (not resized, recolored or synthesized) and review metadata:

- [Light mobile candidate](docs/phase55b-evidence/2026-10-28/mobile-reference-review/home-light-mobile-darwin.candidate.png)
  SHA256 96700c32f36e584a0198021077ec085f1362ff1021d125e3507d54ed7d6cc519.
- [Dark mobile candidate](docs/phase55b-evidence/2026-10-28/mobile-reference-review/home-dark-mobile-darwin.candidate.png)
  SHA256 4626b942a2d2b1835ec6e58f48914a927790804dca6baf2f11f66e59bcba67ea.
- [Review record](docs/phase55b-evidence/2026-10-28/mobile-reference-review/review.json) retains pending
  approval, artifact hash, geometry and scope. No raw DOM/authentication state is copied into evidence.

### Changes, verification and remaining gate

Only this report, IMPLEMENTATION_STATUS.md and the new public review/evidence files change.
Application code, test assertions/configuration, screenshot tolerances, masks, approved desktop PNGs,
financial rules, MFA, Risk Gateway and provenance remain unchanged. No snapshot-update command,
browser permission workaround, development container operation or volume deletion was performed.
No full native integration rerun is claimed for this evidence-only review; the prior real service
results are retained above as dated evidence.

- make check: exit 0, 212 Python + 98 frontend tests, lint/format/types/build; 79 deselections are not
  passes. Existing Starlette TestClient deprecation warning remains.
- make smoke-demo: exit 0, readiness HTTP 200 and execution-denial smoke pass.
- Secret, repository, whitespace and source/reference preservation checks are recorded in
  [verification.json](docs/phase55b-evidence/2026-10-28/mobile-reference-review/verification.json).
- Agent browser execution remains BLOCKED by the existing managed-origin restriction. No fresh
  mobile screenshot, post-reference visual comparison or complete-suite success is claimed.

The owner's instruction “Only generate new candidates for explicit human review” required approval
of these two mobile references. The owner subsequently answered “Approve both mobile references”.
[approval.json](docs/phase55b-evidence/2026-10-28/mobile-reference-review/approval.json) binds that
approval to the two exact candidate/reference hashes above. Both existing generated files match
byte-for-byte, so no copy, replacement or snapshot-update command was needed. All four current
reference hashes, including the previously approved desktop files, were verified unchanged.
review.json and verification.json retain the original pending review as historical evidence; the
approval record is the current reference status. Approval does not reclassify the failed run as a pass.
Only approval/report metadata changed in this follow-up; prior check/smoke results are retained,
and fresh secret/repository/whitespace checks are recorded in approval-checks.json. Rerun locally
without rewriting snapshots:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=mobile E2E_ONLY_SCENARIO=ux make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

These commands were NOT EXECUTED HERE (exit code null). Require the focused mobile UX group and all
20 desktop/mobile cases, plus outstanding manual gates. A newly generated reference is not a passing
comparison. SIMULATED/DENY_ALL remains enforced. No Phase 6 or broker execution.
