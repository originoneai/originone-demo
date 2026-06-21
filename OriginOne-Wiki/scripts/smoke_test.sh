#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== OriginOne-Wiki smoke test =="
echo "cwd: $(pwd)"

echo
echo "1. Check LLM Agent harness"
test -x scripts/llm_wiki_agent.sh || chmod +x scripts/llm_wiki_agent.sh
test -x scripts/llm_wiki_api_runner.sh || chmod +x scripts/llm_wiki_api_runner.sh
test -x scripts/validate_design_package.sh || chmod +x scripts/validate_design_package.sh
test -x scripts/check_llm_runtime.sh || chmod +x scripts/check_llm_runtime.sh
test -f .env.example
test -f prompts/llm-wiki-system.md
test -f prompts/actions/weave.md
test -f prompts/actions/ask.md

echo
echo "2. Check local LLM runtime config"
bash scripts/check_llm_runtime.sh --soft

echo
echo "3. Run map"
bash scripts/llm_wiki_agent.sh map

echo
echo "4. Build prompts without calling an LLM"
bash scripts/llm_wiki_agent.sh prompt weave 02-ingest-and-weave >/tmp/originone-wiki-weave-prompt.md
bash scripts/llm_wiki_agent.sh prompt ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki" >/tmp/originone-wiki-ask-prompt.md
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" >/tmp/originone-wiki-manual-ask.md
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" >/tmp/originone-wiki-api-dry-run.txt
bash scripts/llm_wiki_api_runner.sh prompt ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" >/tmp/originone-wiki-api-prompt.md
grep -q "LLM-Wiki Agent" /tmp/originone-wiki-weave-prompt.md
grep -q "wiki-first" /tmp/originone-wiki-ask-prompt.md || grep -q "wiki" /tmp/originone-wiki-ask-prompt.md
grep -q "Manual Chat Mode" /tmp/originone-wiki-manual-ask.md
grep -q "Bundled Stage Files" /tmp/originone-wiki-manual-ask.md
grep -q "API runner dry run" /tmp/originone-wiki-api-dry-run.txt
grep -q "API Runner Mode" /tmp/originone-wiki-api-prompt.md
grep -q "Required JSON schema" /tmp/originone-wiki-api-prompt.md

echo
echo "5. Validate design package"
bash scripts/validate_design_package.sh design-package

echo
echo "OK: OriginOne-Wiki harness is ready. Run API runner or Agent weave/ask to modify wiki/output."
