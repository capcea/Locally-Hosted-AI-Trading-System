# Risk calculation specification — Phase 4

Scope: deterministic SIMULATED accounting, never a broker balance, tradability assertion or performance claim.
Implementation: packages/risk/{contracts,sizing,ledger,clock,gateway}.py. Money arrives as finite bounded
Decimal strings; authoritative calculations use Decimal with local precision 80. Risk and margin round
up to 8 decimal places; available budgets round down. Ledger accounting preserves 12 decimal places.

## Supported payoff and currency contracts

LINEAR_CONTRACT uses contract_size × price change × volume; supplied tick value must equal
contract_size × tick_size. LINEAR_TICK uses tick_value_profit_currency / tick_size as the multiplier.
Forex requires explicit base/quote currencies. Metals (including separate gold/silver contract sizes),
indices and crypto support these explicit linear conventions. INVERSE, unverified payoff, contradictory
currency/tick metadata, missing margin, future/stale symbol evidence and missing stop-distance facts
fail closed. No approximate pip value, exchange margin model or actual broker capability is inferred.
Margin is explicitly attested fixed account-currency margin per volume unit; other conventions need
new verified implementations. Contract fixtures prove arithmetic, not external product certification.

Convert losses conservatively using direct ask or inverse bid; convert positive proceeds with direct
bid or inverse ask. FX edges must be observed, available and valid at the decision, no older than 30s.
At most three edges are accepted. Missing paths or unequal alternative paths refuse sizing. Symbol,
quote, trading-session and calendar validation also runs in the gateway; sizing alone grants no authority.

## Budget and sizing

Entry is pending order price or current executable ask for BUY / bid for SELL. Required SL and TP must
be on the legal tick grid, on the correct sides and satisfy the explicit minimum distance.

Per-unit monetary risk = (absolute entry-to-stop distance + entry/exit adverse slippage buffers) ×
payoff multiplier × loss conversion + round-trip commission + funding buffer. Actual-fill validation
uses the actual entry and only the remaining exit buffer; it cannot exceed the proportional original
signed reservation. Known negative modeled funding over the maximum holding period increases an
insufficient owner buffer. Unknown funding conventions remain explicitly unverified assumptions;
continuous synthetic accrual is not a broker rollover/swap calculation.

Available budget is the minimum of equity × per-trade cap, remaining aggregate and correlation-group
caps, daily headroom and total headroom after initial-capital buffer and existing allocated exposure.
At the configured warning utilization (default 80%), new per-trade budget is capped at its configured
multiplier (default 0.5). Losses never increase the allowed percentage. Margin is independently bounded.
Maximum volume = floor_to_step(min(budget / unit risk, margin available / margin per unit, symbol max)).
Below-minimum volume refuses; a requested volume above that maximum refuses rather than rounding up.
What-if auto-sizing returns this legal volume without creating a reservation, grant or emergency action.

## Account ledger and references

Balance = declared synthetic account initial capital + sum(run cash − that run's initial balance).
Every run must use the account initial capital, preventing multiple runs from multiplying capital.
Equity adds executable-side unrealized P&L converted conservatively. Realized P&L, commission, funding,
open/pending/reserved risk, margin, positions and correlation/strategy allocations remain separate.
Projection advances known funding liabilities across runs; committing a run charges them once.

Exposure retains the greater of measured open+pending risk and durable allocation; UNKNOWN retains
its full reservation. Partial hedged fills/closes release only verified portions. Netting retains the
original conservative allocation until flat. A stop is an estimate: gap losses can exceed it.

Policy supports balance/equity/max/initial daily references; initial or daily-reference amount basis;
static, trailing balance or trailing equity total drawdown; initial or high-water amount basis; and
explicit floating P&L / fee treatment. Internal daily/total ceilings additionally constrain the policy.
Daily headroom = loss allowance minus measured loss from the selected daily reference. Total headroom
uses the configured static/high-water floor. Negative verified headroom stays visible during a STOP;
unverified observations instead display unknown values. Hash-verified chained snapshots retain anchors.

Reset boundaries use an IANA zone, local minute and explicit earlier/later DST fold. Nonexistent local
reset instants refuse. Pre-execution boundary capture prevents a midnight stop loss from resetting the
daily starting balance after the loss. Missing held-position reset evidence remains unverified for that
period; flattening cannot manufacture it. Trusted initial flat state or known flat carry can initialize
a reference. New account commands must be globally time-monotonic; idempotent old receipts remain readable.
Independent historical experiments should use separate synthetic accounts or interleave global clocks.

See test_risk_math.py and test_risk_integration.py for exact examples, property tests, DST, cross-currency,
midnight loss, funding, actual concurrency and restart checks. Official calculation references are in
external-sources.md; no dated prop-brand numeric rule is treated as a current universal policy.
