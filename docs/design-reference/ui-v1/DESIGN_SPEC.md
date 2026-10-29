# AI Trading — Phase 6.5 / Design V1: Visual Specification

**Status:** USER-APPROVED VISUAL DESIGN REFERENCE. Implement only after baseline verification.  
**Scope:** UI/UX implementation across Phases 0–6; not Phase 7, not trading execution.  
**Language:** Romanian primary.  
**Visual sources:** `references/00_HOME_MASTER_1672x941.png` (primary, high-resolution Home) and `references/01_ALL_TABS_CONTACT_SHEET_1536x1024.png` (nine pages). The 9 cropped references are convenience crops, not separate generated high-resolution designs.

## Core directive: 1:1 visual fidelity without fake facts

Implement the *visual design language, placement, density, component hierarchy, silhouette, card geometry, navigation, and page-specific compositions* as faithfully as possible to the approved mockups. Do not reinterpret into a different aesthetic. Treat marketing-like or imaginary screenshot content as layout examples ONLY. All product labels, numerical values, connected models, experiments, research outcomes, job counters, PnL/equity, and security statuses in the images are fictional illustration and MUST NOT be hardcoded into a production UI. Avoid an unearned green overall status. Preserve true backend API semantics, source/provenance/risk qualifiers and explicit unknown/no-data states. Where mockup claims conflict with real capabilities or security, the app's technical and safety contract wins, while preserving card position and visual design.

The Home master is 1672×941, highly detailed; the nine-tab sheet is 1536×1024 with 3×3 *small* panels. These are concept images, not guaranteed pixel-correct frontend output or measured design tokens. Match visually at 1672×941 first, then 1440×900, 1280×800; implement responsive mobile designs grounded in the existing tested application (390×844 and 360×800). Avoid pretending pixel-for-pixel exact equivalence at every resolution, font rasterizer or data state. Screenshot review by human is required.

## Fidelity priorities — STRICT

1. **Palette and shell:** full-height dark navy left sidebar, white/off-white canvas, top light navbar, slightly tinted pale bordered cards, royal blue primary actions, violet accents, restrained green/warm amber/red statuses. No full-dark content overhaul or glassmorphism redesign.
2. **Composition:** sidebar approx. 256px of 1672px; main canvas with approx. 20–24px inset/gaps; topbar approx. 66–70px; header title/subtitle and tools; consistent 12–16px rounded panels; gentle 1px borders and subtle shadows. These are starting estimates to calibrate by visual overlay, not arbitrary mandatory measurements.
3. **Typography:** modern neutral sans, strong dark navy headings, 14–16px main labels, supporting text 12–14px where accessible, aligned numeral labels, no tiny unreadable text from generated collage. Do not add paid fonts or remote fonts by default; use existing typography or an appropriate system fallback.
4. **Icons:** thin line icons in predictable sizes with colored circle backplates; consistent icon language. Reuse existing icon infrastructure or a small compatible icon set, avoiding heavy new dependencies.
5. **Sidebar:** brand `AI Trading / Research Platform` at top; exact five main destinations: `Acasă`, `Testează`, `Rezultate`, `Conturi și siguranță`, `Setări`. Hierarchical submenu under Testează: `Strategii`, `Backtesting`, `Experimente`, `AI Center`. Under Setări: `Modele AI`, `Conexiuni`, `Date și piață`, `Simulator`, `Utilizatori și acces`, `Sistem`, etc., as existing functionalities require. Active item royal-blue pill. Slim system-status section low in sidebar. Small phase label near footer if real, never a fake progress claim.
6. **Topbar:** global search (only functional if backed by actual accessible search; else implement scoped functional search or clearly inactive explanatory state), notifications with real unread state only, help, light/dark theme, authenticated avatar. No fabricated notification count.
7. **KPI cards:** rounded pastel tiles in one desktop row; icon on left, clearly defined metric title/value/microcopy. Substituting honest metrics is allowed while preserving positions/dimensions.
8. **Tables/charts:** financial chart with time axis, currency, units, accessible exact-value alternative; softly filled line. Clear small status chips. No fabricated multi-experiment equity aggregate, no cherry-picked sample to imply portfolio returns.
9. **Right-column tools:** AI assistant card, contextual actions, safety checks. Keep polished two-column split where shown, approximate ratio of wide 2/3 main and narrow 1/3 sidebar, not arbitrary remapping.
10. **Bottom flow:** horizontal 6-stage process in Home: `Date` → `Strategie` → `Risc` → `Testare` → `Rezultate` → `AI`, with numbered step cards and connectors. Checkmarks/status only if actual prerequisites met. Mobile becomes scrollable/reflowed step list; never imply real AI is configured when it is not.

