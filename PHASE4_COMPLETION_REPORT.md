# Phase 4 Completion Report

Date: 2026-10-27. Scope: deterministic **SIMULATED risk management**, following the owner's
OWNER_REPORTED_PASS for prior local Phase 3 acceptance. **Phase 4 is NOT fully accepted:** current
managed Chromium launch remains blocked. No Phase 5 started. All external DEMO/LIVE orders,
generated-code execution and live promotion remain disabled. No broker credentials were introduced.

## Delivered implementation

- Mandatory journal gateway: bounded typed proposals, exact account/strategy scope, latest verified
  policy/profile/context versions, account-global clock, session/quote/spec/FX/calendar freshness,
  protection, spread/slippage, margin and portfolio limits. Durable ALLOW/DENY/INDETERMINATE evidence.
- Exact Decimal sizing: linear-contract and linear-tick Forex/metals/index/crypto contracts, explicit
  separate gold/silver specifications, conservative cross-currency rates, legal step-down/minimum,
  commission/slippage/funding buffers and fixed per-unit margin. Inverse/unverified products refuse.
- Account-scoped equity/drawdown/cost ledger, static/trailing balance/equity references, explicit daily
  timezone/DST boundaries, pre-execution midnight anchor and hash-verified history. Known losses stay
  visible during hard stops; missing/untrusted financial evidence displays unknown.
- Immutable policy/profile/context versions with owner recent MFA/provenance/attestation, exact prop
  account/program revision and latest-version refusal. No official brand-wide numeric rules invented.
- Account-locked atomic reservations, domain-separated consumed HMAC scopes, fresh exact-fill risk
  checks, conservative UNKNOWN/partial/netting allocation and durable idempotency/recovery.
- Separate fixed-code monitor container and API poll, persistent STOP, distinct owner-MFA simulated
  FLATTEN/CLEAR, incidents and audit. What-if stores decisions but cannot grant execution or change STOP.
- Romanian real-API Risk Center, global risk/emergency banner, mandatory simulator SL/TP and explicit
  assumption forms, generated OpenAPI/TypeScript, desktop/mobile workflow source.
- Additive Alembic 0005 with ten risk tables, immutable SQL triggers and runtime grants; fresh private
  pre-migration backup, existing owner/MFA/source/volume preservation. No migrations rewritten.

Key source areas: packages/risk/, apps/api/risk/, packages/execution/{engine,journal}.py,
apps/api/execution/, scripts/risk_monitor.py, compose.yaml, Dockerfile, migration0005,
apps/web/src/{RiskCenter,RiskBanner,BrokerCenter}.tsx and e2e/risk-workflow.ts/phase4.spec.ts.
The machine [source-change manifest](docs/phase4-evidence/2026-10-27/source-changes.json) records
added/modified paths and hashes against the private Phase 4 starting snapshot; Git is uncommitted.

## Exact final verification

Exact argv, child exit status, UTC start, duration and sanitized-log SHA-256 for every recorded attempt
are in [the execution ledger](docs/phase4-evidence/2026-10-27/README.md). The recorder's own exit0 is
not a child-test pass; JSON exit_code is authoritative. Test totals below are cases, not generated
Hypothesis examples, and repeated write/restart stages are not counted as unique tests.

- **PASSED:** `make check`, exit0: Ruff lint/format, mypy (112 files), frontend ESLint/Prettier/TypeScript,
  **179 Python + 16 frontend tests**, production frontend build. 61 service/infrastructure cases are
  deselected here, not skipped or counted as passing. See check-final.json/txt.
- **PASSED:** `make integration`, exit0: **1 actual running-API readiness case**, **60 actual disposable
  PostgreSQL/Redis/MinIO cases in write stage + 60 in restart/verify**, then
  `.venv/bin/python -m scripts.smoke_demo --require-ready` with readiness HTTP200. Dynamic 127.0.0.1
  bindings and TCP are checked before/after restart; only the owned UUID project is cleaned.
- **PASSED:** `make integration-services`, exit0, 60/60 in both stages independently. Browser harness
  attempts separately also completed their native 60/60 stages before browser launch.
