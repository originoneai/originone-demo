#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== OriginOne-Wiki smoke test =="
echo "cwd: $(pwd)"

echo
echo "1. Check Python scripts"
python3 -m py_compile \
  scripts/llm_wiki_demo.py \
  scripts/make_terminal_screenshots.py \
  scripts/validate_design_package.py

echo
echo "2. Run map"
python3 scripts/llm_wiki_demo.py map

echo
echo "3. Run full demo"
python3 scripts/llm_wiki_demo.py demo-all

echo
echo "4. Check screenshots"
for file in \
  assets/screenshots/00-map.png \
  assets/screenshots/01-retrieve-first.png \
  assets/screenshots/02-weave.png \
  assets/screenshots/02-ask.png \
  assets/screenshots/04-data-dev.png \
  assets/screenshots/05-personal-kb.png
do
  test -s "$file"
  echo "ok $file"
done

echo
echo "5. Validate design package"
python3 scripts/validate_design_package.py design-package

echo
echo "OK: OriginOne-Wiki demo is runnable."
