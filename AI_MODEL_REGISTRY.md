# AI model registry and role routing

## OpenRouter follow-up — 2026-10-28

The private default remains. Public OpenRouter requires a separate operator/owner cloud policy;
fixed destination registration precedes connection, write-only key and exact `author/model`
registration. Registering or discovering a model never marks it online. An actual bounded structured
probe, current policy/key revision and unexpired measured verification are needed for Research or
Critic assignment. Automatic router aliases/fallbacks are refused. Catalog listings are bounded,
explicitly incomplete and never invented. Source tests pass; actual public inference and browser
acceptance remain open. See [setup and evidence](OPENROUTER_INTEGRATION_REPORT.md).


Updated 2026-10-28. No real model has been discovered or verified in this environment.
`SYNTHETIC_HTTP_FIXTURE:1` appears only in explicit transport tests, never as a bundled AI capability.

## Setup order

1. Operator prepares isolated identities, encryption and approved endpoint configuration using
   [the deployment guide](AI_DEPLOYMENT_GUIDE.md). Browser requests cannot supply an endpoint URL.
2. Owner with recent MFA approves immutable connection policy, data rights, remote processing,
   account-context permissions and retention. Disabling a connection is separate from changing policy;
   changed policy requires a new connection record. Existing requests pin the old policy.
3. Discovery makes a real bounded HTTP request, through the worker. It does not download models.
4. Register the exact installed model name and an operator-reviewed context ceiling. It starts
   unverified. Probe actual structured streaming, identity/context, inert tool suggestions, reasoning
   controls and seed support. Verification expires after 24 hours.
5. Independently bind RESEARCH, CODING, CRITIC and LIGHTWEIGHT to verified models. One physical
   model may serve several roles; roles do not imply multiple agents or parallel GPU allocation.
6. Explicit alternatives must be distinct, owned, verified models (at most two). No alternative is
   used unless the submission permits it. Every remote candidate must also satisfy remote policy.

## Capability semantics

- Ollama native: `/api/tags`, `/api/show`, `/api/version`, `/api/chat`; NDJSON structured streaming,
  bounded `num_ctx`, `num_predict`, temperature/top-p, verified accepted seed and measured think-off.
- Ollama OpenAI compatible: uses Ollama identity metadata plus `/v1/chat/completions` SSE/schema.
  Native options are not silently mapped to compatible endpoints.
- Private OpenAI compatible: `/v1/models` and `/v1/chat/completions`; provider must actually expose
  context metadata and accept the bounded structured probe. A product name alone proves no parity.
  Unsupported/missing context or controls fail closed. Compatible seed/reasoning controls remain
  unavailable unless this adapter can verify their semantics; mere request acceptance is insufficient.
- Tool capability probes use a fixed inert nonce. Tool suggestions during ordinary analysis are
  refused. There is no dispatcher. Hidden reasoning is not exposed or stored.
- Cloud aliases and reported remote models are excluded. Operator private-only attestation remains
  necessary because a loopback server can itself forward traffic.
- Context/GPU distinction: a provider-reported context ceiling and an accepted small probe do not
  prove full-window token capacity, available VRAM, throughput or actual GPU execution.

Reported digest, quantization, server version and usage remain null when unavailable. Changed known
model digest, endpoint configuration, expired verification or disabled connection refuses inference.
The registry never certifies financial findings, permissions, prop-firm eligibility or performance.

## Main contracts and operations

All routes are `/api/v1/ai`: status, endpoints, connections, discovery, models, probe, role routes,
requests, bounded wait, stream, events, cancel and content erasure. Setup/probe/submission require
owner/recent MFA, all reads are owner scoped, unsafe routes retain Origin/CSRF. Other users cannot
read an owner's jobs merely because they have VIEWER/OPERATOR roles. No shared-account delegation
is introduced. OpenAPI and generated frontend contracts remain the exact API reference.

Advanced UI: `/setari/ai`. Analysis UI: `/testeaza/ai`. Empty/unverified/no-worker states explain what
must be configured. Actual real-provider and rendered browser acceptance are still open gates.
