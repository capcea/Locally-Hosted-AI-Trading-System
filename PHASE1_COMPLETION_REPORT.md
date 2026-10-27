# Phase 1 completion report

Date: 2026-10-26 (Europe/Bucharest; evidence timestamps are UTC).
Decision: **BLOCKED / NOT COMPLETE — browser workflow acceptance has not passed.**

Phase 1 identity, persistent governance and audit are implemented and tested against actual local
PostgreSQL. Romanian management screens call those real APIs and compile successfully. The owner
authorized browser testing, but Chromium still failed at the managed macOS process boundary. This
report does not substitute native API tests or a frontend build for working browser acceptance.
Phase 2 was not started. LIVE, broker orders, automatic live promotion and generated-code execution
remain disabled. No external integration is claimed from a mock or metadata record.

## Scope and preserved baseline

Read the original master, PRODUCT_SPEC, previous audit/status/Phase 0 reports, architecture, roadmap,
threat model, risk policy and deployment checklist before implementation. The existing repository was
extended, not rebuilt. The supplied master and docs/PRODUCT_SPEC.md have identical SHA-256
c125b5353c6a6653b5d783c90ec037adfa70f61e7ba9d04b594df9ac8814d085.
The 60 derived audit criteria remain in IMPLEMENTATION_STATUS.md, with their numbering distinction
from the unavailable original questionnaire preserved.

A private source baseline and pre-migration pg_dump were saved under ignored .cache/phase1; the dump
is 0600. A dump is not a tested restore. No development database downgrade, volume deletion, prune,
real broker connection, owner credential invention or real order submission occurred. PostgreSQL,
Redis and MinIO container IDs, start times and mounts match the pre-migration snapshot. API/Web and
the one-shot migration container were rebuilt/recreated intentionally. The current schema is
0002_identity_governance; /health/ready returns HTTP 200. Owner setup is available but the actual
development owner is still uninitialized. All test identities were disposable.

## Implemented features and evidence

### A. Identity and authorization — PASSED native; BLOCKED browser acceptance

Sources: apps/api/identity/{schemas,crypto,dependencies,routes}.py; apps/api/config.py;
packages/persistence/models.py; scripts/{identity_setup,provision_runtime,migrate_runtime}.py.
Migration: 0002_identity_governance adds roles, users, security_state, login_sessions, recovery_codes
and rate_buckets, with constraints/indexes. Identity service requires PostgreSQL and rejects a
superuser/create-role/create-database/audit-rewrite runtime identity.

- Bootstrap uses a private 256-bit token and a database lock; concurrent attempts create exactly one
  owner. It is single-use. Additional users are created only by the owner; there is no public signup.
- Argon2id uses 64 MiB, three iterations and parallelism one, random salts and rehash support. No
  plaintext password is stored. Generic failures perform a dummy hash for unknown users.
- Password authentication grants only ENROLLMENT/MFA sessions. TOTP enrollment is encrypted with
  Fernet, expires in five minutes, and uses persisted counters to reject replay. Recovery requires
  password authentication plus a single-use hashed code, revokes all sessions and forces fresh MFA.
- Opaque random sessions are stored as hashes. HttpOnly/SameSite=Strict cookies rotate after MFA and
  reauthentication; absolute/idle expiry and revocation persist. Sensitive owner actions require MFA
  within five minutes. Password and user authorization changes revoke affected sessions.
- Unsafe cookie requests require exact Origin and session-bound HMAC CSRF; persistent per-address/
  subject limits throttle password/MFA attempts. OWNER/OPERATOR/VIEWER authorization is enforced.
- Record ownership is separate from the OWNER role: one user's data cannot be read, listed or linked
  by another. VIEWER cannot write. There is no account-sharing/delegation or streaming API.

