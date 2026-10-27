# Integration repair evidence — 2026-10-26

Actual command records for the internal-only disposable network repair. Metadata JSON preserves exact argv (including complete Python diagnostic scripts), UTC start time, duration, child exit code and SHA-256 of the sanitized output. A successful capture-wrapper process is not a successful child check. The wrapper used workspace-local UV/PIP/npm/Playwright cache paths and a 1,200-second timeout; no timeout occurred. No browser execution was attempted.

The passing complete integration run is [integration.txt](integration.txt). Earlier failures remain evidence, not current acceptance. The original report is preserved as a historical snapshot.

## Commands and outcomes

- **main-before — exit 1**: `Python read-only diagnostic (exact script in metadata)`. [Output](main-before.txt), [exact command and metadata](main-before.json).
- **reproduce-internal-network — exit 2**: `make integration-services`. [Output](reproduce-internal-network.txt), [exact command and metadata](reproduce-internal-network.json).
- **main-before-fixed — exit 0**: `Python read-only diagnostic (exact script in metadata)`. [Output](main-before-fixed.txt), [exact command and metadata](main-before-fixed.json).
- **reproduce-internal-network-buildx-local — exit 2**: `make integration-services`. [Output](reproduce-internal-network-buildx-local.txt), [exact command and metadata](reproduce-internal-network-buildx-local.json).
- **focused-guards — exit 0**: `.venv/bin/python -m pytest tests/test_integration_guards.py -q`. [Output](focused-guards.txt), [exact command and metadata](focused-guards.json).
- **integration — exit 0**: `make integration`. [Output](integration.txt), [exact command and metadata](integration.json).
- **check — exit 2**: `make check`. [Output](check.txt), [exact command and metadata](check.json).
- **check-fixed — exit 0**: `make check`. [Output](check-fixed.txt), [exact command and metadata](check-fixed.json).
- **doctor — exit 0**: `make doctor`. [Output](doctor.txt), [exact command and metadata](doctor.json).
- **contracts — exit 0**: `make contracts-check`. [Output](contracts.txt), [exact command and metadata](contracts.json).
- **smoke-demo — exit 0**: `make smoke-demo`. [Output](smoke-demo.txt), [exact command and metadata](smoke-demo.json).
- **main-after — exit 0**: `Python read-only diagnostic (exact script in metadata)`. [Output](main-after.txt), [exact command and metadata](main-after.json).
- **cleanup-and-preservation — exit 0**: `Python read-only diagnostic (exact script in metadata)`. [Output](cleanup-and-preservation.txt), [exact command and metadata](cleanup-and-preservation.json).
- **compose-version — exit 0**: `docker compose version --short`. [Output](compose-version.txt), [exact command and metadata](compose-version.json).

- **repository-check — exit 0**: `make repository-check`. [Output](repository-check.txt), [exact command and metadata](repository-check.json).
- **secret-scan — exit 0**: `make secret-scan`. [Output](secret-scan.txt), [exact command and metadata](secret-scan.json).

## Isolation and interpretation

The failed reproduction and passing run use unique phase0-test UUID projects. The cleanup check queries only labels for the three projects attempted in this repair. No development restart, migration, volume deletion or prune was performed. Build images/cache are retained; disposable runtime containers, networks, volumes and private temporary configuration are removed.

The before/after diagnostic reads only selected Docker identity/mount/health metadata and the API readiness endpoint. It does not extract environment credentials or compare mutable database contents. Both snapshots match for configuration hash, container IDs/start times/health and mounted persistent volume identities.

Integration selections are intentional: unit checks execute 75 Python cases; the integration target executes one infrastructure case and the three isolated cases in each of two stages. No integration case is skipped or marked as a mock success. Six harness lifecycle unit cases explicitly mock Docker/socket responses and are not counted as service proof.

Current source fingerprints are in [source-snapshot.json](source-snapshot.json).
