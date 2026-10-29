# Threat model — Phase 6 follow-up

Phase6 adds untrusted model content, temporary research context and private inference credentials.
The inference worker receives only AI-scoped SQL/Redis/content-key identities and preauthorized
minimized context. It cannot read identity/research/risk tables or execute generated code. Actual
native grant/ACL/refusal/fencing/holdout tests pass; model semantics, deployed remote network isolation and
browser acceptance have separate open gates. Read
[AI_SECURITY_BOUNDARIES.md](../AI_SECURITY_BOUNDARIES.md) for controls and residual risks.
The following existing control-plane threat assumptions continue to apply.

Assets include passwords, encrypted MFA seeds, recovery/session hashes, private bootstrap/HMAC keys,
account/policy/risk metadata, audit integrity, local service credentials and source/lock integrity.
The current deployment trusts the local host owner and Docker/database administrators. It is not
approved for shared/public exposure. No broker credentials or trading authority exist.

## Controls implemented and tested

- Accidental execution: configuration rejects LIVE/DEMO, permissive capabilities and generated-code
  execution. Independent order/worker denials remain. API activation/order routes return 403.
- Account takeover: Argon2id (64 MiB, three iterations, parallelism one), generic login rejection,
  mandatory TOTP with persisted replay counters, rate limiting, one-use recovery after password
  verification, forced reenrollment and revocation. No email/SMS recovery fallback exists.
- Browser forgery/session theft: opaque hashed sessions, expiry/idle timeout, rotation/revocation,
  HttpOnly/SameSite cookies, exact Origin validation plus HMAC CSRF for mutations. Session secrets
  never enter localStorage. TLS/Secure cookies are mandatory before any non-loopback deployment.
- Unauthorized records: OWNER/OPERATOR/VIEWER checks, user partitions and composite foreign keys,
  immutable scope references, revision conflicts and recent MFA for owner-sensitive changes.
- Audit rewriting: append-only grants and triggers, serialized HMAC chain/head, transactionally
  coupled mutations and failure rollback tests. An administrator mutation is detected by verification.
- False policy permission: only manually attested version/source/scope metadata; changed scope,
  latest unverified version, missing/expired policy fail closed. Trading remains disabled regardless.
- Secret leakage: private 0600 .env, excluded build context, restricted API DB role, metadata-only
  broker schemas, URL credential/query rejection, no raw request body/URL in API logs, sanitized
  422/409/503 responses and no-store headers. MFA seed/recovery codes are deliberately returned only
  during enrollment to the authenticated user, not stored in audit records or browser traces.
- Supply chain: pinned locks/images/Actions, local dependency and source scans. Actual remote CI and
  container vulnerability scanning are distinct evidence requirements, not inferred from a build.

## Residual risks and required future work

The backend, its encryption key and database administrator remain trusted. A compromised process
holding both DB write access and the HMAC key can construct valid malicious events; no independent
anchor exists. Session/rate/audit retention and abuse/volumetric load defenses need operational work.
The audit-head and per-user locks favor correctness over throughput; sustained-load limits are unmeasured.
Recovery codes must be stored privately by the owner. Losing the encryption key can strand MFA,
recovery and audit verification; key rotation/restore is not automated. No WebAuthn exists.

Redis is unauthenticated on loopback/internal networks; MinIO still uses development identities.
TLS, reverse-proxy identity/rate architecture, secret-manager integration, off-host encrypted backups,
full restore, production incident response and independent penetration testing remain deployment gates.
TOTP is not phishing-resistant. App DB privileges do not protect against a malicious host owner.

No live permission, actual firm policy, quote, calendar, broker capability or strategy performance
has been verified. No research code runs. A future sandbox needs VM/microVM isolation, constrained
network/filesystem, immutable inputs and quotas, tested against escape/exfiltration. A future executor
must independently enforce signed scope, risk, idempotency, reconciliation and durable kill state.

## Phase 2 data threat boundary

Uploads are untrusted data, never executable Python/pickle/strategy source. Input/body/row/cell/Parquet
sizes and query scans are bounded. Worker/API containers have memory/CPU/tmpfs limits, and data reads
and worker claims each have two concurrency slots. Providers use a static trusted adapter registry;
ECB has a fixed HTTPS allowlist and no redirects, and user rights URLs are never fetched as endpoints.
Declared source clocks/rights still require trustworthy evidence. Checksums prove byte integrity,
not factual prices or licensing. Parsed data cannot enable orders or generated-code execution.

