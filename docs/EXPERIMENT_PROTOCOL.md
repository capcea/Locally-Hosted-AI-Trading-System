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


## Implemented Phase 5 protocol

Use owner-MFA research APIs/Strategy Lab, pin the reviewed strategy and actual immutable manifests,
and explicitly approve source-policy cloning into isolated SIM accounts. Discovery/calibration/
validation/final phases, purge/embargo and independent OOS accounts are implemented. Register every
candidate/fold/cost hypothesis before work, including failed/cancelled attempts. Select on training
results only. Final release freezes one event scope once; prior exposure stays UNKNOWN. No adaptive
paper gate, ML/LLM filter or promotion is implemented. Details: STATISTICAL_VALIDATION.md,
BIAS_AND_LEAKAGE_PREVENTION.md and EXPERIMENT_REPRODUCIBILITY.md. Exact current tests live in the
Phase 5 completion report; this protocol is not acceptance evidence or a performance claim.
