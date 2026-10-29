# Approved UI Redesign V1 — implementation and acceptance

Date: 2026-10-28. **SOURCE IMPLEMENTED / NATIVE CHECKS PASSED / RENDERED ACCEPTANCE BLOCKED.**
All nine compositions have source implementations. This is not pixel-perfect, browser-complete,
WCAG-certified or production acceptance. No Phase7, external orders or generated-code execution.

## Visual-polish follow-up — 2026-10-28

[Final visual audit](REDESIGN_V1_FINAL_VISUAL_AUDIT.md) and [review package](docs/redesign-v1-evidence/2026-10-28/final-visual-review/index.html)
now preserve and inspect one actual public Home before image and its older-UI expected/diff.
All11 approved reference images were reinspected; no nine-screen candidate directory exists.
Source corrections: independent Home column stacks, readable safety-state KPI, compact AI suggestion
labels/grid, concise disabled explanation, title-sized visible focus and 70px shared header minimum.
Original questions, owner review/consent and all state/API handlers remain. Desktop Home geometry
assertions are added to the existing redesign test; capture also waits for loaded fonts.

Fresh make check passes243 Python +149 frontend tests; integration passes one readiness case and86
real isolated cases before plus86 after restart. Contracts/smoke/secrets/repository pass.24 cases
collect only. Fresh browser origin access is denied; focused/full browser and post-fix visual/manual
acceptance are NOT EXECUTED. Web alone refreshed successfully. Twelve non-web identities/images/mounts,
162 backend/infrastructure files and15 original browser/helper/golden files remain unchanged.
Four golden references are retained. No uninspected baseline candidate is submitted for approval.
The original implementation evidence below remains historical; its missing-capture statements
refer to that initial source implementation, before the saved Home artifact was discovered.

## Authority, references and protected baseline

The owner explicitly approved V1 in the attached request. The supplied handoff was found in
`/Users/andy/Downloads/AI_Trading_UI_V1_Codex_Handoff/`, verified against all14 entries in MANIFEST.json
and copied without alteration to [the reference directory](docs/design-reference/ui-v1/README.md).
DESIGN_SPEC.md, CODEX_PROMPT.md and README.md were read. The 1672×941 Home master,1536×1024 contact
sheet and **all nine individual crops were actually inspected with the image tool**. These are
concept references with fictional content, not screenshots of this implementation.

1213 existing Git-selected source/evidence files, including prior uncommitted work, were hashed and
privately snapshotted before changes. Development container/mount identities and all four accepted
Home PNG hashes were recorded. No stash/reset, commit, remote, push, model download or paid service.
Earlier Phase0–6 evidence is preserved. Baseline check, integration, contracts, smoke, secret and
repository checks passed;22 browser cases collected. Existing managed localhost-origin denial
prevents current agent browser acceptance; no CLI/CDP/proxy/alternate browser bypass was attempted.

[Implementation/data map](docs/design-reference/ui-v1/IMPLEMENTATION_MAP.md) preceded frontend edits.
[Visual review ledger](REDESIGN_V1_VISUAL_FIDELITY.md) distinguishes inspected references from missing
current captures. Native command evidence is in
[verification.json](docs/redesign-v1-evidence/2026-10-28/verification.json).

## Implementation sequence and nine screens

1. **Shared system and shell — implemented.** Semantic light/dark tokens,256px navy sidebar, blue
   selected navigation, system-font hierarchy, pale bordered panels and pastel KPI primitives.
   `App.tsx`, `ui/tokens.css`, `v1/{components,ShellTools,navigation,redesign}` retain five primary
   links, with separate nested research/settings navigation. Header includes functional destination
   search (Cmd/Ctrl+K, Enter, Escape), actual identity, theme, help and incident-review links. There
   is no fictional unread notification count. Light is the fresh-install default; saved dark/system
   preference remains honored. Auth and RiskBanner remain independent of public overview loading.
2. **Acasă — implemented.** `home/HomePage.tsx`, `v1/{ExperimentPreview,AIWidgets,AccountSafety,data}`.
   Four KPI tiles use the actual bounded owned experiment page, returned reviewed library, completed
   page count and explicit account-risk context. One selected completed experiment's stored trial,
   provenance and equity drive the chart; no portfolio sum or average success score. Recent table,
   scoped safety, real next-action links and six-stage research workflow retain empty geometry.
   AI prompt handoff is one-use, owner-bound memory only; AI Center still requires context review,
   processing consent and explicit submit. Unconfigured/unverified models leave an explained disabled
   state. Missing financial facts remain UNKNOWN. A failed read cannot retain a green success value;
   last-known account stops remain labeled on failed safety reads.
