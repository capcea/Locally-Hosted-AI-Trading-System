# Phase 7A completion report

2026-10-28. **IMPLEMENTED FOUNDATION; ACCEPTANCE PARTIAL.** SIMULATED / DENY_ALL.
The owner explicitly authorized Phase7A and postponed final V1 visual acceptance. This report does
not overwrite earlier Phase0–6 evidence. No Phase7B, paper/demo/live orders, generated-code runner,
model downloads or paid infrastructure were introduced.

## Delivered

- Strict versioned objective/hypothesis/candidate/plan/evidence/evaluation/critique/feedback/lineage
  contracts. One reviewed strategy version, finite authorized typed domain, pinned account/datasets,
  chronology, simulator, financial/risk context, source, methodology and seed. No arbitrary source.
- Four additive Alembic0008 tables, immutable specifications/links/hash-chained lineage and durable
  runtime budgets, leases, cancellation requests, deadline and atomic counters. Idempotent exact-plan
  owner handoffs reuse the original Phase5 creation transaction; concurrent requests return one run.
- Trusted metadata coordinator, optional hardened Compose profile, global2/per-owner1 campaign
  admission, bounded retries/recovery and original Phase5 per-run quotas. Worst-case three attempts
  reserve time and artifact space. Pausing never implies active child cancellation.
- Actual canonical Phase5 result retrieval from MinIO, conservative evaluation and immutable critique/
  feedback. Deterministic synthetic ticks exercise insufficient-evidence stopping; complete admitted
  synthetic M1 bars exercise two bounded training iterations. No fictional market profitability.
- Actual Gateway Research/Critic handoff/acceptance integration, measured capability checks, finite
  output validation, restricted contexts and explicit MODEL_UNAVAILABLE. No silent fixture fallback.
- Near-Phase5-worker cancellation/deadline refusal even without a coordinator. Linked AI requests
  lose authority through the existing restricted boolean view; AI workers gain no campaign/account
  reads. Explicit cancellation is acknowledged only after real children terminate.
- Romanian **Testează → Campanii de cercetare** guarded routes, owner constraints/consents, exact-plan
  review, actual states, paginated history/lineage, immutable details and links to existing setup,
  experiments, data, safety and AI configuration. Existing five destinations and features remain.

## Intentional automation boundary

Existing Phase5 and Phase6 require a real OWNER session and recent MFA. Campaign approval does not
waive that. The worker plans and monitors; the owner explicitly submits each exact experiment and
each model request, then accepts valid model output. Expired sessions/MFA require normal renewal.
No unattended delegated capability was invented. This is the required owner-reviewed scheduling
handoff, not a claim that a campaign can operate indefinitely without human authorization.

The current loop selects one candidate per iteration, at most two iterations. The broader default
ceilings (8 proposals/12 experiments) never authorize bypassing this tighter planner bound. Frozen
CALIBRATION/VALIDATION permits one candidate/iteration, and previously exposed owner VALIDATION
intervals are refused conservatively. All final holdouts remain inaccessible.

## Changes and preservation

New code: `packages/campaigns/*`, `apps/api/campaigns/*`, migration0008,
`scripts/campaign_worker.py`, `apps/web/src/campaigns/*`, campaign unit/integration/browser tests.
Additive integration: API router/config/readiness, runtime grants, Compose optional profile,
Phase5 approval's campaign authority check, disposable/browser harnesses, frontend routes/navigation,
generated API contract. No risk arithmetic, accounting, strategies, existing backtest math, broker,
authentication/MFA implementation or old browser assertions changed for this phase.

Existing uncommitted work was protected using hashes of1300 existing files and a local archive in
`.cache/phase7a/before.*`. No original file was removed. Existing four visual goldens were preserved.
Only uniquely named disposable test projects were cleaned up. No development service was rebuilt,
restarted, migrated, reset or given broker credentials. The development schema is still0007; the
source expects0008. A healthy old API smoke does not establish deployed Phase7A readiness.

## Actual verification

Exact commands, exit codes and durations are retained in `.cache/phase7a/*.json`; stdout is in the
corresponding `.txt`. These are local evidence, not a claim of committed CI or external acceptance.
Final verified results are recorded below; earlier failures retain their original status.

Early failures are preserved, not hidden:

- `campaign-integration`: exit1,7 passed/2 failed; polling-lease fixture and inadequate tick coverage
  for follow-up. The test scheduler advances only its disposable lease. Real complete M1 bars replace
  the invalid follow-up fixture; the insufficient tick test is retained with its original refusal.
- `campaign-integration-v2`: exit1,8 passed/1 failed; insufficient tick fixture still correctly stopped.
- `campaign-integration-v3`: exit0,9 passed before/9 after restart, before added guard/fault/AI tests.
- `campaign-integration-v4`: exit1,11 passed/1 failed; actual AI_CONTEXT_BUDGET_EXCEEDED. Campaign
  handoff used the4096 default despite a larger verified model. The request now selects at most8192,
  bounded by the approved measured capability. Existing context refusal remains unchanged.
