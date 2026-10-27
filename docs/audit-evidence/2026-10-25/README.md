# Audit evidence — 2026-10-25

These are actual local command records, not placeholder results. Logs are sanitized for known
local secret values. Child command exit codes below are authoritative; the capture wrapper itself
returns normally to preserve failed-command evidence. No test count is inferred from a collection.

The root [audit report](../../../AUDIT_REPORT.md) explains interpretations and limitations.
`requirements.json` contains the 60 derived criteria; original individual Q1–Q60 were not supplied.
`source-review.json` is a mid-audit snapshot, explicitly not a pristine baseline.
`final-source-manifest.json` lists delivered non-evidence source files and their SHA-256 values;
evidence is excluded from that manifest to avoid self-referential hashes. Raw command logs retain
their own hashes in their JSON records. `commands.json` is the machine-readable command ledger.

No ignored .env contents are included. The scoped environment review records only mode and absence
of known broker-key variable names. Source scanning does not certify host/external secret storage.

## Recorded commands

- **baseline-check** — `make check` — exit **0**, 5.246 s, started 2026-10-25T16:55:04.016763+00:00. [Log](baseline-check.txt); [record](baseline-check.json).
- **baseline-e2e-list** — `npm --prefix apps/web run test:e2e -- --list` — exit **0**, 1.543 s, started 2026-10-25T16:55:05.127580+00:00. [Log](baseline-e2e-list.txt); [record](baseline-e2e-list.json).
- **baseline-integration** — `make integration` — exit **2**, 1.463 s, started 2026-10-25T16:55:05.130545+00:00. [Log](baseline-integration.txt); [record](baseline-integration.json).
- **baseline-doctor** — `make doctor` — exit **2**, 0.795 s, started 2026-10-25T16:55:05.138937+00:00. [Log](baseline-doctor.txt); [record](baseline-doctor.json).
- **baseline-npm-audit** — `npm --prefix apps/web audit --audit-level=high` — exit **0**, 0.807 s, started 2026-10-25T16:55:14.000699+00:00. [Log](baseline-npm-audit.txt); [record](baseline-npm-audit.json).
- **baseline-pip-audit** — `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --progress-spinner off --cache-dir .cache/pip-audit` — exit **0**, 11.663 s, started 2026-10-25T16:55:14.003242+00:00. [Log](baseline-pip-audit.txt); [record](baseline-pip-audit.json).
- **defect-reproductions** — `.venv/bin/python -m pytest tests/test_audit_regressions.py -q` — exit **1**, 0.657 s, started 2026-10-25T16:56:46.802828+00:00. [Log](defect-reproductions.txt); [record](defect-reproductions.json).
- **fixed-check** — `make check` — exit **2**, 3.474 s, started 2026-10-25T16:59:51.614067+00:00. [Log](fixed-check.txt); [record](fixed-check.json).
- **fixed-integration** — `make integration` — exit **2**, 0.95 s, started 2026-10-25T16:59:52.308724+00:00. [Log](fixed-integration.txt); [record](fixed-integration.json).
- **docker-start** — `make dev` — exit **2**, 0.356 s, started 2026-10-25T16:59:53.303752+00:00. [Log](docker-start.txt); [record](docker-start.json).
- **compose-config** — `docker compose config --quiet` — exit **0**, 0.253 s, started 2026-10-25T17:00:17.098857+00:00. [Log](compose-config.txt); [record](compose-config.json).
- **shell-syntax** — `bash -n scripts/setup.sh` — exit **0**, 0.003 s, started 2026-10-25T17:00:17.391737+00:00. [Log](shell-syntax.txt); [record](shell-syntax.json).
- **e2e-collection** — `npm --prefix apps/web run test:e2e -- --list` — exit **0**, 0.5 s, started 2026-10-25T17:00:17.423810+00:00. [Log](e2e-collection.txt); [record](e2e-collection.json).
- **final-check** — `make check` — exit **0**, 5.125 s, started 2026-10-25T17:00:27.442544+00:00. [Log](final-check.txt); [record](final-check.json).
- **final-python-all** — `.venv/bin/python -m pytest` — exit **1**, 1.047 s, started 2026-10-25T17:03:34.621839+00:00. [Log](final-python-all.txt); [record](final-python-all.json).
- **final-npm-audit** — `npm --prefix apps/web audit --audit-level=high` — exit **0**, 0.883 s, started 2026-10-25T17:03:34.621881+00:00. [Log](final-npm-audit.txt); [record](final-npm-audit.json).
- **final-smoke** — `make smoke-demo` — exit **0**, 0.181 s, started 2026-10-25T17:03:41.988499+00:00. [Log](final-smoke.txt); [record](final-smoke.json).
- **final-smoke-ready** — `.venv/bin/python -m scripts.smoke_demo --require-ready` — exit **1**, 0.133 s, started 2026-10-25T17:04:13.127396+00:00. [Log](final-smoke-ready.txt); [record](final-smoke-ready.json).
- **contract-generation** — `make contracts` — exit **0**, 0.762 s, started 2026-10-25T17:04:46.721738+00:00. [Log](contract-generation.txt); [record](contract-generation.json).
- **seed-fixture** — `make seed-demo` — exit **0**, 0.1 s, started 2026-10-25T17:07:25.662863+00:00. [Log](seed-fixture.txt); [record](seed-fixture.json).
- **final-secret-scan** — `.tools/bin/gitleaks dir .cache/audit-source-scan --redact --no-banner --report-format json --report-path .cache/audit-gitleaks.json` — exit **1**, 0.31 s, started 2026-10-25T17:16:10.332884+00:00. [Log](final-secret-scan.txt); [record](final-secret-scan.json).
- **final-secret-scan-clean** — `.tools/bin/gitleaks dir .cache/audit-source-scan-clean --redact --no-banner --report-format json --report-path .cache/audit-gitleaks-clean.json` — exit **0**, 0.355 s, started 2026-10-25T17:16:56.389296+00:00. [Log](final-secret-scan-clean.txt); [record](final-secret-scan-clean.json).

