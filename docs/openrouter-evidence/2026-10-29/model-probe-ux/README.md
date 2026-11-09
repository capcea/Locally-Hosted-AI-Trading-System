# Model-probe UX evidence — 2026-10-29

See MODEL_PROBE_UX_FIX_REPORT.md at repository root. Native tests only; no provider requests.
`commands.json` contains real exit codes, command arguments and ignored output paths. The failing
full check is preserved: five unrelated App/cockpit files were not reformatted. `preservation.json`
verifies pre-task file retention and untouched backend/security code. Browser access remains blocked;
unit/static markup and fixture tests do not prove browser or real-model acceptance.
