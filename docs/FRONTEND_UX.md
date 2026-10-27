# Frontend architecture — Phase 5.5B

Date: 2026-10-27. Implementation exists; browser/visual/manual acceptance remains BLOCKED by the
managed local-origin permission. See ../PHASE55B_COMPLETION_REPORT.md and ux-migration-coverage.md.
No Phase6, external execution, generated-code runner or new financial calculation engine.

## Runtime structure

- App.tsx mounts AuthProvider independently of getOverview. Shared identity, route and account context
  live above page modules. A public outage cannot remove authenticated account safety.
- navigation/routes.ts is a finite typed route resolver; history.tsx provides native links and
  pushState/popstate. Unknown/deep malformed URLs are not authorization or external return targets.
  nginx's existing SPA fallback and API/health/OpenAPI proxies remain unchanged.
- Primary destinations: Acasă, Testează, Rezultate, Conturi și siguranță, Setări. Mobile has five
  permanent bottom links, not a modal hamburger drawer. Sensitive actions use native modal dialogs.
- RiskBanner reads all declared account pages or reports incomplete coverage; status failures are
  per-account. Age and last-known stops remain visible. RiskCenter owns actual scoped controls and
  distinguishes descriptive metadata, source documents, enforced versions, what-if and reservations.
- HomePage reads actual owned experiment summaries separately from public readiness. A bounded
  latest-page summary never pretends to certify every historical job or worker availability.
- StrategyLab offers five form steps plus explicit Start. Prerequisites use actual admitted data,
  immutable simulator/context records and verified policy coverage. The API and worker remain final.
- research-drafts.ts keeps allowlisted inputs/IDs/review in memory, scoped by identity. No local/session
  storage for auth, files, acknowledgements, arbitrary JSON or full financial plans. Logout clears drafts.
  Unknown create outcomes retain the same frozen request and key; there is no automatic write retry.
- ResultView displays stored canonical monetary strings and unavailable metrics honestly. Chart
  coordinates and sampled drawdown are approximate; only stored engine metrics are authoritative.
  Stored records, time/currency axes, exact tables, compare and provenance remain available.
- FinalEvaluation separates sealing, reviewed frozen configuration, one-use release and registration.
  Native backend checks remain intact. Interrupted final authorization can require audit inspection and
  advanced exact-plan resumption; the interface does not invent a new release to hide uncertainty.
- Management preserves owner bootstrap/manual TOTP/recovery, records/revisions, users and audit.
  Destructive security changes have consequence review. No remote QR renderer or new credential factor.
- BrokerCenter separates read-only signed observations, advanced manual simulation and read-only
  journal routes. Existing simulator commands and internal research-journal restrictions are preserved.
- MarketData separates source/catalog setup from guided imports and stored-data inspection. Upload
  acceptance is not research admission; ECB is reference-only. No arbitrary inferred CSV mapping.

## Design and error boundaries

ui/tokens.css defines the approved light/dark palette and compatibility aliases; product.css applies
readable typography, focus,44px controls, reflow and safe areas. Controls centralizes input/select,
notices, evidence and native-dialog behavior. Specialized existing forms remain typed modules rather
than a new design framework. Theme is the only persisted browser preference; system mode is supported.
copy/ro.ts centralizes source, strategy, phase, job and safe error language. Contracts/exports keep exact
technical identifiers. Unknown server messages are not echoed; known codes use an explicit allowlist.
Native unit tests validate money precision, missing values, route coverage and safety-age boundaries.
They do not establish browser accessibility or visual acceptance.

## Additive API reads

No database migration or financial-rule change was needed:

- GET /api/v1/market/jobs/{job_id}: same FullIdentity and owner filter as the existing job list;
  unknown/unowned jobs return404. Enables stable import progress URLs.
- Market JobView.cancel_requested: exposes the existing persisted flag without changing transitions.
- Research job view.cancel_requested: same existing flag, making cancel acknowledgement survive reload.

Native tests assert direct lookup, cross-owner denial, cancelled flag and real queue lifecycle.
Generated OpenAPI/TypeScript artifacts were regenerated; do not edit generated/api.ts by hand.

## Acceptance commands on an authorized local host

Use the existing disposable harness. It creates its own project, loopback ports, temporary credentials,
service databases/buckets and cleanup; never run compose down on the development stack.

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration
# First-time public visual candidates; inspect generated PNGs before accepting them:
E2E_ONLY_SCENARIO=ux E2E_UPDATE_SNAPSHOTS=1 make browser-integration
# Actual regression acceptance, without baseline updates or focused selection:
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
make check
make integration
make contracts-check
make smoke-demo
make secret-scan
make repository-check
```

Default full harness now includes ux in a separate disposable database per viewport, preserving the
old foundation/market/broker/risk/research databases. Collection contains20 cases:16 preserved cases
and4 new viewport cases. Visual comparison captures only signed-out public Home in both themes,
masks only the public read clock and retains visible mode/source/status evidence. Global trace,
screenshot and authentication-error-context restrictions remain in place.

Never treat collection, compilation, native tests or baseline generation as browser acceptance. Review
real baselines and rerun without updates. The managed origin denial must not be bypassed with another
browser surface, raw automation or a proxy.


## Public clock and visual-mask stability

PublicReadTime renders the real last successful public-read instant with ISO datetime and Romanian
HH:MM:SS. The footer reserves 8ch and uses tabular numerals; intrinsic proportional timestamp widths
previously changed the screenshot mask by 4px. Only this non-secret public clock is masked. Keep
mode, service state, source labels and safety content visible to strict visual comparison. The UX
visual case also requires a real public refresh to preserve dimensions and update the observed instant.

The owner's supplied 84-pixel mismatch was exactly the mask edge, not a general rendering regression.
Its source fix intentionally requires reviewed references for the stable slot. Do not add tolerances,
mask larger content, freeze safety clocks or automatically rewrite references. The new actual image
must be inspected before owner approval; no post-fix rendering or full browser pass is claimed here.
See the visual correction section in ../PHASE55B_COMPLETION_REPORT.md and its public PNG evidence.
