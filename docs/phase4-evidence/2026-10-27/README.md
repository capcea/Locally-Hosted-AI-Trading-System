# Phase 4 execution ledger

Actual recorded commands on 2026-10-27. Each linked JSON contains exact argv, UTC start, duration,
child exit status and sanitized log SHA-256. Wrapper exit0 does not override child failure. Logs preserve
earlier failures and fixes; no browser/infrastructure results are fabricated. Repeated service stages
are not unique-case counts. See ../../../PHASE4_COMPLETION_REPORT.md for final interpretation.

Private .env/dumps/raw traces are excluded. native-first had seven synthetic business idempotency
suffixes redacted after the source scan; original hash/private copy are retained and no scanner rules
were relaxed. Other logs use environment-secret redaction. Existing historical evidence is unchanged.

- `baseline-check` — child exit **0**, 13.176s; [record](baseline-check.json), [log](baseline-check.txt).
  Command: `make check`.
- `migration-portable` — child exit **0**, 2.086s; [record](migration-portable.json), [log](migration-portable.txt).
  Command: `.venv/bin/python -m pytest tests/test_migrations.py -q`.
- `risk-math-first` — child exit **0**, 2.142s; [record](risk-math-first.json), [log](risk-math-first.txt).
  Command: `.venv/bin/python -m pytest tests/test_risk_math.py tests/test_execution_engine.py -q`.
