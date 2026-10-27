# Incidents and kill switch — SIMULATED only

STOP_NEW_ENTRIES persists manual stop state and audit; it blocks new entry grants and fill admission.
It does not claim to close positions. Protective synthetic exits remain enabled.

FLATTEN is a distinct privileged action requiring owner authentication, recent MFA, explicit action
selection, account revision and idempotency key. It cancels known synthetic pending orders and attempts
synthetic closes using actual available current quote/liquidity. Read completed/remaining counts;
UNKNOWN or insufficient liquidity means incomplete. External_positions_closed is always false.

To respond: authenticate, open Centru de risc, inspect data/ledger verification, monitor heartbeat,
headroom, exact refusal reasons, reservations, journal and incidents. STOP immediately if needed.
Choose FLATTEN separately only for the intended synthetic account. Refresh current state; never infer
success from an old receipt. Retry with the same key only for the same payload; conflicting payloads
are refused. Duplicate responses include the original receipt and current emergency state/revision.

Resolve stale quotes/calendars/policies, clock errors or unknown truth at their source. Update only
verified FX/calendar evidence while exposed; payoff/margin/group/protection assumptions cannot be
silently changed. Review configuration/attestation again. Poll the independent monitor. Only then use
owner-MFA CLEAR_STOP with the current revision. Hard breaches or missing reset evidence cannot be
cleared by toggling flags. Stop and incident state survives process/database restarts.

For integrity failure, retain evidence and private backups. Do not edit immutable rows, fabricate an
opening balance, delete owner enrollment or reset production volumes to obtain green checks. Recovery
from malicious admin tampering needs a separately reviewed trustworthy restore/anchor procedure.
No notification delivery or external emergency-order capability is implemented in this phase.
