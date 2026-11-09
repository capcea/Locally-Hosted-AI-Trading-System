# Standing AI research authorization — 2026-10-29

## Implementation

Standing consent is an explicit OWNER action with recent MFA, valid session and CSRF. PostgreSQL
stores append-only policy revisions and revocations in `ai_standing_authorizations`. Consent has
no time expiry; replacement/revocation invalidates the previous revision, including queued work.
Existing cloud authorization and encrypted credentials are preserved and are not automatically
converted into standing consent. No authorization has been activated for the real owner by this
implementation.

The reviewed scope contains connection IDs, provider, exact destination and endpoint digest,
immutable connection-policy digest, current OpenRouter authorization ID, roles, data categories,
operations, and per-request/daily/monthly USD limits. Changed cloud authorization, destination,
disabled connections or an out-of-scope role/category/operation fail closed. A verified model is
still required. Private providers remain supported; public cloud retains its separate opt-in,
exact egress destination, upstream/ZDR policy, encrypted keys and no automatic fallback.

AI Center submits the standing authorization ID rather than per-request rights, remote-processing
or cost acknowledgements. There is no localStorage consent or injected true flag. The backend
resolves and validates the owner-scoped policy before allowing processing or reserving funds.
Legacy explicit-consent inference clients remain compatible while no standing policy has ever
been configured. After activation or revocation, inference requires an active standing ID; legacy
flags cannot bypass it. Separately MFA-approved technical probes remain compatible, but share any
active standing financial caps.
Technical model probes/catalog reads can also use standing consent when explicitly included in
its operation/role/connection scope. Verification remains an explicit action and is never invented.

Financial authorization is bounded: maximum 0.10 USD/request, 5 USD/day, 150 USD/month in this
release, additionally restricted by the existing cloud policy and global 50 USD/day safety cap.
All calculations use Decimal and conservative existing token reservations. One PostgreSQL
transaction advisory lock covers both legacy and standing reservations, concurrent submissions,
owner/day/month totals and request insertion. Reauthorization never resets accumulated spend.
Idempotent retries reuse the original request/reservation. Failed/uncertain calls keep their
reservation; these totals are **not provider billing**. Day/month resets use UTC calendar bounds.
A reservation is checked again at submission; displayed availability is only an observation.

The readiness read separates gateway configuration, model verification, standing policy, cloud
budget, request quotas and real Redis heartbeat. The client polls, fences obsolete responses and
expires positive observations, including the actual heartbeat deadline. A status HTTP200 alone
never establishes readiness. Disabled submission gives an allowlisted Romanian reason.

## Security and 24/7 meaning

Standing permission is continuous; sessions, models, datasets and dependencies are not permanently
trusted. New interactive submissions still require a valid full OWNER login and CSRF. Login expiry
or revocation still stops session-bound work. The worker's boolean authorization view retains
active OWNER/session validation and campaign stop/deadline checks; only the per-job five-minute
MFA requirement is replaced when the exact standing revision is active. MFA freshness itself is
unchanged for activation, replacement, revocation, keys, connections and other sensitive actions.
Per-job processing/retention deadlines and model-verification expiry are unchanged.

The inference worker gains **no SELECT on identity tables and no write permission on standing
policies**. Generated output cannot authorize new work. Revocation is checked at claim, heartbeat
and final publication. A running cancellation/revocation cannot guarantee the upstream provider
has ceased processing or incurred no cost; no automatic retry of an ambiguous cloud call is added.

Campaign gateway handoffs accept the same standing ID and use the same inference checks/budget.
Existing campaign approval, scoped datasets, quotas, final-holdout protection and recent-MFA
handoff gates remain. No unattended scheduler/session impersonation or trading authority is added.
The standing policy enables repeated permitted inference; it does not itself launch a 24/7 agent.

SIMULATED/DENY_ALL, risk calculations, broker/executor denial, immutable results, protected holdouts,
RBAC/owner isolation, source validation and generated-code execution prohibition remain intact.
No provider request, paid model test, credential change, session reset or MFA reenrollment was
performed by the agent.

