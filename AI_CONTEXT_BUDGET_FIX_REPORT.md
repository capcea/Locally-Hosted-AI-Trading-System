# AI context budget correction — 2026-10-30

Implemented and applied locally to API/Web only. Authentication remains PASSWORD under the current
product policy, with legacy MFA enforcement retained where configured. Execution remains
SIMULATED / DENY_ALL. No production data reset, provider request charge, model download or secret
change was performed. Pre-existing uncommitted work was snapshotted and preserved.

## Confirmed cause and reproduction

The actual endpoint is `POST /api/v1/ai/requests`, not an OpenRouter error. A real disposable-service
regression reproduced HTTP422 before the worker/provider was invoked. The pre-fix command
`.venv/bin/python -m scripts.integration_services --auth-only` exited1: **1 failed,39 passed**.
This is separate from the earlier unchanged baseline auth run, which passed39+39 and did not yet
include the new regression.

The latest AI-first Strategy Lab sent `documentation:strategy-lab-v1` automatically. That newly
expanded context contained all eight baseline IDs, versions, long digests and entry/exit prose.
The UI reserved768 output tokens and always requested4096 context tokens. A read-only observation of
the actual installed model confirmed configured ceiling4096 and unexpired verification recording4096.
Neither that record nor the ceiling was changed.

For a short Romanian regression question of **34 UTF-8 bytes**, before correction:

- Approved Lab context JSON:3028 bytes.
- System message content:631 bytes; user message content:3098 bytes; actual message contents:3729 bytes.
- Transport-serialized messages:3995 bytes. The original gate counted this escaped outer JSON.
- Reserved output:768 tokens; chat/template reserve:512.
- Original enforced bound:3995+768+512=**5275**, exceeding4096, hence HTTP422.
- The separately transmitted structured-output schema is1053 bytes and was omitted by the old gate.
  Correct conservative accounting of the original content would require6062, so merely discounting
  JSON escaping would not fix the oversized default context safely.

This was a context-size regression accompanying the newer workflow, not evidence that standing
consent itself consumes model context. For the same34-byte question, the older default
`research-limits-v1` already fit:1339 serialized bytes and original bound2619. No universal claim is
made that all short requests or all roles previously failed.

## Correction and security properties

`apps/api/ai/context.py` now supplies a bounded discovery summary: actual eight baseline IDs/versions,
short guidance and one SHA256 of the complete reviewed registry. The resulting context remains
immutable/hash-pinned and untrusted. Detailed per-strategy rules, digests and assumptions remain
available through the existing explicit strategy-reference path. No account/dataset/financial facts
are invented; no supplied user question is truncated; no protected context is released. This is an
intentional compact default summary, not a replacement for detailed strategy review.

`apps/api/ai/budget.py` and `routes.py` enforce a conservative upper bound on actual UTF-8 message
contents plus the structured-output schema, output reserve and unchanged512 framing reserve. HTTP
JSON escaping is storage/transport overhead, not extra model text. The effective ceiling is the
minimum of requested, registered and currently verified capacities across every permitted selected
model/fallback. Requests above registered/verified capacity still fail. No bytes/4 approximation,
fictional tokenizer measurement or larger context verification was introduced.

For the same34-byte default Lab request after correction:

- Context JSON:848 bytes; system631; user918; message contents1549.
- Serialized messages1723; stored message envelope1736; unchanged platform input cap12000 bytes.
- Structured schema1053; input upper bound2602; output768; framing512.
- Required conservative bound:2602+768+512=**3882**, within4096.
- A second80-byte Romanian question with diacritics requires3928 and also passes.

These numbers are **conservative byte-derived capacity bounds**, not provider tokenizer counts or
actual billed usage. Explicitly larger contexts still fail closed. Schema/output validation,
owner/session/CSRF checks, persistent consent, worker isolation, holdouts, OpenRouter Decimal spend
reservations and role quotas are unchanged. In particular, cloud spend reservations still use the
requested context/output ceilings; this patch does not lower financial reservations to an estimate.

## Safe diagnostics and submission recovery

The server emits `ai.context_budget` through the existing structured request logger. Only fixed
method/event labels, a correlation ID, an acceptance boolean and integer sizes/limits are logged.
No question, context body, credential, cookie, owner ID or provider response is logged by this code.
Rejected capacity requests retain the compatible string `detail` and add numeric-only
`X-AI-Context-Budget`; `X-Request-ID` correlates the normal request log. HTTP status remains422.

The frontend parses only allowlisted bounded integer diagnostic fields. Malformed diagnostic headers
and unknown fields are never rendered. The Romanian error explains the specific capacity issue,
shows content/schema/reserve/ceiling numbers, and offers editing, a smaller context or separately
verified model capacity rather than a generic invalid-fields message.

