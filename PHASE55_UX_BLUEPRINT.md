# Phase 5.5A — screen blueprint and wireframes

> Phase 5.5B implementation update (2026-10-27): this approved design is now the migration basis.
> See [implementation/acceptance report](PHASE55B_COMPLETION_REPORT.md) and
> [S01–S42 / U01–U24 traceability](docs/ux-migration-coverage.md). Source/native implementation is
> present; browser, visual-baseline and manual accessibility acceptance remain BLOCKED.
> Descriptions below remain the approved design targets; they are not evidence of rendered acceptance.

PROPOSED DESIGN ONLY ·2026-10-27. No implementation, live capabilities or Phase6.
Use with [IA](PHASE55_INFORMATION_ARCHITECTURE.md), [copy](PHASE55_UX_COPY.md) and
[design system](PHASE55_DESIGN_SYSTEM.md). IDs refer to the audited current surfaces.

All diagrams are design wireframes, **not screenshots**. Braced values are data slots, not fabricated
results. The default explains an adult research product in everyday language; it does not target children.
No user testing, current rendered validation or accessibility certification is claimed.

## Shared interaction contract

Desktop: quiet left navigation, scoped breadcrumb/H1, account context and a persistent simulation/
safety strip. Mobile: compact H1/account header, same strip, five labelled bottom destinations and one
content column. Reserve space for sticky actions and device safe areas; focused controls must remain
visible. Global STOP entry opens the selected account's actual controls; no unsupported STOP_ALL.

One task-level primary CTA per screen. Safety actions remain independently visible; their critical
purpose is not demoted to avoid a second button. Contextual subforms may have one local save action.
Loading uses labelled skeleton/status, not invented zero values. Unknown is explicit. Empty data,
filtered-empty, role restriction, unavailable service and forbidden/sealed data have different copy.
Success appears only after the actual API acknowledgement; a pending cancellation is not CANCELLED.

A safe draft may survive navigation in memory. Account/source/version changes invalidate dependent
choices visibly. Reauthentication preserves safe intent, clears secrets and returns to a review step;
it never automatically executes the interrupted mutation. Requests retain idempotency on ambiguous
submission retry. Authentication is mounted independently of the public overview response.

## B01 — Home: answer five questions immediately (S01–S05,S28,S37,S38)

Purpose: know availability, current work, stored results, attention and next action without learning
infrastructure. Primary CTA is the next legitimate task, derived from real owned state.

Desktop:
```text
Acasă               Cont: {cont selectat}       [Contul meu]
[SIMULARE · ordine externe blocate] [Siguranță: {stare} →]
{Sistem disponibil / verificare indisponibilă} · verificat {ora}
{Titlu următor pas}                              [Acțiune principală]
{O propoziție care explică pasul}
┌ Necesită atenție ─────────────────────────────────────────┐
│ {problemă reală sau niciuna} · {consecință} [Vezi problema]│
└───────────────────────────────────────────────────────────┘
În lucru: {test/job real sau Nu rulează teste} [Vezi progresul]
Rezultate recente: {titlu, sursă, fază, rezultat stocat} [Vezi]
[Date pentru teste]                 [Stare și diagnostic →]
```
Mobile:
```text
Acasă       {cont} [Siguranță]
SIMULARE · ordine externe blocate
{Stare + ultima verificare}
{Următorul pas}
[Acțiune principală, lățime completă]
{Atenție / fără probleme raportate}
{Test în lucru →}
{Rezultat recent →}
Acasă | Testează | Rezultate | Conturi | Setări
```

Five answers: status comes from actual dependency checks; doing comes from durable jobs; results from
owned completed experiments; attention from explicit invalid/expired/stopped/error states; next action
from prerequisites. These are separate dimensions. Available services do not mean trading enabled.
No active job does not prove a worker is healthy. Unknown worker readiness must say unknown.

CTA precedence: critical attention → “Vezi problema”; unauthenticated → “Autentifică-te”; no setup →
“Pregătește primul test”; ready/no job → “Testează o strategie”; running → “Vezi progresul”; new result
→ “Vezi rezultatul”. CLEAR_STOP is never the Home recommendation or automatic recovery.

