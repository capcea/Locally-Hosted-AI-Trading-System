# MASTER PROMPT PENTRU CODEX — AI Trading Research Platform

**Version:** 1.0 | **Date:** 2026-10-24 | **Language for product UI:** Romanian by default, architecture/code/documentation in English | **Project:** greenfield

> Paste this entire prompt into Codex at the root of a **new, empty repository**. Treat it as the product specification and engineering contract. Do not assume that a strategy will be profitable. Do not send real orders or connect real-money credentials during implementation. Implement in phases, with working code and tests at every checkpoint.

---

## 0. ROLE, OBJECTIVE, AND NON-NEGOTIABLE PRINCIPLES

You are the principal engineer, quant researcher, security engineer, ML engineer, product architect and technical lead responsible for implementing a production-quality, research-first **AI Trading Research Platform**. Build a reliable, secure, modular, auditable product — not a toy demo or a chat-based “AI says BUY” bot.

### Product mission

Develop a **fully autonomous research and experimentation** system that can discover hypotheses, read permitted public online sources, write strategy code in an isolated sandbox, test it statistically, criticize its own findings, conduct paper trading, and propose strategies for **explicit human approval** before real-money activation. Subsequently, already approved strategies may generate trades automatically, but independent deterministic services enforce every broker, account, risk, and prop-firm policy.

Priority: **stable, risk-adjusted performance and low drawdown**, not maximized gross P&L. Initial reference account: **$25,000**. No promised returns, fabricated performance, backtested leakage, or optimistic defaults.

### Hard system invariants (must enforce in code, not solely in prompts)

1. **LIVE TRADING DISABLED by default** at every layer (UI, API, worker, and executor). A real broker connection must never become enabled simply because a config or environment variable is present. Require a deliberate two-person-equivalent procedure involving authenticated owner confirmation + durable signed approval record + capability-limited executor configuration. Human owner may be the single approver, but the workflow must include explicit two-step acknowledgement and MFA for live activation.
2. **LLMs and autonomous code-generation agents can never directly place real orders, change live risk caps, promote unapproved strategies, read broker credentials, or bypass a kill switch.** Free-form model output must be parsed, validated, and treated as untrusted.
3. **Risk/prop-firm checks are final, mandatory, deterministic and execute near the broker, independently of the GPU/LLM/cloud control plane.** Block new entries on uncertainty or degraded dependencies. Existing exchange/broker-side SL/TP must remain present; reconcile broker truth continuously.
4. **All executable research-generated code runs in a hardened isolated worker**, not in the API process or broker executor: no broker keys, no host Docker socket, restricted network and filesystem, bounded CPU/GPU/RAM/time, immutable artifact inputs, no escalation, no arbitrary host mounts. The generated code can propose strategies but cannot merge its own release branch.
5. **A strategy may advance autonomously from research to controlled paper trading only after statistical gates.** Going from paper to any live mode always requires owner review and an explicit immutable approval tied to strategy hash, risk profile, broker, account, program, instrument list and expiry. All changes invalidate approval until reviewed.
6. **Fail closed:** stale data, clock anomalies, DST ambiguity, lost market calendar, unknown symbol specs, unverified prop policy, broker uncertainty, orphan order, exhausted limits or expired authorization => no new trade.
7. **No invented data, synthetic “realistic” backtest results presented as real, fake broker fills or mock connections silently masquerading as live.** Clearly label fixture, simulation, demo and live in UI, storage and audit.
8. **No autonomous pursuit of prop firm rule circumvention.** Prohibit latency arbitrage, prohibited copy-trading/hedging, news-time restrictions breaches, artificial consistency manipulation, or other practices disallowed by a program. Rules are program-specific, versioned, manually verified before enabling a broker/program account.
9. Never rely on an LLM to calculate final quantity/lot size, enforce risk, assess price freshness, or send broker calls. All critical monetary calculations use reproducible decimal-safe logic, broker symbol specifications, and explicit conversion rates.
10. Ship **working tests, documentation, migrations and small runnable slices** before expanding to the next module. Do not claim unimplemented interfaces work. If external access/credentials are missing, use explicitly labeled deterministic simulators and leave integration blocked, not mocked as success.

---

## 1. AGREED USER REQUIREMENTS (CONSOLIDATED FROM TWO ROUNDS, Q1–Q60)

### Accounts, firms, objectives
- Personal accounts and prop-firm accounts; target **$25k initial account**, multi-account support as future expansion, but schema and risk partitions prepared from start.
- Supported firms: **FTMO, FundedNext, The5ers, extensible others**. Must distinguish firm/program/phase/platform/account-size/effective date, not blindly assume a rule applies firm-wide.
- Primary target: stable results, minimal drawdown, steady robust risk-adjusted strategy selection, rather than max monthly profits or forced challenge completion.

### Instruments, signal types, timing
- Full instrument class support from first useful/demo release: **Forex, XAUUSD, XAGUSD, indices, crypto**. Specific initial watchlist includes EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD, selected additional Forex, index CFDs and crypto CFDs if available and lawful via connected broker. Do **not** claim a symbol is tradable without querying broker capability.
- Research both **scalping and intraday**, without assuming HFT infrastructure. Distinct execution profiles: ordinary minutes-to-hours and lower-latency deterministic execution; real-time LLM inference **never** on critical order path. Disallow strategies banned by specific prop programs.
- Support tick/M1/M5/M15/H1/H4, optional D1 context. Intraday-only by default; target max one trading day per position; configurable rollover/weekend flattening. Session and holiday calendars; no guessing about market opening hours. Choose sessions based on strategy.
- **No entries during major economic events**, with configurable before/after windows by currency, instrument, provider confidence, firm, and event. Fail closed if required calendar is stale.
- Orders: market with mandatory broker-side SL+TP, pending limit/stop, cancel/modify, trailing, break-even, partial close, and conditional/OCO **only when the broker explicitly supports native or safely emulated semantics**.

