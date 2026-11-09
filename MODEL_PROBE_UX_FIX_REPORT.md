# Model verification consent — UX repair

Deployment follow-up,2026-10-29: this UI fix is now included in the deployed, healthy Web update
with the provider-diagnostics repair. Native HTTP confirms the new bundle; no paid probe was
submitted and browser acceptance remains open. See `OPENROUTER_DIAGNOSTICS_REPORT.md`.
The earlier implementation checkpoint and its formatting failures below are preserved evidence.

2026-10-29. Source implemented; browser execution BLOCKED; static Web deployment not changed.

The original Registry disables verification while `busy`, or when the model's connection provider
is OPENROUTER and `cloudProbeConsent` is false. This consent starts false. A configured server key,
cloud-processing authorization and a registered unverified model do not authorize a paid probe.
The existing backend separately enforces cost acknowledgement, MFA, scope, policy and budgets.

The confirmed UX defect is placement: the cost checkbox was a direct child of the registry grid
with default order0, while three forms have order1–3 and model lists order4. The V1 CSS therefore
separated the required checkbox from the disabled button. The owner's screenshot shows the button
and configured connection, but not the checkbox. Browser memory/state could not be inspected due
to the managed origin denial; this is source/structural diagnosis, not claimed browser reproduction.

Changes:

- `apps/web/src/ai/ModelProbe.tsx`: group cost confirmation with each model's button; show the
  exact reason for busy, unavailable/disabled connection, missing cloud key or missing cost consent.
  The button is linked to that explanation through `aria-describedby`.
- `apps/web/src/ai/AICenter.tsx`: per-model explicit consent, initially unchecked and cleared on
  each submission attempt; one model's consent no longer approves another. Checking alone sends
  nothing. Clicking still uses the original probe API and idempotency key. Private-provider probes
  remain independent of cloud-cost consent. No CSS/design token, backend or security rule changed.
- `apps/web/src/ai/ModelProbe.test.tsx`: nine cases; disabled/enabled states, nearby consent/help,
  missing prerequisites, separate model groups, private providers and no automatic submission.

Actual verification (full command/exit records in `.cache/model-probe-ux-fix/`):

- Focused `npm --prefix apps/web run test -- src/ai/ModelProbe.test.tsx src/ai/ai.test.tsx`:
  exit0,17 cases. Backend fixture-only `pytest tests/test_openrouter.py -q`: exit0,20 cases.
- `make typecheck test build`: exit0,294 Python +195 frontend cases, mypy/TypeScript/build pass.
- Formatting of the three changed UI/test files: exit0 after correcting one new wrapping issue.
- `make smoke-demo`: exit0, readiness200 and execution-denial smoke.
- `make check`: exit2 at existing Prettier failures in `apps/web/src/App.tsx` and
  `src/cockpit/{cockpit-shell.css,cockpit-template.html,CockpitPage.tsx,vite-raw.d.ts}`. All five
  match their pre-task SHA256 bytes and were preserved; no checks were removed or reclassified.
- `make secret-scan`, `make repository-check`, `git diff --check`: exit0. Exact final command
  ledger and pre-task source preservation are in `docs/openrouter-evidence/2026-10-29/model-probe-ux/`.
- Browser execution: NOT RUN / BLOCKED by the existing origin policy. No screenshot baseline,
  real model capability, provider connectivity or paid request is claimed verified here.

No external provider request, key access, identity/MFA mutation, Docker change or persistent-data
reset occurred. SIMULATED/DENY_ALL, scoped cloud approval and independent risk controls remain.
The running nginx bundle needs the normal Web-only build/update before the new explanation appears;
the targeted commands are in `SIDEBAR_SYSTEM_HEALTH_FIX_REPORT.md`. The owner may then review the
per-model cost checkbox and explicitly decide whether to send the real verification. This repair
does not authorize the agent to make that call.
