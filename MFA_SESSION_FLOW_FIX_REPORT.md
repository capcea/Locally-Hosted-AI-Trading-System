# MFA reverification and session-loop repair

2026-10-29 (Europe/Bucharest). IMPLEMENTED. Native verification and local deployment results are
recorded below. Browser execution remains BLOCKED by the existing managed localhost restriction.
No owner enrollment, persistent identity reset, financial logic or paid inference was performed.

## Confirmed causes and reproductions

Three defects were reproduced; a stale cookie/domain mismatch was not assumed to be the cause.

1. **Invalid MFA was incorrectly treated as expiration.** The existing backend deliberately returns
   HTTP401 for an invalid/expired/already-used TOTP, retaining the valid password/MFA session and
   auditing/rate-limiting the failed attempt. The shared frontend client dispatched
   `research-session-expired` for every401 except password login. AuthProvider then cleared the
   session, unmounting Security or the MFA challenge and showing login. A disposable backend test
   confirms `/auth/me` remains200 after failed step-up; a frontend reproduction failed because
   the invalid-MFA response incorrectly dispatched expiration.
2. **Old responses could discard new authority.** A request started with the old session could
   resolve401 after successful login/rotation and clear the newly authenticated frontend state.
   The client also lacked a fence against old successful `/auth/me` data replacing a new session.
   A controlled deferred-response test reproduced the invalidation after completed login.
3. **Rotated cookies could precede transaction commit.** MFA transitions used request-scoped yield
   transaction cleanup. At ASGI `http.response.start`, an independent PostgreSQL connection could
   not yet see the new session row, although the cookie was being sent. This is an actual visibility
   race, not a presumed timeout: the reproduction observed `[False]`, with26 other native cases
   passing and this one failing. A fast new-cookie request could therefore return authentication
   failure before commit. The same test now observes the committed row before headers leave.

Separately, the generic401 label combined “session expired” with bad credentials. That made login
credential failures misleading. There was no direct recent-MFA challenge at the original sensitive
action. Those UX problems are corrected without loosening backend approval.

The observed OpenRouter403 is legitimate: `privileged()` enforces OWNER and the unchanged five-minute
recent-MFA limit before any authorization is created. Invalid MFA is not proof of an expired session;
actual idle/absolute expiration or revocation still requires password login and MFA again.

## Changes

- `apps/api/identity/dependencies.py`: allowlisted `X-Auth-Error` categories for authentication,
  expiration, recent MFA, incomplete MFA, role and CSRF refusals. Existing statuses/details remain.
- `apps/api/identity/routes.py`: distinguish login-invalid/MFA-invalid responses; `rotate()` now
  commits the new session, old-session revocation, TOTP counter and audit atomically **before** the
  response can publish its cookie. This is limited to existing MFA/enrollment/recovery transitions;
  the shared financial transaction dependency and risk algorithms are untouched.
- `apps/web/src/management-api.ts`, `auth/lifecycle.ts`: strict error allowlists and Romanian
  explanations; no expiry event for a rejected code, permission refusal or stale CSRF. A memory-only
  generation fence rejects old responses, including late successful session data. Outdated failures
  become an explicit409 requiring review, never an automatic mutation retry.
- `auth/AuthProvider.tsx`: session/CSRF updates are fenced, genuine invalid sessions clear protected
  client state, stale-CSRF errors trigger a read-only session refresh, and focus refresh detects
  cross-tab changes. Enrollment/recovery confirmation is not interrupted by FULL-session focus
  refresh while recovery codes are awaiting acknowledgement.
- `auth/MfaStepUp.tsx`, `App.tsx`: an in-place password+new-TOTP challenge using the existing
  `/auth/reauthenticate` endpoint, existing accessible dialog and V1 components. The original screen,
  fragment and mounted nonsecret form remain. The owner reviews/resubmits after success; there is
  **no automatic OpenRouter registration, paid request or other action replay**. Cancel preserves
  the refusal and offers “Reconfirmă MFA” again.
- `Management.tsx`: clear submitted password/code fields on attempts and key authentication UI by
  session identity, so genuine expiry cannot leave the previous challenge's secrets in the form.
  Manual Security reconfirmation and the existing enrollment/recovery flow remain available.
- Native/client regression tests plus `scripts/integration_services.py --auth-only`. The full
  native suite includes all original tests and the new identity cases.
- `apps/web/e2e/auth-session.spec.ts`, browser harness `auth` scenario and `testing/mfa_state.py`:
  real-service desktop/mobile workflow. The test-only CLI can only make authorization **older** in
  a validated disposable `p1_browser_*` database selected by the private harness configuration.
  It cannot grant MFA, reset counters, create authenticated sessions or select development data.
  It is not a production endpoint or image entrypoint. No browser receives database credentials.

## Resulting flow

1. An OWNER submits the sensitive form. Legitimate recent-MFA403 displays:
   **“Pentru această acțiune trebuie să reconfirmi autentificarea în doi pași.”**
2. A dialog requests the existing password and a new authenticator code. A used/incorrect code
   remains in this challenge with a clear explanation and the valid session intact. Submitted
   secrets are cleared; the server's replay prevention and rate limiter remain authoritative.
3. Successful step-up atomically rotates the opaque cookie/session and derived CSRF token. The
   frontend installs the returned validated SessionView. Old in-flight responses cannot undo it.
4. The dialog closes on the original screen. Nonsecret form choices remain for a valid session;
   the owner explicitly reviews and submits again under the new CSRF and five-minute window.
5. If the underlying session truly expired, it is cleared. The original private route/fragment
   displays login inline, followed by MFA; no redirect chain or automatic login loop is used.
   Secrets/drafts are cleared on real expiry. After login, the owner returns to that same route
   and reviews any form that must be entered again.

