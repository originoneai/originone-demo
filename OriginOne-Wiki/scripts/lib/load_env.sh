#!/usr/bin/env bash

load_llm_wiki_env() {
  local root="$1"
  local env_file="$root/.env"
  local line key value

  test -f "$env_file" || return 0

  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ""|\#*) continue ;;
    esac

    key="${line%%=*}"
    value="${line#*=}"

    case "$key" in
      LLM_WIKI_AGENT|LLM_WIKI_API_BASE_URL|LLM_WIKI_API_MODEL|LLM_WIKI_API_KEY|LLM_WIKI_API_MAX_TOKENS|LLM_WIKI_API_TEMPERATURE|DEEPSEEK_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|GOOGLE_API_KEY|CODEX_HOME)
        if [[ "$value" == \"*\" && "$value" == *\" ]]; then
          value="${value:1:${#value}-2}"
        elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
          value="${value:1:${#value}-2}"
        fi
        export "$key=$value"
        ;;
    esac
  done < "$env_file"
}
