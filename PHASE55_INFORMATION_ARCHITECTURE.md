# Phase 5.5A — information architecture

> Phase 5.5B implementation update (2026-10-27): this approved design is now the migration basis.
> See [implementation/acceptance report](PHASE55B_COMPLETION_REPORT.md) and
> [S01–S42 / U01–U24 traceability](docs/ux-migration-coverage.md). Source/native implementation is
> present; browser, visual-baseline and manual accessibility acceptance remain BLOCKED.
> Descriptions below remain the approved design targets; they are not evidence of rendered acceptance.

PROPOSED, not implemented. Date:2026-10-27. Based on the42 audit units in
[the audit](PHASE55_UX_AUDIT.md). Preserve all current UI capabilities, API contracts, owned data,
immutable records and safety gates. No Phase6, broker execution or new AI capability.

## Primary navigation

Five user destinations, in the same order on desktop and mobile:

1. **Acasă** — “Ce se întâmplă și ce fac mai departe?”
2. **Testează** — choose reviewed strategy/data/setup and follow real test/import activity.
3. **Rezultate** — stored results, comparisons and read-only causal replay.
4. **Conturi și siguranță** — declared accounts, applied limits, policy review and emergency controls.
5. **Setări** — identity/security/users, sources/catalogs, diagnostics, API reference and About.

Default view is beginner-friendly, not a different authorization mode. “Avansat” changes disclosure
only; it never relaxes validation, source labels, MFA, ownership, quotas or Risk Gateway decisions.
Do not create primary “AI”, “Bots”, “Live”, “Paper” or “Buy/Sell” entries for unavailable capabilities.
Technical scope is regrouped rather than removed. Search, if later added, indexes only authorized
records and documentation; do not promise a global search API that does not exist.

Persistent shell: SIMULARE / ordine externe blocate; current account context where relevant; account
safety status/unknown and a visible link to its STOP controls. Login state is distinct from system
readiness. No overview response is required to mount the authenticated shell or safety entry.
Mobile bottom navigation abbreviates only the visual fourth label to “Conturi”; its accessible name
remains “Conturi și siguranță”. No critical action is hidden behind a “More” menu.

## Proposed route tree

All paths below are design targets. The current application has local React page/tab state at `/`,
not these routes. IDs are opaque owned identifiers; every API still checks the authenticated owner.

```text
/                                      Acasă
/autentificare                         password → MFA/recovery
/configurare-proprietar                one-time administrator/owner bootstrap
/securizare-cont                       enrollment → recovery-code saving

/testeaza                              launch/readiness + recent active tests
/testeaza/strategii                    eight reviewed benchmark definitions
/testeaza/nou                          guided test, review before submission
/testeaza/:experimentId/progres        durable status/cancel + result link
/testeaza/activitate                   queued/running/retry/failed/cancelled history
/testeaza/date                         admitted datasets by market/source/period
/testeaza/date/import                  guided import
/testeaza/date/importuri/:jobId         real import progress/quality outcome
/testeaza/date/:datasetId              data detail/quality
/testeaza/date/:datasetId/previzualizare point-in-time sample
/testeaza/date/:datasetId/provenienta   manifest/availability/source
/testeaza/date/:datasetId/versiuni      immutable version comparison
/testeaza/evaluare-finala               owner-only seal/release index
/testeaza/evaluare-finala/:sealId       frozen review + one-use authorization

/rezultate                             completed experiments; active/failed links to Activity
/rezultate/compara                     two matched completed runs
/rezultate/:experimentId               summary and authoritative outcome
/rezultate/:experimentId/tranzactii     actual stored trades/fills
/rezultate/:experimentId/decizii        proposal → risk → order → fill timeline
/rezultate/:experimentId/validare       OOS/folds/uncertainty/regimes/advanced DSR
/rezultate/:experimentId/provenienta   plan/data/software/cost/risk/attempt manifest
/rezultate/simulari                     separate manual-simulator journals
/rezultate/simulari/:runId/jurnal       manual execution events/positions; read-only

/conturi                               owned declared accounts, add/edit
/conturi/:accountId                    account overview + safety summary
/conturi/:accountId/siguranta           STOP, reviewed CLEAR; link to separate simulated close
/conturi/:accountId/inchidere-simulata  FLATTEN consequences/MFA/remaining exposure
/conturi/:accountId/limite              enforced profile/scopes/versions
/conturi/:accountId/politici            source-document and applicable-risk-policy distinction
/conturi/:accountId/politici/:policyId  exact scope/source/attestation/expiry
/conturi/:accountId/ipoteze             reviewed simulation specification/cost/FX/calendar setup
/conturi/:accountId/verificare-risc     what-if calculator; no order or authorization
/conturi/:accountId/alocari-incidente  open/pending/UNKNOWN allocations and incidents
/conturi/:accountId/conexiuni           simulator identity and demo read-only observation status
/conturi/:accountId/conexiuni/:id/observatii signed evidence and advanced import
/conturi/:accountId/avansat/inregistrari-risc descriptive legacy metadata; not applied
/conturi/:accountId/avansat/simulator/nou    manual synthetic scenario/template
/conturi/:accountId/avansat/simulator/:runId/date   explicit tick/replay/clock
/conturi/:accountId/avansat/simulator/:runId/ordine manual simulated commands/fault/reconcile

/setari                                concise settings index
/setari/aspect                         system/light/dark, locale preference where supported
/setari/securitate                     reauth/password/sessions/recovery guidance
/setari/utilizatori                    owner-only role/access management
/setari/istoric                        immutable audit + owner integrity verification
/setari/surse                          providers/entitlement/attribution and connector instructions
/setari/catalog                       firms/programs/instruments/venues, explicit metadata labels
/setari/registru-tehnic                existing API-only metadata contracts and permitted operations
/setari/diagnostic                     service health, errors, version, last verification
/setari/despre                         capabilities and honest limits
/setari/despre/plan                    development roadmap, not operational activity
```

