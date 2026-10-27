# Market browser timeout correction — 2026-10-28

The owner screenshot reports four foundation passes and a Phase 2 desktop global timeout.
The original error-context contains no active locator, stack, DOM snapshot or HTTP error.
Its original timed-out await is unknown. No raw authentication state or imported file is retained here.

Source inspection found missing completion boundaries around instrument creation and import navigation.
The correction waits for actual API responses, persisted instrument UI, the import redirect and real
worker success. It adds fixed stage names for diagnostics. No original assertion was removed;
assertion-preservation.json compares TypeScript AST expressions, not runtime browser outcomes.

verification.json records actual commands and gates. Raw local logs stay ignored under
.cache/phase55b-market-browser/. Browser execution remains blocked by the existing managed-origin
restriction. Collection and native integration are not substitutes for browser acceptance.

Owner-local commands, without rewriting snapshots:

```sh
env -u E2E_UPDATE_SNAPSHOTS E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Require the focused case and all 20 desktop/mobile cases. Approved desktop PNG references remain
unchanged. No development service recreation or volume deletion is part of this correction.
SIMULATED/DENY_ALL remains in force; no Phase 6 or external execution.