### Suggested initial design tokens — calibrate against image and screenshots

```
--nav-bg: #17203b;            /* sampled approximation */
--nav-bg-deep: #111a33;
--nav-selected: #2f5ecf;      /* sampled approximation */
--page-bg: #f7f9fe;
--surface: #ffffff;
--surface-soft: #f9fafe;
--line: #dfe5f3;
--ink: #17233e;
--muted: #64718a;
--primary: #305fec;
--violet: #6255e8;
--positive: #098e49;
--negative: #c93043;
--caution: #a96d03;
--radius-panel: 14px;
--radius-control: 9px;
--sidebar-w: 256px;
--content-gap: 16px;
```

These colors are a **visual target**, not an instruction to replace any existing accessible token without contrast testing. Derive light/dark theme token sets. The approved references show primarily **LIGHT main content with DARK sidebar**.

## Page 1 — Home (`00_HOME_MASTER_1672x941.png`)

Exact spatial sequence:
- Persistent navy sidebar left, topbar above canvas.
- `Acasă` heading with short subtitle.
- 4 horizontal KPI cards: experiments, strategy library, meaningful validated-outcome/readiness metric, scoped risk. **No misleading `Rată medie de succes` across unrelated backtests**. A truthful substitute such as `Experimente finalizate` occupies the third card without changing composition.
- Main large left panel with **one selected experiment's** real stored equity timeline plus metric summary, not a synthetic average of unrelated research experiments. If none exists: designed empty state in same card geometry with CTA.
- Right top AI assistant card with role/model availability, suggested questions, prompt input, submit button. If model not verified, disabled/`Neconfigurat` and clear setup link; never show `Ollama online` by default.
- Below left: recent experiments compact table with real rows. Below near center: safety and scoped risk limits card. Below right: next actions grounded in actual readiness, not invented personal to-dos.
- Bottom full-width six-step research flow card.
- `SIMULATED / DENY_ALL` indicator must remain visible and legible. Service health and risk authorization are different states.

## Page 2 — Testează > Strategii (`02_testeaza_strategii.png`)

- Header `Strategii`; four compact KPI cards only with defensible counts (available fixed strategies, versions, filters etc.).
- Filters as rounded tabs: `Toate`, `Trend`, `Mean Reversion`, `Breakout`, `Sesiune`, when supported by real strategy categories.
- Rounded table/list: icon; human-friendly strategy name and one-line description; category pill; tested version/last reviewed; availability; right action to inspect/test.
- Eight Phase 5 fixed reviewed baselines are explainable as a library, **not eight active real-money strategies**. No claims of live activation or profitability.
- Strategy detail drawer/panel: how it works, inputs, data compatibility, version, limitations, CTA `Testează pe date istorice`; advanced immutable IDs/digests accessible.
- `Strategie nouă` button must not imply code execution if arbitrary strategy creation is not supported: show `Planificat`/`Propune o idee` (inert text proposal) or approved actual existing feature without falsifying state.

## Page 3 — Testează > Backtesting (`03_testeaza_backtesting.png`)

- Left vertical configuration card with market, reviewed strategy, period, timeframe, simulated starting capital/context, costs/risks, review, main blue action.
- Right large card switches state: before run = **review/readiness panel with no invented equity/PnL**; while running = actual job/progress (no fake ETA); after completed = stored chart, KPIs, checks, link to full result.
- All prerequisites remain enforced and linked: VALID admissible dataset, real time/cost/session contract, account, reviewed financial context, verified applicable automation/risk policy, owner permissions, holdout rules.
- Advanced accordion retains sweeps, portfolio, OOS, walk-forward, roles, embargo, quota settings.
- Adapt to existing Phase 5 backend quotas (do not imply 5 years of tick history is already usable).

