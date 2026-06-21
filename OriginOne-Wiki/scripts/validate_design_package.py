#!/usr/bin/env python3
"""Validate the OriginOne-Wiki design package.

This local validator is intentionally lightweight. It lets readers who cloned
the public repository check the demo package without relying on a private Codex
skill path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = [
    "wiki-product-brief.md",
    "retrieval-contracts.md",
    "ingest-contracts.md",
    "storage-architecture.md",
    "directory-blueprint.md",
    "implementation-plan.md",
    "tech-stack-recommendation.md",
    "health-check-rules.md",
]

REQUIRED_STAGE_DIRS = [
    "00-minimal-raw-wiki-output",
    "01-retrieve-first",
    "02-ingest-and-weave",
    "03-output-and-reuse",
    "04-scenario-data-dev",
    "05-scenario-personal-kb",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OriginOne-Wiki design package")
    parser.add_argument("package_dir", type=Path, help="Path to design-package")
    args = parser.parse_args()

    package_dir = args.package_dir
    if not package_dir.is_dir():
        fail(f"package directory not found: {package_dir}")

    missing = [name for name in REQUIRED_FILES if not (package_dir / name).is_file()]
    if missing:
        fail("missing required files: " + ", ".join(missing))

    empty = [name for name in REQUIRED_FILES if not (package_dir / name).read_text(encoding="utf-8").strip()]
    if empty:
        fail("empty required files: " + ", ".join(empty))

    root = package_dir.parent
    missing_dirs = [name for name in REQUIRED_STAGE_DIRS if not (root / name).is_dir()]
    if missing_dirs:
        fail("missing stage directories: " + ", ".join(missing_dirs))

    blueprint = (package_dir / "directory-blueprint.md").read_text(encoding="utf-8")
    for stage in REQUIRED_STAGE_DIRS:
        if stage not in blueprint:
            fail(f"directory-blueprint.md does not mention {stage}")

    required_terms = ["Retrieval Contracts", "Ingest Contracts", "Storage Architecture", "Health Check"]
    combined = "\n".join((package_dir / name).read_text(encoding="utf-8") for name in REQUIRED_FILES)
    missing_terms = [term for term in required_terms if term.lower() not in combined.lower()]
    if missing_terms:
        fail("design package missing expected terms: " + ", ".join(missing_terms))

    print(f"Package: {package_dir.resolve()}")
    print("Status: PASS")
    print("No issues found.")


if __name__ == "__main__":
    main()

