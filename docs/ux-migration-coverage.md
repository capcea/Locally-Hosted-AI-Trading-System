# Phase 5.5B — feature and issue traceability

Implementation dated 2026-10-27. SOURCE / native-test evidence is separate from browser acceptance.
The approved Phase 5.5A audit is unchanged. No item below is a claim of current rendered validation.
All 42 inventory units retain a path; API-only operations remain explicitly API-only.

## S01–S42 destination coverage

Current canonical destinations follow the approved mapping below. Deep entity routes use owned API
reads, with the same server guards. Risk subroutes share the scoped RiskCenter; policy versions remain
in its account list. Broker observation subroutes share the account connection tools; registry and
source lists retain bounded API paging where present. Simulation journal routes set the view read-only.

- **S01:** App shell, theme, refresh → persistent shell; `/setari/aspect`; refresh scoped to current data.
- **S02:** App `overview` → `/`. Replace public reference metrics with labeled public status and, after
  authentication, actual owned task summaries. Keep configuration examples in `/setari/despre`.
- **S03:** App `infrastructure` → `/setari/diagnostic`; retain service search and stale reasons.
- **S04:** App `governance` → `/conturi/:accountId/siguranta` plus public mode explanation under About.
- **S05:** App `roadmap`, all three future sidebar buttons → `/setari/despre/plan`; future entries remain
  readable documentation, not broken duplicate controls for available backtesting.
- **S06:** Management unauthenticated/login/session → `/autentificare`, with safe intended destination.
- **S07:** uninitialized owner bootstrap → `/configurare-proprietar`; same server bootstrap restrictions.
- **S08:** ENROLLMENT/secret/recovery-save → `/securizare-cont`; secret pages excluded from captures.
- **S09:** MFA/recovery login mode → authentication step; no replacement factor or bypass.
- **S10:** Management `accounts` → `/conturi` and account detail/edit.
- **S11:** Management `risks` (governance risk-profiles) → descriptive legacy records under account Advanced.
- **S12:** Management `policies`/firms/programs/source attestation → account Policies and Settings Catalog.
  Source-document verification stays distinct from applicable RiskPolicy verification (S30).
- **S13:** Management `security` reauth/password/revoke → `/setari/securitate`; contextual reauth may open
  the same secured flow from the interrupted action, retaining only a safe draft.
- **S14:** owner-only user create/role/suspend/reactivate → `/setari/utilizatori`.
- **S15:** Management `audit`/verify/pagination → `/setari/istoric` with optional account/experiment links.
- **S16:** App `market` or Management `market`, catalog/filter/pagination → `/testeaza/date`.
- **S17:** selected dataset sample/chart/table/decision time → dataset `/previzualizare`.
- **S18:** quality/manifest/compare versions → data detail, `/provenienta`, `/versiuni`.
- **S19:** import history/cancel → `/testeaza/date/importuri/:jobId`; list remains linked from data index.
- **S20:** CSV/Parquet/ECB form → `/testeaza/date/import`; adapter limits and mandatory facts remain.
- **S21:** provider/venue/instrument create → `/setari/surse` and `/setari/catalog`, contextually linked
  from import. A missing prerequisite returns to the draft, not to a second competing wizard.
- **S22:** App/Management `broker` connection identity/list/status → account `/conexiuni`.
- **S23:** signed snapshot import/reported demo symbols/quotes/orders/positions → connection `/observatii`.
- **S24:** new manual synthetic scenario/assumptions → account Advanced simulator `/nou`.
- **S25:** manual tick/admitted replay → account Advanced simulator `/:runId/date`.
- **S26:** order submit/repeat/modify/cancel/close/OCO/fault controls → Advanced simulator `/:runId/ordine`.
- **S27:** journal/positions/events → `/rezultate/simulari/:runId/jurnal`; mutation/reconcile stays in the
  scoped manual tool. Internal research journals remain mutation-prohibited and are not unhidden.
- **S28:** RiskBanner + App/Management `riskCenter` status → persistent strip and account Safety.
- **S29:** enforced independent profiles/scopes/version JSON → account `/limite`.
- **S30:** risk-policy rules/personal/prop/attest/source → account `/politici/:policyId`.
- **S31:** monetary/payoff/FX/news-calendar/context evidence → account `/ipoteze`; required status is
  visible in test readiness, while full evidence is an expert review rather than a hidden assumption.
