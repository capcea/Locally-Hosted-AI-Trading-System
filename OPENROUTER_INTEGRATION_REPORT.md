# OpenRouter integration and AI settings repair

2026-10-28. **IMPLEMENTED; local startup and native integration PASSED;
browser acceptance BLOCKED; actual OpenRouter inference NOT VERIFIED.** No OpenRouter key was
introduced, public inference enabled, model downloaded or chargeable provider request made.
SIMULATED/DENY_ALL remains unchanged. This is a Phase6 integration follow-up, not another phase.

## Verified cause

The existing development installation has zero approved `AI_ENDPOINTS`, zero AI connections and
zero AI models. These are sanitized counts from a read-only configuration/database inspection,
not inferred from a screenshot. The empty destination → connection → model chain is therefore
primarily missing configuration, make ai-check-deployment
make ai-check-runtime
make integrationbehaving fail-closed. A saved connection would not establish
model availability anyway.

The previous private-only endpoint schema accepts approved literal-IP origins, not a public DNS
URL with `/api/v1`. Selecting PRIVATE_OPENAI or privately approving OpenRouter would have been
incorrect: private consent does not authorize processing by OpenRouter and its upstream provider.

There were also source-confirmed UX defects: one failed registry read rejected the entire
`Promise.all`, empty selects lacked useful prerequisites, protocol selection did not follow the
selected destination, and role options did not independently check verification expiry. The repair
loads collections independently, clears failed reads, exposes retry/error states, explains empty
and disabled controls, derives the public protocol from its approved destination and excludes
expired/revoked model verification. Accessible select names remain stable.

## Changes and authority

Three independent approvals are required for public processing:

1. Operator opt-in on API and worker, plus the exact CONNECT proxy destination. Default is OFF.
2. Authenticated OWNER with recent MFA and CSRF creates an immutable `openrouter-public-v1`
   authorization: explicit public-cloud, upstream/data-rights, cost and provider-policy-limit
   acknowledgements; one exact upstream provider tag; price and reservation bounds.
3. Connection privacy consent, write-only key setup and a separate cost acknowledgement on each
   probe/inference submission. Remote-context consent and existing rights/retention checks remain.

Saving the authorization, connection, credential or exact model identifier makes no provider call.
Model registration is explicitly unverified. Catalog lookup uses a queued metadata GET; verification
uses one potentially billable structured completion. There is no silent synthetic fallback.

Important source changes:

- `packages/ai/cloud_contracts.py`, `cloud.py`, `models.py`: strict policy/credential contracts,
  encrypted connection credential revisions, immutable authorizations and atomic Decimal spend
  reservations. Alembic `0009_openrouter` is additive, following `0008_research_campaigns`.
- `apps/api/ai/cloud_routes.py`: owner-scoped `GET /api/v1/ai/cloud-policy`,
  `POST /api/v1/ai/endpoints/openrouter`, and
  `POST /api/v1/ai/connections/{id}/credential`. No arbitrary URL registration or key readback.
- Existing `apps/api/ai/routes.py`, registry and worker: original scoped queue/lease/idempotency,
  session authorization and context restrictions; new cloud snapshot/reservation checks. Policy
  and credential revisions revoke verification and refuse stale queued/in-flight publication.
- `packages/ai/providers.py`: reuse the compatible SSE adapter with exact OpenRouter paths,
  HTTPS verification, strict upstream routing and safe status categories. Private Ollama/native,
  Ollama-compatible and private-compatible support remain.
- `services/ai_egress/proxy.py`, `compose.ai.yaml`: exact opt-in hostname exception, otherwise
  existing isolation and literal destinations. `scripts/configure_openrouter.py` previews/applies
  only the nonsecret operator exception; `scripts/refresh_ai_grants.py` retains the existing identity.
- `apps/web/src/ai/{AICenter,CloudSetup}.tsx`, `api.ts`, `copy.ts`: setup, consents, key entry,
  prerequisites and errors inside the existing V1 layout. No CSS or accepted golden changes.
- Campaign handoffs carry the same explicit cost acknowledgement and pinned authorization/key
  revision. Research bounds, financial math, risk rules, holdout protection and owner MFA remain.
- `scripts/provision_ai.py`, `scripts/provision_runtime.py`: narrowly extend original AI-only reads
  and append-only table restrictions. API contracts regenerated; readiness expects schema0009.

## Egress, keys and financial limits