## Page 4 — Testează > Experimente (`04_testeaza_experimente.png`)

- Four truthful summary cards; filters/search; high-density rounded experiment table; stage/result/status chips and overflow actions.
- Show queue/running/failed/completed/cancellation requested/cancelled separately. Cancellation is a request until confirmed.
- Every row goes to a stable experiment detail route; preserve immutable pinning, data/source/version and replay links.
- Do not confuse AI jobs with backtest experiments; label separate types if shown together.

## Page 5 — Testează > AI Center (`05_testeaza_ai_center.png`)

- In-content tabs if supported by current flows: `Asistent`, `Roluri și modele`, `Jurnale`, `Evaluare` (only implemented operations may appear actionable).
- Two-column layout: left conversation/research question with sourced/qualified structured answer; right model-role list and real usage limits.
- Models Research/Coding/Critic/Lightweight, each true connection/probe state. AI text is not executed and never attributed to a verified expert.
- Prompt field and suggested requests allowed only when configured and authorized; otherwise clear empty setup state with source-safe explanations.
- Context selections must be reviewed and owner-scoped; sealed holdout content unavailable. Avoid faux streaming, model tokens, quality scores, or `online` chips.
- Existing routes `/testeaza/ai`, `/testeaza/ai/{id}`, and `/setari/ai` must keep working; route discovery for other tabs must use actual source.

## Page 6 — Rezultate (`06_rezultate.png`)

- KPI row from **selected completed stored experiment**, NOT a cross-experiment average: net simulated change, profit factor (when defined), win rate (when defined), max drawdown, all qualified by costs/data origin.
- Wide left time-series equity chart with explicit currency/time units, source, sample disclosure; right doughnut win/loss distribution ONLY if enough actual trades.
- Bottom comparative table of eligible runs; API matching eligibility and comparability must be enforced, explaining refusal (`409`) without invented normalization.
- Drill-down views for trade replay, folds, statistical uncertainty, fees, data source/provenance, and final sealed holdout restrictions.
- Avoid implying the curve represents a real brokerage balance or aggregated wealth.

## Page 7 — Conturi și siguranță (`07_conturi_siguranta.png`)

- Tabs: `Conturi`, `Limite de risc`, `Politici Prop Firm`, `Monitorizare`, `Incidente` with server-reality mapping.
- Left selected account list with account type and provenance. Middle panel with capital explicitly *declared simulation capital*, actual applied risk limits and statuses. Right panel with **three distinct controls**: STOP_NEW_ENTRIES, reviewed CLEAR_STOP, simulated FLATTEN; clear consequences, confirmation, recent-MFA as needed.
- All important states visibly differentiate `SAFE/VERIFIED`, `UNKNOWN`, `STALE`, `UNCONFIGURED`, `STOPPED`, `UNAVAILABLE`; actual backend categories take precedence over marketing-colored badges.
- Descriptive legacy risk metadata must never be labelled active enforcement. Account/program scope and incomplete pagination cannot be concealed.
- Live/demo order capability must stay DENY_ALL; `FLATTEN` never claims to liquidate real positions.

## Page 8 — Setări > Modele AI (`08_setari_modele_ai.png`)

- Compact header and tabs `Modele`, `Roluri`, `Conexiuni`, `Limite și consum`.
- Data table: configured model, provider, verified context, supported capability, probe/expiry, actual connection state.
- Bottom role assignment cards, one each for Research/Coding/Critic/Lightweight.
- Connection form and advanced settings use secure existing owner-scoped gateway; no embedded endpoint token/secret visible or browser-stored.
- No model can be shown connected if Ollama discovery and real inference have not been verified.
- `Adaugă model` is a genuine configuration wizard (not a model download or cloud GPU purchase).

## Page 9 — Setări > Platformă (`09_setari_platforma.png`)

- Nested tabs/grouped settings: Date și piață, Brokeri, Simulator, Utilizatori și acces, Sistem; include integrations, owner security/MFA, audit and any remaining Phase 0–6 advanced feature. Keep all 42 preexisting feature paths and Phase 6 additions reachable.
- Two aligned card columns as mockup: left provider/source list, right selected settings form with validation and review/commit. Persist using existing APIs, no illustrative toggles with no backend action.
- Distinguish technical service up/down, data completeness, source quality, broker read-only observations and execution authority.
- Preserve source checksums/versioning, import entitlement acknowledgements, exact currency/timezone/volume semantics, no silent auto-repair of market history.

