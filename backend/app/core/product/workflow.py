"""Workflow orchestrator for the CaseOS Product Layer.

The workflow turns a ``ProductSession`` into a completed
``ProductResponse`` by walking five stages in the order the user
specified:

    1. vision        -- call VisionAnalyzer.analyze(image_path)
    2. selections    -- apply user-supplied project_type + primary_goal
    3. engine        -- run the DecisionEngine (with overrides)
    4. report        -- render the Markdown report
    5. images        -- reserved for future design-image generation

Every stage writes its own ``SessionStage`` so the future Web UI can
show progress. A failure in any stage marks the session FAILED but
does not silently abort; the caller gets back the session object with
``error`` populated.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.decision.context import DecisionContext
from app.core.decision.engine import DecisionEngine
from app.core.decision.knowledge import KnowledgeBase
from app.core.decision.models import GoalRef
from app.core.product.request import ProductRequest
from app.core.product.response import DecisionGoalView, ProductResponse
from app.core.product.session import ProductSession, SessionStatus
from app.core.recommendation.markdown_generator import render_markdown
from app.services.vision.analyzer import VisionAnalyzer


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class WorkflowConfig:
    """Optional knobs that callers can pass to ``ProductWorkflow``."""

    site_name_override: str = ""
    extra_constraints: dict[str, Any] = field(default_factory=dict)


class ProductWorkflow:
    """Run the five product stages against one ``ProductSession``."""

    STAGES: list[str] = [
        "vision",
        "selections",
        "engine",
        "report",
        "images",  # reserved; always skipped in V1
    ]

    def __init__(
        self,
        vision_analyzer: VisionAnalyzer,
        knowledge: KnowledgeBase,
        engine: DecisionEngine | None = None,
        config: WorkflowConfig | None = None,
        repo_root: Path | None = None,
    ):
        self.vision_analyzer = vision_analyzer
        self.knowledge = knowledge
        self.engine = engine or DecisionEngine(knowledge=knowledge)
        self.config = config or WorkflowConfig()
        self.repo_root = repo_root

    # ----- main entry -----

    def execute(self, session: ProductSession) -> ProductSession:
        """Walk all stages, mutating ``session`` in place."""
        session.status = SessionStatus.RUNNING
        try:
            vision_json = self._stage_vision(session)
            context = self._stage_selections(session, vision_json)
            context = self._stage_engine(session, context)
            markdown = self._stage_report(session, context)
            self._stage_images(session)
            session.response = self._build_response(
                session=session, context=context, markdown=markdown
            )
            session.status = SessionStatus.COMPLETED
        except Exception as exc:
            session.status = SessionStatus.FAILED
            session.error = f"{type(exc).__name__}: {exc}"
            session.response = None
        finally:
            session.updated_at = _now_iso()
        return session

    # ----- stages -----

    def _stage_vision(self, session: ProductSession) -> dict[str, Any]:
        stage = session.start_stage("vision")
        try:
            image_path = self._resolve_image_path(session.request)
            t0 = time.perf_counter()
            vision_json = self.vision_analyzer.analyze(image_path)
            elapsed = round(time.perf_counter() - t0, 4)
            if not isinstance(vision_json, dict):
                raise TypeError(
                    f"VisionAnalyzer returned {type(vision_json).__name__}; expected dict"
                )
            stage.extra["image_path"] = str(image_path)
            stage.extra["duration_sec"] = elapsed
            stage.extra["keys"] = sorted(vision_json.keys())
            session.finish_stage(stage, "ok", note=f"{elapsed}s")
            return vision_json
        except Exception as exc:
            session.finish_stage(stage, "error", note=str(exc))
            raise

    def _stage_selections(
        self, session: ProductSession, vision_json: dict[str, Any]
    ) -> DecisionContext:
        """Pre-seed a DecisionContext with the user's project_type + primary_goal.

        Returns the context. The user's primary_goal is prepended so the
        engine's Decision Maker Agent sees it before inferring others.
        """
        stage = session.start_stage("selections")
        context = DecisionContext(vision_json=vision_json)
        try:
            req: ProductRequest = session.request
            context.add_metadata("user_project_type", req.project_type.value)
            context.add_metadata("user_domain", req.domain)

            primary_goal_id = req.primary_goal_id
            primary_goal_entry = self.knowledge.goal(primary_goal_id)
            if primary_goal_entry is None:
                stage.note = f"PrimaryGoal {primary_goal_id!r} not in library; skipped injection"
                session.finish_stage(stage, "ok", note=stage.note)
                return context

            user_goal = GoalRef(
                goal_id=primary_goal_entry.goal_id,
                name=primary_goal_entry.name,
                name_en=primary_goal_entry.name_en,
                priority=primary_goal_entry.priority,
                confidence=1.0,
                rationale=f"User-selected primary goal: {req.primary_goal.value}.",
                domain_affinity=list(primary_goal_entry.domain_affinity),
                conflicts_with=list(primary_goal_entry.conflicts_with),
            )
            context.goals = [user_goal]
            stage.extra["primary_goal_id"] = primary_goal_id
            stage.extra["project_domain"] = req.domain
            session.finish_stage(stage, "ok")
            return context
        except Exception as exc:
            session.finish_stage(stage, "error", note=str(exc))
            raise

    def _stage_engine(
        self, session: ProductSession, context: DecisionContext
    ) -> DecisionContext:
        stage = session.start_stage("engine")
        try:
            t0 = time.perf_counter()
            context = self.engine.run(context.vision_json, context=context)
            elapsed = round(time.perf_counter() - t0, 4)
            stage.extra["duration_sec"] = elapsed
            stage.extra["agent_names"] = context.metadata.get("pipeline", [])
            session.finish_stage(stage, "ok", note=f"{elapsed}s")
            return context
        except Exception as exc:
            session.finish_stage(stage, "error", note=str(exc))
            raise

    def _stage_report(
        self, session: ProductSession, context: DecisionContext
    ) -> str:
        stage = session.start_stage("report")
        try:
            t0 = time.perf_counter()
            markdown = render_markdown(context)
            elapsed = round(time.perf_counter() - t0, 4)
            stage.extra["length"] = len(markdown)
            stage.extra["duration_sec"] = elapsed
            session.finish_stage(stage, "ok", note=f"{len(markdown)} chars")
            return markdown
        except Exception as exc:
            session.finish_stage(stage, "error", note=str(exc))
            raise

    def _stage_images(self, session: ProductSession) -> None:
        """Reserved for future design-image generation."""
        stage = session.start_stage("images")
        stage.note = "skipped (not implemented in Sprint 8)"
        session.finish_stage(stage, "skipped")

    # ----- helpers -----

    def _resolve_image_path(self, req: ProductRequest) -> str:
        p = Path(req.image_path)
        if p.is_absolute():
            return str(p)
        if self.repo_root is None:
            return str(p)
        return str((self.repo_root / req.image_path).resolve())

    def _build_response(
        self,
        *,
        session: ProductSession,
        context: DecisionContext,
        markdown: str,
    ) -> ProductResponse:
        req = session.request
        dm = context.decision_maker
        primary_goal_label = req.primary_goal.value.replace("_", " ").title()
        extra_goals = [g for g in context.goals if g.confidence < 1.0]
        decision_goal = DecisionGoalView(
            project_type=req.project_type.value,
            project_description=req.project_description,
            primary_goal_label=primary_goal_label,
            primary_goal_id=req.primary_goal_id,
            inferred_profile=dm.profile if dm else "",
            profile_description=dm.description if dm else "",
            extra_goals=extra_goals,
        )
        return ProductResponse(
            space_summary=context.space_summary,
            decision_goal=decision_goal,
            strategies=list(context.strategies),
            recommended_objects=list(context.top_recommendations),
            explanations=list(context.explanations),
            markdown_report=markdown,
            decision_maker=dm,
            all_goals=list(context.goals),
            stages=[s.to_summary() if hasattr(s, "to_summary") else {} for s in session.stages],
            metadata=dict(context.metadata),
        )


__all__ = ["ProductWorkflow", "WorkflowConfig"]