- **PASSED:** `make smoke-demo`, exit0, API/external-order denial and readiness200.
- **PASSED:** `make contracts`; `make contracts-check`, exit0, generated API byte-for-byte consistency.
- **PASSED:** `npm --prefix apps/web audit --audit-level=high`, exit0, zero vulnerabilities;
  `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`,
  exit0, no known vulnerabilities. These do not scan actual Windows optional dependencies or built images.
- **PASSED:** local `docker compose config --quiet` and `.tools/bin/actionlint`, exit0.
  Remote GitHub Actions NOT RUN; no remote/commit/push created.
- **PASSED:** `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker risk-monitor`,
  followed by packaging-fix rebuild and `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker risk-monitor`,
  exit0. All seven long-running services healthy. Migration completed; no data service recreated.
- **PASSED:** runtime probe: development schema0005, no ORM/Alembic drift, runtime immutable grants,
  valid HMAC audit, no broker/admin/root-storage secrets or sockets in API/workers, monitor private
  control-only network/no public port/no bootstrap or storage keys, main images exclude MT5 SDK/bridge.
  API readiness200/three HEALTHY dependencies, web200, overview4 and safety flagsfalse.
- **PASSED (startup only):** `docker compose exec -T risk-monitor /app/.venv/bin/python -m scripts.risk_monitor --once`,
  exit0, zero configured development risk accounts. Native fixtures test configured-account behavior;
  this startup command alone is not exposure-monitor acceptance.
- Final fresh secret/repository results are recorded in the final-scan section below and linked ledger.

One pre-existing FastAPI/Starlette TestClient/httpx deprecation warning remains. It is visible in logs,
not suppressed; replacing the pinned test transport requires a separate compatibility change.

## Browser gate — FAILED command / BLOCKED environment

Collection: `npm --prefix apps/web run test:e2e -- --list`, exit0, **14 cases in five files** across
desktop/mobile. Collection is not an execution pass.

Focused attempt:
`E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=risk make browser-integration`, with
`PLAYWRIGHT_BROWSERS_PATH` set to the workspace cache by the recorder, **exit2**. Native write/restart
stages each pass60. phase4.spec.ts:32 fails **before page creation** with Chromium:
`bootstrap_check_in ... MachPortRendezvousServer ... Permission denied (1100)`.

Full attempt: `make browser-integration`, same browser path, **exit2**. Native stages each pass60;
desktop foundation yields **3 launch failures / 1 HTTP-only external-denial pass**. The harness stops
on the failed group; the later **10 cases are NOT RUN**, including mobile and risk. No test was
marked skipped, no assertion weakened, and no browser flag/route/permission bypass attempted.
This is not evidence that the Risk Center rendered workflow passes or fails an application assertion.
Owner-reported prior Phase 3 local passes remain distinct from these current agent-executed failures.

Owner/environment-administrator action: run the focused and full commands above in a legitimately
permitted local environment. Use NEXT_STEPS.md. No broker keys are needed; all resources are disposable.

## Defects found and fixed

1. Existing fixture runs used a different initial balance from their owned account. Run admission now
   requires exact equality; fixtures explicitly use account capital. This prevents duplicated/mismatched
   account equity across runs, without changing the existing assertions.
2. Actual fill risk counted the entry slippage buffer twice. Actual-price checks now retain only exit
   slippage, still capped by the proportional original signed allocation. Bounded/larger gap tests cover it.
3. Derived P&L could exceed the strict 12-place accounting input precision. Deterministic conservative
   ledger quantization fixes serialization without floats or relaxed financial bounds.
4. Daily reset after a midnight stop gap could hide that loss. Capture balance/equity **before** the
   execution; missing reset observations remain sticky/unverified rather than manufactured after flatten.
5. Pending funding was absent before assessment and could be double charged. Centralized pure clock
   advancement charges once, projects other runs' known liabilities and preserves duplicate receipts.
6. Hard breaches incorrectly hid known negative headroom. Data verification is now separate from policy
   compliance; verified losses stay visible while entry remains stopped.
