"""Tests for the loader (test 2 + knowledge layer)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.objects.loader import (
    DEFAULT_SAMPLES_DIR,
    KnowledgeObject,
    load_objects_from_dir,
    load_objects,
)


def test_default_samples_dir_has_three_objects() -> None:
    objs = load_objects_from_dir(DEFAULT_SAMPLES_DIR)
    assert len(objs) >= 3, "expected at least 3 sample Knowledge Objects"
    identities = sorted(o.identity for o in objs)
    assert any("GoldenCase" in i for i in identities)
    assert any("FailurePattern" in i for i in identities)
    assert any("DecisionPattern" in i for i in identities)


def test_loader_skips_files_without_identity(tmp_path: Path) -> None:
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    good.write_text(json.dumps({"identity": "X", "principle": "p"}), encoding="utf-8")
    bad.write_text(json.dumps({"principle": "p"}), encoding="utf-8")

    objs = load_objects_from_dir(tmp_path)
    assert len(objs) == 1
    assert objs[0].identity == "X"
    assert bad.name not in [o["_source_file"] for o in objs]
    assert good.name in [o["_source_file"] for o in objs]


def test_load_objects_explicit(tmp_path: Path) -> None:
    p = tmp_path / "ko.json"
    p.write_text(json.dumps({"identity": "Y", "principle": "p"}), encoding="utf-8")
    out = load_objects([p])
    assert len(out) == 1
    assert isinstance(out[0], KnowledgeObject)
    assert out[0]["identity"] == "Y"