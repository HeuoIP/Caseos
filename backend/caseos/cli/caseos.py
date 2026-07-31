"""CaseOS CLI entry point (`caseos analyze`).

The CLI is intentionally thin: it parses a project.json, runs the
default pipeline, and writes the Markdown report. Network calls,
LLM calls, image generation, and database writes are explicitly
out of scope per Sprint 19.1 "Explicit NOT Included".

Usage (from repo root):

    python -m caseos.cli.caseos analyze path/to/project.json

The Markdown is written to stdout (so it can be redirected) and also
to the path given by --output (default: alongside the input file
with suffix `.analysis.md`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from caseos.brain.runtime.context import ProjectContext
from caseos.brain.runtime.pipeline import default_pipeline


def _load_project(path: Path) -> ProjectContext:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project.json root must be a JSON object: {path}")
    project_id = data.get("project_id") or path.stem
    data.setdefault("project_id", project_id)
    return ProjectContext.from_dict(data)


def cmd_analyze(args: argparse.Namespace) -> int:
    project_path = Path(args.project).resolve()
    if not project_path.exists():
        print(f"[error] project file not found: {project_path}", file=sys.stderr)
        return 2
    project = _load_project(project_path)

    pipeline = default_pipeline()
    ctx = pipeline.run(project)

    markdown = ctx.metadata.get("markdown") or ""

    output_path = Path(args.output).resolve() if args.output else project_path.with_suffix(".analysis.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    if args.also_stdout:
        print(markdown)
    print(f"[ok] Wrote {output_path}", file=sys.stderr)
    print(f"[ok] Stages executed: {[s.name for s in pipeline.stages]}", file=sys.stderr)
    print(f"[ok] Trust confidence: {ctx.trust_object.get('confidence', 'Unknown') if ctx.trust_object else 'Unknown'}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="caseos", description="CaseOS CLI (Sprint 19.1).")
    sub = p.add_subparsers(dest="command", required=True)
    pa = sub.add_parser("analyze", help="Run the default pipeline on a project.json.")
    pa.add_argument("project", help="Path to a project.json file.")
    pa.add_argument("-o", "--output", help="Path for the Markdown report (default: <input>.analysis.md).")
    pa.add_argument("--stdout", dest="also_stdout", action="store_true", help="Echo Markdown to stdout as well.")
    pa.set_defaults(func=cmd_analyze)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())