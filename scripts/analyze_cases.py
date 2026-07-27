"""CaseOS batch case analyzer.

This script has ONE responsibility: flow control.

Flow:
    read images
        |
        v
    for each image:
        |
        v
        call VisionAnalyzer
        |
        v
        receive JSON
        |
        v
        save analysis
        |
        v
        continue to next image

All actual work (prompt loading, model call, JSON persistence) is
delegated to ``backend/scripts/run_vision.py``. This top-level entry
exists only so the operator can invoke CaseOS without knowing the
backend layout.

Usage:
    python scripts/analyze_cases.py                       # data/images/
    python scripts/analyze_cases.py path/to/one.png
    python scripts/analyze_cases.py path/to/folder
    python scripts/analyze_cases.py data/images --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parent.parent
_BACKEND = _REPO_ROOT / "backend"

# Make ``backend`` importable so we can reuse its analyzer pipeline.
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Backend module (not this file's directory) is the source of truth.
from scripts.run_vision import run as _run_pipeline  # noqa: E402

_DEFAULT_INPUT = _REPO_ROOT / "data" / "images"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI args. Nothing more."""
    parser = argparse.ArgumentParser(
        prog="analyze_cases",
        description="CaseOS batch case analyzer (flow control only).",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=str(_DEFAULT_INPUT),
        help="Image file or directory. Defaults to data/images/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-analyze even when the analysis JSON already exists.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Single flow: enumerate -> analyze -> save -> next."""
    args = _parse_args(argv)
    # All implementation is in the backend; this is orchestration only.
    _run_pipeline(args.input, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