3. **Testează / Strategii — implemented.** `v1/ResearchViews.tsx` and StrategyLab. Search/category
   filters operate on actual API-returned reviewed baselines, with counts/version/category pills,
   plain descriptions, exact definition evidence and real test navigation. No live-active/profit
   claim or arbitrary strategy-code runner. Choosing a strategy preserves the reviewed wizard and
   refuses changes after an uncertain frozen submission.
4. **Testează / Backtesting — implemented.** Narrow existing five-step form plus wide prerequisite
   review panel. Every original field, advanced sweep/portfolio/OOS/walk-forward/cost/chronology/quota
   option, review acknowledgement, idempotency key and API submission remains. Checklist reflects
   selected account/dataset/registry/context/policy facts; it is not authorization. The server still
   performs final deterministic checks. Before completion there is no invented performance curve.
5. **Testează / Experimente — implemented.** Bounded page summary tiles, text/state/phase filters,
   compact table, immutable identifiers and exact detail evidence. Existing real progress, paging,
   cancellation request and terminal acknowledgement remain. A request never becomes an optimistic
   CANCELLED state. AI jobs are separate from research experiments.
6. **Testează / AI Center — implemented.** Existing question/context/rights/request/answer handlers
   arranged as a two-column research workbench with actual role/probe/expiry/limit cards. Suggestions
   only edit a draft and clear consent; they never execute a request. Questions and model source are
   inert text. Recent jobs and reloadable analyses remain. Expiring verification is not called online
   connectivity; no invented GPU usage, streaming, cost or agent activity.
7. **Rezultate — implemented.** One selected stored trial, four actual metric tiles and equity chart;
   detailed views retain transaction records, causal replay, cost/statistical warnings, provenance,
   matching restrictions and final-holdout gates. A table is shown only after the matched-comparison API succeeds; it retains exact money/currency, scenario and cost stress, without a client-side eligibility rule or ranking. Coordinate grids/stems show observed points without
   joining unknown gaps or calculating authoritative metrics from samples. Exact values remain in
   the table. Screening results are explicitly approximate/risk-unvalidated; source labels distinguish
   synthetic/user-supplied/public data, with UNKNOWN where unreadable. Exact trade distribution is
   unavailable in the current summary contract; a designed explanation replaces a fabricated doughnut.
8. **Conturi și siguranță — implemented.** Account metadata overview and selected-account navigation
   precede the retained CRUD workspace. Declared simulation capital is explicitly separated from
   broker balance and enforced limits. RiskCenter has an owned account list, actual status/limits
   column and distinct STOP / reviewed CLEAR / simulated FLATTEN column. Original consequence
   reviews, revision binding, recent owner MFA, audit and incident behavior remain. All policy,
   profile, context, what-if and reservation tools remain below. No global emergency endpoint.
9. **Setări / Modele AI — implemented.** Real registered-model table, declared context ceiling,
   measured capabilities/expiry and role cards above/beside actual connection/model/role forms.
   Unverified entries never appear online. Secure server-side endpoints/credentials are unchanged.
   All eight explicit accessible select labels from the previous correction remain intact.
10. **Setări / Platformă — implemented.** Real provider list and original registration form in two
   structural columns, including empty/error/viewer states. Same validated rights/attribution/adapter
   inputs and API save. ECB is described as reference rates, not tradable bid/ask. Theme preference,
   grouped security/users/audit/catalog/diagnostic links and advanced tools remain. No illustrative
   global timezone, auto-quality or persistence toggles were added without a matching API.
11. **Regression and acceptance — native complete; rendered pending.** Existing22 browser cases
   remain; one new real-service scenario per viewport adds2, for24 collected cases. A separate
   disposable `redesign` scenario avoids a second owner bootstrap in the existing UX database.
   It exercises all nine screens in both themes at all five requested sizes, scoped search,
   strategy selection, missing-data refusal, Back/Forward/reload and execution denial. Optional
   captures are explicitly owner-invoked, separate from golden references, and prohibited on secret
   authentication/recovery fields. This scenario has not been executed here.

## Routes and S01–S42 preservation

Canonical destinations remain `/`, `/testeaza/strategii`, `/testeaza/nou`, `/testeaza/activitate`,
`/testeaza/ai`, `/rezultate`, `/conturi`, `/conturi/siguranta`, `/setari/ai`, `/setari`. All existing
entity/detail/import/progress/replay/holdout URLs are unchanged. Additive finite aliases:

- `/testeaza/backtesting` → existing `nou` screen.
- `/testeaza/experimente` → existing `activitate` screen.
- `/setari/modele-ai` → existing AI registry.
- `/setari/platforma` → existing Settings index.

Alias routes retain the actual browser path. Five primary destinations and account context remain;
Back/Forward/reload use the same typed history/guard implementation. No arbitrary return URL is
accepted. Scoped page search indexes finite destinations, not private full-text content.

