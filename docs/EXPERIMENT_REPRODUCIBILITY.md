# Experiment reproduction

1. Import an entitled source through Phase2 and require VALID quality. Preserve original objects,
   hashes, provider/source, real availability timestamps and observed coverage. Tick completeness and
   five-year coverage remain unknown unless independently established.
2. Configure/verify the exact source account risk policy and profiles with owner recent MFA. Automated
   baselines require explicit automation permission. Supply actual supported contract/margin/FX/calendar
   facts or labeled synthetic assumptions; uncertainty cannot default to authorization.
3. Submit a typed research plan through Strategy Lab or the authenticated API. Pin strategy digest,
   dataset manifest hashes, parameters, chronology, seed, costs, context, quotas and risk approval.
   Stable idempotency keys return the original job; changed payloads with the same key refuse.
4. The worker records fixed source/runtime/package hashes and immutable hypothesis slots. Each trial/
   fold/cost/attempt gets a separate account and clock. Inspect job progress, errors, actual risk decisions,
   orders/fills/fees/funding, exact equity trace and source provenance.
5. Retrieve only a complete immutable result. It pins a MinIO object version and checksum plus a semantic
   digest of financial outputs and software/input identity. Operational account/order/job UUIDs may differ
   on reproduction; equivalent financial results must match the semantic digest. Changed inputs/software
   are distinguishable. Reproduce with a new submission key, never by editing the old manifest.
6. For final evaluation, seal and release a separately reviewed frozen scope once. Prior exposure is not
   certified untouched. Deterministic crash retries retain the same frozen inputs; they cannot tune them.

Run make check, make contracts-check, make integration and make browser-integration for regression proof.
The harness owns only UUID-scoped disposable resources. Never delete development volumes or owner MFA,
relax the gateway or replace failures with placeholder results. Full Phase5 evidence and measured run
counts/durations are in PHASE5_COMPLETION_REPORT.md and docs/phase5-evidence/2026-10-27/README.md.