States: public signed-out Home exposes mode/public health only; no owned balances/counts. First use
shows a small readiness list. Active work shows real status/observed progress with no invented ETA.
Outage retains prior values marked stale plus last verification; no green assurance or offline STOP
success. Remove static25k capital/“checkpoint02” from the normal financial summary. Reference examples
remain labelled under About. Real aggregated account P&L is not inferred by summing unrelated backtests.

Data reuse: overview/health, authenticated research list/detail, owned accounts and risk statuses.
Worker heartbeat/last-change precision is an explicit API gap in the implementation plan.

## B02 — Guided research: six understandable steps (S24,S29–S31,S35,S36)

Primary flow: **Market → Strategy → Period → Reviewed setup → Review → Start**. “Start” is a separate
explicit confirmation, not a side effect of selecting a dropdown. Default engine is actual event
validation; exploratory screening is an explained Advanced choice with no promotion authority.

Desktop:
```text
Testează pe date istorice              SIMULARE
1 Piață — 2 Strategie — 3 Perioadă — 4 Siguranță — 5 Revizuire
┌ Pasul {n}: {scop} ─────────────────┐ ┌ Rezumat ───────────────┐
│ {alegeri disponibile și eligibile} │ │ Cont / monedă          │
│ {de ce lipsește o opțiune}         │ │ Date / sursă / versiune│
│ [? Explicație simplă]              │ │ Strategie / perioadă   │
│ [Avansat ▸]                       │ │ Limite / costuri / fază│
└───────────────────────────────────┘ └─────────────────────────┘
[Înapoi]                                          [Continuă]
```
Mobile:
```text
Test nou · Pasul {n} din5
{Scopul pasului într-o propoziție}
{Opțiuni în listă, fără coloane}
{Condiție lipsă + link de pregătire}
[Rezumatul alegerilor ▾] [Avansat ▸]
[Înapoi]                     [Continuă]
SIMULARE · ordine externe blocate
```

Step1: select a market/instrument from actual accessible datasets. Show range, timeframe, origin and
quality. No available VALID history → “Adaugă date istorice”; do not display a synthetic substitute as
real history. Account context is explicit, selected early if multiple source accounts exist.

Step2: strategy cards explain what triggers entries/exits and what market behavior they test. Show
supported data and “Etalon experimental, nu strategie recomandată”. Preserve exact registry ID/version/
source digest in details. No AI-created strategy box, fake ML filters or unsupported broker availability.

Step3: select within actual admitted coverage, with visible UTC dates and local timezone rendering.
Explain discovery/calibration/OOS portions before launch. Ordinary flow never accesses sealed final
rows. Chronology/purge/embargo are actual constraints, not decorative timeline percentages. Preserve
server checks; label estimates if exact selected-row counts cannot yet be fetched.5000-row/300-second/
trial quotas remain visible in the review; no silent truncation, interpolation or five-year assumption.

Step4: choose an **existing owner-reviewed** profile and compatible template/context/policy version.
Show initial simulated capital, currency, amount-at-risk examples, daily/total bases/reset, restrictions,
source facts and explicit cost assumptions. “Use reviewed default” exists only if that account really
has a current reviewed eligible version. Otherwise link to setup; never pre-attest or substitute a
looser rule. Automation permission must remain explicit; a fixed algorithm is not relabelled manual.

One-time setup branch: account → admitted data/source → explicit symbol/cost/calendar/FX/margin facts →
profile/policy → owner review/recent MFA. The ordinary user should not type contract JSON, but missing
expert facts must block the test with an understandable explanation. An administrator may prepare a
reviewed version; the beginner selects it, rather than granting it authority by accepting a preset.
Current APIs have no general reusable preset entity; only existing verified template/context selection
is assumed initially. A new preset contract would need separate explicit implementation/review.

Step5 review: market/source/version/coverage, strategy/parameters, chronology and sample phase, risk
account/profile/policy scope, costs/unknown funding, engine limitations and quotas. Show exactly what
is acknowledged. Costs cannot be reduced to a “yes” toggle if some components are zero/unknown/modeled.
Start CTA: “Pornește testul în simulare”. Keep current MFA and explicit clone/research/cost acknowledgements.

Advanced preserves all existing controls: indicators, direction, volume/SL/TP, holding/session buffers,
pending types/expiry, signal timeframe, EXECUTION/SIGNAL/CONFIRMATION/FX pins, sweeps/cost stress,
random-entry controls/seed, validation mode/folds/purge/embargo, quotas and strict JSON import/export.
Validate advanced input as the same typed contract; no code execution or silent parameter changes.

