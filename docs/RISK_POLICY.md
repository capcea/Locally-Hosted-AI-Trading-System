# Risk policy — Phase 4

The operational SIMULATED gateway now enforces exact account/strategy/instrument/asset/firm/program
limits and strict latest verified policies. Default internal caps are 0.25% per trade, 1% daily,
3% total, 1% aggregate, 0.5% correlated group, three positions and 0.1% capital headroom buffer.
These are editable synthetic safety defaults, not advice or official prop-firm limits. New
configuration is stopped until explicit owner-MFA review/CLEAR. No implicit account approval exists.

Policy terms require provenance/digest, exact effective period, currency/timezone/DST reference,
loss/high-water semantics, overnight/weekend/news/style/instrument/automation/duration permissions.
Personal policy is explicit; prop policy additionally binds the latest verified exact account/program
FirmPolicy. Latest unknown/expired/revoked versions block; scope revisions invalidate. More restrictive
applicable profiles and verified policy ceilings take precedence. Human attestation is not proof of
external contractual compliance. All future DEMO/LIVE execution remains unconditionally DENY_ALL.

SL and TP, fresh quotes/specs/conversions/calendars, supported payoff, verified margin, current monitor,
ledger integrity, legal volume and exact material scope are mandatory. Decimal sizing rounds volume
down and risk up, including modeled fees/slippage/funding. Missing or contradictory inputs refuse.
Warnings reduce future risk; losses never increase it. Stops do not guarantee fills at their price.

Durable account-locked reservations prevent competing strategies from spending the same budget.
UNKNOWN retains allocation; partial/cancel/close release follows verified synthetic truth. Submission
and every fill require freshly validated, scoped, tamper-evident grants consumed in the same database
transaction as journal/audit. Owner STOP persists; privileged FLATTEN is distinct and simulated only.

Read [RISK_CALCULATIONS.md](RISK_CALCULATIONS.md),
[RISK_AUTHORIZATION_PROTOCOL.md](RISK_AUTHORIZATION_PROTOCOL.md),
[PROP_FIRM_POLICY_SCHEMA.md](PROP_FIRM_POLICY_SCHEMA.md),
[RISK_RESERVATION_RUNBOOK.md](RISK_RESERVATION_RUNBOOK.md) and
[INCIDENT_KILL_SWITCH_RUNBOOK.md](INCIDENT_KILL_SWITCH_RUNBOOK.md).

No external order-capable executor, separate external approval keys, two-acknowledgement live approval,
actual broker margin/protection proof, generated-code runner or live promotion exists in this release.
