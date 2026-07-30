"""scripts/migrations/v2_to_v3.py

Idempotent V2 to V3 conversion helper for one CaseOS Vision output.

Usage:
    python scripts/migrations/v2_to_v3.py INPUT.json OUTPUT.json

The input is expected to be the flat V2 shape that was on disk
before ADR-008 (2026-07-30). The output is the V3 nested shape.
If the input is already V3 (has ai_analysis wrapper), the script
is a no-op and exits 0. Run it freely in CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def v2_to_v3(case, image_filename):
    metadata = case.get("metadata") or {
        "model": "qwen3.7-plus",
        "vision_standard": "CaseOS_Vision_Standard_V1",
        "output_schema": "CaseOS_Output_Schema_V3",
        "analyzed_at": "2026-07-30T00:00:00Z",
    }
    return {
        "basic_info": {
            "project_name": case.get("project_name", ""),
            "case_id": image_filename,
            "site_type": case.get("site_type", ""),
            "country": "", "city": "",
        },
        "design": {
            "theme": case.get("theme", []) or [],
            "style": case.get("style", []) or [],
            "design_language": case.get("design_keywords", []) or [],
            "design_story": "", "design_highlights": [],
        },
        "target_users": {
            "age_group": case.get("age_group", []) or [],
            "user_type": [],
            "estimated_capacity": "",
        },
        "play_experience": {
            "play_behaviors": case.get("play_behaviors", []) or [],
            "play_value": [],
            "challenge_level": "",
            "interaction_type": [],
        },
        "space": {
            "space_structure": "",
            "functional_zones": [],
            "circulation": "",
            "viewpoints": [],
        },
        "equipment": {
            "functional_units": case.get("functional_units", []) or [],
            "core_equipment": [],
            "interactive_devices": [],
        },
        "landscape": {
            "planting": [],
            "terrain": "",
            "water_features": [],
            "shade": "",
        },
        "materials": {
            "main_materials": case.get("materials", []) or [],
            "ground_materials": [],
            "safety_surface": [],
        },
        "color": {
            "colors": case.get("colors", []) or [],
            "main_color": "",
            "color_strategy": "",
        },
        "safety": {
            "estimated_age_range": "",
            "risk_level": "",
            "inclusive_design": False,
        },
        "commercial": {
            "applicable_scene": [],
            "commercial_value": [],
            "operation_features": [],
        },
        "ai_analysis": {
            "keywords": case.get("design_keywords", []) or [],
            "vision_summary": case.get("vision_summary", ""),
            "design_interpretation": case.get("design_interpretation", ""),
            "confidence": 0.6,
        },
        "metadata": metadata,
    }


def main(argv):
    if len(argv) != 3:
        print("usage: python v2_to_v3.py INPUT.json OUTPUT.json", file=sys.stderr)
        return 2
    src = Path(argv[1])
    dst = Path(argv[2])
    raw = json.loads(src.read_text(encoding="utf-8"))
    if raw.get("ai_analysis"):
        if src != dst:
            dst.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    image_filename = src.stem + ".png"
    v3 = v2_to_v3(raw, image_filename)
    dst.write_text(json.dumps(v3, ensure_ascii=False, indent=2), encoding="utf-8")
    print("converted:", src, "->", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
