# Phase 0 Completion Report

Updated **2026-10-26 (Europe/Bucharest)** after the disposable integration repair.

**The remaining service integration failure is fixed and the complete `make integration` target
passes against actual PostgreSQL, Redis and MinIO. Phase 0 overall remains incomplete:** permitted
browser acceptance, authorized initial commit/remote CI, container scanning and fresh-machine
reproducibility remain open. Phase 1 was not started. Live trading and broker execution remain disabled.

Current evidence: [command ledger](docs/phase0-evidence/2026-10-26-integration/README.md).
Earlier results are historical: [previous Phase 0 report](docs/phase0-evidence/2026-10-26-integration/phase0-report-before-integration.md)
and [2026-10-25 evidence](docs/phase0-evidence/2026-10-25/README.md). The earlier missing-Docker and
HTTP 503 outcomes are superseded by this verified run, not erased or relabeled as successes.

## Root cause and changes

The disposable Compose network was `internal: true`. Reproduction on Docker Engine **29.7.2** /
Compose **5.5.0** showed a healthy PostgreSQL container, a bridge with `internal: true`,
`docker compose ... port postgres 5432` returning `invalid IP:0`, and the actual Docker binding
`{"5432/tcp":[]}`. An internal container health check did not establish host reachability.
The strict loopback assertion correctly rejected this state.

