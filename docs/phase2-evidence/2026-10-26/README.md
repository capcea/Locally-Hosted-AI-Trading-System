# Phase 2 execution evidence — 2026-10-26

Decision: **IMPLEMENTED / NATIVE TESTED; browser acceptance BLOCKED.**

Each command entry links its exact argv, UTC start, duration, child exit code and sanitized log SHA-256. The capture helper exits zero after writing a child failure; statuses use JSON child exit_code. This ledger includes failed intermediate attempts. A zero exit from a collection/build does not prove browser acceptance.

Final functional checks: quality-coverage-regression (98 Python, 16 frontend), final-native-suite (1 readiness and 27 cases per native stage), final-coverage-native (27 per stage including corrected coverage and derived Parquet), acceptance-stack, final-runtime-verified, final-smoke, final-strict-smoke, final-contracts, final-actions, final-compose and final-secrets-sanitized. Dependency/npm audits are actual local scans; no remote CI/container scan/restore success is claimed.

browser-attempt failed with the macOS Chromium launch denial: 3 page cases failed, 1 request-only case passed, 6 later cases NOT RUN. Ten cases collect in collected. No browser workaround was used.

first-native: Docker Keychain pull error; cached flag was used only after pinned image availability was checked. native-cached: MinIO admin exception handling and first fixture failures. market-portable: original timestamp loss. Static errors and their fixes remain visible. final-runtime: diagnostic incorrectly treated a null/unbound EXPOSE entry as host publishing; final-runtime-verified checks actual host binding lists and passes. final-secrets found four temporary MinIO accessKey identity fields in an old failed SDK traceback. They were redacted, the failed test status preserved and hash refreshed; no scanning exclusion was added. See [sanitization record](evidence-sanitization.json).

[Source fingerprints](source-hashes.json) and [changes from the private baseline](source-changes.json) identify the uncommitted source snapshot. Original PRODUCT_SPEC.md hash matches the owner file. Evidence directories are excluded from source hashing to avoid recursion. [Capture helper](capture-command.txt) and [read-only runtime diagnostic](runtime-check.txt) preserve reproduction code; the diagnostic also needs the private local before-state fingerprints in .cache/phase2. No secret/dump/raw data is included. Runtime grants/ports/root filesystems, schema drift, 2 MiB temporary upload spooling, preserved empty Phase 1 records/data mounts and HTTP/CSP checks passed. Browser rendering/enforcement remains unverified.

[Actual ECB verification](ecb-service-verification.json): five daily reference observations, no intraday/tick/OHLC/volume or five-year claim. [Write benchmark](benchmark-write.json) and [restart benchmark](benchmark-verify.json) measure one 30,000-row synthetic fixture against actual services with real worker SIGKILL; lease expiry was advanced explicitly. They do not certify production scale.

## Commands in execution order