7. Account time could reverse through a non-entry command; new commands/runs are now account-global
   monotonic, while exact duplicate receipts remain recoverable. FLATTEN uses the current account clock.
8. Existing holiday comparison used a string against date objects. Correct typed date comparison now
   refuses holidays as intended. Held duration, unresolved protection and cross-run session restrictions
   are checked before admissions; known funding costs cannot be understated by a smaller owner buffer.
9. Monitor container initially omitted scripts.risk_monitor from the Dockerfile allowlist. Packaging was
   fixed, rebuilt and verified by actual container health and --once. No credential boundary was widened.

Earlier failures remain in the ledger: native-first28pass/7fail; subsequent34pass/1fail fill/precision
rounds; extended56pass/2fail missing test import; boundary58pass/2fail known-headroom display. They are
resolved by current60/60 stages. First make check stopped on three lint findings, then passed after
fixes. Buildx initially could not write ~/.docker activity; workspace client cache solved that without
changing engine/browser permissions. A test-list invocation used a nonexistent npm script and failed;
the correct test:e2e collection passes. A private comparison probe initially omitted pg_restore's
output flag and another omitted PYTHONPATH; corrected probes pass. None are recorded as test successes.

## Preservation and security evidence

A fresh private mode0600 pg_dump and all30 legacy table fingerprints/container mounts were captured
immediately before additive development migration. All three data container identities/mounts match.
29 legacy table hashes match exactly. login_sessions changed through monotonic idle_expires_at renewal;
field-by-field comparison with the private dump verifies identical sessions/token/MFA/expiry/revocation
fields. The initial all-hashes assertion failed honestly; the exact difference is preserved in evidence.
No database reset, development volume removal, owner/MFA deletion or source-dataset mutation occurred.

Gateway grants always contain external_execution_authorized=false. Legacy/new API external execution,
adapter mutation methods and live activation remain denied. SIMULATED and DENY_ALL are enforced config,
not opt-in authorization toggles. Research/generated code has no runner, Docker socket, broker keys or
right to edit risk/governance. No external order or account connection was attempted.

The current signing key and API/gateway share trusted host authority; SQL immutability cannot defend
against malicious host/DB admins with secrets. A genuinely independent broker executor, separate keys,
capability checks, external audit anchoring, rotation/revocation and owner-MFA/two-acknowledgement live
approval remain NOT IMPLEMENTED. No production or external integration certification is claimed.

## Mathematical and operational limits

Read [RISK_CALCULATIONS.md](docs/RISK_CALCULATIONS.md),
[RISK_AUTHORIZATION_PROTOCOL.md](docs/RISK_AUTHORIZATION_PROTOCOL.md),
[PROP_FIRM_POLICY_SCHEMA.md](docs/PROP_FIRM_POLICY_SCHEMA.md),
[RISK_RESERVATION_RUNBOOK.md](docs/RISK_RESERVATION_RUNBOOK.md) and
[INCIDENT_KILL_SWITCH_RUNBOOK.md](docs/INCIDENT_KILL_SWITCH_RUNBOOK.md).

- Explicit linear contract/tick payoff and fixed per-unit margin only. Inverse/unknown modes deny.
  Synthetic calendars/FX/metadata and human attestations are not actual broker or official firm proof.
- Continuous synthetic funding is not a real broker rollover convention. Losses can gap beyond stops.
  Netting allocation intentionally stays conservative until flat. No manufactured performance results.
- Account clocks are global; independent historical runs should use separate accounts. Missing held
  midnight references fail closed, including imported legacy history without an established anchor.
- Ledger/journal capacity is bounded at20000; independent monitor polls at most1000 configured accounts.
  Production partitioning/retention/performance, real provider coverage and independent audit anchors
  remain operational work. No five-year coverage, backup restore or production-load claim.
- External MT5/cTrader reads/Windows deployment, actual economic-calendar service, real margin/protection,
  container/SBOM/Windows vulnerability checks, full off-host restore and remote CI remain unverified.

## Acceptance scenario traceability

Items1–34 below are verified within the explicit synthetic/contract scope, never external certification.
Item35 remains BLOCKED; therefore the definition of done is not satisfied.

