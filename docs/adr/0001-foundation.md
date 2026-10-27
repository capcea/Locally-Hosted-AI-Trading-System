# ADR 0001 — Honest, read-only foundation before order-capable services

Date: 2026-10-24. Status: accepted for Phase 0.

Use a modular monolith with Python 3.12, FastAPI/Pydantic v2, SQLAlchemy/Alembic and React/Vite/TS.
Separate the future research sandbox and broker risk gateway as actual deployment trust boundaries.
The initial source tree is deliberately smaller than the suggested directory tree; add domain modules
when their behavior is implemented rather than filling empty interfaces with simulated success.

Choose Arq 0.28.0 for future research jobs because it fits the async Python stack and has explicit
at-least-once semantics. Redis 5.3.1 is the compatible Python client pin. No executable research jobs
are registered yet. Durable SQL job records and idempotency will be required before starting workers.

Choose a loopback-only unauthenticated read-only shell for Phase 0. This does not satisfy Phase 1
auth. All potentially trading actions are denied at the API and executor boundary; there is no live
mode implemented. A reference risk configuration is displayed but explicitly not enforced as a risk
engine. No exchange account or quote is invented for cosmetic completeness.

Choose a real PostgreSQL service in Compose and a reversible initial migration. SQLite is used solely
for portable schema unit tests, never as evidence of PostgreSQL integration. The readiness endpoint
fails if infrastructure is unavailable or the migration revision is wrong.

Use pinned dependency resolution rather than blindly choosing the latest package release. The latest
TypeScript 7.0.2 did not meet openapi-typescript's peer range; use verified compatible TypeScript 5.9.3.
Generate API types from the Pydantic/OpenAPI contract and commit both outputs.

The user's requested local repository, Python backend and gated deployment take precedence over
generic hosted-site defaults. No Sites registration, remote hosting or paid infrastructure is created.

Public registry checks found the original MinIO binary image unavailable (401), so build the development
store from upstream commit `7aac2a2c5b7c882e68c1ce017d8256be2feea27f` with a verified archive checksum.
The original Redis Alpine 3.22 tag did not exist (404); pin the available 7.4.11 Alpine 3.21 image.
All base images now have verified registry digests. This verifies references, not container startup or
image security; those acceptance checks still require a running Docker engine.

