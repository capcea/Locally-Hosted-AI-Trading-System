#!/usr/bin/env bash
# Preview only the web UI from a separate Git worktree. Do not recreate API,
# workers, databases, volumes, or change broker execution flags.
set -euo pipefail

action="${1:-apply}"
original_root="${2:-$PWD}"
original_root="$(cd "$original_root" && pwd)"
script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="ai-trading-research"

if [[ ! -f "$original_root/.env" ]]; then
  echo "Missing original .env at $original_root/.env (no secrets copied)." >&2
  exit 2
fi
if [[ ! -f "$original_root/compose.yaml" ]]; then
  echo "Run from the original Local AI Trading checkout." >&2
  exit 2
fi
command -v docker >/dev/null || { echo "Docker CLI not installed" >&2; exit 2; }

if [[ "$action" == "apply" ]]; then
  config="$script_root/compose.yaml"
elif [[ "$action" == "rollback" ]]; then
  config="$original_root/compose.yaml"
else
  echo "Usage: $0 [apply|rollback] [original-repository-path]" >&2
  exit 2
fi

# Existing project services must be present. We intentionally do not start or
# rebuild the backend, allowing an easy UI-only rollback.
api_running="$(docker compose -p "$project" --env-file "$original_root/.env" -f "$original_root/compose.yaml" ps --status running -q api)"
if [[ -z "$api_running" ]]; then
  echo "Existing API is not running. Start your usual Local AI Trading stack first." >&2
  exit 1
fi

echo "Rebuilding ONLY the web service: $action"
docker compose -p "$project" --env-file "$original_root/.env" -f "$config" up -d --build --no-deps web
docker compose -p "$project" --env-file "$original_root/.env" -f "$config" ps web
echo "UI URL: http://127.0.0.1:5173/"
if [[ "$action" == "rollback" ]]; then
  echo "The original frontend has been restored; all non-web services were left untouched."
else
  echo "Rollback: bash $script_root/scripts/cockpit-preview.sh rollback $original_root"
fi
