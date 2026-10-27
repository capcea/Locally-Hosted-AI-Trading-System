# Returning-owner MFA/navigation correction

The owner failure's authentication-state predicates are recorded in owner-failure-summary.json. Raw
DOM, field values, verification bodies, cookies, OTPs, MFA seeds and recovery codes are not copied.
The original MFA HTTP status and network-abort/correlation logs were unavailable; none are invented.

The definite source defect is immediate hard navigation after clicking an asynchronous MFA submit.
The corrected test requires actual verification HTTP200/completed response, FULL owner UI and a
server-confirmed FULL session first. All original account heading, reload, storage and denial
assertions remain. No backend authorization, MFA replay window or visual reference was changed.

The native regression uses actual restricted PostgreSQL plus real password/MFA/session APIs. It
proves the renamed account survives, the returned rotated cookie permits access and the old
challenge cookie is revoked. This validates the proposed mechanism; it does not reproduce the
original Chromium scheduling. Focused tests run within the standard disposable harness, selecting
only two explicit pytest nodes. Auth tests do not exercise MinIO/Redis round trips; the complete
native integration target covers those services separately.

verification.json records exact commands and exits once complete. Raw logs and source manifests
remain private under .cache/phase55b-auth-navigation/. Browser collection is not execution. The
agent's managed-origin restriction still prevents the focused foundation/full browser run. All20
cases and existing manual gates remain required for Phase5.5B acceptance. Earlier visual and risk
evidence and both owner-approved desktop PNGs are preserved.
