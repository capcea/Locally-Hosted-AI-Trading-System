# Phase 3 implementation and acceptance report

Date: 2026-10-27 (Europe/Bucharest). API0.1.0, schema0004_execution_journal.
**Status: implementation delivered; full Phase 3 acceptance BLOCKED. Phase 4 NOT STARTED.**
SIMULATED/DENY_ALL remains enforced. No external broker credentials, real/demo orders, generated
strategy execution, account connection, remote repository, push or public deployment was performed.

## Implemented and fixed

- Exact broker-neutral contracts and nullable venue metadata: `packages/brokers/contracts.py` and
  `packages/execution/contracts.py`; no broker SDK in the domain layer. Future risk contracts cannot
  approve execution. SIMULATED/DEMO_READ_ONLY are distinct; LIVE/DEMO_EXECUTION are unavailable.
- Pure seeded deterministic simulator: market/limit/stop, cancellation/expiry, protection/gaps,
  partial fills/rejects, netting/hedging, modify/partial close and explicit synthetic OCO. It consumes
  finite bid/ask liquidity and refuses stale/unknown inputs. Fees, slip, latency and optional funding
  are explicit assumptions, never real performance evidence. Invalid gap protection and reused
  quote-liquidity paths were corrected; Decimal overflow is a safe refusal.
- Transactional PostgreSQL journal: run row locks, unique command keys/payload digests, compact first
  receipts, immutable chained events and snapshot digest, atomic HMAC audit, UNKNOWN and explicit
  reconciliation. A response includes current state plus original_receipt; a duplicate never fills
  again. Fixed the crash-test fixture import and ensured crash probes commit audit with state.
- Additive Alembic0004 extends existing account/broker/identity data with five tables; runtime grants
  and triggers deny event/receipt/observation rewrites. Existing Phases0/1/2 remain in place.
- Existing MFA/role/ownership/CSRF APIs now expose signed pinned observations, simulated commands,
  journal and actual VALID Phase 2 MinIO tick replay with provenance/cutoff/idempotency checks.
- Separate MT5 Windows official-SDK read-only adapter and cTrader official demo JSON/OAuth adapter.
  Both deny external mutations. MT5 verifies demo/investor/terminal/pinned identity. cTrader requires
  verified VIEW scope and explicit demo account, exact integer-unit conversion, message correlation,
  bounded reconnect/heartbeat/rates and strict read-message allowlist. OAuth tokens stay encrypted
  on the connector host. Their actual broker connectivity remains BLOCKED.
- Private bridge: loopback mTLS plus bearer identity, Ed25519 packets, bounded spawned read process,
  request/concurrency limits, optional Windows SCM/Job/ACL source. Local real TLS tests pass.
  Corrected Windows ACL path/service interpreter and connector image dependency on API modules;
  shared validation/canonical serialization now live in `packages/domain`. The connector image
  builds and starts its CLI with networking disabled. This is not broker or Windows deployment proof.
- Romanian `BrokerCenter.tsx` uses real APIs for connections/accounts, nullable observed metadata,
  synthetic scenarios/orders/positions/fills, faults/reconciliation, journal and operational status.
  Controls preserve account/MFA/roles. Clock/sequence form updates follow current virtual state.
  Rendering/browser acceptance remains BLOCKED. No browser assertion was relaxed or skipped.
- Generated OpenAPI/TypeScript and pinned lock updated. CI includes the new native tests, default
  twelve browser cases and independent connector packaging check. Remote CI was NOT RUN.

## Actual verification

Exact argv, UTC start, duration, child exit code and sanitized log SHA-256 are retained in the
[command ledger](docs/phase3-evidence/2026-10-27/README.md). These are local measurements.

- **PASSED**, `make check`, exit0: 148 Python portable/unit tests, 16 frontend tests; Python/frontend
  lint/format/types and frontend production build. 36 service/infrastructure cases deselected here.
- **PASSED**, `P0_CACHED_IMAGES=1 make integration`, exit0: one running-API readiness case; 35 native
  disposable PostgreSQL/Redis/MinIO cases in write stage and 35 after real stop/start; strict smoke200.
  Cases include Alembic up/down/up on disposable databases, migration/security/immutability, Redis
  queue/storage round-trips, process SIGKILL before/after commit, real DB restart, concurrent duplicate
  processors and actual stored VALID dataset replay. Repeated stages are not 70 distinct scenarios.
- **PASSED**, `make smoke-demo`, exit0: API, execution denials and readiness200.
- **PASSED**, `make contracts-check`, exit0: generated artifacts match source byte-for-byte.
- **PASSED**, adapter/local transport subset: 25 fixture/protocol/OAuth/private-storage tests plus
  one actual bridge mTLS test, included in the 148 Python tests. OAuth HTTP uses MockTransport and
  MT5 uses injected SDK fixtures; neither is an external connection. TLS test proves actual local
  application rejects missing client cert/bearer and exposes no order route.
- **PASSED**, rebuilt local API/migrate/Web/market-worker and separate connector image; local stack
  --wait succeeds. Connector --help succeeds with --network none/read-only/nonroot/resource limits.
- **PASSED**, dependency audits: npm reports0 vulnerabilities; pip-audit reports no known
  vulnerabilities in the resolved installed Python environment. Windows optional SDK dependencies
  and built-container vulnerability/SBOM acceptance are NOT RUN. Initial pip-audit cache write was
  denied; rerun with a writable project-local --cache-dir passes.
