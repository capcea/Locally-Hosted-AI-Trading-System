# Phase 5.5A — proposed design system

> Phase 5.5B implementation update (2026-10-27): this approved design is now the migration basis.
> See [implementation/acceptance report](PHASE55B_COMPLETION_REPORT.md) and
> [S01–S42 / U01–U24 traceability](docs/ux-migration-coverage.md). Source/native implementation is
> present; browser, visual-baseline and manual accessibility acceptance remain BLOCKED.
> Descriptions below remain the approved design targets; they are not evidence of rendered acceptance.

DESIGN SPECIFICATION ONLY ·2026-10-27. These tokens/components are not applied to the application.
Current source includes strengths worth retaining: CSS theme variables, reduced motion, skip link,
explicit field labels, source badges, wrapping grids and bounded raw-data panels. Consolidate rather
than discard them. Current rendered layouts and assistive-technology behavior were not inspected.

## Direction and hierarchy

Calm modern research workspace: neutral ink/slate surfaces, one restrained teal action accent,
readable typography, ample spacing and factual state language. Premium means precision, consistency
and clear evidence, not a terminal, glowing trading signals, a decorative profit chart or childish
illustrations. Remove competing orbital/phase visuals from the task hierarchy; development remains
available in About. No copied video identity; that reference was unavailable.

Hierarchy: page purpose → account/mode/safety → one next action → meaningful content → supporting
facts → advanced evidence. Most content is open layout; cards group genuinely related decisions.
Avoid a wall of equally weighted cards. Use separators for rows and explicit headings for sections.
No fabricated performance, AI activity, P&L placeholder or auto-generated “success score”.

## Typography

- Font: system UI stack initially; self-host Inter only if already packaged/licensed and reviewed.
  No remote font/analytics dependency or unapproved installation. Romanian diacritics must render well.
- Body16px/24px; compact data14px/21px; helper14px/20px. No7–12px operational labels.
- H1 desktop28px/36px semibold, mobile24px/32px; H2 22px/30px; H3 18px/26px.
- Main monetary metric28px/36px desktop,24px/32px mobile; associated currency and description stay legible.
- Use tabular numerals in aligned financial rows; reserve monospace14px for IDs, hashes and technical
  payloads. Technical text is not reduced to unreadable size to fit a card.
- Labels use sentence case Romanian, not excessive all-caps or letter spacing. Maximum paragraph
  width approximately65–75 characters.16px is a product target, not a WCAG-mandated font minimum.

## Spacing, geometry and responsive layout

Spacing scale in px:4,8,12,16,24,32,48,64. Default field gap8; control group16; section32; page gutter
24 desktop/16 mobile. Corners8 controls,12 panels; border1; no decorative shadow needed for every card.
Dialog width480–640, forms max720, content max1280; allow full width for meaningful chart/table tasks.

Proposed breakpoints: below640 mobile,640–959 compact/tablet,960–1279 desktop,1280+ wide. These replace
fragmented600/640/900/1200/1600 decisions after a compatibility review; do not apply partially by accident.
Desktop sidebar224; compact uses labelled navigation without stealing form width; mobile uses five
bottom destinations. Layout responds to content and text zoom, not only a device model.

