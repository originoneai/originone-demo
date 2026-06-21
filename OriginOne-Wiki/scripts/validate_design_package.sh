#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_DIR="${1:-$ROOT/design-package}"

required_files=(
  wiki-product-brief.md
  retrieval-contracts.md
  ingest-contracts.md
  storage-architecture.md
  directory-blueprint.md
  implementation-plan.md
  tech-stack-recommendation.md
  health-check-rules.md
)

required_stages=(
  00-minimal-raw-wiki-output
  01-retrieve-first
  02-ingest-and-weave
  03-output-and-reuse
  04-scenario-data-dev
  05-scenario-personal-kb
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

test -d "$PACKAGE_DIR" || fail "package directory not found: $PACKAGE_DIR"
test -s "$ROOT/.env.example" || fail "missing .env.example"
test -s "$ROOT/scripts/check_llm_runtime.sh" || fail "missing scripts/check_llm_runtime.sh"
test -s "$ROOT/scripts/llm_wiki_api_runner.sh" || fail "missing scripts/llm_wiki_api_runner.sh"
test -s "$ROOT/scripts/lib/llm_wiki_api_runner.mjs" || fail "missing scripts/lib/llm_wiki_api_runner.mjs"
test -s "$ROOT/scripts/lib/load_env.sh" || fail "missing scripts/lib/load_env.sh"

for file in "${required_files[@]}"; do
  test -s "$PACKAGE_DIR/$file" || fail "missing or empty design file: $file"
done

for stage in "${required_stages[@]}"; do
  test -d "$ROOT/$stage" || fail "missing stage directory: $stage"
  test -d "$ROOT/$stage/raw" || fail "missing raw directory: $stage/raw"
  test -d "$ROOT/$stage/wiki" || fail "missing wiki directory: $stage/wiki"
  test -d "$ROOT/$stage/output" || fail "missing output directory: $stage/output"
  grep -q "$stage" "$PACKAGE_DIR/directory-blueprint.md" || fail "directory-blueprint.md does not mention $stage"
done

combined="$(mktemp)"
cat "$PACKAGE_DIR"/*.md > "$combined"
grep -qi "Retrieval" "$combined" || fail "design package missing retrieval contract language"
grep -qi "Ingest" "$combined" || fail "design package missing ingest contract language"
grep -qi "LLM Agent" "$combined" || fail "design package must mention the LLM Agent layer"
grep -qi "API runner" "$combined" || fail "design package missing API runner language"
grep -qi "OpenAI-compatible" "$combined" || fail "design package missing OpenAI-compatible API language"
grep -qi "Health" "$combined" || fail "design package missing health-check language"
rm -f "$combined"

echo "Package: $(cd "$PACKAGE_DIR" && pwd)"
echo "Status: PASS"
echo "No issues found."
