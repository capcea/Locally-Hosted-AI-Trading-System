# Risk monitor database interruption recovery

2026-10-28. Runtime recovery IMPLEMENTED and deployed locally. Independent risk calculations,
authorization, manual/automatic stops and SIMULATED/DENY_ALL are unchanged. No new development phase.

## Verified cause

This is a different failure from the missing campaign entrypoint. Actual risk-monitor logs show an
uncaught SQLAlchemy/psycopg OperationalError: PostgreSQL connection refused during `once()`.
Container lifecycle inspection shows the PostgreSQL replacement was created at21:10:54 UTC and
started at21:10:55; the running risk monitor exited at21:10:55. It had started at21:08:41. The
connection target matches the current PostgreSQL control-network address. This is a dependency
interruption during recreation, not a missing module, bad model selection or cloud policy refusal.

The prior daemon validated its restricted identity once, then let any database interruption escape
its polling loop. Its restart policy was `no`. Initial service dependency ordering did not recover
this already-running process when PostgreSQL was recreated later.

## Small scoped correction

`scripts/risk_monitor.py` now:

- Rechecks the original restricted-role/no-risk-ledger-UPDATE requirements before every scan.
- Withdraws its readiness marker at startup, during failed scans and at daemon shutdown. Only a
  successful scan publishes readiness. Docker still applies its configured healthcheck cadence.
- Retries only connection/resource/temporary-shutdown categories, with at most6 consecutive failures
  and backoffs1/2/4/8/8 seconds. Successful scans reset the consecutive-failure counter. Each retry
  disposes the connection pool so the next connection resolves the service afresh.
- Refuses known authentication, permission and statement failures without retry. Unknown driver
  connection errors can retry only within the same finite limit; they never grant authority.
  Exhaustion exits with a sanitized diagnostic and no readiness marker; it does not retry forever.
- Uses signal-interruptible waits. The `--once` diagnostic fails immediately rather than retrying,
  and does not publish/delete another daemon's readiness file.

The original `once()` scan, account locks, audited policy checks, risk calculations and freshness
thresholds are untouched. No monitor timestamp is manufactured during failure. Existing Risk
Gateway database/freshness refusals remain authoritative; process health is not trading approval.
Reconnection does not clear manual stops, authorize orders or prove any broker/model connection.
No automatic Docker restart policy was added to hide persistent failures.

`tests/test_risk_monitor_recovery.py` adds7 deterministic recovery/health/permission/log-sanitization
unit cases. The risk integration suite adds a real PostgreSQL self-connection termination test:
successful scan → connection loss/readiness absent → successful fresh scan. It verifies that the
owner's STOP remains set, a simulated order stays refused and the HMAC audit chain remains valid.
Only the disposable client's own connection is terminated; development PostgreSQL is not restarted.
Event-controlled test waits avoid arbitrary sleeps or weakened timeouts.

`scripts/integration_services.py --risk-only` provides a focused actual-service path. The full suite
retains every existing test and includes the new case. No assertion or acceptance gate was removed.

## Actual local repair and preservation

The risk image was rebuilt and its packaged `--help` tested non-root, read-only, with no network,
all capabilities dropped and no-new-privileges. Only `risk-monitor` was recreated using `--no-deps`.
It is running/healthy with a fresh readiness marker. Read-only runtime inspection confirms UID10001,
schema0009, a working database read and **no UPDATE privilege on risk_ledger**.
Container IDs prove no other service was recreated by this repair. PostgreSQL/Redis/MinIO named
volume identities are unchanged. No credentials, migrations, datasets or development volumes changed.

## Verification

Exact command records and local logs: `.cache/risk-monitor-recovery/`. Sanitized summaries are
published under `docs/openrouter-evidence/2026-10-28/risk-monitor-recovery/` at finalization.

- `.venv/bin/pytest tests/test_risk_monitor_recovery.py -q`: exit0,7 cases.
- `make check`: exit0,290 Python +153 frontend cases; Ruff, mypy and production build pass.
- `.venv/bin/python -m scripts.integration_services --risk-only`: exit0,27 cases before and27
  after graceful disposable service restart. Actual migrations, TCP binding checks and cleanup pass.
- Risk image build, no-network packaged-entrypoint smoke and targeted service start: exit0.
- `make smoke-demo`: exit0, deployed API and execution-denial smoke, readiness200.
- `make contracts-check`: exit0.
- Full `make integration`: **exit0**,452.949s. Development infrastructure readiness passes;
  all108 isolated service cases pass before and all108 after graceful restart. Final deployed API/
  execution-denial smoke reports readiness200. Disposable cleanup completed successfully.
- `make secret-scan`, `make repository-check` and `git diff --check`: exit0. No leaks or altered
  sensitive-path exclusions.

No browser execution or public inference was attempted. Existing managed browser restrictions,
OpenRouter real-model acceptance and V1 visual acceptance remain separate open gates. No paid
provider call, demo/live order, generated-code execution or risk-limit change occurred.

## Operations

This local service is already repaired. To reproduce on another authorized local installation:

```sh
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up --build -d --no-deps --wait --wait-timeout 90 risk-monitor
```

In this managed session Buildx client state uses the permitted ignored workspace cache through
`BUILDX_CONFIG`; no filesystem permission or container protection was relaxed. If an outage exceeds
the retry budget, repair the dependency/identity first and explicitly restart this service. Do not
clear owner stops or weaken monitoring freshness, permissions or healthchecks to obtain a green state.
