# Dynamic AI context —4K /16K /32K

2026-10-30. Implementation and native/service validation are complete as described below. Overall
acceptance remains open for rendered browser testing and an explicitly authorized real-provider
verification. No paid provider request, model download, key change, trading activation or data reset
was performed. SIMULATED / DENY_ALL remains active.

## Implemented behavior

The existing UTF-8 capacity accountant is extended by one server allocator:

- AUTO is the default in AI Center, Strategy Lab and campaign Gateway handoffs. It selects the
  smallest configured tier that fits the assembled system/user contents, structured-output schema,
  reserved output and unchanged512 framing reserve. Active tiers are4096,16384,32768.
- RAPID selects4096, STANDARD16384 and COMPLEX32768. Every choice is bounded by the minimum of
  registered and currently verified capacity among all selected models/fallbacks, plus operator
  configuration. A selected tier cannot create authority or enlarge verification.
- Explicit numeric legacy requests retain their numeric behavior, including existing8192 clients.
  Omitted mode and omitted numeric context use AUTO. Omitted mode with an explicitly supplied numeric
  context is the compatibility path. Old-client idempotency fingerprints omit the new null field.
- No instruction, question, schema or protected reference is silently truncated. If no allowed tier
  fits, the request fails422 with numeric-only diagnostics. Diagnostic selected capacity is an actual
  available tier, so a rejected8K-model/5K-request does not falsely report positive usable headroom.
- The encrypted immutable request stores the resolved Generation parameters and allocation evidence.
  The existing worker wire format is retained: context mode is not inserted into worker Generation.
  Final quota, consent, revocation, session, output-schema and monetary reservation gates remain.

These are conservative byte-derived capacity bounds, not a guessed tokenizer, actual billed tokens
or a claim that a provider has passed a full-window stress test. The earlier34-byte Romanian Lab
regression remains valid at4096 with unchanged system/schema/output/framing accounting.

## Preview and interface

`POST /api/v1/ai/requests/preview` reuses the actual owner-authorized context assembler, model snapshot,
standing authorization and allocator. It creates no job, reservation or provider request. It returns
sizes, selected tier, remaining estimated context and exact Decimal financial reservation/cap data.
Actual submission rechecks all facts atomically; a preview is advisory and grants no authority.

The current chat and Strategy Lab have a compact AUTO/4K/16K/32K selector, current verified ceiling,
server-estimated consumption and remaining context. Cloud previews show configured reservation,
request cap and daily/monthly remaining amounts. Missing data stays unknown. Typing is debounced;
obsolete preview requests are aborted and their results cannot replace the current draft.

The advanced legacy composer also submits the selected mode. Its pre-submission advisory display
remains limited; the ordinary AI Center/Strategy Lab use the full server preview. No repetitive
consent checkboxes were added. An accepted frozen request retains its exact key through uncertain
network/5xx outcomes; deterministic422 releases editing and the next submission obtains a new key.

Model versions are visibly distinguished by configured and measured context. A registered32K variant
is not marked verified merely because its4K parent is verified. Existing model/role controls and
private Ollama/OpenAI-compatible providers remain available. No accepted screenshots were rewritten.

## Versioned model increase and provider verification

`POST /api/v1/ai/models/{id}/context-revisions` is an owner/sensitive-session operation. It creates a
new immutable model configuration on the same connection/name, records the parent in immutable audit,
and leaves the original model, verification, requests, credentials and role assignments untouched.
Repeated preparation returns the existing matching version. Decreasing the ceiling is refused.

The new model requires its own probe through the existing isolated worker, using approved provider
metadata and a bounded structured-output request. Existing routing refuses it until fresh
verification exists. After verification the owner explicitly assigns desired roles via the existing
append-only route API. No probe, role switch, policy change or paid call occurs on registration.

The installed model was observed read-only after deployment:

- Configured and recorded verified ceiling4096; proof was unexpired at observation.
- Standing authorization remains active. Request cap0.01USD, daily0.50USD, monthly120USD unchanged.
- Approved pricing ceilings are1USD/million input and4USD/million output.
- A4096/768 inference reserves0.007168USD. A32768/64 verification reserves0.033024USD; a32768/768
  inference reserves0.035840USD. Both larger reservations exceed the current0.01 request cap.

These are **conservative reservations at saved pricing ceilings**, not a quote or actual bill. No
cap was raised. The owner must separately review both the OpenRouter authorization and permanent
request cap before any larger paid verification/inference; daily/monthly caps need not be increased.
Preparing the new version alone is unpaid. The application deliberately retains the working4K model
until that review and fresh verification; it does not claim the installed provider is already32K.

