"""Local-JSON loader for Knowledge Objects (Sprint 19.1 stub).

Real retrieval lands in Sprint 20 (ADR-015c). For now this module
loads every `.json` file under a directory and treats each as one
Knowledge Object.

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

A file may use a subset of these fields (placeholders do); the
loader does not enforce schema, only that `identity` is present
so the file can be indexed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


# Default location, relative to this file. Sprint 19.1 ships three
# sample Knowledge Objects at this path.
DEFAULT_SAMPLES_DIR = Path(__file__).resolve().parent / "samples"


class KnowledgeObject(dict):
    """A `KnowledgeObject` is a dict with a required `identity` key.

    Subclassing dict gives ergonomic access (`obj["identity"]`) without
    forcing callers to learn a new API.
    """

    @property
    def identity(self) -> str:
        return self.get("identity", "<unknown>")


def load_objects_from_dir(directory: Path | str) -> list[KnowledgeObject]:
    """Load every JSON file under `directory` as a Knowledge Object.

    Files that do not parse as JSON, or that parse but have no
    `identity` field, are skipped silently. This lenient behaviour
    matches the spec ("Support loading sample Knowledge Objects";
    "No vector retrieval. No database. Local files only.").
    """

    out: list[KnowledgeObject] = []
    directory = Path(directory)
    if not directory.exists():
        return out
    for path in sorted(directory.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or "identity" not in data:
            continue
        data["_source_file"] = path.name
        out.append(KnowledgeObject(data))
    return out


def load_objects(paths: Iterable[Path]) -> list[KnowledgeObject]:
    """Load an explicit list of paths (used by tests)."""
    out: list[KnowledgeObject] = []
    for p in paths:
        try:
            with Path(p).open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and "identity" in data:
            data["_source_file"] = Path(p).name
            out.append(KnowledgeObject(data))
    return out


__all__ = ["KnowledgeObject", "load_objects_from_dir", "load_objects",
           "DEFAULT_SAMPLES_DIR"]