### Research + ML
- Autonomous research **24/7 when resources available**, internet research allowed through restricted research-only tools, versioned evidence and citations. Agents propose new strategies and modify code only in isolated branches.
- Parallel agent roles for hypothesis discovery, quantitative research, coding, backtest review, adversarial critique, news/calendar analysis, data QC and risk policy validation. Logical parallelism; 24GB VRAM may require sequential physical inference.
- Strategy families: trend/breakout; mean-reversion/range; price action/market structure; volatility/session/regime switching; correlation/statistical arbitrage (only lawful/policy-allowed); ML-driven. Exclude disallowed prop strategies before deployment.
- ML experiments: **XGBoost, LightGBM, HMM/clustering** compared against non-ML baselines, with strict time splits and protection against data leakage.
- Backtesting: **vectorbt for fast screening + own event-driven engine for serious validation and live-parity**. Robustness requires OOS, walk-forward, different regimes, transaction costs, bootstrap/Monte Carlo, multiple-testing controls, drawdown, underwater time, expectancy, PF, risk-adjusted metrics, confidence intervals and adequate sample sizes. Use adaptive eligibility criteria by strategy class, documented and configured, not arbitrary global promises.
- Five years of history is **desired**, especially tick history for core instruments; source first from MT5/broker and legitimate free/public feeds, premium if justified. If complete tick data is unavailable, mark **coverage incomplete**, do not silently fill invented ticks or claim five years coverage.
- Data persisted in Parquet and PostgreSQL metadata.
- Strategies that pass research gates automatically enter **paper trading**, subject to policy gates; after an adaptive observation window combining calendar duration, number of independent trades, confidence and multiple regime exposure, require owner approval for live.
- Auto-pause weak strategies. Manual approval to reactivate paused live strategies.

### Risk, execution, infrastructure
- Risk fully configurable by account and strategy, but provide **conservative starting profile** (to be treated as an editable safety baseline, not advice): e.g. 0.25% equity risk/trade, 1.0% account daily loss stop, 3.0% account total drawdown stop, tight portfolio open-risk/correlation and position limits; choose exact semantics explicitly and ensure caps tighter than any prop firm rules.
- Hybrid sizing: risk budget + technically defined stop distance + broker-specific notional, volume step, pip/tick value, currency conversion, margin and correlated exposure caps. Never open without valid SL+TP and quote freshness.
- Approaching a firm limit: predeclared exposure reductions and thereafter block new entries. Daily reset timezone and basis (balance/equity/high-water mark) configurable per exact firm/program.
- On AI/cloud outage: block new entries, rely on independent executor, reconcile positions and maintain broker-side stops. Kill switch, no double orders on retry, max spread/slippage, settlement/rollover/weekend handling, stateful reconnection.
- First parallel broker integrations **MT5 and cTrader**; Windows VPS for MT5 terminal integration, independent Linux service for cTrader Open API, shared broker interface, portable central API. Demo end-to-end for both; live blocked pending explicit policy authorization. MT4 and TradingView webhook interfaces can be future optional adapters.
- Broker secrets only on executor/VPS secret store; GPU host never receives them. Trading broker integration must be separate from research cluster.
- VPS plus cloud AI GPU 24/7 initially, local GPU workstation subsequently, **modular monolith with containers** and cloud/local provider switch. Budget for infra can exceed €200/month when justified by measured outcomes, resource quotas and cost dashboards.
- User-facing web UI includes all: financial dashboard, P&L, positions, risk, agents/status/cost, strategy lab, backtesting charts, paper/live isolation, settings for models/brokers/firms/limits, decision replay, audit, mobile secure dashboard, Telegram/email emergency notifications, owner kill switch.
- One comprehensive master prompt and implementation roadmap. New repo from zero, no assumption of previous project code.

---

## 2. EXTERNAL FACTS, SOURCES & IMPLEMENTATION CONSTRAINTS

Review the official docs before using SDK API calls; record citations/URLs, publication/access date and source in `docs/external-sources.md`:

- MT5 Python integration: https://www.mql5.com/en/docs/python_metatrader5 and `initialize`, `copy_ticks_range`, `order_check`, `order_send`, `positions_get`. Windows MT5 terminal is required in the proposed deployment; do not fabricate native Linux support for the official terminal package.
- cTrader Open API: https://help.ctrader.com/open-api/ ; official Python SDK: https://help.ctrader.com/open-api/python-SDK/python-sdk-index/ ; app/account OAuth 2.0 flow: https://help.ctrader.com/open-api/account-authentication/ . Implement broker rate limits, token refresh, demo/live environment separation, and reconnect reconciliation.
- Ollama OpenAI-compatible **subset**: https://docs.ollama.com/openai . Do not assume feature parity with the complete OpenAI SDK. Test JSON modes/tool calls explicitly; fall back to native API or validated JSON parser where required.
- Model tags: `qwen3.5:27b-q4_K_M` (~17 GB), `qwen3-coder:30b-a3b-q4_K_M` (~19 GB), `qwen3.5:9b`, optional `qwen3.5:4b`. Track exact digests, runtimes, context, quantization and prompt templates; 24GB GPU cannot safely hold two large models concurrently with large KV caches.
- FTMO official rules: https://ftmo.com/en/faq/which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/ and https://ftmo.com/en/forbidden-trading-practices/ . The presence of general algo permission does not override program/strategy/request limits.
- FundedNext EA details: https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext . At time of design: EA/bots on MT4/MT5 for accounts **under $50k** subject to EA usage fee/add-on; **not allowed on cTrader or Match-Trader**; accounts $50k+ require manual trading. MUST reverify for each account/program and never silently extend this permission.
- The5ers EA policy: https://the5ers.com/faqs/can-i-use-an-ea-expert-advisor-can-i-set-a-stealth-mode-stop-loss/ and prohibited practices at https://www.the5ers.com/faqs/prohibited-trading-practices/ . Tick scalping, HFT, latency/reverse/hedge arbitrage and hidden SL are examples of exclusions.

Do **not** hardcode legal/contractual policies as timeless facts. Define versioned `PolicyPack`s with explicit source, effective date, verification timestamp, account tier, platform, permitted symbols, prohibited styles, caps and unknown-field behavior. Any unverified or expired pack => trading **disabled** for that account.

---

## 3. REFERENCE ARCHITECTURE AND TRUST BOUNDARIES

