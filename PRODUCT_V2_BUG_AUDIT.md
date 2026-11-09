# Product V2 bug audit and repairs

Date: 2026-10-29. Scope: targeted source review, reproductions and repairs of the current
three-destination product, its workspace API, owned reads, research views and authentication/safety
regressions. This is not a claim that every external integration or every possible defect is verified.
No model invocation, broker order, database reset or screenshot-reference update was authorized or used.

## Findings and corrections

### A01 — P1: saved strategy could be reported available for the wrong account

`GET /api/v1/workspace/accounts/{account_id}/strategy` revalidated the candidate but did not compare
its source account with the account being displayed. Creation and simulation already rejected this
mismatch; a stale/inconsistent persisted selection could therefore falsely appear available on read.
This is an incorrect within-owner availability claim, not demonstrated cross-owner account access.

Reproduction: a unit test replaces only the candidate/selection data dependencies and observes
`available=True` for different account IDs. It failed before the fix. The read now returns unavailable,
no candidate, and `WORKSPACE_ACCOUNT_VALIDATION_REQUIRED`. Write/risk gates remain unchanged.

### A02 — P1: candidate evidence was not bound to its recorded campaign experiment and exact plan

A matching result digest and EVALUATION label were checked, but the workspace did not require the
`CampaignExperiment` association or compare the exact immutable PLAN payload with the ResearchRun.
An inconsistent persisted lineage could associate evidence from a different plan/account with a
candidate. No model has direct database-write authority; this is a missing independent integrity
check, not proof that model text could directly place orders.

The reader now requires the scoped campaign/experiment/plan association, typed AI_GATEWAY evidence,
evaluation and critique, matching plan source/parent, identical immutable experiment payload, matching
source account, and the exact artifact reference as well as semantic digest. Missing/unlinked or
mismatched evidence remains unavailable. Existing canonical evaluation and financial calculations
are reused unchanged. Unit tests reject changed plans/accounts; a matching in-sample fixture passes
lineage checks and is still correctly rejected as insufficient validation. No positive real-model
qualification is fabricated.

### A03 — P2: malformed evidence crashed the entire library with HTTP 500

`UUID(evidence.payload["experiment_id"])` could raise KeyError/ValueError rather than a bounded
HTTP refusal. The listing catches HTTPException, so one malformed row could prevent all other
candidates from being listed. Native pre-fix tests reproduced missing/invalid IDs.

Existing versioned schemas now validate evidence/evaluation/critique and plan payloads. Validation
errors become `409 WORKSPACE_LINEAGE_INVALID`; library reads count the unavailable item instead of
claiming success or crashing. Actual disposable PostgreSQL tests insert explicitly adversarial
missing-ID, malformed-ID and unlinked evidence records and require 409 / normal 200 listing. These test
records are not real AI results. Missing PLAN IDs are handled without NULL-primary-key reads.

### A04 — P1: a nullable backend job could crash Dashboard, Lab and history/results views

The backend explicitly returns `job:null` when an experiment has no associated job. Frontend types
and code assumed `job.state` always existed. A source-based SSR reproduction failed with TypeError.

Affected product cards, shared history filters/statistics, StrategyLab history/selection, prior Home
and retained cockpit bridge now preserve UNKNOWN when a job is missing. Missing progress/attempts
are not invented as zero. Missing jobs cannot be selected as SUCCEEDED or cancelled as if active.
Tests cover the Lab/Dashboard render, UNKNOWN filters and results/statistics without fabricated charts.
The underlying missing database job is not manufactured or repaired from frontend assumptions.

### A05 — P2: a stalled read blocked polling and recovery indefinitely

`useOwnedRead` kept `pending=True` until completion but could not cancel a hung fetch. The API client
also discarded cancellation signals. Its pre-fix native test observed no signal reaching fetch.

Owned GET reads now have a 15-second deadline and an account/owner effect-lifetime cancellation
signal. Timeout failures clear current data and retain only explicitly last-known data; cleanup
aborts obsolete requests and removes timers/listeners. Existing generation fences still reject
old-session responses. Native fake-clock tests prove timeout, cleanup, already-cancelled scope and
successful later recovery. These are frontend transport unit tests, not actual browser acceptance.
The helper only issues GET; no mutation is automatically replayed or retried.

### A06 — P2: account strategies after the first 50 were unreachable

The account chooser requested the first 50 library records and exposed no page controls. A link to
the general library did not provide selection of later account candidates. Unavailable records
could also consume that first page. There are now scoped previous/next controls, explicit loading
and empty-page text, and a candidate choice reset on account/page change. Saving requires a candidate
actually present in the current successfully read page, preventing an invisible stale selection
from being submitted after refresh. Account switching is disabled during the mutation. Native tests
cover the later-page controls and first-page scoped request; interactive browser paging remains unrun.

