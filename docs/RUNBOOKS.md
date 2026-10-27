# Development runbooks

## Local setup and owner enrollment

Run `make setup`, `make identity-setup`, then `make dev`. Identity setup validates the private existing
.env and adds stable encryption/bootstrap/runtime-DB secrets without changing existing data-service
passwords. Repeating it does not rotate keys. Compose applies Alembic with the admin migration identity
and provisions research_app before starting the API. `make stop` preserves volumes.

Open http://127.0.0.1:5173 and choose “Cont & administrare”. Privately read AUTH_BOOTSTRAP_TOKEN from
.env using a local editor; do not paste it into chat or an issue. Choose the owner username/password
(at least 15 characters), enter the setup token in the local form, enroll an authenticator and save
the ten recovery codes in a password manager. No owner was created in the development database by
the implementation agent. Test identities live only in disposable databases.

Owner bootstrap is single-use even if the environment token remains configured. Subsequent user
creation, authorization edits and policy attestation require recent MFA. Reauthenticate with the
password and a fresh TOTP if five minutes have elapsed; an already used TOTP is intentionally rejected.
To recover, first pass the password step, then use a recovery code and enroll a fresh authenticator.
Recovery revokes all sessions and replaces the recovery set. No insecure password/MFA reset exists.

## Secret and session operations

Preserve AUTH_ENCRYPTION_KEY with the database backup: it protects TOTP seeds and derives recovery,
CSRF, rate and audit HMAC keys. Do not regenerate/delete .env to troubleshoot. Resetting service
passwords in a file does not reset passwords in existing volumes. Automated key rotation, off-host
backup and verified restore are not implemented. Lost owner password/MFA/recovery material requires
an explicit administrative recovery design, not disabling authentication.

Local HTTP sets AUTH_COOKIE_SECURE=false only while all published endpoints remain loopback. Default
configuration uses Secure cookies. Exact AUTH_ORIGINS must match the browser origin. No public/tunnel
hosting is approved. Never pass MIGRATION_DATABASE_URL or POSTGRES_PASSWORD to the API runtime.

## Readiness and migrations

Run `make doctor`, `docker compose ps`, `make smoke-demo` and
`.venv/bin/python -m scripts.smoke_demo --require-ready`. /health/live only checks process liveness;
/health/ready requires PostgreSQL at 0002_identity_governance, Redis and MinIO. Identity additionally
checks that the runtime DB role lacks admin/audit-rewrite privileges. A healthy overview is not proof
that MFA enrollment has happened.

Use `docker compose config --quiet` for validation; raw config/inspect/env output can disclose secrets.
Do not paste raw logs in issues. Apply missing migrations with `docker compose run --rm migrate` or
`make migrate` for the configured host DSN. Back up first. Downgrading 0002 deletes identities and
management/audit records; run downgrades only in disposable tests. Never run down -v or prune against
valuable development resources. The pre-migration backup is private under .cache/phase1 and is not
a claim of tested restoration.

## Native and browser acceptance

`make check` runs static checks, portable tests and the production frontend build. `make integration`
checks the running application, then creates its own unique phase0-test project with a regular bridge,
dynamic loopback ports, temporary credentials and volumes. It validates actual Docker bindings/TCP,
PostgreSQL migrations/transactions, Redis Streams, authenticated MinIO integrity and Phase 1 security
and persistence across graceful restart. Cleanup targets only that unique project, even on failure.
Do not point integration tests at ambient development databases.

Where browser testing is permitted, install Chromium with
`PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix apps/web exec -- playwright install chromium`,
then run `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" make browser-integration`.
This performs native tests and starts disposable API/Web processes with a fresh PostgreSQL database
for each viewport. Temporary owner/password/MFA data never touches the development account. Traces
and screenshots are off during authentication to avoid capturing secrets. A browser policy denial
must be reported, never bypassed. `--list` proves collection only.

Restart acceptance proves graceful process/database persistence, not power-loss durability, worker
recovery, backup restore or internet deployment. Broker/model/feed integration is not part of it.

## Phase 2 data operations

Run make market-setup then make dev. New private scoped MinIO credentials are generated without
rotating existing database/MFA/storage-root secrets. Migration provisions a locked/versioned bucket
and service grants, then starts the trusted data worker. API has a private upload tmpfs; worker roots
remain read-only except their bounded tmpfs. Keep all host ports on loopback.

Use the Market Data section for provider/instrument registration, licensed source imports, job state,
quality and provenance. Account selection refers to an existing owned SIMULATED metadata account.
SUCCEEDED is ingestion completion, not quality acceptance: VALID is required for research, DEGRADED
preview is labeled, and REJECTED is refused. A historical cutoff includes only records actually
available then. Add a source sequence cutoff for partial-instant replay; missing cutoff means end
of instant. Clear/failed queries do not retain an old chart as the new result.

Use P0_CACHED_IMAGES=1 make integration only when exact digest images are already cached. It avoids
registry pulls and does not alter Docker credentials. Ordinary CI still pulls images normally.
make browser-integration runs foundation/identity and market workflows with fresh databases per
viewport/scenario. Current macOS launch Permission denied 1100 remains an external acceptance blocker.

On worker failure inspect the authenticated job error_code/progress/attempt/next_attempt_at. The DB
outbox recovers missing Redis hints; expired leases are fenced and retried. Retries reprocess pinned
complete inputs; byte-range download resumption is not available. Do not edit dataset statuses to
force VALID. Correct data/specifications through a justified new version. Do not delete retained
objects/volumes: COMPLIANCE protection and immutable references must remain intact. Orphan capacity
management and verified restore remain operational work, not silently simulated successes.
