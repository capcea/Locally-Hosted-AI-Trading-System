# AI Trading Research Platform

A local simulation-only research platform built from [the master specification](docs/PRODUCT_SPEC.md).
Phase 4 adds a deterministic simulated risk gateway, account equity/drawdown ledger, atomic risk
reservations, exact policy/profile versions, independent monitor and Romanian Risk Center to the
identity, immutable market data and durable simulator foundation. Native/portable checks pass;
**full Phase 4 acceptance is blocked by managed Chromium launch**. See the
[Phase 4 report](PHASE4_COMPLETION_REPORT.md).

All external broker orders remain DENY_ALL. No generated-code runner, external broker-capable
executor, strategy backtester, AI inference or paper engine is implemented. Synthetic values never
certify real balances, tradability, external margin/protection or performance. Current risk HMACs
have SIMULATED scope only; actual MT5/cTrader connectivity is unverified.

## Start locally

Use Python 3.12.14, Node 24.7.0, npm, Make and a running Docker Compose engine. Dependencies are locked
in uv.lock and apps/web/package-lock.json; runtime pins live in .python-version and .node-version.

```sh
make setup
make market-setup
make dev
make smoke-demo
make integration
```

`make dev` also runs identity/market setup idempotently. Existing data-service secrets/volumes are preserved.
Additive migrations through 0005 add data/jobs, execution journal and simulated risk ledgers. API/worker receive no admin storage credentials.
Use `make setup PYTHON=/absolute/path/to/python3.12` if needed. The initial MinIO image build compiles
checksum-pinned upstream source and can take time. `make stop` preserves development volumes.

Open [the dashboard](http://127.0.0.1:5173), choose “Cont & administrare”, and use the private
AUTH_BOOTSTRAP_TOKEN from your ignored 0600 .env in the owner setup form. Choose your own password,
enroll an authenticator and save recovery codes privately. Never paste secrets into chat/issues.
No development owner account was created automatically. See [the runbook](docs/RUNBOOKS.md).

All published endpoints bind to loopback. This is not a public deployment. API runtime credentials
are separate from migration credentials. Preserve AUTH_ENCRYPTION_KEY with private backups; changing
it casually breaks MFA/recovery and audit verification. No broker/model credentials are needed.

Without Docker, `make local-api` and `make local-web` can develop the public shell, but persistent
authentication requires migrated PostgreSQL. Missing dependencies honestly return readiness 503.

## Verify

```sh
make check
make contracts-check
make repository-check
make secret-scan
make smoke-demo
.venv/bin/python -m scripts.smoke_demo --require-ready
make integration
```

`make check` covers Python/frontend lint, formatting, types, portable/unit tests and frontend build.
`make integration` requires the local API, then runs native PostgreSQL migration/security/persistence,
Redis Streams and authenticated MinIO tests in disposable projects before/after restart. It verifies
real loopback port bindings/TCP and removes only its own resources. Never use ambient databases for
these destructive migration tests. `make contracts` regenerates API artifacts; `make seed-demo` writes
only an explicit configuration fixture.

Where Chromium execution is permitted:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix apps/web exec -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" make browser-integration
```

For an explicit focused run against the same disposable PostgreSQL/Redis/MinIO and real owner/MFA
workflow, set `E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=market` before `make browser-integration`.
The accepted projects are desktop/mobile and scenarios foundation/market/broker/risk. Unset both variables for
the complete fourteen-case suite; focused results never establish full-suite acceptance.

The browser harness creates separate databases/users and scoped storage per viewport/scenario. It does not initialize your
owner account. The last actual run hit macOS `bootstrap_check_in ... Permission denied (1100)`;
three desktop page cases failed before page creation, one HTTP-only case passed, and ten later
cases (including mobile) were not run. Authorization from the owner did not remove the OS restriction. No bypass was attempted.

## Safety boundary

Configuration only accepts SIMULATED and DENY_ALL; enabling live or generated-code execution fails
startup. Both order/activation endpoints always return 403, and worker execution is independently
denied. Broker metadata/observations confer no execution authority. Reviewed approval records never grant execution power.
Risk percentages and human policy attestations cannot authorize trading. Authentication tokens never
enter localStorage; TOTP seeds are encrypted, passwords are Argon2id hashes and sessions are revocable.

## Documentation

- [Phase 4 report and exact tests](PHASE4_COMPLETION_REPORT.md)
- [Risk calculations](docs/RISK_CALCULATIONS.md), [authorization protocol](docs/RISK_AUTHORIZATION_PROTOCOL.md)
- [Phase 3 historical report](PHASE3_COMPLETION_REPORT.md)
- [Phase 2 historical report](PHASE2_COMPLETION_REPORT.md)
- [Phase 1 historical report](PHASE1_COMPLETION_REPORT.md)
- [Data provenance/input formats](docs/DATA_PROVENANCE.md)
- [Implementation inventory and 60 derived criteria](IMPLEMENTATION_STATUS.md)
- [Architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), [roadmap](docs/ROADMAP.md)
- [Deployment checklist](DEPLOYMENT_CHECKLIST.md), [next steps](NEXT_STEPS.md), [runbooks](docs/RUNBOOKS.md)
- [Risk policy](docs/RISK_POLICY.md), [limitations](docs/RULES_AND_LIMITATIONS.md)
- [Historical Phase 0 report](PHASE0_COMPLETION_REPORT.md), [audit](AUDIT_REPORT.md)
- [GitHub preparation](docs/GITHUB_PREPARATION.md), [external references](docs/external-sources.md)

Phase 4 code/native tests are implemented; full browser acceptance and actual broker reads remain blocked. No remote repository, push, public deployment or live-trading operation is authorized here.

## Market data

Create an owned SIMULATED account, then open “Date de piață”. Register an instrument/provider and
acknowledge source usage rights. Import exact-decimal CSV/Parquet with event_time, observed_at and
available_at, source symbol/zone and a declared range/calendar. Unknown calendars degrade quality;
only VALID datasets enter as-of research. The chart shows actual stored samples with provenance.
ECB supports daily EUR reference rates, without bid/ask/OHLC/volume; MT5 retrieval needs a separate
authorized Windows terminal. No five-year coverage is asserted. See docs/DATA_PROVENANCE.md.

A fixed data worker runs alongside API/Web. Inputs are capped at 20 MiB/one million rows per job;
multi-year/tick archives must be split into bounded files. Objects have pinned versions and default
30-day COMPLIANCE retention, plus application delete denial. Protected retention cannot be shortened;
plan storage before large imports. This is not a backup/restore service or a generated-code sandbox.

Where exact pinned images are cached and registry credential lookup is unavailable, use
`P0_CACHED_IMAGES=1 make integration` or `P0_CACHED_IMAGES=1 make browser-integration`. This disables
pulling, preserves configured credentials and fails if required images are absent. The last ordinary
pull encountered macOS Keychain -67674; cached real-service runs passed. Never replace actual tests
with fabricated results. Browser execution still requires a legitimately permitted environment.

## Simulated Risk Center

Create a synthetic account/run and explicit quote, then open “Centru de risc”. Configure an owned
versioned profile, draft a personal or exact prop policy with provenance/dates, attest with recent
MFA, and declare synthetic payoff/tick/margin/FX/calendar evidence. New configuration remains stopped
until explicit review/CLEAR. Required stops, fresh inputs, monitored account state and reservations
are checked at submission and every actual simulated fill. What-if creates no authorization.
STOP blocks entries; FLATTEN is separate and closes only available synthetic positions. No real broker
credentials are required or accepted. Read the risk/incident runbooks before changing assumptions.