1. Decimal exactness: test_risk_math exact cost oracle and finite/non-float refusals.
2. Step/minimum: exact oracle, minimum rejection and 100-example Hypothesis sizing budget property.
3. Cross-currency: conservative direct/inverse paths and actual synthetic USDJPY P&L native case.
4. JPY precision: reported .001 tick/100 tick value and loss conversion oracle.
5. Gold/silver: parametrized distinct metal contract sizes, plus linear index/crypto cases.
6. Inverse: unsupported/unverified payoff refusal parameters.
7. Costs: round-trip commission/slippage oracle, actual-fill buffer and funding-once native tests.
8. Specification uncertainty: stale/unverified/contradictory payoff/specification refusal tests.
9. Currency mismatch: payoff quote/profit checks, actual cross-currency fixture and prior account boundary tests.
10. Static/trailing: balance/equity/high-water oracles, no reset-on-loss.
11. Floating: explicit include/exclude P&L reference tests; internal safety caps remain stricter.
12. Midnight/DST: nonexistent/fold/23/25-hour/reset tests and actual midnight gap native case.
13–14. Daily/total breach: adverse-gap native case with durable STOP and visible negative headroom.
15. Correlation: actual competing account allocations hit the shared group cap.
16. Pending: durable reservation and open/pending/max allocation assertions.
17. Concurrency: three actual processes, two ALLOW/one DENY; no over-reservation.
18. Duplicate: one allocation/use for repeated submission; current state with original receipt.
19. Rollback: actual SIGKILL before/after commit proves no unreserved committed approved order.
20. UNKNOWN: retained allocation, explicit reconciliation and owner review before clearing stop.
21. Partial: actual fill/cancel/partial-close allocation release assertions.
22. Policy changes: expiry between reserve/fill, revised profile and latest-unverified policy refusal.
23. Programs: three explicitly synthetic FTMO/FundedNext/The5ers exact-program fixtures and stricter ceilings.
24. Calendar: required-feed outage/blackout native tests; no real provider integration claimed.
25. Staleness: quote/FX/spec/calendar checks and stale independent-monitor refusal.
26. Kill: owner STOP vs FLATTEN, automatic adverse-gap STOP, hypothetical refusal cannot mutate STOP.
27. Interruption: real process kills, database stop/start and persistent STOP/journal/reservations.
28. Ownership: foreign viewer/account access and direct service-identity refusal.
29. MFA: actual authenticated/recent-MFA native configuration/emergency tests.
30. Tamper/replay: scope signature/consumption, SQL immutable grants, admin ledger corruption detection.
31. Full order: exact approval, atomic allocation/consumption, real synthetic fill/journal/audit.
32. Bypass: direct durable journal without service identity refuses; no executable generated code.
33. External denial: previous API/adapter/bridge denial tests plus actual running API smoke; no broker orders.
34. Regression: all179 portable,16 frontend and60 native cases per service stage, including Phases0–3.
35. Desktop/mobile:14 collect, execution BLOCKED as documented above.

## Owner action and next module

Close browser acceptance in an authorized local environment and retain actual logs. Review exact
synthetic assumptions before configuring retained accounts. No credentials or infrastructure purchases
are required for this phase. Production/external dependencies require separate scope; private GitHub
creation/push still requires owner approval and writable Git access. See NEXT_STEPS.md.

After Phase4 acceptance and a new request, the recommended module is Phase5 reproducible backtesting
with immutable data, realistic costs, chronological holdouts and uncertainty. It has not been started.

## Final repository scans

**PASSED:** `make repository-check`, exit0: sensitive path exclusions and prospective regular-file
checks pass; no staging/commit/remote/push. **PASSED:** fresh `make secret-scan`, exit0: Gitleaks finds
no leaks in Git-selected source/evidence. The first scan failed on seven synthetic `owner-clear-`
idempotency suffixes in an earlier pytest failure traceback. Those business identifiers were narrowly
redacted; original log hash/private copy retained. No scanner exclusions or detection rules changed.
Final source/evidence records and checksums are linked in the execution ledger.
