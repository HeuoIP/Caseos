"""High-level facade for the CaseOS Product Layer.

``ProductFlow`` is what the future Web UI / CLI / script calls. It
owns:

  * the Vision Analyzer (one provider, swappable for tests),
  * the Knowledge Base (lazy-loaded),
  * the Decision Engine,
  * the Workflow orchestrator.

The single public method is ``run(request) -> ProductResponse``.
A second method ``run_session(session) -> ProductSession`` is
exposed for callers that want the full session object (useful for
the future async UI that polls status).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.decision.engine import DecisionEngine
from app.core.decision.knowledge import KnowledgeBase
from app.core.product.request import ProductRequest
from app.core.product.response import ProductResponse
from app.core.product.session import ProductSession, SessionStatus
from app.core.product.workflow import ProductWorkflow, WorkflowConfig
from app.services.vision.factory import build_vision_analyzer


class ProductFlowError(RuntimeError):
    """Raised by ``ProductFlow.run`` when a session ends in FAILED."""


class ProductFlow:
    """End-to-end product workflow.

    Construct once, call ``run(request)`` many times.
    """

    def __init__(
        self,
        *,
        vision_analyzer=None,
        knowledge: KnowledgeBase | None = None,
        engine: DecisionEngine | None = None,
        repo_root: Path | str | None = None,
        config: WorkflowConfig | None = None,
    ):
        self.repo_root = Path(repo_root) if repo_root is not None else None

        # Default: build the real Qwen-backed analyzer.
        if vision_analyzer is None:
            vision_analyzer = build_vision_analyzer()
        self.vision_analyzer = vision_analyzer

        # Default: lazy-load knowledge base from <repo>/knowledge.
        if knowledge is None:
            if self.repo_root is None:
                # Fall back to the path the vision factory uses.
                self.repo_root = Path(__file__).resolve().parents[4]
            knowledge = KnowledgeBase(self.repo_root / "knowledge")
        self.knowledge = knowledge

        self.engine = engine or DecisionEngine(knowledge=self.knowledge)
        self.workflow = ProductWorkflow(
            vision_analyzer=self.vision_analyzer,
            knowledge=self.knowledge,
            engine=self.engine,
            config=config or WorkflowConfig(),
            repo_root=self.repo_root,
        )

    # ---- public API ----

    def run(self, request: ProductRequest) -> ProductResponse:
        """Run the full product flow synchronously. Raise on failure."""
        session = ProductSession(request=request)
        session = self.workflow.execute(session)
        if session.status == SessionStatus.FAILED:
            raise ProductFlowError(session.error or "unknown failure")
        assert session.response is not None
        return session.response

    def run_session(self, session: ProductSession) -> ProductSession:
        """Run the workflow against a pre-built session (preserving its id)."""
        return self.workflow.execute(session)

    # ---- introspection ----

    def describe(self) -> dict[str, Any]:
        """Return a small summary useful for logs / health endpoints."""
        return {
            "workflow_stages": list(self.workflow.STAGES),
            "vision_analyzer": type(self.vision_analyzer).__name__,
            "knowledge": self.knowledge.summary(),
            "engine_agents": self.engine.agent_names,
        }


__all__ = ["ProductFlow", "ProductFlowError"]