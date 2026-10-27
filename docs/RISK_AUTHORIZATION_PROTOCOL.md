# Simulated risk authorization protocol

Phase 4 grants authorize only a specific SIMULATED journal operation. Every external adapter mutation,
legacy order endpoint, live activation and DEMO/LIVE execution remains DENY_ALL. This protocol is a
future integration contract, not a deployed independent broker execution capability.

1. Authenticate the owner/account and validate the bounded typed proposal. Recent owner MFA is required
   for configuration, policy verification and emergency operations. Strategy metadata must belong to
   the same owner/account; no free-form source, LLM output or client flag grants authority.
2. Lock the account before its run. Verify journal/ledger integrity, persisted STOP, real monitor
   heartbeat, account/global clock, exact latest verified policy/profile versions and immutable context.
3. Assess actual quote/session/calendar/protection/FX/payoff/margin/exposure and return typed
   ALLOW, DENY or INDETERMINATE with reasons and calculation evidence. Persist denial and audit as well.
4. On ALLOW bind account/run/order, command/request/context digests, policy/profile IDs, risk, margin,
   issue time and expiry. Domain-separated HMAC-SHA256 signs canonical scope using the private service
   key. The browser never receives signing authority. External execution authority is literally false.
5. Insert immutable grant, immutable single-use consumption, budget reservation, journal event/state
   and HMAC audit within the same PostgreSQL transaction. Unique constraints plus account locking
   prevent duplicate consumption and over-reservation. Failure rolls everything back.
6. Before each actual simulated fill, verify the original allocation/signature and freshly assess the
   actual price/partial volume and current material inputs. Issue and consume a fresh grant. The original
   short-lived submission grant cannot be replayed; its durable reservation remains an allocation until
   verified release. The fill cannot exceed the proportional original risk allocation.
7. Reconciliation/cancel/close updates only verified exposure. UNKNOWN remains reserved. Duplicate keys
   return the original receipt with current state; conflicting payloads refuse. STOP blocks entries,
   while genuine protective exits and separately privileged simulated FLATTEN remain available.

Current trust limit: API/gateway share a trusted Python host and private authentication key. SQL runtime
cannot rewrite grants/uses/ledger. Host/DB administrator plus secret compromise can subvert local trust;
there is no external audit anchor, separate risk signing identity or broker-capable executor. Future
execution requires separately deployed capability checks, key rotation/revocation, expiry and exact
immutable strategy/account/broker/risk/program/symbol bindings, owner MFA and two acknowledgements.
An environment variable, successful what-if or valid SIMULATED HMAC can never activate that future flow.