## Shared interaction specs

- All sidebar tabs, sub-tabs, breadcrumbs, theme toggle, real search, filter chips, sorting, tables, chart selectors, modals, CTA and navigation must work. No decorative dead buttons.
- Preserve stable deep links, browser Back/Forward, reload, role authorization, recent-MFA, CSRF, idempotency, cancellation semantics, and existing Phase 5.5 navigation conventions.
- Empty state: same card footprint, dignified icon, explicit `Nu există încă ...` and a contextual CTA; don't backfill screenshot numbers.
- Loading state: unobtrusive skeletons with accessible labels, safe no-data interpretation.
- Errors: WHAT failed / WHAT it affects / NEXT safe action. No raw secrets/errors.
- Disabled controls: visible reason, not just disabled hover tooltip.
- Long tables: horizontal or mobile card reflow; no loss of action discoverability.
- Mobile: accessible 5-destination bottom nav or equivalent tested existing design, top context tools in compact row, charts with exact-value fallback, KPI rows become two-up/one-up, sidebar becomes manageable accessible navigation; never squeeze desktop content to illegibility.
- Keyboard/screen reader: focus order, aria-labelledby/description, popup focus restoration, Escape, 44px target intent, 200% zoom/reflow, non-color warning labels, contrast tests; don't capture MFA or authentication secret states in screenshot baselines.

## Visual implementation QA / acceptance

### Gate 0 — Baseline

`make check`, `make integration`, `make contracts-check`, `make smoke-demo`, `make secret-scan`, `make repository-check`, and owner-local browser tests must be recorded. Preserve existing developer DB volumes and screenshots, and do not rewrite financial engine or AI network boundaries.

### Gate 1 — Component fidelity

Compare completed **real browser** captures at chosen desktop viewport with approved visual references. Review navbar, card positions, widths/heights, spacing, icon scale, typography, chart geometry, palette, shadows/borders, active nav, overall density. Do not pass by using the reference as a background image. Inspect with overlay/difference images. Render dynamic data fixtures for screenshot tests with fixed, honest `TEST FIXTURE` flag; production pages use APIs.

### Gate 2 — Per-page functionality

A matrix must cover all 9 reference pages and every visible control. Mark each as FUNCTIONAL / DISABLED-WITH-REASON / DESIGN-ONLY-APPROVED. No inert button or fabricated status passes unnoticed. Document route mapping and original S01–S42 preservation, including Phase 6.

### Gate 3 — Security and financial truth

SIMULATED/DENY_ALL, risk/holdout/owner scopes, no real broker orders, no generated-code execution, no unverified model connectivity, no synthetic PnL represented as live, no cross-experiment PnL aggregation, no external provider credential leaks.

### Gate 4 — Regression and rendered acceptance

Run complete current unit, integration and Playwright suite including Phase 6 AI; add focused tests on every page, route, dynamic empty state, model-unavailable, no-data, risk unknown, keyboard and viewport. Existing Playwright cases must not be disabled, loosened, skipped, rewritten to mock away service flows, or snapshots silently overwritten. If agent browser blocked, accurately report not run and provide owner instructions.

### Gate 5 — Human signoff

Owner reviews full-size screens at desktop and mobile, both themes; approves any deviations from mockup with rationale. The contact sheet has limited per-panel resolution; request owner decisions rather than inventing unreadable text. Do not mark 1:1 accepted solely because visual screenshot tests pass on arbitrary golden images. No Phase 7 work or live activation.

## Deliverables

- Source changes plus a design-system and component inventory.
- `REDESIGN_V1_IMPLEMENTATION_REPORT.md`: screenshots compared, per-screen changes, functional controls, inaccessible designs, accuracy exceptions, route matrix, test evidence, unverified gates.
- `REDESIGN_V1_VISUAL_FIDELITY.md`: reviewer-facing side-by-side references, actual captures, notable deviations and owner approvals.
- Updated frontend UX docs and implementation status. Keep original Phase 5.5/6 evidence intact.