Test320,390,768,1024,1440 CSS-pixel widths, both orientations and200% text/400% page zoom. At320px
ordinary content must reflow into one column. Necessary2D data tables may scroll inside a labelled
region, never forcing whole-page horizontal scrolling. Avoid scroll traps. Account/mode/safety,
error summaries, long Romanian labels and primary controls cannot disappear at a breakpoint.
[W3C reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

Reserve bottom space for safe-area inset plus navigation/action bars; use content scroll margins
so focused fields/errors remain visible. Sticky controls may not cover chart legends, acknowledgements,
MFA inputs or final-release consequences. No three stacked sticky bars on a small screen.

## Semantic color tokens — exact proposed values

Light theme:
- canvas #F5F7FA; surface #FFFFFF; raised #EEF2F6.
- text #17212F; secondary text #526174; subdued-but-readable text #64748B.
- decorative separator #D9E0E8; interactive boundary #718096.
- action/focus #155E75; hover #164E63; on-action #FFFFFF.
- positive/result #166534; attention #854D0E; danger #B42318; information #1E40AF.

Dark theme:
- canvas #10151D; surface #17202C; raised #202B3A.
- text #F1F5F9; secondary text #AAB8C8.
- decorative separator #344155; interactive boundary #8191A5.
- action/focus #67D3E0; on-action #0B2025.
- positive/result #8DD6AA; attention #F4C06A; danger #FFB4A9; information #A8C7FA.

Give tokens names such as color.text.primary, color.surface.default, color.border.control,
color.action.primary and color.state.attention. One canonical border token replaces the current
undefined application --border references; do not silently assume a decorative divider meets the
contrast requirement of a field boundary. Token naming is proposed, not a new source API.

Computed sRGB contrast ratios for the exact listed foreground/background pairs (not visual tests):
light text/white16.22:1, secondary/white6.32:1, white/action7.27:1, control boundary/white4.02:1,
danger/white6.57:1; dark text/surface14.98:1, secondary/surface8.13:1, on-action/action9.60:1,
control boundary/surface5.10:1, danger/surface9.66:1. These calculations do not establish whole-UI
conformance: opacity, hover/selected/tint backgrounds, charts and actual rendering still require QA.
Normal text targets at least4.5:1; qualifying large text at least3:1.
[W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

Profit/loss use sign + words + currency, optionally semantic color. A positive return is never a
success badge implying deployability. State uses icon + text + explanation, not colored dots alone.
Default theme follows the operating system, with explicit system/light/dark choice. Honor an existing
stored light/dark preference during migration; theme is a preference, never an authorization setting.

## Status, source and safety primitives

StatusBadge supports these user concepts with distinct text:
- Working: “Disponibil” for verified service capability; “Test în lucru” only for actual running job.
- Waiting: “În așteptare” with queue/dependency/user-action reason; no false spinner implying computation.
- Needs attention: “Necesită atenție”, with issue, consequence and next action.
- Unavailable: “Indisponibil” or “Nu putem verifica”, with last trustworthy timestamp.
- Simulation mode: “SIMULARE · ordine externe blocate”, always independent of the above states.

A green service cannot turn a simulated account live, attest a policy or certify a data source.
Unknown/stale must not look identical to a confirmed stop or completed test. Keep raw enum in details.
A neutral “Neconfigurat” is not “Dezactivat” and not “Neimplementat”.

SourceLabel has two independent dimensions: data origin/evidence and execution environment.
Map current exact provenance enums, do not replace API values. Examples:
“Date sintetice / Execuție simulată”; “Istoric declarat, sursă {nume} / Execuție simulată”;
“Observație demo semnată, numai citire / ordine externe blocate”. A live-observed category is a design
slot for verified future read data only; it is unavailable now and grants no execution capability.
Never relabel user-supplied history independently verified or show all stored account capital as cash.

SafetyStrip names the current account/mode, known/unknown stop state and a visible safety entry.
Its error state does not disappear because overview fetching fails. Scope must be explicit before
mutations. On mobile, a concise strip can expand, but mode/unknown/STOP access cannot be collapsed away.

## Component contracts

Proposed shared components, not implemented exports:
- AppShell / PrimaryNav / AccountContext: five destinations, native link semantics, active state,
  page heading and safety entry. Mobile uses the same hierarchy, no hidden operational sixth module.
- PageHeader: purpose, one primary CTA and optional quiet contextual links. No global refresh that
  misleadingly appears to refresh every independent module; label the actual scope.
- StatusBadge / SourceLabel / SafetyStrip / LastVerified: distinct factual dimensions with text.
- Panel / DefinitionList / MetricSummary: semantically grouped content, not equal-weight dashboards.
- Field / Select / TextArea / Checkbox / ErrorSummary: one naming/error/help contract for all modules.
- Disclosure: native or equivalently accessible expanded state; precise title, never mandatory warnings
  hidden by default. Raw payloads wrap or have labelled local scroll, copy only safe authorized data.
- EmptyState / LoadingState / InlineError / ActionNotice: clear purpose, cause and next action.
- Stepper / ReviewSummary / EligibilityList: workflow progress versus prerequisites; no fake percentage.
- DataTable / Timeline / ChartFrame / ExactValues: explain sampling, units/source and read order.
- ConsequenceReview / Reauthenticate: shared verified-scope pattern for emergency/security/final release.

Start by extracting repeated Field/Select/submit/error patterns from the existing components. Keep
API contracts/generated types and server risk math independent. Components receive structured safe
facts; they do not parse arbitrary server HTML or infer permissions from a display label.

## Forms and errors

Permanent visible label; explicit stable accessible name; help/error associations; required marker
explained in text. Preserve the Phase5 exact-select-label correction: option text must not contaminate
control names. Label and accessible name must agree through translation. Never use placeholder as label.

Match input purpose: username/current-password/new-password/one-time-code where appropriate, allow
paste/password managers, choose numeric keyboard without stripping meaningful decimal or recovery-code
characters. Use Romanian presentation, but normalize to the existing exact decimal/ISO API contract
with validation. No floating-point lot/risk sizing in the browser. Preserve original UTC/zone/fold facts.

On validation, focus a concise error summary with links to affected fields; retain safe inputs and
show errors inline. On503, retain draft with unknown availability and a real retry/read action.
On401/expired MFA, return through the existing authentication mechanism, clear secrets and require
explicit action review. On409, explain conflict/changed version or matched-comparison mismatch;
never auto-overwrite. Ambiguous submission preserves idempotency and checks existing job state.

Disabled actions have a visible reason and an actionable prerequisite/role explanation, not an
inaccessible hover-only tooltip. Pending and disabled are separate states: the current global CSS
cursor:wait for every disabled button should not imply all restrictions are temporary computation.
No arbitrary sleep, fake request success or removal of assertions can stand in for state handling.

## Buttons, dialogs and consequential actions

Primary is solid accent; secondary outlined/quiet; tertiary text link; danger uses explicit consequence
language. Default minimum44×44px product target with adequate separation, especially emergency actions.
WCAG2.2AA target minimum is24×24px or a permitted exception;44px here is a stricter design choice.
[W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

No single dropdown combining STOP, CLEAR and FLATTEN. Consequence review lists account, scope, current
state/unknowns, what changes/does not change, required acknowledgements and existing MFA. STOP does
not close positions; FLATTEN is simulated-only and can be incomplete. Separate final irreversible
submission from review; do not optimistically report success. No offline mutation queue.

Dialogs: meaningful title/description, labelled close/cancel, sensible initial focus, keyboard cycle,
Escape before submission, background inertness and return focus to trigger. An async request closing
its dialog does not cancel server work; present actual pending status on the resource page. Avoid
nested modals and focus loss on a background poll. Review may use a full page on mobile for long policy/
final-release consequences. Never truncate an acknowledgement to fit a dialog.

## Charts and financial presentation

ChartFrame requires title, source/mode, time window, labelled axes/units, legend and sampling statement.
Use actual timestamps for x positions, explicit gaps and inspectable data; no smoothing or interpolated
missing ticks that imply observation. Timeframe, tick/OHLC uncertainty and timezone are visible.
Use one or two comparable series; labels/dashes/symbols distinguish them without color alone.

Results show stored net change/drawdown/trade count/costs before advanced ratios. Currency and basis
always accompany money. Romanian grouping/decimal display is presentation only; exact canonical
Decimal strings remain available. Values below display precision must not silently become zero or
hide a breach. Drawing coordinates may be approximate; authoritative metrics come from stored output,
not chart points. A sampled drawdown trace must be labelled approximate unless a full verified series
is served. No fabricated histogram from missing trades or probability-of-profit meter.

Provide keyboard-operated inspection plus exact-value table and narrative summary. A generic SVG
role=img is not alone proof of equivalent data access. Tooltips cannot be the only way to find losses,
null warnings, timestamps or series names. Dense tables use semantic headers/captions, contextual
units, row actions with specific names and labelled horizontal scroll only where necessary.

## WCAG2.2AA target and acceptance checklist

[WCAG2.2](https://www.w3.org/TR/WCAG22/) is the conformance target, not a claim that this blueprint or
current app passes. Apply checks in every implementation step, not only at the end.

- Keyboard/focus: visible focus, sensible order, no trap, skip link and native navigation. Sticky UI
  cannot fully obscure focus; design for fully visible focus where practical.
  [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
- Design ring:2px outline +3px offset with3:1 contrast against adjacent surfaces; this is an internal
  target. SC2.4.13 Focus Appearance is AAA, not an AA requirement or certification here.
  [W3C Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html).
- Names/relationships: visible labels, matching accessible names, grouped choices, errors/help linked,
  semantic headings/landmarks and understandable account scope. Test dynamic options and translated text.
- Authentication: preserve MFA while providing password-manager/paste and accessible OTP assistance;
  no cognitive workaround that weakens security. Validate actual assistive use.
  [Accessible authentication](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html).
- Updates: polite announcements for task state/success without stealing focus; urgent role=alert for
  important actionable errors, deduplicated during polling. Do not announce every percentage/timestamp.
  [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).
- Visual: test actual themed/hover/selected/error states, contrast, reflow, text enlargement, orientation,
  high contrast/forced colors and non-color cues. Respect reduced motion; no essential auto-animation.
- Manual checks: VoiceOver with Safari and real mobile keyboard/touch where available, plus desktop
  keyboard and screen-reader alternatives. Chromium iPhone emulation is not iOS conformance proof.
- Privacy: no authentication/recovery screenshot baselines or secret logging. Visual fixtures use
  clearly synthetic authorized data; never mask the very safety labels a test must verify.

## Design review gates

Approve token/component states, screen hierarchy and safety vocabulary first. Then verify that a
novice can explain the task without advanced terminology and an expert can still reach exact controls.
Computed color pairs, source inspection and passing unit tests cannot replace rendered/manual review.
No design-system installation, production CSS rewrite or dependency addition occurs in Phase5.5A.

## Implementation status

ui/tokens.css and product.css apply the palette/layout with compatibility aliases for retained expert
panels. Controls.tsx provides shared inputs/selects/evidence/native dialogs; product remains Romanian.
No design framework or font dependency was added. Real-browser contrast/focus/zoom and actual mobile
remain unverified. Mobile uses permanent five-link navigation rather than an overlay menu.
