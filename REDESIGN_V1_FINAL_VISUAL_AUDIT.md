# V1 final visual audit — refinement delivered, acceptance open

2026-10-28. **SOURCE REFINED / NATIVE CHECKS PASSED / AFTER-RENDER VALIDATION BLOCKED.**
This task has not met the nine-screen visual definition of done. No 1:1, pixel-perfect, mobile,
WCAG or complete browser acceptance is claimed. SIMULATED / DENY_ALL remains unchanged; no Phase 7.

Start with the [visual review package](docs/redesign-v1-evidence/2026-10-28/final-visual-review/index.html).
It contains the approved references and the one genuine available Home before capture. There are
no invented after images or simulated screenshot results. Existing uncommitted work was protected:
1279 Git-selected files were hashed and archived privately before editing.

## References and evidence boundaries

Read DESIGN_SPEC.md, README.md, IMPLEMENTATION_MAP.md, both V1 implementation/fidelity reports,
PRODUCT_SPEC, IMPLEMENTATION_STATUS and the complete S01–S42 migration map. All 14 original handoff
entries verify SHA256 and byte counts. Actually inspected the 1672×941 Home master, contact sheet
and all nine individual crops with image-capable tools. The crops are small, include adjacent-panel
fragments and illustrative text/data; they cannot define exact production text or font rasterization.

`.cache/redesign-v1-captures/` does not exist. The latest saved Playwright artifacts do contain a
real V1 public Home image, expected image, diff and error context. All four were preserved in
[the review folder](docs/redesign-v1-evidence/2026-10-28/final-visual-review/artifact-inventory.json).
The actual image is 1280×1684 full-page; its saved mtime is 2026-10-28 09:56:53 UTC, later than the
previous V1 CSS modification. Its visible composition matches V1. There is no source-build sidecar,
so an exact commit/bundle identity cannot be attested. It is **before evidence**, not a new agent run.
No other current V1 screen/mobile/dark capture was located in the designated folder or latest artifacts.

A fresh `cua.createBrowserTab("iab", "http://127.0.0.1:5173", {visible:true})` was rejected:
“a saved user permission setting blocks this action … origin approval gate did not grant access.”
The restriction explicitly prohibits alternate-browser/CLI/CDP/indirect workarounds. None was used.
Consequently no new capture, overlay, post-fix rendered measurement or browser-suite execution was
performed. Command-level browser exits are **N/A**, not zero or fabricated failures.

## Home — five supported priorities and corrections

Measurements describe the **before** image, not the corrected render. Exact border pixel runs and
approximate visible bounds are in [before-geometry.json](docs/redesign-v1-evidence/2026-10-28/final-visual-review/before-geometry.json).
The source/reference viewports and data states differ, so no numerical fidelity score is appropriate.

1. **Main row stretched by the unavailable AI card.** Performance and AI occupy approximately
   y317–978; matching border runs at x276 and x952 both extend y331–963. The reference performance
   panel is approximately 297px high, whereas the before empty panel is approximately 661px high.
   The shared grid row stretches performance to the taller AI content and pushes recent history
   to y992. Changed Home to independent left/right stacks: performance above recent/safety on the
   left; AI above next actions on the right. No fixed clipping or maximum content height. The empty
   performance minimum is 215px instead of 275px; real results retain natural height and exact evidence.
