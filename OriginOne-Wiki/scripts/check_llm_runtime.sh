#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/load_env.sh
. "$ROOT/scripts/lib/load_env.sh"
load_llm_wiki_env "$ROOT"

soft=false
if [ "${1:-}" = "--soft" ]; then
  soft=true
fi

mask_state() {
  local name="$1"
  if [ -n "${!name:-}" ]; then
    echo "set"
  else
    echo "empty"
  fi
}

echo "== LLM-Wiki runtime check =="

if [ -f "$ROOT/.env" ]; then
  echo ".env: found"
else
  echo ".env: not found, copy .env.example to .env when you need local config"
fi

echo
echo "Agent command:"
if [ -n "${LLM_WIKI_AGENT:-}" ]; then
  echo "- LLM_WIKI_AGENT: configured"
else
  echo "- LLM_WIKI_AGENT: empty, will try Codex CLI by default"
fi

echo
echo "Installed CLI runtimes:"
found_runtime=false
for runtime in codex claude gemini; do
  if command -v "$runtime" >/dev/null 2>&1; then
    echo "- $runtime: $(command -v "$runtime")"
    found_runtime=true
  else
    echo "- $runtime: not found"
  fi
done

echo
echo "API key env vars:"
echo "- OPENAI_API_KEY: $(mask_state OPENAI_API_KEY)"
echo "- DEEPSEEK_API_KEY: $(mask_state DEEPSEEK_API_KEY)"
echo "- LLM_WIKI_API_KEY: $(mask_state LLM_WIKI_API_KEY)"
echo "- ANTHROPIC_API_KEY: $(mask_state ANTHROPIC_API_KEY)"
echo "- GEMINI_API_KEY: $(mask_state GEMINI_API_KEY)"
echo "- GOOGLE_API_KEY: $(mask_state GOOGLE_API_KEY)"

echo
echo "OpenAI-compatible API runner:"
if command -v node >/dev/null 2>&1; then
  echo "- node: $(command -v node)"
else
  echo "- node: not found"
fi
echo "- LLM_WIKI_API_BASE_URL: ${LLM_WIKI_API_BASE_URL:-https://api.deepseek.com}"
echo "- LLM_WIKI_API_MODEL: ${LLM_WIKI_API_MODEL:-deepseek-v4-flash}"
if [ -n "${LLM_WIKI_API_KEY:-}" ] || [ -n "${DEEPSEEK_API_KEY:-}" ] || [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "- api key for runner: configured"
else
  echo "- api key for runner: empty"
fi

echo
if [ -n "${LLM_WIKI_AGENT:-}" ] || [ "$found_runtime" = true ]; then
  echo "OK: an LLM Agent runtime is available or configured."
  echo "Note: API keys are only required if your chosen runtime uses API-key auth."
  exit 0
fi

if command -v node >/dev/null 2>&1 && { [ -n "${LLM_WIKI_API_KEY:-}" ] || [ -n "${DEEPSEEK_API_KEY:-}" ] || [ -n "${OPENAI_API_KEY:-}" ]; }; then
  echo "OK: no Code Agent CLI found, but the OpenAI-compatible API runner is configured."
  echo "Run: bash scripts/llm_wiki_api_runner.sh ask 00-minimal-raw-wiki-output \"raw wiki output 区别是什么\""
  exit 0
fi

echo "FAIL: no LLM Agent runtime found."
echo "Install Codex CLI / Claude Code / Gemini CLI, or set LLM_WIKI_AGENT in .env."
echo "Have a DeepSeek/OpenAI-compatible key? Configure LLM_WIKI_API_BASE_URL, LLM_WIKI_API_MODEL, and DEEPSEEK_API_KEY or LLM_WIKI_API_KEY in .env."
echo "No CLI yet? Use manual mode to generate a self-contained prompt for a normal LLM chat:"
echo "  bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output \"raw wiki output 区别是什么\""

if [ "$soft" = true ]; then
  exit 0
fi
exit 2
