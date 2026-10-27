# Phase 1 execution evidence — 2026-10-26

Each command JSON contains exact argv (including full inline diagnostic code), UTC start, duration,
actual child exit code and sanitized-output SHA-256. The .txt file is its output. The capture
wrapper returns zero after recording any child exit; rely on the recorded child exit_code.
Failed attempts are retained. Collection/static builds never count as browser acceptance.

This directory remains under the existing phase0-evidence parent for continuity; its contents
document Phase 1. No secrets, private database dump or generated browser authentication traces
are intentionally included. The prior implementation status is an explicitly historical snapshot.

Latest acceptance: acceptance-quality (81 Python, 16 frontend), acceptance-integration (one app
readiness case plus 20 native cases in each stage), native schema/boundary diagnostics pass.
Browser-acceptance failed: three desktop Chromium permission failures, one HTTP-only pass;
mobile NOT RUN after desktop failure. Owner authorization did not remove the OS restriction.

## Command ledger

- [first-native-integration](first-native-integration.json): `make integration-services` — exit **0**, 22.917s, 2026-10-26T13:29:32.928620+00:00. [Output](first-native-integration.txt).
- [expanded-native-integration](expanded-native-integration.json): `make integration-services` — exit **2**, 15.733s, 2026-10-26T13:45:56.169851+00:00. [Output](expanded-native-integration.txt).
- [first-complete-check](first-complete-check.json): `make check` — exit **0**, 7.416s, 2026-10-26T13:45:56.169853+00:00. [Output](first-complete-check.txt).
- [expanded-native-integration-fixed](expanded-native-integration-fixed.json): `make integration-services` — exit **0**, 28.252s, 2026-10-26T13:47:53.183294+00:00. [Output](expanded-native-integration-fixed.txt).
- [local-identity-setup](local-identity-setup.json): `make identity-setup` — exit **0**, 0.171s, 2026-10-26T14:00:40.886636+00:00. [Output](local-identity-setup.txt).
- [pre-migration-backup](pre-migration-backup.json): `Inline diagnostic — exact argv/code in JSON` — exit **0**, 0.424s, 2026-10-26T14:02:12.614176+00:00. [Output](pre-migration-backup.txt).
- [local-image-build](local-image-build.json): `env BUILDX_CONFIG=.cache/buildx docker compose build api web migrate` — exit **0**, 5.187s, 2026-10-26T14:02:13.160440+00:00. [Output](local-image-build.txt).
- [local-stack-up](local-stack-up.json): `docker compose up -d --wait --wait-timeout 180 api web` — exit **1**, 2.074s, 2026-10-26T14:08:56.997521+00:00. [Output](local-stack-up.txt).
- [local-migration-failure](local-migration-failure.json): `docker compose logs --no-color migrate` — exit **0**, 0.07s, 2026-10-26T14:09:13.807436+00:00. [Output](local-migration-failure.txt).
- [local-packaging-build](local-packaging-build.json): `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate` — exit **0**, 2.256s, 2026-10-26T14:09:51.025994+00:00. [Output](local-packaging-build.txt).
- [local-stack-up-fixed](local-stack-up-fixed.json): `docker compose up -d --wait --wait-timeout 180 api web` — exit **0**, 23.639s, 2026-10-26T14:09:59.525003+00:00. [Output](local-stack-up-fixed.txt).
- [main-readiness-and-preservation](main-readiness-and-preservation.json): `Inline diagnostic — exact argv/code in JSON` — exit **0**, 0.545s, 2026-10-26T14:11:21.530347+00:00. [Output](main-readiness-and-preservation.txt).
- [expanded-check](expanded-check.json): `make check` — exit **2**, 1.966s, 2026-10-26T14:11:39.018998+00:00. [Output](expanded-check.txt).
- [final-integration](final-integration.json): `make integration` — exit **0**, 32.258s, 2026-10-26T14:11:39.750471+00:00. [Output](final-integration.txt).
- [final-check](final-check.json): `make check` — exit **2**, 0.071s, 2026-10-26T14:12:32.493111+00:00. [Output](final-check.txt).
- [npm-audit](npm-audit.json): `npm --prefix apps/web audit --audit-level=high` — exit **0**, 0.625s, 2026-10-26T14:13:02.665412+00:00. [Output](npm-audit.txt).
- [final-check-fixed](final-check-fixed.json): `make check` — exit **2**, 5.092s, 2026-10-26T14:13:02.665417+00:00. [Output](final-check-fixed.txt).
- [python-audit](python-audit.json): `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --progress-spinner off` — exit **1**, 0.713s, 2026-10-26T14:13:02.668421+00:00. [Output](python-audit.txt).
- [playwright-collection](playwright-collection.json): `npm --prefix apps/web run test:e2e -- --list` — exit **0**, 0.62s, 2026-10-26T14:13:02.673105+00:00. [Output](playwright-collection.txt).
- [python-audit-local-cache](python-audit-local-cache.json): `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off` — exit **0**, 4.034s, 2026-10-26T14:13:11.078952+00:00. [Output](python-audit-local-cache.txt).
- [final-quality](final-quality.json): `make check` — exit **0**, 8.152s, 2026-10-26T14:13:36.172609+00:00. [Output](final-quality.txt).
- [final-images](final-images.json): `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web` — exit **0**, 5.325s, 2026-10-26T14:13:37.334253+00:00. [Output](final-images.txt).
- [actionlint](actionlint.json): `.tools/bin/actionlint .github/workflows/ci.yml` — exit **0**, 0.255s, 2026-10-26T14:13:38.496949+00:00. [Output](actionlint.txt).
- [compose-validation](compose-validation.json): `docker compose config --quiet` — exit **0**, 0.065s, 2026-10-26T14:13:38.783367+00:00. [Output](compose-validation.txt).
- [contracts-check](contracts-check.json): `make contracts-check` — exit **0**, 2.507s, 2026-10-26T14:13:38.879135+00:00. [Output](contracts-check.txt).
- [browser-acceptance](browser-acceptance.json): `make browser-integration` — exit **2**, 74.203s, 2026-10-26T14:37:29.417846+00:00. [Output](browser-acceptance.txt).
- [final-stack-up](final-stack-up.json): `docker compose up -d --wait --wait-timeout 180 api web` — exit **0**, 28.359s, 2026-10-26T14:37:41.125810+00:00. [Output](final-stack-up.txt).
- [current-smoke](current-smoke.json): `make smoke-demo` — exit **0**, 0.309s, 2026-10-26T14:38:23.823911+00:00. [Output](current-smoke.txt).
- [current-strict-readiness](current-strict-readiness.json): `.venv/bin/python -m scripts.smoke_demo --require-ready` — exit **0**, 0.264s, 2026-10-26T14:38:24.181171+00:00. [Output](current-strict-readiness.txt).
- [source-secrets](source-secrets.json): `make secret-scan` — exit **0**, 0.848s, 2026-10-26T14:46:49.859645+00:00. [Output](source-secrets.txt).
- [source-exclusions](source-exclusions.json): `make repository-check` — exit **0**, 0.083s, 2026-10-26T14:46:50.758400+00:00. [Output](source-exclusions.txt).
- [acceptance-quality](acceptance-quality.json): `make check` — exit **0**, 13.776s, 2026-10-26T14:47:39.086959+00:00. [Output](acceptance-quality.txt).
- [acceptance-integration](acceptance-integration.json): `make integration` — exit **0**, 52.119s, 2026-10-26T14:47:40.098385+00:00. [Output](acceptance-integration.txt).
- [acceptance-api-image](acceptance-api-image.json): `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate` — exit **0**, 3.616s, 2026-10-26T14:47:41.264122+00:00. [Output](acceptance-api-image.txt).
- [acceptance-stack-up](acceptance-stack-up.json): `docker compose up -d --wait --wait-timeout 180 api web` — exit **0**, 14.715s, 2026-10-26T14:50:35.899589+00:00. [Output](acceptance-stack-up.txt).
- [acceptance-preservation-and-boundaries](acceptance-preservation-and-boundaries.json): `Inline diagnostic — exact argv/code in JSON` — exit **0**, 1.47s, 2026-10-26T14:51:34.966241+00:00. [Output](acceptance-preservation-and-boundaries.txt).
- [schema-drift](schema-drift.json): `Inline diagnostic — exact argv/code in JSON` — exit **0**, 0.876s, 2026-10-26T14:52:39.566469+00:00. [Output](schema-drift.txt).
- [final-source-secrets](final-source-secrets.json): `make secret-scan` — exit **0**, 0.794s, 2026-10-26T14:55:45.205682+00:00. [Output](final-source-secrets.txt).
- [final-source-exclusions](final-source-exclusions.json): `make repository-check` — exit **0**, 0.084s, 2026-10-26T14:55:46.049526+00:00. [Output](final-source-exclusions.txt).
- [final-contracts](final-contracts.json): `make contracts-check` — exit **0**, 2.163s, 2026-10-26T14:55:46.179448+00:00. [Output](final-contracts.txt).
- [evidence-secret-scan](evidence-secret-scan.json): `make secret-scan` — exit **0**, 0.767s, 2026-10-26T14:56:43.874807+00:00. [Output](evidence-secret-scan.txt).

## Source fingerprints

source-hashes.json covers current Git-selected non-evidence source/docs; source-changes.json compares
it with the private pre-implementation snapshot. Evidence directories are excluded to avoid recursive
hashes. No commit exists, so these hashes identify the reviewed snapshot without inventing a SHA.
The ignored private .env and private dumps are not part of this inventory.
capture-command.txt preserves the small command recorder used for this evidence.
