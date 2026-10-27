# Implementation status — canonical pointer

Updated 2026-10-27. Read [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) for all 60 derived
criteria and [../PHASE4_COMPLETION_REPORT.md](../PHASE4_COMPLETION_REPORT.md) for exact evidence.

Phase 4 simulated risk gateway, Decimal sizing, exact versioned policies, account drawdown ledger,
atomic reservations, consumed signed scopes, independent monitor and owner-MFA emergency APIs are
implemented and native-tested. `make check` passes 179 Python and 16 frontend tests; actual disposable
integration passes 60 cases per write/restart stage. Local revision0005 and strict readiness pass.

Full acceptance remains BLOCKED: risk desktop and full-suite attempts hit macOS Chromium launch
Permission denied (1100). Full attempt has 3 launch failures, 1 HTTP-only pass and 10 later NOT RUN;
all 14 cases collect. Owner-reported Phase 3 local passes remain separate evidence. All external demo/
live orders, generated code and promotion stay disabled. No Phase 5, broker keys, publish/remote/push.