On submit: retain one request key while outcome is ambiguous; await real202/409. Refresh existing job
on duplicate, not a second submission. Successful submission opens the real stable progress URL.
Failure returns to the relevant step with the safe draft intact and a next action; eligibility is
revalidated by the API and worker even after a successful preview.

## B03 — Experiment progress and history (S19,S37)

Desktop:
```text
{Numele testului}                 SIMULARE
{În așteptare / În lucru / Reluare / Finalizat / Eșuat / Anulat}
{Progres raportat de server; fără estimare inventată}
{Configurație fixată}   {Încercarea reală}   {Actualizat la}
Pași cunoscuți: date → simulare → publicare (numai dacă disponibili)
{Costuri/limite/sursă}                       [Solicită anularea]
[Detalii tehnice ▸] [Înapoi la activitate]     [Vezi rezultatul]*
* numai după rezultat complet publicat
```
Mobile:
```text
{Test} · SIMULARE
{Stare} · {progres observat}
{Ce înseamnă și ce urmează}
[Solicită anularea]
[Setările testului ▸]
[Detalii tehnice ▸]
[Vezi rezultatul] numai după confirmare
```

Use only observed progress/state. Do not infer three independent job stages from a single percent;
when detailed stages are unavailable show one honest progress line. Activity has filters for actual
states and source/market, plus links to failed/cancelled records; history is not deleted to tidy the UI.
Until an actual server update timestamp is exported, replace “Actualizat la” with “Verificat de
interfață la {ora}”; a client read timestamp must not imply the worker recently made progress.
Cancellation: request acknowledgement → “Anularea a fost cerută” → actual CANCELLED; SUCCEEDED may win
a completion race, so show the actual result/status. No optimistic success or accepted partial result.
Worker retry remains the same frozen experiment with a new attempt, not a new independent hypothesis.

Failure detail: what happened, whether a result exists, why nothing incomplete is accepted, one suitable
next action and safe diagnostic code/correlation. A new test after changed inputs creates a new record.
An uncertain submission asks to check existing activity before retrying with the same idempotency key.
Progress remains accessible on reload/Back after authentication; no private data before FULL session.

## B04 — Results: plain meaning before metrics (S38,S39)

Desktop:
```text
{Test} · {strategie} · {perioadă}       [Compară] [Datele testului]
SIMULARE | {date istorice declarate / sintetice} | {fază}
{Rezultat descriptiv bazat pe valoarea netă, fără verdict de eligibilitate}
{Câștig/pierdere netă}  {Cea mai mare scădere}  {Tranzacții}
Costuri: {componente} · Date: {acoperire/limite} · Validare: {tip}
┌ Capital simulat: timp UTC × monedă ─────────────────────────┐
│ {curbă din valori stocate; interval și eșantionare explicite}│
└─────────────────────────────────────────────────────────────┘
[Capital | Scăderi] [Valori exacte]
{Ce știm}                          {Ce nu putem concluziona}
Sinteză | Tranzacții | Decizii | Validare | De unde provin datele
[Analizează o variantă nouă]          [Statistici avansate ▸]
```
Mobile:
```text
{Test} · SIMULARE · {origine} · {fază}
{Modificare netă în monedă și %}
{Cea mai mare scădere} · {număr tranzacții}
{Costuri / acoperire / avertisment}
{Grafic cu axe și unități}
[Valori exacte]
Sinteză | Tranzacții | Mai multe detalii*
{Concluzii descriptive / limite}
[Analizează o variantă nouă]
* meniu local etichetat pentru toate cele cinci secțiuni
```

Meaning: net gain/loss after specified costs; maximum observed equity decline from an earlier peak;
actual round trips; cost components; observed coverage and quality; discovery/calibration/validation/
final-release phase; which statistical summaries are absent and why. A positive result is not “a
profitable strategy”. Drawdown is not maximum possible future loss. Unknown must never display as0.

Costs show observed tick spread versus modeled bar spread, declared fees/slippage/funding and stress
scenario. No implicit “all costs included” if funding is unknown. Equity/drawdown chart uses stored
marks/metrics; display sample never recalculates authoritative maximum loss. If the API does not
supply a full drawdown series, label a displayed sampled trace approximate or add a reviewed read-only
series API; do not manufacture an authoritative curve from500 display points.

