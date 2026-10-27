# Phase 2 completion report

Date: 2026-10-26, Europe/Bucharest. Evidence timestamps are UTC.
Decision: **IMPLEMENTED / NATIVE TESTED; ACCEPTANCE BLOCKED — browser workflows have not passed.**

## Browser failure follow-up — 2026-10-26

The owner's saved `apps/web/test-results/phase2-market-data-imports-345a4-nly-available-stored-prices-desktop/error-context.md`
contains a concrete assertion failure at `e2e/phase2.spec.ts:99`, in the test declared at line 13.
`page.locator('.market-json').last()` resolved to the LOCAL provider capabilities JSON
(`formats`, `network`, `resumable`), while the assertion expected `schema_version`. Provider cards
render after the dataset explorer, so waiting longer cannot select the manifest. This owner failure
is **not** the earlier Chromium launch failure. The saved trace shows that import, VALID quality and
the stored-data chart assertions were reached before the wrong-element assertion.

Changes:

- `apps/web/src/MarketData.tsx`: wrap the actual provenance/comparison response in the accessible
  named region “Detalii de proveniență”. Provider capabilities remain separate and visible.
- `apps/web/e2e/phase2.spec.ts`: scope to that region inside the dataset explorer. Wait for the actual
  provenance GET, require HTTP 200 and schema version 1, then compare the complete displayed JSON to
  the response. For the earlier cutoff, wait for the actual sample GET, require HTTP 200/empty items,
  verify the rendered zero count and retain the no-chart assertion. No sleeps, fake routes, removed
  quality checks or skipped tests were added.
- `scripts/browser_acceptance.py`: explicit validated `E2E_ONLY_PROJECT`/`E2E_ONLY_SCENARIO` selection
  for a focused run through the existing disposable database/storage, worker and real owner/MFA flow.
  Defaults still select every desktop/mobile scenario; focused success cannot establish full acceptance.
- `tests/test_integration_guards.py`: invalid selections fail before configuration/resource access.
  README documents focused and complete commands. No API, storage, migration, risk or auth behavior changed.

The owner-local failure excerpt and hash are preserved separately from the managed reproduction in
[follow-up evidence](docs/phase2-evidence/2026-10-26-browser-fix/README.md). The full original artifact is
private in ignored cache, because Playwright artifacts can contain authentication material.

The focused command was attempted before and after the fix:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" P0_CACHED_IMAGES=1 \
  E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market make browser-integration
```

Both managed attempts ran 27 actual native cases before and after service restart, then failed the
single desktop browser case at Chromium launch: `bootstrap_check_in ... Permission denied (1100)`.
The Make command exited 2 (the browser subprocess exited 1); neither attempt executed the page or
reproduced the owner's assertion in this environment. The selector fix is implemented, with browser
verification **BLOCKED**, not passed. No browser permission, executable, launch flag or execution
route was changed to bypass that boundary.

`make check` passed with **100 Python tests**, 28 marked service cases deselected for separate actual
execution, **16 frontend tests**, all lint/format/types and production build. An initial harness loop
variable lint failure and a Prettier failure were corrected; their real failed outputs are retained.
`P0_CACHED_IMAGES=1 make integration` passed, **exit 0**: one actual application readiness test,
27 service/security/data cases before restart and the same 27 after restart, followed by strict
execution-denial/readiness smoke, HTTP 200. `make smoke-demo` and `make contracts-check` separately
passed, exit 0. These checks execute actual PostgreSQL, Redis and MinIO behavior, including dataset
immutability, quality, timestamps, corruption checks, provenance and killed-worker recovery; no
mocked substitute was introduced. The two restart stages are repetitions, not 54 unique test cases.

The complete unfiltered browser command (both selection variables explicitly unset) exited **2**:
27 native cases passed in each restart stage; three desktop foundation/identity page cases failed
at Chromium launch and the HTTP-only execution-denial case passed. The remaining six market/mobile
cases were **NOT RUN** after that group failed. Collection still finds all ten cases in three files;
collection and native success do not establish browser acceptance. Disposable resources were cleaned
up by their own UUID project; no development volume cleanup was requested.

Read-only preservation verification passed, **exit 0**: development PostgreSQL/Redis/MinIO container
IDs and mount definitions, and Phase 1 record counts/digests, match this follow-up's before-state.
All four test invocations left no containers, volumes or networks with their own project labels.
Readiness remains HTTP 200; SIMULATED/DENY_ALL and all live/order/generated-code flags remain false.

In the owner's permitted local browser environment, run the focused command above, followed by:

```sh
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO \
  PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" P0_CACHED_IMAGES=1 make browser-integration