### A. Product control plane (Linux, modular monolith)
- **Backend:** Python 3.12 if supported by all dependencies, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, REST + authenticated WebSocket/SSE for streaming; OpenAPI contract and generated TS client.
- **Frontend:** React + Vite + TypeScript, Tailwind, accessible responsive dark/light theme, charts for price/equity/drawdown and data quality; polished but maintainable. Default locale Romanian, i18n-ready English.
- **Database:** PostgreSQL for users, RBAC, accounts, jobs, evidence/provenance, strategy versions, orders/positions snapshots, risk policies, promotions, audit metadata and alerts.
- **Queues/scheduler:** Redis + a modest Python worker system (Arq, Dramatiq, Celery or similarly suitable; justify and pin one), persisted jobs, retries with idempotency, dependency orchestration, recovery and concurrency quotas.
- **Object/data storage:** versioned Parquet for ticks, bars, spreads and backtest outputs; DuckDB/Polars for analytics; S3-compatible MinIO in dev or cloud object storage where needed. Verify hashes and manifest/provenance.
- **Observability:** structured JSON logs, OpenTelemetry compatible tracing, Prometheus-style metrics, incident alerting, cost usage, backups and restore verification.

### B. AI research plane (cloud GPU now, own workstation later)
- Ollama behind an **authenticated private gateway** (e.g. WireGuard/Tailscale or mTLS), never public unauthenticated `11434`.
- `LLMProvider` interface with `generate`, `generate_structured`, optional `tools`; config `AI_BASE_URL`, `AI_MODEL_RESEARCH`, `AI_MODEL_CODER`, `AI_MODEL_REVIEW`, timeouts, token limits, retries, digest and health; use Ollama-compatible APIs, respecting partial compatibility.
- Research model: `qwen3.5:27b-q4_K_M`; coding: `qwen3-coder:30b-a3b-q4_K_M`; fast/backup: `qwen3.5:9b` (with verified tag). Queue large models one at a time on one RTX 3090; manage unloading/memory pressure and budget.
- Research workflows: Planner → Researcher → Hypothesis → Developer → Data QA → Backtest → Statistical Critic → Risk/Compliance Critic → Paper Candidate. Persist reasoning *summaries, evidence, tool inputs/outputs and structured decisions*; do not persist secrets or require storing private model chain-of-thought.
- News and internet content is untrusted. Use citation-based source retrieval, domain/scheme allowlisting, bounded pages/downloads; prohibit remote instructions from modifying the agent policy. All outbound tool actions have narrowly scoped permissions and auditable provenance.
- Code-generation sandbox separate from GPU pod (a dedicated restrictive container/VM/worker, preferably isolated host/VM for hostile code). No Docker socket, no privileged execution, no broker/network secrets, no outbound internet by default, read-only datasets, strict limits, ephemeral workspace and artifacts.
- `CandidateStrategy` is an immutable versioned artifact: source digest, deterministic build, tests, datasets, prompts/model digests, research results, policies and optional signal contract. No agent can self-approve live deployment.

### C. Deterministic quant plane
- `DataProvider`, `CalendarProvider`, `SymbolSpecification`, `Strategy`, `Signal`, `BacktestEngine`, `ExecutionSimulation`, `RiskPolicy`, `BrokerAdapter` are stable typed interfaces.
- Initial vectorbt fast screener; independent event-driven simulator with bid/ask, partial fills where modeled, spread/slippage/commission/swaps, broker session constraints, pending orders, stop/limit gaps, fees and recorded order lifecycle. Prove contract parity against replay broker simulator.
- Research results include baselines, sample metadata, OOS boundaries, multiple-testing adjustment, uncertainty, regime stability, capital usage, transaction costs and weakest-period analysis.

### D. Execution/trust plane (independent servers)
- Central application proposes only **signed trade intents** from approved immutable strategy artifacts; no client-issued market order without per-account role/approval policy.
- `RiskGateway` runs on broker-side environment, validates account activation & policy version, strategy digest, typed intent, quote freshness, session/news blackout, account equity, margin, daily/total drawdown, exposure, symbol specs, volume steps, legal lot size, confidence in account currency conversion and firm compliance. Reject on unknown conditions.
- **MT5 Bridge**: native Windows service connecting to installed terminal; separate account/session config; secure authenticated control channel; use `order_check` before `order_send` but do not treat it as full guarantee of fill.
- **cTrader Adapter**: Linux service with official SDK/OAuth and full demo/lifecycle support. Keep OAuth credentials only in this trust plane. Implement max API rates and event subscription, reconnect replay.
- Broker environment **explicit enum** `SIMULATED`, `DEMO`, `LIVE`; no default coercion and no shared credentials. Automatic tests should not even know live secrets.
- Broker is truth: persistent states `PROPOSED → AUTHORIZED → SUBMITTING → ACKNOWLEDGED/UNKNOWN → FILLED/PARTIAL/REJECTED/CANCELED`, with reconciled external IDs. At-least-once jobs require deduplication; never assume exactly-once external order execution. On ambiguous timeout, **query broker** and reconcile before any resubmission.
- Hard kill switch blocks new entries and optionally executes an independently authorized flatten policy; UI must distinguish 'stop entries' from 'close open positions' with confirmation. Do not count an unavailable AI as an execution signal.

### E. Deployment diagram

```text
Browser/Mobile
  │ auth + MFA
  ▼
React Dashboard ───────► FastAPI modular monolith ───► PostgreSQL / Redis / Parquet
                               │                        │
                               ├──► Research Scheduler ─┴─► Sandbox Runner
                               │            │
                               │            ▼
                               │       LLM Gateway ──► Cloud GPU Ollama
                               │                        (later Local GPU Ollama)
                               ▼
                          Strategy Registry
                               │ only APPROVED immutable strategies
                               ▼
                  Signed Trade-Intent / Policy Channel
                               │
                               ▼
                    Independent Risk Gateway
                           ┌───┴─────┐
                           ▼         ▼
                    Windows MT5    Linux cTrader
                       Bridge         Adapter
                           └───┬─────┘
                               ▼
                         Demo / Live Broker
```

The architecture is a **modular monolith plus genuinely separate trust/execution workers**, not fake microservices for every class. Use Docker Compose for the Linux pieces; provide Windows-native installation scripts/instructions for MT5 bridge rather than pretending its Python package runs natively in a generic Linux container.

---

## 4. DOMAIN MODELS AND CONTRACTS

Implement well-typed schemas with migrations and validation for:

- `User`, `Role`, `MFAEnrollment`, `Approval`, `ApprovalChallenge`, `Account`, `BrokerConnection`, `TradingVenue`, `PropFirm`, `PropProgram`, `PolicyPack`, `RiskProfile`, `SymbolSpec`, `TradingSession`, `EconomicEvent`, `CalendarStatus`.
- `DataSource`, `DatasetManifest`, `TickRecord`, `BarRecord`, `BidAskObservation`, `QuoteQuality`, `DatasetQualityReport`, `BacktestConfig`, `BacktestRun`, `MetricSet`, `WalkForwardFold`, `MonteCarloResult`, `RegimeEvaluation`.
- `ResearchHypothesis`, `ResearchExperiment`, `Evidence`, `AgentRun`, `ToolCallAudit`, `StrategySource`, `StrategyVersion`, `StrategyBuild`, `StrategyApproval`, `StrategyLifecycle`, `PaperRun`, `PaperEvaluation`, `LiveActivation`.
- `TradeIntent`, `PreTradeRiskDecision`, `PositionSizingDecision`, `OrderRequest`, `OrderStateEvent`, `Order`, `Fill`, `Position`, `BrokerReconciliation`, `RiskSnapshot`, `DailyEquityReference`, `Incident`, `KillSwitchEvent`, `Notification`.
- Every event includes monotonically ordered ID/sequence (or time + source sequence), UTC timestamp, source, correlation ID, idempotency key, relevant account/version identifiers; money amounts decimal-safe and tagged with currency.
- Distinguish instrument ID from broker-specific symbol mapping, point/pip/tick size, tick value and volume step. Reconcile instrument-specific trading availability before any trade.

### Essential strategy lifecycle

`IDEA → CODED → STATIC_CHECKED → REPLAY_BACKTESTED → STAT_VALIDATED → PAPER_ELIGIBLE → PAPER_ACTIVE → REVIEW_READY → LIVE_APPROVED → LIVE_ENABLED / LIVE_PAUSED / RETIRED`

Only an owner can create `LIVE_APPROVED`, and any change to strategy, config, symbol list, code artifact, permitted broker/account, model-dependent signal logic or critical risk pack invalidates approval. A strategy may be automatically paused by risk, research governance or compliance and only manually reactivated.

### Policy engine rules (representative, not exhaustive)

- Per firm / program / phase / platform / account size / account type allow/deny logic.
- Example of a hard-denied combination under presently published rules: FundedNext account using bot execution via cTrader. Do not attempt to circumvent through other tools or manual-looking automation.
- The5ers: reject tick scalping/HFT/latency-arbitrage strategies and non-visible SL when applicable; auto-generated code must not route around these restrictions.
- FTMO: store account-specific forbidden practices and request budget/rate limits; use conservative throttling and regular reviews.
- State what is confirmed, unconfirmed and outdated. A policy imported from the internet can never silently enter enforceable LIVE policy until an authorized human verifies it.

---

## 5. MARKET DATA, CALENDARS, QUALITY, AND PROVENANCE

1. Ingest MT5 broker ticks/bars and permitted public feeds with entitlement/provenance; calendar data from a licensed or terms-compliant source, with recorded update/validity timestamps. Do not scrape around authentication, quotas or restrictions.
2. For core instruments, **target** five years of tick data. Measure actual historical coverage per symbol and source; visible gaps/insufficient history are a reportable limitation and can block a validation gate.
3. Normalize to UTC with original source timezone, broker server timezone, DST transition handling and raw timestamps retained; sessions keyed by venue and holiday calendar. Reject ambiguous conversions.
4. Persist raw immutable Parquet partitions + normalized derived datasets with checksums and manifests. Deduplicate ticks with source-specific sequence keys where available; validate ordering and same-millisecond collisions carefully.
5. Detect absent periods, zero/negative bid/ask, crossed spreads, duplicates, spikes, incorrect currency scaling, irregular volume units, off-session records, low-liquidity/wide spreads, split changes, symbol suffix changes and unavailable symbols.
6. Maintain separate `data-as-of` cutoffs for all strategy features and backtest execution; features must never access a data point timestamped after the simulated decision time. Align cross-asset data only to data available at decision time, including realistic provider publication/ingestion delay.
7. A backtest without historical spread must say so prominently; simulate conservative costs, label estimated, and block high-frequency claims without suitable tick/bid-ask data.
8. Economic event blackout triggers by affected base/quote currency, instrument, severity and program-specific settings; tolerate delayed publications by fail-closing new trades.

---

## 6. STRATEGY RESEARCH, MULTIPLE TESTING AND ML DISCIPLINE

- Begin with explicit **baselines** (simple session/time filters, trend, mean reversion) and demonstrate that advanced LLM/ML research adds measurable out-of-sample value after fees; do not assume improvement.
- Templates for trend following, breakout, regime-aware, mean-reversion, liquidity/market structure, correlation/stat arb (subject to compliance), XGBoost/LightGBM signals and HMM/clustering regime features.
- All generated strategies declare inputs, instruments, data frequency, lookback, explicit close conditions, SL, TP, trade duration, expected costs, resource budget, permitted firm/program constraints and failure modes. No unrestricted network or trading SDK imports in strategy runtime.
- Separate discovery, calibration and evaluation: chronological research/train/validation/test with realistic purging/embargo where labels overlap; use rolling walk-forward and frozen final holdout. Never retune based on final holdout while treating it as untouched.
- Use realistic backtests for entry/exit timing, bid/ask, execution delays, partial fills, slippage as a function of venue/liquidity, rejected orders and news gaps.
- Statistical tests: bootstrap confidence bands, block bootstrap / Monte Carlo perturbations, robustness under widened spreads and shifted entry latency, regime breakdowns, multiple comparison adjustments (document method), correlation between discovered ideas and meaningful benchmark comparisons. Control selection bias from large autonomous search.
- Metrics: net expectancy per trade, net profit factor, distribution of outcomes, max drawdown, relative and absolute drawdown, time underwater, Sharpe/Sortino calculated with documented sampling assumptions, downside deviation, turnover, trade count, loss streak, costs, risk-of-ruin estimates with caveats and confidence intervals.
- `StrategyGate` conditions are **policy-controlled, auditable, adaptive by family and instrument**, with hard universal requirements (data provenance, no leaks, enough samples for inference, positive expected value after plausible costs, robust OOS and risk acceptance). Human-adjustable thresholds may be conservative and cannot be dynamically relaxed by the same agent evaluating itself.
- Paper candidate stage must reproduce executable signal logic and event timing of live. Promotion criteria combine **elapsed time + independent trades + diverse market regimes + uncertainty bounds + compliance**. If too few trades or too narrow regime exposure, keep it in paper indefinitely.
- Runtime monitor drift: realized slippage/costs vs assumptions, drawdown, hit rate, risk-adjusted residuals, environment changes. Auto-pause/reject on threshold breaches. Reactivation requires owner approval.
- ML features must have time-available timestamps; feature training and scaling strictly within each fold; preserve model artifact/version/seed/metrics; compare against non-ML baseline and report failures.