Tests: test_identity_crypto.py (four portable tests), test_identity_setup.py (two setup tests) and
native cases in test_phase1_integration.py cover bootstrap/concurrency, hashing, encryption, TOTP
success/failure/replay/expiry, recovery reuse denial, absolute/idle expiry, recent MFA, revocation,
roles, cross-user/account denial, CSRF, throttling and privileged-DB refusal. These passed.

Limitations: local HTTP explicitly disables Secure cookies only for the loopback configuration;
production TLS/Secure deployment is not tested. TOTP is not phishing-resistant. No WebAuthn, automated
key rotation, email/password-reset bypass, production abuse/load validation or retention service is
implemented. Private keys must be backed up securely and never casually regenerated.

### B. Core persistence and API contracts — PASSED for metadata scope

Sources: packages/persistence/{models,store}.py, apps/api/governance/{schemas,routes}.py,
migrations/versions/0002_identity_governance.py, docs/openapi.json, generated/api.ts.

Persistent entities cover users/roles; trading accounts; broker connection metadata; venues and
instruments; firms and programs; versioned firm policies; risk profiles; strategies and immutable
strategy versions; experiment metadata; approval requests; audit events; and incidents. There are
13 scoped management record kinds in the governance API, in addition to identity/audit APIs.

GET/POST /api/v1/records/{kind}, GET/PUT /records/{kind}/{id}, explicit policy verification and approval
review routes implement real transactions, ownership/reference checks, revision conflicts, filtering
and bounded pagination. Users and audit have their own paginated routes. Immutable content cannot be
edited through generic PUT. Composite foreign keys enforce same-owner references. Approval scope must
match the strategy account. Exact NUMERIC columns and decimal-string inputs preserve monetary values;
floating-point financial input and LIVE/broker-secret fields are rejected. Validation/database errors
return sanitized messages. OpenAPI and generated TypeScript are checked for drift.

Native tests create/read every metadata kind, exercise exact values, unauthorized references,
conflicts/rollback, immutable strategy/policy content, PostgreSQL up/down/up, persistence after service
restart and matching ORM column/type/index/foreign-key metadata. All passed. Phase 0 SQLite migration
tests remain portable checks, not substituted PostgreSQL evidence.

Limitations: account values are user configuration, not broker balances. Risk records are not a risk
engine. Broker records contain no credentials or adapter calls. Strategy digests/experiments/reviews
are metadata, not executed research, safe code certification or promotion authority. Later data,
order/fill/position/reconciliation and risk-ledger models remain NOT IMPLEMENTED.

### C. Firm policy foundation — PASSED native metadata behavior

Bootstrap creates only FTMO, FundedNext and The5ers catalog names; custom firms are supported.
Programs specify phase/platform. Policies bind immutable source references/document SHA-256, effective
and expiry timestamps, account/program identity and captured revisions. URL credentials/query strings/
fragments are rejected. Owner source-review acknowledgement records verification actor/time/state.

Only the latest version is eligible. Missing, unverified, expired/future-dated, archived or changed-scope
records fail closed. Updating the account invalidates the existing attestation. Eligibility always
returns trading_authorized=false, including after a human verification. No current firm permission
has been invented, imported or externally verified. Policy source contents are not fetched or
interpreted automatically. Native tests for these boundaries passed; browser attestation is unverified.

### D. Transactional audit — PASSED native; bounded trust model

Sources: packages/persistence/audit.py, identity/governance routes, runtime grants and migration
triggers. Events have sequence/UUID, UTC timestamp, actor/role/MFA context, entity/correlation IDs,
public before/after metadata and previous/current HMAC-SHA256 digests. Mutation and success event
commit in the same transaction. Authentication failures and rate counters persist separately.

Database privileges and triggers deny audit UPDATE/DELETE/TRUNCATE. A serialized head prevents
concurrent branching. Runtime modification denial, administrator tamper detection, chain verification,
injected audit-failure rollback, concurrent revision conflict and restart persistence all passed.

