# Risk reservations and concurrency runbook

Use `make integration-services` for actual disposable PostgreSQL/Redis/MinIO verification; it creates a
unique project, random private test credentials and dynamic loopback ports, then removes only its own
resources. Never use `docker compose down --volumes` on the development project.

The transaction lock order is account → simulation run. All competing strategies share the account
mutex; validate after locking, then atomically write the risk decision/grant/consumption/reservation,
order journal and audit. A database exception must roll back all of these. Every new command respects
account-global time. Separate accounts are required for independent historical clocks.

Reservation states are RESERVED, OPEN, UNKNOWN and RELEASED. Partial hedged fill/cancel/close releases
only the verified remainder; netting retains a conservative allocation until flat. An ambiguous submit
never releases budget or blindly retries. Reconcile durable synthetic truth first, inspect incidents,
then explicitly review and CLEAR the persisted stop with recent owner MFA. A timeout is not evidence
that an order failed. Do not manually zero allocations or rewrite immutable ledger/authorization rows.

After an outage, start PostgreSQL and the trusted independent risk-monitor. Verify readiness and
monitor heartbeat, inspect account status, ledger integrity, journal chain, unknown orders and retained
reservations. Entries remain blocked during uncertainty. The monitor polls fixed trusted code without
an LLM, broker keys or Docker socket. Do not use a database admin identity for this worker.

The native suite includes three actual competing processes (two allowed allocations, one refusal),
SIGKILL before/after commit, idempotent retries, immutable SQL grants and actual database restart.
These tests certify the local synthetic transaction boundary; they do not prove exactly-once delivery
to an external broker, production load resilience or network-partition behavior of a future executor.