Both composers choose a context ceiling from actual current model verification/configuration,
including explicitly enabled fallback capacity. Missing/expired metadata does not invent a4096
fallback. Reserved output remains768.

On definitive HTTP422 pre-enqueue validation, the frozen draft is released and becomes editable;
the next user submission obtains a new key. Network failures,503 and other uncertain outcomes retain
the exact frozen request/idempotency key. No automatic resend occurs. Existing server idempotency
checks precede mutable context reads, so a retry cannot silently change an already accepted request.

## Files changed in this task

- API: `apps/api/ai/budget.py` (new), `context.py`, `routes.py`.
- Frontend: `apps/web/src/ai/budget-diagnostics.ts` and `submission-budget.ts` (new), `AIChat.tsx`,
  legacy `AICenter.tsx`, `copy.ts`, `apps/web/src/management-api.ts`.
- Regressions: `tests/test_ai_context_budget.py` and `test_ai_context_budget_integration.py` (new),
  existing `test_password_ai_integration.py`, `apps/web/src/ai/submission-budget.test.ts` (new),
  existing `apps/web/e2e/phase6.spec.ts`.
- Harness: `scripts/integration_services.py` includes the new actual-service regressions in focused
  auth and complete suites, including after graceful restart.
- This report, both implementation-status pointers, current-context amendment in the AI-first
  workflow report, and sanitized evidence under `docs/ai-context-budget-evidence/2026-10-30/`.

All `packages/` and `apps/api/research/` files match the pre-task SHA256 snapshot. In particular,
OpenRouter adapters/routing/credentials, standing authorization/spending logic, schema validation,
risk/backtest calculations and research software fingerprints were not modified.

## Verification

Executed commands and results (exit0 unless stated):

- `make check`:346 Python unit/native tests and246 frontend tests pass; Ruff, mypy, ESLint,
  Prettier, TypeScript and production build pass.150 infrastructure/isolated tests are deselected
  by this command and are not counted as native success.
- `.venv/bin/python -m scripts.integration_services --auth-only`:41+41 pass against actual disposable
  PostgreSQL, Redis and MinIO before/after graceful restart. Includes short Romanian Research
  requests with both approved default documentation contexts, actual HTTP fixture inference,
  valid4096 verification, numeric-only diagnostics, real overflow/no-provider/no-key reservation,
  corrected submission, duplicate protection and refusal of unverified8192 requests.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`:25+25 pass against disposable
  services and synthetic HTTP transport. Preserves cloud policy, spending, secret, owner and permanent
  authorization checks. This is not real-model/provider acceptance.
- `make integration-services`:149+149 pass, exit0,546.404 seconds. All149 selected real-service
  scenarios pass before and after restart, including AI, research, market data, risk, execution
  denial, owner isolation, cloud budgets and campaigns. The harness cleans up only its own project.
- `make contracts-check`, `make smoke-demo`,
  `.venv/bin/python -m scripts.smoke_demo --require-ready`, `make secret-scan`,
  `make repository-check`:pass. Strict readiness confirms actual dependencies HEALTHY, HTTP200.
- `npm --prefix apps/web run test:e2e -- --list`:30 cases collect, exit0; collection is NOT execution.

The existing Phase6 browser scenario now additionally exercises a real server422 at verified4096,
editable recovery, new key, approved Lab default context and successful corrected Research submission.
No mock response or tolerance/snapshot change was added. Browser execution is **NOT RUN/BLOCKED** by
the previously observed managed local-origin restriction; it was not bypassed through a CLI or
alternate browser. No current rendered visual acceptance is claimed.

Nonblocking existing warnings: Starlette TestClient/httpx deprecation and frontend bundle >500kB.
No test assertion was weakened or skipped.

## Local rollout and remaining acceptance

Built only API/Web and applied with `up -d --no-build --no-deps --wait --wait-timeout 90 api web`
using the existing Compose files/profiles. Build and update exited0. Container identities for every
other service and all named-volume mount mappings are unchanged. No worker restart, migration,
policy edit, model reverification, provider-credential inspection/change or real generation/probe was performed.
Deployed budget module matches source; served HTML and both JS/CSS assets match the new native build. Readiness200,
PASSWORD and DENY_ALL were verified after update.

Owner browser validation, without snapshot rewriting or paid providers:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT E2E_ONLY_SCENARIO=ai make browser-integration
```

These use disposable infrastructure and the explicitly synthetic HTTP fixture. For the running local
application, reload the tab to load the new bundle. A prior definitive422 draft should now unlock
editing; the correction itself never automatically submits a chargeable OpenRouter request.
Large prompts, additional strategy/experiment context, or other roles with larger schemas may still
exceed this conservative4096 budget. The UI now explains that limitation rather than claiming model
success. Actual paid inference and rendered browser acceptance remain separate owner gates.

See [sanitized evidence](docs/ai-context-budget-evidence/2026-10-30/README.md).
