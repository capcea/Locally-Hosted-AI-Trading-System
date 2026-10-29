# AI inference evaluation and evidence

Updated 2026-10-28. Do not equate an HTTP fixture with an AI model or financial validation.

## Evidence classes

- **Actual native integration:** disposable PostgreSQL/Redis/MinIO; actual migrations, immutable
  artifacts, scoped grants/denials, real HTTP requests, cancellation, quotas, leases, SIGKILL and
  graceful-service-restart acceptance. Full integration passed 86 tests before and86 after restart.
- **Synthetic transport contract:** native Ollama, Ollama-compatible and private-compatible HTTP
  protocols use a loopback fixture explicitly named `SYNTHETIC_HTTP_FIXTURE:1`. It ignores questions
  and returns authored outputs. Passing demonstrates plumbing/validation, not intelligence or
  resistance of a real model to an attack.
- **Actual TLS:** disposable certificate with loopback IP SAN and random bearer token; trusted
  identity succeeds, untrusted server fails. No verify-false or fabricated TLS result.
- **Real Ollama:** discovery at `http://127.0.0.1:11434` returned
  `BLOCKED_RUNTIME_UNAVAILABLE` (exit2). No runtime/model/download/inference verified.
- **Browser:** 22 cases collect; execution BLOCKED by managed localhost browser-origin restriction.
  No CLI/CDP/browser substitute was used. Prior Phases0–5.5 acceptance is OWNER_REPORTED_PASS.
- **Deployment:** restricted image build/run, Compose inspection and actual local worker/queue/proxy
  startup/boundaries pass, including queue restart. Initial delays, API-name collision and Redis
  root-entrypoint chown failure are preserved as failures. Remote provider/firewall acceptance remains
  unverified. Redis uses its native non-root UID/GID without adding capabilities.

## Automated coverage

`tests/test_ai_http.py`, `test_ai_tls.py`, `test_ai_egress.py` test actual local protocols, strict
schemas, exact authority/version types, invented references, duplicate fields, hidden reasoning
removal, unsupported tool calls, terminal framing, bounded errors, busy versus ambiguous failures,
SSRF targets and proxy refusal. Contracts are independently validated after provider formatting.

`tests/test_ai_integration.py` tests discovery/probe/role routing, idempotency/conflict, encrypted
durable output, single final artifact, real permission attempts, Redis ACL, viewer/CSRF isolation,
concurrent quotas, queued/running cancellation, invalid output, erasure, session revocation, expired
dispatched lease and actual process SIGKILL recovery. The kill test advances only its disposable
lease timestamp to avoid sleeping, then proves no duplicate provider request. Actual data import and
quality admission precede the holdout test; active disclosure blocks sealing, queued input is
revoked, and sealed/cached context plus stored output reads fail closed.

`scripts/evaluate_ai.py` runs 12 explicitly synthetic schema/protocol cases (four roles × three
benign/adversarial questions). It reports schema validity, reference count, missing evidence and
fixture token counts; **no real-model safety/accuracy score**. Run:

```sh
.venv/bin/python -m scripts.evaluate_ai
```

`scripts/verify_ai_runtime.py` probes an operator-approved endpoint and exact already-installed model.
With `--run-evaluation`, it makes 12 additional bounded actual requests and records independent
schema/reference validity, measured latency and provider usage. It retains no raw response/reasoning
or credentials. This is a small structural evaluation, not financial correctness, confidence or
profitability certification. Real evidence remains NOT EVALUATED until the owner runs it successfully.

```sh
# Set AI_ENDPOINTS/AI_SECRET_ROOT using the deployment guide; do not put secrets in CLI arguments.
.venv/bin/python -m scripts.verify_ai_runtime --endpoint local-private \
  --provider OLLAMA_NATIVE --model EXACT_ALREADY_INSTALLED_MODEL --run-evaluation
```

## Required real-provider review

Check private-only/cloud-off deployment, exact model/digest/context/quantization, every selected role,
streaming/cancellation uncertainty, accepted seed versus reproducibility, reasoning suppression,
context under load, measured latency/token variability and GPU memory on the actual host. Review
unsupported claims, fabricated references, missing evidence, instruction injection and inert code
manually as well. Repeat across selected models and record all failures, not just successful probes.
No real financial holdout or confidential broker data belongs in evaluation fixtures. Cost is unknown
until actual usage and explicit rates exist. Broader semantic/financial evaluation is a later gate.

Exact commands, exits and sanitized logs are linked from [the completion report](PHASE6_COMPLETION_REPORT.md).

An additional native regression verifies that malformed AI settings and identity-key reuse disable
AI while full-MFA identity and SIMULATED/DENY_ALL safety remain reachable. The current AI-focused
suite contains8 real-service cases, each repeated after graceful restart. See final ledger for exits.
