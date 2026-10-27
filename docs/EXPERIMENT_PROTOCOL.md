# Experiment protocol

No experiments run in Phase 0. Every future strategy must be immutable and linked to source/build
hashes, data manifests, model digest, prompt version and decoding configuration, reproducible seed,
cost model, instruments, sampling, features' availability times and family-specific acceptance gates.

Discovery/calibration/validation/final holdout remain distinct. Fit preprocessing only on training
folds, purge overlaps and use embargo where appropriate. Record every tested hypothesis to account
for selection bias. Report non-ML baselines, OOS costs, uncertainty, multiple-comparison adjustments,
trade count, independent regimes, drawdown/underwater time and weakest periods. A promising tiny
sample cannot promote a strategy. Evidence and concise decision summaries are stored; private model
chain-of-thought is not required or retained.

