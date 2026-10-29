# Campaign container startup repair — 2026-10-28

The Compose command selected `scripts.campaign_worker`; the image did not contain that module.
Dockerfile now copies the fixed entrypoint and tests its packaged `--help` during build. A second
real image smoke ran non-root/read-only/no-network with capabilities dropped. Targeted service
recreation returned exit0 and actual Docker health is healthy. The fresh heartbeat and configured
runtime SQL read confirm schema0009. Only campaign-worker was recreated; all development named
volumes remain unchanged. The owner applied migration0009 before this repair.

See [the full follow-up](../../../../OPENROUTER_INTEGRATION_REPORT.md#follow-up-campaign-container-startup-repair--2026-10-28).
`commands.json` records actual exit codes, including the initial Buildx metadata filesystem refusal.
Only client state was relocated to a permitted ignored directory using supported BUILDX_CONFIG;
no permission, network isolation, secret mount or application authorization was relaxed.

No public inference/key entry, browser bypass, golden rewrite or trading action occurred.

Final `make integration`: exit0 (452.824s),1 development readiness case,107 isolated cases before
and107 after restart, followed by deployed API/execution-denial smoke readiness200. Native check
passes283 Python/153 frontend tests; contracts, secret/repository checks pass. The earlier schema
readiness failure is retained as historical evidence in the parent report. No browser or actual
model acceptance is inferred from these results.
