# AI-first Strategy Lab — 2026-10-29

Actual validation: 342 Python / 237 frontend tests, 39+39 focused actual PostgreSQL/Redis/MinIO tests
across restart, contracts/smoke/strict readiness/scans pass. The new registry-context test uses an
explicit synthetic HTTP provider fixture, not real OpenRouter/model acceptance. Exact argv and
exit codes are in commands.json. The earlier full 146+146 checkpoint was not rerun for this change.

Deployment changes only API/Web. Persistent services, named volumes, credentials and worker
containers remain. No paid inference, orders, migration, generated-code execution or golden update.
Browser collection reports 30 cases; actual browser/visual acceptance is NOT RUN. Prior managed
restrictions were respected. No new screenshot or visual-fidelity claim.

The proposal-to-form handoff is temporary, owner-bound and retention-limited; it is not an immutable
AI-origin association on a ResearchRun. Model suggestions never set financial facts or submit tests.
See [the report](../../../STRATEGY_LAB_AI_WORKFLOW_REPORT.md) for scope, limits and local commands.