Limitations: the process, host administrator and administrator with the HMAC key are trusted. A
compromised trusted backend/key can construct events. There is no independent external anchor,
separate audit-writer service, retention job, full causal decision replay or verified full restore.
Passwords, seeds, session/recovery values are excluded from audit payloads and request logging.

### E. Romanian React management — implemented, acceptance BLOCKED

Sources: apps/web/src/{Management,management-api,management-locale,App,schema,styles}, generated/api.ts.
Screens implement bootstrap/login/MFA/recovery, account overview/create/edit, risk profiles,
firm/program/policy entry/attestation, password/session controls, owner user/role management and audit
paging/integrity verification. Existing infrastructure status, themes, responsive navigation and
outage behavior remain. Sources distinguish USER_ENTERED and SYNTHETIC_TEST_FIXTURE from public
configuration references. English localization is not yet implemented.

All screens call real backend APIs. Session CSRF state stays in memory, cookies are HttpOnly and no
auth token is stored in localStorage. Enrollment/recovery values are displayed only to the user and
cleared after use. Browser traces/screenshots and automatic failure DOM snapshots are disabled for
these secret-bearing flows; assertions are unchanged.

Six existing Phase 0 browser cases plus two new desktop/mobile identity/account/risk/policy/security/
audit workflows collect. Actual desktop Chromium launch failed before page creation; no rendered
management interaction, responsive layout, accessibility or production CSP enforcement is accepted.
The one passing request-only test checked actual denial through Vite's proxy, not a browser page.

## Exact final commands and results

The [evidence ledger](docs/phase0-evidence/2026-10-26-phase1/README.md) links every captured argv,
UTC start, duration, child exit code, sanitized output and SHA-256. The capture wrapper itself returns
zero after recording a child failure; classifications below use the recorded child exit code.

- `make check` — **PASSED, exit 0** (`acceptance-quality`): Ruff lint/format, ESLint/Prettier, mypy,
  TypeScript, **81 Python passed / 21 deliberately deselected service tests**, **16 frontend passed**,
  production Vite build. The service tests run through the separate native target below.
- `make integration` — **PASSED, exit 0** (`acceptance-integration`): **one application readiness test**,
  **20 native disposable cases passed in write stage and 20 passed after restart**, then strict smoke
  with HTTP 200. These are 20 repeated cases, not 40 distinct test definitions. No skips.
- `make smoke-demo` — **PASSED, exit 0** (`current-smoke`); real API and both execution refusals.
- `.venv/bin/python -m scripts.smoke_demo --require-ready` — **PASSED, exit 0**
  (`current-strict-readiness`); readiness HTTP 200 and all three dependencies healthy.
- `make contracts-check` — **PASSED, exit 0**; no OpenAPI/TypeScript drift.
- `npm --prefix apps/web audit --audit-level=high` — **PASSED, exit 0**, zero known vulnerabilities.
- `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`
  — **PASSED, exit 0**, no known vulnerabilities. This is not a container/OS vulnerability scan.
- `make secret-scan` and `make repository-check` — **PASSED, exit 0**; source/evidence Gitleaks and
  sensitive-path exclusions. Ignored .env, dumps, caches, credentials, models and raw logs are excluded.
- `.tools/bin/actionlint .github/workflows/ci.yml` and `docker compose config --quiet`
  — **PASSED, exit 0**, local static validation only.
- `make identity-setup` — **PASSED, exit 0**; private stable auth/runtime secrets provisioned locally.
- `env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web` — **PASSED, exit 0**;
  final API/migration-only rebuild also passed after status copy changed.
- `docker compose up -d --wait --wait-timeout 180 api web` — **PASSED, exit 0** after packaging fix;
  migration completed, all five long-running services healthy.
- `npm --prefix apps/web run test:e2e -- --list` — **PASSED collection, exit 0**, eight cases;
  collection does not mean execution passed.