Only `https://openrouter.ai/api/v1` is supported. No custom cloud CA/mTLS/token-file override,
alternate hostname, HTTP, redirect, arbitrary URL or public fallback is accepted. The CONNECT
exception is exactly `openrouter.ai:443` with policy version `openrouter-public-v1`. Every DNS
answer is checked; any private, loopback, link-local, shared/reserved or multicast answer refuses
the connection. The proxy connects the validated literal without resolving the hostname again.
The trusted worker independently verifies the public TLS hostname/CA using HTTPX with ambient
proxies disabled. The proxy does not possess credentials or join application control networks.
Its CONNECT tunnel is not a general HTTP service; application paths are fixed by the trusted adapter.

The key is a bounded `SecretStr`, encrypted with the existing separate AI content key in
`ai_connection_secrets`. Response/audit expose only configured/revision status, never plaintext or
ciphertext. Request validation omits rejected input values. The React password form is mounted
only on demand, cleared and unmounted on submission, and never stored in browser persistence.
Bearer authorization is added only to the worker's approved provider HTTP request, outside prompts.
Known OpenRouter-key patterns in questions/context and provider credential reflection are refused.
Public partial output is not persisted. Errors never echo provider bodies. Automatic authentication
screenshots/traces remain disabled.

The upstream route requests one exact provider tag, `allow_fallbacks:false`, `require_parameters:true`,
`data_collection:deny`, ZDR and maximum prompt/completion prices. A model with no compliant route
must fail; the application must not weaken these conditions to obtain a response. The single public
probe measures structured output, not tool/reasoning capabilities; those remain unverified.

Default authorization bounds are $1/million input tokens, $4/million output tokens, $0.01/request
and $0.50/UTC day. These are owner-reviewable maximum-price assumptions, **not model prices**.
Reservation = approved context ceiling × maximum input price + output limit × maximum output price,
rounded upward to eight decimal USD places. Limits cap each authorization at $0.10/request and
$5/day, with a fixed $50/day global reservation cap. Original hourly, role, pending-job and
concurrency limits still apply. Reservations are atomic, not refunded after failure/cancellation/
uncertainty, and remain counted across authorization revisions. DISCOVER reserves zero dollars.
Public calls never automatically retry or switch models; UNKNOWN is not permission to retry.

Reservations are not independently verified invoices. Provider fees, policy changes, dishonest
usage reports and external calls made with the same key are outside this ledger. **A separate low
provider-side key spending limit is required before real use.** The host/API/worker administrators
and encryption key are trusted, not an HSM boundary. The worker necessarily holds the inference
credential in memory; model text receives no database, broker, shell, tool or execution capability.
ZDR/no-training routing requests are not independent certification of provider behavior/residency.

## Original existing-installation setup — owner actions

At the original implementation checkpoint, development was inspected at schema0008; source requires0009. No
development migration, restart, credential/key rotation, operator opt-in or volume reset was done.
The original AI key/queue identities already exist: **do not rerun `make ai-setup` over them**.
Take and verify the normal database/immutable-storage backup, including separately protected AI
content keys. Review/reconcile active work before rebuilding software-bound workers.

From the repository root:

```sh
.venv/bin/python -m scripts.configure_openrouter
# REVIEW_ONLY: read this policy and review the exact destination exception first.
make migrate
.venv/bin/python -m scripts.refresh_ai_grants --apply
.venv/bin/python -m scripts.configure_openrouter --apply --reviewed-policy openrouter-public-v1
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up --build -d --wait --wait-timeout 180
make ai-check-deployment
make ai-check-runtime
make integration
```

Only the preview was executed here; it returned REVIEW_ONLY and zero provider requests. Apply keeps
private endpoints, credentials, content key and queue identities unchanged, atomically preserving
mode0600. It adds `AI_OPENROUTER_ENABLED=true` and the exact hostname exception to the existing
egress allowlist. API and worker receive the flag; the proxy receives only its destination policy.
Normal migrations refresh API grants; the explicit grant refresh adds the new AI-only reads.
The command preserves volumes; never add `down --volumes`, prune or reset. For a genuinely fresh
installation follow the original deployment guide first. All commands above still need actual
owner-local deployment/readiness verification; they are not claimed successful here.

Then, with owner MFA:

1. On OpenRouter's website, review processing/retention and upstream terms. Create an inference key
   with a small hard spending limit, not a management key. Never paste it into chat, a shell command,
   `.env`, a prompt, a screenshot, trace or source file.
2. Open `/setari/ai#ai-destinations`. Choose the intended exact model from current provider metadata;
   find the exact upstream endpoint **tag**, not a display name. Register the fixed destination with
   that tag, reviewed price ceilings/reservation bounds and all four separate acknowledgements.
3. Create a connection. OpenRouter selects `OPENROUTER · OpenAI compatibil`, not OLLAMA_NATIVE.
   Independently approve cloud/remote processing, rights and retention. Optional minimized account
   context requires its own consent; approving ordinary documentation does not grant that right.