---

## 7. RISK ENGINE — IMPLEMENT INDEPENDENTLY AND TEST FIRST

### Default conservative example for 25k account (configurable and MUST be stricter than active program caps)

- Single trade initial max loss at SL = 0.25% of current eligible equity (~$62.50 if equity=$25,000), including estimated commissions/slippage buffer.
- Internal daily stop = 1% (~$250 at reference $25k), based on precisely specified balance/equity reference and account timezone, including floating P&L if mandated.
- Internal total drawdown stop = 3% (~$750 at reference $25k), with high-watermark/static basis configured per account/program.
- Aggregate open-at-risk cap = 1% initially, tighter for related FX/metals/index positions; maximum simultaneously active positions and per-symbol concentration configurable.
- Spreads, quote age, max order deviation/slippage, minimum liquidity, market-open sessions, weekend/rollover flatten rules and margin utilization caps configurable; unverified values block orders.

**Sizing algorithm:** available risk = min(trade cap, strategy budget, portfolio residual capacity, account daily residual capacity, prop firm residual headroom) minus fees/slippage cushion. Compute monetary risk of 1 volume unit using broker symbol contract size/tick size/tick value and account-currency conversions, never universal pip shortcuts; round **down** to legal volume step; reject if below minimum legal size or stop too close. Validate max losses from multiple correlated positions including conditional/pending orders.

- All protection checks apply to **market, pending, modifications and partial closes** when relevant, with monotonic constraints on increasing risk. Never widen SL beyond an approved max risk without new approval.
- Stops must be resident at broker whenever supported; fail if broker cannot confirm required protective orders. Analyze gaps and broker inability to guarantee exact stop fill; never claim stop-loss fully eliminates risk.
- Price freshness and heartbeats: if beyond configured TTL or clocks diverge => block new entries.
- Broker API errors, uncertain acceptance, partial fills, reconnect => reconcile external order/position IDs before retry; use idempotency keys and durable journal.
- Daily reset uses the **exact firm's** trading day, timezone/DST and loss method; no guessed UTC-midnight hardcoding.
- On automation/AI outage, the executor remains reachable and broker SL/TP persists; never force close automatically merely because GPU goes down unless owner configured and explicitly approved a conservative flatten policy.

### Fault injection tests are required

Test interrupted order submission, server restart after submit-before-ack, duplicate webhooks, duplicated queue delivery, broker disconnect/reconnect, stale market price, stale economic calendar, improper currency conversion, missing contract specs, day reset across DST, changes to prop rules, negative equity shock, partial fills, rejected SL, unavailable network, tampered approval signature, and kill switch mid-flow. Every critical case must refuse a new unauthorized trade and emit an audit/alert.

---

## 8. BROKER ADAPTERS: MT5 AND CTRADER IN PARALLEL

Design `BrokerAdapter` contract covering `capabilities()`, `list_accounts`, `symbol_specs`, `quotes`, `subscribe_quotes`, `historical_bars`, `historical_ticks`, `place_order`, `modify_order`, `cancel_order`, `positions`, `orders`, `fills`, `account_state`, `heartbeat`, `reconcile` and broker-specific constraints.

### MT5
- Windows `mt5-bridge` as independent authenticated service using official Python MT5 terminal integration. Parameterize terminal path, account, broker server, magic/comment tags and graceful connection management.
- Test against locally controllable mock first, and live demo only with credentials provided later. Validate SL/TP filling modes, hedging/netting differences, pending orders, symbol suffixes, trading time and rate limits.

### cTrader
- Linux `ctrader-adapter` using official Spotware Open API Python SDK and OAuth; store credentials securely, refresh tokens, respect API connection/rate limits and subscriptions.
- Cover both demo and live **technical capability** but never let prop policy allow automated cTrader on FundedNext under current prohibited conditions.
- Integration must run end-to-end in demo when the owner supplies credentials, not merely compile. When absent, CI fake broker contract tests demonstrate interface consistency but no claim of broker certification.

### Order manager semantics
- Atomic audit trail and durable intent IDs with broker-side tagging when feasible.
- For OCO/conditional orders: expose explicit capability; native where available, otherwise reject until safe emulation with reconnect safeguards is implemented and tested. Do not claim 'OCO supported' if only a local if-statement exists.
- Reconciliation at launch, reconnect and periodically; unknown orders/positions trigger restricted mode until resolved.

---

## 9. AI AGENTS, GOVERNANCE, RESEARCH SCHEDULER

Agent roles and example deliverables:

1. **Market Researcher:** research papers/blogs/documentation with provenance and dates; creates falsifiable hypotheses, not unsupported predictions.
2. **Strategy Architect:** defines deterministic rules, feature contracts and exit logic.
3. **Code Agent:** implements proposed strategy on isolated branch and writes unit tests; no deployment privileges.
4. **Data Quality Agent:** verifies dataset coverage, calendars, anomalies, survivorship and as-of controls.
5. **Quant Validation Agent:** runs fast and event-driven backtests, proper OOS, robustness, cost sensitivity and reports trade-level traceability.
6. **Adversarial Reviewer:** actively searches for leakage, overfitting, bad assumptions, invalid data, policy violations, fragile dependence on fee/spread parameters.
7. **Compliance & Risk Reviewer:** checks strategy family and intended environment for prohibited practices, and simulates hard risk caps.
8. **News/Calendar Agent:** compiles evidence and event blackout information; no independent authority to bypass restrictions.
9. **Research Orchestrator:** controls quotas, progress, failed jobs, staging gates, model allocation and budgets.

