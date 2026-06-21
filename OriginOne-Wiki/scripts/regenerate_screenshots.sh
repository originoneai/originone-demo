#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 - <<'PY'
try:
    import PIL  # noqa: F401
except Exception as exc:
    raise SystemExit(
        "Pillow is required to regenerate screenshots. "
        "Run: python3 -m pip install -r requirements.txt"
    ) from exc
PY

python3 scripts/make_terminal_screenshots.py assets/screenshots/*.txt

echo "OK: screenshots regenerated under assets/screenshots/"
