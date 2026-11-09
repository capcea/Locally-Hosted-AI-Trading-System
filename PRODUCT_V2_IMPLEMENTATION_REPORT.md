# Product V2 implementation — three-destination workspace

Date: 2026-10-29. Owner requested implementation of the product reset, including removal of ordinary
MFA-code challenges. This is an implementation checkpoint, not live-trading or visual acceptance.
Historical phase reports remain unchanged as evidence of their original checkpoints.

## Implemented product

### Trading Dashboard — `/`

The native authenticated dashboard replaces the previous public iframe/technical Home. It offers
an owner-scoped account chooser, four canonical simulation statistics (realized PnL, unrealized PnL,
equity, positions), actual research/AI job activity, selected strategy and account safety. Financial
values require verified ledger/data and a monitor observation no older than 30 seconds; absent/stale
values are not converted to zero. No cross-account/currency aggregation or invented AI narration.

Account/strategy selection is saved as append-only revisions. The start action explicitly runs a
**finite historical simulation**, using the pinned experiment through the existing Phase5 submission,
risk and quota gates. Ambiguous retries retain the same idempotency key. There is no continuous broker
trader. The UI states this before the action; no disabled pretend-live control is substituted.

### Strategy Lab — `/strategy-lab`

Three steps: develop an idea with the configured model, test/compare on admitted historical data,
review evidence-qualified candidates in the library. Existing AI Center, eight reviewed baselines,
five-step wizard, costs/advanced settings, experiment activity/results/replay, comparison, campaign
lineage, import and final-holdout controls remain reachable. An explanatory advanced section states
that a connected model is not demonstrated to be a trading-specialized trained model.

`/strategy-lab/biblioteca` reads actual persisted campaign evidence, not a hand-curated success list.
A selectable research candidate requires an AI_GATEWAY campaign, completed critique/lifecycle,
canonical successful VALIDATION result with matching digest, admitted accessible datasets, no final
holdout release, and conservative server re-evaluation. Synthetic claims, incomplete evidence and
unfinished critiques are refused. The existing evaluation algorithm is reused unchanged: positive
profit alone does not qualify. Selection is source-account-specific and **not** paper/live approval.

No real eligible historical/model campaign currently exists in the local installation. Positive
real-candidate acceptance, including actual selection/start from that candidate, is **NOT VERIFIED**.
Negative integrity/eligibility tests use deliberately adversarial test records and are not described
as real model results. This conservative library is narrower than a future deployable strategy
catalog: it provides research eligibility only.

### Settings — `/setari`

A five-step setup guide links accounts, AI/model/standing authorization, historical data, risk and
Strategy Lab. Existing groups retain providers, symbols, read-only broker observations, manual
simulator/journal, descriptive risk metadata, actual policies/profiles, identity/roles, audit and
technical diagnostics. No important function is removed to achieve three primary destinations.

Primary navigation is exactly Trading Dashboard / Strategy Lab / Settings. Existing `/testeaza/*`,
`/rezultate/*`, `/conturi/*` and settings routes remain; new `/strategy-lab/{idei,testeaza,rezultate,compara,date}` aliases map to the corresponding existing finite route
allowlist. Account/safety routes highlight Settings; old results highlight Strategy Lab. Back/Forward,
deep-link guards and context ownership fences are preserved in source and native route tests.

## Password/session authentication

- Default server authentication is PASSWORD. Bootstrap/login produces FULL only after actual valid
  password verification. No fabricated MFA timestamp or authenticator enrollment is created.
- Owner-sensitive operations use the active session policy instead of demanding TOTP. Password
  changes/reauthentication still verify the actual current password and rotate session/CSRF together.
- RBAC, account isolation, origin checks, CSRF, cookie protections, rate limits, expiry, idle timeout,
  revocation and immutable audit remain. Wrong password reauth returns REAUTH_INVALID without
  destroying the valid session. Policy mismatch requires fresh login, not implicit elevation.
- Explicit legacy TOTP mode remains for compatibility/regression tests. It is not the normal product
  flow. Legacy enrollment/recovery endpoints refuse mutations in PASSWORD mode. No owner MFA seed,
  recovery code, password, session expiry or historical audit record is deleted/reset by migration.