## Source changes

- `packages/ai/standing_contracts.py`, `standing.py`, `models.py`: bounded typed policy,
  pinned scopes, append-only authorization records and owner-scoped resolution.
- `packages/ai/contracts.py`, `cloud.py`: optional standing request/action IDs, explicit legacy
  validation, shared conservative reservation totals and atomic monthly limits.
- `apps/api/ai/standing_routes.py`, `routes.py`, `apps/api/main.py`: activation/read/revocation,
  readiness, truthful heartbeat expiry, shared quotas, server-authorized submission/expiry.
- `packages/campaigns/contracts.py`, `apps/api/campaigns/routes.py`: standing ID handoff while
  retaining all campaign-specific authorization and scheduling requirements.
- `migrations/versions/0010_ai_standing.py`, `scripts/provision_runtime.py`, `apps/api/health.py`:
  additive table/view migration, least-privilege API grants and required schema revision.
- `apps/web/src/ai/StandingAuthorization.tsx`, `readiness.ts`, `useInferenceReadiness.ts`:
  one-time settings activation/revocation, exact scope/limits, read confirmation and availability.
- `apps/web/src/ai/AIChat.tsx`, `AICenter.tsx`, `ModelProbe.tsx`, `api.ts`, `copy.ts`: remove
  repeated composer consent, use standing ID, preserve model setup and legacy scoped probes,
  report actionable Romanian errors and conservative budget usage without changing V1 styling.
- `docs/openapi.json`, `apps/web/src/generated/api.ts`: regenerated API contracts.
- `tests/test_ai_standing.py`, `tests/test_ai_standing_integration.py`,
  `apps/web/src/ai/readiness.test.tsx`: validation, real disposable persistence/isolation,
  stale MFA, worker restart, revocation, holdout, budgets/concurrency and UI regression coverage.
- `scripts/integration_services.py`, `apps/web/e2e/phase6.spec.ts`: include standing service tests;
  retain measured private setup, Research/Critic, cancellation and denial assertions, replace
  obsolete consent clicks with stronger activation/persistence/no-consent-payload/revocation checks.

## Database migration

`0010_ai_standing` follows `0009_openrouter`. It adds one empty table with owner foreign key,
unique owner/revision constraints and immutable update/delete/truncate triggers. It replaces the
existing boolean `ai_request_authority` view while retaining session/owner/campaign refusal paths.
It adds only SELECT/INSERT on the new table to an existing API role, without rotating credentials.
No existing row is rewritten, adopted as consent, deleted or reset; no broker/financial schema
changes. Migration execution and final native results are recorded in the evidence package.

## Verification evidence

Command records and sanitized deployment/preservation evidence are under
`docs/standing-ai-evidence/2026-10-29/`. Full local command logs are in `.cache/standing-ai/`.
Actual commands and results:

- `make check`: exit **0**, 336 Python tests and 222 frontend tests; Ruff/format, ESLint/Prettier,
  mypy, TypeScript and production build pass. Nonfatal existing bundle-size warning remains.
