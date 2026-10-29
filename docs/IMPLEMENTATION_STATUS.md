# Implementation status — canonical pointer

## Current sidebar health follow-up — 2026-10-29

The pre-request/completion clock mismatch that made valid infrastructure observations UNKNOWN is
fixed. Completion time and backend timestamp freshness, stable service IDs, response fencing and
retry/recovery are covered by native tests. Native check294 Python/186 frontend, focused67,
contracts and smoke pass. Browser execution remains BLOCKED; static nginx Web update is pending.
No Docker/data/security/financial changes. Public phase6/Phase7 PLANNED remain coarse static
metadata; Phase7A foundation has partial acceptance. Read
[the repair report](../SIDEBAR_SYSTEM_HEALTH_FIX_REPORT.md) and canonical status for the full scope.

## Current MFA/session repair — 2026-10-29

Invalid MFA no longer clears a valid session. In-place step-up, response-generation fencing and
atomic session commit before cookie publication correct three reproduced defects. Recent MFA,
CSRF/RBAC, revocation and genuine expiration remain enforced; original sensitive actions require
explicit review/resubmission. API/Web alone were updated; existing data/enrollment are preserved.
Native check294 Python/160 frontend, focused auth27+27, full disposable services117+117, contracts,
deployed smoke and secret/repository checks pass. Browser execution remains BLOCKED;28 cases collect
only. No paid inference or financial/trading changes. Read
[the repair report](../MFA_SESSION_FLOW_FIX_REPORT.md) and
[canonical current status](../IMPLEMENTATION_STATUS.md); earlier evidence below is preserved.

## Current risk daemon follow-up — 2026-10-28

The risk-monitor process now safely recovers bounded transient PostgreSQL interruptions, with no
readiness publication on failure or weakening of risk/owner controls. Deployed service is healthy;
only that container was recreated. Native290 Python/153 frontend and focused real-risk27+27 pass.
Full integration also passes108+108 across restart and final deployed API/execution-denial smoke200.
Contracts and secret/repository checks pass.
Read [the recovery report](../RISK_MONITOR_RECOVERY_REPORT.md) and
[canonical current status](../IMPLEMENTATION_STATUS.md) for the full regression result and limits.

## Current local campaign startup — 2026-10-28

The owner-upgraded database is0009. The missing campaign-worker module in the control image is
fixed and protected by a packaged entrypoint build check. The repaired service is healthy; actual
readiness/SQL/network boundary checks pass. No other container or persistent mount was changed by
this repair. Full `make integration` passes: readiness,107+107 across restart and API smoke200.
`make check`283 Python/153 frontend, contracts and secret/repository scans pass. See [canonical status](../IMPLEMENTATION_STATUS.md) and
[startup evidence](../OPENROUTER_INTEGRATION_REPORT.md#follow-up-campaign-container-startup-repair--2026-10-28)
for current final results. Earlier pending-upgrade/failing-schema records below are historical.

## Current OpenRouter follow-up — 2026-10-28

Read [the integration report](../OPENROUTER_INTEGRATION_REPORT.md) and
[canonical current status](../IMPLEMENTATION_STATUS.md). Zero configured endpoints/connections/models
explain the empty selectors; independent loading/prerequisite/protocol fixes are also implemented.
Exact public OpenRouter is an explicit operator/owner cloud exception, disabled by default, using
write-only encrypted keys and scoped budgets; private providers and SIMULATED/DENY_ALL remain.
Native check283 Python/153 frontend; focused cloud7+7 and full disposable107+107 pass across restart.
`make integration` fails the retained development schema probe (0009 required,0008 retained); no
migration/rebuild/opt-in was performed. Browser execution and real provider acceptance remain open.
Earlier phase results below are preserved historical evidence, not current deployment acceptance.


Updated 2026-10-28. Read [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) for all60 criteria.
The owner explicitly authorized Phase6 and reports Phases0–5.5 local automated acceptance passed.
That is OWNER_REPORTED_PASS, separate from agent verification and remaining manual/external gates.

Read [the Phase6 report](../PHASE6_COMPLETION_REPORT.md) for the private gateway, native evidence,
unavailable real Ollama, verified local AI service boundaries and prohibited managed browser
execution. No external execution, generated-code runner or Phase7 is enabled. Prior reports retain
historical evidence: [Phase5](../PHASE5_COMPLETION_REPORT.md),
[Phase5.5B](../PHASE55B_COMPLETION_REPORT.md), [UX coverage](ux-migration-coverage.md).

Current Phase6 follow-up corrects the owner-reported AI dropdown exact-label failure. Native
regression evidence is separate from pending owner-local browser acceptance; see the
[accessible-name correction](../PHASE6_COMPLETION_REPORT.md#ai-dropdown-accessible-name-correction--2026-10-28).

The current approved V1 redesign is source-implemented with native regression evidence; rendered
acceptance and reviewed golden replacements remain open. Read the
[V1 implementation report](../REDESIGN_V1_IMPLEMENTATION_REPORT.md) and
[visual fidelity ledger](../REDESIGN_V1_VISUAL_FIDELITY.md). No Phase7 or broker execution.

V1 visual polish follow-up: one real Home before artifact was inspected and supported source layout
fixes pass fresh native checks. All after/nine-screen/mobile visual acceptance remains blocked by
managed browser policy. See [the final visual audit](../REDESIGN_V1_FINAL_VISUAL_AUDIT.md).


## Current scope — Phase7A

The owner authorized the bounded research foundation and postponed V1 visual acceptance. Prior
no-Phase7 statements above retain their historical scope. Current implementation, exact native
results and browser/model/data blockers are in [the Phase7A report](../PHASE7A_COMPLETION_REPORT.md)
and [canonical status](../IMPLEMENTATION_STATUS.md). Owner-MFA handoffs remain; no Phase7B, generated
code execution, automatic promotion or external orders. The development stack has not been migrated
or rebuilt for this phase.

Final Phase7A evidence:263 Python/152 frontend tests;14 focused campaign cases before/after restart;
100 full isolated service cases before/after restart. Contracts, existing deployed API smoke and
secret/repository checks pass. `make integration` itself fails because source expects0008 while the
retained development schema is0007.26 browser cases collect but are not executed. All external/manual
gates and the earlier transient S3 clock-skew failure remain explicit in the report.