4. Use “Configurează cheia OpenRouter” and submit the key once. It is write-only. Missing-key
   discovery/probe is refused. Rotation invalidates previous model verification.
5. Enter the **exact owner-selected `author/model` ID** and context ceiling. No fictional model is
   preselected. Automatic `openrouter/*` routing aliases are refused. Catalog reads are bounded
   and show at most100 entries, explicitly incomplete; manual exact registration remains available
   if the catalog is larger than its metadata/network budget. Registration never implies online.

### Separately approved first real call

This task did **not** authorize or execute a paid probe. After choosing the real model/tag, the
owner must review the displayed bounds, provider-side key limit and the actual processing policy,
then explicitly authorize a single probe. “Aprob o verificare OpenRouter…” plus the probe button
authorizes one structured completion with at most64 output tokens, not a benchmark suite. With
4096 context and the default price ceilings, its conservative reservation is $0.004352. This is a
bound under the routing assumptions, not an asserted bill. Do not retry an uncertain call before
reviewing its durable state and provider billing.

Only a successful, current measured verification enables Research/Critic role assignment. Actual
OpenRouter availability, account credit, upstream compliance, structured-output support, TLS/DNS
deployment and latency remain unverified until that call succeeds. Unsupported routes must remain
unavailable. A registry entry, catalog listing or healthy worker is not verification.

For the first Research request, use a short nonsecret question and approved documentation context;
select Research, explicitly allow remote processing and the per-request cloud cost. The default UI
4096 context/768 output reserves $0.007168 at the stated ceilings. Review the immutable queued job
and unverified structured output. Repeat separately for Critic. Using a Research artifact as Critic
context can require additional account-associated remote-context permission and fresh source-access
checks; it is not authorized just by selecting the role. Campaign requests obey the same boundary;
8192 context/768 output would exceed the default $0.01 request bound at those ceilings and must be
explicitly resized or reauthorized, never silently expanded. No trading approval is produced.

## Verification ledger

Exact command records and unmodified local logs are in `.cache/openrouter/`. Sanitized durable
summaries are in `docs/openrouter-evidence/2026-10-28/`. Provider HTTP is synthetic in tests below;
PostgreSQL, Redis, MinIO, migrations, encryption, scoped identities and durable workers are real.

- `make check`: final run passes283 Python and153 frontend tests, Ruff formatting/lint, strict
  mypy and production TypeScript/Vite build. Exit0. Build retains the existing >500kB chunk warning
  and Starlette's TestClient deprecation warning; neither is hidden or suppressed.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`: exit0; **7 before +7 after
  restart**. Empty/operator-off setup, independent consent, synthetic measured Research/Critic,
  encryption/no readback, scope/CSRF/RBAC, restricted SQL, atomic budget/idempotency, key/policy
  revocation, no automatic provider retry and explicit error recovery.
- `make integration-services`: exit0; **107 before +107 after restart**. Full existing research,
  risk, identity, AI/campaign and new cloud service regressions; disposable project cleanup passed.
- `make integration`: **exit2, FAILED** at its first read-only development infrastructure test.
  Redis/storage healthy; PostgreSQL readiness refuses source0009 versus retained schema0008. The
  later independent `integration-services` success does not turn this target into a pass.
- `make contracts-check`: exit0. `make smoke-demo`: exit0, against the retained deployed API;
  this is not deployment or OpenRouter readiness evidence. `make ai-check-deployment`: exit0,
  effective configuration only. Operator helper preview: exit0, REVIEW_ONLY.
- `make secret-scan`: exit0, no leaks found in Git-selected source/evidence.
  `make repository-check`: exit0, all19 sensitive-path exclusions pass. `git diff --check`: exit0.
  `npm --prefix apps/web run test:e2e -- --list`: exit0,26 cases in11 files. Collection is not
  browser execution. No accepted snapshot was changed.

Intermediate failures are retained: initial integration test fixture attempted a prohibited second
OWNER (422); a subsequent fixture helper signature mismatch caused fail-closed worker failures.
Both fixture defects were corrected, without changing production permission checks or expected
assertions. Initial lint/import/line-length failures were repaired before final checks. Focused and
full final service reruns passed; no test was skipped or weakened to obtain acceptance.

### Browser and manual gate

**BLOCKED:** managed browser policy explicitly denied the localhost origin earlier in this session
and prohibited alternate/indirect access. No CLI/CDP/alternate-port workaround was used. Source/SSR
tests are not interaction, visual or accessibility acceptance. Owner-local regression commands:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

