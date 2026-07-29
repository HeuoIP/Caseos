"""Public exports for the CaseOS Product Layer.

A consumer (future Web UI, CLI, script) only needs to import this
package to get every public type.
"""

from app.core.product.product_flow import ProductFlow, ProductFlowError
from app.core.product.request import (
    PRIMARY_GOAL_TO_GOAL_ID,
    PROJECT_TYPE_DESCRIPTION,
    PROJECT_TYPE_TO_DOMAIN,
    PrimaryGoal,
    ProductRequest,
    ProjectType,
)
from app.core.product.response import DecisionGoalView, ProductResponse
from app.core.product.session import ProductSession, SessionStage, SessionStatus
from app.core.product.workflow import ProductWorkflow, WorkflowConfig

__all__ = [
    "PRIMARY_GOAL_TO_GOAL_ID",
    "PROJECT_TYPE_DESCRIPTION",
    "PROJECT_TYPE_TO_DOMAIN",
    "DecisionGoalView",
    "PrimaryGoal",
    "ProductFlow",
    "ProductFlowError",
    "ProductRequest",
    "ProductResponse",
    "ProductSession",
    "ProductWorkflow",
    "ProjectType",
    "SessionStage",
    "SessionStatus",
    "WorkflowConfig",
]