- **S32:** what-if sizing/history → account `/verificare-risc`; decision details also link from replay.
- **S33:** reservations/UNKNOWN allocations/incidents → account `/alocari-incidente` and safety summary.
- **S34:** MONITOR/STOP/CLEAR/FLATTEN → explicit account Safety actions, separate close route; no STOP_ALL.
- **S35:** App/Management `research` strategy library → `/testeaza/strategii` and guided strategy step.
- **S36:** research form/costs/timeframe/sweeps/portfolio/random controls → `/testeaza/nou` with Advanced.
- **S37:** research jobs/progress/cancel/history → Activity and stable experiment progress URL.
- **S38:** completed results/equity/metrics → `/rezultate/:experimentId`.
- **S39:** trades/fills/signals/replay/exposure/walk-forward/provenance → corresponding result tabs.
- **S40:** matched experiment comparison → `/rezultate/compara`; explicit source-run links.
- **S41:** seal/final frozen release → `/testeaza/evaluare-finala`; deliberate owner entry, no routine CTA.
- **S42:** mobile/theme/focus/keyboard/empty/error states → shared shell/components on every route,
  not a new module that can be skipped during feature implementation.


## Source and verification by surface

- S01–S05: App.tsx, navigation/{routes,history}.tsx/ts, home/HomePage.tsx, LegacyPublic.tsx.
  Finite-route unit tests; existing platform browser scenarios migrated, execution BLOCKED.
- S06–S09: auth/AuthProvider.tsx and Management.Authentication; username/password/OTP autocomplete,
  manual TOTP enrollment/recovery preserved. Phase1 and UX browser tests retain real enrollment.
- S10–S15: Management.Workspace/Security/Cards, shared fields/dialogs, settings route grouping.
  Existing governance/identity integration tests retained. Role and metadata separation UX tests added.
- S16–S21: MarketData.tsx, shared form controls, six-part import journey, actual timestamps/quality/
  provenance. Real service tests including direct job read and cross-owner404 PASS in native suite.
- S22–S27: BrokerCenter.tsx, connection/manual/journal routes; all existing commands, OCO, tick replay,
  fault/reconcile and read-only observation controls retained. Phase3 behavior assertions retained.
- S28–S34: RiskBanner.tsx, RiskCenter.tsx, ui/EmergencyActions.tsx, records.ts. Scope/age/unknown unit
  tests, actual gateway/ledger/owner-MFA integration tests; Phase4 and UX browser cases retained/added.
- S35–S37: StrategyLab.tsx and research-drafts.ts. Five form steps plus explicit Start, existing
  reviewed source facts, no automatic clearance. Real experiment/cancel/service-restart tests pass.
- S38–S40: results/{ResultView,AdvancedStatistics}.tsx and StrategyLab result/compare routes. Stored
  precision/uncertainty/sampling tests; native causal replay/comparison/statistics tests preserved.
- S41: FinalEvaluation.tsx, separate owner route. Native one-use authorization/frozen-scope rejection
  tests retained; new guided freeze/release/resume interface NOT browser validated.
- S42: ui/{tokens,product}.css, Controls.tsx, both theme controls, permanent mobile navigation.
  Sanitized visual tests added; no PNG baseline, real-mobile or VoiceOver acceptance yet.

All frontend paths above are relative to apps/web/src/. Unit/portable tests PASS; Playwright collection
is not execution. See PHASE55B_COMPLETION_REPORT.md for exact commands and current gate.

## U01–U24 closure register

“Implemented / acceptance pending” means the source correction exists, with relevant native evidence
where applicable; it does not close a browser or assistive-technology gate.

- U01 — Implemented / acceptance pending: shared auth and safety mount outside overview reads.
  Platform outage fault injection preserved; authenticated outage case added in ux-workflows.spec.ts.
- U02 — Implemented / acceptance pending: explicit descriptive-only metadata banners and separate
  applied-profile/policy/source-document paths. Real metadata-without-enforcement-change UI test added.
- U03 — Implemented / acceptance pending: distinct STOP, reviewed CLEAR, simulated FLATTEN dialogs;
  existing emergency API tests preserved. No global endpoint or implicit MFA approval.
- U04 — Implemented / acceptance pending: persistent SIMULATED/DENY_ALL, data-source labels and exact
  provenance; read-only observation, historical data and execution environment remain separate.
- U05 — Implemented / unit verified, browser pending: all account pages or a refusal, per-account
  failure, invalid/future/stale monitor checks and last-known stop retention. No “all safe” badge.
