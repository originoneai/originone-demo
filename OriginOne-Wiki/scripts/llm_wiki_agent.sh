#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/load_env.sh
. "$ROOT/scripts/lib/load_env.sh"
load_llm_wiki_env "$ROOT"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/llm_wiki_agent.sh map
  bash scripts/llm_wiki_agent.sh prompt weave <stage>
  bash scripts/llm_wiki_agent.sh prompt ask <stage> "<question>"
  bash scripts/llm_wiki_agent.sh manual weave <stage>
  bash scripts/llm_wiki_agent.sh manual ask <stage> "<question>"
  bash scripts/llm_wiki_agent.sh weave <stage>
  bash scripts/llm_wiki_agent.sh ask <stage> "<question>"
  bash scripts/llm_wiki_agent.sh health-check <stage>
  bash scripts/llm_wiki_agent.sh demo-all

LLM runtime:
  By default this script uses Codex CLI when available:
    codex -a never exec --sandbox workspace-write -C <repo> -

  To use another agent, set LLM_WIKI_AGENT to a command that reads the task
  prompt from stdin and can edit files in the current repository, for example:
    export LLM_WIKI_AGENT='claude -p --permission-mode acceptEdits'
    export LLM_WIKI_AGENT='gemini --approval-mode auto_edit --prompt "Run this LLM-Wiki task"'

  Use the prompt command when you only want to print the task prompt.
  Use the manual command when you do not have an Agent CLI. It prints a
  self-contained prompt with the stage's text files bundled for a normal LLM
  chat window.

Examples:
  Layer 1, manual chat:
    bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" > /tmp/originone-wiki-manual-ask.md
    bash scripts/llm_wiki_agent.sh manual weave 02-ingest-and-weave > /tmp/originone-wiki-manual-weave.md

  Layer 3, Code Agent CLI:
    bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
    bash scripts/llm_wiki_agent.sh ask 04-scenario-data-dev "订单表 drop column 会影响哪些下游表和指标"

Config:
  Copy .env.example to .env to configure LLM_WIKI_AGENT or API keys locally.
  The .env file is ignored by git and must never be committed.
USAGE
}

stage_exists() {
  local stage="$1"
  test -d "$ROOT/$stage" || {
    echo "FAIL: stage not found: $stage" >&2
    exit 1
  }
}

sample_question() {
  case "$1" in
    00-minimal-raw-wiki-output) echo "raw wiki output 区别是什么" ;;
    01-retrieve-first) echo "为什么要由取倒推存" ;;
    02-ingest-and-weave) echo "LLM-Wiki 怎么把 raw 编织成 wiki" ;;
    03-output-and-reuse) echo "output 保存什么 为什么不能直接当 wiki" ;;
    04-scenario-data-dev) echo "订单表 drop column 会影响哪些下游表和指标" ;;
    05-scenario-personal-kb) echo "全栈项目知识库怎么自动生成需求并维护规则" ;;
    *) echo "这个阶段讲什么" ;;
  esac
}

map_command() {
  cat <<'MAP'
LLM-Wiki 最小地图
========================================
raw/    : 原始材料。先保留事实，不急着改写。
wiki/   : 长期知识。由 LLM Agent 把 raw 编织成可复用页面。
output/ : 本次任务产物。回答、清单、报告草稿、复盘结果。

动力源：LLM Agent 负责理解、编织、检索和生成。
检索顺序：先读 wiki，wiki 不够再回 raw 查证据。
设计顺序：先问以后要取什么，再决定 raw/wiki/output 怎么放。
MAP
}

file_lang() {
  case "$1" in
    *.md) echo "markdown" ;;
    *.sql) echo "sql" ;;
    *.json) echo "json" ;;
    *.yaml|*.yml) echo "yaml" ;;
    *.csv) echo "csv" ;;
    *) echo "text" ;;
  esac
}

print_stage_bundle() {
  local stage="$1"
  local file rel lang

  find "$ROOT/$stage" -type f | sort | while IFS= read -r file; do
    case "$file" in
      *.md|*.sql|*.txt|*.json|*.yaml|*.yml|*.csv)
        rel="${file#$ROOT/}"
        lang="$(file_lang "$file")"
        printf '\n## File: %s\n\n~~~~%s\n' "$rel" "$lang"
        cat "$file"
        printf '\n~~~~\n'
        ;;
    esac
  done
}