- **compose.test.yaml:** uses a project-scoped bridge with `internal: false`. Each service explicitly
  sets `host_ip: 127.0.0.1` and TCP; the published host port is omitted so Docker assigns it.
  The network also defaults host bindings to loopback. No shared/external network or fixed host port
  was introduced. Docker documents [bridge port publishing](https://docs.docker.com/engine/network/drivers/bridge/)
  and [Compose network isolation](https://docs.docker.com/reference/compose-file/networks/).
- **scripts/integration_services.py:** cross-checks Compose port discovery against
  `docker inspect .NetworkSettings.Ports`, rejects missing/multiple/wildcard/privileged/additional
  published bindings, and opens an actual TCP connection before running service tests.
- **Restart handling:** discovers and validates the ports again after stop/start and refreshes the
  private test configuration. The real run changed all three ephemeral host ports; retaining the
  original ports would have caused the verification stage to connect to stale endpoints.
- **Buildx state:** defaults its client metadata directory to ignored `.cache/buildx`, respecting an
  explicitly supplied BUILDX_CONFIG. The first build attempt was blocked when Buildx tried to write
  activity metadata under unwritable ~/.docker. No filesystem permissions were relaxed.
- **Regression coverage:** 28 focused guards cover invalid/missing/public/multiple bindings,
  connection failures, cleanup after failures, restart binding mismatch and changed restart ports.
  Six lifecycle cases explicitly mock commands/sockets; they are not real service evidence.

UUID project names, random disposable database/storage credentials, a private 0600 configuration,
local-engine checks, an empty Compose env file and finally-based scoped cleanup remain in place.
The regular test bridge permits ordinary networking for trusted infrastructure services; it is
**not an experimental-code sandbox**. No generated-code runner was introduced or enabled.

## Actual commands and results

All exit codes below belong to the child command, not the evidence wrapper. Exact arguments,
UTC timestamps, durations, sanitized output and SHA-256 hashes are retained in the command ledger.

- **PASSED — `make integration`, exit 0.** Its complete sequence executed:
  `.venv/bin/python -m pytest -m infrastructure` (**1 passed, 78 deselected**);
  `.venv/bin/python -m scripts.integration_services` (**3 passed** in the write stage and
  **3 passed** after restart);
  `.venv/bin/python -m scripts.smoke_demo --require-ready` (**HTTP 200**, safety/denial checks pass).
  These are four distinct integration cases with seven actual test executions. No failing case
  was skipped or converted to a mock.
- **PASSED — `make check`, exit 0.** **75 Python tests passed, 4 integration cases deselected** for
  this unit target and executed separately above; **13 frontend logic tests passed**. Ruff lint and
  formatting, ESLint/Prettier, mypy, TypeScript and frontend build pass.
- **PASSED — `.venv/bin/python -m pytest tests/test_integration_guards.py -q`, exit 0:** 28 passed.
- **PASSED — `make smoke-demo`, exit 0:** application contract, simulation safety, both execution
  refusal endpoints and infrastructure readiness HTTP 200.
- **PASSED — `make contracts-check`, exit 0:** generated OpenAPI/TypeScript match byte-for-byte.
- **PASSED — `make doctor`, exit 0:** installed prerequisites and Docker engine available.
- **PASSED — `make repository-check`, exit 0:** 19 sensitive-path exclusions validated.
- **PASSED — `make secret-scan`, exit 0:** no leaks found across 239 Git-selected source/evidence
  files. Ignored runtime state is excluded; this is not a scan of all host secrets or Git history.
- **PASSED — read-only before/after and cleanup checks, exit 0:** development configuration hash,
  container IDs/start times/health and mounted persistent volume identities match. All three
  disposable projects created/attempted by this repair have no remaining containers, networks or
  volumes. Main API readiness is HTTP 200 before and after.

The real service checks prove:

- PostgreSQL: Alembic upgrade/downgrade/upgrade, rejection of LIVE metadata, committed data,
  transaction rollback and persisted data after graceful restart.
- Redis: AOF enabled; Streams consumer-group delivery/pending state, pending redelivery after
  restart, acknowledgement and removal of the test stream.
- MinIO: authenticated private bucket/object creation, anonymous-read denial, GET payload SHA-256
  equality before/after restart and deletion of that test object/bucket.

In the passing project `phase0-test-d79e785cdd5c41b2b10893d538066c92`, the verified host bindings were:

- PostgreSQL: **127.0.0.1:57474**, then **127.0.0.1:57494** after restart, targeting 5432/tcp.
- Redis: **127.0.0.1:57475**, then **127.0.0.1:57496**, targeting 6379/tcp.
- MinIO: **127.0.0.1:57473**, then **127.0.0.1:57495**, targeting 9000/tcp.

All six actual binding/TCP checks passed. These ports were temporary and have been cleaned up.
This proves graceful-restart persistence, not power-loss recovery, a production job system,
backup/restore or any broker/model/feed integration.

## Failed attempts retained

- **FAILED — initial `make integration-services`, exit 2:** Buildx activity metadata write was denied
  outside the workspace. Fixed using the writable workspace client-state directory.
- **FAILED — instrumented reproduction `make integration-services`, exit 2:** reproduced
  `internal: true`, `invalid IP:0` and an empty actual published binding. Scoped cleanup succeeded.
- **FAILED — initial `make check`, exit 2:** Ruff S104 flagged three intentionally unsafe address
  literals used solely as rejection fixtures. Each now has a narrow, explained fixture annotation;
  production checks and all test assertions remain intact. The subsequent full check passes.
- **FAILED — initial read-only snapshot helper, exit 1:** the completed migration container has no
  Health field. Corrected the diagnostic template to handle that absent field; before/after
  snapshots and comparison then passed. This was not a product or service test failure.

One upstream Starlette TestClient deprecation warning remains visible. No coverage or external
integration certification is inferred from the passing checks.

## Safety and remaining acceptance gates

**PASSED:** simulation-only configuration and unconditional execution denial remain tested.
No broker credentials, live activation, real broker orders or experimental code execution were
introduced. Only disposable services were started/stopped/migrated/removed. compose.yaml and the
owner's existing containers were not edited or restarted by this repair. Development persistent
volumes were not migrated, removed or targeted by test writes; no daemon-wide prune was run.

**BLOCKED:** six Playwright desktop/mobile cases remain unexecuted under the previously recorded
managed browser restriction. This repair did not attempt another browser route. Browser access
must be restored by the owner/administrator before running:

```sh
E2E_EXTERNAL_SERVERS=1 npm --prefix apps/web run test:e2e
```

**BLOCKED:** staging/commit remains unavailable because managed .git access is read-only. No
alternate Git directory was used. Private repository creation/push still require owner approval;
no remote CI run is claimed. See [GitHub preparation](docs/GITHUB_PREPARATION.md).

**MOCKED:** command/safety unit fixtures and static reference account/risk presentation remain
explicitly labeled. Actual service success above is based on real containers, not those fixtures.

**NOT IMPLEMENTED / NOT VERIFIED:** broker adapters, risk gateway, genuine isolated AI sandbox,
identity/RBAC/MFA, approvals and paper trading remain future modules; container scanning,
fresh-machine reproducibility and remote CI have not been established by this repair. Previous
2026-10-25 dependency/workflow scan results retain their original scope and date.

No broker or paid-provider credentials are needed to finish Phase 0. Recommended next implementation
module, **only after the remaining Phase 0 gates pass and further work is requested**, is Phase 1
owner identity, RBAC/MFA, domain persistence and protected append-only audit.

## Phase 1 follow-up — 2026-10-26

The owner reported previous Phase 0 browser success and authorized Phase 1 implementation/testing.
The native Phase 0 service/safety checks continue passing with the added Phase 1 schema and identity.
During this run Chromium still failed at the managed OS launch boundary (Permission denied 1100):
three desktop page cases failed, one HTTP-only denial case passed and mobile did not run. Historical
results above are preserved; current evidence and the unclosed browser gate are in
[PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md). No live execution or Phase 2 was started.