- `campaign-integration-v5`: exit1,11 passed/1 failed; the test expected explicit child cancellation
  before the coordinator propagated it. The authority view already refused inference as revoked.
  The test now runs the real coordinator cancellation step, asserts still-unacknowledged, then checks
  actual AIJob cancellation and final acknowledgment. No refusal/assertion was relaxed.
- `check-final`: exit2, mypy caught optional-approval narrowing and a misplaced ignore after formatting.
  Explicit absence rejection and typed narrowing fix it; no check was removed.
- `campaign-integration-final`: exit1,13 passed/1 failed; the new persistent result-read fault also
  intercepted prerequisite manifest reads. The still-running `integration-services-final` retained
  that test version and exits2 with99 passed/1 failed. The fault now applies only to result artifacts;
  prerequisite manifests still come from actual MinIO. All retry/UNKNOWN/cancellation assertions remain.
- `make integration`: exit2 at its first read-only infrastructure probe (1 failed): development
  PostgreSQL revision0007 differs from required0008. Redis and MinIO are healthy. The Make target
  correctly stops, so its later isolated command and final smoke were not counted as executed there.
  The full isolated target and strict smoke were invoked separately; this is not a full target pass.

A further negative unit test reproduced synthetic market provenance incorrectly receiving
RESEARCH_CANDIDATE when mode was AI_GATEWAY. `synthetic-provenance-red` exits1 before the fix.
The evaluator now independently checks canonical dataset provenance, without changing underlying
financial metrics. Exact literal types reject boolean schema versions and numeric acknowledgments.
Persistent dependency recovery is bounded across recovery transitions; cancellation/terminal evidence
space is reserved inside the total artifact budget and cannot be consumed by ordinary controls.
Real-service cases verify repeated storage failure and cancellation at exhausted ordinary lineage.

`integration-services-final-v2` exits2:100 passed before restart, then90 passed/1 failed/9 setup
errors afterward. MinIO explicitly returned RequestTimeTooSkewed; the resulting actual import
returned503. No clock/skew checks were relaxed. A read-only comparison afterward found host and
Docker VM both2026-10-28T14:20:39Z; a fresh isolated rerun is separately recorded. Development
services were not restarted to address it. This infrastructure failure remains in the ledger even
if the retry passes.

The first delivery secret scan exits2 with3 generic-api-key findings in the evidence checksum JSON.
All three were independently recomputed source-file SHA256 values, not credentials. The manifest is
now conventional `SOURCE_SHA256SUMS.txt` rather than JSON keys containing API filenames beside
hash values. No scanner exclusion, tolerance or detection rule changed. A fresh scan is recorded.

## Browser and external gates

**BLOCKED / NOT EXECUTED**: focused campaign and complete26-case desktop/mobile browser execution.
The prior current-session managed origin refusal explicitly denies localhost browser access and
alternate browser/CLI/CDP/indirect workarounds; see the preserved V1 final visual audit. No workaround,
secret capture or golden rewrite was used. Playwright collection alone is not execution success.
New browser source exercises actual data import, risk setup, reviewed experiment/campaign submission,
canonical evidence, reload and order refusal. It still requires authorized local execution:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=campaigns make browser-integration
E2E_ONLY_SCENARIO=campaigns make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Full browser suite now26 cases (previous24 +2 campaign cases). Existing old-UI visual references may
still require separate explicit owner review for V1; do not rewrite snapshots to satisfy this gate.
No rendered/mobile/manual-accessibility or real-model campaign acceptance is claimed.

**BLOCKED / NOT VALIDATED**: real Research/Critic inference, licensed sufficient historical data,
statistical robustness and scalable backtesting. Synthetic HTTP transport probes validate boundaries,
not actual AI reasoning. No real model is connected/downloaded. No paper/live eligibility exists.

## Foundation acceptance scope

Bounded creation/approval, finite reproducible plans, original risk-approved backtests, persisted
budgets/state, immutable lineage, canonical evaluation and two-iteration synthetic feedback have
real-service coverage. Missing model/data gates, no promotion and unchanged regression boundaries
are explicit. Unattended submission is deliberately unavailable because recent owner MFA is retained.

Campaign lease recovery is tested with expired disposable leases and fresh worker instances; storage
faults exercise rollback/UNKNOWN/recovery and bounded persistent failure. This does not establish an
exhaustive OS-kill campaign-daemon or ambiguous-network-commit chaos certification. Manual outage,
long-running operational and rendered accessibility acceptance remain outstanding. The existing
Phase6 process-kill and isolation regression cases remain in the full native suite.

No new external credential is required for deterministic fixture campaigns. Actual-model acceptance
needs an owner-approved private runtime and verified Research/Critic capabilities under existing
Phase6 controls. Meaningful market acceptance needs permitted historical datasets, source rights and
adequate coverage/chronology. Broker credentials are neither required nor authorized.

## Owner actions and next gate

