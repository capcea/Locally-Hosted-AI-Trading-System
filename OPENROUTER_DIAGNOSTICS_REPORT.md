# OpenRouter refusal diagnostics

2026-10-29. Diagnostic fix implemented and native-tested; real provider failure cause remains
UNVERIFIED. No live model call or paid verification was submitted by the agent.

## Confirmed observations and limits

The owner reported `AI_PROVIDER_REQUEST_REFUSED` and supplied an OpenRouter Activity screenshot
with zero requests in the selected workspace/time window. This does not establish that the API
was never contacted, that a generation started, that there was no cost, or that the key is valid.
The probe first reads model metadata and only then requests a completion. The old adapter replaced
many different non200 statuses with this generic code and discarded status/stage. The worker kept
only that code. The original HTTP status and response body cannot be reconstructed from the old
application record. No historical error has been rewritten or guessed.

Official API documentation confirms the existing model-metadata route shape:
[GET /models/{author}/{slug}/endpoints](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model).
[OpenRouter errors](https://openrouter.ai/docs/api_reference/errors-and-debugging) have HTTP/error
details; missing Activity data is not a substitute for an observed transport response. No provider
URL, model, price cap, ZDR requirement or approved upstream was changed on speculation.

## Changes

- `packages/ai/diagnostics.py`: whitelist exactly an integer HTTP status100–599 and a constant
  operation enum: MODEL_CATALOG, MODEL_METADATA, COMPLETION or PROVIDER_REQUEST. Reject invalid
  fields and strip every extra field. No raw messages, headers, URLs, prompt data or keys retained.
- `packages/ai/providers.py`: attach these observations to existing ProviderFailure exceptions.
  Existing error codes, retryability, ambiguous-outcome classification, TLS, DNS/proxy boundaries,
  redirect refusal and streaming limits remain unchanged. Error bodies are still not read/stored.
- `packages/ai/worker.py`: retain sanitized facts in the existing durable terminal AIEvent under
  the original worker token/transaction checks. Cancellation clears the diagnostic and retains
  its own acknowledged outcome. Cloud refusal still never retries automatically.
- `apps/api/ai/routes.py`: return only allowlisted facts from the matching terminal event/code in
  the existing metadata object. Original authenticated owner scoping and event reads remain.
  No schema migration, new permission, credential read endpoint or contract shape was introduced.
- `apps/web/src/ai/{ProviderError.tsx,copy.ts,AICenter.tsx}`: show observed HTTP status and stage,
  plain Romanian guidance and an explicit unavailable-diagnostics explanation for old failures.
  Unknown/extra provider data is rejected. No fabricated historical status, online badge or retry.
- Unit/client tests and two actual-service scenarios: metadata404 before any completion and
  completion400 after exactly one synthetic completion attempt, durable scoped reread/events,
  viewer cross-owner refusal and no verified model or automatic paid replay.

The previously prepared adjacent per-model cost checkbox is included in the Web build. Checking
it alone sends nothing; an owner must explicitly submit a separately authorized verification.

## Verification

Exact commands/exit codes/durations: `.cache/provider-diagnostics-fix/*.json`, sanitized final
ledger in `docs/openrouter-evidence/2026-10-29/provider-diagnostics/`.

- `.venv/bin/python -m pytest tests/test_provider_diagnostics.py tests/test_openrouter.py -q`:
  exit0,40 cases. All provider responses are synthetic HTTP fixtures.
- Focused frontend ProviderError/ModelProbe/registry tests: exit0,25 cases.
- `make check`: exit0,314 Python +203 frontend; Ruff/format/mypy/TypeScript/production build pass.
  Initial import ordering and new test wrapping were corrected without removing checks. Earlier
  unrelated cockpit formatting failures in the previous report remain historical evidence.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`: exit0,9 cases before and
  9 after restart, actual isolated PostgreSQL/Redis/MinIO/API/worker with synthetic provider HTTP.
  All original7 cases are retained. Owner-only diagnostics are not exposed to the other viewer.
- `make contracts-check`: exit0; existing schemas unchanged. `make smoke-demo`: exit0, readiness200
  and execution-denial smoke against the running API. No actual broker order is submitted.
- `make secret-scan`, `make repository-check`, `git diff --check`: exit0.
- Targeted API/ai-worker/Web image build: exit0; `up -d --no-build --no-deps --wait`: exit0.
  All three healthy. Every other development container ID and named-volume mount is unchanged.
  Native public HTTP checks confirm nginx serves the new status/stage and adjacent-consent code.
- Browser acceptance remains BLOCKED by the recorded managed-origin rejection. Native/static
  markup tests are not rendered browser acceptance. No visual references were overwritten.

## Deployment and owner verification

Only API, ai-worker and Web images/services were rebuilt/recreated. No development migration, database
restart/reset, user/MFA/session reset, credential replacement, grant change or volume deletion.
Deployment does not relaunch the FAILED request. Final health, served-bundle and preserved mount
identities are recorded in the evidence ledger; no environment or secret values are included.

After the deployed Web update, reload with Cmd+Shift+R. The old failed request will correctly state
that its HTTP status/stage were not preserved. A **new** owner-approved verification, if the owner
chooses to submit one after reviewing its possible cost, can show the exact HTTP status and stage.
That is a separate paid-call authorization; the agent has not executed it. Then inspect Detalii
analiză and Metadate verificabile ale solicitării. Do not lower privacy/routing safeguards to obtain
a successful probe. Real inference acceptance remains open; SIMULATED/DENY_ALL is unchanged.
