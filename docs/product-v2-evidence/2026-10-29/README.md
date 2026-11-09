# Product V2 evidence — 2026-10-29

The command manifest records actual executions and exit codes. `integration-final.txt` includes
143 passing tests before and 143 after actual disposable PostgreSQL/Redis/MinIO stop/start. Focused
identity/product coverage passes 35+35; campaign recovery 14+14. The earlier failed complete run is
preserved in `earlier-failure.txt` and its full private local `.cache/product-v2/` log.

`deployment.json` describes the initial API/Web rollout. `deployment-final.json` records the complete
rollout and healthy recovery of previously stopped, empty-queue market/research workers. Named
persistent volumes are unchanged. AI worker, provider credentials and authorization were not reset.
Only sanitized service/container identifiers, public health observations and empty queue counts are
retained here. Identity/recovery comparison fingerprints stay in ignored local cache, not this folder.

Browser collection succeeds for 30 cases. This is **not** browser execution. Prior managed restrictions
were respected. No current screenshots or visual/mobile/accessibility acceptance are asserted. The
old Home goldens remain byte-identical and require explicit owner review of genuine new candidates.
No automatic screenshot update, arbitrary tolerance increase, paid inference or broker order.

See [the implementation report](../../../PRODUCT_V2_IMPLEMENTATION_REPORT.md) for exact scope and
owner-local disposable browser commands. `source-preservation.txt` records the pre-edit source
inventory comparison; no original inventory file is missing.