1. Review source and this foundation's handoff constraints. Preserve the current development data.
2. For actual development installation, use the normal additive migration/runtime provisioning
   workflow (`make migrate`) and rebuild affected API/research services; then enable the optional
   `campaigns` profile worker. Do not run development `down --volumes`. Review Phase6's existing
   restricted worker provisioning if enabling its optional runtime. No real model is required for
   deterministic fixture campaigns. Installation was not performed automatically in this phase.
3. Rerun `make integration` against the upgraded development schema, then the authorized local browser
   commands above without snapshot rewriting. Complete manual UX review separately.
4. When available, review permitted historical data and verify actual models through existing Phase6
   controls before claiming real AI/historical acceptance. A familiar model or policy name is no proof.

Stop at Phase7A. Do not start7B, release holdouts, activate paper/live or relax owner-MFA boundaries.


## Final verified command results

- **PASSED — `make check`, exit0** (`check-final-v4`,26.271s): Ruff/format/ESLint/Prettier,
  mypy169 source files, TypeScript,263 Python tests,152 frontend tests and production build. The
  focused campaign contract suite has20 passing cases. Existing Starlette/httpx deprecation and
  Vite's large-bundle warning remain non-fatal; no warning threshold or check was suppressed.
- **PASSED — `.venv/bin/python -m scripts.integration_services --campaigns-only`, exit0**
  (`campaign-integration-final-v2`,275.870s):14 actual service cases before and14 after restart.
  Covers immutable lineage/canonical evidence, concurrency/idempotency, scope/MFA, holdouts,
  policy revocation, deadlines, finite feedback, storage recovery, restricted AI cancellation,
  repeated failures and exhausted-lineage cancellation. Synthetic fault injection is explicitly
  scoped; PostgreSQL/Redis/MinIO and successful results are real.
- **PASSED — `make integration-services`, exit0** (`integration-services-final-v3`,458.136s):
  all100 existing/new isolated cases before and100 after graceful restart. Real migrations0008,
  loopback binding/TCP checks, object/queue round trips and persistence pass. This final fresh run
  retains S3 signature/time checks; it follows the recorded transient clock-skew failure.
- **PASSED — `make contracts-check`, exit0** (`contracts-check-final`,2.931s), after
  `make contracts` exit0. OpenAPI and generated frontend contract are synchronized.
- **PASSED — `make smoke-demo`, exit0**, and separately
  `.venv/bin/python -m scripts.smoke_demo --require-ready`, exit0: existing deployed API readiness200
  and both execution refusals403. This is the unchanged existing deployment, not a deployed campaign
  endpoint acceptance claim.
- **PASSED — `make secret-scan`, exit0** (`secret-scan-delivery-v2`,2.170s), after converting
  the checksum manifest; scanner rules unchanged. `make repository-check` exit0 and
  `git diff --check` exit0. Python independently verifies all32 source checksum entries.
- **PASSED COLLECTION ONLY — `npm --prefix apps/web run test:e2e -- --list`, exit0:**
  26 cases in11 files. Focused/full browser **NOT EXECUTED / BLOCKED**, not passed.
- **FAILED — `make integration`, exit2:** first development schema-readiness probe fails, as
  explained above. The100+100 isolated pass does not convert this command into a pass.

[Sanitized evidence and all command records](docs/phase7a-evidence/2026-10-28/README.md) retain
intermediate failures, exact exit codes and durations. Final source hashes, original-file preservation
and12 unchanged non-web container identities/images/mounts are included. No original file was
removed; all four browser goldens remain unchanged. An optional host `shasum` invocation encountered
an unsupported locale; independent Python verification passed instead.

**Foundation delivered; full acceptance remains partial.** Development migration/rebuild, authorized
local26-case browser execution, manual review, real model inference and sufficient historical evidence
are outstanding gates. No autonomous unattended execution or trading authority is inferred.
Companion documents: [architecture](AUTONOMOUS_RESEARCH_ARCHITECTURE.md),
[lifecycle](RESEARCH_CAMPAIGN_LIFECYCLE.md), [evaluation](RESEARCH_EVALUATION_POLICY.md),
[security](RESEARCH_SECURITY_BOUNDARIES.md). Stop at Phase7A.


## Packaged campaign-worker startup follow-up — 2026-10-28

The owner-upgraded Compose deployment exposed a packaging defect: the shared control Dockerfile
omitted `scripts/campaign_worker.py`, although its Compose command correctly selected that module.
The missing-module exit1 was reproduced against the built image. The explicit COPY list is repaired
and image builds now exercise the packaged entrypoint's `--help`. Actual no-network/non-root image
smoke and targeted service startup pass; the campaign worker is running/healthy with a fresh
heartbeat and actual schema0009 database read. No other service was recreated; persistent mount
identities are unchanged. See the [startup repair evidence](OPENROUTER_INTEGRATION_REPORT.md#follow-up-campaign-container-startup-repair--2026-10-28)
for exact commands and native verification. This does not establish browser, real model, historical
data or V1 visual acceptance and does not authorize another phase.