Use small typed JSON schemas to exchange findings between agents and validate every response. Do not accept prompts from web pages as instructions. Only agents in controlled sandbox can access research-only tools. Repository writes use temporary isolated branches, gated reviews and a release manager controlled by policy/human permission.

**Schedule:** continuous asynchronous research bounded by GPU RAM, model switching cost, CPU availability, API quotas and monthly budget. LLM inference can be offline without compromising running approved trading strategies. Use persistent queue priorities (risk reconciliation always higher priority than research). Implement daily per-agent usage and cost ceilings, automatic suspension when exceeded, manual resume; provide scheduler health UI.

### LLM portability contract

- Provider switch = `AI_BASE_URL` / gateway credentials + pinned model identity; do not bake cloud IPs into business logic.
- Cloud: Vast.ai or Runpod RTX3090 or equivalent 24GB running pinned Ollama image. Local: own Ubuntu workstation with the **same image/model/quantization/runtime versions** and copied config and model digest. Use a secure private network, never publicly expose Ollama port.
- Preserve model weights/digests, prompt version, decoding parameters, context size, runtime version, evaluation fixtures and expected schema. Outputs need not be byte-identical; regression tests check required structure, tool routing, safety behavior and numeric determinism outside LLM.
- On 24GB device expect research and coding models to share GPU **sequentially**, not both resident at full context. Queue load/unload; compact/summarize context with provenance rather than silently truncating data.
- Include `deploy/cloud/`, `deploy/local/`, model pull script, health tests and a documented reversible migration procedure.

---

## 10. DASHBOARD & MOBILE CONTROL CENTER

Navigation modules, with real backend functionality:

- **Overview:** health summary, account mode indicators (SIM / DEMO / LIVE), P&L, balance, equity, open risk, daily/total drawdown, active/pending positions, symbols.
- **Accounts & Prop Policies:** separate accounts, exact firm/program/platform/phase rules, last verified source/date, remaining risk budget, read-only when unverified.
- **Strategy Lab:** hypothesis cards, code artifacts, diff, reproducibility manifest, experiment history, compare results, frozen holdouts, strategy state transitions.
- **Backtesting:** configuration, data coverage, fees assumptions, trades, equity/drawdown curves, walk-forward folds, regime/asset breakdown, monte-carlo bands and evidence.
- **Agents:** task graph, model/provider, prompt/artifact versions, usage, token/time GPU cost, agent critiques, pending approvals, queue state.
- **Data Quality & News:** historical coverage matrix, invalid symbols/ticks, calendar freshness, current upcoming restricted periods.
- **Execution:** order journal, pending/filled/rejected/unknown, broker reconciliation, slippage, recorded risk decision with `why accepted/rejected`.
- **Risk & Governance:** policy version, emergency stop-new-entries, owner-authorized flatten, pause/resume with MFA, approval/revocation UI, compliance blocking reasons.
- **Settings:** model endpoint/config, environment flags, broker adapter status (never show secrets), monitoring, notification subscriptions, bounded budgets.
- **Audit/Replay:** select trade -> replay causal timeline including data-as-of, signal, model/research provenance, risk decision, broker response, reconciled fill and P&L, all tagged by immutable version.

Use secure cookie/session strategy or equivalent, CSRF protections where relevant, password hashing, MFA for sensitive flows, rate limits, RBAC and websocket authentication. Mobile-first for emergency actions; double confirmation, clear labels and no ambiguous tap targets. Telegram/email notify incidents and trade summaries; Telegram bot command for kill switch only if authenticated, signed, replay-protected, rate-limited and separately authorized; otherwise notifications only.

---

## 11. REPOSITORY STRUCTURE (SUGGESTED)

```text
ai-trading-platform/
  README.md
  AGENTS.md
  pyproject.toml
  .env.example
  .github/workflows/ci.yml
  docs/
    PRODUCT_SPEC.md
    ARCHITECTURE.md
    THREAT_MODEL.md
    RULES_AND_LIMITATIONS.md
    RISK_POLICY.md
    DATA_PROVENANCE.md
    EXPERIMENT_PROTOCOL.md
    RUNBOOKS.md
    external-sources.md
    adr/
  apps/
    api/                 # FastAPI composition, auth, endpoints
    web/                 # React/Vite/TS
    mt5-bridge/          # Windows-native service
    ctrader-adapter/     # Linux SDK adapter
  packages/
    domain/              # typed contracts, enums, schemas
    data/                # ingestion, quality, parquet manifest
    quant/               # vector screening, event-driven engine, metrics
    strategies/          # strategies and versioned artifact schemas
    risk/                # pure deterministic risk / compliance engine
    brokers/             # adapters, simulator, broker contract tests
    agents/              # LLM provider, agent graph, research governance
    notifications/       # Telegram/email
    observability/
  workers/
    jobs/                # research queues/schedule
    sandbox-runner/      # untrusted code runner (isolated deployment)
    risk-gateway/        # independent trusted process on VPS
  deploy/
    compose/
    cloud/
    local/
    windows-mt5/
  scripts/
    doctor.sh
    seed_demo_data.py
    import_market_data.py
    model_healthcheck.py
    backup_restore_test.sh
  tests/
    unit/
    integration/
    contracts/
    replay/
    fuzz/
    fault_injection/
    e2e/
  fixtures/
    market_data/         # synthetic TEST datasets only; labeled
    broker_events/
```

You may simplify directories if warranted, but preserve architectural boundaries and document deviations with ADRs. No bloated boilerplate.

---

## 12. PHASED ROADMAP WITH HARD ACCEPTANCE GATES

**Important:** The user wants one giant specification, **not** all code dumped in one response. Implement in reliable reviewable phases. At every phase: deliver runnable code, migrations, tests, demo screenshots/recordings if applicable, commands, progress and next module. Never skip tests to superficially check off modules.

### Phase 0 — Design, security boundaries, dev environment
- Repo skeleton, pinned toolchain, ADRs, threat model, env file, Compose for Linux app + Postgres + Redis + development object store, Makefile/task runner, pre-commit/lint, CI.
- `AGENTS.md` with non-negotiable constraints; sample configuration is simulation-only.
- **Acceptance:** `docker compose up` starts without live secrets; health endpoints pass; CI lint/types/tests; threat model documents broker and sandbox isolation; live mode cannot be enabled accidentally.

