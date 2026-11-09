# OpenRouter generation404 — ZDR routing and parameter compatibility

2026-10-29. Confirmed configuration conflict; safe preflight/adapter repair. No paid request was
submitted by the agent. Actual model inference and browser acceptance remain unverified.

## Evidence and diagnosis

The owner supplied a new failure with HTTP404 at COMPLETION and confirmed approved upstream
`openai`. The model shown in the setup is `openai/gpt-4.1-mini`. The model author (`openai/…`) and
the processing provider tag (`openai`, `azure`, etc.) are different identifiers.

Read-only public API observations, without credentials or generation:

- The [model's endpoint catalog](https://openrouter.ai/api/v1/models/openai/gpt-4.1-mini/endpoints)
  includes `openai`, `azure`, `azure/swedencentral`. Thus model/catalog presence is confirmed.
- The actual [ZDR endpoint preview](https://openrouter.ai/api/v1/endpoints/zdr) returned200 and
  listed **azure and azure/swedencentral, but no openai**, for that model. The filtered timestamped
  observation is preserved in the evidence directory. The complete metadata response was1110576
  bytes, within the existing4MiB bound; unrelated model records were not retained.
- The authorized request pins `provider.only = ["openai"]`, `zdr = true`, `data_collection = deny`,
  `require_parameters = true`, no fallback. The selected provider and current ZDR eligibility have
  an empty intersection. This is a verified routing conflict sufficient to prevent a compatible
  selection; the original404 body's exact wording was not retained, so no claim of its exclusive
  server-side reason is made. Account guardrails/pricing can impose further restrictions.
- Azure's metadata declares `max_completion_tokens`, while the adapter always sent `max_tokens`.
  With require_parameters=true, that is an additional supported-parameter mismatch if the owner
  explicitly approves Azure. The numeric output allowance must remain unchanged.

Sources: [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection) and
[ZDR preview API](https://openrouter.ai/docs/api/api-reference/endpoints/preview-the-impact-of-zdr-on-the-available-endpoints).
These are dated provider observations, not independent certification of third-party privacy terms.

## Changes and preserved authority

- `packages/ai/providers.py`: before completion, read the exact model metadata plus the ZDR preview
  through the existing authenticated, pinned HTTPS/egress adapter. Require an exact approved tag
  and model match, declared structured output/temperature/top_p support and a supported output-limit
  parameter. Missing/unknown/incompatible metadata refuses with a constant code before completion.
  A per-adapter/job cache avoids duplicate metadata reads, not durable readiness or authorization.
- Select `max_tokens` or `max_completion_tokens` from declared capabilities, carrying the **same**
  integer allowance. Provider-reported usage is checked against either spelling. Probe authorization
  is rechecked after metadata and before completion through the existing heartbeat callback.
- `apps/web/src/ai/copy.ts`: clear Romanian explanation of absent approved ZDR provider or parameter
  support. No fake HTTP status, verified-model flag or success output is created.
- Test fixtures now explicitly declare ZDR/parameter metadata. Ten unit tests, one frontend test
  and two additional real-service scenarios cover refusal with zero completion POSTs, exact-provider
  matching, token aliases, usage overflow and no automatic fallback/retry.

The cloud policy, owner-selected upstream, privacy flags, price caps, request/day budgets, API key,
MFA/CSRF/RBAC, immutable model/policy revisions and SIMULATED/DENY_ALL are **unchanged**. No provider
was automatically substituted. No migration, risk/backtest/account arithmetic or new phase.

## Actual tests and operational status

Exact invocations/exit codes/timings are in `.cache/openrouter-routing-fix/*.json`; final sanitized
evidence is in `docs/openrouter-evidence/2026-10-29/zdr-routing/`.

- Focused readiness/provider/diagnostic unit tests: exit0,50 cases, synthetic HTTP only.
- Focused frontend registry/probe/error tests: exit0,26 cases.
- `make check`: exit0,324 Python +204 frontend; lint, formatting, mypy, types and build pass.
  An initial Ruff false-positive on an LLM output-parameter variable name was corrected by renaming
  it; the scanner was not suppressed or weakened. Existing deprecation/chunk warnings remain.
- `make contracts-check`: exit0; API contracts unchanged.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`:11 before +11 after restart,
  actual disposable PostgreSQL/Redis/MinIO/API/worker, synthetic provider responses. Original cases
  retained; no actual OpenRouter generation was used for passing results.
- Targeted ai-worker/Web build and start: exit0; both healthy. Actual native HTTP confirms the new
  error copy is served. Every other container ID and named-volume mount identity is unchanged.
- `make smoke-demo`, `make secret-scan`, `make repository-check`, `git diff --check`: exit0.
- Managed browser execution remains BLOCKED. No browser success or accepted golden rewrite.

## Owner action

The update is deployed. Reload Web. The current `openai` authorization is intentionally still unchanged;
a new probe now explains its ZDR incompatibility before generation rather than blindly submitting
the same incompatible completion. Do not remove ZDR, privacy, strict validation or billing limits.

If the owner chooses Azure after reviewing its processing/privacy terms, use Setări → Modele AI →
Revizuiește autorizarea OpenRouter, enter the currently eligible exact provider tag (for example
`azure`), review/preserve intended billing caps and explicitly approve a new authorization with MFA.
This changes the processing provider and invalidates prior approvals/verifications as designed.
Keep the model ID `openai/gpt-4.1-mini`; do not confuse its author prefix with the provider tag.
Then, only if the owner chooses to authorize the possible cost, submit one new model verification.
It is not automatically submitted by this deployment. Real-model Research/Critic acceptance is
pending that measured result and explicit role assignment. Provider eligibility can change.