## Bounded limits and migration

Alembic0013_ai_context_capacity expands the model CHECK envelope to131072 without rewriting any
model, proof, role, credential or audit row. Runtime allocation/registration still defaults to at
most32768. Downgrade refuses to discard larger immutable model versions. SQLite migration up/down
and actual PostgreSQL migrations passed. Readiness expects0013 after deployment.

- AI JSON request bodies:64KiB, enforced before parsing for declared-length and chunked bodies.
  This covers the existing4000-character question, bounded reference IDs and configuration JSON.
  Imported/retrieved context is assembled separately server-side; the question limit is unchanged.
- Assembled/encrypted input:64KiB default, configurable only within1KiB–256KiB. The context broker
  and pre-enqueue storage guard retain explicit byte bounds. Storage is encrypted TEXT, with Fernet
  expansion; no unbounded database blob or browser prompt persistence was introduced.
- Output remains bounded independently: Generation64–4096 tokens; provider/worker output defaults
  24000 bytes, configurable only up to32000. Larger context does not enlarge output or role quotas.
- Proxy destination/TLS/DNS/redirect restrictions, timeouts, network isolation and concurrency remain
  unchanged. The CONNECT proxy streams bounded-lived connections; it is not an arbitrary HTTP proxy.

Future128K is structurally supported by contracts, persistence, provider cap logic and the allocator,
but is **not enabled**. It needs explicit `AI_CONTEXT_TIERS`, a sufficient bounded
`AI_MAX_INPUT_BYTES`, a compatible deployed AI worker and a separately registered/freshly verified
model configuration. Operator configuration alone never authorizes unverified capacity. The current
AI worker was intentionally not recreated; its existing32K support is sufficient for this release.

## Files changed

- API: `apps/api/ai/budget.py`, `routes.py`, `standing_routes.py`, new `limits.py`, `apps/api/main.py`
  and schema-readiness revision in `health.py`.
- Campaign handoff: `apps/api/campaigns/routes.py` removes the fixed8K request assumption and calls
  the same allocator through the existing Gateway submission pathway.
- Shared contracts/settings: `packages/ai/contracts.py`, `models.py`, `providers.py`, `settings.py`.
  Provider change is solely the structural context bound; OpenRouter routing/privacy logic is intact.
- UI: new `ContextBudget.tsx`/test, `AIChat.tsx`, `AICenter.tsx`, `ai-chat.css`, `submission-budget.ts`,
  `budget-diagnostics.ts`, `copy.ts`, `management-api.ts` and corresponding registry tests.
- Migration0013, new `scripts/migrate_ai_context.py`, Dockerfile packaging and `compose.ai.yaml`.
- Tests/fixtures: context-budget unit/integration tests, cloud fixture options, campaign cancellation
  setup, `testing/ai_fixture.py`, Phase6 Playwright scenario and its synthetic metadata harness.
- Generated OpenAPI/TypeScript contracts, deployment guidance, implementation-status pointers,
  this report and sanitized evidence. The evidence inventory lists exact source paths and hashes.

Financial engine, authentication policy, Risk Gateway, market data, holdout and execution modules
were not modified. A pre-task archive/hash inventory protects1562 existing workspace files. No reset,
stash, checkout, commit, remote push or accepted golden-reference change was performed.

## Actual tests and failures

- Initial `make check`:exit2;345 passed and1 failed because readiness still expected0012 after the
  new migration. The schema revision was aligned; checks were not weakened. Intermediate formatting
  and import failures were corrected before final acceptance.
- Initial `make integration-services`:exit2;150 passed and1 failed in campaign cancellation setup.
  The existing fixture was verified at8192, while its assembled5039 request cannot use the4K tier
  and cannot authorize16K. The refusal was correct. The fixture now creates and actually probes a
  fresh32K synthetic configuration before campaign approval; all cancellation/isolation assertions
  are preserved. The confusing positive headroom in the refused diagnostic was also corrected.
- Final `make integration-services`:**151+151 passed**, exit0,573.588 seconds, before/after actual
  disposable-service restart. Includes real PostgreSQL/Redis/MinIO and the isolated inference worker.
- Final `make check`:**350 Python and251 frontend tests passed**, exit0. Ruff, mypy, ESLint,
  Prettier, TypeScript and production build pass.152 infrastructure/isolated tests are deselected by
  this command; those are not counted as native executions.