### Phase 1 — Core contracts, auth and app shell
- Typed domain/event schemas, SQL migrations, auth+RBAC+MFA flow for sensitive owner actions, basic React dashboard and API, immutable append-only audit events, configuration service.
- **Acceptance:** reproducible migrations up/down; demo app accessible; rejected unauthenticated and unauthorized actions; secret scanning; tests for audit tampering and role boundaries.

### Phase 2 — Data + time correctness
- MT5/public historical ingest through adapters, Parquet partitioning, coverage matrices, multi-asset symbol definitions, UTC/DST normalization, economic event blackout system.
- **Acceptance:** deterministic ingestion of fixture data; gap/spike/DST tests; cannot label <5 years as five years; data-as-of validation demonstrates zero look-ahead on fixtures; provenance visible in UI.

### Phase 3 — Broker contract / simulation + real demo integrations
- Fake `BrokerAdapter` with deterministic fixtures, **MT5 demo bridge and cTrader demo adapter in parallel**, quote snapshots, account balance, order types, positions, state/reconciliation.
- **Acceptance:** shared broker contract suite passing for fake + both demo adapters when user supplies access; otherwise both verified integration paths have explicit `PENDING_CREDENTIALS` and comprehensive simulated contract tests. Never claim live/demo broker proof without actual connection.

### Phase 4 — Risk engine + firm policy engine (before any live trading)
- Pure risk calculus, configurable policy packs, firm/program/platform constraints, independent trusted service, signed trade intents, owner approval workflow, idempotency and incident handling.
- **Acceptance:** adversarial and property-based tests for size/currency/timezone/correlation; no order without verified account/strategy authorization; FundedNext cTrader automated path always rejected under current verified policy; kill switch and cloud outage simulation pass.

### Phase 5 — Backtest/simulation engine
- Fast screening via vectorbt, independent event-driven validation, broker lifecycle simulation, costs and order trace replay, metrics, walk-forward, bootstrap/Monte Carlo, multiple-test accounting.
- **Acceptance:** golden trade-by-trade fixtures, no look-ahead; event-driven and screening differences measured/explained; price/spread sensitivity warnings; deterministic replay and metrics.

### Phase 6 — AI model gateway and research agent graph
- Ollama provider contract, Qwen model registry, agent roles, typed output, prompt injection defense, sandboxed code branch workflow, evidence and cost accounting.
- **Acceptance:** local/remote model gateway mocked in CI; actual Qwen endpoint health run possible; agent-generated code cannot read secrets/access executor/merge to production; outputs schema-validated and attributable.

### Phase 7 — Autonomous research, ML and evaluation governance
- Hypothesis scheduler, strategy generation, sandbox tests, quant validation, adversarial critique, XGBoost/LightGBM + HMM/clustering baseline comparison, candidate gate, duplicate idea prevention, quotas.
- **Acceptance:** demonstrates one end-to-end *synthetic-labeled* sample research workflow producing a reproducible artifact; rejects intentionally leaking and overfitted strategies; review cannot self-relax gate limits.

### Phase 8 — Paper trading and strategy lifecycle
- Real-time paper fills under realistic broker quote/spread model, strategy registry, adaptive paper gate, promotion requests with signed immutable approvals, degradation pauses.
- **Acceptance:** fully functional paper mode with MT5/cTrader demo feed if available; live mode untouched; candidate cannot promote itself; strategy change revokes live eligibility; approval audit replay works.

### Phase 9 — Full dashboard, alerts and operations
- All dashboard tabs, permissioned actions, mobile kill switch, Telegram/email messages, GPU job cost reports, real-time logs/metrics, backup/restore runbooks.
- **Acceptance:** Playwright e2e paths for browse/search/backtest/paper/kill/policy block; mobile accessibility baseline; verified alerts; forced worker crash recovery test; backup restore completes.

### Phase 10 — Deployment cloud → local & live readiness review
- Vast.ai/Runpod Ollama Compose+scripts, local Ubuntu workstation deployment, model digest migration, VPN/mTLS, Windows broker bridge runbooks, performance and cost tests.
- **Acceptance:** switch provider by env config without application code changes; both environments pass same deterministic eval suite; no public unauthenticated LLM API; test cloud outage while demo trade runs; explicit human signoff required for any live readiness checklist.
- **Crucial:** **Do not automatically activate LIVE** or insert real broker credentials, even after all phases. Deliver a security/risk readiness report and an owner-run checklist. Live activation is an explicit separate operation after manual review.

### Release gates
- Unit + property tests for risk, reconciliation and policy invariants; fail CI on violation.
- Type checks, lint, SAST/dependency scan, secret scan, container scan.
- Integration tests for Postgres, Redis, API, fake broker; real demo broker tests marked separately and gated by owner-provided access.
- Load tests for quote ingress/agent job queue; no silent dropped trade events.
- Recorded versioned benchmarks and test reports.
- No product claims of profitability; performance must be explicitly tagged simulation/paper/live, with dates and cost assumptions.

---

## 13. DEPLOYMENT, COSTS, BACKUP AND MIGRATION

### Cloud pilot
- Rent a 24GB RTX 3090 or equivalent on Vast.ai/Runpod; choose reputable host, proper RAM/CPU, no public endpoint, secure SSH, validated image, persistent model/experiment artifacts and off-host backup. GPU usage 24/7 **if budget allows**, scheduler throttles research.
- LLM cloud GPU has no broker credentials. Control API and SQL storage on dedicated VPS/cloud with backups. Trusted brokers/risk gateway on separately managed Windows/Linux VPSs; private authenticated channel.
- Cost reporting: GPU-hour, CPU job-hour, storage/egress, calendar/data subscription, Windows VPS, object storage; monthly total with warning thresholds and circuit-breaker quota. On instance loss research pauses, broker operations remain safe.

