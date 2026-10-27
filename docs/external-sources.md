# External sources

Reviewed on 2026-10-24. Documentation pages generally publish no fixed date; access date is recorded
instead. This file distinguishes documentation consulted from integration proof.

- [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/): reviewed for image
  composition and server startup. No deprecated all-in-one base image is used.
- [Pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): reviewed for typed
  environment validation and secret-bearing configuration. Actual behavior is covered by tests.
- [Vite getting started](https://vite.dev/guide/): reviewed for the supported Node toolchain and build.
- [Tailwind Vite integration](https://tailwindcss.com/docs/installation/using-vite): reviewed for the
  Vite plugin and CSS import.
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/): reviewed for
  service_healthy and service_completed_successfully dependency conditions.
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html): reviewed for migration
  environment and explicit upgrades/downgrades.
- [Arq documentation](https://arq-docs.helpmanual.io/): reviewed for queue selection and at-least-once
  execution implications. The package is pinned; no research jobs run in Phase 0.
- Package versions and peer constraints were queried directly from the [Python package index](https://pypi.org/)
  and [npm registry](https://www.npmjs.com/) on the same date. Python and npm resolution produce the
  committed transitive locks. TypeScript 5.9.3 satisfies openapi-typescript's required 5.x peer range.

## Not yet implemented or verified

The following are supplied by the product specification and must be reread at their implementation
phase. No SDK method is called and no firm permission is enabled based on these references today:

- [MT5 Python integration](https://www.mql5.com/en/docs/python_metatrader5)
- [cTrader Open API](https://help.ctrader.com/open-api/), [Python SDK](https://help.ctrader.com/open-api/python-SDK/python-sdk-index/), [OAuth](https://help.ctrader.com/open-api/account-authentication/)
- [Ollama compatibility subset](https://docs.ollama.com/openai)
- [FTMO allowed strategies](https://ftmo.com/en/faq/which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/), [forbidden practices](https://ftmo.com/en/forbidden-trading-practices/)
- [FundedNext EA policy](https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext)
- [The5ers EA policy](https://the5ers.com/faqs/can-i-use-an-ea-expert-advisor-can-i-set-a-stealth-mode-stop-loss/), [prohibited practices](https://www.the5ers.com/faqs/prohibited-trading-practices/)

No model tag/digest, prop-firm rule, broker capability or market calendar is asserted as verified.

## Container provenance checked on 2026-10-24

- [MinIO upstream source-build instructions](https://github.com/minio/minio): reviewed after its old
  Docker Hub image returned 401. The upstream source commit is
  `7aac2a2c5b7c882e68c1ce017d8256be2feea27f` (commit date 2026-02-12). The downloaded source archive
  SHA-256 is `71794c2df26aad0cc99e8421c58b7aa2dd55969f979b0e7d1e931042e9fabcd6`, enforced in the Dockerfile.
- [Redis official image](https://hub.docker.com/_/redis): selected the existing 7.4.11-alpine3.21 tag.
- Docker Registry v2 manifest responses confirmed the exact Python, Node, PostgreSQL, Redis, Nginx,
  Go and Alpine tags and digests recorded in Dockerfiles/Compose. These are reference-availability
  checks, not proof the images build, run, or are free of known vulnerabilities.


## Audit implementation references — accessed 2026-10-25

- [Pydantic model validation](https://docs.pydantic.dev/latest/concepts/models/): reviewed for strict
  JSON validation of the local smoke safety contract; behavior verified by regression tests.
- [Zod API](https://zod.dev/api): reviewed for strict runtime response schemas; Zod 4.6.7 was pinned
  from the npm registry and frontend tests/type checking/build pass.
- TrustedHostMiddleware behavior was checked against installed Starlette source and an API regression
  test. The attempted external middleware documentation fetch returned 502; it is not cited as reviewed.

These references support code choices, not external trading integration or prop-program permission.

## Phase 0 test/CI preparation — reviewed 2026-10-25, delivered 2026-10-26

- [MinIO Python 7.2.20 API](https://github.com/minio/minio-py/blob/7.2.20/docs/API.md): reviewed
  authenticated object/bucket methods and response cleanup for isolated test fixtures. The package
  version was verified against PyPI and pinned in the dev dependency group; actual service tests
  remain blocked. The older min.io documentation URL redirected to an inaccessible page.
- [Redis XREADGROUP](https://redis.io/docs/latest/commands/xreadgroup/): reviewed pending/new delivery
  semantics. The fixture uses existing Redis 7.4-compatible group operations, not newer optional flags.
- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/): reviewed wait/start
  behavior. Disposable restart verification is configured but has not run against Docker here.
- Official action repositories were queried with git ls-remote for checkout v4.2.2, setup-python
  v5.6.0 and setup-node v4.4.0; exact commits are recorded in phase0 evidence and pinned in CI.
- [actionlint 1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12): official macOS archive
  verified against its published checksum, then used for local workflow static validation.

## Phase 1 identity references — reviewed 2026-10-26

- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): Argon2id guidance; configured 64 MiB / three iterations / parallelism one.
- [PyOTP upstream documentation](https://github.com/pyauth/pyotp): TOTP replay-counter, throttling and transport guidance.
- [Fernet documentation](https://cryptography.io/en/latest/fernet/): authenticated encryption for MFA seeds and key lifecycle limitations.

Package versions were verified against PyPI and locked. These references inform implementation;
local tests, not documentation or dependency installation, supply the acceptance evidence. Earlier
Phase 0 source-review notes retain their original dates; service tests subsequently ran successfully
as recorded in the Phase 0/1 evidence ledgers.

## Phase 2 implementation references — accessed 2026-10-26

- [ECB SDMX data API](https://data.ecb.europa.eu/help/api/data) and [examples](https://data.ecb.europa.eu/help/api/data-examples): bounded daily EXR CSV requests and series direction. Actual HTTP/provider pipeline tests were executed.
- [ESCB reuse policy](https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html): attribution, unmodified source statistics and third-party/revision limitations recorded. No blanket entitlement is inferred.
- [MinIO Python 7.2.20](https://github.com/minio/minio-py/blob/7.2.20/docs/API.md): versioned reads, retention and object-lock bucket behavior; tested against actual local MinIO.
- [PostgreSQL advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS): session-owned concurrency slots and row claims; tested on pinned PostgreSQL 17.
- [MT5 historical ticks](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py) and [bars](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py): UTC/read-only export contract. Actual Windows connectivity NOT tested.
- PyArrow 26.0.0 APIs were inspected locally and verified by serialization/readback tests. The attempted external Arrow Parquet documentation fetch returned 404 and is not recorded as reviewed.

These references are implementation inputs, not proof of actual broker authorization, complete history
or successful external integrations beyond the specifically recorded ECB/service tests.

## Phase 3 official interface sources — reviewed 2026-10-26/27

- [cTrader endpoints](https://help.ctrader.com/open-api/proxies-endpoints/): demo JSON port5036;
  fixed demo endpoint in the connector, no configurable/live endpoint.
- [cTrader account authentication](https://help.ctrader.com/open-api/account-authentication/) and
  [OpenApiPy authentication](https://spotware.github.io/OpenApiPy/authentication/): OAuth token
  flow; this implementation explicitly requests accounts-only scope, not SDK default trading scope.
- [Connection/heartbeat guidance](https://help.ctrader.com/open-api/connection/) and
  [official JSON messages](https://help.ctrader.com/open-api/sending-receiving-json/): correlated
  envelopes, heartbeat and a custom JSON WebSocket client; this does not use unsupported SDK WebSockets.
- [Official message definitions](https://github.com/spotware/openapi-proto-messages/blob/main/OpenApiMessages.proto)
  and [model definitions](https://github.com/spotware/openapi-proto-messages/blob/main/OpenApiModelMessages.proto),
  [model units](https://help.ctrader.com/open-api/model-messages/): account scope/isLive, identifiers,
  integer quote and volume conversions. Protocol fixtures are labeled CONTRACT_FIXTURE.
- [Official MT5 Python account_info](https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py)
  and linked terminal/symbol/tick/order/position/history read APIs: Windows-only official SDK,
  demo/investor/terminal identity checks. No actual terminal connectivity was tested.
- [websockets synchronous client](https://websockets.readthedocs.io/en/stable/reference/sync/client.html):
  synchronous TLS WebSocket API; installed version17.3 is pinned in uv.lock.
- [pywin32 service host source](https://github.com/mhammond/pywin32/blob/main/win32/Lib/win32serviceutil.py):
  SCM wrapper design. Actual Windows install, ACL and Job runtime were not tested.

Documentation review and package version checks establish implementation references only; they are
not actual OAuth, terminal, venue, service-deployment or order-execution acceptance evidence.

## Phase 4 calculation sources — reviewed 2026-10-27

- [MT5 symbol calculation conventions](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants):
  contract/tick/profit metadata differ by product. Phase 4 supports explicitly supplied linear contract
  and linear tick conventions only; inverse/unverified products refuse. No actual broker certification.
- [MT5 margin conventions](https://www.mql5.com/tr/book/automation/symbols/symbols_margin): margin modes
  differ. Current SIMULATED input is explicit fixed account-currency margin per volume unit; this is
  not certification of actual exchange/CFD/Forex leverage or portfolio-margin calculations.
- [Python Decimal](https://docs.python.org/3/library/decimal.html) and
  [zoneinfo](https://docs.python.org/3/library/zoneinfo.html): exact monetary arithmetic and explicit
  IANA timezone/fold semantics; tested on pinned Python 3.12.14. Latest online documentation may target
  a newer interpreter; this implementation uses APIs present in the pinned runtime.

No current FTMO/FundedNext/The5ers numeric contract terms were fetched or embedded in Phase 4.
Owner attestation binds document hashes and exact account/program dates; synthetic test policies are
not official rules. No external broker, account, margin service or economic calendar was connected.