S3 version IDs, COMPLIANCE retention, restricted storage grants and manifest hashes protect published
artifacts; SQL triggers protect metadata. Root provisioning is isolated from API/data-worker config.
Existing host-admin/secret-manager/backup limitations still apply. Malformed native-parser inputs can
exhaust their bounded worker and retry; production hostile-input/parser and sustained-load testing
are not certified. Unreachable retained objects need a deliberate capacity/retention process. An
as-of source sequence cutoff is necessary when replaying part of a shared availability instant.

## Phase 3 execution and broker trust boundary

The synthetic engine accepts bounded typed data only; no generated code is loaded or executed.
All external execution remains denied in config, legacy/new API routes, adapter methods and bridge
transport allowlists. Future risk contracts have false authority fields. Presence of a demo account,
token, LLM response, signed observation or frontend command cannot authorize an external order.
Primary API and market-worker images exclude bridge source/MT5 SDK; neither receives broker secrets,
admin database/MinIO root credentials or Docker socket mounts. No research execution environment is
present, so hostile-code sandbox acceptance remains NOT IMPLEMENTED.

Observation signatures prove possession of the pinned connector key, not that the connector/venue
reported factual prices. A compromised authorized connector could lie about read-only observations;
observations do not grant tradability/risk authority. Owner recent MFA pins identity; SQL prevents
repinning account/server/provider/key. Signature/identity/age/sequence mismatches, gaps and changed
order/position truth fail closed or raise uncertainty/incidents. Fixtures stay explicitly fixtures.

The bridge requires client certificates plus bearer identity, uses only loopback and bounds bodies,
concurrency, SDK process lifetime and memory. OAuth callback instead requires client certificate and
one-use state. An owner must provision/revoke certificates, token encryption keys and Windows ACLs.
MT5 investor/demo/terminal checks and cTrader verified VIEW scope/demo account checks are additional
application controls, not external service certification. SDK/service accounts remain trusted fixed
code, not a sandbox for AI output. Actual Windows isolation and external revocation/reconnect tests
are BLOCKED. The optional image currently shares the full runtime lock, not a minimized connector SBOM.

Journal rows/commands/observations have immutable triggers/grants and hash-chain/snapshot validation;
HMAC audit commits with mutations. Concurrent duplicates and real process kills are native-tested.
UNKNOWN cannot be cleared by blind retry. Host/DB admin compromise with application secrets remains
outside these protections; independent anchoring, production abuse/load tests, key rotation/restore,
external transport deployment and actual connector credentials are still operational gates.

## Phase 4 risk boundary

Every durable simulated entry is gated under an account lock and exact immutable policy/profile/
context bindings. Fresh fill validation, proportional allocation ceilings and consumed signed grants
protect against TOCTOU, replay and competing strategies. Denied/indeterminate decisions persist;
UNKNOWN retains budget. Journal and risk ledger integrity failures stop admissions and do not invent
trusted balances. A hypothetical request cannot create an execution grant or change the emergency flag.

All risk configuration/attestation/STOP/CLEAR/FLATTEN actions reuse authenticated owner/recent MFA,
CSRF, scope and HMAC audit. Material configuration forces review. Policy content, authorizations,
consumption, contexts, decisions, profile versions, ledger and emergency receipts have SQL immutability
and restricted runtime grants. Separate STOP and FLATTEN prevent misleading claims of position closure.

The fixed-code risk-monitor has restricted DB/HMAC credentials but no broker keys, root storage/admin
identity, Docker socket, generated-code runtime or outside network. The current API/gateway still share
trusted host/key authority; this is not protection from a malicious host administrator or a fully
compromised trusted API process. Future separate executor/signing keys, credential isolation, external
anchoring and broker capability checks remain mandatory before any external execution work. No sandbox
is claimed: generated code remains prohibited. User-provided financial/calendar attestations are
untrusted facts that must be reviewed; signatures/checksums alone do not establish factual market truth.

Main deployment preserves local loopback-only publications. The risk monitor has none. Container
resource limits/read-only roots are defense in depth, not hostile-code certification. Actual native
multiprocess/SIGKILL/restart tests prove the specified synthetic transaction invariants, not production
throughput or external exactly-once order delivery. Browser launch restrictions are preserved.
