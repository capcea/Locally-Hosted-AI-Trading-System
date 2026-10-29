# Phase 6 — implementation and acceptance report

Date: 2026-10-28. **IMPLEMENTED / ACCEPTANCE PARTIAL.** SIMULATED/DENY_ALL remains enforced.
Real installed-model inference and current browser/manual acceptance are not verified. No Phase7.

**Current follow-up:** the owner-local Phase6 desktop browser run failed at the AI destination's
exact label. The accessible-name defect is corrected in source and covered by failing-before /
passing-after native tests. This does not establish a passing browser run. See
[the correction evidence](#ai-dropdown-accessible-name-correction--2026-10-28).

The owner explicitly authorized this phase and reports Phases0–5.5 local automated acceptance passed.
That is **OWNER_REPORTED_PASS**, separate from agent evidence. Previous reports/logs/approved images
are preserved. No remote repository, paid infrastructure, model download, broker credentials,
external order capability, generated-code runner or automated promotion was introduced.

## Delivered implementation

- **Private adapters and contracts — implemented, native protocol-tested:** Ollama native NDJSON,
  Ollama-compatible SSE and private-compatible SSE through a typed fixed adapter registry. Strict
  bounded schemas independently validate version/authority types, fields, references and missing
  evidence. Hidden reasoning is discarded; ordinary tool calls and executable authority are refused.
- **Registry/routing — implemented, real-service tested:** owner-scoped immutable connection/model/
  role revisions, worker-measured expiring capabilities, independent four-role selection, explicit
  alternatives and remote processing policy. Saved entries are never presented as verified models.
- **Lifecycle — implemented, real-service tested:** additive Alembic0007, encrypted temporary inputs,
  durable jobs, scoped Redis hints, quotas/global slots, idempotency, bounded wait/SSE, cancellation
  acknowledgement, bounded safe retry, UNKNOWN after uncertain dispatch, fencing, one final artifact,
  metadata-only audit, bounded retention and owner content erasure.
- **Research context — implemented, real-service tested:** API-only scoped read allowlist for strategy,
  completed experiment, quality metadata and reviewed documentation; no raw SQL/files/web/tools.
  Existing holdout/alias restrictions extend to cached AI references and stored output reads. Sealing
  is fenced against active disclosure and revokes queued input. Prior exposure remains UNKNOWN.
- **Isolation/deployment — implemented and locally tested:** AI-only database/Redis/key identities,
  whitelist non-root worker image, disjoint API/worker queue networks, private database/inference
  networks, empty-by-default constrained CONNECT proxy, scoped read-only secrets, non-root AI Redis.
  Actual running-container denial/round-trip checks pass, including after dedicated queue restart.
  This is local topology evidence, not a remote GPU/public-deployment certification.
- **Romanian AI Center — implemented, unit/type/build tested; browser acceptance BLOCKED:**
  `/testeaza/ai`, reloadable `/testeaza/ai/{id}` and advanced `/setari/ai`. Actual APIs drive unavailable
  model states, setup/probes/roles, question/context/rights review, immutable-key retry, job/cancel,
  structured unverified answers, critique, inert code text, usage/limits and provenance. Stale worker
  observation is refreshed; expired verification cannot remain usable just because a page stayed open.
  Five main destinations and previous workflows remain. No fabricated AI activity or financial score.
- **Evaluation — contract fixture implemented; actual model evaluation NOT EXECUTED:** reproducible
  fixture/adversarial/schema/TLS/protocol tests and an owner-invoked real-provider probe/evaluation
  command. Synthetic cases explicitly ignore questions; they are not a model-safety benchmark.

Source groups: `packages/ai/*`, `apps/api/ai/*`, `migrations/versions/0007_ai_gateway.py`,
`scripts/{ai_setup,ai_worker,provision_ai,check_ai_deployment,check_ai_runtime,evaluate_ai,verify_ai_runtime}.py`,
`deploy/ai/*`, `services/ai_egress/*`, `compose.ai.yaml`, `apps/web/src/ai/*` and
`apps/web/e2e/phase6.spec.ts`. Existing API mounting, health, registry metadata, research seal,
runtime grants, navigation, generated contracts, smoke and disposable harnesses changed additively.
No financial sizing/backtest engine or broker-order implementation was rewritten.

## Defects found and fixed

1. Initial real-service AI discovery failed HTTP409: request/content/job objects had no cascading
   ORM relationship to enforce parent insert order. Explicitly flush the immutable request before
   children. Foreign-key assertions remain enforced. Initial result:5 failed/78 passed; reruns pass.
2. Independent validation exposed Pydantic literal equality accepting numeric0 for boolean false.
   Exact JSON version/authority type checks now reject this, duplicate keys and malformed schemas.
   Model-supplied references must be a subset of authorized inputs. New adversarial tests pass.
3. Cached AI summaries and later holdout seals needed a shared disclosure boundary. Advisory locks,
   queued-input revocation, recursive source/hash authorization and read-time content hiding prevent
   reuse after sealing. Actual admitted data/MinIO tests cover the race and preserved provenance.
4. Invalid optional AI configuration could have prevented the entire API from mounting. Malformed
   settings, missing key files and identity-key reuse now disable AI alone with a fixed safe category.
   Native full-MFA identity and SIMULATED/DENY_ALL safety remain reachable. No permissive fallback.
5. A shared API/worker queue network could expose the API on that interface. They now use separate
   internal client networks; Redis alone joins both. Effective configuration and actual TCP denials
   verify that the running worker cannot reach any API interface or resolve its service alias.
6. Docker creation initially stalled without a diagnostic; interrupted operations later completed and
   caused a stateless API-name conflict. Recover by retaining the correct container and data mounts,
   removing only a stopped stateless API container. A transient smoke exit2 (connection refused) is
   retained. Dedicated Redis then failed `chown: .: Operation not permitted`: its root entrypoint
   conflicted with dropped capabilities. Run directly as pinned UID999/GID1000 with owned tmpfs;
   keep ALL capabilities dropped. Local AI services now start, and queue-restart boundary checks pass.
7. The smoke phase allowlist was still0–5; extend it to the newly authorized Phase6 while retaining
   every safety and order-denial probe. Initial portable failures were corrected and rerun.

A fresh scan of copied failure evidence flagged five disposable UUID idempotency keys in diagnostic
request-body snippets. They were verified as test keys and redacted; no scanner allowlist/rule changed.
The source/evidence scan then passed. No service credential was published.

Early HTTP tests also had incorrect expected error-category/wrapper types; these test-authoring
errors were corrected to assert the actual fail-closed categories. No timeout/tolerance increase,
assertion removal, mock authenticated response, skipped case or snapshot rewrite was used.

## Actual verification

Commands were run at the repository root. Exact invocations, exit codes, timings and sanitized output
are in [the evidence ledger](docs/phase6-evidence/2026-10-28/verification.json). Earlier failed
iterations remain recorded; the following are the final completed results.

- **PASSED**, `make check`, exit0: Ruff/format, ESLint/Prettier, strict Python/TypeScript, **243 Python
  tests +117 frontend tests**, production build. Existing Starlette/httpx deprecation and Vite bundle
  size warning remain; no verified accessibility/performance claim follows from this result.
- **PASSED**, `make integration`, exit0:1 native infrastructure readiness case, **86 actual isolated
  cases before restart +86 after restart**, and strict HTTP200 readiness/execution-denial smoke.
  Includes actual PostgreSQL migrations, Redis/MinIO, research/risk/execution regressions and8 AI cases.
- **PASSED**, `env PYTEST_ADDOPTS='-k test_ai_' make integration-services`, exit0:8 focused AI cases
  before +8 after restart, with78 deliberately deselected for this *focused* run only. The separate
  full integration above has no deselection of its applicable isolated cases.
- **PASSED**, `make contracts-check`, `make smoke-demo`, `make secret-scan`, `make repository-check`,
  exit0. Secret scan reports no leaks in Git-selected source/evidence, not a remote vulnerability audit.
- **PASSED**, `npm --prefix apps/web run test:e2e -- --list`, exit0: **22 cases in9 files**, desktop
  and mobile. This is collection only. Existing20 remain; the new AI flow adds one case per viewport.
- **BLOCKED / NOT EXECUTED**, focused and full browser execution, exit **null**: existing managed
  localhost browser-origin denial persists. No Chromium/bootstrap failure was fabricated and no CLI,
  CDP, proxy or alternative browser was used to bypass that denial. Prior owner acceptance remains
  separately attributed; current AI flow and all22 scenarios require owner-local execution.
- **BLOCKED**, actual Ollama discovery `http://127.0.0.1:11434`, exit2:
  `BLOCKED_RUNTIME_UNAVAILABLE`, `actual_inference_verified:false`. No installed model inferred,
  downloaded or replaced by a fixture. Real GPU/context/quality/cost results are NOT VERIFIED.
- **PASSED**, `.venv/bin/python -m scripts.evaluate_ai`, exit0:12 **SYNTHETIC_HTTP_FIXTURE** schema/
  protocol cases. Real model quality explicitly NOT EVALUATED; fixture token counts are not AI usage.
- **PASSED**, worker image build and network-none/non-root/source-boundary run, exit0. API/risk/
  research implementation and Docker socket are absent from the worker image.
- **PASSED**, `.venv/bin/python -m scripts.check_ai_deployment`, exit0: effective network/environment/
  no-public-AI-port configuration, with no printed secrets.
- **PASSED**, scoped AI overlay `up ... --wait`, exit0 after fixes; API/AI worker/AI Redis healthy and
  proxy running. `.venv/bin/python -m scripts.check_ai_runtime`, exit0 before and after AI Redis
  restart: actual scoped SQL/Redis, forbidden table/key denial, all API interfaces unreachable,
  metadata/public TCP denied, unapproved proxy CONNECT refused. Approved inference endpoints:0.

## Persistence and current local state

The initial working tree (including unrelated uncommitted changes) was hashed and privately backed
up before Phase6. The four owner-approved PNG references remain byte-for-byte unchanged. PostgreSQL,
Redis and MinIO original persistent mounts are unchanged. PostgreSQL container was recreated for an
additive private network; stateless API/web containers were refreshed. A private PostgreSQL dump was
taken before development migration0007. No development volume was removed, pruned, downgraded or reset.
Only random disposable test projects/volumes were cleaned by their owning harness.

The ordinary eight application services are healthy. Optional AI worker/Redis are healthy and the
empty-allowlist proxy runs. No real model is configured, no active AI research is claimed and no
external orders can execute. Physical ciphertext sweeping needs a running worker; API retention and
context checks still hide expired/revoked content when sweeping is delayed.

## Remaining gates and owner actions

1. Select an **already installed**, private-only reviewed runtime/model and approved endpoint. Verify
   cloud-off behavior, identity/digest/context, capability controls, actual latency/usage and resource
   limits with the real-provider command in [the deployment guide](AI_DEPLOYMENT_GUIDE.md). No paid
   host or automatic model download is authorized. Remote TLS/SSH deployment remains unverified.
2. In an owner-permitted local terminal run:

   ```sh
   E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
   env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
   ```

   Require all22 cases. Inspect genuine visual differences; any intentional reference change still
   requires owner review. No reference candidate was captured or automatically adopted in this phase.
3. Perform actual keyboard/mobile/light-dark/200% zoom/screen-reader checks. Source/SSR/unit evidence
   does not prove WCAG2.2AA or rendered acceptance. Current screenshots are not fabricated.
4. Before production/remote exposure: define secret rotation, backup expiry/restore and metadata
   archival, monitor actual GPU/VRAM/cost, review remote privacy/licensing and enforce deployment
   firewall/identity controls. Monthly cost accounting, autonomous agents/web retrieval, hostile-code
   sandbox, paper/live trading and automatic promotion are **NOT IMPLEMENTED** here.

**Phase6 is not fully accepted.** Next action is to close these gates, not start another module.
Phase7 requires a separate instruction and remains untouched.

## AI dropdown accessible-name correction — 2026-10-28

**FIXED IN SOURCE / NATIVE REGRESSIONS PASSED / BROWSER ACCEPTANCE STILL PENDING.**
The owner supplied an actual local Chromium failure, not a bootstrap problem. The preserved
non-secret [error context](docs/phase6-evidence/2026-10-28/ai-select-label/owner-error-context.md)
shows `phase6.spec.ts:17` waiting for the exact `Destinație aprobată` label inside `Registru AI`.
The preceding connection-name fill succeeded. There is no resolved-select entry in the failure
call log; `backend_failures: []` alone does not establish that every backend call succeeded.

### Root cause and correction

The rendered JSX puts both the label text and the select/options inside one `<label>`, with no
`aria-label` or `aria-labelledby` on the select. The installed Playwright1.64.1 label selector
uses the wrapping label's recursive text when no explicit accessible name exists. With the
configured fixture option it reads `Destinație aprobatăSYNTHETIC_HTTP_FIXTURE · LOOPBACK`.
That cannot match the existing exact string `Destinație aprobată`. The field is present, but
its selector label is contaminated by option content. Additional waiting cannot repair that.

A native diagnostic exercised the installed selector-label function on non-secret synthetic
element records, without launching a browser or accessing/rendering the application. It reproduces
the mismatch, and the same function returns an exact match with the explicit label. See
[selector-diagnostic.json](docs/phase6-evidence/2026-10-28/ai-select-label/selector-diagnostic.json).
This is selector-algorithm evidence, not a reconstructed DOM snapshot or browser success claim.
The owner's artifact contains no DOM snapshot or HTTP response capture, so those are not invented.

- `apps/web/src/ai/AICenter.tsx`: give all eight AI dropdowns explicit accessible names identical
  to their visible Romanian labels. This includes destination, protocol, connection, role,
  primary/fallback model, analysis type and context type. Export the existing registry component
  for direct native regression rendering. Field names, values, filtering, API payloads and handlers
  are unchanged; no CSS or visual reference changed.
- `apps/web/src/ai/ai.test.tsx`: cover empty, populated and revised registry options, preservation
  of the `fixture` option, exclusion of unverified models from routing, and both analysis selectors.
  The four new cases failed before the correction; all seven AI frontend cases pass afterward.
  These are native static-markup checks and do not establish keyboard or screen-reader acceptance.
- `apps/web/e2e/phase6.spec.ts`: retain the exact label/region and original selection; add explicit
  fixture option/value assertions and require real HTTP201 on connection creation before continuing.
  The 180-second global timeout and all model verification, analysis, cancellation, FULL-session,
  execution-denial and viewport assertions remain intact.
- `tests/test_ai_integration.py`: the existing real-service registry round-trip now first asserts
  authenticated `GET /api/v1/ai/endpoints` returns HTTP200 and the approved fixture entry. The
  existing actual HTTP201 connection, worker discovery/probe, unverified-route refusal,
  encrypted result/idempotency, audit and scoped SQL/Redis denials remain required.

`scripts/browser_acceptance.py` already provisions the `fixture` endpoint through isolated
`AI_ENDPOINTS` configuration and starts the real synthetic HTTP server. The authenticated API
returns only approved id/label/transport metadata. Neither this setup nor backend production
logic needed a change. The native service check uses actual PostgreSQL/Redis/MinIO infrastructure
and real synthetic-provider HTTP; it is not installed-model inference or browser validation.

No MFA/CSRF/RBAC, owner scope, allowlist, verification, encryption, risk, holdout or financial rule
changed. No authenticated response was mocked. No assertion was removed, timeout increased,
sleep inserted or image tolerance/reference changed. SIMULATED/DENY_ALL remains active.

### Follow-up verification and remaining gate

Exact commands, exits and logs are preserved in the
[follow-up ledger](docs/phase6-evidence/2026-10-28/ai-select-label/verification.json).
Earlier Phase6 evidence above is retained separately.

- `npm --prefix apps/web test -- src/ai/ai.test.tsx`: **expected RED**, exit1, four new failures
  and three existing passes before the correction; **PASSED**, exit0, seven tests after correction.
- `make check`: **PASSED**, exit0;243 Python +121 frontend tests, lint/format/type checks and build.
- `env PYTEST_ADDOPTS='-k test_registry_real_roundtrip_idempotency_and_scoped_worker' make integration-services`:
  **PASSED**, exit0; one focused real-service case before restart and one after,85 deselected each
  time for this focused invocation. The full integration invocation is recorded separately.
- `make integration`: **PASSED**, exit0; one infrastructure readiness case,86 actual isolated
  cases before restart and86 after restart, plus strict HTTP200 readiness/execution-denial smoke.
  PostgreSQL migrations, Redis/MinIO round trips and the previous research/risk/AI regressions
  all run; the full isolated invocation has no focused-test filter.
- `make contracts-check`, `make smoke-demo`: **PASSED**, exit0; smoke reports HTTP200 readiness
  and execution-denial success.
- `make secret-scan`, `make repository-check`, `git diff --check`: **PASSED**, exit0; no leaked
  secrets detected in the selected source/evidence, sensitive paths remain excluded, no whitespace
  errors. No Git commit, remote creation or push was performed.
- `npm --prefix apps/web run test:e2e -- --list`: **PASSED**, exit0;22 desktop/mobile cases collected
  in9 files. Collection does not run a browser.
- Web-only local image refresh: **PASSED**, exit0. The healthy web container serves HTML/JS/CSS
  byte-identical to the new production build. All11 other development container identities,
  images and mounts, and all four approved reference hashes are unchanged. No development
  volume was removed/reset. Only the integration harness's own disposable resources were cleaned.
- Focused/full browser execution: **BLOCKED / NOT EXECUTED**, exit null. The existing managed
  localhost-origin restriction remains; no alternative browser/CLI/CDP/proxy bypass was attempted.
  The owner's reported failing Chromium run is distinct from this restriction.

Run locally without snapshot rewriting:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

Require all22 cases before browser acceptance. Actual model availability/inference and manual
accessibility gates remain as stated above. No Phase7 implementation was started.

## Design/operations references

[Architecture](AI_GATEWAY_ARCHITECTURE.md), [model registry](AI_MODEL_REGISTRY.md),
[security boundaries](AI_SECURITY_BOUNDARIES.md), [evaluation](AI_INFERENCE_EVALUATION.md),
[deployment](AI_DEPLOYMENT_GUIDE.md), [implementation status](IMPLEMENTATION_STATUS.md).
