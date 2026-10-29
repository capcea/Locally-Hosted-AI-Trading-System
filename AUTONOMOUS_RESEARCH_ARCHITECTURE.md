# Phase 7A research orchestration architecture

2026-10-28. Scope: persistent, bounded research coordination; SIMULATED / DENY_ALL.
This is a foundation, not autonomous trading or verified self-improvement.

## Reuse and authority

`packages/campaigns` coordinates existing Phase5 experiments and Phase6 requests. It contains no
backtesting engine, inference transport, broker adapter or generated-code runner. The API exposes
`/api/v1/campaigns`; the Romanian UI is under **Testează → Campanii de cercetare**,
`/testeaza/campanii[/campaign-id]`. Five primary navigation destinations remain unchanged.

Phase5 and Phase6 submissions require a real OWNER session with recent MFA. The campaign worker
cannot manufacture that identity. Every backtest requires owner review of its exact immutable plan
ID and digest. Each Research/Critic request also requires an authenticated owner handoff and the
existing processing/retention consent. Expired MFA requires authentication again. Automatic planning,
monitoring, evaluation and fixture feedback continue between these handoffs. No unattended submission
capability or delegated session is introduced.

## Persistence and execution

Alembic `0008_research_campaigns` adds four tables: immutable campaign specifications,
mutable fenced runtime, immutable hash-chained lineage, and immutable campaign/plan/experiment links.
Owner-scoped foreign keys and database update/delete triggers protect immutable records.
`provision_runtime` revokes destructive table privileges. Existing Redis queues, ResearchJob,
Phase5 workers and hash-verified MinIO results remain authoritative. PostgreSQL is the durable
campaign queue; it does not introduce an additional Redis job type or second queue truth.

The optional Compose `campaigns` profile runs `scripts.campaign_worker` on the private control
network with read-only filesystem, dropped capabilities, no published ports and bounded resources.
It is a trusted metadata service with the existing trusted research runtime role. It is **not** an
isolation boundary for hostile code. It must never execute model text or receive broker credentials.
The separate Phase6 AI worker retains its restricted SQL/Redis/network boundaries.

## Finite authorization

A campaign pins an existing valid Phase5 template: owned account, admitted immutable datasets,
reviewed strategy digest, simulator assumptions, risk context, verified policy/profile revisions,
chronology, costs, seed, methodology and software snapshot. Every allowed parameter candidate is
validated against the actual Phase5 contract. The owner supplies a finite domain of at most eight
complete typed parameter sets. The planner selects within it; a model cannot expand it.

Defaults: eight proposals, twelve experiments, two iterations, one active experiment, 1800 seconds,
192MiB artifact ceiling (including lineage and reserved control space), 512KiB lineage. Global active campaigns default two; per-owner one.
The current loop produces one plan per iteration, so the two-iteration ceiling is more restrictive
than twelve experiments. Runtime admission reserves each Phase5 run's worst-case three attempts,
including 48MiB result space and three times its timeout. The campaign deadline is an additional
wall-clock authorization limit, including owner waiting time. No hidden budget extension on resume.

## Integration boundaries

Source/code/policy/dataset/model changes invalidate approved work. The Phase5 worker independently
checks campaign deadline/cancellation even if the coordinator is offline. Migration0008 extends the
existing AI boolean authority view to refuse canceled/expired linked campaigns, without giving AI
workers SELECT access to campaign/account tables. Model availability is verified through the existing
registry; registry presence alone is insufficient. No model means MODEL_UNAVAILABLE, never a fixture
fallback. Final holdout references and releases cannot enter campaign planning or model context.

See [lifecycle](RESEARCH_CAMPAIGN_LIFECYCLE.md), [evaluation](RESEARCH_EVALUATION_POLICY.md),
[security](RESEARCH_SECURITY_BOUNDARIES.md) and [actual verification](PHASE7A_COMPLETION_REPORT.md).