- **first-portable — child exit 0**, 6.924s, 2026-10-26T19:23:56.422947+00:00. `.venv/bin/python -m pytest -m 'not infrastructure and not isolated_services'`. [Record](first-portable.json), [output](first-portable.txt).
- **first-native — child exit 2**, 39.248s, 2026-10-26T19:25:33.702821+00:00. `make integration-services`. [Record](first-native.json), [output](first-native.txt).
- **market-portable — child exit 1**, 1.784s, 2026-10-26T19:27:16.377604+00:00. `.venv/bin/python -m pytest tests/test_market_time_quality.py -q`. [Record](market-portable.json), [output](market-portable.txt).
- **native-cached — child exit 2**, 27.813s, 2026-10-26T19:27:54.294785+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](native-cached.json), [output](native-cached.txt).
- **native-storage-fix — child exit 0**, 78.197s, 2026-10-26T19:30:10.440439+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](native-storage-fix.json), [output](native-storage-fix.txt).
- **portable-new — child exit 0**, 4.019s, 2026-10-26T19:31:21.073119+00:00. `.venv/bin/python -m pytest tests/test_market_time_quality.py -q`. [Record](portable-new.json), [output](portable-new.txt).
- **expanded-native — child exit 0**, 60.421s, 2026-10-26T19:35:27.481163+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](expanded-native.json), [output](expanded-native.txt).
- **first-check — child exit 2**, 0.056s, 2026-10-26T19:37:56.713306+00:00. `make check`. [Record](first-check.json), [output](first-check.txt).
- **expanded-check — child exit 2**, 0.091s, 2026-10-26T19:38:29.658448+00:00. `make check`. [Record](expanded-check.json), [output](expanded-check.txt).
- **market-config — child exit 0**, 0.328s, 2026-10-26T19:38:29.829151+00:00. `make market-setup`. [Record](market-config.json), [output](market-config.txt).
- **quality-pass-candidate — child exit 0**, 13.946s, 2026-10-26T19:39:22.523213+00:00. `make check`. [Record](quality-pass-candidate.json), [output](quality-pass-candidate.txt).
- **crash-and-provider-native — child exit 0**, 122.543s, 2026-10-26T19:39:23.252215+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](crash-and-provider-native.json), [output](crash-and-provider-native.txt).
- **private-pre-migration-backup — child exit 1**, 0.263s, 2026-10-26T19:39:24.428396+00:00. exact argv in linked JSON (multiline/long command). [Record](private-pre-migration-backup.json), [output](private-pre-migration-backup.txt).
- **current-data-start — child exit 0**, 5.898s, 2026-10-26T19:39:36.589142+00:00. `docker compose up --pull never --no-build -d --wait --wait-timeout 120 postgres redis minio`. [Record](current-data-start.json), [output](current-data-start.txt).
- **images — child exit 0**, 40.142s, 2026-10-26T19:39:55.542848+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker`. [Record](images.json), [output](images.txt).
- **private-backup-after-start — child exit 0**, 2.591s, 2026-10-26T19:40:33.624283+00:00. exact argv in linked JSON (multiline/long command). [Record](private-backup-after-start.json), [output](private-backup-after-start.txt).
- **latest-images — child exit 0**, 2.874s, 2026-10-26T19:42:44.084642+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate market-worker`. [Record](latest-images.json), [output](latest-images.txt).
- **browser-attempt — child exit 2**, 126.455s, 2026-10-26T19:43:25.204542+00:00. `env P0_CACHED_IMAGES=1 make browser-integration`. [Record](browser-attempt.json), [output](browser-attempt.txt).
- **start-stack — child exit 0**, 30.959s, 2026-10-26T19:43:26.349047+00:00. `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker`. [Record](start-stack.json), [output](start-stack.txt).
- **preservation — child exit 0**, 3.033s, 2026-10-26T19:44:30.448667+00:00. exact argv in linked JSON (multiline/long command). [Record](preservation.json), [output](preservation.txt).
- **dependency-audit — child exit 0**, 9.737s, 2026-10-26T19:45:34.852602+00:00. `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`. [Record](dependency-audit.json), [output](dependency-audit.txt).
- **npm-audit — child exit 0**, 0.740s, 2026-10-26T19:45:36.008479+00:00. `npm --prefix apps/web audit --audit-level=high`. [Record](npm-audit.json), [output](npm-audit.txt).
- **actions-lint — child exit 0**, 0.037s, 2026-10-26T19:45:36.823276+00:00. `.tools/bin/actionlint .github/workflows/ci.yml`. [Record](actions-lint.json), [output](actions-lint.txt).
- **compose-config — child exit 0**, 0.120s, 2026-10-26T19:45:36.934433+00:00. `docker compose config --quiet`. [Record](compose-config.json), [output](compose-config.txt).
- **collected — child exit 0**, 3.022s, 2026-10-26T19:45:37.135309+00:00. `npm --prefix apps/web run test:e2e -- --list`. [Record](collected.json), [output](collected.txt).
- **final-check — child exit 2**, 0.048s, 2026-10-26T19:47:54.813466+00:00. `make check`. [Record](final-check.json), [output](final-check.txt).
- **final-quality — child exit 2**, 2.326s, 2026-10-26T19:49:14.325505+00:00. `make check`. [Record](final-quality.json), [output](final-quality.txt).
- **full-integration — child exit 0**, 143.774s, 2026-10-26T19:50:43.285798+00:00. `env P0_CACHED_IMAGES=1 make integration`. [Record](full-integration.json), [output](full-integration.txt).
- **verified-quality — child exit 0**, 26.899s, 2026-10-26T19:50:45.861019+00:00. `make check`. [Record](verified-quality.json), [output](verified-quality.txt).
- **native-final-with-ticks — child exit 0**, 125.051s, 2026-10-26T19:52:10.991475+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](native-final-with-ticks.json), [output](native-final-with-ticks.txt).
- **release-images — child exit 0**, 27.697s, 2026-10-26T19:52:12.071194+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker`. [Record](release-images.json), [output](release-images.txt).
- **contracts-final — child exit 0**, 2.390s, 2026-10-26T19:54:29.612314+00:00. `make contracts-check`. [Record](contracts-final.json), [output](contracts-final.txt).
- **secrets-pre-docs — child exit 2**, 0.827s, 2026-10-26T19:54:32.051849+00:00. `make secret-scan`. [Record](secrets-pre-docs.json), [output](secrets-pre-docs.txt).
- **final-build — child exit 0**, 2.886s, 2026-10-26T19:56:22.088547+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate market-worker`. [Record](final-build.json), [output](final-build.txt).
- **release-quality — child exit 0**, 13.111s, 2026-10-26T19:58:08.711633+00:00. `make check`. [Record](release-quality.json), [output](release-quality.txt).
- **accepted-quality — child exit 0**, 18.978s, 2026-10-26T20:00:25.925797+00:00. `make check`. [Record](accepted-quality.json), [output](accepted-quality.txt).
- **final-quality-verified — child exit 0**, 25.013s, 2026-10-26T20:00:55.728315+00:00. `make check`. [Record](final-quality-verified.json), [output](final-quality-verified.txt).
- **final-image-verified — child exit 0**, 17.576s, 2026-10-26T20:00:56.578501+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker`. [Record](final-image-verified.json), [output](final-image-verified.txt).
- **final-contract-verified — child exit 0**, 2.746s, 2026-10-26T20:01:20.835329+00:00. `make contracts-check`. [Record](final-contract-verified.json), [output](final-contract-verified.txt).
- **final-stack — child exit 0**, 25.686s, 2026-10-26T20:04:53.409954+00:00. `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker`. [Record](final-stack.json), [output](final-stack.txt).
- **final-native-suite — child exit 0**, 79.031s, 2026-10-26T20:04:54.532357+00:00. `env P0_CACHED_IMAGES=1 make integration`. [Record](final-native-suite.json), [output](final-native-suite.txt).
- **frontend-after-state-fix — child exit 0**, 24.334s, 2026-10-26T20:11:15.154210+00:00. `make check`. [Record](frontend-after-state-fix.json), [output](frontend-after-state-fix.txt).
- **web-after-state-fix — child exit 0**, 16.576s, 2026-10-26T20:11:15.881612+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build web`. [Record](web-after-state-fix.json), [output](web-after-state-fix.txt).
- **final-derived-native — child exit 0**, 98.772s, 2026-10-26T20:14:02.841647+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](final-derived-native.json), [output](final-derived-native.txt).
- **timezone-validation-fix — child exit 0**, 21.448s, 2026-10-26T20:22:03.325969+00:00. `make check`. [Record](timezone-validation-fix.json), [output](timezone-validation-fix.txt).
- **timezone-fix-images — child exit 0**, 6.824s, 2026-10-26T20:22:04.301616+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate market-worker`. [Record](timezone-fix-images.json), [output](timezone-fix-images.txt).
- **quality-coverage-regression — child exit 0**, 16.611s, 2026-10-26T20:26:02.520722+00:00. `make check`. [Record](quality-coverage-regression.json), [output](quality-coverage-regression.txt).
- **final-coverage-native — child exit 0**, 120.142s, 2026-10-26T20:26:38.288130+00:00. `env P0_CACHED_IMAGES=1 make integration-services`. [Record](final-coverage-native.json), [output](final-coverage-native.txt).
- **final-coverage-images — child exit 0**, 3.113s, 2026-10-26T20:26:39.446867+00:00. `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate market-worker`. [Record](final-coverage-images.json), [output](final-coverage-images.txt).
- **acceptance-stack — child exit 0**, 25.331s, 2026-10-26T20:31:42.643678+00:00. `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker`. [Record](acceptance-stack.json), [output](acceptance-stack.txt).
- **final-contracts — child exit 0**, 2.696s, 2026-10-26T20:31:51.323563+00:00. `make contracts-check`. [Record](final-contracts.json), [output](final-contracts.txt).
- **final-compose — child exit 0**, 0.215s, 2026-10-26T20:31:51.323591+00:00. `docker compose config --quiet`. [Record](final-compose.json), [output](final-compose.txt).
- **final-actions — child exit 0**, 0.083s, 2026-10-26T20:31:51.323836+00:00. `.tools/bin/actionlint .github/workflows/ci.yml`. [Record](final-actions.json), [output](final-actions.txt).
- **final-runtime — child exit 1**, 1.101s, 2026-10-26T20:32:36.334897+00:00. `.venv/bin/python .cache/phase2/final_runtime_check.py`. [Record](final-runtime.json), [output](final-runtime.txt).
- **final-strict-smoke — child exit 0**, 0.534s, 2026-10-26T20:32:37.479442+00:00. `.venv/bin/python -m scripts.smoke_demo --require-ready`. [Record](final-strict-smoke.json), [output](final-strict-smoke.txt).
- **final-smoke — child exit 0**, 0.533s, 2026-10-26T20:32:37.479620+00:00. `make smoke-demo`. [Record](final-smoke.json), [output](final-smoke.txt).
- **final-runtime-verified — child exit 0**, 3.738s, 2026-10-26T20:33:06.778892+00:00. `.venv/bin/python .cache/phase2/final_runtime_check.py`. [Record](final-runtime-verified.json), [output](final-runtime-verified.txt).
- **final-repository — child exit 0**, 0.092s, 2026-10-26T20:33:29.005758+00:00. `make repository-check`. [Record](final-repository.json), [output](final-repository.txt).
- **final-secrets — child exit 2**, 0.896s, 2026-10-26T20:33:29.180584+00:00. `make secret-scan`. [Record](final-secrets.json), [output](final-secrets.txt).
- **final-secrets-sanitized — child exit 0**, 1.030s, 2026-10-26T20:34:21.558335+00:00. `make secret-scan`. [Record](final-secrets-sanitized.json), [output](final-secrets-sanitized.txt).
- **release-repository — child exit 0**, 0.075s, 2026-10-26T20:35:10.294551+00:00. `make repository-check`. [Record](release-repository.json), [output](release-repository.txt).
- **release-secrets — child exit 0**, 0.944s, 2026-10-26T20:35:10.474029+00:00. `make secret-scan`. [Record](release-secrets.json), [output](release-secrets.txt).

The local .git directory is read-only. No initial commit, remote repository, push, public deployment, Phase 3, broker order or live/generated-code execution was performed.
