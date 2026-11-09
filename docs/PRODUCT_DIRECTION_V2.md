# Product direction V2 and project checkpoint

Recorded 2026-10-29 from the owner's explicit product-reset request.
Engineering documentation is English; product language remains Romanian.

## Owner's current objective

Build a simple product centered on a trading-specialized, trained/fine-tuned model. The owner
is dissatisfied with the complexity of the current platform. Three primary destinations only:

1. **Trading dashboard**: automatic trading on owner-added accounts using a selected,
   model-developed and validated strategy; PnL/statistics and an activity/message box explaining
   what the system is actually doing. No fabricated activity, balances or profit.
2. **Strategy Lab**: strategy development and backtesting. Worthwhile validated candidates enter
   the strategy library for selection by the automated trader. Model output alone is not evidence
   that a strategy deserves promotion. Promotion criteria still need a focused definition.
3. **Settings**: all configuration in one place, with precise explanations, prerequisites and
   actionable setup instructions. Technical modules should support these three tasks rather than
   become additional primary navigation destinations.

Desired primary journey: develop a strategy -> evaluate it -> select an eligible version for an
account -> monitor the trader. An owner selects the account/strategy and limits. The model's
research role and the execution engine's deterministic responsibility must remain explicit.

The owner explicitly requests removal of MFA codes. This changes the earlier preference for
repetitive MFA in ordinary application use; do not ask again whether the owner wants that removed.
Default direction is normal password/session authentication without TOTP challenges. Login,
account isolation, CSRF, secret protection and separate external-execution authority still matter.
Do not silently reset MFA enrollment or user records as an implementation shortcut.

The owner subsequently instructed implementation. The three-destination shell, focused dashboard,
Strategy Lab, evidence-gated library and consolidated Settings are now source-implemented. The default
server policy is password/session authentication (`AUTH_MODE=PASSWORD`), with no TOTP challenge.
Existing enrolled secrets and recovery records are retained, not reset. See
[the implementation report](../PRODUCT_V2_IMPLEMENTATION_REPORT.md) for actual validation and local
rollout evidence. This supersedes the earlier documentation-only checkpoint; it does not authorize
external execution or declare a trained trading model available.

Current rollout note: API/Web now serve the new product with PASSWORD policy. Market/research
workers were recovered only after confirming empty queues; both are healthy. The AI worker was
already healthy at this turn's actual inspection and was not restarted. This supersedes the older
stopped-worker observation retained below. No paid request or broker order was initiated.

## Keep product claims honest

A trading-specialized model is the intended center of the product. The repository currently has
a provider gateway and model registry, not a demonstrated trained trading model. A successful
OpenRouter capability probe does not establish trading skill, robust strategy performance or an
autonomous trader. Model selection/training data/rights, training method and validation are still
work to define. No model training or paid infrastructure was initiated here.

Do not discard the existing validated persistence, data integrity, research lineage, risk and
execution-denial components. Reuse them behind the simplified product where useful. Retain the
source and reports while reconsidering the architecture. Do not continue adding phases or
redesigning nine independent technical screens by default.

## Exact technical checkpoint before the rethink

- Persistent owner-scoped AI authorization is implemented. The owner reports activating it.
  It is distinct from worker availability, a valid session and current model verification.
- Schema0010_ai_standing was applied locally; API/Web updated. Native336 Python/222 frontend,
  full134+134 service checkpoint and final focused25+25 across actual restart passed. See
  ../AI_STANDING_AUTHORIZATION_REPORT.md for precise scope, timing and blocked browser acceptance.
- At the last read-only inspection, the AI Center submit button was correctly disabled for
  missing worker heartbeat. ai-worker was EXITED(1), with a PostgreSQL connection refusal.
- The worker targets172.30.61.2:5432 on the private ai_database network. The actual PostgreSQL
  container had been created with compose.yaml only and was attached to control/local_services,
  not ai_database. Its general health could therefore be healthy while the AI worker could not
  connect. The worker has restart policy no and remained stopped.
- The last turn provided, but did not execute, the following owner-local repair:

```sh
docker compose --env-file .env --env-file .env.ai \
  -f compose.yaml -f compose.ai.yaml \
  --profile ai --profile campaigns \
  up -d --no-build --no-deps --wait --wait-timeout 90 postgres ai-worker
```

- Restarting can process approved pending inference; no restart or billable provider request was
  performed by the agent. Do not assume the command subsequently ran without new evidence.
- market-worker/research-worker were also already exited at that inspection.
- Managed browser execution remained blocked; no rendered acceptance was claimed and accepted
  screenshot baselines were not rewritten.
- Live/demo broker submission and generated strategy-code execution remain disabled;
  SIMULATED/DENY_ALL remains the current runtime boundary.
- Existing uncommitted work, credentials, encryption keys and development volumes must be retained.

## Recommended sequence for the new direction

1. Agree the compact product contract and real meaning of a trading-specialized model.
2. Define the strategy artifact, evidence gates and minimal path from Lab to selectable library.
3. Design the three-screen journeys and consolidate useful existing capabilities behind them.
4. Implement the requested password/session authentication migration without TOTP prompts.
5. Complete one real, bounded strategy-development/backtest/library/simulated-execution loop.
6. Validate account adapters and later demo/live eligibility separately, with real service evidence
   and explicit scope. Do not turn on real execution as part of navigation/authentication cleanup.

These are proposed implementation steps, not claims that those capabilities currently work.
