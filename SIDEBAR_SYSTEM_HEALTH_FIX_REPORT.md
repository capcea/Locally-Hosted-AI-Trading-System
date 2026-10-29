# Sidebar system health repair

2026-10-29. IMPLEMENTED / NATIVE PASSED / BROWSER BLOCKED / RUNNING WEB UPDATE PENDING.

## Confirmed cause

Read-only GETs to `http://127.0.0.1:18000/api/v1/overview` and the actual Web proxy at
`http://127.0.0.1:5173/api/v1/overview` both returned200 with explicit HEALTHY observations for
`api`, `postgres`, `redis`, `storage`. The actual response passes `overviewSchema.safeParse`.
Stable IDs, field mapping, enums and API/proxy contracts are correct for this response.

The defect was in `App.tsx`: the poll stored `now = Date.now()` **before** awaiting the request,
then stored `lastSuccess = Date.now()` **after** it. `isStale` correctly rejects observations from
the future (`now < lastSuccess`), but that frozen pre-request clock made every nonzero-latency
success look future-dated. Each subsequent poll repeated the error. A controlled20ms reproduction
using the actual valid payload produced `sidebar_stale: true` again on the next poll (exit1).
This is an observation-clock/state-update bug, not evidence of failed infrastructure.

## Changes and behavior

- `overview-state.ts`, `useOverview.ts`, `App.tsx`: the shell's existing public polling now records
  completion and clock in one state update; an independent clock expires observations between
  requests.15-second polls,10-second request timeout and45-second freshness limit remain.
  Request identity fences old success/error responses, including transports ignoring abort.
  Timeout/unmount cannot publish late success; regressed server timestamps are refused.
- `api.ts`: finite-clock validation and freshness of **both** receipt time and backend timestamp.
  A cached/old200 response does not renew backend observation age. Parsing and `cache: no-store`
  remain; HTTP success alone grants no health status.
- `infrastructure-health.ts`, `v1/ShellTools.tsx`: exact stable-ID mapping, unique observations,
  per-service status text, explicit loading/unavailable/stale feedback and functional retry.
  Fresh explicit HEALTHY becomes “Disponibil”; UNAVAILABLE becomes “Indisponibil”/DOWN.
  Missing/ambiguous/untrusted observations stay UNKNOWN. Aggregate DEGRADED means mixed known
  HEALTHY/DOWN infrastructure; it is not a new backend service enum. Unsupported raw enum values
  such as DEGRADED/DOWN/UNKNOWN still fail strict contract parsing instead of implying health.
  Broker/AI/GPU/worker capability and trading authority are not inferred from infrastructure.
- `api.test.ts`, `overview.fixture.ts`, `overview-state.test.tsx`: original tests preserved plus26
  cases covering all aggregate states, missing/duplicate fields, invalid enums, request latency,
  stale/future/invalid clocks, API/network errors, out-of-order success/failure, timeout, unmount,
  retry and recovery. Tests render the actual sidebar as static markup; this is not browser QA.
- `e2e/platform.spec.ts`: stronger existing desktop/mobile cases compare each sidebar service with
  the actual API response and verify UNKNOWN on transport failure plus recovery through retry.
  Existing scenarios/assertions and accepted visual references are retained.

V1 sidebar classes, geometry, colors, primary navigation and design tokens are unchanged. Only
status content/icons and the error-state retry control changed. Authentication remains independent
of public overview loading. No backend/schema, secrets, MFA, risk, trading or financial logic changed.

## Phase metadata

`packages/domain/contracts.py::Overview.phase` is a static default6; `apps/api/catalog.py::ROADMAP`
statically marks the broader “Cercetare autonomă & ML” Phase7 PLANNED. `/overview` returns these
constants, not a deployment/source scan or acceptance ledger. `docs/ARCHITECTURE.md` explicitly
records the Phase6 compatibility metadata. Newer Phase7A source is not reflected in that coarse
roadmap description: its report says **IMPLEMENTED FOUNDATION; ACCEPTANCE PARTIAL**, with real
model/data, browser/manual and other acceptance gates still open. Broader Phase7/7B/ML is not fully
delivered or accepted. Thus this is incomplete milestone detail, separate from actual probe health;
no public phase number, roadmap status, frontend contract or acceptance claim was advanced here.

## Actual verification

Exact commands/exit codes/timings: `.cache/sidebar-health-fix/*.json`; corresponding `.txt` logs.

- Focused `npm --prefix apps/web run test -- src/api.test.ts src/overview-state.test.tsx
  src/v1/redesign.test.tsx`: exit0,67 tests.
- `make check`: exit0,294 Python +186 frontend tests; lint/format/mypy/TypeScript/build pass.
- `make contracts-check`: exit0; existing public/API schemas unchanged.
- `make smoke-demo`: exit0, readiness200 and execution-denial smoke. These are unchanged public
  denial probes, not broker orders or authorization attempts.
- Browser `npm --prefix apps/web run test:e2e -- --list`: exit0,28 cases in12 files, collection only.
- `make secret-scan`, `make repository-check`, `git diff --check`: exit0. All1369 pre-task
  source/evidence files remain; the source-preservation ledger accompanies this report.

Browser execution remains BLOCKED by the prior managed localhost restriction; no alternate browser,
CDP or origin workaround was used. No visual/mobile acceptance or successful browser execution is
claimed. Existing TestClient deprecation and Vite >500kB chunk warnings remain.

## Owner-local verification and deployment

No Docker reset, restart, rebuild, database change or persistent resource deletion was performed.
Port5173 is currently nginx serving a previously built static bundle, not the Vite development
server. The source fix and generated local `dist` do not replace that running container's bundle.
To apply only the Web change using the existing stack configuration:

```sh
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns build web
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns up -d --no-build --no-deps --wait web
```

Reload the same hostname. Verify the four statuses against the actual overview, retry after an
outage, desktop/mobile layout and expiry after old observations. Do not infer AI/broker readiness.
Real-service browser verification without rewriting snapshots:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=foundation make browser-integration
E2E_ONLY_SCENARIO=foundation make browser-integration
```

SIMULATED/DENY_ALL remains. No provider calls or credentials, phase advancement or Docker/data resets.