The existing26 desktop/mobile scenarios use synthetic private transport, not real OpenRouter.
Separately check this new cloud flow manually: empty prerequisites; operator-disabled state;
policy-read error/retry; switching private/public destination clears consent; missing key; invalid
credential validation with no reflection; unavailable catalog/model; one explicitly approved real
probe; Research/Critic assignment; budget refusal; policy/key revision and recovery. Protect secrets
from captures, trace and DOM artifacts. Preserve reviewed goldens; no snapshot rewrite is authorized.

## Remaining gates

Local schema/readiness and campaign startup were subsequently verified in the follow-up below.
Browser/manual cloud UX acceptance;
separate minimal-cost real provider authorization and measurement; reviewed data-processing rights,
retention/residency and a restricted provider key. Existing real-data, real-model campaign evaluation,
V1 visual acceptance and production secret-manager/backup gates remain open. No financial result,
model capability, paper/live eligibility or external execution is inferred from fixture success.


## Follow-up: campaign container startup repair — 2026-10-28

The owner executed the upgrade and reported Compose failing with `campaign-worker exited (1)`.
Actual container logs identify `/app/.venv/bin/python: No module named scripts.campaign_worker`.
The image was built successfully, but the shared control Dockerfile's explicit scripts COPY list
omitted the campaign entrypoint. Compose's command was correct. This fails before configuration,
database, MFA or model processing, and is unrelated to OpenRouter availability or cloud approval.
An isolated `docker run --network none ... -m scripts.campaign_worker --help` reproduced exit1
against the original image. Host-source tests had not exercised the packaged entrypoint.

The Dockerfile now includes that one script and runs its `--help` as a build-time regression gate.
The gate imports real packaged dependencies but starts no worker and requires no credentials or
provider calls. No broad scripts copy or change to the separate AI image allowlist was introduced.
A second image smoke test passed as the image's non-root user with network disabled, read-only
filesystem, all capabilities dropped and no-new-privileges.

Only the campaign image was rebuilt and its service recreated with `--no-deps --no-build --wait`.
The worker is healthy, its heartbeat is fresh and an actual read-only query through its configured
runtime identity confirms `SELECT 1` and schema `0009_openrouter`. Container IDs prove every other
service was left untouched by this repair; PostgreSQL/Redis/MinIO named-volume identities are
unchanged. The owner's preceding upgrade—not this repair—applied migration0009. Earlier pending
schema/deployment statements above describe the preceding implementation run and are historical.

Exact verification records are under `.cache/openrouter/`, labeled `campaign-*` and `startup-*`:

- Original image entrypoint: exit1, missing module (expected reproduction).
- Default build attempt: exit1 because this managed session cannot write Buildx activity under
  `~/.docker/buildx`. No permission was relaxed. The retry used Docker's supported `BUILDX_CONFIG`
  to store client build state under writable ignored `.cache/openrouter/startup/buildx` and passed.
  See [Docker build configuration](https://docs.docker.com/build/building/variables/#buildx_config).
- Corrected campaign image build, including packaged entrypoint gate: exit0.
- Corrected no-network/non-root image smoke: exit0.
- Targeted service start/readiness: exit0; campaign-worker running/healthy.
- `make check`: exit0;283 Python +153 frontend tests, lint/types/production build.
- `make smoke-demo`: exit0, current deployed API.
- `make ai-check-runtime`: exit0, actual restricted container SQL/Redis/network boundaries;
  `actual_model_inference` remains false. No inference request was sent.
- Full `make integration`: **exit0**,452.824s. The retained development infrastructure check passes;
  all107 disposable service tests pass before and all107 after graceful restart; final deployed API
  and execution-denial smoke reports readiness200. This resolves the earlier exit2 schema failure
  without weakening its assertion or altering development volumes.
- `make contracts-check`, `make secret-scan`, `make repository-check`: exit0. `git diff --check`
  passes. Fresh final checks are recorded in the startup evidence package.

Owner-local reproduction of this repair, without touching dependencies or volumes:

```sh
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up --build -d --no-deps --wait --wait-timeout 60 campaign-worker
```

No OpenRouter API key was entered or read, public inference submitted, accepted visual reference changed, trading
capability activated or new development phase started. Real OpenRouter/model and browser acceptance
remain separate gates.


## Subsequent risk-monitor dependency interruption — 2026-10-28

The owner's following rebuild recreated PostgreSQL while risk-monitor was already polling. Actual
connection-refused logs and container timestamps distinguish this from the earlier campaign image
omission. The fixed risk daemon now uses bounded transient reconnects, readiness withdrawal and
repeated restricted-identity checks; policy/financial logic is untouched. Only the risk service was
recreated and its local health is verified. See [RISK_MONITOR_RECOVERY_REPORT.md](RISK_MONITOR_RECOVERY_REPORT.md)
for the real connection-loss regression, exact results and preserved-volume evidence. No provider
call or cloud-consent change was made by this repair.
