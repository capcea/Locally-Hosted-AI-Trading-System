# Phase 0 command evidence

Work began 2026-10-25; current handoff date is 2026-10-26 (Europe/Bucharest).
Individual records preserve actual UTC timestamps. These are local execution results, not remote CI.
The capture wrapper writes the child command exit code even when the wrapper itself returns normally.
Sanitized transcripts are .txt; raw operational .log files and ignored runtime state are excluded.

See [PHASE0_COMPLETION_REPORT.md](../../../PHASE0_COMPLETION_REPORT.md) for interpretation.

## Command ledger

- **dependency-lock**: `.tools/bin/uv lock` — exit **0**, 1.761 s, UTC 2026-10-25T17:57:00.327984+00:00. [Transcript](dependency-lock.txt), [record](dependency-lock.json).
- **dependency-sync**: `.tools/bin/uv sync --frozen` — exit **0**, 2.569 s, UTC 2026-10-25T18:00:10.118916+00:00. [Transcript](dependency-sync.txt), [record](dependency-sync.json).
- **initial-check**: `make check` — exit **2**, 0.085 s, UTC 2026-10-25T18:00:49.320382+00:00. [Transcript](initial-check.txt), [record](initial-check.json).
- **initial-types**: `.venv/bin/python -m mypy` — exit **1**, 0.732 s, UTC 2026-10-25T18:00:49.320386+00:00. [Transcript](initial-types.txt), [record](initial-types.json).
- **final-check**: `make check` — exit **0**, 11.775 s, UTC 2026-10-25T18:01:21.654055+00:00. [Transcript](final-check.txt), [record](final-check.json).
- **docker-engine**: `docker info --format '{{json .ServerVersion}}'` — exit **1**, 0.817 s, UTC 2026-10-25T22:26:05.886847+00:00. [Transcript](docker-engine.txt), [record](docker-engine.json).
- **contracts-check**: `make contracts-check` — exit **0**, 1.333 s, UTC 2026-10-25T22:26:05.886849+00:00. [Transcript](contracts-check.txt), [record](contracts-check.json).
- **integration**: `make integration` — exit **2**, 1.426 s, UTC 2026-10-25T22:26:05.886871+00:00. [Transcript](integration.txt), [record](integration.json).
- **isolated-services**: `make integration-services` — exit **2**, 0.838 s, UTC 2026-10-25T22:26:05.886874+00:00. [Transcript](isolated-services.txt), [record](isolated-services.json).
- **npm-audit**: `npm --prefix apps/web audit --audit-level=high` — exit **0**, 1.467 s, UTC 2026-10-25T22:26:05.888629+00:00. [Transcript](npm-audit.txt), [record](npm-audit.json).
- **pip-audit**: `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --progress-spinner off --cache-dir .cache/pip-audit` — exit **0**, 8.652 s, UTC 2026-10-25T22:26:05.888867+00:00. [Transcript](pip-audit.txt), [record](pip-audit.json).
- **actionlint**: `.tools/bin/actionlint -color .github/workflows/ci.yml` — exit **0**, 1.471 s, UTC 2026-10-25T22:26:05.888916+00:00. [Transcript](actionlint.txt), [record](actionlint.json).
- **e2e-list**: `npm --prefix apps/web run test:e2e -- --list` — exit **0**, 0.477 s, UTC 2026-10-25T22:26:34.585198+00:00. [Transcript](e2e-list.txt), [record](e2e-list.json).
- **smoke**: `make smoke-demo` — exit **0**, 0.442 s, UTC 2026-10-25T22:27:01.487207+00:00. [Transcript](smoke.txt), [record](smoke.json).
- **strict-readiness**: `.venv/bin/python -m scripts.smoke_demo --require-ready` — exit **1**, 0.443 s, UTC 2026-10-25T22:27:01.487443+00:00. [Transcript](strict-readiness.txt), [record](strict-readiness.json).
- **repository-check**: `make repository-check` — exit **0**, 0.141 s, UTC 2026-10-25T22:27:01.493176+00:00. [Transcript](repository-check.txt), [record](repository-check.json).
- **compose-config**: `docker compose config --quiet` — exit **0**, 0.495 s, UTC 2026-10-25T22:27:01.496494+00:00. [Transcript](compose-config.txt), [record](compose-config.json).
- **test-compose-config**: `env P0_DATABASE_NAME=phase0_syntax_validation P0_DATABASE_PASSWORD=SYNTAX_ONLY P0_STORAGE_PASSWORD=SYNTAX_ONLY docker compose -f compose.test.yaml config --quiet` — exit **0**, 0.491 s, UTC 2026-10-25T22:27:01.500265+00:00. [Transcript](test-compose-config.txt), [record](test-compose-config.json).
- **doctor**: `make doctor` — exit **2**, 0.702 s, UTC 2026-10-25T22:27:01.502617+00:00. [Transcript](doctor.txt), [record](doctor.json).
- **dev-start**: `make dev` — exit **2**, 0.27 s, UTC 2026-10-25T22:27:02.255497+00:00. [Transcript](dev-start.txt), [record](dev-start.json).
- **release-check**: `make check` — exit **0**, 5.418 s, UTC 2026-10-25T22:28:29.645570+00:00. [Transcript](release-check.txt), [record](release-check.json).
- **secret-scan**: `make secret-scan` — exit **0**, 0.388 s, UTC 2026-10-25T22:29:20.285672+00:00. [Transcript](secret-scan.txt), [record](secret-scan.json).

- **final-secret-scan**: `make secret-scan` — exit **0**, 0.426 s, UTC 2026-10-25T22:34:11.247922+00:00. [Transcript](final-secret-scan.txt), [record](final-secret-scan.json).

## Limits and failure history

- initial-check/initial-types record lint and typing failures in new code. These were repaired;
  release-check passes 58 Python tests and 13 frontend tests, plus lint/types/build.
- Four infrastructure-dependent cases are intentionally outside unit-only make check: the existing
  application readiness case and three new isolated service cases. The existing case was executed
  and failed. The disposable harness was separately invoked and blocked before starting containers.
- Two unit tests mock harness command responses to verify cleanup/failure propagation; they are
  explicitly MOCKED and are not proof of Docker/Postgres/Redis/MinIO behavior.
- Smoke passed bounded API/denial checks with HTTP 503 dependency readiness; strict-readiness failed.
- Docker info/dev-start/doctor/isolated-services are nonzero because the daemon socket is absent.
- e2e-list collected six cases. browser-block.json records an unresolved prior managed denial;
  no browser test command or alternate browser route was executed in this task.
- actionlint validates workflow syntax/static context only. Git metadata is read-only and remote
  creation/push lacks owner approval; no commit, remote CI or publication result exists.
- The direct initial uv lock/sync attempt (before captured rerun) returned exit 2 for an unwritable
  default /Users/andy/.cache/uv. Recorded successful reruns use workspace-local UV_CACHE_DIR.
- Dependency/secret scans only cover their stated package/source scope and advisory data.
  No external broker/model/feed/notification/market data service is claimed tested.

Old audit transcripts were renamed from .log to .txt for deliberate documentation packaging.
Contents/hashes were preserved; historical audit reports remain evidence of that earlier source state.
Current source changes are described by the Phase 0 report, not retroactively certified by old hashes.
