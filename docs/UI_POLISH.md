# UI/UX tidy-up — 2026-10-28

Implemented as a frontend-only refinement of Phase 5.5B. No Phase 6, new financial calculations,
API changes or migrations. New rendered behavior is not browser-accepted here; the existing managed
localhost-origin restriction remains in force. The owner's supplied research-screen screenshot was
inspected, not a screenshot of the new implementation.

## Changes across the interface

- Shared shell: task-specific Romanian descriptions, clearer account-selection loading/empty/error
  text, visible selected navigation, and the same five primary destinations. No account is selected
  automatically. Public overview loading remains independent of authentication and safety.
- Research: remove the redundant introduction/second start link on /testeaza. Both /testeaza and
  /testeaza/nou retain the actual five-step form, all validation, reviewed configuration and explicit
  submit. Progress has numbered steps, an accessible description and clearer spacing. Missing account
  or admitted data has an explanation and setup links; the disabled Continue action has visible help.
- Safety: an empty completed account read says so instead of “0 of 0.” Unknown/incomplete reads stay
  UNKNOWN/UNAVAILABLE; per-account STALE labels, observation times, per-order checks and exact scope
  remain. Last-known persistent stops are called out without opening details. The separate safety
  destination/action remains available. Remove only the duplicate mode text inside this banner;
  SIMULATED/DENY_ALL stays visible in the shell. No stop-clear/flatten logic changes.
- Settings: group the existing nine task links into Cont și acces, Date și cercetare and Platformă,
  plus the existing appearance control. Subpages show their own group and Toate setările. Signed-out
  users retain the pre-existing public diagnostics/about/roadmap navigation without exposing protected
  settings. Exact destinations and authenticated route guards are preserved.
- Home: shorter authenticated primary guidance; refresh/diagnostic actions are spaced as a group.
  Every activity/result/availability summary still uses the existing actual API reads.
- Accounts, security, data, broker observations, results and advanced tools inherit consistent shared
  paragraph spacing, controls, records, details, tables and metric cards. All financial display values,
  charts, immutable provenance, read-only scopes, MFA and error sanitization retain existing behavior.
- Responsive behavior: wrapping section links, two-column wrapping mobile step labels, full-width
  mobile safety action, safe-area-aware scroll padding, and a scrollable desktop sidebar for short
  viewports. Existing reduced-motion, focus and touch-target rules are retained. Native checks and
  source inspection do not establish 200% reflow, keyboard, screen-reader or WCAG acceptance.

## Source and regression scope

App.tsx composes the existing modules; navigation/sections.ts centralizes the previous destinations
and navigation/SectionNavigation.tsx marks the current task on root/deep routes. No route is renamed
or removed, so the S01–S42 mapping remains valid. navigation/sections.test.tsx covers visual location,
reachable destinations and the signed-out public navigation path. safety.test.ts adds fail-closed
summary-language cases. ux-workflows.spec.ts adds root-wizard and Settings discoverability assertions
to its existing real-service owner/viewer scenario; existing assertions and 20-case count are retained.

Shared styling lives in ui/product.css. HomePage.tsx and StrategyLab.tsx have the task-specific
presentation changes; RiskBanner.tsx changes presentation only. Backend financial/risk/storage/auth
modules and security contracts are untouched. Original work was hashed and frontend sources archived
privately before editing under .cache/ui-polish/.

## Evidence, local refresh and remaining acceptance

Actual commands/exits/results and source/container/reference preservation are recorded in
phase55b-evidence/2026-10-28/ui-polish/verification.json. Raw logs remain ignored in .cache/ui-polish/.
Initial test mistakes/failures and the normal Docker builder cache restriction are retained honestly
in that ledger. The local web image was rebuilt using a writable workspace Buildx cache; only web is
refreshed with --no-deps, with no development migration or persistent-data cleanup.

The four previously owner-approved PNG references remain unchanged as evidence of the previous
presentation. This requested UI change affects public Home geometry/styles; visual differences must
be reviewed using genuine fresh captures before approving any replacement references. No automatic
snapshot update, tolerance change, broader mask or screenshot of authentication state is authorized
or performed. A visual failure on the old references is not grounds to weaken tests.

Run on the owner's authorized browser host, without rewriting snapshots:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_SCENARIO=ux make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Fresh public light/dark actual/diff PNGs may require explicit review for this intentional design
change. Keep those separate from functional failures; preserve all original regressions and require
all 20 desktop/mobile scenarios before overall Phase 5.5B browser acceptance. These commands are
BLOCKED / NOT EXECUTED HERE, exit code null. No permission workaround was attempted.