## Security and integrity review

- PASSWORD remains the default ordinary session policy; MFA codes were not reintroduced.
- Owner/account isolation, CSRF, expiry/revocation, role checks, request-policy authority and the
  existing legacy TOTP regression mode are preserved. Authentication code and secrets are unchanged
  by this audit; session behavior is checked through the existing actual-service regressions.
- No financial calculation, strategy engine, dataset storage, final holdout release, risk policy,
  provider egress/credential storage or AI budget implementation was changed.
- Workspace availability is research-only. Starting a bounded simulation still calls the actual
  Phase5 validation/submission path; no external execution capability is added.
- Source checks found no new generated-code runner/eval path. This is not a substitute for a future
  adversarial runtime sandbox assessment. SIMULATED/DENY_ALL remains mandatory.

## Exact validation

Logs and argument-array/exit-code manifests are retained in ignored `.cache/product-v2-audit/`
and sanitized `docs/product-v2-audit-evidence/2026-10-29/`.

- Pre-fix `.venv/bin/python -m pytest tests/test_workspace_validation.py -q`: exit 1, 3 expected
  regression failures (missing ID, invalid ID, incorrect account availability).
- Pre-fix client and product native regressions each exited 1 (signal lost; missing-job render crash).
- Focused workspace unit suite: exit 0, 6 passed.
- Final `make check`: exit 0, 342 Python tests and 233 frontend tests, plus lint, mypy, TypeScript and
  production build. Existing httpx deprecation and bundle-size warnings remain.
- Actual complete `make integration-services`: exit **0**, **146 before + 146 after** actual
  PostgreSQL/Redis/MinIO stop/start, including the three new persisted-lineage refusal cases.
  The first stage included an extra SQLAlchemy NULL-key warning, removed by the final guarded read;
  both stages passed and the second retains only the existing httpx deprecation warning.
- `make contracts-check`: exit **0**, generated contracts match byte-for-byte; no API schema change.
- `make smoke-demo`: exit **0**. Strict `.venv/bin/python -m scripts.smoke_demo --require-ready`
  after local rollout: exit **0**.
- Playwright `npm --prefix apps/web run test:e2e -- --list`: exit **0**, 30 cases collected only.
- Secret scan, repository validation and diff checks: final results recorded in the evidence manifest.

Development-only test typing/nullable-consumer compilation errors were corrected without weakening
assertions, changing timeouts of existing financial tests, or deleting regression cases.

## Runtime and preservation

A pre-edit archive/SHA256 inventory preserves 1488 existing Git-selected files. No reset, clean,
rebase, commit or push. Existing uncommitted OpenRouter/chat/auth changes are retained. Accepted
visual PNG references are not changed. There is no new migration or data-mutating maintenance script.

Local rollout: build and `up -d --no-build --no-deps --wait --wait-timeout 90 api web` both exit 0.
Only API/Web container IDs changed. PostgreSQL/Redis/MinIO and every worker container ID and named
volume mount are unchanged; no migration or data-maintenance command was run on development data.
Public readiness/auth/safety reads return 200, confirm PASSWORD and SIMULATED/DENY_ALL with external
orders/generated-code execution disabled. The served HTML matches the final native production build
byte-for-byte. This is actual deployment/readiness evidence, not rendered browser acceptance.
Current readiness is separate from model verification, statistically valid research and trading authority.

## Remaining gates and non-bug limitations

- Browser execution and visual/mobile/keyboard acceptance are NOT RUN here. The earlier managed
  local-origin restriction is respected; no alternate browser/CDP/CLI bypass or sensitive capture.
- The unchanged old Home screenshot goldens already require Product V2 owner review. No snapshots
  were rewritten and no visual tolerance was relaxed.
- Real historical/model candidate qualification and an actual positive library-to-simulation flow
  were not executed in this audit. Unit dependencies and adversarial negative service fixtures are
  clearly separate from actual AI/model acceptance.
- Trading-model training, continuous broker execution and generated-code execution remain
  NOT IMPLEMENTED, rather than being disguised as passing tests or repaired bugs.

Owner-local browser verification in an authorized environment:

```sh
E2E_ONLY_SCENARIO=product make browser-integration
E2E_ONLY_SCENARIO=redesign make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Use only disposable services/credentials for these commands. The final visual assertion remains a
human-reference acceptance gate; do not automatically update accepted screenshot baselines.
