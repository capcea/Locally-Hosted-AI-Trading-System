# Market data provenance — Phase 2

Updated 2026-10-26. Real imports work in native service tests; no private development dataset was
seeded by the agent. Five years of coverage is a target, not achieved or asserted. A measured ECB
verification fetched five daily reference observations for 2026-10-19..23; actual provider/native
results live in [the Phase 2 evidence](phase2-evidence/2026-10-26/README.md).

## Source and usage identities

Every import binds an authenticated user, owned SIMULATED account, provider and instrument, exact
source symbol, requested half-open range, type/timeframe and provenance. USER_SUPPLIED is a file
provided by its owner, not a certified broker balance/feed. SYNTHETIC_TEST_FIXTURE is explicit test
data. PUBLIC_PROVIDER identifies the actual allowlisted source. Registering a provider requires a
rights reference, attribution and affirmative usage-rights acknowledgement; this is not automatic
legal entitlement verification. Secret-bearing URLs, broker passwords and arbitrary network endpoints
are not accepted as provider configuration. Dataset operations are scoped by composite owner keys.

LOCAL accepts CSV/Parquet; MT5_EXPORT accepts authorized historical exports. The optional Windows
export CLI uses an already authorized terminal, contains no order/login call and conservatively sets
availability to export time. It has not been tested against MT5. PREMIUM is an extension point with
no downloader. ECB is tested against its real SDMX endpoint and supports only declared daily EUR
reference series (EURUSD/EURGBP/EURJPY/EURCHF/EURAUD); it provides no ticks, tradable bid/ask, OHLC or
volume. Core Forex/metals/indices/crypto symbols are configurable through local instrument/import
records; a catalog symbol never asserts broker availability or complete source coverage.

ECB source: https://data-api.ecb.europa.eu/service/data/EXR/
Rights: https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html
Attribution: Source: ECB statistics. Original responses/statistics are retained unchanged. UTC/Parquet
representations are separately identified transformations. No historical publication timestamp is
invented: ECB observations become available in replay only at the actual download time.

## Input contract and timestamps

CSV uses UTF-8 with a unique header. Required fields are event_time, observed_at, available_at and
the values appropriate to the declared type. Bars require open/high/low/close; ticks require bid/ask;
reference rows require price; economic-release rows require event_id/published_at and a revision;
session rows require a positive session_end. Unknown volume/spread stays null. Spread is derived
only as ask-bid when both actual quotes were supplied; source raw fields remain unchanged. Parquet
accepts exact decimal/string prices, not floating-point prices silently coerced into exact money.

Original source timestamp and IANA zone are preserved; UTC is used internally. Naive local timestamps
require the declared zone. Ambiguous DST needs fold=0/1, nonexistent local times are rejected, and an
explicit offset must agree with the declared zone. Availability/publication/observation need offsets.
Availability cannot precede observation/publication; a bar cannot be available before its close.
Provider timestamp assertions still need trustworthy source evidence; checksums cannot establish
that an upstream price or a claimed historical timestamp was factually true.

Timestamps are inclusive decision cutoffs, while data ranges are [start,end). Optional source sequence
cutoffs restrict records that share the decision's availability instant; without one, the decision
is the end of that instant. Economic revisions retain publication/availability/vintage and cannot
replace an earlier available release. Cross-asset as-of queries check all three time fields plus event
time and account scope. Future news/price observations never enter an earlier decision. Future-known
calendar schedules/trading blackouts are a separate unimplemented service, not silently inferred.

## Immutable versions and publication

Each registry row has UUID/version, provider/source symbol, account/instrument, schema version via
its manifest, ingestion/publication time, earliest/latest, normalized/raw row counts, measured quality/
coverage, input SHA-256 and a manifest checksum. The manifest records every object version/digest,
source metadata, transformations and quality findings. Raw upload bytes and raw Parquet are retained;
normalized data/derived OHLCV are separate layers. Aggregation currently accepts complete, ordered
finer bars into coarser UTC buckets; it never fills empty buckets, invents trade volume or makes a bar
available before its close/all inputs. A transformation needs a recorded justification.

MinIO version IDs are pinned and verified; source-byte changes produce new dataset versions.
Unacknowledged source changes degrade quality. Published registry content is protected by triggers;
application storage credentials cannot delete objects. Default COMPLIANCE protection is 30 days
(configurable before new writes); protected versions cannot be shortened even by the normal root
API. The host/storage administrator remains trusted beyond these application/retention boundaries.
Do not delete volumes or underlying objects to correct a dataset. Publish a new version instead.

A dataset becomes usable only after all parts and the immutable manifest exist and the DB/audit
transaction commits. Interrupted uploads/worker attempts never expose partial data. Retained orphan
objects, storage capacity planning, off-host archival and verified restore need operational follow-up.

## Quality and measured coverage

States are PENDING, VALIDATING, VALID, DEGRADED and REJECTED. Processing SUCCEEDED means validation
finished, not that a dataset is VALID. Blocking schema/time/price/quote/spread/duplicate/order/session/
increment issues reject; unknown calendars, gaps, suspicious spikes or unreviewed revisions degrade.
Only VALID is admitted to as-of research. Explicit DEGRADED preview stays labeled research_eligible=false.

Reports preserve counts, bounded source-row examples, observed gap ranges (which may include closed
sessions), spread min/max/mean/histogram in price units and coverage basis. Bars use the explicitly
declared session/holiday UTC grid for expected counts. Calendar assertions are not an external
exchange-calendar certification. Tick expected counts/completeness remain unknown; no percentage is
invented from a few timestamps. No suspicious value is silently repaired or forward-filled.

## Reproduction and remaining sources

Run make check and P0_CACHED_IMAGES=1 make integration against cached pinned Docker images, or ordinary
make integration where registry pulls are available. The harness owns unique test projects, random
credentials and disposable resources. It includes actual PostgreSQL migrations, Redis persistence,
MinIO locking/checksums, Parquet readback, restart and killed-worker recovery, plus actual ECB access.
Benchmarks use labeled 30,000-row synthetic files and real services; they do not establish five-year,
production-tick-scale throughput. Browser proof is still blocked. Actual MT5, premium feeds, intraday/
tick/free metals/index/crypto provider coverage and a calendar feed remain unverified or unavailable.
