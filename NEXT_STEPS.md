# Next steps

Updated 2026-10-27. Phase 4 source/native verification is implemented; full acceptance is BLOCKED by
managed Chromium launch. See [PHASE4_COMPLETION_REPORT.md](PHASE4_COMPLETION_REPORT.md). Keep
SIMULATED/DENY_ALL, owner MFA, immutable data and all external execution refusals. No Phase 5 started.

## P1 — browser acceptance, owner/environment administrator

Browser testing is authorized, but managed macOS still refuses Chromium bootstrap_check_in with
Permission denied (1100) before page creation. Do not bypass that restriction. Run in a legitimately
permitted local environment, using the same disposable harness and unchanged assertions:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" npm --prefix apps/web exec -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=risk make browser-integration
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO make browser-integration
make check
make integration
make contracts-check
make secret-scan
```

Require all 14 desktop/mobile cases to pass. Current focused risk attempt fails at launch; default
attempt has 3 desktop launch failures, 1 HTTP-only denial pass and 10 NOT RUN. Collection/build is
not workflow acceptance. Inspect profile/policy/context setup, calculator non-authority, actual order
reservation/fill, owner STOP persistence, separate FLATTEN, mobile overflow and prior identity/data/
UNKNOWN workflows. Fix any exposed application defect without weakening assertions.

## P1 — review risk assumptions and operational boundaries

Read RISK_CALCULATIONS, RISK_AUTHORIZATION_PROTOCOL, PROP_FIRM_POLICY_SCHEMA and reservation/incident
runbooks in docs/. Explicit linear contract/tick payoff and fixed per-unit margin are supported;
inverse/unverified conventions refuse. Supply trustworthy facts rather than generic pip values.
Real broker payoff/margin/calendar/tradability and current exact firm terms remain unverified. Human
attestation is not automatic contractual certification. No broker credentials are needed for Phase 4.

Known synthetic clocks are account-global; independent historical experiments need separate accounts.
A missing held-position midnight reference stays unverified rather than inventing one after a loss.
New/adapted legacy configurations require explicit review; existing records are preserved, never reset
to gain acceptance. Current development has zero configured risk accounts; monitor runtime is healthy,
while behavior is exercised using disposable native fixtures. Production capacity/retention, monitor
partitioning beyond 1000 configured accounts per poll and chained-history limits need separate work.

## P2 — external read-only and production dependencies, separately scoped

Actual Windows MT5 investor/demo terminal, cTrader registered application/accounts-only OAuth, PKI,
connector-host secrets and permitted source/calendar access remain owner/operations prerequisites.
Use docs/BROKER_RUNBOOK.md; no broker keys in chat, control-plane .env or research host. Contract/OAuth
fixtures do not certify connectivity. Continuous central observation polling is still missing.

Before any order-capable external phase, independently deploy executor capability verification,
separate signing keys/rotation/revocation, exact scope and owner MFA/two acknowledgements. Current
shared-host SIM HMAC is not such a capability. Do not enable external demo or live methods here.

.git remains read-only; no initial commit/remote/push created. Review source in an authorized Git
environment; owner approval is still required for private repository creation/push. Local Actions
syntax is not remote CI. Container/Windows audits, SBOM, fresh-machine setup, production-load tests,
actual off-host backup restore, TLS/Secure cookies, secrets/Redis hardening and audit anchoring remain.

## Recommended next implementation module — Phase 5, only by a new request

After Phase 4 browser acceptance is evidenced and scope is approved, add reproducible cost-aware
backtesting over immutable VALID datasets, baseline strategies, chronological OOS/holdouts,
walk-forward/purging and statistical uncertainty. Reuse deterministic simulated execution and risk
contracts. Do not start it automatically or claim performance before actual evidence exists.