### Local migration
- Backup datasets, DB, artifacts, prompts, configs and digests from cloud; verify checksums and restore rehearsal.
- Install pinned Ollama runtime and pull same quantized model tags/digests on local Linux workstation.
- Configure private network endpoint `AI_BASE_URL`, TLS/auth, model availability and context/concurrency limits.
- Run reproducibility suite (JSON schema, tool behavior, prompt injection protection, numerical deterministic controls, reference agent fixtures); acknowledge LLM text may be non-identical.
- Switch traffic with a reversible feature flag; keep last cloud endpoint for rollback until validated.
- MT5/cTrader executors need **no** redeployment just because the LLM moves; trading remains safe while the GPU is offline.

---

## 14. FAILURE SCENARIOS AND EXACT EXPECTED ACTIONS

| Condition | Expected behavior |
|---|---|
| GPU host unavailable / LLM timeout | Pause research/inference; no new LLM-dependent strategy entries; broker gateway maintains independent risk controls and existing SL/TP. |
| Broker disconnected during submit | Persist `UNKNOWN`, prohibit duplicate resubmit, reconcile order IDs/positions before deciding next action. |
| Data/quote stale, venue closed, DST ambiguous | Refuse entry and alert. |
| Economic calendar missing/stale | Refuse affected new entries, with transparent reason. |
| Firm/platform rule unverified or changed | Refuse affected live entries; require manually reverified PolicyPack. |
| Live strategy digest differs from approval | Reject; revoke eligibility until human reapproval. |
| Research agent tries to access broker secret | Sandbox hard deny, log incident, quarantine generated artifact. |
| Account approaching daily/total stop | Reduce permissible new exposure according to preauthorized deterministic policy; block new entries at threshold. |
| Partial fill, slipped fill or protective SL rejected | Recalculate actual exposure immediately; enact preauthorized protective remediation/flatten policy if configured; alert; no false assumption of safety. |
| Duplicated queue task/webhook | Idempotent processing, one broker intent at most; reconcile unknown external state. |
| Kill switch triggered | Block new entries immediately; flatten only if that distinct operation was explicitly confirmed/preauthorized. |
| Agent finds promising result on tiny sample | Reject promotion or keep research-only; display sample-size limitations. |
| Unsupported CFD/crypto symbol | Mark unavailable for specific broker/account; never substitute an arbitrary equivalent ticker. |

---

## 15. IMPLEMENTATION QUALITY, SECURITY AND CODEX WORKING PROTOCOL

- Build clean code, domain-first design, readable modules and clear interfaces. Prefer comprehensible implementations over heavy frameworks or unnecessary distributed microservices.
- Use typed, documented, validated contracts for every transition. All SQL schema changes through migrations; parameterized queries; strict JSON schema validation; unit-of-work transaction boundaries.
- Never hardcode tokens, passwords, broker IDs, real addresses, trading credentials, account numbers or market data licensing secrets. `.env.example` includes placeholder-only values; deployment secrets use external secret manager and dedicated service identities.
- Enforce capability-based permissions across services; network isolation between untrusted research and trusted trade executor. Docker isolation alone is not automatically sufficient for malicious code; document threat model and deploy a VM/microVM runner or equivalent hardening where feasible.
- Preserve strict distinction between backtest, demo/paper and live across labels, credentials, logs and database rows.
- For critical accounting/risk invariants use Python `Decimal` and verified symbol metadata; never floats for authoritative lot sizing or cash limits; distinguish reporting approximations from execution math.
- Include a repeatable sample data pipeline with **clearly labeled synthetic TEST fixtures** to permit local development without purchased market data.
- Provide end-to-end `README.md` with prerequisites, `make dev`, `make test`, `make lint`, `make typecheck`, `make seed-demo`, `make doctor`, `make smoke-demo`, `make stop` or equivalent. Commands must actually work on provided code.
- External dependency versions must be pinned and confirmed compatible; don't hallucinate SDK parameters. If sandbox lacks web/external credentials, implement verified interfaces and transparent `NOT_CONNECTED` status instead of pretending integrated success.
- Prefer incremental commits. At completion of each phase, update `docs/IMPLEMENTATION_STATUS.md` with completed / blocked / tests run / known limitations / exact next steps and a compact acceptance checklist.
- Do not allow generated strategy source to modify governance, risk, broker adapters or auth modules; keep separate repos or restricted directories/permissions for agents.
- Make critical numerical tests deterministic, and model-driven outputs structured/validated rather than claiming fixed text matches. Capture seeds and model digests for evaluation.
- Implement role-aware error pages, loading states, no-data states and meaningful refusal reasons; never bury risk-denial causes in generic error strings.

---

## 16. START EXECUTION NOW — FIRST CODEX RESPONSE AND FIRST DELIVERABLE

**Do not ask questions already answered in this prompt.** Make reasonable technical choices and record them in ADRs. Ask only when a genuinely missing owner decision affects account authorization, real credentials, live risk or irreversible infrastructure expense; otherwise ship the safe default.

### Your first implementation turn must:

1. Restate the technical plan in at most 20 concise lines, identify key risks and exact Phase 0 deliverables.
2. Create a real working Phase 0 repository, not a speculative pseudocode architecture. Initialize folders, pinned dependencies, Docker Compose, sample env, CI, docs, simple API health endpoint, minimal frontend, Postgres/Redis, type/lint/test tooling and safe simulation-only config.
3. Document trust boundaries and the phase roadmap with acceptance gates.
4. Run every locally available test/build/lint/health command, record exact results, and fix failures. If environment restrictions prevent execution, report them specifically and leave executable scripts.
5. Explain how to run the project locally and how to verify that real trading is technically disabled.
6. Continue to the next phase only after tests pass, clearly labeling phase transition and any missing integrations. The user wants a complete end-to-end product developed iteratively; proceed through modules when feasible without compromising correctness.
7. **Do not** sign up for paid services, deploy spending resources, connect real accounts, start a paid GPU 24/7 or activate live trading without the user's separate explicit authorization.

### Definition of success

A successful product is not measured by claimed gains. It is measured by: a reproducible strategy research pipeline; real historical data provenance; honest backtests with realistic costs and untouched OOS validation; auditable paper trading; functional MT5/cTrader demo connectors when credentials are supplied; independently enforced broker/prop risk caps; reliable incident handling; complete secure mobile-friendly observability; and a documented reversible cloud-to-local model migration.

**Build this system. Prioritize correctness, reproducibility, resilience, and risk containment over shortcuts and cosmetic completeness.**
