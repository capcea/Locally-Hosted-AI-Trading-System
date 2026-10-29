# MFA/session fix evidence — 2026-10-29

Native/actual-service evidence only. See the root MFA_SESSION_FLOW_FIX_REPORT.md.

- `commands.json`: exact invocations, real exit codes, durations and ignored raw log paths.
  Deliberate baseline failures and an initially corrected mypy failure are retained.
- `source-preservation.json`: all1357 pre-task files remain; only listed existing files changed.
- `deployment-preservation.json`: sanitized container identity/health and named-volume mounts;
  only API/Web were recreated. No environment, key, cookie, enrollment or account values.
- `SOURCE_SHA256SUMS.txt`: final changed/new implementation and report source fingerprints.

Final native check:294 Python +160 frontend; focused auth27+27 across restart; complete service
suite117+117. PostgreSQL/Redis/MinIO disposable resources are isolated and cleaned by the harness.
The OpenRouter201 tests register only synthetic metadata, never a key or chargeable request.

Browser acceptance is BLOCKED by the managed localhost restriction.28 desktop/mobile scenarios
collect, which is not execution. Run the `auth` scenario and then the complete suite locally as
specified in the report. No sensitive traces/screenshots or accepted reference updates were made.

All source fingerprints were verified with Python hashlib. The system shasum/Perl utility
failed to initialize the inherited C.UTF-8 locale; no source mismatch was reported by it.