Different Romanian messages identify expired session, incorrect login, invalid/reused MFA, recent
MFA required, insufficient role, origin refusal, stale CSRF and rate limiting. Unknown server bodies
are not echoed. A rotated CSRF requires refresh/review, not bypass or blind replay.

## Security preserved

- Same five-minute recent-MFA guard, normal absolute/idle expiration and revocation. No duration
  increase, reused expired cookie, role escalation or MFA/password exemption.
- Original TOTP replay counters, enrollment, one-use recovery and persistent attempt limits.
- Original cookie settings: HttpOnly, SameSite=Strict, configured Secure, path `/`, **no Domain
  sharing**. API calls remain same-origin with CSRF and strict origin checks. `127.0.0.1` and
  `localhost` are different cookie hosts; use one consistently. A wrong-origin test is rejected
  without logging out a valid session. No wildcard origin or development bypass was introduced.
- No passwords, TOTP seeds/codes, opaque cookies, CSRF values or keys in logs/evidence/storage.
  Error tests retain booleans/categories rather than raw cookie comparisons in failure output.
  Browser trace, automatic screenshots and authentication DOM error snapshots remain disabled.
- OWNER/RBAC/account isolation, OpenRouter cloud consents/budgets, Phase6 network separation,
  Phase7 bounds, holdouts, financial algorithms and SIMULATED/DENY_ALL are unchanged.
- Production users/sessions/enrollment/data are not reset. No schema migration or volume removal.

## Verification ledger

Exact machine records and ignored full logs: `.cache/mfa-session-fix/`. Sanitized final records:
`docs/mfa-session-evidence/2026-10-29/`.

- Baseline client reproduction: exit1,2 failed/5 passed; invalid-code logout and late401 race.
- Baseline PostgreSQL commit probe: exit1,1 failed/26 passed; new row invisible at cookie headers.
- Final focused `.venv/bin/python -m scripts.integration_services --auth-only`: exit0,
  **27 before +27 after graceful restart**. Includes original login/enrollment/recovery tests,
  MFA aging, step-up, commit visibility, cookie/CSRF rotation, old-session refusal, true expiration,
  replay/invalid codes, attempt limits, role/origin refusal and actual OpenRouter metadata201 only
  after valid MFA. No provider/key/model calls occur.
- `make check`: exit0, **294 Python +160 frontend cases**, Ruff/formatting, mypy and production
  TypeScript/Vite build. Existing TestClient deprecation and >500kB chunk warnings remain visible.
- `make contracts-check`: exit0; response body contracts unchanged.
- `npm --prefix apps/web run test:e2e -- --list`: exit0, **28 cases in12 files**; collection only.
- `make integration-services`: exit0, **117 before +117 after graceful restart**,463.210 seconds;
  real PostgreSQL/Redis/MinIO migrations, round trips, all existing service regressions and cleanup
  of only the disposable project. The first run took228.75 seconds; the second220.03 seconds.
- `make smoke-demo`: exit0 against the updated development API; readiness and execution denial pass.
- `make secret-scan`, `make repository-check`: exit0; final post-documentation runs are included in
  the sanitized evidence ledger. `git diff --check`: exit0.
- Targeted API/Web image build: exit0. Targeted `up -d --no-build --no-deps --wait --wait-timeout 90
  api web`: exit0, both healthy. Only these two containers were recreated; every other development
  container ID and named-volume mount identity matches the pre-task inventory. No database restart,
  migration, owner enrollment/session mutation or volume deletion was used for this deployment.

The exact build/start commands, including Compose files and profiles, are preserved in the command
ledger. All1357 pre-task Git-selected files remain; their before/after SHA comparison confirms no
change to accepted golden images, financial/risk/research/execution logic, AI/campaign logic or
migrations during this task. Existing unrelated uncommitted work is preserved.

Initial formatting/mypy issues in the new test fixture were corrected before final native checks;
the reproduction failures above are retained rather than reclassified as passes. No assertions,
existing scenarios, freshness checks, security settings or snapshots were weakened or removed.

## Browser and owner-local acceptance

**BLOCKED here:** the prior managed browser policy explicitly denied localhost and prohibited
alternate/indirect access. No CLI/CDP/alternate-origin workaround was used. Native ASGI/PostgreSQL
and client unit execution do not establish rendered/focus/mobile/browser acceptance.

Owner-local commands, without rewriting references:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=auth make browser-integration
E2E_ONLY_SCENARIO=auth make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

The new scenario uses actual login/MFA/cloud-registration APIs and disposable services, no mocked
auth responses. It ages only its disposable session, checks step-up refusal/invalid-code recovery,
new-session/CSRF refresh, original-route/draft retention, explicit cloud registration, Back/reload,
true expiration and password+MFA recovery. It waits for an actually unused TOTP window using a
condition, not a counter reset or arbitrary sleep. All28 cases must execute before browser acceptance.

On the owner installation, reload the current app on the **same hostname** used for login. At
`/setari/ai#ai-models`, review and submit cloud authorization. If recent MFA is required, enter the
password and a **new, unused** authenticator code in the dialog, then review/resubmit the original
form. If the same code was just used for login, wait for the authenticator's next code. A genuinely
expired session requires fresh password login and MFA. Do not re-enroll/reset MFA to fix an error.
Check modal focus/Escape/return and mobile usability manually without capturing secrets.

No paid probe/inference is authorized by this repair. Real OpenRouter model acceptance and existing
V1 visual/manual acceptance remain separate gates. Stop after this authentication fix.
