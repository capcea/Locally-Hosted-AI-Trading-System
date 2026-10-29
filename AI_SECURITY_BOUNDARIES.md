# AI security boundaries — Phase 6

Updated 2026-10-28. SIMULATED/DENY_ALL. This is an inference transport worker, **not** a hostile-code
sandbox. Generated code remains prohibited. See the [completion report](PHASE6_COMPLETION_REPORT.md)
for tested boundaries versus deployment blockers.

## Current explicit public-cloud exception — 2026-10-28

Private processing remains the default. Historical literal-only restrictions below now have one
separately authorized exception: exact `https://openrouter.ai/api/v1`, operator opt-in and exact
`openrouter.ai:443` proxy allowlist, immutable owner-MFA cloud policy, explicit upstream/data-rights/
cost acknowledgements, connection consent and per-request cost approval. Private attestation never
substitutes for these. No default credential, provider model or automatic cloud fallback exists.

All DNS answers are validated before the proxy pins a global nonreserved address; mixed public/
private answers refuse. TLS CA/hostname checks, no redirects, byte/time/concurrency limits, internal
worker networks and no broker credentials remain. The proxy is credential-free. The trusted worker
reads only its encrypted AI key, decrypted in memory for fixed bearer-auth transport; model text
receives no key or database/tool authority. Host administrators remain trusted.

Policy/credential revisions invalidate measured capability and queued/in-flight publication. Public
partial responses are not persisted; known key patterns in prompt/context and exact credential
reflection in provider responses are refused. Keys are write-only through authenticated CSRF-protected
UI and encrypted by the existing separate content key; validation errors omit rejected raw input.

Immutable atomic reservations, no automatic paid retry/fallback and strict one-upstream ZDR/
no-training/max-price routing reduce exposure. They do not certify provider behavior or invoices;
the owner must set an independent low key spending limit. No actual paid call was executed;
public deployment/browser acceptance remains open. See
[OPENROUTER_INTEGRATION_REPORT.md](OPENROUTER_INTEGRATION_REPORT.md) for full limits and evidence.

## Trust and isolation

The API/auth/context broker and database/host administrators are trusted. Questions, imported data,
model responses and suggested source are untrusted. Prompt wording is supplemental; there is no
model-accessible SQL, shell, filesystem, URL fetch, policy mutation, approval or order tool.

The worker image copies only `packages/ai`, basic persistence schema/store definitions and its fixed
entry point. It excludes auth/governance/risk/research/execution application code, migrations,
deployment credentials, broker tokens and Docker sockets. Persistence model definitions contain
table schemas, not credentials or risk enforcement implementations. No model output is imported,
evaluated or executed. React escapes plain text; proposed source is displayed in a text `pre`.

`research_ai` can read AI records and a boolean session-authority view, insert immutable AI
artifacts/events/verifications and update only lease/job/ciphertext columns. It cannot SELECT users,
broker/research/risk tables, modify connections/policies, grant roles or access the identity/risk key.
Actual PostgreSQL permission-denial attempts are tested. API cannot insert its own model verification
or final artifact. Runtime cannot rewrite append-only request/registry/artifact/event records.

Redis ACL grants only bounded `ai:*` hints/heartbeat commands. Actual non-AI GET and CONFIG attempts
are denied. PostgreSQL remains authoritative when Redis hints disappear. API and worker use different
Redis users; dedicated queue ACL is reloaded from its scoped file on restart.

## Network and secrets

Endpoint origins are operator configured, pinned literal IPs with no userinfo/path/query/fragment.
DNS/rebinding, metadata/link-local/multicast/unspecified targets, trading/database/Docker service
ports, redirects and ambient proxies are refused. IPv4-mapped IPv6 addresses are normalized before
checks. Loopback/SSH HTTP requires explicit private attestation; private container inference belongs
on its own network. Remote inference requires authenticated TLS with certificate verification.
Bearer/mTLS/CA material is read only from scoped `ai-*` secret paths; symlink/traversal is refused.

The opt-in Compose overlay places the worker only on internal AI database/queue/inference/proxy
networks. It cannot join the control/frontend networks. A separate CONNECT-only proxy has an exact
literal-IP/443-or-8443 allowlist, no DNS/HTTP forwarding, no public ports, bounded bytes/time/slots and
no secrets. Default allowlist is empty. TLS server identity remains independently verified by HTTPX.
No broker/order executor is deployed on an AI network.

Local image/no-network execution, actual loopback HTTP/TLS/proxy refusal, effective Compose
configuration and running-container boundary tests pass. API and worker have no shared network:
Redis alone joins separate API-side and worker-side internal queue networks. Actual worker TCP to
all API interfaces, metadata and a public endpoint is denied; the proxy denies unlisted CONNECT.
These checks pass again after dedicated queue restart. They establish this local topology, not remote
firewall/GPU-provider acceptance or protection against a compromised host administrator. Initial
container-create delays and an API-name conflict were recovered; Redis startup's root chown failure
was fixed by running directly as its pinned non-root UID/GID with owned tmpfs and all caps dropped.

Separate AI encryption is mandatory; reuse of the identity/risk key is refused. Setup writes
`.env.ai` mode0600 and a host-private mode0700 `.secrets/ai` directory. Individual read-only container
secret files are mode0644 **inside that private parent**, so UID10001 need not run as root. Keep that
parent private; never copy these files to a shared directory. Build/Git excludes all runtime secrets.
Local administrator/Docker inspection can still observe service environment credentials; Docker
administration is trusted, not a defense against a compromised host administrator.

## Injection, data and privacy

Context selection is an API-only owner-scoped read allowlist. Remote processing and account context
need explicit policy plus per-request approval. No automated policy verification or final holdout
release exists. Sealed data, aliases and recursively cached summaries are refused. Sealing is fenced
against concurrent disclosure. Plaintext questions are encrypted temporary input, never ordinary
logs/audit. Raw model responses, hidden reasoning, provider error bodies and credentials are not
logged. Partial content remains unvalidated and is not shown as a final result.

Strict output parsing rejects duplicate keys, wrong exact JSON version/boolean types, extra fields,
wrong references, tool calls and reasoning markup. A validated schema cannot establish truth;
missing evidence and unverified status stay visible. Typed input minimization and secret-like string
refusal reduce accidental disclosure but cannot identify every secret a user might manually type.
Do not enter secrets; the gateway is not a universal DLP service.

Cancellation is acknowledged locally, not proof of remote GPU termination. Dispatched lease loss is
UNKNOWN, with no automatic duplicate. Quotas, deadlines, wire/line/body/output budgets, global slots,
MFA/session revocation and fencing protect publication. Worker SIGKILL and scoped database/Redis
denials are tested with disposable resources. No network grant authorizes real trading.

## Open acceptance and residual risks

Real installed-model behavior, remote endpoint ownership/cloud-off configuration, real GPU quotas,
deployed network/firewall rules, encrypted backup expiry/key rotation, metadata archival, formal
prompt-injection model evaluation and production multi-tenant hardening remain unverified. A hostile
provider can lie about capabilities/usage or produce plausible false statements. Trusted provider
and administrator compromise are not solved by prompt restrictions or Docker alone. Owner browser
acceptance/manual accessibility and current intentional visual references require separate evidence.

Malformed AI environment, unreadable key files and identity-key reuse fail closed by disabling AI
only. They cannot take authenticated safety offline. The fallback uses trusted empty configuration,
never an unvalidated user-supplied endpoint; native session/safety tests verify this separation.
