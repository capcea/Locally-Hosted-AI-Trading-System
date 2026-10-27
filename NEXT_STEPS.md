# Next steps

Updated 2026-10-27. Phase 5 quantitative research is implemented and native-tested; full acceptance
remains BLOCKED by managed macOS Chromium launch. Exact current results, failures, source paths and
limits: [PHASE5_COMPLETION_REPORT.md](PHASE5_COMPLETION_REPORT.md). No Phase 6 started.

1. Run the focused Strategy Lab desktop and complete16-case desktop/mobile commands below in the
   owner's authorized environment where Chromium can launch. Retain real disposable PG/Redis/MinIO,
   owner/MFA and all assertions; record actual exits/logs. Prior Phase4 confirmation is owner-reported
   evidence, not execution proof for this revision. Do not bypass managed browser permissions.
2. Resolve any actual application/test failures exposed by those runs, then rerun make check,
   make integration and make contracts-check. Do not mark Phase5 accepted until all required gates pass.
3. Provide entitled immutable historical data and verified contract/calendar/FX/margin/funding evidence
   for real research. Actual native fixtures are explicitly synthetic. No five-year coverage or
   profitability is certified, and broker credentials are not needed for Phase5.
4. Plan independent holdout custody before claiming data is untouched. Existing owner-imported data
   has UNKNOWN prior exposure. Current API seals/one-use frozen release do not defeat host administrators.
5. Size/monitor retained attempts, internal accounts and immutable artifacts; rehearse off-host restore
   and fresh-machine install. Current limits intentionally bound small research, not five-year tick scale.
6. Review changes locally. Managed .git is read-only; no alternate write workaround, commit, remote,
   repository creation or push has occurred. Remote GitHub Actions acceptance remains NOT RUN.

```sh
cd '/Users/andy/Documents/ChatGPT/Sistem Trade Ai'
env E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration
make browser-integration
make check
make integration
make contracts-check
```

The additive0006 migration and worker run locally. Never remove development volumes to repeat tests.
The harness creates UUID-scoped projects, random credentials and loopback ports, checks actual TCP,
restarts only its own services and cleans up only its own disposable volumes. Keep the private0600
pre-migration backup in .cache/phase5/ secure; it is intentionally excluded from Git.

After Phase5 acceptance and a separate request, the recommended next module is Phase6: a bounded
private AI gateway with typed untrusted responses, exact model/provider identity and resource budgets.
No ML/LLM judge is implemented now. A hostile-code sandbox, broker executor, paper/live promotion and
live approvals remain separate future work. An environment variable can never authorize LIVE.