Static path names such as `compara`, `simulari`, `nou` and `date` must resolve before identifier
patterns. A job route uses the experiment ID returned by the existing API, not an invented second job
identifier. Dataset/import jobs retain their separate IDs and ownership. No financial amounts, raw
JSON, credentials, MFA codes or approval payloads belong in URLs.

## Exhaustive current-state → destination mapping

The left side is an actual App.Page or Management.Tab state, not a fabricated old URL. Additional
paths describe drill-down panels that currently share the same screen.

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

App aliases `market`, `broker`, `riskCenter`, `research` and their Management tabs lead to one
canonical route each. Do not retain duplicate forms or invisible compatibility controls merely to
satisfy old text locators. Update old test navigation intentionally, retaining behavior assertions.

API-only preservation: existing13 governance kinds remain authorized through `/api/v1/records/*`
and their actual immutable/attestation rules. Advanced registry explains which are metadata-only and
links to the existing API contract; no new generic mutation privileges. Advanced DSR uses its existing
owner-MFA endpoint with declared assumptions; no fake confidence UI or ML comparison becomes available.
Signed observations, compare endpoints, exportable stored pages and every advanced manual command
remain available from the above paths with the original guards.

## Beginner and advanced layers

Always visible: purpose, account/currency, execution mode, data origin/quality/scope, applied policy
status/expiry, stopping/unknown state, irreversible consequences, meaningful limits and primary CTA.

Contextual: plain explanations of a strategy, risk basis, costs, missing coverage and OOS. Read them
without leaving the task; help must not conceal errors or mandatory acknowledgement.

Advanced: exact hashes/versions/contracts, source schemas/UTC and availability, cost sensitivities,
parameter sweeps, multi-stream roles, random controls, quotas, raw read-only records, manual simulator
faults and specialized statistics. Expanders retain keyboard names and state. Technical capability is
not removed, automatically altered or falsely certified when collapsed.

Privileged: policy verification, risk change, STOP/CLEAR/FLATTEN, final release, role management and
secret/session actions follow existing backend roles/recent-MFA constraints. These are permissions,
not an “expert mode” switch. VIEWER sees permitted status and explains why owner actions are unavailable;
OPERATOR cannot acquire OWNER power through a wizard. Ownership partitions remain stronger than role.

## Route and state preservation rules

- Keep `/` functional. Existing navigation has no deep-link URLs to redirect; map state entry points
  and test helpers one-to-one. Explicitly document that distinction in migration acceptance.
- Preserve `/api/*`, `/health/*` and `/openapi.json` nginx proxy routes; never intercept them as pages.
  nginx already has SPA fallback, but every proposed deep link still needs direct-load/Back tests.
- Use native links plus a small typed history adapter for these finite routes; no routing package is
  installed or required by this design. Handle popstate, invalid IDs, authorized404, focus and scroll.
- Auth/session lives above routes; sensitive pages still require FULL session and server checks.
  Safe return destinations must be local allowlisted paths; no automatic replay after MFA.
- Account change invalidates incompatible dataset/template/compare selections. Explain the reset and
  ask before discarding safe unsaved input; never mix data from different owned accounts.
- Store no credentials, recovery codes, source payloads or complete financial plans in localStorage.
  Default wizard drafts are in memory; a non-secret allowlisted session draft is optional and scoped
  to user/account, cleared on logout. Server-side drafts are a separate future contract, not assumed.
- Immutable experiment/result URLs survive navigation; rerun creates a new experiment/version with
  reviewed current inputs. Changing settings never edits past evidence or bypasses holdout access.
- Results are owned/protected on direct link, not merely hidden from navigation. Shared/public result
  links are not introduced. A generic403/404 must not reveal another owner's names or counts.

## Reachability acceptance

For each S01–S42, future tests must demonstrate a discoverable path from its primary destination,
an authorized direct-load URL where applicable, Back/reload behavior and a meaningful forbidden or
missing-state outcome. Every mutation retains its existing backend acknowledgement/revision/idempotency.
Audit and detailed evidence stay reachable within two intentional drill-downs from the related result/
account; the number is a design target, not an observed current usability metric.
The implementation plan contains the API matrix and the behavioral regression gate for all 16 scenarios.

## Implemented migration notes

The former local-state navigation is replaced by navigation/routes.ts and history.tsx. All42 IDs
have mapped entry paths; aliases /conturi/siguranta, /conturi/documente, /conturi/conexiuni and
/conturi/avansat/simulator provide safe unscoped selection entries. Risk subsections share a scoped
account workspace; exact policies remain in its version list. Broker observation subsections share
the connection workspace. Deep simulation, dataset, result and import-job IDs use owned reads.
The full case gate is now20, including16 preserved cases and4 new viewport cases.

## Phase6 additive navigation — 2026-10-28

The S01–S42 mapping and five destinations are preserved. New AI analysis is a subordinate
`/testeaza/ai` screen with reloadable owned job links `/testeaza/ai/{id}`; private model/role setup is
`/setari/ai`. Neither AI availability nor a model response authorizes risk/trading. No old route or
action is removed. The suite now collects22 cases (20 preserved + desktop/mobile AI). Execution of
the new gate is blocked here; see PHASE6_COMPLETION_REPORT.md.