- 0011 adds session authentication policy and updates the worker's read-only authorization view.
  Password authority requires both a PASSWORD session and a newly server-stamped PASSWORD request.
  Previously unauthorized queued requests are not revived by this migration. Session/standing consent
  revocation and campaign/expiry checks remain mandatory.0012 adds append-only strategy selections.
- Existing FULL sessions migrate coherently; old partial ENROLLMENT/MFA sessions are never promoted.
  A truly expired or partial legacy session must sign in using the existing password.

Future real-order approval is not introduced or weakened. All existing order/activation endpoints
remain denied independently of normal authentication mode.

## Main changed files

- Product shell/routes: `apps/web/src/App.tsx`, `cockpit/PlatformChrome.tsx`, `cockpit/platform.css`, `navigation/routes.ts`,
  `navigation/sections.ts`, `v1/navigation.ts`; new `product/Workspace.tsx`, `workspace.css`.
- Session policy: `apps/api/config.py`, `identity/{dependencies,routes,schemas}.py`,
  `packages/persistence/models.py`, `migrations/versions/0011_password_sessions.py`.
- Product persistence/API: new `apps/api/workspace/routes.py`, `packages/research/selections.py`,
  `migrations/versions/0012_workspace_selections.py`; API registration, readiness and restricted grants.
- Auth-aware frontend, risk/research/AI explanatory copy and session error handling. Existing sensitive
  route callsites use the policy-neutral dependency; financial engines and provider adapters unchanged.
- New password auth/AI/workspace integration tests, four product frontend tests, product desktop/mobile
  E2E scenario. Historical TOTP tests explicitly select their legacy policy. Existing browser tests
  retain functional/safety assertions and adapt navigation to the new product. The old decorative Home
  geometry assertions are replaced by four scoped statistics, account selection, real activity and
  disabled-without-evidence simulation checks. No assertion is replaced with a mocked success.
- Existing campaign integration assertion gained sanitized state diagnostics after a real failure;
  its three worker-transition assertions and evidence requirements remain unchanged.
- OpenAPI/generated TypeScript contracts, README, product direction/spec/status and setup runbooks.

A pre-edit SHA256 inventory and archive preserve 1448 existing source/evidence files in ignored
`.cache/product-v2/`. No original inventory file was removed, no Git reset/rebase/clean/commit/push
was performed, and unrelated OpenRouter/standing-authorization work is retained.

## Actual validation

Exact argument arrays, exit codes and sanitized output are recorded under
`docs/product-v2-evidence/2026-10-29/` and ignored `.cache/product-v2/`.

- `make check`: final exit 0, 336 native Python tests and 226 frontend tests; lint, formatting, mypy,
  TypeScript and production build pass. Existing bundle-size and httpx deprecation warnings remain.
- `.venv/bin/python -m scripts.integration_services --auth-only`: final exit 0, 35 tests before and 35
  after actual PostgreSQL/Redis/MinIO stop/start. Includes password login/rotation/CSRF, retained
  enrollment, restricted AI-worker fixture transport and request-policy authority, and new workspace
  refusal/immutability cases. No paid provider inference.
- `.venv/bin/python -m scripts.integration_services --campaigns-only`: exit 0, 14+14 tests after a
  complete-suite failure. Genuine Phase5/campaign workers, PostgreSQL, Redis and MinIO are used.
- First `make integration-services`: exit 2. 141 passed before restart; 140 passed / 1 failed after
  restart in `test_two_real_bounded_training_iterations_retain_feedback_and_never_promote` at
  `assert step(market)`. The focused rerun passes; its original failure lacks enough state to prove
  the cause. State diagnostics were added, not sleeps/timeouts/looser assertions. Do not retrospectively
  relabel this failed attempt as a pass or assert an unproven root cause.
- Final `make integration-services`: exit **0**, **143 before + 143 after** actual service restart.
  Both complete stages passed; the earlier failure remains recorded above.
