# Public timestamp-mask mismatch evidence

The three owner PNGs are exact copies of directly viewed, signed-out public Home failure artifacts.
They contain no authentication enrollment, recovery or account secrets. Expected and received PNGs
were decoded with the PNG implementation already bundled in the installed Playwright utilsBundle;
no browser launch, image editing, reference rewrite or new dependency was involved. The private
analysis command was node .cache/phase55b-visual/pixels.cjs; its exact counts/bounds/SHA256 results
are retained in pixel-analysis.json. There are exactly84 differing RGBA pixels, all mask edge pixels.

verification.json records actual checks and the distinction between owner-supplied rendered evidence
and unexecuted post-fix browser acceptance. Raw check output and the starting-state hash manifest
remain private under .cache/phase55b-visual/. Earlier Phase 5.5B/risk-503 evidence was not replaced.

The source now reserves a clock-format-sized8ch slot and keeps the real observed instant. Old
references contain intrinsic-width masks. No reference was changed. Obtain genuine actual/diff
images from the normal authorized local run, inspect every changed region and approve the relevant
reference explicitly before replacing it. A candidate is not a passing comparison. Any non-clock
difference needs separate investigation. Both themes and desktop/mobile remain required; the agent
did not verify the post-fix rendering or generate mobile baselines. All20 cases must pass without
rewriting before full acceptance. See the visual correction section in PHASE55B_COMPLETION_REPORT.md.
