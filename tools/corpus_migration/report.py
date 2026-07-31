"""Corpus quality report generator (Sprint 20.5).

Produces a Markdown quality report covering:

  * object count (total + per-subdirectory)
  * identity distribution (by ADR-015 prefix)
  * ADR-015 validation result (one row per KO)
  * missing-field summary
  * retrieval benchmark result (the three Sprint 20.5 cases)

Usage:

    python -m tools.corpus_migration.report \
        --corpus backend/caseos/knowledge/corpus \
        --output docs/reviews/Sprint_20_5_Corpus_Quality_Report.md

The benchmark section invokes the existing Sprint 20 retrieval
engine against a small set of benchmark project fixtures. The
engine is unchanged (per "Do not change Retrieval decision
logic"); the report is read-only.

Python stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from tools.corpus_migration.validator import (  # noqa: E402
    REQUIRED_FIELDS,
    validate_corpus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _identity_prefix(identity: str) -> str:
    """Extract the ADR-015 prefix (e.g. GoldenCase) from a KO identity."""
    for prefix in (
        "GoldenCase",
        "DecisionPattern",
        "FailurePattern",
        "ExpertPrinciple",
        "UserPreference",
    ):
        if identity.startswith(prefix):
            return prefix
    return "<unknown>"


def _collect_per_subdir(corpus_dir: Path) -> dict[str, list[Path]]:
    """Group every .json file in the corpus by its parent subdir."""
    out: dict[str, list[Path]] = {}
    for path in sorted(corpus_dir.rglob("*.json")):
        rel = path.relative_to(corpus_dir)
        sub = rel.parts[0] if len(rel.parts) > 1 else "<root>"
        out.setdefault(sub, []).append(path)
    return out


# ---------------------------------------------------------------------------
# Benchmark definitions
# ---------------------------------------------------------------------------

# Each benchmark is a (name, project_type, site_description,
# user_goal, constraints, expected_substring) tuple. The
# retrieval engine is run against the corpus; we record whether
# the expected knowledge category appears in the result.
BENCHMARKS = [
    {
        "id": "A",
        "label": "Kindergarten -- empty site, natural preference, "
                 "avoid equipment stacking",
        "project_type": "kindergarten_outdoor",
        "site_description": (
            "outdoor area with some existing equipment but lacks a "
            "memorable identity; owner prefers natural materials"
        ),
        "user_goal": "improve enrollment",
        "constraints": "limited budget",
        "expected_substrings": [
            # We expect to retrieve a DecisionPattern, a GoldenCase,
            # AND a FailurePattern (in any order, in any count >= 1
            # of each).
            "DecisionPattern",
            "GoldenCase",
            "FailurePattern",
        ],
    },
    {
        "id": "B",
        "label": "Public space -- community green, children + elderly",
        "project_type": "public_park_open_area",
        "site_description": (
            "open community green with walking paths and partial shade"
        ),
        "user_goal": "support multi-generation users",
        "constraints": "limited budget",
        "expected_substrings": [
            "park",
        ],
    },
    {
        "id": "C",
        "label": "Cultural tourism -- theme experience, visitor journey",
        "project_type": "cultural_tourism",
        "site_description": (
            "linear historical district with multiple heritage sites"
        ),
        "user_goal": "create a memorable visitor journey",
        "constraints": "",
        "expected_substrings": [
            "cultural",
        ],
    },
]


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _run_benchmarks(corpus_dir: Path) -> list[dict]:
    """Run the three Sprint 20.5 retrieval benchmarks.

    Uses the Sprint 20 RetrievalEngine (unchanged); the report
    is read-only and does not modify the engine.
    """
    # Late import so the report script can be invoked from a
    # directory that does not have the backend on PYTHONPATH.
    from caseos.knowledge.objects.loader import load_corpus
    from caseos.knowledge.retrieval.module import RetrievalEngine
    from caseos.brain.runtime.context import ProjectContext

    objects = load_corpus(corpus_dir)
    engine = RetrievalEngine()

    out: list[dict] = []
    for bench in BENCHMARKS:
        project = ProjectContext(
            project_id=f"benchmark-{bench['id']}",
            project_type=bench["project_type"],
            site_description=bench["site_description"],
            user_goal=bench["user_goal"],
            constraints=bench["constraints"],
        )
        # A "synthetic decision" the engine can rank against. The
        # engine never *makes* the decision; it only ranks KOs
        # that match the project.
        synthetic_decision = {
            "decision": "Create a single experience anchor",
            "diagnosis": "the site lacks identity",
            "boundary": "Do not add scattered equipment",
        }
        ep = engine.retrieve(
            project=project,
            decision=synthetic_decision,
            knowledge_patterns=objects,
        )
        ids = [ko.get("identity", "") for ko in ep.relevant_objects]
        # Per-benchmark verdict
        missing = [
            s for s in bench["expected_substrings"]
            if not any(s in i for i in ids)
        ]
        out.append({
            "id": bench["id"],
            "label": bench["label"],
            "project_type": bench["project_type"],
            "retrieved_identities": ids,
            "expected_substrings": bench["expected_substrings"],
            "missing_substrings": missing,
            "passed": not missing,
            "applicability_reason": ep.applicability_reason,
        })
    return out


def _build_report(
    corpus_dir: Path,
    validation_results: list,
    benchmarks: list[dict],
) -> str:
    """Compose the Markdown report. Pure function."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    per_sub = _collect_per_subdir(corpus_dir)
    total = sum(len(paths) for paths in per_sub.values())

    valid_count = sum(1 for v in validation_results if v.valid)
    invalid_count = total - valid_count

    # Identity distribution (by prefix).
    prefix_counter: Counter = Counter()
    for v in validation_results:
        if v.identity and v.identity != "<unknown>" and v.identity != "<unparseable>":
            prefix_counter[_identity_prefix(v.identity)] += 1

    # Missing-field summary.
    missing_counter: Counter = Counter()
    for v in validation_results:
        for m in v.missing:
            missing_counter[m] += 1

    # Build the Markdown body.
    lines: list[str] = []
    lines.append("# Sprint 20.5 -- Golden Case Corpus Quality Report V1")
    lines.append("")
    lines.append(f"- **Generated:** {now}")
    lines.append(f"- **Corpus root:** `{corpus_dir}`")
    lines.append(f"- **Total Knowledge Objects:** {total}")
    lines.append(f"- **Valid (ADR-015 9-field contract):** {valid_count}")
    lines.append(f"- **Invalid:** {invalid_count}")
    lines.append("")
    lines.append(
        "This report is generated by `tools/corpus_migration/report.py`. "
        "It is read-only; the Sprint 20 retrieval engine is unchanged."
    )
    lines.append("")

    # ---- Section 1: object count per subdirectory ----
    lines.append("## 1. Object Count")
    lines.append("")
    lines.append("| Subdirectory | Count |")
    lines.append("| --- | --- |")
    for sub, paths in sorted(per_sub.items()):
        lines.append(f"| `{sub}/` | {len(paths)} |")
    lines.append(f"| **TOTAL** | **{total}** |")
    lines.append("")

    # ---- Section 2: identity distribution ----
    lines.append("## 2. Identity Distribution (by ADR-015 prefix)")
    lines.append("")
    lines.append("| Prefix | Count |")
    lines.append("| --- | --- |")
    for prefix, count in sorted(prefix_counter.items()):
        lines.append(f"| `{prefix}` | {count} |")
    lines.append("")

    # ---- Section 3: validation result per KO ----
    lines.append("## 3. Validation Result (ADR-015 9-field contract)")
    lines.append("")
    lines.append(
        "Each row is one Knowledge Object. `OK` means all 9 fields are "
        "present and the mandatory fields (`applicability`, `boundary`) "
        "pass their type checks. `FAIL` rows below must be fixed before "
        "they enter the corpus."
    )
    lines.append("")
    lines.append("| Status | Identity | Missing Fields | Errors |")
    lines.append("| --- | --- | --- | --- |")
    for v in validation_results:
        status = "OK" if v.valid else "FAIL"
        missing = ", ".join(v.missing) if v.missing else "-"
        errors = "; ".join(v.errors) if v.errors else "-"
        lines.append(f"| {status} | `{v.identity}` | {missing} | {errors} |")
    lines.append("")

    # ---- Section 4: missing-field summary ----
    lines.append("## 4. Missing-Field Summary")
    lines.append("")
    if missing_counter:
        lines.append("| Field | Count |")
        lines.append("| --- | --- |")
        for field_name, count in sorted(missing_counter.items(), key=lambda x: -x[1]):
            lines.append(f"| `{field_name}` | {count} |")
    else:
        lines.append("_No missing fields._")
    lines.append("")

    # ---- Section 5: retrieval benchmark ----
    lines.append("## 5. Retrieval Benchmark")
    lines.append("")
    bench_pass = sum(1 for b in benchmarks if b["passed"])
    lines.append(f"**Result: {bench_pass}/{len(benchmarks)} benchmarks pass.**")
    lines.append("")
    for b in benchmarks:
        flag = "PASS" if b["passed"] else "FAIL"
        lines.append(f"### Benchmark {b['id']} -- {flag}")
        lines.append("")
        lines.append(f"- **Label:** {b['label']}")
        lines.append(f"- **Project type:** `{b['project_type']}`")
        lines.append(f"- **Expected category substrings:** {b['expected_substrings']}")
        lines.append(f"- **Retrieved identities ({len(b['retrieved_identities'])}):**")
        if b["retrieved_identities"]:
            for ident in b["retrieved_identities"]:
                lines.append(f"  - `{ident}`")
        else:
            lines.append("  - _(none)_")
        if b["missing_substrings"]:
            lines.append(f"- **MISSING:** {b['missing_substrings']}")
        lines.append("")

    # ---- Section 6: summary ----
    lines.append("## 6. Summary")
    lines.append("")
    lines.append(
        f"- Corpus has **{total}** Knowledge Objects across "
        f"**{len(per_sub)}** subdirectories."
    )
    lines.append(
        f"- **{valid_count}** pass ADR-015 validation, "
        f"**{invalid_count}** require fixes."
    )
    lines.append(
        f"- Retrieval benchmarks: **{bench_pass}/{len(benchmarks)}** pass."
    )
    lines.append("")
    if valid_count == total and bench_pass == len(benchmarks):
        lines.append("**Sprint 20.5 acceptance criteria: all met.**")
    else:
        lines.append("**Sprint 20.5 acceptance criteria: NOT all met; see FAIL rows above.**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "_End of report. Generated by `tools.corpus_migration.report`._"
    )
    lines.append("")
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="caseos-corpus-report",
        description="Generate the Sprint 20.5 corpus quality report.",
    )
    p.add_argument(
        "--corpus",
        default=str(_BACKEND / "caseos" / "knowledge" / "corpus"),
        help="Corpus root to inspect.",
    )
    p.add_argument(
        "--output",
        default=str(_REPO_ROOT / "docs" / "reviews" /
                    "Sprint_20_5_Corpus_Quality_Report.md"),
        help="Output Markdown path.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    corpus_dir = Path(args.corpus)
    if not corpus_dir.exists():
        print(f"[error] corpus directory not found: {corpus_dir}", file=sys.stderr)
        return 2

    validation = validate_corpus(corpus_dir)
    benchmarks = _run_benchmarks(corpus_dir)
    markdown = _build_report(corpus_dir, validation, benchmarks)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"[ok] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())