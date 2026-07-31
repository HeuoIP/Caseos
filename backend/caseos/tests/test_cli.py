"""CLI tests (Sprint 19.1 acceptance Test 3: "markdown report generated").

We invoke the CLI via `python -m caseos.cli.caseos` to validate the
real entry point rather than re-implementing its parsing.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # caseos/tests/ -> repo root
BACKEND = REPO_ROOT / "backend"


def _run_cli(project_file: Path, output_file: Path) -> subprocess.CompletedProcess:
    env_overrides = {"PYTHONPATH": str(BACKEND)}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "caseos.cli.caseos",
            "analyze",
            str(project_file),
            "-o",
            str(output_file),
            "--stdout",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env_overrides},
        check=False,
    )


def test_cli_generates_markdown(tmp_path: Path) -> None:
    project = tmp_path / "kg.json"
    project.write_text(
        json.dumps(
            {
                "project_id": "kg-test",
                "project_type": "kindergarten_outdoor",
                "site_description": (
                    "outdoor area with some existing equipment but "
                    "the area lacks a memorable theme or identity"
                ),
                "user_goal": "increase enrollment",
                "constraints": "limited budget",
            }
        ),
        encoding="utf-8",
    )
    out_md = tmp_path / "report.md"

    cp = _run_cli(project, out_md)
    assert cp.returncode == 0, cp.stderr
    assert out_md.exists(), "Markdown report was not written"
    text = out_md.read_text(encoding="utf-8")
    # Six required headings from Sprint 19.1 example output:
    for heading in [
        "# Project Understanding",
        "# Spatial Diagnosis",
        "# Decision",
        "# Evidence",
        "# Confidence",
        "# Recommendation",
    ]:
        assert heading in text, f"Missing section: {heading}"

    # Sprint 19.3: with the fixture above triggering Decision R-01
    # (lack of identity + existing equipment) and a GoldenCase KO
    # applicable to kindergarten_outdoor, the Trust Engine emits
    # T-01 (full evidence) and confidence = Medium. The Markdown
    # renderer must also surface the canonical Sprint 19.3 caveat.
    assert "Medium" in text, "Sprint 19.3 expected Medium confidence"
    assert "Low" not in text, "Low should no longer be the only level"
    assert "Caveats" in text, "Caveats heading must be present"
    assert (
        "no site image analysis" in text.lower()
    ), "Sprint 19.3 canonical caveat must appear"