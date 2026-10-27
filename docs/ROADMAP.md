# Phased roadmap and acceptance gates

Updated 2026-10-27. Phase 4 deterministic SIMULATED risk gateway, account ledger, atomic
reservations, exact versioned policies, independent monitor and Romanian Risk Center are implemented.
Native/portable acceptance passes; managed browser execution remains separately BLOCKED. Owner-reported
Phase 3 local acceptance is OWNER_REPORTED_PASS, not agent-executed evidence. External MT5/cTrader
connectivity remains unverified. See [../PHASE4_COMPLETION_REPORT.md](../PHASE4_COMPLETION_REPORT.md).
No Phase 5 work has started; stop at Phase 4 until its acceptance gaps are resolved.

The original specification remains authoritative. No phase is complete merely because its navigation
item, interface or documentation exists. Phase transitions require working code and evidence.

0. **Foundation:** pinned toolchain and locks; simulation-only startup; Compose Postgres/Redis/MinIO;
   API liveness/readiness; Romanian shell; reversible migration; CI/lint/types/tests; threat model.
   Full Compose startup and health verification are mandatory before closing this checkpoint.
1. **Identity and core contracts:** users, roles, accounts, immutable version identifiers; secure
   password/session handling, CSRF, RBAC and MFA-sensitive flows; append-only audit with tamper tests.
   Native unauthenticated/unauthorized, migration, concurrency, tamper and restart checks pass.
   Romanian management screens use real APIs; browser workflow acceptance is still required.
   Metadata approvals never grant execution capability.
2. **Data and time correctness — implemented/native-tested, acceptance BLOCKED:** immutable
   CSV/Parquet imports, actual ECB reference adapter, PostgreSQL/MinIO manifests, Redis-backed jobs,
   UTC/DST/availability/sequence guards, quality and real-service restart/crash tests. Market Data UI
   source builds; rendered browser acceptance is unverified. No five-year/tick coverage claim.
   MT5/premium/calendar connectivity remains explicitly blocked/unimplemented where unavailable.
3. **Broker simulation and read-only demo adapters — implemented/native-tested, acceptance BLOCKED:**
   exact deterministic fill/lifecycle models, journal/idempotency/UNKNOWN/crash recovery and real-data
   replay; private Windows MT5/cTrader contracts, demo/scope checks, OAuth/private token source and
   local mTLS acceptance. Actual broker reads/Windows deployment remain unverified. Romanian UI uses
   real APIs; desktop/mobile acceptance must pass in an administrator-permitted environment.
4. **Risk and policy — implemented/native-tested, browser acceptance BLOCKED:** Decimal sizing,
   explicit account/day/DST/high-water semantics, exact verified policy versions, consumed HMAC scopes,
   atomic reservations, mandatory simulated gateway, independent monitor and durable STOP/FLATTEN.
   Property/adversarial/native multiprocess/crash/restart tests pass. External orders remain denied;
   the current shared-host/key contract does not certify a future independent broker executor.
5. **Backtesting:** vectorbt screening and independent event-driven simulation with bid/ask, costs,
   lifecycle trace, gap semantics, deterministic replay and independent baselines. Include OOS,
   walk-forward, uncertainty and multiple-testing corrections; never fabricate history.
6. **Model gateway and research graph:** private authenticated Ollama, verified exact model digests,
   schema validation, bounded tools, cost quotas and isolated code artifacts. Prove generated code
   cannot read secrets, contact executor services or merge governance changes.
7. **Autonomous research and ML:** scheduled hypotheses, baseline comparisons, leakage checks,
   sandbox tests, reproducible experiments and independent statistical/risk critique. Demonstrate a
   clearly labeled synthetic sample pipeline and reject insufficient/overfit evidence.
8. **Paper and lifecycle:** paper quotes/fills with explicit modeling, observation gates, degradation
   pauses and signed immutable promotion requests. Agents cannot approve themselves; any critical
   change invalidates eligibility. Live remains a separate owner decision.
9. **Operations:** authenticated mobile controls, notifications, metrics/tracing and cost budgets,
   backup/restore rehearsal, worker recovery and full browser workflows. Distinguish stopping entries
   from separately authorized flattening.
10. **Cloud/local portability and readiness review:** pinned image/model migration, private networking,
    reproducibility suite and reversible endpoint switch. Test GPU outage while independent demo
    execution remains safe. Deliver readiness report; do not automatically activate real trading.

