# Product V2 bug audit — 2026-10-29

`commands.json` records exact argv, exit codes and timings. Red reproductions are deliberately
retained: 3 workspace failures, 1 discarded-signal failure and 1 partial-job render failure. The final
native checkpoint passes 342 Python / 233 frontend tests. Complete actual-service tests pass 146+146
across PostgreSQL/Redis/MinIO stop/start. These results do not certify real model quality or profitability.

`deployment.json` confirms only API/Web changed, with the same database/data-service/worker containers
and named volume mounts, actual HTTP readiness and PASSWORD/SIMULATED/DENY_ALL policy. No migration,
model invocation, credential update or broker order was needed. No owner secrets are stored here.

Browser collection reports 30 tests; browser execution is NOT RUN. Existing managed restrictions are
respected. No screenshots/goldens are rewritten. Native transport/SSR dependency mocks are unit
reproductions and never substituted for actual-service acceptance. Real historical/model positive
candidate qualification remains unverified in this audit.

See [the detailed audit](../../../PRODUCT_V2_BUG_AUDIT.md). Full pre-edit archive/inventory and
intermediate development checks remain in ignored `.cache/product-v2-audit/`.
