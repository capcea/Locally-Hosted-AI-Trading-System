# Risk policy HTTP 503 correction evidence

verification.json supplements the original Phase 5.5B ledger; no earlier evidence was replaced. It
records exact native commands, failing reproduction, successful reruns and safe request correlation
metadata. The original owner assertion is summarized separately without secret page states. Raw
command logs remain private in .cache/phase55b-policy503/ and are excluded from the repository.

The focused native selector retains the standard integration_services harness and changes only the
pytest node list. It still validates loopback bindings/TCP, real PostgreSQL/Redis/MinIO, temporary
credentials, migrations, restart and cleanup of its own disposable project. The race test coordinates
real concurrent transactions; it does not mock successful API responses or risk decisions.

Native request IDs and SQLSTATE40P01 were observed during the reproduction. The original owner
request ID, response body and server log were unavailable and are not reconstructed. The fixed
backend logs only an allowlisted SQLSTATE and correlation ID; the browser harness emits a bounded
sanitary subset before removing temporary server logs. No SQL parameters/headers/auth secrets are
retained as evidence.

All 20 browser cases collect, but current agent execution remains blocked by the existing managed
origin restriction. Collection and native service tests do not establish browser, visual or manual
accessibility acceptance. See the correction section of PHASE55B_COMPLETION_REPORT.md for exact
owner-local commands. Snapshot baselines were not updated.
