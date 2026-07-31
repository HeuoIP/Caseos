"""Runtime context types for the Brain pipeline.

Two kinds of context:

- `ProjectContext` is the **frozen input** that the pipeline consumes.
  It is built from a `project.json` and does not change while the
  pipeline runs. The class is a frozen dataclass so accidental
  mutation is caught at runtime.

- `PipelineContext` is the **mutable shared state** that flows
  through the six stages. Each stage reads what it needs, writes
  what it produced, and never invents data that another stage
  should own. This is the runtime analogue of the
  `DecisionContext` declared in ADR-005 + Sprint 7.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class ProjectContext:
    """The user-supplied input. Frozen, JSON-serialisable."""

    project_id: str = ""
    project_type: str = ""
    site_description: str = ""
    user_goal: str = ""
    constraints: str = ""
    # Optional passthrough fields (e.g. budget).
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectContext":
        known = {f for f in cls.__dataclass_fields__ if f != "extras"}
        base = {k: v for k, v in data.items() if k in known}
        extras = {k: v for k, v in data.items() if k not in known}
        return cls(extras=extras, **base)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        return out


@dataclass
class PipelineContext:
    """Mutable shared state across the six pipeline stages.

    Each stage adds / reads its own slot:
        - human stage      -> human_context
        - knowledge stage  -> knowledge_patterns
        - decision stage   -> decision_object
        - trust stage      -> trust_object
        - recommendation   -> recommendation
        - output stage     -> (renders the final Markdown)
    """

    project: ProjectContext
    human_context: dict[str, Any] | None = None
    knowledge_patterns: list[dict[str, Any]] = field(default_factory=list)
    decision_object: dict[str, Any] | None = None
    trust_object: dict[str, Any] | None = None
    recommendation: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def stage_log(self, stage: str, status: str = "ok", **detail: Any) -> None:
        """Record a stage tick into metadata (used for debugging + tests)."""
        log = self.metadata.setdefault("stage_log", [])
        entry: dict[str, Any] = {"stage": stage, "status": status}
        entry.update(detail)
        log.append(entry)