# Risk monitor recovery evidence — 2026-10-28

See [the recovery report](../../../../RISK_MONITOR_RECOVERY_REPORT.md). The actual owner deployment
failed when PostgreSQL was recreated: lifecycle timestamps and a connection-refused error establish
the cause. The repaired risk daemon retries bounded transient connections and withholds readiness.

The original account scan and21 checked risk/execution/identity sources are unchanged. Actual
runtime metadata proves UID10001, a fresh marker, schema0009 and no risk_ledger UPDATE grant.
Before/after container IDs show only risk-monitor recreated; development named volumes are retained.
No development database outage was induced during tests. Only an isolated test client's connection
was deliberately terminated; it recovered while preserving owner STOP and a valid HMAC audit.

Command records contain no credentials or raw database/provider responses. Full logs and protected
original scripts remain ignored under `.cache/risk-monitor-recovery/`. The targeted risk suite passes
27 before/27 after disposable restart; unit/native check passes290 Python/153 frontend cases.
Full `make integration` exits0 (452.949s): development readiness,108 service cases before/108 after
graceful restart, and final API/execution-denial smoke readiness200. Contracts, secret/repository
checks also pass. No browser, model or trading acceptance
is inferred from these tests, and no paid request or order was submitted.