- `.venv/bin/python -m scripts.integration_services --auth-only`:**43+43 passed**. After the complete
  suite, an audit-label correction distinguishes implicit AUTO from an explicit legacy numeric
  request in immutable provenance. Final native checks and another43+43 actual-service run cover
  that final correction. The complete151-case run predates only that metadata-label correction.
- `.venv/bin/python -m scripts.integration_services --campaigns-only`:**14+14 passed**, exit0,
  after the reviewed fixture setup correction.
- `make contracts-check`, `make smoke-demo`,
  `.venv/bin/python -m scripts.smoke_demo --require-ready`:exit0. Actual readiness200 and execution
  refusal confirmed after the API/Web deployment.
- `make secret-scan` and `make repository-check`:exit0. No leaks found;19 sensitive-path
  exclusions validated. Exact scanned-file counts and commands are recorded in the evidence package.
- `npm --prefix apps/web run test:e2e -- --list`:30 desktop/mobile cases collect, exit0.
  This is **not execution**. Prior managed local-origin restrictions remain respected. No browser
  was launched through an alternate CLI/CDP path; no rendered acceptance is claimed.

The browser scenario now covers real server422 recovery, four modes, unpaid version preparation,
fresh synthetic32K verification, unchanged routes until explicit owner assignment, actual selected
Generation tiers and standing-authorization revocation. Native tests cover UTF-8 Romanian text,
large schemas, exact tier boundaries, fallback ceilings, stale verification, JSON/body bounds,
revocation, conservative cloud reservations and monetary refusal.

Private-provider tests use an explicitly synthetic real loopback HTTP server. OpenRouter transport
fixtures do not contact the actual service and are not real-model acceptance. Existing nonblocking
warnings remain: Starlette TestClient/httpx deprecation and a frontend bundle above500kB.

## Deployment, worker alignment and remaining gates

The bounded CHECK migration was applied using a one-shot migration container with a dedicated script
that does not provision/change roles, credentials or storage. API/Web were rebuilt and refreshed;
PostgreSQL, Redis, MinIO, AI worker and other persistent services were not recreated. All named-volume
mappings are preserved; served assets match the native build.

The broad existing backtest software fingerprint includes four AI package files. A read-only check
confirmed the running research worker initially matched pre-task source, so new API experiments
would have been correctly refused after the package changes. That integrity check was not bypassed.
The owner explicitly approved refreshing **research-worker and campaign-worker**. Both work tables
were empty before refresh. Both refreshed workers passed Compose readiness and their complete software file manifests match
current source. Post-update strict readiness/smoke pass; other container IDs and all volume mounts
are unchanged. Exact alignment/health evidence is recorded in the evidence package.
The AI worker remains unchanged; no uncertain work was cancelled or replayed.

Remaining gates:

1. Rendered desktop/mobile browser acceptance under an allowed environment; no screenshot acceptance
   or visual claim is manufactured from source, collection or build results.
2. Owner review of financial request limits and a separately approved real-provider verification.
   Installed4K proof is never reused as32K evidence. Actual Research/Critic32K inference remains gated.
3. Future128K requires operator/model/worker verification; it is not part of current activation.

## Exact owner-local commands

For this version's API/Web and one-time schema migration, with the existing secret files/env intact:

```sh
env BUILDX_CONFIG="$PWD/.cache/buildx" docker compose --env-file .env --env-file .env.ai \
  -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns build api web migrate
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns run --rm --no-deps migrate \
  /app/.venv/bin/python -m scripts.migrate_ai_context
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up -d --no-build --no-deps --wait --wait-timeout 90 api web
```

The owner-approved alignment of the two empty research queues uses:

```sh
env BUILDX_CONFIG="$PWD/.cache/buildx" docker compose --env-file .env --env-file .env.ai \
  -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns build research-worker campaign-worker
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up -d --no-build --no-deps --wait --wait-timeout 90 \
  research-worker campaign-worker
```

Do not interrupt active/uncertain jobs to apply this; retain pinned history and review quiescence.
No `down`, volume removal, key reset, broker connection or real generation is needed for deployment.
Reload the tab after the update. In Settings → Modele AI, prepare a32K version of the configured model,
review caps separately, explicitly verify that version, inspect its measured capacity, then assign
Research/Critic roles. Ordinary requests retain permanent authorization without repeated checkboxes.
Do not perform a paid probe merely because a new row appears.

Owner-local synthetic browser acceptance, without rewriting goldens:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

[Sanitized evidence and exact command results](docs/ai-context32-evidence/2026-10-30/README.md).
