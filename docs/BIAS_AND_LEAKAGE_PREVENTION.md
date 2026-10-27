# Bias and leakage boundaries

- Inputs pin owned VALID dataset IDs, versions, manifest/content hashes and provider/source metadata.
  Original Phase2 MinIO versions/checksums are read again; no repaired/interpolated prices are inserted.
- Event, observation, publication and availability constraints remain separate. A complete bar cannot
  supply its high/low before close/availability. Separate signal observations must precede execution
  observations strictly; source timestamp ties cannot smuggle a completed future bar into an earlier fill.
- Cross-asset/confirmation reads are causal as-of histories, with explicit direction and freshness
  assumptions. Economic-event values are not loaded as benchmark features; required fresh calendar
  blackouts remain actual gateway checks. Unknown required evidence refuses execution/publication.
- Indicator windows contain visible data only, with explicit warm-up. Folds are chronological; maximum
  holding/label horizons are purged and embargoed. Parameters are selected from training results only.
- Signal-dependent orders/exits wait for later observations. Tick bid/ask is side-aware; costs, gaps,
  partial fills and protections use the existing simulator. OHLC ambiguity is rejected/conservative and
  labeled modeled; no missing tick chronology or observed spread is manufactured.
- Independent historical trials use independent accounts/clocks. Frozen strategy/software/risk/policy
  versions and repeated worker checks prevent mutable configuration from contaminating accepted results.
- Every attempted hypothesis remains registered. Random controls filter entries without changing
  quantitative exit logic. ML/LLM judges remain NOT IMPLEMENTED, with no fake judge decisions.

## Final holdout

Owner/recent MFA seals an admitted dataset interval. Ordinary market-data reads, queries, replay and
research submissions are refused across overlapping aliases, instruments and accounts for that owner.
Protected metadata is excluded from ordinary dataset lists. A separate audited release freezes the
complete final event experiment and can be consumed once. Invalid preflight configuration rolls back
release creation. Retuning/releasing the same holdout again is refused; deterministic recovery of the
same frozen run is not a new independent evaluation.

Existing owner-supplied data may already have been seen before sealing. Prior exposure is UNKNOWN and
untouched_certified is always false; the platform cannot retroactively certify blindness or stop an
owner/host administrator from obtaining public data elsewhere. Such a window must not be described as
an untouched independent holdout. SQL/API and ordinary workflow protection is implemented; an independent
custodian with separately provisioned vault identities is needed to certify stronger real-world secrecy.
No host-admin-resistant secret custody or fabricated untouched-data claim is made in Phase5.
