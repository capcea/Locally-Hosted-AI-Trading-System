# Rules and limitations

Phase 1 provides local authenticated administration with persistent accounts, policies, risk settings
and audit. It cannot trade. LIVE_TRADING_ENABLED=false, EXECUTOR_CAPABILITY=DENY_ALL and generated
code execution remain enforced in code. Do not expose this development stack publicly.

USER_ENTERED means an actual database record entered by a user; it does not mean a real broker balance
or permission. SYNTHETIC_TEST_FIXTURE identifies test records. The public reference account remains a
configuration example. No feed, historical dataset, backtest, AI job, paper fill or P&L is implemented.
Strategy/experiment/approval records are metadata; there is no runner or promotion authority.

FTMO, FundedNext and The5ers are catalog names only. Policy verification records the owner's explicit
source review, scope, dates and digest. It cannot verify contract terms automatically. Current firm
permissions have not been imported, asserted or tested. Expired/unverified/changed scope fails closed,
and every policy-eligibility result explicitly refuses trading authorization.

Financial inputs use decimal strings. Risk settings are not active sizing or exposure controls.
Currency conversion, loss/reset semantics, market metadata, calendars and independent enforcement
must be implemented and tested before any order-capable flow. There is no kill/flatten function.

Authentication and durable audit have local acceptance tests. They do not establish public-deployment
security: Redis/service identities, TLS, secrets management, backups/restores, load/fault defenses and
external audit anchoring remain gaps. All records are partitioned by owner_id; an OWNER role does not
grant a shared view of other users' domain records. There is no sharing/delegation workflow.

English translations, actual broker adapters, hostile-code sandbox, AI orchestration, notifications
and the rest of the master specification remain later phases. Read the completion report for exact
test evidence and any outstanding acceptance gates. Do not start Phase 2 automatically.
