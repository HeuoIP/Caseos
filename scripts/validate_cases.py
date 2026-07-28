"""CaseOS batch validator.

Iterates over every analysis JSON under ``data/analysis/cases/`` and
runs it through CaseOSValidator. Writes an aggregated report to
``data/analysis/validation_report.json`` and prints a console summary.

Pipeline position:

    VisionAnalyzer
        v
    Validator
        v
    Database

This script is the batch-mode gatekeeper. Anything that fails here
must NOT be persisted to the database.

Usage:
    python scripts/validate_cases.py
    python scripts/validate_cases.py path/to/another/dir
    python scripts/validate_cases.py data/analysis/cases/0001.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_INPUT_DIRNAME = "data/analysis/cases"
DEFAULT_REPORT_FILENAME = "validation_report.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_targets(arg: str | None) -> list[Path]:
    """Resolve CLI arg into a list of JSON files.

    - None -> DEFAULT_INPUT_DIRNAME (recursive)
    - directory -> every *.json under it
    - single file -> [file]
    """
    if arg is None:
        target = _repo_root() / DEFAULT_INPUT_DIRNAME
        if not target.exists():
            raise FileNotFoundError(target)
        return sorted(p for p in target.rglob("*.json"))

    p = Path(arg)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(pp for pp in p.rglob("*.json"))
    raise FileNotFoundError(p)


def _build_validator():
    """Construct a CaseOSValidator with default paths."""
    repo = _repo_root()
    sys.path.insert(0, str(repo / "backend"))
    from app.services.validator.validator import CaseOSValidator
    return CaseOSValidator(
        schema_path=repo / "schemas" / "case_analysis_v3.json",
        taxonomy_root=repo / "knowledge" / "taxonomy",
    )


def _result_to_dict(r, filename: str) -> dict[str, Any]:
    return {
        "file": filename,
        "passed": r.passed,
        "score": r.score,
        "errors": list(r.errors),
        "warnings": list(r.warnings),
        "suggestions": list(r.suggestions),
    }


def run(input_arg: str | None = None, report_path: Path | None = None) -> dict[str, Any]:
    """Validate every JSON and emit a report dict.

    Returns the report dict so callers can post-process or persist it.
    """
    targets = _resolve_targets(input_arg)
    if not targets:
        raise FileNotFoundError("No JSON files found in target directory.")

    validator = _build_validator()
    print("[CaseOS] validator : " + type(validator).__name__)
    print("[CaseOS] libraries  : " + str(validator.library_summary))
    print("[CaseOS] inputs     : " + str(len(targets)) + " JSON(s)")

    results: list[dict[str, Any]] = []
    for idx, t in enumerate(targets, 1):
        r = validator.validate_file(t)
        results.append(_result_to_dict(r, t.name))
        status = "PASS" if r.passed else "FAIL"
        print(f"[{idx}/{len(targets)}] {status:4s} score={r.score:3d}  {t.name}")

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    avg = (sum(r["score"] for r in results) / len(results)) if results else 0

    report = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "avg_score": round(avg, 2),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "results": results,
    }

    out = report_path or (_repo_root() / "data" / "analysis" / DEFAULT_REPORT_FILENAME)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + chr(10),
        encoding="utf-8",
    )

    print("[CaseOS] summary    : " + str(passed) + " OK / " + str(failed) + " Failed (avg=" + str(round(avg, 2)) + ")")
    print("[CaseOS] report     : " + str(out))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_cases",
        description="CaseOS batch validator (gatekeeper before database).",
    )
    parser.add_argument(
        "input", nargs="?", default=None,
        help="JSON file or directory. Default: data/analysis/cases/.",
    )
    parser.add_argument(
        "--report", default=None,
        help="Override output path for the report JSON.",
    )
    args = parser.parse_args(argv)
    run(args.input, Path(args.report) if args.report else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

