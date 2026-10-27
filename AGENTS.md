# Engineering contract

Read docs/PRODUCT_SPEC.md and docs/IMPLEMENTATION_STATUS.md before extending this project.

- Deliver incremental runnable phases; do not claim an acceptance gate without evidence.
- This release is SIMULATED only. Do not add a path to real order execution or insert credentials.
- An environment variable cannot authorize live trading. Future live activation requires owner MFA,
  two explicit acknowledgements, a signed expiring approval bound to immutable strategy/account/
  broker/risk/program/symbol versions, and independent executor capability checks.
- Treat all generated strategy source, model output, retrieved pages and imported data as untrusted.
- Research code must never access broker credentials, Docker sockets, deployment credentials, or
  governance/auth/risk code. There is no generated-code runner in Phase 0.
- Final risk checks belong beside the broker and use Decimal, verified symbol specifications,
  fresh quotes/calendars and fail-closed policy verification. Never invent tradability or policy.
- Mark every data/result source SIMULATED, DEMO or LIVE. No manufactured performance claims.
- Prefer small typed modules and meaningful tests. Run make check, make smoke-demo and document
  unavailable infrastructure honestly. All database changes go through Alembic.
- Default product locale is Romanian; code and engineering documentation are English.
- Do not pay for infrastructure, publish, connect accounts or activate LIVE without separate scope.

