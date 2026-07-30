"""Stage 2: bridge to the Vision Engine.

Wraps the existing ``VisionAnalyzer`` (see
``app.services.vision.analyzer``) so the pipeline has a single
``analyze()`` method that returns a structured
``RawCaseUnderstanding``.

The wrapper does THREE things beyond a thin pass-through:

1.  Validates the image file exists before calling the Vision Engine
    -- avoids round-tripping for missing files.
2.  Normalises the Vision V3 JSON into the five raw-understanding
    fields required by Sprint 18 Stage 2.
3.  Preserves the full Vision payload in ``RawCaseUnderstanding.vision_payload``
    so the extractor (Stage 3) and Reviewer (Stage 5) can read
    taxonomy fields the wrapper does not pre-shape.

The wrapper never modifies the Vision Engine contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import CaseInput, RawCaseUnderstanding

if TYPE_CHECKING:
    from app.services.vision.analyzer import VisionAnalyzer


def _coerce_list(value: Any) -> list[str]:
    """Normalise any 'value or list of values' field into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            if isinstance(v, dict):
                # Vision V3 stores taxonomy fields as [{id, role, confidence}, ...]
                out.append(str(v.get("id") or v.get("value") or ""))
            elif v is not None:
                out.append(str(v))
        return [x for x in out if x]
    if isinstance(value, dict):
        return [str(value.get("id") or value.get("value") or "")]
    return [str(value)]


class CaseImageAnalyzer:
    """Stage 2 of the Golden Case pipeline.

    Usage:

        analyzer = CaseImageAnalyzer(build_vision_analyzer())
        raw = analyzer.analyze(CaseInput(image_path=..., source=..., ...))
    """

    def __init__(self, vision_analyzer: "VisionAnalyzer") -> None:
        self._vision = vision_analyzer

    def analyze(self, case_input: CaseInput) -> RawCaseUnderstanding:
        image_path = case_input.image_path

        # 1. Validate file exists -- prevents the Vision Engine from
        #    retrying on a missing file and makes failure a clear
        #    pipeline-level error (handled in ``pipeline.py``).
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 2. Call the Vision Engine. May raise provider / network errors;
        #    the pipeline catches them at Stage 2.
        payload = self._vision.analyze(image_path)

        # 3. Build the raw understanding from the V3 payload.
        return self._from_payload(payload, image_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _from_payload(payload: dict[str, Any], image_path: str) -> RawCaseUnderstanding:
        """Map a Vision V3 JSON onto the five RawCaseUnderstanding fields.

        Field mapping (see ``schemas/case_analysis_v3.json``):

            visible_elements            <- design.functional_units
                                           + design.design_highlights
            spatial_features            <- design.style
                                           + spatial_characteristics
            environmental_relationship  <- basic_info.site_type
            possible_user_behavior      <- play_experience.play_behaviors
            visual_characteristics      <- color.colors
                                           + ai_analysis.keywords
        """
        design = payload.get("design", {}) or {}
        basic = payload.get("basic_info", {}) or {}
        play_exp = payload.get("play_experience", {}) or {}
        equipment = payload.get("equipment", {}) or {}
        materials = payload.get("materials", {}) or {}
        color = payload.get("color", {}) or {}
        ai_analysis = payload.get("ai_analysis", {}) or {}

        visible = _coerce_list(equipment.get("functional_units")) + _coerce_list(
            design.get("design_highlights")
        )
        spatial = _coerce_list(design.get("style")) + _coerce_list(
            design.get("spatial_characteristics")
        )
        env_rel = str(basic.get("site_type") or "") or ""
        behavior = _coerce_list(play_exp.get("play_behaviors"))
        visuals = _coerce_list(color.get("colors")) + _coerce_list(
            ai_analysis.get("keywords")
        )

        # Materials are not in the five "raw understanding" fields, but
        # the extractor still wants them. Keep them on the payload so
        # Stage 3 can pick them up.
        if materials.get("main_materials"):
            payload.setdefault("_derived", {})["materials"] = _coerce_list(
                materials.get("main_materials")
            )

        return RawCaseUnderstanding(
            image_path=image_path,
            visible_elements=visible,
            spatial_features=spatial,
            environmental_relationship=env_rel,
            possible_user_behavior=behavior,
            visual_characteristics=visuals,
            vision_payload=payload,
        )


__all__ = ["CaseImageAnalyzer"]