## Interpret failures correctly

- baseline-integration: actual PostgreSQL connection refused; no successful migration/integration.
- defect-reproductions: three new regressions failed before fixes, reproducing unsafe Host acceptance,
  unrestricted smoke target and false smoke success on HTTP 500.
- fixed-check: two intermediate regressions exposed strict Python-object/tuple validation; corrected
  to strict JSON validation before the passing final-check.
- fixed-integration and final-python-all: actual service readiness fails; no infrastructure success.
- docker-start and baseline-doctor: Docker engine socket unavailable.
- final-smoke passes API/denial behavior with readiness 503; final-smoke-ready correctly exits 1.
- final-secret-scan: 11 findings were verified against recomputed source SHA-256 values.
  `secret-scan-triage.json` records each false positive; raw redacted findings are preserved.
  Metadata was represented as path/sha256 records without disabling any detector or allowlisting paths.
  final-secret-scan-clean exited 0, no leaks found in 137 selected source/evidence files.
- Browser execution was BLOCKED by access policy. `browser-execution.json` records the limitation;
  e2e-collection/baseline-e2e-list only listed six cases, never executed them.

## Scope limits

Python API tests use in-process TestClient and some explicit mocks; migration round trips use temporary
SQLite. Frontend unit tests use synthetic contract payloads, clearly labeled TEST fixtures. Those
fixtures do not establish PostgreSQL, broker, model, feed or rendered-browser integration.

The secret scan uses a regular-file export selected by `git ls-files --cached --others
--exclude-standard -z`, including untracked source and the evidence present at scan time. Its scope
files identify the exact selection; ignored runtime directories and .env are excluded. Later evidence
indexes/manifests are metadata about the run, not additional application code. The export remains
ignored in .cache; the reports preserve the exact command and redacted output.

The four root reports and docs status are current. `previous-implementation-status.md` is preserved
only as historical Phase 0 evidence and contains earlier counts, not current acceptance.
No paid infrastructure, broker service, message delivery, or live promotion was activated.