All42 original inventory units retain their documented paths in
[the complete traceability map](docs/ux-migration-coverage.md): S01–S05 shell/status/About/roadmap;
S06–S09 auth/MFA/recovery; S10–S15 metadata/identity/audit; S16–S21 data/import/quality/versions;
S22–S27 observations/manual simulator/journal; S28–S34 risk/policy/context/reservations/incidents/
emergency; S35–S41 registry/research/jobs/results/replay/compare/final holdout; S42 themes/mobile/
focus/empty/error states. Phase6 AI routes, jobs and registry are also retained. U01–U24 are not
reclassified as visually/accessibility accepted by this source redesign.

## Defects corrected during implementation

- The public frontend schema still allowed only phases0–5 while the real API reports6. Add explicit
  Phase6 support and a regression that continues rejecting Phase7 and unsafe execution contracts.
- Initial new TypeScript checks exposed dataset display fields nested under `spec`, and a missing
  Link import in the risk layout. Corrected to the actual generated contracts/import; no API change.
- Initial `make check` exited2 on a102-character harness validation message (Ruff E501). Split the
  literal; repeated full checks pass. The failed iteration is retained in the evidence ledger.
- Provider columns were made structural so extra error/notice rows cannot overlap a fixed grid row.
- Unrepresentable date coordinates are omitted from the chart rather than throwing during time-axis
  formatting. Monetary values remain those of the stored engine result.

## Verification

Commands ran from the repository root. Full exact invocations/exits/output are in the ledger.

- Baseline `make check`: exit0,243 Python +121 frontend tests and production build.
- Baseline `make integration`: exit0,one readiness case +86 isolated cases before +86 after restart.
- Baseline contracts/smoke/secret/repository checks: exit0;22 Playwright cases collected, not executed.
- Current `make check`: exit0,243 Python +149 frontend tests, Ruff/format, ESLint/Prettier,
  mypy/TypeScript and production build. Existing Starlette/httpx deprecation and Vite chunk-size
  warning remain; neither is hidden or presented as a runtime acceptance result.
- Current `make integration`: exit0,one infrastructure case +86 actual isolated cases before
  and86 after restart, then strict HTTP200 readiness and execution-denial smoke. Actual PostgreSQL
  migrations, Redis, MinIO, risk/research/AI fixtures and persistence remain tested. Synthetic AI HTTP
  fixtures are not real model inference. No applicable isolated test was skipped to obtain this.
- `make contracts-check`, `make smoke-demo`: exit0. No backend contract change.
- `npm --prefix apps/web run test:e2e -- --list`: exit0,24 cases in10 files, desktop/mobile.
- `make secret-scan`, `make repository-check`, `git diff --check`: exit0. The web-only image refresh
  passes, and served HTML/JS/CSS match the build. All11 non-web development container identities,
  images and mounts,118 protected backend/infrastructure files,15 previous E2E source/reference
  files and all four accepted PNG hashes are unchanged. These are native checks, not browser or
  accessibility certification.
- Full/focused Playwright execution: **BLOCKED / NOT EXECUTED**, exit null, due to the existing
  managed localhost-origin restriction. No synthetic render, screenshot or successful case count
  is substituted. No new production UI screenshot was captured or visually inspected by this agent.

## Local acceptance and owner review

Run the new isolated functional/layout flow first:

```sh
E2E_ONLY_SCENARIO=redesign make browser-integration
```

For genuine desktop/mobile candidates in both themes, using only disposable synthetic fixtures:

```sh
V1_CAPTURE_CANDIDATES=1 E2E_ONLY_SCENARIO=redesign make browser-integration
```

This writes `.cache/redesign-v1-captures/`:90 authenticated layout candidates per project (nine
screens × five sizes × two themes), plus two public Home candidates at the project's original
viewport. It does not update any golden. Authentication/recovery screens and secret inputs are
excluded. Captures are NOT evidence until genuinely generated and inspected. Keep public Home
candidates separate from authenticated layouts; they are not interchangeable baseline inputs.

Then run the full suite without snapshot rewriting:

```sh
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

All24 cases must pass. The intentional V1 redesign necessarily changes the old Home visual
composition; the four previously accepted PNGs are deliberately preserved. Review actual public
Home differences and explicitly approve exact new references before adoption. Do not use blanket
snapshot updates or widen tolerances to mask regressions. Prior design approval is distinct from
acceptance of newly captured golden images.

Human review still needs desktop/mobile geometry against all nine references, dark/light behavior,
keyboard/focus/zoom/VoiceOver and meaningful populated results from the existing real-service
research workflow. Reference crops are low resolution; illegible generated copy was not copied.
No1:1/pixel-perfect assertion or accessibility compliance claim is made. Real Ollama inference
remains outside this visual task's evidence; an unverified runtime stays unavailable in the UI.
SIMULATED/DENY_ALL remains enforced. Stop at V1 acceptance; no Phase7.
