# Versioned personal/prop policy schema

Machine contract: [PROP_FIRM_POLICY_SCHEMA.json](PROP_FIRM_POLICY_SCHEMA.json), exported from
apps/api/risk/schemas.py PolicyInput and packages/risk/contracts.py PolicyTerms. OpenAPI additionally
contains profile, attestation, financial context, calendar, decision, status and emergency schemas.
JSON Schema is structural; Pydantic validators and database/account-scope checks remain mandatory.

A RiskPolicy version belongs to one owned synthetic account/revision and a nonempty provenance list,
SHA-256 document digest, effective interval and verification state. PERSONAL has no firm policy link.
PROP requires the latest VERIFIED Phase 1 FirmPolicy for the exact account and program revision.
That immutable program identifies firm, platform, account size/type and phase. Verification requires
recent owner MFA, matching document digest and explicit exact-program/effective-date acknowledgement.
Attestation is human verification, not automatic proof of a current firm's contract or broker permission.

Content is immutable; create a new version to change terms. Latest unverified/revoked/expired versions
block rather than falling back to an older permissive policy. Account/program/base-profile revisions
invalidate their bindings. Policy caps override more permissive requested settings. Applicable account,
strategy, instrument, asset-class, firm and program-phase profiles combine by strictest ceiling and
largest buffer; calendar requirements combine with logical OR.

Required financial semantics include currency/IANA zone, explicit DST fold, daily loss percentage,
daily balance/equity/max/initial reference and amount basis, total static/trailing mode and amount basis,
floating P&L inclusion, fees included, overnight/weekend/automation permissions, maximum duration,
permitted instruments, prohibited styles and news requirement/scope. Reset minute and news windows
are explicit bounded fields. UNKNOWN cannot imply permission. News scope distinguishes new entry
blackouts from forbidden held exposure; stale required evidence blocks both relevant paths.

No built-in FTMO/FundedNext/The5ers numeric rules are represented as current facts. Three program
fixtures in native tests are explicitly synthetic. To use actual terms later, obtain the exact official
program/account/platform documents, preserve their digests/dates, review prohibitions and broker symbol
specs, and attest in the intended scope. This does not enable external orders in Phase 4.