- `native-first` — child exit **2**, 55.404s; [record](native-first.json), [log](native-first.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `native-account-balance` — child exit **2**, 59.476s; [record](native-account-balance.json), [log](native-account-balance.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `contracts-first` — child exit **0**, 2.859s; [record](contracts-first.json), [log](contracts-first.txt).
  Command: `make contracts`.
- `native-fill-buffer` — child exit **2**, 60.8s; [record](native-fill-buffer.json), [log](native-fill-buffer.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `native-decimal-projection` — child exit **0**, 112.078s; [record](native-decimal-projection.json), [log](native-decimal-projection.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `native-adversarial-first` — child exit **0**, 156.704s; [record](native-adversarial-first.json), [log](native-adversarial-first.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `compose-risk-config` — child exit **0**, 0.202s; [record](compose-risk-config.json), [log](compose-risk-config.txt).
  Command: `docker compose config --quiet`.
- `native-extended` — child exit **2**, 95.416s; [record](native-extended.json), [log](native-extended.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `portable-risk-current` — child exit **0**, 4.687s; [record](portable-risk-current.json), [log](portable-risk-current.txt).
  Command: `.venv/bin/python -m pytest -m 'not infrastructure and not isolated_services' -q`.
- `contracts-current` — child exit **0**, 2.805s; [record](contracts-current.json), [log](contracts-current.txt).
  Command: `make contracts`.
- `native-extended-stable` — child exit **0**, 185.665s; [record](native-extended-stable.json), [log](native-extended-stable.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `risk-math-expanded` — child exit **0**, 2.062s; [record](risk-math-expanded.json), [log](risk-math-expanded.txt).
  Command: `.venv/bin/python -m pytest tests/test_risk_math.py -q`.
- `clock-funding-unit` — child exit **0**, 2.039s; [record](clock-funding-unit.json), [log](clock-funding-unit.txt).
  Command: `.venv/bin/python -m pytest tests/test_execution_engine.py tests/test_risk_math.py -q`.
- `native-boundary` — child exit **2**, 101.87s; [record](native-boundary.json), [log](native-boundary.txt).
  Command: `env P0_CACHED_IMAGES=1 make integration-services`.
- `native-final-candidate` — child exit **0**, 206.071s; [record](native-final-candidate.json), [log](native-final-candidate.txt).
  Command: `make integration-services`.
- `preservation-before` — child exit **0**, 6.062s; [record](preservation-before.json), [log](preservation-before.txt).
  Command: `.venv/bin/python .cache/phase4/preserve.py before`.
- `contracts-phase4` — child exit **0**, 3.348s; [record](contracts-phase4.json), [log](contracts-phase4.txt).
  Command: `make contracts`.
- `check-phase4` — child exit **2**, 0.137s; [record](check-phase4.json), [log](check-phase4.txt).
  Command: `make check`.
- `browser-risk-desktop` — child exit **2**, 224.713s; [record](browser-risk-desktop.json), [log](browser-risk-desktop.txt).
  Command: `env E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=risk make browser-integration`.
- `check-phase4-lint-fixed` — child exit **0**, 22.752s; [record](check-phase4-lint-fixed.json), [log](check-phase4-lint-fixed.txt).
  Command: `make check`.
- `build-phase4` — child exit **1**, 0.578s; [record](build-phase4.json), [log](build-phase4.txt).
  Command: `docker compose build api migrate web market-worker risk-monitor`.
- `build-phase4-workspace` — child exit **0**, 15.862s; [record](build-phase4-workspace.json), [log](build-phase4-workspace.txt).
  Command: `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker risk-monitor`.
- `python-audit` — child exit **0**, 5.651s; [record](python-audit.json), [log](python-audit.txt).
  Command: `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`.
- `npm-audit` — child exit **0**, 1.614s; [record](npm-audit.json), [log](npm-audit.txt).
  Command: `npm --prefix apps/web audit --audit-level=high`.
- `contracts-check` — child exit **0**, 5.35s; [record](contracts-check.json), [log](contracts-check.txt).
  Command: `make contracts-check`.
- `stack-phase4` — child exit **1**, 16.695s; [record](stack-phase4.json), [log](stack-phase4.txt).
  Command: `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker risk-monitor`.
- `local-config` — child exit **0**, 0.174s; [record](local-config.json), [log](local-config.txt).
  Command: `.venv/bin/python -c 'import subprocess; subprocess.run(["docker","compose","config","--quiet"],check=True); subprocess.run([".tools/bin/actionlint"],check=True); print("PASSED: Compose and pinned Actions syntax. Remote CI NOT RUN.")'`.
- `browser-collect` — child exit **1**, 0.411s; [record](browser-collect.json), [log](browser-collect.txt).
  Command: `npm --prefix apps/web run e2e -- --list`.
- `browser-collection` — child exit **0**, 1.009s; [record](browser-collection.json), [log](browser-collection.txt).
  Command: `npm --prefix apps/web run test:e2e -- --list`.
- `risk-monitor-start-failure` — child exit **0**, 0.12s; [record](risk-monitor-start-failure.json), [log](risk-monitor-start-failure.txt).
  Command: `docker compose logs --no-color risk-monitor`.
- `browser-full` — child exit **2**, 230.178s; [record](browser-full.json), [log](browser-full.txt).
  Command: `make browser-integration`.
- `build-monitor-packaging` — child exit **0**, 3.401s; [record](build-monitor-packaging.json), [log](build-monitor-packaging.txt).
  Command: `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate market-worker risk-monitor`.
- `preservation-after` — child exit **1**, 4.894s; [record](preservation-after.json), [log](preservation-after.txt).
  Command: `.venv/bin/python .cache/phase4/preserve.py after`.
- `secret-scan-first` — child exit **2**, 1.292s; [record](secret-scan-first.json), [log](secret-scan-first.txt).
  Command: `make secret-scan`.
- `stack-monitor-fixed` — child exit **0**, 26.041s; [record](stack-monitor-fixed.json), [log](stack-monitor-fixed.txt).
  Command: `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker risk-monitor`.
- `session-preservation` — child exit **1**, 0.238s; [record](session-preservation.json), [log](session-preservation.txt).
  Command: `.venv/bin/python .cache/phase4/session_preservation.py`.
- `session-preservation-comparison` — child exit **0**, 0.332s; [record](session-preservation-comparison.json), [log](session-preservation-comparison.txt).
  Command: `.venv/bin/python .cache/phase4/session_preservation.py`.
- `runtime-validation` — child exit **1**, 0.369s; [record](runtime-validation.json), [log](runtime-validation.txt).
  Command: `.venv/bin/python .cache/phase4/validate_runtime.py`.
- `integration-final` — child exit **0**, 213.032s; [record](integration-final.json), [log](integration-final.txt).
  Command: `make integration`.
- `runtime-validation-path` — child exit **0**, 9.169s; [record](runtime-validation-path.json), [log](runtime-validation-path.txt).
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase4/validate_runtime.py`.
- `smoke-final` — child exit **0**, 0.489s; [record](smoke-final.json), [log](smoke-final.txt).
  Command: `make smoke-demo`.
- `risk-monitor-once` — child exit **0**, 7.701s; [record](risk-monitor-once.json), [log](risk-monitor-once.txt).
  Command: `docker compose exec -T risk-monitor /app/.venv/bin/python -m scripts.risk_monitor --once`.
- `preservation-final` — child exit **0**, 6.478s; [record](preservation-final.json), [log](preservation-final.txt).
  Command: `.venv/bin/python .cache/phase4/preserve.py after`.
- `check-final` — child exit **0**, 14.379s; [record](check-final.json), [log](check-final.txt).
  Command: `make check`.
- `repository-final` — child exit **0**, 0.089s; [record](repository-final.json), [log](repository-final.txt).
  Command: `make repository-check`.
- `secret-final` — child exit **0**, 1.001s; [record](secret-final.json), [log](secret-final.txt).
  Command: `make secret-scan`.

Current browser failures are Chromium OS launch Permission denied (1100), before page creation.
Focused risk: 1 failed launch; full default:3 failed launch/1 HTTP-only pass/10 later NOT RUN.
Native tests passed60 cases in each write/restart stage; current complete makeintegration also passed
one running-API readiness case and strict readiness/execution-denial smoke. No Phase5 work.

Source differences are captured in source-changes.json, excluding evidence to avoid recursive hashes.

Final delivery scan: `make secret-scan`, child exit0; [record](delivery-secret-scan.json), [log](delivery-secret-scan.txt).
