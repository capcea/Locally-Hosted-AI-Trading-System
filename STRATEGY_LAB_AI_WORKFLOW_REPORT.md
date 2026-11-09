# Strategy Lab — AI-first discovery and review

> Context amendment —2026-10-30: the default Lab discovery context now carries actual baseline
> IDs/versions and a SHA256 of the complete registry instead of eight digests and full entry/exit
> prose. Detailed strategy references remain available. This fixes an actual4096-budget regression;
> the earlier implementation description below is preserved as historical evidence. See
> [the capacity correction and validation](AI_CONTEXT_BUDGET_FIX_REPORT.md).

2026-10-29. Implemented against the current three-destination product. Ordinary authentication remains
PASSWORD; execution remains SIMULATED/DENY_ALL. No real provider invocation was made by the agent.

## Product flow

Strategy Lab now opens directly on the existing real AI composer, not a grid of technical modules.
The compact flow is: **Idei cu AI → Pregătește testul → Citește rezultatele → Biblioteca validată**.
The sidebar exposes assistant, test activity and library. Manual settings, baseline catalog, data
imports, campaigns, comparison and protected final evaluation remain reachable through collapsed
advanced tools or activity. The unused account selector/duplicate technical navigation is hidden
only on this assistant workspace; account context and safety controls elsewhere are preserved.

The assistant still uses actual registry/verification/worker/standing-authorization/budget state.
It never displays a configured-but-unverified model as online. A new reviewed documentation reference,
`strategy-lab-v1`, supplies the actual eight registered baseline IDs, versions, digests and entry/exit
summaries. It contains no invented prices, balances, symbol specifications or permissions. This uses
the existing documentation context policy, byte/token bounds and isolated Gateway adapter.

A completed accessible Research hypothesis exposes **Pregătește testul acestei idei**. The existing
five-step historical wizard opens at step 1 with the proposed hypothesis/test plan visible. It does
not infer/set an account, dataset, risk, capital, costs, parameters or acknowledgement. The owner
still chooses a reviewed implementation and valid setup; unsupported new logic remains an idea.
Critic/Coding/probe/failed/expired/inaccessible jobs do not get this handoff action.

On an actual completed stored result, **Cere AI-ului să analizeze acest rezultat** prepares a Critic
question referring to the actual experiment ID. The user must submit it separately through the same
readiness/consent/budget gates. No prompt is sent on navigation. Final-holdout results do not expose
this button, and the backend context assembler remains authoritative for later seals/revocation.

Campaign creation defaults explicitly to AI_GATEWAY instead of a synthetic fixture. Missing models
still refuse; the explicit labeled development fixture mode remains available without automatic
fallback. Existing bounded lifecycle and owner handoffs are unchanged.

## Important scope and provenance limit

This is an AI-first **assistive workflow**, not autonomous execution of arbitrary model-generated
strategies. AI proposes hypotheses and critiques evidence; the existing deterministic engine tests
reviewed implementations. No mathematical engine, risk gate, account permission or promotion rule
was changed.

The idea panel is a bounded, owner-bound memory-only draft. It clears on consumption/logout, expires
with the server's retained output, and does not survive reload. It is explicitly labeled temporary.
No new durable AI-origin foreign key was added to ResearchRun, and selecting a baseline is not proof
that it implements a new model idea. Existing campaigns remain the supported immutable multi-stage
hypothesis/plan/experiment lineage when that persistent research structure is needed.

## Source changes

- `product/Workspace.tsx`, `workspace.css`, `App.tsx`, cockpit/navigation: focused AI workspace,
  compact navigation and progressive disclosure; legacy routes retained.
- `ai/AIChat.tsx`, new `ai/research-idea.ts`, `research-drafts.ts`, `ai/draft.ts`, `StrategyLab.tsx`:
  validated proposal handoff, owner/retention scope, wizard context and explicit result-review draft.
- `apps/api/ai/context.py`: additive reviewed document assembled from actual baseline definitions.
- `campaigns/CampaignCenter.tsx`: explicit AI default; no campaign backend authority change.
- Native tests for root composer, proposal state/role/access/expiry, bounded draft fields,
  ownership/cleanup and critique deep links. Product E2E retains its assertions and additionally
  requires the assistant region before navigating to the library.

A pre-edit archive/SHA256 inventory preserves 1513 existing Git-selected files in `.cache/ai-lab/`.
No unrelated uncommitted work was reset. No schema migration, credentials or accepted PNG baseline
is changed. No workers are restarted to deploy this UI/context update.

## Actual validation

Exact argv, exit codes and logs are recorded in `.cache/ai-lab/` and sanitized
`docs/ai-lab-evidence/2026-10-29/`.

- `make check`: exit 0, 342 Python and 237 frontend tests, plus lint/mypy/TypeScript/build. A fixture
  typing error during development was corrected by supplying the full real AIJobView shape.
- `.venv/bin/python -m scripts.integration_services --auth-only`: exit 0, 39 before +39 after actual
  PostgreSQL/Redis/MinIO stop/start. Includes a new queued/worker HTTP synthetic-provider round trip
  for the reviewed strategy document and exact baseline digest checks. This is **fixture transport**,
  not OpenRouter or real-model research acceptance.
- `make contracts-check`: exit 0, byte-identical generated contracts. No API schema change.
- `make smoke-demo` and strict `smoke_demo --require-ready`: exit 0. Secret scan, repository
  validation and diff checks also exit 0.
- Playwright collection: exit 0, 30 desktop/mobile cases. Browser execution is NOT RUN; prior managed
  local-origin restrictions are respected. No screenshots/goldens/tolerances were rewritten.
- Full 146+146 integration remains the prior audit checkpoint; the complete suite was not rerun
  additionally to the relevant actual-service suite for this UI/documentation-context change.

Existing bundle-size and httpx deprecation warnings remain. Real-model quality, paid inference,
visual/mobile/keyboard acceptance and positive historical strategy qualification are not claimed.

## Local rollout and owner verification

Local build/rollout and strict readiness pass with exit 0. The deployment manifest confirms only
API/Web container IDs changed, all named-volume mounts and worker/data containers are unchanged,
and served HTML matches the final native build. This is not rendered browser acceptance.
No inference request, broker order, migration or model download is performed.

Reload `/strategy-lab`, submit a research question when actual model readiness permits it, review the
proposal and open its test preparation action. Select real reviewed setup; read the stored result
and explicitly request an AI critique if authorized. No numerical results are invented for empty
histories or missing data.

Owner-local disposable browser verification:

```sh
E2E_ONLY_SCENARIO=product make browser-integration
E2E_ONLY_SCENARIO=research make browser-integration
E2E_ONLY_SCENARIO=ai make browser-integration
```

Browser screenshots need separate actual rendered inspection. Missing historical setup or model
verification must be configured honestly, not bypassed to make the flow appear complete.