Statistical meaning is not a traffic-light score. Show sample size, temporal coverage, OOS boundaries,
null reasons and uncertainty intervals with assumptions. A computed ratio is not proof of significance.
No automatic “passed research” threshold or paper CTA exists without a separately implemented gate.
Explain purged/embargoed folds, training selection and all attempted configurations including failures.
DSR remains advanced, owner-MFA and explicitly assumption-dependent; independence is never guessed.

Trades: readable actual entries/exits/fees/holding with source-clock caveats. Replay: signal → gateway
ALLOW/DENY/INDETERMINATE → command → actual fill/partial/exit. ALLOW is not a fill. Exact values, IDs,
risk versions and provenance remain downloadable/readable under the same ownership/holdout rules.
Downloading is a proposed UI action over existing stored reads, not a new signed performance report.

## B05 — Comparison (S40)

Desktop:
```text
Compară două teste                         [Alege testele]
Test A {nume}                 Test B {nume}
{Condiții potrivite / incompatibile + motiv verificat}
Date · interval · costuri · risc · software: {identice / diferență}
{Rezultat A}                  {Rezultat B}
{Scădere / tranzacții / cost / OOS / limite pentru fiecare}
{Curbe în aceeași monedă și scară, numai dacă sunt comparabile}
[Condiții și ipoteze ▸]       [Revino la rezultat]
```
Mobile:
```text
Compară teste
{Eligibilitate și motiv}
{Metrică}       A {valoare}   B {valoare}
{Metrică}       A {valoare}   B {valoare}
{Limită A} / {Limită B}
[Curbe etichetate] [Date exacte]
```

Match according to the actual compare endpoint, including data pins, chronology, risk approval,
costs and software. Strategy/parameters may differ where the API permits. Frontend previews explain
mismatch but never override409. The server currently returns a generic mismatch string; a precise
condition diff is a proposed read-only contract improvement, not assumed available.
Do not rank by a combined “best” score. Surface net result, drawdown, sample/phase and uncertainty;
selection from many runs remains a multiple-testing risk. No ML/LLM/hybrid series with fake zeros.
CTA becomes “Vezi de ce nu se pot compara” for an incompatible pair, not a forced normalized comparison.

## B06 — Accounts and connection identities (S10,S22,S23)

Desktop:
```text
Conturi și siguranță                         [Adaugă cont pentru simulare]
{Cont / monedă / capital declarat} {Siguranță / politică / sursă}
{Cont / monedă / capital declarat} {stare verificată sau necunoscută}
Selectat: {cont}
Sinteză | Limite | Politici | Conexiuni | Alocări/incidente | Avansat
Capital declarat, nu sold broker | {restricții și ultima verificare}
[Vezi siguranța contului]                    [Editează configurația]
```
Mobile:
```text
Conturi · SIMULARE
[Adaugă cont pentru simulare]
{Cont} · {monedă} · {siguranță}
{Capital declarat / politică / verificare}
[Vezi siguranța]
[Limite] [Politici] [Conexiuni] [Avansat]
```

No actual broker balance is inferred from the reference capital. Changing account identity/currency/
program prompts consequence review and respects revisions/approval invalidation. Empty-state create
is role-aware; VIEWER sees an explanation rather than a dead save button.
Connection identity, signed latest observation and external capability are three separate states.
Registration is not connectivity. Snapshot verification/staleness, observed symbols/quotes/positions
and orders stay available, with demo/source labels and “numai citire”. Never request private MT5/OAuth
credentials centrally. Advanced signed imports/manual simulator preserve their exact restrictions.

## B07 — Risk controls and policies (S11,S12,S28–S34)

Desktop:
```text
Siguranță · {cont exact} · SIMULARE
{Intrări oprite / necunoscut / permise în simulator} · {verificat la}
{Per tranzacție / zi / total / risc deja alocat} în {monedă}
{Bază, interval de resetare și politică aplicată, cu expirare}
[Oprește intrările pentru acest cont]          mereu ușor de găsit
[Revizuiește oprirea]   [Închiderea pozițiilor simulate →] separate
Limite | Politici/documente | Ipoteze | Calculator | Alocări/incidente
{Explicație în bani}                          [Revizuiește limitele]
[Versiuni, surse și calcul exact ▸]
```
Mobile:
```text
Siguranță · {cont}
{Stare + momentul verificării}
[Oprește intrările pentru {cont}]
{Limită per tranzacție în bani}
{Limită zilnică / totală + bază/reset}
{Risc alocat / incert / incident}
[Revizuiește limitele]
[Închide pozițiile simulate →] separat
```