build_prompt() {
  local action="$1"
  local stage="$2"
  local question="${3:-}"
  local action_prompt="$ROOT/prompts/actions/$action.md"

  stage_exists "$stage"
  test -f "$action_prompt" || {
    echo "FAIL: action prompt not found: $action_prompt" >&2
    exit 1
  }

  cat "$ROOT/prompts/llm-wiki-system.md"
  printf '\n\n'
  cat "$action_prompt"
  printf '\n\n'
  cat <<TASK
# Task Context

Repository root:

\`\`\`text
$ROOT
\`\`\`

Stage:

\`\`\`text
$stage
\`\`\`

Question:

\`\`\`text
${question:-N/A}
\`\`\`

Stage contract:

- Read files under \`$stage/raw/\` as evidence.
- Write or update \`$stage/wiki/\` for long-term knowledge.
- Write one-task results under \`$stage/output/\`.
- Keep \`raw/\` immutable.
- Keep changes scoped to this stage unless a validation file must be updated.

Please execute the task in the repository, not just describe what you would do.
TASK
}

build_manual_prompt() {
  local action="$1"
  local stage="$2"
  local question="${3:-}"
  local action_prompt="$ROOT/prompts/actions/$action.md"

  stage_exists "$stage"
  test -f "$action_prompt" || {
    echo "FAIL: action prompt not found: $action_prompt" >&2
    exit 1
  }

  cat "$ROOT/prompts/llm-wiki-system.md"
  printf '\n\n'
  cat "$action_prompt"
  printf '\n\n'
  cat <<TASK
# Manual Chat Mode

You are being used in a normal LLM chat window, not inside a Code Agent CLI.
You cannot read or edit the user's local file system directly.

Use the bundled files below as the stage evidence. Produce complete file
contents that the user can place back under the same relative paths.

Repository root:

\`\`\`text
$ROOT
\`\`\`

Stage:

\`\`\`text
$stage
\`\`\`

Question:

\`\`\`text
${question:-N/A}
\`\`\`

Manual output contract:

1. Start with a short summary.
2. List the files that should be created or updated.
3. For each file, return the relative path and the complete new file content.
4. Do not ask to edit \`raw/\`. Treat raw files as immutable evidence.
5. Keep source references to the bundled raw/wiki files.
6. If the evidence is insufficient, say what is missing instead of inventing it.

# Bundled Stage Files
TASK

  print_stage_bundle "$stage"
}

run_agent() {
  local prompt="$1"

  if [ -n "${LLM_WIKI_AGENT:-}" ]; then
    printf '%s\n' "$prompt" | bash -lc "$LLM_WIKI_AGENT"
    return
  fi

  if command -v codex >/dev/null 2>&1; then
    printf '%s\n' "$prompt" | codex -a never exec --sandbox workspace-write -C "$ROOT" -
    return
  fi

  cat >&2 <<'ERR'
FAIL: no LLM Agent runtime found.

Install Codex CLI, or set LLM_WIKI_AGENT to a command that reads stdin and can
edit this repository. You can still inspect the task prompt with:

  bash scripts/llm_wiki_agent.sh prompt weave 02-ingest-and-weave

If you do not have a Code Agent CLI, generate a self-contained prompt for a
normal LLM chat window with:

  bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
ERR
  exit 2
}

agent_action() {
  local action="$1"
  local stage="$2"
  local question="${3:-}"
  local prompt
  prompt="$(build_prompt "$action" "$stage" "$question")"
  run_agent "$prompt"
}

prompt_action() {
  local action="$1"
  local stage="$2"
  local question="${3:-}"
  build_prompt "$action" "$stage" "$question"
}

manual_action() {
  local action="$1"
  local stage="$2"
  local question="${3:-}"
  build_manual_prompt "$action" "$stage" "$question"
}

cmd="${1:-}"

case "$cmd" in
  map)
    map_command
    ;;
  prompt)
    action="${2:-}"
    stage="${3:-}"
    question="${4:-}"
    test -n "$action" && test -n "$stage" || { usage; exit 1; }
    prompt_action "$action" "$stage" "$question"
    ;;
  manual)
    action="${2:-}"
    stage="${3:-}"
    question="${4:-}"
    test -n "$action" && test -n "$stage" || { usage; exit 1; }
    manual_action "$action" "$stage" "$question"
    ;;
  weave)
    stage="${2:-}"
    test -n "$stage" || { usage; exit 1; }
    agent_action weave "$stage"
    ;;
  ask)
    stage="${2:-}"
    question="${3:-}"
    test -n "$stage" && test -n "$question" || { usage; exit 1; }
    agent_action ask "$stage" "$question"
    ;;
  health-check)
    stage="${2:-}"
    test -n "$stage" || { usage; exit 1; }
    agent_action health-check "$stage"
    ;;
  demo-all)
    map_command
    for stage_dir in "$ROOT"/[0-9][0-9]-*; do
      stage="$(basename "$stage_dir")"
      question="$(sample_question "$stage")"
      echo
      echo "== $stage: weave =="
      agent_action weave "$stage"
      echo
      echo "== $stage: ask =="
      agent_action ask "$stage" "$question"
    done
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "FAIL: unknown command: $cmd" >&2
    usage
    exit 1
    ;;
esac
