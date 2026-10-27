# Backtest engines and execution conventions

Phase 5 has two distinct engines. All results are SIMULATED research; admitted user/provider history
is identified separately from SYNTHETIC_TEST_FIXTURE input. Screening cannot grant paper eligibility.

## Fast exploratory screening

Arrow executes vectorized price-change/position/cost arithmetic. Parameter batches are bounded and
ranked using approximate float mark-to-close P&L. Decisions execute only at a later observation,
subject to the maximum declared latency. Prior exposure earns the current change; new decisions cannot
earn their own observed bar. Spread, commission, slippage stress and declared funding are included.
Unknown funding is flagged. Random controls filter entries; technical exits remain quantitative.

This model does not certify stops, pending orders, liquidity, session/news/risk compliance or account
currency conversion. Separate feature/confirmation streams and cross-currency sizing require EVENT.
Every candidate needs event-driven validation; these rankings are preliminary and never promotion gates.

## Event-driven validation

The orchestrator reuses packages/market.processing.verify_manifest/read_rows and the Phase 3 journal
and Phase 4 gateway. No second broker simulator or risk calculator is implemented. Each parameter/cost/
fold/attempt receives a distinct synthetic account and global clock. Multiple instruments in the same
trial share that account, portfolio reservations and an availability-ordered clock. Unrelated periods
never share an account clock. Owner balances, MFA, source datasets and original journals are preserved.

Every proposal passes the actual gateway; every entry fill is independently revalidated and consumes
its scoped signed grant. Known partial/cancel/UNKNOWN facts retain/release the original allocations.
Orders, fills, fees, funding, protections, latency, volume/tick grids, sessions and calendar restrictions
use the existing execution/risk implementation. Missing margin, unverified contracts/calendars, stale
FX, policy revisions, STOP or uncertain account state cannot become a successful unauthorized trade.
Indeterminate scientific inputs refuse publication; legitimate risk denials remain visible in replay.

## Tick and OHLC timing

Tick fills use stored bid/ask; quotes and features must be observed and available by decision time.
A new market order waits for a later eligible observation. Signal-dependent exits likewise wait for a
later observation. Duration/session/reset exits follow predeclared clocks, never an inspected future
high/low. No artificial tick history, volume, broker spread or calibrated fill probability is claimed.

BAR execution is explicitly a hypothetical BID-OHLC plus declared spread model. All modeled points
become available only at bar availability: open, adverse extreme, favorable extreme, close. Existing
single-side exposure determines the adverse-first ordering; mixed exposure and both-touch SL/TP cases
are refused rather than selecting an optimistic path. Pending protective ambiguity is refused too.
One finite per-side liquidity budget is shared across the modeled bar, not replenished four times.
Actual intrabar chronology/holding time remains uncertain; these are observation-clock results.

The strategy sees bar high/low only after these completed observations. A proposal from that bar can
fill only on a later eligible event. Exposed bars crossing an unobserved daily reset are refused.
Predetermined conservative session/reset exits reduce this ambiguity. Maximum holding requests must
align with an execution bar interval. Higher-timeframe signals can instead drive actual tick execution.
Portfolio streams must satisfy the approved freshness bounds; sparse bars do not authorize relaxing
those bounds. Supply suitable ticks or explicitly reviewed compatible assumptions, or accept refusal.

Valuation observations may occur exactly at the declared phase endpoint; new proposals require a time
strictly before it. Terminal liquidation uses that declared endpoint and a genuinely available fresh
quote/liquidity. Missing terminal observations or incomplete closure fail instead of extrapolating
prices or publishing incomplete accepted results. Every intrabar/command mark enters the equity trace,
so a recovered close cannot hide a modeled drawdown or risk stop.

## Resource and failure boundary

PostgreSQL is the durable outbox: two advisory-lock worker slots, SKIP LOCKED claims, expiring leases,
worker-token fencing, three crash attempts, idempotent submissions, cancellation and monotonic progress
within an attempt. A retry recreates isolated accounts from frozen inputs; partial attempts remain
historical evidence and never accepted results. Publication checks owner authority, source approval,
lease/token, cancellation, pin integrity and result uniqueness after an actual MinIO upload.

Inputs allow eight streams, sixteen parameter sets and at most twenty-four actual trial/fold slots;
rows/time/results are bounded. Per-result JSON is capped at16MiB and published owner results at256MiB.
The container is read-only with 1CPU,1GiB RAM,128pids and256MiB temporary filesystem, no public port,
control-network only and no broker/admin/root-storage/bootstrap credentials or Docker socket. Retained
orphan objects/aborted account histories need operational capacity planning; they are not deleted to
manufacture acceptance. There is no paid GPU requirement or hostile-code execution capability.