Limits: simple currency examples plus exact percentages/basis, static/trailing definition, reset
IANA timezone and restrictive scopes. Example only:25,000USD ×0.25%=62.50USD before exact fees/sizing;
that is an explanation, not a saved reviewed limit or guaranteed loss cap. The actual gateway performs
Decimal sizing, margin, group/pending exposure and final checks. No UI calculator authorizes orders.

Policies: show document verification separately from enforced policy. Include exact firm/program/
phase/platform/account revision, effective/expiry, permitted automation/style/symbols/session/news and
required evidence. “Reviewed” is never a brand-wide trading permission. Legacy descriptive risk records
stay accessible in Advanced and clearly marked “nu se aplică”; no automatic conversion or duplicate
ordinary profile editor. Financial facts still need explicit reviewed source/context versions.

STOP: name account, explain no closure, require existing owner/recent-MFA/ack/revision behavior; success
only after real response. CLEAR: separate reviewed readiness flow, never an automatic “fix”. FLATTEN:
separate consequence review listing simulated exposure, uncertainty and unfilled outcomes; require
MFA/explicit simulated-only acknowledgement. Never promise real positions will close. MONITOR remains
a separately labelled status refresh, retaining its actual endpoint permission.

An API outage cannot produce an optimistic emergency acknowledgement. Preserve draft scope but do
not queue mutations offline. If a recent-MFA prompt interrupts, return to review and require a fresh
explicit confirmation. Do not hide uncertainty or remaining exposure inside technical diagnostics.

## B08 — Data management/import (S16–S21)

Desktop:
```text
Date pentru teste                                   [Adaugă date istorice]
{Piață} {perioadă observată} {origine} {calitate} [Vezi]
Detaliu: {utilizabil pentru acest scop / necesită verificare / blocat}
{Goluri / calendar / disponibilitate / volum necunoscut / eșantion}
[Previzualizează]  [De unde provin datele]  [Versiuni]
Import: 1 Sursă → 2 Fișier/date → 3 Verificare → 4 Rezultat
[Avansat: schemă, timezone, calendar, hash ▸] [Continuă]
```
Mobile:
```text
Date pentru teste
[Adaugă date istorice]
{Piață · interval · origine}
{Calitate și motiv}
[Vezi datele]
Import pas cu pas
{Problemă concretă + corectare}
[Continuă]
```

Default import uses an already configured entitled source or a file with a guided column preview.
Infer candidate mappings only as suggestions; confirm original timezone, session calendar, symbol and
meaning of event/observation/availability. Missing timestamps or DST ambiguity cannot be filled from
clock guesses. Never set historical availability equal to event time without valid source evidence.
If the current import contract cannot represent a source, refuse clearly; a mapping/validation preview
is a future implementation, not a backend feature assumed present today.

Owner/provider rights and attribution are prepared once under Sources, with explicit review, not a
checkbox automatically accepted by a wizard. CSV/Parquet schema and provenance remain inspectable,
not ordinary prerequisite vocabulary. ECB route explains daily reference-only rates, no execution
bid/ask/volume. Explicit synthetic practice data stays labelled on every output.

Quality feedback groups blocking errors, review warnings and descriptive coverage. Point to exact
rows/fields only if actual diagnostics provide them; otherwise offer schema/sample troubleshooting.
VALID does not prove five-year/tick completeness. DEGRADED sample viewing never enables research.
A protected window shows access restriction without leaking rows or bypassing the owner-wide seal.
Progress/cancel/version publication reuse B03 patterns; datasets remain immutable and revisions create
new versions with reasons. Original data and manifests are never overwritten for convenience.

## B09 — Settings/diagnostics (S03,S05,S21,S42)

