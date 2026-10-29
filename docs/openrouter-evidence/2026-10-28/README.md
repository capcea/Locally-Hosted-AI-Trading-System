# OpenRouter follow-up evidence — 2026-10-28

See [the report](../../../OPENROUTER_INTEGRATION_REPORT.md). JSON records contain commands,
exit codes and paths to ignored local logs; they contain no API key, session or raw provider output.
The full protected-source archive remains ignored under `.cache/openrouter/`, not committed here.

Final native check:283 Python/153 frontend cases, Ruff/mypy/build pass. Full disposable services:
107 cases before and107 after graceful restart; focused cloud7+7. HTTP transport is explicitly
synthetic, with real PostgreSQL/Redis/MinIO, worker, encryption, scoped identities and queue behavior.
`make integration` itself fails the retained development schema readiness probe (0008 vs0009).
No development volumes, keys or operator configuration changed. No external inference request ran.

Browser collection:26 cases only. Managed localhost restriction blocks browser execution. No browser,
visual, TLS/public-network or actual model acceptance is claimed. Accepted golden images are unchanged.

`commands.json` preserves intermediate failing runs as well as final results. `source-preservation.json`
checks the1328 protected original files. Original unrelated uncommitted work remains intact.
