# Phase 2 browser-fix evidence — 2026-10-26

**Decision: selector defect fixed in source; rendered verification BLOCKED; Phase 2 acceptance not complete.**

## Root cause and provenance of evidence

[Owner-local failure excerpt](owner-failure.txt), [original artifact fingerprint](owner-failure.json): the test at e2e/phase2.spec.ts:13 failed at its former line 99. Global `.market-json.last()` selected provider capabilities rendered below the explorer, not the manifest. This is distinct from Chromium launch denial. The source fix names the provenance result region and scopes the assertion to it, requires actual GET HTTP 200/schema version 1, and compares the complete displayed JSON with that actual response. Earlier-cutoff assertions now require an actual successful empty API sample and the rendered empty state. No route mocks, fake service integration, sleeps, skips or weakened assertions.

The two focused managed attempts (before/after) each passed 27 native cases before and after service restart, then failed the single desktop case at Chromium launch. The complete unfiltered attempt passed 27+27 native cases, then recorded 3 desktop launch failures and 1 HTTP-only denial pass. Six later market/mobile cases were NOT RUN after the failed group. Ten cases collect. No browser success is inferred. No executable, launch flag, permission or alternative execution route was changed.

`make check` ultimately passed 100 Python tests, 16 frontend tests, lint/format/types/build; 28 service cases are deliberately selected in their separate native runs. Initial B020 loop-variable and Prettier failures were corrected, with outputs retained. `P0_CACHED_IMAGES=1 make integration` passed actual readiness, 27+27 native cases and strict readiness/safety smoke. Standalone smoke and contracts passed. No dependency or backend schema/API/auth/risk changes.

[Preservation output](preservation.txt): development data container IDs/mounts and Phase 1 record counts/digests unchanged. All four UUID test projects removed only their own labeled containers/volumes/networks. API readiness 200 and SIMULATED/DENY_ALL; live trading, order submission and generated-code execution false. [Diagnostic source](preservation-check.txt) needs the private local before-state in ignored cache; it contains no secret values.

## Reproduce in an owner-permitted browser environment

Run from the project root with Chromium installed through the normal Playwright installer. The browser testing authorization already exists; this managed session is blocked by actual macOS `bootstrap_check_in ... Permission denied (1100)`. Do not bypass it.

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" P0_CACHED_IMAGES=1 make browser-integration
make check
P0_CACHED_IMAGES=1 make integration
```

The cached flag requires exact pinned images already available; otherwise omit it and use ordinary Docker pulls. The full command explicitly unsets both focus variables. Focused runs use the same genuine disposable services, worker, MFA and isolation; they cannot establish all-case acceptance.

## Exact execution records

Each JSON records exact argv, UTC start, duration, child exit code and sanitized output hash. [Capture helper](capture-command.txt) itself returns zero after recording child failure; only recorded child exit_code determines status. Failed attempts remain present.

[Source fingerprints](source-hashes.json) identify the final uncommitted non-evidence source; [changed files](changed-files.json) lists the eight source/document files edited in this follow-up. Older evidence directories describe earlier snapshots and remain historical records. No commit SHA, remote CI, browser pass, public deployment or Phase 3 is claimed.

- **desktop-before: child exit 2**, 81.382s, 2026-10-26T21:35:16.333583+00:00. `env P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration`. [Record](desktop-before.json), [output](desktop-before.txt).
- **desktop-after: child exit 2**, 84.675s, 2026-10-26T21:36:54.031477+00:00. `env P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration`. [Record](desktop-after.json), [output](desktop-after.txt).
- **check: child exit 2**, 0.118s, 2026-10-26T21:36:55.183128+00:00. `make check`. [Record](check.json), [output](check.txt).
- **check-verified: child exit 2**, 2.596s, 2026-10-26T21:37:16.289841+00:00. `make check`. [Record](check-verified.json), [output](check-verified.txt).
- **check-final: child exit 0**, 12.994s, 2026-10-26T21:37:49.989284+00:00. `make check`. [Record](check-final.json), [output](check-final.txt).
- **e2e-collection: child exit 0**, 1.013s, 2026-10-26T21:37:51.130448+00:00. `npm --prefix apps/web run test:e2e -- --list`. [Record](e2e-collection.json), [output](e2e-collection.txt).
- **full-e2e: child exit 2**, 85.932s, 2026-10-26T21:38:22.903854+00:00. `env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO P0_CACHED_IMAGES=1 make browser-integration`. [Record](full-e2e.json), [output](full-e2e.txt).
- **contracts: child exit 0**, 1.977s, 2026-10-26T21:39:48.953774+00:00. `make contracts-check`. [Record](contracts.json), [output](contracts.txt).
- **integration: child exit 0**, 79.086s, 2026-10-26T21:39:55.185830+00:00. `env P0_CACHED_IMAGES=1 make integration`. [Record](integration.json), [output](integration.txt).
- **smoke: child exit 0**, 0.323s, 2026-10-26T21:40:24.216393+00:00. `make smoke-demo`. [Record](smoke.json), [output](smoke.txt).
- **preservation: child exit 0**, 1.108s, 2026-10-26T21:41:27.020477+00:00. `.venv/bin/python .cache/phase2-browser-fix/preserve.py`. [Record](preservation.json), [output](preservation.txt).

- **repository: child exit 0**, 0.077s, 2026-10-26T21:42:34.583484+00:00. `make repository-check`. [Record](repository.json), [output](repository.txt).

- **secrets: child exit 0**, 0.902s, 2026-10-26T21:42:34.741611+00:00. `make secret-scan`. [Record](secrets.json), [output](secrets.txt).