- **PASSED**, local Compose/Actions syntax and final repository/secret scans (see ledger). No remote
  CI or history-commit scan is inferred; repository contents are still untracked in read-only .git.
- **PASSED**, collection of12 desktop/mobile Playwright cases with explicit web Playwright config.
  An initial collection command omitted --config and incorrectly collected Vitest files; corrected
  invocation collects all12, without editing or skipping the tests.
- **FAILED/BLOCKED**, focused broker desktop browser command, exit2: native35+35 pass, then Chromium
  launch is denied by macOS `bootstrap_check_in ... MachPortRendezvousServer ... Permission denied
  (1100)`. This is actual launch output, not an assumed previous Chromium failure.
- **FAILED/BLOCKED**, full default desktop/mobile browser command, exit2: native35+35 pass; first
  desktop foundation group has3 launch failures/1 HTTP-only denial pass. Remaining8 market/broker/
  mobile cases are NOT RUN after fail-fast. Collection does not constitute execution acceptance.
  Owner-reported prior local passes are OWNER_REPORTED_PASS, not independent current-agent evidence.

Development failures remain in the ledger. One earlier native attempt lacked the explicit market
fixture import. Another encountered incompatible old in-memory/new crash-child receipt shapes while
source was being edited. Stable-source native reruns pass. Initial connector CLI failed because a
shared contract imported `apps`; that dependency was removed and independent image/CLI reruns pass.
The fresh secret scan initially flagged a synthetic idempotency identifier twice; its construction
and one saved traceback were adjusted, with the old log hash retained. No failing integration case
was skipped and no assertions or scanner rules were weakened.

## Data preservation and security evidence

A private pre-migration pg_dump was saved (88,133 bytes; SHA-256
4002f5a9ffaca436168ddd05bed7f14bfe6640fe64ce46a6a9f686448cfcd3c0); it is ignored, not committed.
Its restore was NOT TESTED. Original PostgreSQL/Redis/MinIO container IDs and volume mounts match.
17 of25 legacy table fingerprints match that early backup;8 authentication/bootstrap tables changed
through owner bootstrap/MFA at23:12–23:15UTC, before Phase3 migration at01:28UTC. No baseline table
row count decreased. All25 post-migration legacy fingerprints remain unchanged through final
rebuild/verification, including the owner's enrollment records. The3-event HMAC audit chain verifies.
No claim is made that all tables were unchanged since the early backup.

Actual main runtime checks verify revision0004, no ORM drift (foundation platform_metadata excluded),
immutable-table privileges, readiness200/all3 dependencies healthy, Web200/overviewphase3 and false
live/order/generated-code flags. API/worker images exclude bridge source and MT5 SDK, broker/admin/
root credential variables and Docker socket mounts. Disposable UUID test projects use private random
credentials, nonprivileged ephemeral127.0.0.1 ports checked against Docker inspection and actual TCP,
and scoped automatic cleanup. Development volumes were never deleted or reset.

## Remaining limitations and owner actions

1. **P1 BLOCKED:** run focused then all12 browser cases in an environment whose administrator permits
   Chromium. Current permissions were preserved. Commands are in [NEXT_STEPS.md](NEXT_STEPS.md).
   Any newly exposed UI assertion failure still requires investigation; UI behavior is not certified.
2. **P1 BLOCKED:** separately authorize actual demo read-only MT5/cTrader service access. Need Windows
   terminal/investor/demo identity, cTrader registered app/HTTPS callback/accounts scope, private PKI,
   service signing/bearer identities and executor-local token storage. Do not put secrets in chat,
   central .env or AI infrastructure. [Controlled runbook](docs/BROKER_RUNBOOK.md) explains setup.
3. **PARTIAL:** central broker sync is an owner-uploaded signed snapshot, not continuous polling.
   Windows SCM/ACL/Job deployment is source-only; actual service permissions/revocation/reconnect
   remain unverified. History is bounded/incomplete; metadata unknowns never imply tradability.
4. **MODELED:** simulator has no calibrated venue queue/impact/fill probability, FX conversion, inverse
   payoff, real margin/liquidation or broker rollover engine. Funding is synthetic continuous daily
   proration. No automatic trailing/break-even or full research backtest/statistics/paper engine.
5. **P2:** production TLS/secrets/rotation, independent audit anchoring, restore/load/fresh-machine,
   Windows/container dependency acceptance and remote CI remain open. No commit/remote/push performed.

Definition of done is **not fully satisfied**: native implementation and regression evidence pass,
but required desktop/mobile workflow evidence is blocked and actual external reads are unverified.
Recommended next implementation module is Phase4 independent deterministic risk/policy gateway,
after Phase3 gates close and a separate user request. Phase4 was not started; external orders remain denied.

Technical references: [architecture](docs/ARCHITECTURE.md), [adapter contract](docs/BROKER_ADAPTERS.md),
[capability matrix](docs/BROKER_CAPABILITIES.json), [simulator assumptions](docs/EXECUTION_SIMULATOR.md),
[state machine](docs/ORDER_STATE_MACHINE.md), [threat model](docs/THREAT_MODEL.md),
[official interface sources](docs/external-sources.md) and [60-criterion inventory](IMPLEMENTATION_STATUS.md).
