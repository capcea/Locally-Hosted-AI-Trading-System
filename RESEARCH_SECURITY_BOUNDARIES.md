# Phase 7A security boundaries

2026-10-28. SIMULATED / DENY_ALL remains mandatory.

## Trust and ownership

Campaigns are owner/account scoped with authenticated reads and original OWNER/recent-MFA/CSRF
mutations. Viewer/operator identity grants no owner authority. Typed extra-forbid contracts reject
arbitrary source, unsupported versions, unknown parameters, coercion of integer/boolean parameters,
unauthorized datasets/accounts, unconstrained budgets and protected holdout references.
A proposal is inert input: no shell, SQL, filesystem, Docker, broker tools or generated-code runner.

The campaign metadata worker is trusted control-plane code, using the existing research application
SQL role and bounded artifact store. It can inspect approved governance metadata; it is **not** a
sandbox for untrusted strategies. The Phase6 inference worker remains separate and cannot SELECT
campaigns, lineage, account or risk tables. It receives only owner-approved restricted contexts.
Its existing boolean authorization view additionally rejects linked canceled/expired campaigns.
No broker credentials, deployment secrets or owner session tokens are provisioned to the campaign
worker. Existing encrypted audit-key configuration is control-plane signing material, not authority
for trading. No new credential is introduced in the frontend.

## Execution and revocation

Only an actual owner session can call original Phase5/6 submission paths. Plan review pins ID/hash;
campaign approval alone cannot submit unattended experiments. Existing risk/policy/symbol/context
validation remains final at Phase5 execution. An additive near-worker campaign guard enforces
cancellation/deadline without depending on metadata coordinator availability.

Policy/profile/account/software changes, dataset sealing/revocation, model route/verification changes
and expired campaign authorization stop further work. An uncertain mutation/cancellation remains
UNKNOWN until reconciled. The system does not optimistically clear financial reservations, grant
prop eligibility or reinterpret descriptive records as enforced policy.

## Durable evidence and quotas

Immutable specifications, run links and hash-chained lineage have database update/delete refusal.
Atomic runtime locks, global admission locks, worker slots, token leases and deterministic Phase5
keys prevent duplicate submissions. Concurrent owner requests cannot spend the same plan twice.
Result reservations include existing three-attempt worst cases; original per-run row/trial/fold/time
limits remain stricter where applicable. Metadata storage is bounded with a small reserved cancellation/terminal-state
allowance inside the total artifact ceiling; ordinary pause/control events cannot consume it.
Repeated pause/cancel requests are idempotent, and unresolved recovery claims do not reset retry
counts, so persistent storage faults require review instead of repeatedly retrying until expiry. There is no arbitrary query or upload endpoint.

## Explicitly unavailable

No autonomous source modification/deployment, expanded risk policy, model tools, automatic holdout
release, paper/demo/live promotion or broker orders. No internet browsing capability is added to
models. Prompt injection remains inert schema-validated text. Existing Phase6 egress/SQL/Redis
isolation is retained; real model verification remains a separate unavailable acceptance gate.
Integration cleanup targets unique disposable test projects only; development volumes are retained.
