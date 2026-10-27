# Trusted strategy framework — Phase 5

Strategies are reviewed Python implementations in packages/research/strategies.py. The registry permits
only EMA_TREND, MA_CROSS, DONCHIAN, BOLLINGER, RSI, ATR_BREAKOUT, OPENING_RANGE and SESSION_MOMENTUM.
Every definition pins version, implementation source digest, typed parameter schema, asset classes,
data/timeframe contracts, entry/exit/sizing assumptions and quality/warm-up requirements. Source and
software hashes are checked again by the worker. No uploaded source, module name, pickle, eval, exec,
LLM judge or generated-code runner exists. Registered strategies receive visible observations and
parameters only; they receive no database, broker, host-path, Docker, deployment or signing capability.

## Reviewed benchmark conventions

- EMA_TREND compares the current completed close with an EMA and its prior slope. EMA seeds at the
  first admitted close; the declared warm-up is an assumption, not proof of convergence.
- MA_CROSS uses simple moving averages and a fresh fast/slow crossing. Entry requires a flat instrument;
  an opposite crossing schedules an exit. It is not an always-invested reversal guarantee.
- DONCHIAN compares the current completed close with the prior lookback highs/lows, excluding the
  current bar from its breakout channel.
- BOLLINGER uses the previous window's mean and population standard deviation; current-close
  excursions trigger a mean-reversion proposal.
- RSI is a rolling simple-gain/loss (Cutler-style) RSI, not an undisclosed Wilder initialization.
- ATR_BREAKOUT compares the completed close with the previous close plus/minus a trailing true-range
  threshold. The current bar does not set its own prior ATR threshold.
- OPENING_RANGE uses the known observations in the declared opening receipt-time window. Missing tick
  completeness is never inferred; a range from sparse data is an explicit experimental assumption.
- SESSION_MOMENTUM compares the completed close with the first observed opening-window close.
  Session settings use UTC; verified venue and account-policy restrictions additionally apply.

All are experimental benchmarks, with no profitability certification. Long-only, short-only and both
sides are explicit. Required warm-up is max(slow, lookback+1) admitted observations. Future observations
are refused. A strategy cannot optimize parameters or inspect future rows from inside the registry.

## Signals, execution and permissions

EXECUTION pins supply actual bid/ask ticks or explicitly modeled OHLC execution. SIGNAL pins supply
separate completed timeframes; CONFIRMATION pins provide causal optional confirmations. For a separate
signal timeframe, its observation must have been available strictly before the execution observation;
this conservative rule avoids ambiguous ordering inside a shared timestamp. Confirmation staleness and
same/inverse cross-asset direction are explicit parameters. No missing price is interpolated.

Volume, mandatory SL/TP, pending type/offset/expiry and maximum holding requests are typed parameters.
The actual Phase 4 gateway decides legal risk/margin/volume; a strategy never grants capacity.
Signal-dependent exits execute on a later observation. Predetermined duration/session/reset protection
can request exit at the next observable quote; insufficient liquidity delays actual closure, which is
reported rather than invented. Pending remainders are cancelled before strategy liquidation.

Baselines are AUTOMATED/INTRADAY_BENCHMARK. Experiments require an explicitly verified policy permitting
automation and an owner-MFA acknowledgement of the isolated research scope. Declaring automated code
manual is refused. No source account is traded; per-trial simulated accounts copy the reviewed limits
conservatively. Source policy/profile revocation invalidates queued/running work. ALLOW remains
SIMULATED only, with external execution authority always false.