- `make contracts-check`: exit 0, generated contracts match byte-for-byte.
- `.venv/bin/python -m pytest -m infrastructure -q`: exit 0, 1 passed / 479 deselected.
- `make smoke-demo` and `.venv/bin/python -m scripts.smoke_demo --require-ready`: both exit 0.
  The three integration constituents were executed separately; the `make integration` wrapper was
  not rerun in addition to them.
- `make repository-check`: exit 0.
- `make secret-scan`: exit 0, no leaks in 1483 Git-selected files (ignored runtime state excluded).
- Playwright `npm --prefix apps/web run test:e2e -- --list`: exit 0, 30 cases collected (15 desktop,
  15 mobile), including the new product scenario. Collection is not browser execution.

Early validation also caught/fixed an incorrect password error category and old navigation/copy
expectations. Formatting-only failures were corrected. No financial/risk assertion was removed.

## Local rollout and preserved data

Initial rollout built `api web migrate`; ran an isolated one-off Alembic `upgrade head` using the existing migration
configuration, without credential/role/storage provisioning; recreated only API/Web with `--no-deps`.
All three initial rollout commands exit 0. Schema is 0012_workspace_selections. `/health/ready` and `/auth/status`
return 200 with PASSWORD policy; `/safety` confirms SIMULATED, DENY_ALL and generated code disabled.
All four principal UI routes return the actual SPA HTML with HTTP 200; this is **not rendered proof**.

The initial rollout changed only API/Web. A final build/recreation also restored the already-stopped
market/research workers after verifying both queues were empty; Web received the final mobile-nav
and heading correction. Both workers now have actual Docker health confirmation. The previous market
worker logs contained a name-resolution failure; the research worker had OperationalError. No broader
root cause is claimed from those old logs. No queued task was dispatched by this recovery.

Across the complete rollout, container IDs changed only for API, Web, market-worker and research-worker.
Named PostgreSQL/Redis/MinIO volumes and every other container ID remain unchanged. Final served HTML
matches the native production build byte-for-byte; this still does not establish rendered fidelity. Before/after database counts match (one user/enrolled record, ten recovery
codes, one AI connection, zero accounts/datasets/research runs). Server-side fingerprints verify
password/enrollment and recovery contents remained unchanged. No new inference request or broker
connection was made. The AI worker was already healthy at this turn's current inspection; this
supersedes the older product-rethink checkpoint that recorded it stopped. No AI worker restart.

## Remaining acceptance and actual limitations

- Browser execution: **NOT RUN / prior managed restriction respected**. No CLI/CDP/alternate-origin
  workaround or sensitive screenshot/trace capture. No visual/mobile/keyboard acceptance claim.
- Existing approved Home screenshot goldens are intentionally retained, now stale for Product V2.
  They require fresh non-secret candidates and explicit owner review; no auto-update or tolerance
  change. Full browser visual acceptance is therefore outstanding even when browser access returns.
- Real historical data, actual sufficient-sample candidate qualification and the positive selected
  candidate simulation path remain unverified. Synthetic HTTP fixtures are not real model evidence.
- Continuous broker trader, paper/live execution, arbitrary generated-code execution and training/
  fine-tuning/evaluating a trading-specialized model remain **NOT IMPLEMENTED**. No profitable-trader
  claim, background agent activity or invented model specialization.
- Market/research workers were initially stopped and now both report healthy after empty-queue
  recovery. Future imports/backtests still require valid setup/data; no owner historical run was
  manufactured to demonstrate activity. HTTP API readiness never implies verified model ability.

## Owner-local acceptance

Reload `http://127.0.0.1:5173/`, sign in with the existing username/password if required, and verify
three primary destinations. No MFA enrollment reset or setup token is needed for the existing owner.

```sh
E2E_ONLY_SCENARIO=product make browser-integration
E2E_ONLY_SCENARIO=redesign make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

The first command exercises actual disposable PASSWORD services. Historical scenarios explicitly
retain TOTP compatibility to preserve those regressions. The final command preserves the visual
review gate and will require approval of genuine new dashboard candidates before visual acceptance.
Do not update accepted goldens automatically. No new phase or real trading is activated.