2. **UNKNOWN breaks across lines.** The amber card renders `UNKNOW` / `N`, inflating the KPI row
   (approximately 167px versus the illustrative reference's 110px). Financial values remain 28px;
   the actual safety-state value now uses an explicit 18px status variant. UNKNOWN is preserved,
   not translated into a safe/zero-risk claim. Narrow content may still wrap without horizontal loss.
3. **AI suggestions stack four deep.** At the captured width, long chips occupy four rows and
   inflate both top cards. Home suggestions now use two equal columns and shorter Romanian labels.
   Full question strings, disabled checks and explicit review/consent before submission are unchanged.
   The unavailability explanation is shorter but still requires verified private model, recent worker
   and owner MFA. No unverified model becomes connected.
4. **Title focus resembles a page-wide input.** The visible focus rectangle spans approximately
   x277–709 around a short heading. The h1 now sizes to its content and retains an explicit 2px,
   offset focus outline. Route-change focus behavior is unchanged. Focus is not masked in screenshots.
5. **Shared header consumes excess height.** Before header is approximately 78px, versus about
   68px in the master. Shared source now uses a 70px minimum with 8px vertical inset instead of
   76px/12px. It can grow for real wrapping and touch controls; no fixed-height clipping.

Sidebar is approximately 256px and content inset 20px in the before capture, already consistent
with the specified starting geometry. Those were retained. Navy/light palette, radii, five primary
links, account context, public diagnostics and independent safety banner remain. Footer/status can
require sidebar scrolling at short heights; real device inspection remains necessary.

## Nine-screen ledger

“Functional” below describes implementation/native evidence, **not unexecuted browser acceptance**.
Every reference was visually inspected. Only Home has an actual before image. An absent capture is
not a visual finding. Header refinement is shared; no speculative page-specific restyling was made.

| Screen / reference | Actual screenshot | Desktop findings / corrections | Mobile findings | Remaining differences | Functional / visual evidence / approval |
|---|---|---|---|---|---|
| Acasă — [master](docs/design-reference/ui-v1/references/00_HOME_MASTER_1672x941.png), [crop](docs/design-reference/ui-v1/references/01_home_contact.png) | [1280px before](docs/redesign-v1-evidence/2026-10-28/final-visual-review/before-home-light-actual.png); after unavailable | Five observed priorities above corrected in source. Independent ~2.1:1 stacks, status size, suggestions, focus, header. | NOT INSPECTED. Single-column source reflow preserves DOM/focus order; no screen-reader/mobile acceptance. | Need after capture at 1672/1440/1280. Empty public page differs honestly from populated illustration. Sidebar short-height scroll remains to review. | Native checks pass; before visually inspected; after/browser unverified. Exact new public goldens require owner approval. |
| Testează / Strategii — [reference](docs/design-reference/ui-v1/references/02_testeaza_strategii.png) | NOT AVAILABLE | Source has four KPIs, actual reviewed baselines, filters, table/details/actions. Shared header corrected. No claim of five observed visual differences. | NOT INSPECTED; overflow/touch/table behavior pending. | Capture and assess KPI heights, filter spacing, row density, detail expansion and action alignment. | Native registry/route tests pass; real rendered library not verified here. Owner visual review pending. |
| Testează / Backtesting — [reference](docs/design-reference/ui-v1/references/03_testeaza_backtesting.png) | NOT AVAILABLE | Narrow five-step configuration / wider prerequisite review retained. Header corrected; no form handlers changed. | NOT INSPECTED; form scrolling/sticky-to-static reflow pending. | Inspect column ratio, step density, form labels, readiness height, result chart size. Required setup may exceed illustrative static form. | Native and service research tests pass; actual browser flow pending. Owner review pending. |
| Testează / Experimente — [reference](docs/design-reference/ui-v1/references/04_testeaza_experimente.png) | NOT AVAILABLE | Actual bounded counts, search/state/phase filters, table and details retained. Header corrected. | NOT INSPECTED; long names/table scroll pending. | Inspect KPI density, toolbar alignment, state badges, row height and paging actions. No fake rows/counts. | Native filters/routes and real service lifecycle pass; browser/visual pending. Owner review pending. |
| Testează / AI Center — [reference](docs/design-reference/ui-v1/references/05_testeaza_ai_center.png) | NOT AVAILABLE | Existing composer/structured evidence plus model-role panel retained; header corrected. Home prompt polish does not rewrite AI Center submission. | NOT INSPECTED; composer/roles/focus reflow pending. | Inspect workspace proportions, input placement, context evidence, response density and role cards. No fake conversation or online state. | Native/fixture transport integration pass; actual model inference and rendered workbench not verified. Owner review pending. |
| Rezultate — [reference](docs/design-reference/ui-v1/references/06_rezultate.png) | NOT AVAILABLE | Selected stored experiment/tiles/chart/exact values and API-matched comparison retained. Header corrected. | NOT INSPECTED; chart labels/exact-value table pending. | Inspect metric density, chart dimensions/axes, sampling disclosure, evidence spacing and comparison. Exact distribution remains unavailable rather than invented. | Native/service result, replay and holdout tests pass; populated browser/visual pending. Owner review pending. |
| Conturi și siguranță — [reference](docs/design-reference/ui-v1/references/07_conturi_siguranta.png) | NOT AVAILABLE | Existing account/status/emergency columns retained; shared header corrected. No safety-control consolidation. | NOT INSPECTED; consequences/dialog/focus and long IDs pending. | Inspect account-list width, limit labels, three distinct actions, policy evidence and short-height layout. Required MFA/consequences remain longer than mockup. | Native/service risk scope and safety pass; rendered emergency workflow pending. Owner review pending. |
| Setări / Modele AI — [reference](docs/design-reference/ui-v1/references/08_setari_modele_ai.png) | NOT AVAILABLE | Real registry, expiry/capability table, role assignments/forms retained; header corrected. | NOT INSPECTED; forms/table/hash reflow pending. | Inspect registry density, long identifiers, role grid, connection form and unverified badges. No mockup model names hardcoded. | Native/service AI registry/authorization pass; rendered settings and real model availability unverified. Owner review pending. |
| Setări / Platformă — [reference](docs/design-reference/ui-v1/references/09_setari_platforma.png) | NOT AVAILABLE | Structural source/form columns and all existing settings links retained; header corrected. | NOT INSPECTED; form/order/overflow pending. | Inspect column ratio, provider rows, validation messages, grouped links and source metadata. No unsupported global toggles. | Native/service provider/data checks pass; rendered setup pending. Owner review pending. |

The five checks listed for each unrendered screen are **next review tasks**, not invented defects.
All nine still need actual 1672×941, 1440×900, 1280×800, 390×844 and 360×800 review, both themes.

## Changes, interactions and safety

Changed source: `apps/web/src/home/HomePage.tsx`, `v1/components.tsx`, `v1/AIWidgets.tsx`,
`v1/redesign.css`; strengthened `apps/web/e2e/redesign-v1.spec.ts`. No large framework or backend
change. New browser assertions require a one-line desktop safety state and recent history immediately
below performance rather than below the AI card's height. Capture waits for actual loaded fonts.
Those new browser assertions are **not executed here**; original assertions are preserved.

No source fields, table rows, exact-value alternatives, context/policy/provenance, auth/MFA, ownership,
CSRF/RBAC, five-step workflow, replay, cancellation acknowledgment or holdout controls were removed.
All S01–S42 and Phase 6 destinations remain mapped. Mobile source reflow follows DOM order rather
than visually moving focused controls ahead of their reading order. Charts/math/API contracts are
unchanged. No authoritative financial calculation in JavaScript, fake performance/model/broker state,
AI-generated execution or external orders. Model/worker outage remains truthful; optional AI worker
was already unhealthy at task start and was not represented as connected or repaired by a UI change.

## Commands and actual results

Full records, output paths and durations: [verification.json](docs/redesign-v1-evidence/2026-10-28/final-visual-review/verification.json).

| Exact command | Exit | Actual result |
|---|---:|---|
| `make check` | 0 | 243 Python +149 frontend tests; lint/format/types/build pass. |
| `make integration` | 0 | One readiness case; 86 real isolated cases before and 86 after restart; migrations, loopback TCP, PostgreSQL/Redis/MinIO round trips/persistence; strict HTTP200 readiness and order refusal. |
| `make contracts-check` | 0 | Generated contracts byte-identical. |
| `make smoke-demo` | 0 | API/execution-denial smoke; readiness HTTP200. |
| `make secret-scan` | 0 | No leaks in Git-selected files; ignored secrets/runtime state excluded. Final evidence scan also run. |
| `make repository-check` | 0 | 19 sensitive-path exclusions; no commit/remote/push. |
| `npm run test:e2e -- --list` from `apps/web` | 0 | 24 cases /10 files collected only; **zero claimed executed**. |
| `env BUILDX_CONFIG=.cache/buildx docker compose up -d --build --no-deps --wait --wait-timeout 120 web` | 0 | Only web refreshed; healthy. This is not rendering evidence. |
| `V1_CAPTURE_CANDIDATES=1 E2E_ONLY_SCENARIO=redesign make browser-integration` | N/A | NOT EXECUTED: managed browser-origin refusal. |
| `E2E_ONLY_SCENARIO=redesign make browser-integration` | N/A | NOT EXECUTED: same restriction. |
| `env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration` | N/A | NOT EXECUTED: same restriction; old-UI golden mismatch also remains unresolved. |

The saved owner artifact reports 237080 changed pixels / ratio0.11, expected1280×1047 versus
actual1280×1684. The expected image is visibly the older Phase 5.5 layout. This is a **historical
recorded visual failure**, not a new run or comparison to the approved V1 PNG. It cannot be fixed
by tolerance increases or treated as successful acceptance. No golden replacement was performed.

Two tooling-only probes failed: the optional system-Python image-metadata probe lacked Pillow
(PNG dimensions/borders were then read using standard-library struct/zlib), and the collection log
wrapper initially used a cwd-relative output path. The latter exited1 before npm ran, was corrected
to script-relative output, and the actual collection then exited0. No application test failure was
suppressed. Vite's >500kB bundle warning and Starlette/httpx deprecation remain advisory.

[Preservation evidence](docs/redesign-v1-evidence/2026-10-28/final-visual-review/preservation.json):
162 backend/infrastructure files unchanged; all15 original browser source/helper/golden files unchanged,
including four approved PNGs; all12 non-web container identities/images/mounts unchanged. Only the
integration harness's own uniquely named disposable resources were cleaned. Development database,
Redis and MinIO volumes were not reset, deleted or substituted.

## Remaining gates and exact owner-local procedure

1. Generate fresh candidates in a local environment whose browser policy permits access:

   ```sh
   env -u E2E_ONLY_PROJECT -u E2E_UPDATE_SNAPSHOTS V1_CAPTURE_CANDIDATES=1 E2E_ONLY_SCENARIO=redesign make browser-integration
   ```

   It uses disposable real services and outputs `.cache/redesign-v1-captures/`. It captures only
   sanitized non-secret public/disposable-fixture pages, never MFA/recovery. No model download or
   broker credentials required. Authenticated SYNTHETIC_FIXTURE files are not public Home goldens.
2. Inspect all nine pages, both themes/five viewports. Compare Home after against preserved before
   and the master, then each other page against its crop. Record source/build identity and exact
   screenshot hashes. Populate this ledger with genuine screenshots and remaining differences.
   Also exercise keyboard/search, disabled reasons, zoom200%, long IDs, screen-reader semantics,
   chart/exact-table usability and populated immutable-result states. Do not certify these from CSS.
3. If intentional V1 public Home captures are correct, obtain explicit owner approval for those
   exact new candidates. Earlier Phase 5.5 references/clock-mask approvals do not authorize new V1
   golden replacements. Do not update snapshots globally or increase mismatch tolerances.
4. After review/adoption, run without rewriting snapshots:

   ```sh
   env -u E2E_ONLY_PROJECT -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_SCENARIO=redesign make browser-integration
   env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
   ```

   All24 desktop/mobile cases must pass. Until then the final visual acceptance gate remains OPEN.

No uninspected candidate is presented for approval now. Stop at V1 polish; do not start Phase 7.


## Owner terminal follow-up — 2026-10-28 16:33

**OWNER-REPORTED VISUAL FAILURE; BASELINE MIGRATION STILL OPEN.** The supplied terminal screenshot
reports expected1280×1047 versus received1280×1684,237080 changed pixels,1 failed/1 passed and
`backend_failures: []`. It confirms browser execution reached a screenshot assertion; it does not
establish the remaining26-case suite or after-polish visual acceptance.

Actually inspected expected/actual/diff PNGs. The expected image is the former Phase5.5 public
Home: white223px sidebar, introductory card and stacked public status panels. The received image
is V1: navy256px sidebar, blue selection, four pastel KPIs, performance/AI cards, recent/safety/next
actions and six-stage workflow. The changes span the shell and page composition, not an84/336-pixel
clock-mask or antialiasing difference. The page is637px taller. Reverting to the old composition
would contradict the approved V1 design. Raising tolerances would conceal the whole-page change.

The available three PNGs are byte-for-byte identical to the already-preserved pre-polish artifacts,
with modified time09:56:53UTC. They contain the oversized empty performance card (approximately
y317–978), wrapped UNKNOWN and wide heading focus rectangle. Current source already contains
the previously documented independent Home columns, status typography and compact header/suggestions.
These files therefore cannot verify the current render or establish a new approved golden. The
terminal screenshot alone supplies no frontend bundle identity. No stale-build cause is asserted.

[Artifact hashes/dimensions and evidence scope](docs/redesign-v1-evidence/2026-10-28/final-visual-review/owner-1633-artifact-review.json).
No application code, visual assertions, tolerances or accepted PNGs changed for this diagnosis.
Agent-side browser capture remains unavailable under the recorded managed-origin restriction.
Generate fresh owner-local review candidates using the existing isolated capture path:

```sh
env -u E2E_UPDATE_SNAPSHOTS V1_CAPTURE_CANDIDATES=1 E2E_ONLY_SCENARIO=redesign make browser-integration
```

This writes review candidates under `.cache/redesign-v1-captures/`, including four public
`PUBLIC-REVIEW-home-{light,dark}-{desktop,mobile}-darwin.png` images, without overwriting accepted
references. Inspect current geometry and all four exact public candidates before requesting owner
reference approval. Earlier clock-mask approvals apply to the old presentation only. Then adopt
only approved exact files and rerun all26 cases without snapshot rewriting. Current V1 reference
migration remains pending; no visual success or Phase7B is claimed.
