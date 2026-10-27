# Deterministic execution simulator — Phase 3

All results are SIMULATED. No synthetic fill proves real venue execution quality or strategy profit.
Implementation: `packages/execution/contracts.py`, `engine.py`, `adapter.py`, `journal.py`;
API: `apps/api/execution`; UI: `apps/web/src/BrokerCenter.tsx`.

## Inputs, clock and execution

A run pins its owned account, instrument, explicit synthetic SymbolSpec and SimulationModel. Models
include seed, documented assumption source, latency/jitter, adverse slippage ticks, commission,
optional funding, per-tick synthetic liquidity, maximum quote age and synthetic initial balance.
Decimal strings reject binary float/bool, nonfinite values, excessive precision and magnitude.
Financial overflow is refused. Tick/volume grids and min/max sizes are checked. Symbol asset class,
account mode and profit/account currency must match; no implicit FX conversion is implemented.

Virtual command time is explicit and cannot reverse. Quote event/availability times and sequences
cannot go backward, and quotes must have bid<=ask. Seeded latency uses deterministic digest-derived
jitter; IDs derive from run/command identity. There is no wall-clock, network or random fill decision
inside the engine. External I/O is outside the pure engine and journal transaction.

A market order acknowledges at submission and can fill only on a subsequent eligible TICK, after
its modeled latency. BUY uses ask plus adverse slippage, SELL bid minus adverse slippage. Limits
activate at their limit and cap execution price there; stops activate then follow market/gap rules.
Protection geometry is rechecked at fill, so a gap cannot create an invalid protected position.
Stop loss executes on the liquidation side, including adverse gaps/slippage. Take profit uses an
explicit limit-style capped-price convention; it is not a universal claim about venue stop policies.
SL protection is evaluated before new entries on each tick. Cancellation/expiry apply only to valid
nonterminal orders. Closed/unknown sessions, stale specifications/quotes and unsupported order types
are refused. No missing calendar is guessed open.

Liquidity is finite per bid/ask side per tick and resets even on a disconnected/closed-session tick.
Partial fills are rounded down to a legal volume step and consume that side's remaining budget.
When supplied, quote liquidity is used; otherwise the owner's declared synthetic budget is used.
There is no modeled queue priority, order-book depth/impact, venue matching algorithm or measured
fill probability. Manual close refuses insufficient remaining liquidity rather than inventing volume.

## Positions and costs

NETTING uses weighted entry, opposite-side reduction and reversal; HEDGING keeps distinct positions.
Modify protection enforces declared stop/freeze distances. Partial close and SL/TP produce exact
fills, cash and fees. OCO is available only when explicitly enabled in the synthetic spec; the first
fill cancels peer orders. This does not certify safe native or emulated OCO at any broker.

Profit uses a linear contract-size payoff in one account/profit currency. Inverse contracts,
cross-currency conversions, real margin/liquidation and portfolio risk are NOT IMPLEMENTED. Commission
is the explicitly supplied per-unit execution charge; bid/ask already includes supplied spread.
Optional swap_per_unit_per_day is continuous prorated synthetic funding over actually held virtual
time. It is not a verified broker rollover/holiday/triple-swap model. Unknown costs remain documented
assumptions, not evidence of zero actual costs. Synthetic balance is always labeled synthetic.

## Faults, persistence and limits

Faults include reject-next, disconnect-before-submit, after-submit uncertainty and delayed ack.
UNKNOWN prevents new submissions; reconnect alone cannot clear it. Reconciliation requires durable
synthetic broker truth and records transitions. Missing truth leaves UNKNOWN with an incident.
No exactly-once guarantee is claimed for external services.

Runs are limited to 200 orders, 2,000 fills and 20,000 journal events; creation is quota-limited.
API request bodies, event pages and replay samples are bounded. The list API paginates; the current
UI initially displays 20 runs and does not provide full historical pagination controls.

## Phase 2 replay

A run may pin an owned VALID TICK dataset with matching account/instrument/source symbol and manifest
hash. Real MinIO versions, checksums and stored bid/ask ticks are read through the existing market
query path. A decision cutoff (no later than now), availability and source sequences constrain the
sample. Replay refuses truncation and is bounded to 500 ticks per request. Stable row hashes create
idempotent journal commands. A bound dataset run refuses manually injected TICKs. No OHLC-derived
bid/ask, interpolated ticks or future prices are invented. Upstream availability declarations still
require trustworthy evidence; checksums alone cannot certify factual prices or rights.

Tests: `tests/test_execution_engine.py` covers deterministic lifecycle/cost/fault cases;
`tests/test_execution_integration.py` covers actual transactions, crash/restart/concurrency and
immutable Phase 2 data replay. This is an execution simulator, not the Phase 5 research backtester,
statistical gate, independent risk gateway or executable strategy runner.