- `make integration-services`: exit **0**, **134 before + 134 after** actual service restart at the
  full regression checkpoint. Later standing-specific refinements were rechecked by the focused
  suite. The subsequently added explicit PostgreSQL standing-row persistence case was covered
  by the final focused run, not claimed part of that earlier full count.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`: final exit **0**,
  **25 before + 25 after** actual PostgreSQL/Redis/MinIO restart. This includes real standing-row
  preservation across the two harness stages, API/worker restart, stale MFA, session revocation,
  owner/CSRF/scope refusal, holdout protection, concurrent budgets, monthly totals, legacy-budget
  refusal, explicit cloud probe/Research/Critic transport and revoked-running-output refusal.
- `make contracts-check`: exit **0**, regenerated contracts match.
- `make smoke-demo`: exit **0**, deployed API/execution denial smoke passes, readiness **200**.
- `npm --prefix apps/web run test:e2e -- --list`: exit **0**, **28 cases collected**; no execution.
- Final `npm --prefix apps/web run test`, `npm --prefix apps/web run lint` and
  `npm --prefix apps/web run build`: each exit **0**, including222 frontend tests and final accessible field labels.
- `make secret-scan`: exit **0**, no leaks.
- `make repository-check`: exit **0**, sensitive runtime files excluded.
- `git diff --check`: exit **0**.

Intermediate defects were corrected without weakening checks: the first focused service run
returned exit1 (21 pass/1 fail) because the new test queried the audit column `action` instead of
`event_type`; the query was fixed. Native iterations caught an overlong comment and test typing
errors (dict type arguments and reused connection/session variable), all corrected. Final results
above supersede these failed iterations; no failing assertion was removed.

Browser acceptance remains **BLOCKED** by the previously recorded managed browser restriction.
No CLI/CDP/alternate-origin workaround was attempted. Playwright collection is not execution;
source/static markup tests do not establish rendered or accessibility acceptance. Existing visual
snapshots were not rewritten. Provider HTTP in integration tests is explicitly synthetic; no real
OpenRouter inference is claimed by these tests.

## Enable in the owner's application

1. Open **Setări → Modele AI → Autorizări permanente** after the documented additive migration
   and local API/Web update. An existing OpenRouter authorization/key does not activate this grant.
2. Expand **Activează autorizarea permanentă**. Select the approved connection(s), eligible data
   categories, roles and operations; review exact destination/provider and limits. Multi-select
   permits more than one reviewed connection. Default data categories are documentation/strategies.
3. Configure per-request/day/month caps in USD. Existing stricter OpenRouter caps still apply.
4. Click **Activează autorizarea permanentă cu MFA**. If step-up is required, complete it and
   explicitly resubmit the reviewed activation. This does not make a paid request.
5. Check the active revision and reload to confirm persistence. AI Center then needs only a valid
   question and ready, in-scope infrastructure. No repeated rights/remote/cost checkboxes remain.
6. **Revocă autorizarea permanentă** stops future authorization and invalidates queued/running
   work on its next authorization check. Inspect uncertain provider billing separately.

Owner-local real-service browser verification, without visual snapshot rewriting:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

These commands use disposable synthetic provider fixtures, not the owner's OpenRouter account.


## Local rollout and remaining operational gate

Local development schema is now **0010_ai_standing**. Only **API and Web** were recreated; all
other running container IDs and named volume mounts are unchanged. Before/after counts of existing
users, cloud policies, connections, credentials, models, requests, risk profiles and research runs
match. This is row-count/deployment evidence, not a claim of bytewise database comparison.
No persistent volumes were reset. Anonymous access to the new standing read returns401. The new
Web asset contains the standing-authorization interface and ID-based submission path; HTTP asset
inspection is not rendered browser acceptance.

The pre-existing `ai-worker` container is **EXITED (1)**. Sanitized logs identify PostgreSQL
`OperationalError`; raw logs/secrets were not copied into evidence. Market/research workers were
also already exited. They were not restarted here, and no inference-availability claim is made.
The user will see a missing-heartbeat reason until the AI worker is restored. Models must also
remain verified and all other configured limits/prerequisites must pass.

Only after reviewing the pending queue and deciding to resume previously authorized work, the
owner can restore the existing AI worker without touching dependencies or volumes:

```sh
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up -d --no-build --no-deps ai-worker
```

Starting a worker can dispatch existing approved paid jobs; the agent deliberately did not do so.
This report does not assert that the old connection error has been resolved by a restart.

The local rollout used a build of `api web migrate`, an isolated one-off Alembic `upgrade head`
using the migration service's existing configuration, followed by
`up -d --no-build --no-deps --wait --wait-timeout 90 api web`. Exact argument arrays, exit codes,
counts and safe deployment observations are in the evidence manifest. No provisioning script
was used to rotate identities, keys or storage credentials.