- `make browser-integration` — **FAILED, exit 2; acceptance BLOCKED**. Native stage again passed
  20+20. Nested `npm run test:e2e -- --project=desktop --workers=1` had **three failed, one passed**.
  Failed cases hit Chromium `bootstrap_check_in … MachPortRendezvousServer … Permission denied (1100)`
  before page creation. Four mobile cases were **NOT RUN** after the failed desktop stage.
  Scoped cleanup completed. No launch flag/alternate browser/permission bypass was introduced.
- Read-only diagnostics (`acceptance-preservation-and-boundaries`, `schema-drift`) — **PASSED, exit 0**:
  actual bindings/TCP, preserved data resources, schema revision/runtime privileges, setup availability,
  simulation flags, Nginx HTTP/CSP header and ORM/schema comparison. Full inline commands are in JSON.

One Starlette TestClient/httpx deprecation warning remains; tests passed without suppressing it.
Remote GitHub CI, container vulnerability scans, fresh-machine install, actual model/feed/broker
services, load/fault/power-loss/backup-restore checks are NOT RUN. No results are fabricated for them.

## Failures found and fixes

- Initial expanded native run: one failed / 16 passed. Immutable strategy-version reads used
  SELECT FOR UPDATE, which required UPDATE privilege intentionally withheld. Changed immutable
  version lookup to a normal stable read; retained the privilege denial and immutability assertions.
  The rerun passed 17+17, and expanded acceptance later passed 20+20.
- First local stack start exited 1: scripts.migrate_runtime was absent from the image. Dockerfile now
  copies only the required migration/provisioning modules; rebuild/start/migration/readiness passed.
- A stale Phase 0 smoke phase check rejected the new overview.phase=1 and caused two unit failures.
  It now recognizes phases 0 and 1 while preserving application identity, strict safety/readiness and
  execution-denial checks. Both original regression tests and all safety tests pass unchanged.
- Intermediate static checks caught a typed callback returning Any and long lines; fixed directly.
  An early Prettier invocation used the wrong relative path (exit 2); the explicit project path fixed it.
- Initial pip-audit exited 1 trying to create ~/Library/Caches/pip-audit, outside writable roots.
  Its supported --cache-dir option now writes inside the workspace; scan passed without escalation.
- Public status/catalog copy was updated for identity availability. Policy attestation actor/time/
  captured revisions are exposed for review. Secret-bearing source URLs are rejected and tested.
- Browser OS failure is unresolved. Tests were not weakened, skipped or relabeled as successful.

## Required owner action and remaining acceptance

Provide an administrator-approved execution environment that permits Chromium and run:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix apps/web exec -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" make browser-integration
```

Require all eight cases to pass and fix actual UI failures, then inspect desktop/mobile accessibility
and the production frontend. No further authorization request is needed for browser testing itself;
the owner already gave it. The remaining problem is the actual managed OS permission boundary.

Initialize the actual local owner privately via the dashboard and save recovery material. Do not
paste .env secrets here. Git remains read-only; no commit/remote/push was made. Remote repository
creation/push still needs separate owner approval. Public deployment additionally requires the open
security/operations gates in DEPLOYMENT_CHECKLIST.md; Phase 1 code alone is not deployment approval.

**Definition of Done is not satisfied:** native identity, RBAC, persistence, audit and safety pass,
but real frontend workflows/E2E have not passed. The recommended next implementation module, after
closing this gate and receiving scope, is Phase 2 data provenance and time correctness. It was not
started. All live trading and experimental execution remain disabled.

## Phase 2 follow-up — 2026-10-26

The owner supplied a later browser report showing three passing foundation tests and an identity
workflow timeout at the Firmă selector. Phase 2 adds explicit accessible names to the shared select/
input fields. That fix is compiled, not accepted as browser-passing: the subsequent authorized run
in this managed environment again failed at Chromium Permission denied (1100) before page creation.
The Phase 1 acceptance gate remains open. Native Phase 0/1 tests continue to run with Phase 2.
