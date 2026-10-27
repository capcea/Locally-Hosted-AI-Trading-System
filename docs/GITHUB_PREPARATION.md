# Private GitHub repository preparation

Target name: **ai-trading-research-platform**. Intended visibility: **private**.
Prepared 2026-10-26. No repository was created, no remote added, no code pushed and no GitHub CI
run triggered. Current .git is read-only under managed workspace policy, so no staging/commit was
attempted and no alternate Git directory was used.

## Prepared contents

- README, master specification, implementation status, audit/evidence and Phase 0/1 completion reports.
- Typed simulation-only API with identity/MFA, governance persistence, Romanian management UI,
  locked dependencies and executable safety/native integration tests.
- Development Compose plus isolated service-test Compose/harness.
- Read-only GitHub Actions workflow with pinned action revisions, dependency/secret scans, quality/
  contracts, real infrastructure and browser validation paths.
- [Initial commit message](INITIAL_COMMIT_MESSAGE.txt). It does not claim that blocked acceptance passed.

.gitignore excludes .env variants, private keys, secrets directories, local databases/dumps, volumes,
backups, model weights/checkpoints/artifacts, raw .log files, traces and caches. The placeholder-only
.env.example stays included. Sanitized audit command transcripts are deliberate .txt documentation;
they have been secret-scanned. Never rename raw logs just to bypass ignore rules.

## Review and make the local initial commit

Run these only from a terminal/session authorized to write this repository's Git metadata:

```sh
cd "/Users/andy/Documents/ChatGPT/Sistem Trade Ai"
make check
make contracts-check
make repository-check
make secret-scan
.venv/bin/python -m scripts.repository_check --manifest .cache/initial-commit.files
git --literal-pathspecs add --pathspec-from-file=.cache/initial-commit.files --pathspec-file-nul
git diff --cached --check
git diff --cached --stat
git diff --cached
git status --short
# Review the staged source and confirm no sensitive files are present.
git commit -F docs/INITIAL_COMMIT_MESSAGE.txt
```

The manifest is generated in ignored .cache, not an alternate index. It lists regular source/evidence
files selected by Git's ignore rules. Regenerate and rescan if files change before staging. Git identity
is already configured locally; review your author identity before committing without copying it into
public logs. The initial commit may honestly record incomplete Phase 0/1 gates; it must not describe
the platform as accepted or production-ready.

Local secret scan uses Gitleaks from .tools/bin/gitleaks or PATH. The current checked tool is 8.28.0.
On a fresh machine, obtain the appropriate release from the
[official Gitleaks releases](https://github.com/gitleaks/gitleaks/releases/tag/v8.28.0), verify its
published SHA-256, then place the executable in the ignored .tools/bin directory. Do not turn a
missing scanner into a passing status. CI uses the already digest-pinned Gitleaks image.

## Remote operations stay pending

After reviewing the local commit, the owner must explicitly approve creation of the private target
repository and separately scope any push. No automatic publishing script or credential setup has been
added. No GitHub credential is requested or stored by this task. Existing GitHub connection/access
can be checked after authorization; do not paste tokens into .env, reports or chat.

Before accepting GitHub preparation as remotely verified, run the prepared workflow on the approved
remote, inspect all logs and resolve failures. actionlint exit 0 only validates the local workflow
definition. Private repository rules, access, branch protection and successful remote CI are not
established by a YAML file.

The workflow uses no broker keys. Its integration harness cleans only its uniquely named disposable
project; its final docker compose down preserves the development project's volumes. Docker builds
and Playwright in CI remain unverified here. Do not use a remote CI run to bypass the current local
browser restriction; remote execution is pending explicit repository/push approval.