Desktop:
```text
Setări
Aspect                  [Sistem / Luminos / Întunecat]
Securitate și acces     [Securitate] [Utilizatori, doar proprietar]
Surse și catalog        [Surse] [Firme/programe/instrumente/locuri]
Istoric și diagnostic   [Istoric verificabil] [Starea serviciilor]
Despre versiune         [Capabilități] [Plan de dezvoltare] [Contract API]
```
Mobile:
```text
Setări
Aspect →
Securitate →
Utilizatori → (rol explicat)
Surse și catalog →
Istoric verificabil →
Diagnostic →
Despre și contract API →
```

No one global save for unrelated settings. Theme is a local preference, not a server permission.
Romanian remains the only complete product locale until an actual translation catalog exists; do not
show an English toggle leading to partial untranslated flows. Diagnostics provides service names,
last check and safe failure/correlation data, not leaked DSNs/tokens. Retry is a real read refresh;
restart/deploy buttons are not invented. Roadmap displays future AI/paper as planned only.
All API-only metadata remains reachable as documented technical contracts, not falsely enabled flows.

## B10 — Security, onboarding and immutable audit (S06–S09,S13–S15)

Desktop:
```text
Securitate · {identitate și rol}
Autentificare în doi pași: {stare} [Instrucțiuni]
{Acțiune sensibilă cere reconfirmare aici, în context}
[Schimbă parola]  [Închide toate sesiunile] (consecințe explicite)
Istoric verificabil      [Filtre permise] [Verifică integritatea]*
{Ce s-a întâmplat · când · actor/rol · cont · MFA}
[Date tehnice originale ▸]                       *proprietar
```
Mobile:
```text
Securitate
{Identitate / rol / MFA}
[Acțiunea aleasă + consecințe]
{Parolă/cod în flux separat}
Istoric verificabil
{Eveniment în limbaj simplu}
{Moment · cont · actor · MFA}
[Detalii exacte ▸]
```

Login: password manager and paste assistance; clear step “Parolă” then “Cod de autentificare”. Setup:
private owner bootstrap remains explicit; no public signup, auto-discovered secret or changed owner
credentials. Enrollment may add a locally generated QR from existing provisioning URI, alongside a
manual key; no third-party QR service. Recovery codes are secret, one use, shown/saved deliberately.
No OTP/password persistence or screenshots/traces containing enrollment/recovery material.

Recent MFA: explain why, preserve only safe task context and clear secrets. Password change/session
revocation/user-role/access changes review affected scope and require existing server authority;
no newly offered credential reset factor or permission. Owner-only user management remains separate
from personal Security. Cancel returns to the originating task without executing it.

Audit: readable event summaries, original enum/sequence/correlation and authorized before/after details,
with redaction policy intact. Integrity check says what the HMAC proves and that trusted host/DB admins
are still within the threat boundary. No deleting/rewriting/“clean history” action. Search/export require
actual available bounded contracts and ownership; future read filters are identified in the plan.

## Dedicated final evaluation (S41; a guarded branch, not a beginner step)

From Testează → Evaluare finală, only an authorized owner can initiate an intentional seal/release.
Show exact dataset/window/account, loss of ordinary access, frozen strategy/parameters/risk/software,
no repeated tuning, UNKNOWN prior exposure and a separate single-use acknowledgement/MFA review.
Do not preview protected rows to help the user choose them. Sealing is not proof of prior blindness.
Invalid configuration must not consume a release; preserve transactional backend preflight semantics.
The result is still SIMULATED and paper_eligible=false. Mobile presents the same consequences before
the final CTA, not a truncated dialog. Full raw contract is inspectable but not mandatory JSON entry
in the future guided UI. Nothing in this design implements stronger independent vault custody.

## Definition of design success, to test later

A representative adult novice can locate a legitimate next step, complete a prepared historical test,
identify simulated versus observed data, explain net change versus maximum historical decline, find
insufficient-data warnings and distinguish STOP from FLATTEN. These are proposed test tasks, not study
results. Record observed errors/comprehension, not only completion time. Run an advanced-user session
to prove every mapped capability remains discoverable, plus manual keyboard/screen-reader/mobile review.

## Implemented screens and remaining validation

B01–B10 now have source implementations in App/HomePage, StrategyLab, ResultView, Management,
RiskCenter, EmergencyActions, BrokerCenter and MarketData; see the coverage map. Primary research
uses five form steps plus explicit Start. FinalEvaluation is a separate guarded branch with reviewed
frozen configuration and explicit registration after release. Diagram slots above are still wireframes,
not screenshots. No current visual/manual acceptance is implied.
