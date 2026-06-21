#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/load_env.sh
. "$ROOT/scripts/lib/load_env.sh"
load_llm_wiki_env "$ROOT"

if ! command -v node >/dev/null 2>&1; then
  cat >&2 <<'ERR'
FAIL: node is required for the OpenAI-compatible API runner.

Install Node.js 18 or newer, or use manual mode:

  bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
ERR
  exit 2
fi

exec node "$ROOT/scripts/lib/llm_wiki_api_runner.mjs" "$ROOT" "$@"
