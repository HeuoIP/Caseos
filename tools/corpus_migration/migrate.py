"""Corpus migration CLI (Sprint 20.5).

Migrates the legacy sample KOs (under
`backend/caseos/knowledge/objects/samples/`) into the new
5-subdirectory corpus layout, validating each migrated KO
against the ADR-015 contract.

Usage:

    python -m tools.corpus_migration.migrate \
        --source backend/caseos/knowledge/objects/samples \
        --target backend/caseos/knowledge/corpus

The migration is *additive*: the legacy `samples/` directory is
left untouched. A mapping from the legacy identity to the
canonical subdirectory is maintained as the 5 ADR-015 identity
prefixes (GoldenCase, DecisionPattern, FailurePattern,
ExpertPrinciple, UserPreference).

If a target file already exists and is identical, the migration
is a no-op. If the target differs, the migration refuses to
overwrite (pass `--force` to override).

No network, no LLM, no embedding. Python stdlib only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Make `backend/` importable so the validator (a tools-level
# module) can import `tools.corpus_migration.validator` without
# the package being on sys.path when invoked as a script.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Local import (after sys.path fix).
from tools.corpus_migration.validator import (  # noqa: E402
    validate_knowledge_object,
    ValidationResult,
)


# Mapping from ADR-015 identity prefix to canonical subdirectory.
# Anything not in this map goes to the `golden_cases` bucket
# (which is the catch-all for "proven design examples").
PREFIX_TO_SUBDIR = {
    "GoldenCase":     "golden_cases",
    "DecisionPattern": "decision_patterns",
    "FailurePattern":  "failure_patterns",
    "ExpertPrinciple": "expert_principles",
    "UserPreference":  "user_preferences",
}


def _subdir_for_identity(identity: str) -> str:
    """Map a KO identity to its target subdirectory.

    The mapping is by prefix; an unknown prefix falls back to
    `golden_cases` (the most permissive bucket).
    """
    for prefix, subdir in PREFIX_TO_SUBDIR.items():
        if identity.startswith(prefix):
            return subdir
    return "golden_cases"


def _safe_filename(identity: str) -> str:
    """Convert a KO identity into a filesystem-safe filename. Drops the ADR-015 IdentityType prefix so the corpus is human-readable; the type is recovered from the parent subdirectory and from the identity string itself."""
    stem = identity.split(".", 1)[1] if "." in identity else identity
    return stem.replace("/", "_") + ".json"


def migrate_one(
    source_path: Path,
    target_root: Path,
    force: bool = False,
) -> tuple[Path, ValidationResult]:
    """Migrate a single source file to its target subdirectory.

    Returns (target_path, validation_result). Raises if the
    target exists and differs and `force` is False.
    """
    with source_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    validation = validate_knowledge_object(data)
    identity = data.get("identity") if isinstance(data, dict) else None
    if not identity:
        identity = "<unknown>"

    subdir = _subdir_for_identity(str(identity))
    target_dir = target_root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / _safe_filename(str(identity))

    if target_path.exists() and not force:
        existing = json.loads(target_path.read_text(encoding="utf-8"))
        if existing == data:
            return target_path, validation  # no-op
        raise FileExistsError(
            f"target {target_path} exists with different content; "
            "pass --force to overwrite"
        )

    target_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target_path, validation


def migrate_directory(
    source_dir: Path,
    target_dir: Path,
    force: bool = False,
) -> list[tuple[Path, ValidationResult]]:
    """Migrate every .json file under `source_dir` (non-recursive)
    into `target_dir` (using the prefix routing). Returns a list
    of (target_path, validation_result) tuples.
    """
    out: list[tuple[Path, ValidationResult]] = []
    for path in sorted(source_dir.glob("*.json")):
        try:
            target, validation = migrate_one(path, target_dir, force=force)
        except FileExistsError as e:
            print(f"[skip] {e}", file=sys.stderr)
            continue
        out.append((target, validation))
    return out


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="caseos-corpus-migrate",
        description="Migrate sample KOs into the Golden Case Corpus V1.",
    )
    p.add_argument(
        "--source",
        default=str(_BACKEND / "caseos" / "knowledge" / "objects" / "samples"),
        help="Source directory (legacy samples).",
    )
    p.add_argument(
        "--target",
        default=str(_BACKEND / "caseos" / "knowledge" / "corpus"),
        help="Target root (5-subdir corpus).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite target files that differ.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"[error] source directory not found: {source}", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)

    results = migrate_directory(source, target, force=args.force)
    if not results:
        print(f"[warn] no .json files found in {source}", file=sys.stderr)
        return 0

    ok = sum(1 for _t, v in results if v.valid)
    print(f"[ok] migrated {len(results)} file(s) from {source} -> {target}")
    print(f"[ok] {ok}/{len(results)} pass ADR-015 validation")
    for target_path, validation in results:
        flag = "OK" if validation.valid else "FAIL"
        print(f"  [{flag}] {target_path.relative_to(target)}  identity={validation.identity}")
        for err in validation.errors:
            print(f"          ! {err}")
        for miss in validation.missing:
            print(f"          - missing: {miss}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())