"""Local-JSON loader for Knowledge Objects (Sprint 19.1 stub + Sprint 20.5 corpus walker).

The shape of each object is the 9-field Knowledge Object Model from
ADR-015 (Section "Knowledge Object Core Structure"):

    - identity
    - situation_context
    - observation
    - diagnosis
    - decision
    - principle
    - applicability
    - boundary
    - feedback

Sprint 20.5 update: the corpus is now organised into 5 subdirectories
under `backend/caseos/knowledge/corpus/`:

    corpus/
    +-- golden_cases/
    +-- decision_patterns/
    +-- expert_principles/
    +-- failure_patterns/
    +-- user_preferences/

`load_corpus(corpus_dir)` walks every `.json` file under
`corpus_dir` (recursively) and returns the parsed objects.
`load_objects_from_dir(directory)` keeps its single-directory
behaviour for backward compatibility; the Knowledge Module uses
`load_corpus` since Sprint 20.5.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


# Legacy default: the original Sprint 19.1 samples. Retained so
# tests that target this exact path continue to work. The active
# pipeline uses `DEFAULT_CORPUS_DIR` instead.
DEFAULT_SAMPLES_DIR = Path(__file__).resolve().parent / "samples"

# Sprint 20.5 default: the 5-subdir corpus. Located one level up
# from this file (../corpus/).
DEFAULT_CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


class KnowledgeObject(dict):
    """A `KnowledgeObject` is a dict with a required `identity` key.

    Subclassing dict gives ergonomic access (`obj["identity"]`) without
    forcing callers to learn a new API.
    """

    @property
    def identity(self) -> str:
        return self.get("identity", "<unknown>")


def _load_one(path: Path) -> KnowledgeObject | None:
    """Load and validate a single JSON file as a KnowledgeObject.

    Returns None if the file does not parse, or if it does not
    contain a dict with an `identity` field. Silent skip matches
    the Sprint 19.1 contract.
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "identity" not in data:
        return None
    # Tag the source so reports can trace identity -> file.
    rel = path.name
    data["_source_file"] = rel
    subdir = path.parent.name
    if subdir and subdir not in ("samples", "corpus"):
        data["_source_subdir"] = subdir
    return KnowledgeObject(data)


def load_objects_from_dir(directory: Path | str) -> list[KnowledgeObject]:
    """Load every JSON file under `directory` (non-recursive).

    Files that do not parse as JSON, or that parse but have no
    `identity` field, are skipped silently. This lenient behaviour
    matches the Sprint 19.1 spec.
    """
    out: list[KnowledgeObject] = []
    directory = Path(directory)
    if not directory.exists():
        return out
    for path in sorted(directory.glob("*.json")):
        ko = _load_one(path)
        if ko is not None:
            out.append(ko)
    return out


def load_corpus(corpus_dir: Path | str) -> list[KnowledgeObject]:
    """Load every JSON file under `corpus_dir` (recursive).

    Used by the Knowledge Module since Sprint 20.5. The corpus
    is organised into 5 ADR-015 subdirectories; this function
    walks all of them.

    Files that fail to parse or that lack `identity` are skipped
    silently. Validation (the 9-field contract) is the
    migration tool\'s job, not the loader\'s -- the loader
    remains permissive so legacy / partial KOs can still flow
    through the retrieval pipeline.
    """
    out: list[KnowledgeObject] = []
    corpus_dir = Path(corpus_dir)
    if not corpus_dir.exists():
        return out
    for path in sorted(corpus_dir.rglob("*.json")):
        ko = _load_one(path)
        if ko is not None:
            out.append(ko)
    return out


def load_objects(paths: Iterable[Path]) -> list[KnowledgeObject]:
    """Load an explicit list of paths (used by tests)."""
    out: list[KnowledgeObject] = []
    for p in paths:
        ko = _load_one(Path(p))
        if ko is not None:
            out.append(ko)
    return out


__all__ = [
    "KnowledgeObject",
    "load_objects_from_dir",
    "load_objects",
    "load_corpus",
    "DEFAULT_SAMPLES_DIR",
    "DEFAULT_CORPUS_DIR",
]