- U06 — Implemented / acceptance pending: market→strategy→period→reviewed setup→review→Start, with
  missing-prerequisite links and actual template/context/policy reads. No invented saved preset.
- U07 — Implemented / route unit verified, browser pending: finite URLs, Back/Forward, protected
  direct reads, in-memory allowlisted drafts and shared account context; no secret persistence.
- U08 — Implemented / presentation unit verified, browser pending: stored money/drawdown/trade counts,
  missing-ratio explanations, human-readable event rows and expandable exact evidence.
- U09 — Implemented / native verified, browser pending: persisted cancel-request read fields, actual
  final state, stable request key and frozen payload after an uncertain submission.
- U10 — Implemented / acceptance pending: independent shell/safety/account reads and settled resource
  reads in research/data/risk. A failed related read remains an explicit failure, not successful empty.
- U11 — Implemented / acceptance pending: source/instrument/time/rights/review/import-quality journey.
  General arbitrary CSV mapping remains outside the existing adapter contract, clearly explained.
- U12 — Implemented / native verified, browser pending: server matching final, readable409 explanation,
  side-by-side stored summaries, no forced normalization or synthetic ranking.
- U13 — Implemented / acceptance pending: actual task summaries replace static capital/checkpoints;
  future features are documentation in Settings. No false active AI/paper/live labels.
- U14 — Implemented / unit verified, browser pending: safe error mappings, explicit unknown outcome,
  no arbitrary uppercase code echo, fabricated retry timer or automated write retry.
- U15 — Implemented / acceptance pending: contextual source/catalog/account/simulator setup links and
  native Back; every advanced operation has an explicit destination.
- U16 — Implemented / native gates preserved, browser pending: separate owner-only final evaluation,
  frozen review, one-use acknowledgements, recent-MFA gate and uncertain prior exposure retained.
- U17 — Implemented / presentation unit verified, browser pending: real timestamp axes, source/currency,
  exact-value table, sample count and explicitly approximate drawdown; no authoritative client metric.
- U18 — Implemented / rendered acceptance BLOCKED: readable typography,44px controls, mobile bottom
  nav,320px layout rules and safe areas. Source dimensions do not establish mobile/zoom conformance.
- U19 — Implemented / rendered acceptance BLOCKED: native dialogs, Escape before submission, focus
  return, route heading focus, skip target and no modal mobile menu (five permanent destinations).
- U20 — Implemented / build verified: semantic tokens, compatibility aliases, defined --border, shared
  Input/Select/Evidence/Consequence controls; retained specialized forms reuse those primitives.
- U21 — Partial / acceptance pending: password-manager/paste/input-purpose assistance and manual TOTP
  preserved. Local QR renderer not added: no vetted bundled dependency was present. No remote QR call.
- U22 — Implemented / acceptance pending: shared Romanian source/job/strategy/error dictionaries and
  readable labels. Exact IDs/enums/contracts remain in advanced views; audit row enums stay inspectable.
- U23 — Implemented for primary workflows / acceptance pending: prerequisite, role, missing revision,
  pagination and pending explanations. Assistive-tech review must confirm every retained expert control.
- U24 — OPEN / BLOCKED: non-secret visual suite and optional baseline-update path exist, global secret
  screenshot/trace protections remain. Genuine baselines and review cannot be created through the
  managed denied origin. No artificial PNGs or generated mock screenshots are substituted.

## Implementation sequence (approved steps 0–10)

0. Protected1014 starting files with private snapshot/hash manifest; existing work retained.
1. Shared primitives, copy and tokens introduced, then refined alongside P0 work.
2. Auth provider, typed routes, five-destination shell and shared context introduced.
3. Independent account safety and separate emergency consequence reviews implemented before polish.
4. Home rebuilt using actual public readiness and owned task/result reads.
5. Guided import and quality workflow implemented with existing immutable storage contracts.
6. Guided research, prerequisites, safe memory drafts and durable progress implemented.
7. Stored result/compare/replay/statistics and guarded final evaluation views implemented.
8. Accounts/connections/manual tools consolidated; read-only journals separated.
9. Security/users/audit/settings/diagnostics organized; existing backend authority reused.
10. Native/build/contract checks executed; browser and manual acceptance remain BLOCKED.

Sequence reflects dependencies, not a claim that all acceptance gates have closed. No Phase6.
