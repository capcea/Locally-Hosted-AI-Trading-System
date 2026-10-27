# Statistical validation methodology

This is descriptive research, not evidence of profitable deployable trading. Metrics use stored fills
and account marks. Net P&L, drawdown, fees/funding and monetary averages preserve Decimal strings;
dimensionless ratios and resampling summaries are approximate floats and never authorize execution.

## Accounting and conventions

Starting capital is the isolated account's declared synthetic capital. Balance changes come from the
actual journal; equity includes executable-side unrealized P&L. The curve retains every observation/
command mark, including OHLC adverse excursions and exit fees. Maximum drawdown is peak equity minus
subsequent equity, with a fractional version relative to that peak. Open terminal inventory is refused.

Round trips split at flat inventory, including netting reopens. Net trade P&L includes both execution
commissions and actual modeled funding, allocated by volume-time with the final residual exact.
R multiples use the original signed reservation, proportional to actual filled volume. Requested exit
horizons and actual liquidity delays are distinct; OHLC timestamps are not exact intrabar durations.

Profit factor is positive net trade P&L divided by absolute negative net trade P&L; absent losers makes
it undefined, not infinite success. Expectancy is mean net trade P&L; win rate counts strictly positive
trades. Average winners/losers, R distribution, consecutive losses, holding times, exposure by instrument/
UTC session and causal trend/volatility regimes remain visible with sample counts. Cost-stress trials
rerun actual execution; they do not relabel baseline results with invented cost sensitivity.

Daily returns use one last equity mark per observed UTC day and the initial capital reference. Sharpe
uses sample standard deviation; Sortino uses root mean squared negative returns, with zero target.
Annualization uses365.25 calendar days only with at least30 consecutive observed UTC daily returns.
Missing days are not filled; irregular coverage, zero denominators or insufficient samples yield null
with a reason. Calmar additionally requires a full year and defined drawdown. Recovery factor is net
P&L / maximum monetary drawdown when defined. No tiny sample is certified statistically sufficient.

## Chronology and selection

Discovery, calibration, validation and final evaluation windows are distinct. Walk-forward expands the
training window, purges the declared maximum label horizon and embargoes before each OOS interval.
Every candidate is trained through actual execution on its own account; the fixed maximum TRAIN net
P&L selection rule chooses the next OOS configuration. OOS does not select its own parameters. Previous
OOS may enter later chronological training after purge; it is not a sealed final holdout.

Purged interval validation removes overlapping labels and embargoed observations explicitly. All
parameter/cost/fold attempts, failed and cancelled runs are retained in the immutable trial registry.
Provenance reports family and owner-wide attempted trial counts. Correlated trials are not counted as
independent evidence merely because they have different IDs, seeds or cost scenarios.

## Uncertainty

Seeded ordinary bootstrap and circular fixed-block bootstrap report exploratory percentile95% intervals
for mean net trade P&L; fewer than10 trades yields null. Blocks default to five trades. Monte Carlo
permutes the observed trade sequence and reports drawdown intervals; it does not create new market
returns or prove stationarity. Dependence, nonstationarity and sample limitations remain explicit.

Deflated Sharpe follows Bailey/Lopez de Prado (2014), using non-annualized Sharpe, sample length,
skewness, non-excess kurtosis, independent-trial count and cross-trial Sharpe variance. The API derives
return moments from stored eligible daily returns, but requires a separately acknowledged independence/
variance model reference. No independence estimate is invented from correlated parameter sweeps. Invalid
or insufficient samples return null. Assumptions/results are owner-MFA audited and grant no eligibility.
See external-sources.md for the primary paper and exact verification evidence in the completion report.
