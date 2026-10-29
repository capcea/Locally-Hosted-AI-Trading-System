# Codex — Implement approved 1:1 AI Trading dashboard mockups

**Model: GPT-6**  
**Reasoning effort: High for planning, security review and final acceptance; Medium for isolated CSS/component implementation.**

I explicitly APPROVE the attached V1 visual design of the AI Trading Research Platform and authorize you to implement it in the existing project. **Do not implement Phase 7. Do not enable broker execution.**

## Essential reference files

I have extracted the attached package into the project as `docs/design-reference/ui-v1/` (or another location I will give you). Read:

1. `DESIGN_SPEC.md` — binding product/visual/functional spec.
2. `references/00_HOME_MASTER_1672x941.png` — highest priority, visual reference for the Home page.
3. `references/01_ALL_TABS_CONTACT_SHEET_1536x1024.png` — nine page compositions.
4. `references/01_home_contact.png` … `references/09_setari_platforma.png` — nine extracted crops for navigation; crops are low-resolution and cannot supply precise text/typography.

Read the actual images with image-capable inspection. Do not merely read filenames or make up what they depict. If you cannot access these images, stop before implementing visual changes and report the exact missing paths.

## User-approved intent

Implement the mockups **as identically as technically feasible** in *composition and styling*: dark navy fixed sidebar, light spacious canvas, topbar, navigation labels, pastel KPI tiles, soft 1px borders, gradient/pale widgets, compact data tables, blue/violet CTAs, chart layout, component sizes and hierarchy. Do not redesign, recolor, change card placements, switch to a dark page, introduce a new template, or simplify away sections. The HOME master is the main high-resolution standard; the 3×3 contact sheet specifies the eight additional screens.

The nine screens are:
1. Acasă
2. Testează > Strategii
3. Testează > Backtesting
4. Testează > Experimente
5. Testează > AI Center
6. Rezultate
7. Conturi și siguranță
8. Setări > Modele AI
9. Setări > Platformă

Use actual existing routes and add aliases where necessary; specifically preserve `/testeaza/ai`, `/testeaza/ai/{id}`, `/setari/ai`. All prior features must remain reachable, including Phase 5.5 S01–S42 and Phase 6.

## Hard constraints: appearance does not license fake features

Every dollar figure, ROI, win rate, active model status, risk percentage, experiment count and checklist item in the concept images is fictional. In production use genuine owner-scoped backend data or an explicit empty/unknown/unconfigured state. Never copy concept numbers as seed UI. Never sum unrelated backtest equity into a fictitious portfolio PnL; never label 8 reviewed baselines as 8 live active strategies. Risk state comes only from the scoped verified gateway; service health never implies permission. Ollama currently has not been independently verified running; show the truthful unavailable state until authorized probe confirms it.

All current security and financial invariants must remain: MFA, RBAC, CSRF, immutable experiments and audit, dataset provenance, point-in-time / holdout protections, actual Risk Gateway, owner scope, STOP_NEW_ENTRIES, reviewed CLEAR_STOP, simulated-only FLATTEN, strict AI context separation, no AI-generated code execution, no external demo/live orders, SIMULATED/DENY_ALL. No Phase 7 autonomous loop.

## Process — proceed in controlled batches

### Step 1: Audit & precise map (no premature rewriting)
- Inspect React components, CSS/theme tokens, routes, data clients, e2e tests, Phase 5.5A/B specs and Phase 6 completion.
- Map every visual component/button/table/chart in the nine references to EXISTING APIs, or a truthful unavailable/advanced state.
- Create a per-screen implementation checklist and route/feature coverage map. Decide responsive adaptation explicitly.
- Take a baseline of existing source and tests; preserve uncommitted work and persistent database volumes.

### Step 2: Design system & shell
- Build calibrated design tokens, dark sidebar, global topbar, light background, typography, button/card/icon/table/chart primitives.
- Implement keyboard-accessible navigation and desktop/mobile responsive shell.
- Keep the approved visual hierarchy rather than approximating with a different layout library.

### Step 3: Implement all nine pages
- Match each page's physical composition and visual hierarchy per spec and cropped references.
- Reuse existing APIs and state; reorganize views without rewriting financial engine, risk rules, research calculations, AI gateway or migrations unless an additive requirement is clearly justified.
- Use honest empty/loading/error states **with same component geometry** so unconfigured systems still look polished.
- Preserve all admin and advanced tools under their appropriate routes.

### Step 4: Test each page incrementally
- Implement functional controls; no visual-only fake buttons.
- Add tests for 9 pages, navigation, keyboard, mobile, accurate model-unavailable, unknown risk, no-data, real experiments, owner and viewer role limits.
- Use sanitized deterministic **test-only** fixtures for screenshot/visual comparison; never commit fictional research data as production metrics.
- Where browser/screenshot comparison is permitted, capture at 1672×941, 1440×900, 1280×800, and mobile 390×844 / 360×800. Human-review screenshot overlay against reference; do not automatically rewrite baselines. If browser not permitted, mark blocked; cannot assert 1:1 visual acceptance.

### Step 5: Regression, preservation & report
Run and record exact commands, exit codes and assertions:

```sh
make check
make integration
make contracts-check
make smoke-demo
make secret-scan
make repository-check
npm --prefix apps/web run test:e2e -- --list
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Do not weaken older cases or fake browser acceptance if managed browser launch is blocked. Don't delete/reset dev PostgreSQL/Redis/MinIO volumes or expose secrets. Do not download models, rent GPU, execute generated code or enable real/demo orders.

## Deliverables

1. Full implemented responsive UI for all nine screens.
2. Existing backend features preserved and all visible controls functional or clearly unavailable with reason.
3. Updated component inventory, visual tokens, and old→new route map.
4. `REDESIGN_V1_IMPLEMENTATION_REPORT.md` with test exit codes, cases counted, gaps, and screenshots actually inspected.
5. `REDESIGN_V1_VISUAL_FIDELITY.md` with side-by-side per-page feedback and honest deviation tracking.
6. A concise final report showing what is implemented, what was tested, what is only owner-reported, what remains visually unverified, and commands I need to run locally.

**Do not declare the redesign pixel-perfect, entirely finished, or ready for production without full rendered and owner acceptance. Stop at this UI implementation, not Phase 7.**
