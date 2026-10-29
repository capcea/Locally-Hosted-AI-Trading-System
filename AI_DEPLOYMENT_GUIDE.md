# AI deployment guide — private default and explicit OpenRouter exception

Updated 2026-10-28. No GPU has been rented, account connected, model downloaded or broker credential
introduced. SIMULATED/DENY_ALL remains unconditional. Current blockers and evidence are in
[PHASE6_COMPLETION_REPORT.md](PHASE6_COMPLETION_REPORT.md).

## Campaign image startup correction

If the upgraded stack reports `campaign-worker exited (1)` and its log says
`No module named scripts.campaign_worker`, use the current Dockerfile: the original explicit copy
list omitted this entrypoint. The corrected image includes it and tests packaged `--help` during
build. A targeted rebuild retains all data and avoids recreating dependencies:

```sh
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns up --build -d --no-deps --wait --wait-timeout 60 campaign-worker
```

This repair was actually rebuilt, started and observed healthy locally; no volume reset is needed.
The owner has now upgraded the database to0009. Earlier pending-upgrade statements retain their
historical scope. Read the [startup evidence](OPENROUTER_INTEGRATION_REPORT.md#follow-up-campaign-container-startup-repair--2026-10-28).
No provider inference was performed.

## Current OpenRouter follow-up

The private-only default remains. Public inference is disabled unless both the operator and the
authenticated owner independently authorize `openrouter-public-v1`. The fixed destination is
`https://openrouter.ai/api/v1`; choosing PRIVATE_OPENAI or approving private remote processing is
**not** cloud consent. Full existing-installation upgrade/UI instructions and evidence are in
[OPENROUTER_INTEGRATION_REPORT.md](OPENROUTER_INTEGRATION_REPORT.md).

Current read-only inspection found development schema0008, zero approved endpoints, zero connections
and zero models. The new source requires0009. Earlier installation paragraphs below retain Phase6
history; this follow-up has **not** migrated, rebuilt or enabled the development stack. Existing
`.env.ai`/content key must be retained, not regenerated. The operator helper defaults to review-only:

```sh
.venv/bin/python -m scripts.configure_openrouter
```

After backup and explicit policy review, follow the report's normal migration, restricted-grant
refresh and Compose upgrade sequence. No volume reset is required. The helper changes only the
operator flag and exact `openrouter.ai:443` proxy exception; it does not insert an API key or call
the provider. Enter a separately limited inference key only in the write-only authenticated UI.
Saving setup/model metadata does not verify a model. A real probe/request can incur charges and
requires separate explicit approval; none has been executed here. Worker isolation, TLS/validated
DNS and refusal of arbitrary URLs/redirects remain.

Private endpoint secret mounts and migration to a dedicated private workstation remain supported.
Disable cloud connections/operator opt-in when retiring public inference; reconcile dispatched
requests first, since disabling a route cannot prove remote computation stopped. Model/policy/key
revisions require re-verification and fresh scoped handoffs, not automatic migration of approval.

## Existing development installation

The ordinary application is healthy on `http://127.0.0.1:5173`. Additive migration0007 is applied;
PostgreSQL/Redis/MinIO data mounts are retained. A private pre-migration dump is under
`.cache/phase6/backup/`; never commit it. The AI-only identity and `.env.ai`/`.secrets/ai` were prepared
once. **Do not rerun setup over these files or replace the key.** No real model is configured.

The optional AI overlay is now running locally: AI worker/Redis and API are healthy; the constrained
proxy is running. No inference endpoint/model is configured and proxy egress defaults to denied.
Initial secret-bind creation was delayed, interrupted operations caused a transient stateless API-name
conflict, and dedicated Redis then failed with `chown: .: Operation not permitted`. Recovery retained
all persistent mounts. Redis now runs directly as its pinned image's UID999/GID1000, with its own
owned tmpfs; no dropped capability was restored. API and worker use disjoint queue networks, with
only Redis bridging the two client networks. Actual running-container tests verify SQL/Redis scope,
blocked API/metadata/public TCP and denied unapproved proxy CONNECT, including after queue restart.
Docker29.7.2/Compose5.5.0 work. The initial delay's host cause is unconfirmed; no managed permissions
were disabled. Historical failures remain in the ledger rather than being relabeled successful.

Owner-local reproduction/acceptance is:

```sh
cd '/Users/andy/Documents/ChatGPT/Sistem Trade Ai'
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml \
  --profile ai up -d --build --wait --wait-timeout 180 ai-redis ai-egress ai-worker api
make ai-check-deployment
make ai-check-runtime
```

Never print `docker compose config` with production values; the check script inspects effective
configuration internally and prints only boundary summaries. Do not run `down --volumes`, prune or
reset development data. Starting the overlay may recreate the PostgreSQL container to add its private
network; the persistent mount must remain unchanged. Take a verified backup first and allow existing
workers to reconnect/restart. Do not present service health as trading or model authorization.

## Fresh local preparation

First complete the existing bootstrap/identity/market setup and normal stack health checks. Back up
the database and immutable storage. Then `make ai-setup` applies additive migrations and creates a
separate AI PostgreSQL role, content key and queue identities. It refuses overwriting existing AI
configuration. Migrations use an administrator identity; the API/worker do not receive it.

`.env.ai` is mode0600. `.secrets/ai` is mode0700 and its read-only mounted files mode0644 inside that
private parent, allowing the unprivileged container to read its own key/ACL. Keep the parent private
and owner controlled. No secret file enters Git/build context. Rotating this key without a reviewed
data migration makes existing encrypted content unreadable. Host/Docker administrator access is
trusted; use a real secret manager before multi-user/public deployment.

The overlay starts no inference server. Its default `AI_ENDPOINTS=[]` and egress allowlist deny all
inference. Dedicated AI Redis is deliberately nondurable: requests remain durable in PostgreSQL,
and missed wakeups recover by polling. Its scoped ACL file is reloaded on every restart. No Redis
port is published. Worker has no control/frontend/execution network or trading/auth secrets.

## Local Ollama or future private workstation

Use an already installed, owner-reviewed runtime/model; no automated model pull is included. Check
its cloud forwarding is disabled and attest private-only processing. In `/setari/ai`, discover actual
models, register their exact names, run real probes, then choose a model independently for each role.
Choose supported model capabilities from measurements, never from family names or marketing.

For the isolated worker, attach the owner's inference container only to `ai_inference` with an
operator-selected literal address, for example `172.30.63.2:11434`. Keep its port unpublished and
default internet egress disabled; no model downloads are performed by the worker. Ensure the
172.30.61–65 subnets do not overlap the host/VPN before creating them. Configure the exact origin as
an endpoint with `PRIVATE_CONTAINER` and `private_only_attested:true`. Example configuration data:

```json
[{"id":"local-private","label":"Model local privat","url":"http://172.30.63.2:11434",
  "transport":"PRIVATE_CONTAINER","private_only_attested":true}]
```

For explicitly trusted host-side development, `LOOPBACK` can point to `http://127.0.0.1:11434`.
Container loopback means the worker itself, not the host. Do not replace it with a broad host-gateway
or join control networks. Host-side worker execution lacks the container's network isolation and is
not production isolation acceptance. Gateway settings deliberately do not read the application's
`.env`; supply only the separate AI database/queue/key/allowlist configuration to that process.

## Private remote GPU / Vast-style portability

No remote instance or cost is authorized by this implementation. Before using an owner-provisioned
host, review jurisdiction, confidentiality/licensing, endpoint ownership, cloud-off configuration,
compute quotas, exact model/digest and monitoring. Use either:

- A protected owner SSH tunnel bound only to loopback. Check SSH host identity. Configure a
  `SSH_TUNNEL` endpoint and approve remote processing even though the application sees loopback.
  A tunnel must terminate in the inference namespace or use the explicitly trusted host-only setup;
  the isolated Compose worker cannot access an arbitrary host tunnel implicitly.
- Authenticated HTTPS with a certificate valid for the pinned literal IP, using scoped bearer token
  or mTLS and verified CA/server identity. No DNS rebinding or verify-false option exists. Endpoint
  secrets are read only from logical `/run/secrets/ai-*` mounts. Add only the specific mounts to the
  worker overlay; never mount a whole secret directory. API needs endpoint metadata, not token files.
  Configure exact remote IP and443/8443 in `AI_EGRESS_DESTINATIONS`. The CONNECT proxy has no
  credentials and no unrestricted HTTP route. Missing allowlist defaults to denial.

Network isolation and host administration must be verified on the deployment platform. The template
alone is not firewall proof. No unauthenticated public Ollama port is acceptable. Do not transmit
licensed/account context unless owner profile policy and per-request permission explicitly allow it.

## Acceptance and operations

With only authorized AI environment values set, probe an existing real model:

```sh
.venv/bin/python -m scripts.verify_ai_runtime --endpoint local-private \
  --provider OLLAMA_NATIVE --model EXACT_ALREADY_INSTALLED_MODEL --run-evaluation
```

The endpoint ID must already exist in `AI_ENDPOINTS`; replace the name with an actually installed
model. This command performs inference and needs an explicit private-only operator configuration.
It neither downloads models nor reads financial holdouts. Review the real result, unknown metadata,
latency/usage and unsupported capabilities. `/api/v1/ai/status` requires full MFA; heartbeat is not
GPU readiness. `/health/ready` describes infrastructure and does not enable AI/trading.

Then owner-local browser acceptance, without rewriting snapshots:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=ai make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
make check
make integration
make contracts-check
make smoke-demo
make secret-scan
make repository-check
```

The AI browser scenario uses real disposable services and a **synthetic HTTP transport fixture**,
not Ollama. The current26 desktop/mobile cases must pass; real-model acceptance is a separate gate. Trace,
automatic auth screenshots and secret DOM snapshots remain disabled. Intentional visual differences
need actual inspection and owner review, not automatic reference updates. Managed browser execution
remains prohibited here; do not use these commands in the managed session to bypass that restriction.

Stop only optional AI services with the same overlay and `stop ai-worker ai-egress ai-redis`; do not
remove volumes. Requests already dispatched may become UNKNOWN; never assume provider cancellation.
If removing the optional overlay from the API, recreate API with the base Compose configuration and
`--no-deps`; do not reset PostgreSQL. Back up encrypted AI content/metadata together with a separately
protected key, rehearse restore and decide retention/archival/key rotation before production use.
Off-host backup/restore, paid cost accounting, actual GPU quotas and production exposure are open gates.

## Official references inspected

- [Ollama chat/structured streaming](https://docs.ollama.com/api/chat)
- [Ollama OpenAI compatibility subset](https://docs.ollama.com/api/openai-compatibility)
- [Ollama operational/context FAQ](https://docs.ollama.com/faq)
- [Official Ollama OpenAPI source](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml)
- [Vast private SSH access](https://docs.vast.ai/guides/instances/connect/ssh)

Accessed during Phase6 implementation on2026-10-28. `/api/show`'s separate web-doc page returned404;
the official OpenAPI source was used. These references do not establish any real deployment result.
