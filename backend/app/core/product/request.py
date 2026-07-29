"""User-facing input for the CaseOS Product Layer.

The ``ProductRequest`` is the only contract the user (or the future
Web UI) needs to honour. Everything else -- Vision analysis, Decision
Engine, Report generation -- is hidden behind
``ProductFlow.run(request)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectType(str, Enum):
    """The kind of project the user is designing."""

    KINDERGARTEN = "KINDERGARTEN"
    PUBLIC_PARK = "PUBLIC_PARK"
    COMMERCIAL_SPACE = "COMMERCIAL_SPACE"
    COMMUNITY = "COMMUNITY"
    FAMILY = "FAMILY"


class PrimaryGoal(str, Enum):
    """The single most important business goal for this project.

    The user picks one. The product layer translates it into a Goal_ID
    from the Goal Library so the rest of the pipeline stays in
    canonical terms.
    """

    INCREASE_VISITORS = "INCREASE_VISITORS"
    IMPROVE_ENROLLMENT = "IMPROVE_ENROLLMENT"
    IMPROVE_BRANDING = "IMPROVE_BRANDING"
    BETTER_EXPERIENCE = "BETTER_EXPERIENCE"
    SPACE_OPTIMIZATION = "SPACE_OPTIMIZATION"


# Map PrimaryGoal -> Goal Library stable ID. Centralised here so the
# workflow layer never has to know about user-facing labels.
PRIMARY_GOAL_TO_GOAL_ID: dict[PrimaryGoal, str] = {
    PrimaryGoal.INCREASE_VISITORS: "BUSINESS.TRAFFIC",
    PrimaryGoal.IMPROVE_ENROLLMENT: "EDU.ENROLLMENT",
    PrimaryGoal.IMPROVE_BRANDING: "BUSINESS.BRAND",
    PrimaryGoal.BETTER_EXPERIENCE: "CHILD.PLAY_VALUE",
    PrimaryGoal.SPACE_OPTIMIZATION: "BUSINESS.REVENUE",
}

# Map ProjectType -> Goal Library Domain_Affinity tag. The Decision Maker
# Agent normally infers this from site_type, but the user-supplied
# project type is treated as authoritative.
PROJECT_TYPE_TO_DOMAIN: dict[ProjectType, str] = {
    ProjectType.KINDERGARTEN: "EDUCATION",
    ProjectType.PUBLIC_PARK: "PUBLIC_PARK",
    ProjectType.COMMERCIAL_SPACE: "COMMERCIAL",
    ProjectType.COMMUNITY: "COMMUNITY",
    ProjectType.FAMILY: "RESIDENTIAL",
}

# Human-readable description for each ProjectType, surfaced in reports.
PROJECT_TYPE_DESCRIPTION: dict[ProjectType, str] = {
    ProjectType.KINDERGARTEN: "\u5e7c\u513f\u56ed / \u65e9\u6559\u673a\u6784\u3002\u5728\u610f\u5b89\u5168\u3001\u53d1\u5c55\u3001\u62db\u751f\u3001\u5bb6\u957f\u4fe1\u4efb\u3002",
    ProjectType.PUBLIC_PARK: "\u516c\u5171\u516c\u56ed / \u8857\u533a\u3002\u5728\u610f\u793e\u533a\u6d3b\u8dc3\u3001\u5305\u5bb9\u3001\u591a\u4ee3\u9645\u4f7f\u7528\u3002",
    ProjectType.COMMERCIAL_SPACE: "\u5546\u4e1a\u7efc\u5408\u4f53 / \u54c1\u724c\u7a7a\u95f4\u3002\u5728\u610f\u5ba2\u6d41\u3001\u54c1\u724c\u8bb0\u5fc6\u3001\u62cd\u7167\u5206\u4eab\u3002",
    ProjectType.COMMUNITY: "\u793e\u533a\u516c\u5171\u7a7a\u95f4\u3002\u5728\u610f\u4eb2\u5b50\u4e92\u52a8\u3001\u4f4f\u6c11\u6d3b\u8dc3\u3002",
    ProjectType.FAMILY: "\u5bb6\u5ead\u4f7f\u7528\u573a\u666f\u3002\u5728\u610f\u8212\u9002\u3001\u91cd\u590d\u5230\u8bbf\u3001\u4eb2\u5b50\u8d28\u91cf\u65f6\u95f4\u3002",
}


@dataclass
class ProductRequest:
    """One product-layer run.

    Required:
      * ``image_path`` -- absolute or repo-relative path to a site photo.
      * ``project_type`` -- which kind of project this is.
      * ``primary_goal`` -- the single most important goal.

    Optional:
      * ``site_name`` -- a friendly label printed in the report.
      * ``extra_constraints`` -- free-form constraints (budget tier,
        climate, area, ...). Surfaced in the report and respected by
        future Budget / Safety agents.
    """

    image_path: str
    project_type: ProjectType
    primary_goal: PrimaryGoal
    site_name: str = ""
    extra_constraints: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Coerce image_path to a real Path so downstream code never has
        # to deal with relative strings.
        p = Path(self.image_path)
        if not p.is_absolute():
            # Caller may pass a path relative to the repo root.
            # Resolve it later, at execution time, against repo_root.
            # Here we only validate it is non-empty.
            if not self.image_path:
                raise ValueError("image_path must be non-empty")
        else:
            self.image_path = str(p)

    # ----- helpers -----

    @property
    def domain(self) -> str:
        return PROJECT_TYPE_TO_DOMAIN[self.project_type]

    @property
    def primary_goal_id(self) -> str:
        return PRIMARY_GOAL_TO_GOAL_ID[self.primary_goal]

    @property
    def project_description(self) -> str:
        return PROJECT_TYPE_DESCRIPTION[self.project_type]


__all__ = [
    "PRIMARY_GOAL_TO_GOAL_ID",
    "PROJECT_TYPE_DESCRIPTION",
    "PROJECT_TYPE_TO_DOMAIN",
    "PrimaryGoal",
    "ProductRequest",
    "ProjectType",
]