#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== OriginOne-Wiki smoke test =="
echo "cwd: $(pwd)"

echo
echo "1. Check Python scripts"
python3 -m py_compile \
  scripts/llm_wiki_demo.py \
  scripts/validate_design_package.py

echo
echo "2. Run map"
python3 scripts/llm_wiki_demo.py map

echo
echo "3. Run full demo"
python3 scripts/llm_wiki_demo.py demo-all

echo
echo "4. Validate design package"
python3 scripts/validate_design_package.py design-package

echo
echo "OK: OriginOne-Wiki demo is runnable."
