# Phase 7A evidence index

2026-10-28. [Completion report](../../../PHASE7A_COMPLETION_REPORT.md).

`verification.json` records exact executed commands, actual exit codes/durations and scope. Local
stdout remains at the corresponding ignored `.cache/phase7a/*.txt`; no passwords, MFA enrollment,
session cookies, tokens or raw authentication artifacts are copied into this review package.
`preservation.json` compares all1300 original file hashes and lists only changed/missing paths;
all four existing browser goldens are unchanged. `development-preservation.json` compares12 existing
non-web container identities/images/mounts against the prior V1 snapshot. This is configuration/
identity evidence, not a claim of a data backup or complete row-by-row database comparison.
`SOURCE_SHA256SUMS.txt` identifies implementation/test files used for final verification.

The local source's read-only development readiness probe fails because the retained development
schema is0007 while this implementation expects0008. The separate full isolated service test target
applies migrations and provisions actual PostgreSQL/Redis/MinIO in unique disposable projects, then
runs the original and new tests before and after a graceful restart. Only those disposable resources
are cleaned up. A passing old deployed API smoke is scoped to its existing version.

Browser collection is explicitly collection-only. Execution is blocked by the recorded managed
localhost-origin refusal; no CLI/CDP workaround or golden rewrite was used. Real model inference,
real historical statistical acceptance, mobile rendering and manual accessibility are not verified.
