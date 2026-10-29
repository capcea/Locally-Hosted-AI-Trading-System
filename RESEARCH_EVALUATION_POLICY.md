# Research evaluation policy — campaign-evaluation-v1

2026-10-28. This policy classifies research evidence, never financial eligibility.

The evaluator reads the existing complete Phase5 result artifact. It retains exact canonical net
profit after modeled costs, drawdown, trades, chronological evidence, uncertainty and cost assumptions.
It performs conservative comparisons against owner-declared research criteria, without rewriting
backtest arithmetic or deriving financial metrics from chart samples.

- INSUFFICIENT_EVIDENCE: missing/unvalidated risk trials, missing canonical metrics/costs,
  fewer than the configured minimum trades (default30, floor10), absent or incomplete data coverage.
  The campaign stops; no fabricated coverage is substituted for admitted ticks with unknown coverage.
- REJECTED: nonpositive canonical net after costs or declared drawdown criterion exceeded.
- NEEDS_MORE_VALIDATION: unresolved bootstrap interval, insufficient daily sample for ratios,
  missing cost stress, in-sample-only or absent walk-forward evidence, or any synthetic fixture. Synthetic dataset provenance independently blocks candidacy even
  when the proposal came through AI_GATEWAY.
- RESEARCH_CANDIDATE: evidence merits further investigation only. Always paper_eligible=false and
  trading_authority=false. Fixture mode can never receive this decision.

Daily observations under30 remain too short for stable ratio interpretation. Existing Phase5
block-bootstrap output is exploratory evidence, not a p-value or probability of future profit.
No new Sharpe, Deflated Sharpe, significance score, win probability or guarantee is calculated.
Missing independent-trial counts, parameter sensitivity, matched comparison and historical exposure
outside this registry are explicitly UNKNOWN. Campaign/owner attempted-trial counts are exposure
counts, not independent sample sizes or a multiple-testing correction.

## Chronology and leakage

The original Phase5 chronology, causal assumptions, purging and embargo contracts remain enforced.
Adaptive follow-ups are restricted to DISCOVERY training intervals. CALIBRATION/VALIDATION permits
one candidate and one iteration, not repeated tuning. Before VALIDATION submission, the server
conservatively rejects overlap with any previous owner's VALIDATION interval, including ordinary
manual runs and aliases. Failed/canceled prior submissions also consume this exposure permission.
This conservative guard can refuse unrelated instruments sharing the period; it intentionally does
not claim to discover all exposure outside the platform.

Final holdout and release IDs are prohibited. Later sealing or revocation invalidates authorization.
Final results cannot become feedback or AI context. No automatic release, resealing or promotion.

## Synthetic acceptance limits

The integration suite uses real imports, PostgreSQL/Redis/MinIO, original risk-approved simulator
runs and actual canonical artifacts, with synthetic tick/bar inputs labeled explicitly. A complete
synthetic M1 fixture can exercise bounded two-iteration feedback. Unknown tick coverage correctly
stops another fixture as insufficient. Neither validates market profitability or real-model inference.
Meaningful statistical acceptance still needs licensed historical data, longer independent periods,
validated scalable backtesting and properly reviewed methodology.
