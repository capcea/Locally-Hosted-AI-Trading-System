# Phase 6 — private AI gateway architecture

Updated 2026-10-28. This is proposal-only infrastructure, outside every trading capability.
SIMULATED/DENY_ALL and the generated-code refusal remain unconditional. Phase 7 agents are absent.
See [acceptance and current blockers](PHASE6_COMPLETION_REPORT.md).

Historical Phase6 descriptions retain their original private-only scope. Phase7A now adds bounded
owner-reviewed campaign handoffs. This OpenRouter exception changes neither their authority nor
their requirement for explicit authenticated authorization.

## Explicit OpenRouter cloud exception — 2026-10-28

Migration0009 adds immutable cloud authorizations and spend reservations plus encrypted revisioned
connection keys. Default OFF: operator `AI_OPENROUTER_ENABLED`, exact proxy allowlist, owner-MFA
cloud authorization, connection processing consent and per-request cost acknowledgement are all
required independently. Private approval cannot authorize cloud processing.

The compatible adapter uses fixed HTTPS `/api/v1` paths, exact model/upstream identifiers, verified
TLS, no redirects/ambient proxies, strict ZDR/no-training/price routing and no automatic public
fallback or retry. The CONNECT proxy's only DNS exception is `openrouter.ai:443`; it rejects any
nonpublic answer and connects a validated literal. Worker network isolation is unchanged.

API writes encrypted credentials; only the restricted AI identity reads its AI-only ciphertext and
decrypts for approved transport. No plaintext-key readback, prompt field, model tool, arbitrary URL
or generated-code execution exists. Authorization/credential revisions are pinned to verification,
requests and campaign model context. Publication rechecks those revisions.

Atomic Decimal reservations conservatively bound requested input/output under reviewed maximum
prices, alongside original quotas. Failed/unknown attempts retain reservations and never retry
automatically. Reservations are not a billing guarantee; provider-side key caps are required.
Actual public TLS/DNS, model inference and cloud UX acceptance remain unverified. See the
[integration report](OPENROUTER_INTEGRATION_REPORT.md) for limits, evidence and setup gates.

## Components and authority

- `apps/api/ai/`: existing full-MFA session, CSRF and owner/recent-MFA mutations. API-only context
  broker reads scoped, minimized research summaries. It never calls an inference provider.
- `packages/ai/contracts.py`: bounded versioned questions, hypotheses, summaries, critiques,
  missing-evidence reports, inert code suggestions and response metadata. OpenAPI/TypeScript publish
  these contracts. Code suggestions are text; no import, compiler, shell, tool dispatcher or runner exists.
- Registry: operator allowlisted endpoint IDs; immutable owner-scoped connection/model/role versions;
  worker-measured, expiring capability records. A registry entry is not a connectivity claim.
- Worker: separate `research_ai` PostgreSQL identity, AI-only Redis ACL, separate AI content key,
  whitelist-only image, no API/auth/risk/research implementation, no deployment or broker credentials.
- Providers: fixed adapter registry implementing `InferenceProvider`. Ollama NDJSON and compatible
  SSE are separate protocols. Unsupported controls refuse explicitly. No silent public-cloud fallback.
- PostgreSQL is authoritative. Redis provides bounded wakeups and short-lived worker observation,
  not durable ownership or proof of GPU readiness. Dedicated AI Redis may lose all hints safely.

## Request lifecycle

1. Owner authenticates and confirms MFA within five minutes. Privacy/rights acknowledgements and
   explicit remote policy are required. Context is selected by finite typed references, never SQL,
   filesystem paths or arbitrary URLs. Free text must not contain secrets.
2. Owner-row locking serializes quotas and idempotency. The immutable request pins prompt version,
   endpoint configuration digest, exact model/verification/role version, parameters, context hashes,
   policy and session. Same key/same request returns its original job; changed payload conflicts.
3. Temporary inputs are encrypted with the separate AI key. Metadata/audit omit question/output
   bodies and credentials. Parent request is flushed before job/content foreign-key inserts.
4. Worker claims a PostgreSQL lease with a unique fencing token, bounded global slots and fresh
   session/owner authorization through a boolean security-barrier view. It cannot SELECT users.
5. The worker independently rechecks enabled connection, endpoint digest, verification expiry,
   model identity/digest when reported, budgets, cancellation, deadline and authorization.
6. A dispatch marker precedes inference. Only known refusal/unconnected failures can retry, up to
   three attempts with bounded backoff. Configured alternatives are used only after explicit request
   permission. Ambiguous completion, lost dispatched lease or SIGKILL recovery becomes UNKNOWN,
   never automatic resubmission. Exactly one immutable final artifact is permitted.