make check
P0_CACHED_IMAGES=1 make integration
```

Use `P0_CACHED_IMAGES=1` only when the exact pinned images are present; otherwise omit that flag and
use normal Docker pulls. Require all ten desktop/mobile cases to pass before browser acceptance.
Phase 2 remains **not complete** until the required acceptance gates pass. Trading execution remains
disabled, owner MFA remains mandatory, and development volumes are preserved.

## Original Phase 2 implementation record

Phase 2 extends the existing application with persistent ingestion, immutable Parquet/MinIO storage,
quality/provenance, point-in-time queries and controlled jobs. It does not rebuild the platform.
Phase 1 browser acceptance is preserved as unresolved. No Phase 3, real order, live promotion,
broker credential, generated-code runner, paid service, public deployment or GitHub push was started.

The original master, existing architecture/roadmap/status, Phase 1 report, data/experiment protocols,
threat model, persistence/API/frontend/Docker/tests were inspected. The supplied specification remains
unchanged. The original 60 derived criteria are updated in IMPLEMENTATION_STATUS.md; they are not
invented original questionnaire numbers. Source/evidence hashes identify this uncommitted snapshot.

## Implemented behavior and source

- **Registry/API — IMPLEMENTED, TESTED:** packages/market/{contracts,models}.py,
  apps/api/market/{routes,limits,query_slots}.py, migration 0003_market_data. Providers, datasets,
  jobs, exact symbols and account/instrument links use Phase 1 MFA/RBAC and composite owner keys.
  APIs register providers, upload CSV/Parquet, request public downloads, inspect/cancel jobs, list/filter/
  page datasets, inspect quality/coverage/provenance, compare versions and query samples/as-of data.
  Provider registration records rights/attribution acknowledgement, not legal certification.
- **Storage/publication — IMPLEMENTED, TESTED:** processing.py/storage.py, provision_market.py,
  migrate_runtime.py. Original input bytes, raw row-payload Parquet, normalized/derived Parquet and
  manifests have SHA-256 and pinned MinIO version IDs. Partitions include provider/instrument/type/
  dataset/attempt/month/layer. Zstandard batches cap at 10,000 rows. Publication commits registry and
  audit only after every referenced artifact exists. Published metadata is immutable through triggers;
  the runtime cannot DELETE/TRUNCATE datasets or delete storage versions. Corrections create versions.
- **Object protection — IMPLEMENTED, TESTED:** scoped storage identity has no root/admin/delete
  capability. COMPLIANCE retention defaults to 30 days (configurable for new writes); protected
  retention cannot be shortened. Native tests verify that even the normal root API cannot delete
  a protected version. App reads remain pinned when another version is written under the same key.
  Host/storage administrators and backup/retention operations remain trusted boundaries.
- **Time/quality — IMPLEMENTED, TESTED:** time.py/quality.py. Original timestamps/zones coexist with
  UTC, publication/observation/availability, source sequence and release revision. Ambiguous DST
  requires fold; nonexistent time/offset conflicts/unknown zones fail validation. Availability cannot
  precede observation/publication; bars are unavailable before close. Same-instant sequence cutoffs
  and as-of account partitions prevent later observations/revised releases entering earlier decisions.
  A timestamp without sequence cutoff means the end of that instant.
- **Admission — IMPLEMENTED, TESTED:** PENDING → VALIDATING → VALID/DEGRADED/REJECTED. Schema/time,
  duplicates/order, quote/price/spread, session/holiday and increment anomalies are recorded; uncertain
  calendars, gaps, spikes and unreviewed source changes degrade. Nothing suspicious is silently
  repaired. Coverage uses unique aligned session slots, so duplicates cannot inflate it. Tick expected
  counts remain unknown. Only VALID enters as-of research; DEGRADED needs explicit labeled human
  preview, and REJECTED is refused. Processing SUCCEEDED does not imply quality VALID.
- **Aggregation — IMPLEMENTED, TESTED:** complete ordered finer bars aggregate deterministically into
  coarser UTC buckets, with exact OHLC/known volume, conservative availability and recorded reason.
  Incomplete buckets fail; missing volume stays null. Native tests read the actual derived M5 Parquet
  and prove it is unavailable before close. This is not an invented tick/OHLC/cost/fill simulator.
- **Jobs — IMPLEMENTED, TESTED:** jobs.py, scripts/market_worker.py. PostgreSQL is the durable outbox;
  Redis persistent bounded hints wake it. Two advisory-lock slots, SKIP LOCKED claims, 90-second leases,
  heartbeats/tokens, deduplication, progress, cancellation, bounded retries/backoff and Retry-After
  handling control execution. Current authorization is checked before publication. Recovery restarts
  from pinned complete input; current adapters advertise no byte-range resumption.
- **Limits — IMPLEMENTED, TESTED/CONFIGURED:** 20 MiB input, one million rows/job, bounded columns/cells/
  Parquet expansion, five active jobs/user and configurable dataset quota (default 1,000). Queries
  return at most 2,000 records, scan at most 100,000 and have two expensive-read slots/API process.
  Manifest ranges prune months/parts; an eight-object version/hash cache bounds repeated reads.
  API/worker memory/CPU/tmpfs limits are configured. Multi-year ticks require bounded files/jobs.
- **Market Data Center — IMPLEMENTED, BUILD TESTED; BROWSER BLOCKED:** MarketData.tsx plus
  Management/App/generated contracts/locale/styles. Romanian provider/instrument registration,
  imports/progress/cancel, coverage/quality/history/version/provenance and an interactive stored-price
  chart call real APIs. Sample responses carry provenance/quality/research eligibility. Exact tables
  accompany approximate chart coordinates. Failed/new queries clear the prior chart. No fixture
  history is displayed as real data. English translation is not implemented.

## Providers and actual coverage

**LOCAL CSV/Parquet is native-tested**, including exact tick decimals and sequence zero. All required
asset families can be registered/imported through explicit canonical/source symbols; no tradability
is inferred from the suggested EURUSD/GBPUSD/USDJPY/XAUUSD/XAGUSD/index/crypto catalog.

**ECB is tested against the actual service**, both independently and through authenticated jobs,
PostgreSQL, Parquet and MinIO. Verification fetched five daily EURUSD reference observations dated
2026-10-19..23, HTTP 200, 1,366 bytes, SHA-256
46c3a1b8fefbc66b6155d8eed0ca833353ccb702993ace91884074a3874f849f.
These are reference-day values with no ticks, bid/ask, OHLC or volume. Availability is conservatively
actual download time; historical publication vintages are not invented. Source: ECB statistics;
rights/source URLs and timestamps are retained in ecb-service-verification.json and DATA_PROVENANCE.md.

**MT5 terminal connectivity is BLOCKED/unverified.** The optional export_mt5_history.py requires an
explicitly authorized, already logged-in Windows terminal; it has no login/password/order operation
and is not called by API/worker. Actual access was not supplied/tested. **PREMIUM downloading is NOT
IMPLEMENTED** behind the provider extension point. Active economic-calendar/future-schedule feeds,
verified broker symbol specifications and independent blackout execution are NOT IMPLEMENTED.

Five-year history is **NOT VERIFIED**. No private development market dataset was seeded by the agent.
Native tests use explicit SYNTHETIC_TEST_FIXTURE or actual PUBLIC_PROVIDER data in disposable resources.
Source clocks, calendars and usage attestations still require trustworthy external evidence; a
checksum proves byte integrity, not factual prices, entitlement or complete historical coverage.

## Automated acceptance evidence

[The execution ledger](docs/phase2-evidence/2026-10-26/README.md) records exact argv, UTC time, duration,
child exit code, sanitized output and hash, including failed attempts. The recorder itself exits zero
after recording child failure; all statuses here use the recorded child exit code.

- `make check` — **PASSED, exit 0** (`quality-coverage-regression`): **98 Python passed**, 28 marked
  service tests deliberately deselected; **16 frontend logic tests passed**; Ruff/format, ESLint/
  Prettier, mypy, TypeScript and production build passed. The service tests execute separately.
- `env P0_CACHED_IMAGES=1 make integration` — **PASSED, exit 0** (`final-native-suite`): **one actual
  readiness test**, then **27 service/security/data cases passed before and 27 after restart**,
  followed by strict readiness/execution-denial smoke, HTTP 200. These are repeated cases, not 54
  distinct definitions. Final targeted native reruns also exercise derived Parquet and corrected
  coverage. No failing tests were weakened or skipped.
- `env P0_CACHED_IMAGES=1 make integration-services` — **PASSED, exit 0** in the recorded final
  native runs; owns only its unique containers/ports/volumes/credentials and verifies actual Docker
  loopback bindings/TCP before/after restart. Cleanup is scoped to that project.
- `make smoke-demo` and `.venv/bin/python -m scripts.smoke_demo --require-ready` — **PASSED, exit 0**
  (`final-smoke`, `final-strict-smoke`), readiness HTTP 200 and both execution endpoints refused.
- `make contracts-check` — **PASSED, exit 0**, byte-identical OpenAPI/TypeScript.
- `npm --prefix apps/web audit --audit-level=high` — **PASSED, exit 0**, zero vulnerabilities reported.
- `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`
  — **PASSED, exit 0**, no known vulnerabilities. This does not scan container OS/MinIO binaries.
- `make secret-scan`, `make repository-check`, local actionlint and `docker compose config --quiet`
  — exact results and final source/evidence checks are in the ledger. The fresh scan first detected
  four temporary MinIO accessKey identities in an earlier failed SDK traceback. Those fields were
  redacted with the failure retained and hash updated; no scan rule/exclusion was weakened. Private
  credentials/dumps/models remain excluded; no files staged or committed.
- `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker`
  — **PASSED, exit 0**; subsequent changed API/worker/Web images also built successfully.
- `docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker`
  — **PASSED, exit 0**, additive migration and all six long-running services healthy.
- `npm --prefix apps/web run test:e2e -- --list` — **collection PASSED**, ten cases in three files;
  collection is not execution.
- `env P0_CACHED_IMAGES=1 make browser-integration` — **FAILED, exit 2 / BLOCKED**: native 26+26 cases
  passed in that earlier run; desktop foundation/identity group had **three page-launch failures,
  one request-only denial pass**. Chromium returned `bootstrap_check_in ... Permission denied (1100)`.
  The six remaining market/mobile cases were **NOT RUN** after the failed group. No browser/launch/
  permission workaround was introduced. Later native runs add the tick-partition case for 27+27.

The 17 requested categories map to test_market_time_quality.py and test_market_integration.py:
PostgreSQL; actual MinIO; exact Parquet; object/SQL immutability; checksum corruption detection;
UTC/DST; price/news/revision/cross-asset leakage; gaps/duplicates; bid/ask/spread; deterministic bars;
query bounds; controlled provider/storage failures; queue/retry/deduplication; unauthorized access;
actual restart; versions/provenance; and the collected, currently blocked frontend workflow.
Previous Phase 0/1 tests continue passing. A Starlette TestClient/httpx deprecation warning remains;
no suppression turns warnings or failures into success. Remote CI/container scans/restore/load and
actual MT5/premium/calendar integrations are NOT RUN or NOT IMPLEMENTED as identified above.

## Reliability and performance observations

The native suite submits a 30,000-row, 3,018,955-byte synthetic file, launches an actual worker process,
waits for its durable claim, sends SIGKILL, verifies no published dataset, expires the lease and
recovers with a new worker. Lease time is advanced explicitly to avoid waiting 90 seconds; this is
real process-kill recovery, not power-loss/backup-restore proof. Query sampling returns 2,000 bounded
rows and a truncation indicator. Actual per-stage timings/run IDs are copied to benchmark-write.json
and benchmark-verify.json in the evidence directory. They measure this local fixture/services, not
production or five-year tick throughput. No arbitrary throughput promise is made.

The final coverage-regression run measured upload/recovery/query at 0.137 / 8.169 / 0.259 seconds
in its write stage, and 0.133 / 10.183 / 0.259 seconds after restart. Recovery includes normalization,
Parquet/object writes and publication; query timing requests the bounded 2,000-row sample. These
are individual local observations, without peak-RSS, sustained-load or production throughput proof.

## Failures/fixes and preserved resources

- Initial native startup failed with macOS Keychain -67674 during image pulling. Exact pinned images
  were already cached. An explicit cached-image option uses --pull never and retains normal CI pulls;
  it changes no registry credentials and still executes actual services/assertions.
- MinIO provisioning initially caught S3Error for a missing admin user; the SDK actually raises
  MinioAdminException. Fixed the specific missing-user branch; real service reruns passed.
- Parquet readback initially lost the original timestamp spelling. Normalization now preserves the
  source original_timestamp; exact round-trip tests pass. Integer source sequence zero is preserved.
- Later review added unique-slot coverage, proper invalid-timezone validation, point-in-time source
  sequence cutoffs, bounded read concurrency/scans, upload tmpfs, sanitized storage failures and chart
  clearing on a new/failed query. Regression/static/native evidence is retained, without removed gates.
- Static formatting/type failures were fixed directly. Failed attempts remain recorded in the ledger.
- The first read-only runtime diagnostic mistook an unbound Dockerfile EXPOSE entry for a published
  worker port. It was corrected to inspect actual host bindings; the rerun passed. No service port
  or security assertion was relaxed. Runtime checks also verified restricted DB grants, no ORM/schema
  drift, API temporary upload spooling, read-only roots, resource limits and absent admin/broker
  credential variables. Web HTTP/CSP checks do not establish browser rendering or CSP enforcement.
- The private pre-migration dump first failed because the development data services were stopped.
  They were resumed using existing containers/volumes, the 0600 backup succeeded, and only the additive
  schema update/new storage identity/bucket were applied. Data-container IDs/mounts and Phase 1
  users/accounts/risk/policy/audit digests were checked unchanged. Start times changed on deliberate
  service resume. No valuable development volume was deleted or downgraded.
- The owner's saved Phase 1 browser run timed out selecting Firmă after three other passes. Shared
  form fields now have explicit accessible labels. That fix still needs a permitted-browser rerun;
  the managed-session launch denial prevents claiming it resolved the workflow.

## Remaining gate and owner action

In an administrator-permitted browser execution environment, run:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix apps/web exec -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" P0_CACHED_IMAGES=1 make browser-integration
```

Use the cached flag only when exact required images are present. Otherwise use ordinary image pulls
after resolving the owner's Docker credential environment. Owner authorization for browser testing
already exists; the outstanding blocker is the actual OS permission boundary. Require all ten cases
and inspect real desktop/mobile/accessibility/production-proxy behavior before accepting Phase 1/2.

Initialize the actual local owner privately if still uninitialized, and retain keys/recovery codes.
Supply licensed data or separately authorized Windows-terminal connectivity for additional history.
Plan storage/retained-orphan handling and actual backup restore before valuable large imports.
Do not send broker credentials to research services. Git remains read-only and remote publication
unapproved. Phase 2's Definition of Done is **not fully satisfied** because rendered dashboard/E2E
acceptance is unverified. Phase 3 was not started and trading remains unconditionally disabled.
