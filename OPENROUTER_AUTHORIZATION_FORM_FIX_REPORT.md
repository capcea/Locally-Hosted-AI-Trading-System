# OpenRouter authorization form repair — 2026-10-29

## Confirmed cause and scope

The owner reported that the upstream-provider field did not stay saved after trying `openai` and
`azure`. Source inspection confirms a frontend read/display defect: the upstream input always
started blank, even when GET `/api/v1/ai/cloud-policy` returned an authorization; cost fields used
fixed defaults instead of the saved limits. The actual active provider appeared only inside
collapsed technical JSON. There was no explicit save/readback confirmation. These behaviors made
a saved value indistinguishable from an unsaved draft. They do **not** prove production database
persistence failed. We have not read or changed the owner's active authorization.

POST `/api/v1/ai/endpoints/openrouter` still requires OWNER, valid session/CSRF and recent MFA.
A step-up challenge authorizes the session; it deliberately does not automatically replay or save
the original form. The original action must be explicitly reviewed and submitted again.

## Changes

- `apps/web/src/ai/cloud-policy.ts`: typed validation of the existing read contract, exact saved
  strings for provider/caps, fresh form consent, and confirmation only when the POST authorization
  ID and every policy value match the subsequent server read. Invalid reads do not invent defaults.
- `apps/web/src/ai/CloudAuthorizationForm.tsx`: saved values prefilled, editable draft preserved
  across refused mutations/MFA, all four consents initially unchecked, explicit draft/save guidance.
- `apps/web/src/ai/CloudSetup.tsx`: visible **Furnizor aprobat pe server**, explicit confirmed or
  unconfirmed save message, GET-only refresh/retry, loading and read-generation/unmount fencing.
  The existing credential editor is unchanged.
- `apps/web/src/ai/cloud-policy.test.tsx`: eight tests for exact prefill/caps, fresh consent,
  truthful saved status, missing policy and mismatched readback refusal.
- `tests/test_openrouter_integration.py`: actual disposable database/API revision/readback and
  idempotency coverage with exact cap strings; no provider completions.
- `apps/web/e2e/auth-session.spec.ts`: existing real-service MFA flow now also asserts confirmed
  saving and provider persistence through navigation/reload. Existing assertions retained.

No backend production source, schema, financial calculation, policy enforcement or credential
storage changed. There is no automatic Azure selection, consent, provider retry or paid request.
ZDR, exact upstream routing, price caps, expiry, MFA/CSRF/RBAC, owner isolation, holdout boundaries
and SIMULATED/DENY_ALL remain enforced. Saving authorization is separate from verifying a model.

## Verification

All commands ran from the repository root unless otherwise noted. Machine-readable command records
and sanitized deployment evidence: `docs/openrouter-evidence/2026-10-29/authorization-form/`.
Full native command logs: `.cache/cloud-save-ux-fix/`.

- `npm --prefix apps/web run test -- src/ai/cloud-policy.test.tsx src/ai/ai.test.tsx src/ai/ProviderError.test.tsx src/ai/ModelProbe.test.tsx`: exit **0**, 34 frontend tests.
- `.venv/bin/python -m scripts.integration_services --openrouter-only`: exit **0**; 12 tests
  before and 12 after service restart, real isolated PostgreSQL/Redis/MinIO migrations, round trips
  and persistence. Provider interactions are synthetic fixtures, not real OpenRouter acceptance.
- `make contracts-check`: exit **0**.
- Initial `make check`: exit **2**, ESLint warned about a ref read in effect cleanup. Corrected by
  capturing the lifecycle object; no rule suppression or weakened assertion.
- Final `make check`: exit **0**; 324 Python tests, 212 frontend tests, lint, formatting,
  mypy, TypeScript and production build. Existing nonfatal bundle-size warning remains.
- `make smoke-demo`: exit **0**.
- `npm --prefix apps/web run test:e2e -- --list`: exit **0**, 28 cases in 12 files collected.
  This is **not execution**. Managed browser execution remains **BLOCKED** by the recorded local
  browser restriction; no CLI/CDP/alternate-origin workaround was used. Rendered interaction and
  manual accessibility acceptance remain unverified.
- `make secret-scan`: exit **0**, no leaks in 1422 Git-selected files.
- `make repository-check`: exit **0**, 19 sensitive-path exclusions verified.
- `git diff --check`: exit **0**.

## Local Web update

Built Web with the existing development configuration and updated **only** that container:

```sh
BUILDX_CONFIG="$PWD/.cache/openrouter/startup/buildx" docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns build web
docker compose --env-file .env --env-file .env.ai -f compose.yaml -f compose.ai.yaml --profile ai --profile campaigns up -d --no-build --no-deps --wait --wait-timeout 90 web
```

Both exit **0**; Web is healthy. Before/after container IDs confirm all other services were
unchanged; named volume mounts are unchanged. No persistent development data was deleted/reset.
HTTP delivery of `/assets/index-wrnuWVlb.js` confirms the new saved-provider and confirmation copy
is served at `http://127.0.0.1:5173`. Asset delivery is not rendered browser acceptance.

## Owner verification and next action

1. Hard-refresh the existing `http://127.0.0.1:5173/setari/ai` tab with **Cmd+Shift+R**.
2. Read **Furnizor aprobat pe server**. The review form must initially show that same saved
   provider and its exact saved caps. A field you edit is only a draft.
3. If changing provider, independently review the actual processing provider, current catalog/ZDR
   availability, prices and limits. Check all four approvals and click **Înregistrează autorizarea
   cloud**. Do not infer availability merely because a tag is saved.
4. If MFA appears, complete step-up, review the preserved draft and click the original save button
   again. Expect **Salvare confirmată de server. Furnizor autorizat: …**. Reload to confirm.
5. Model verification is a separate potentially billable action requiring explicit cost approval.
   No real inference was submitted for this repair. Existing `openai`/ZDR incompatibility evidence
   and provider-specific limitations remain in `OPENROUTER_ZDR_ROUTING_FIX_REPORT.md`.

Owner-local regression with disposable services, without rewriting snapshots:

```sh
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=auth make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO -u E2E_UPDATE_SNAPSHOTS make browser-integration
```

This repair does not claim browser, real-model or profitable-research acceptance and starts no
new development phase.