7. Partial assistant JSON can be streamed as **unvalidated**, encrypted temporary content. Provider
   reasoning/thinking channels are discarded. `<think>` content, tool calls, excessive bytes,
   incomplete streams, invalid schemas, duplicated fields and invented references are refused.
8. Independent parsing requires exact version/boolean types, bounded schema fields and supplied
   reference IDs. A valid shape does not make the model's statements true. The output always denies
   verification, executable-code or strategy-certification authority.
9. Cancellation is a request until the worker acknowledges it. Publication rechecks the fencing
   token, cancellation, authorization and expiry transactionally. Closing HTTP does not prove that a
   remote GPU stopped computing; this uncertainty is shown.

## Storage, limits and read paths

Alembic `0007_ai_gateway` adds nine `ai_*` tables, immutable triggers, constrained mutable state and
the boolean request-authority view. Destructive development downgrade/reset is not used.

Defaults: two global worker slots, 40 owner requests/hour, 20 per role/hour, eight pending jobs,
1,000 metadata records/owner, 12,000 input bytes, 24,000 output bytes, 180 seconds maximum inference.
Provider-reported context is capped at the approved ceiling and 32,768 tokens; output at 4,096.
Input budgeting uses a deliberately conservative byte bound plus output/overhead, not a claimed exact
tokenizer. Actual usage is reported only if supplied by the provider. Price estimates require explicit
rates and actual usage; otherwise cost is unknown. GPU/VRAM availability remains unknown.

Input/partial retention is bounded by policy and five-minute MFA authorization; structured output
retention is 1–24 hours. Worker sweeps expired ciphertext. If the worker is down physical erasure is
delayed, but API expiry checks still hide output. Owner content erasure is available immediately;
metadata is immutable. Backup retention/key rotation and metadata archival need operational policy.

`GET /requests/{id}/wait` offers a bounded synchronous read of durable queued execution (0–15s);
it does not run an LLM inside the API. SSE is bounded to 30s, one stream per owner, with rechecked
session revocation and no-store headers. Both release authentication row locks before waiting, so
cancellation and safety actions stay reachable. The initial UI polls durable job state, not partial
unvalidated text. Reloadable job links are `/testeaza/ai/{id}`.

## Research context and final holdout

Allowlisted sources: reviewed strategy definitions, completed non-final experiment metrics, dataset
quality metadata and two static reviewed documentation excerpts. No raw market rows, broker tokens,
risk signing keys, arbitrary files or internet retrieval tools are provided. Account IDs are disclosed
only as explicit minimized context; remote account context requires its own approved profile policy.

Existing sealed-dataset checks include overlapping aliases. AI artifact retrieval recursively
revalidates original references and hashes; stored response reads hide content after access is lost.
An owner-scoped advisory lock prevents sealing during active inference; sealing cancels queued AI
work and purges its cached input before admitting the seal. It conservatively affects all owner AI
jobs. Previously exposed data is **not** certified untouched: the existing prior-exposure UNKNOWN
attestation remains. AI cannot release a holdout or substitute for the separate authorization.

## Reproducibility limits

Artifacts retain provider/model/digest when available, reported server version/quantization,
verification snapshot, prompt version, sampling/seed settings, input reference hashes, actual times,
latency, usage and output SHA-256. Inputs are deliberately temporary. This supports provenance and
comparison, not perfect regeneration after retention expiry or deterministic GPU inference. Seed
acceptance is not proof of identical results. Real model evaluation is currently blocked.

Optional AI settings/key-file errors or reuse of the identity key disable only the AI gateway with
`AI_CONFIGURATION_INVALID`; they do not prevent mounting authentication or owned-account safety.
This is verified with actual full-MFA sessions and the independent safety route.


## Phase 7A integration

Campaign Research/Critic calls reuse the existing request API and strict inert output schemas. An
authenticated owner must hand off each request under recent MFA and processing/retention consent.
A campaign selects at most8192 context tokens, bounded by the exact approved model's measured
capability; the existing byte-conservative prompt budget can still refuse oversized evidence. There
is no context-limit bypass, automatic synthetic fallback or model tool authority.

Migration0008 extends `ai_request_authority` with linked campaign deadline/cancellation checks. The
inference role still reads only the existing boolean view, never campaign/account tables. Explicit
coordinator cancellation also reaches the existing AIJob; unacknowledged/UNKNOWN inference prevents
false campaign cancellation confirmation. Expired structured output cannot be accepted. Campaign
source/policy/context revalidation precedes owner acceptance; final holdout remains excluded.
Real AI campaign inference is unverified while no actual configured runtime is available.
