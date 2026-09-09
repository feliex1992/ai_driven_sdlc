"""
Agent runner stubs for the AI Software Factory.

This module provides the agent execution interface that the CLI's `run.py`
depends on. Today, every agent is a stub — it returns a structured result
matching the STEP 1.5 JSON contracts but does not invoke an LLM.

When Steps 4-11 land, each stub is replaced with a real agent implementation
that calls the LLM, validates its output against the corresponding schema,
and returns evidence.

Design:
  - AgentKind: enum of all SDLC roles
  - AgentRunner: holds project context, exposes run(kind, stage, workflow)
  - invoke_agent: convenience wrapper used by run.py
  - Stub agents return completed status with a summary noting they are stubs.
    No real work is done — the goal is to prove the CLI pipeline works.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# AgentKind
# ---------------------------------------------------------------------------


class AgentKind(Enum):
    """Every SDLC role that the factory can dispatch."""

    ANALYST = "analyst"
    ARCHITECT = "architect"
    PLANNER = "planner"
    DEVELOPER = "developer"
    TESTER = "tester"
    SECURITY = "security"
    REVIEWER = "reviewer"
    DEPLOYER = "deployer"


# ---------------------------------------------------------------------------
# AgentRunner
# ---------------------------------------------------------------------------


class AgentRunner:
    """Holds project context and dispatches agent runs.

    Today every run is a stub. When real agents land (Steps 4-11), each
    kind gets its own implementation and this class delegates to it.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self._stub_agents: dict[AgentKind, type[StubAgent]] = {
            AgentKind.ANALYST:   StubAnalyst,
            AgentKind.ARCHITECT: StubArchitect,
            AgentKind.PLANNER:   StubPlanner,
            AgentKind.DEVELOPER: StubDeveloper,
            AgentKind.TESTER:    StubTester,
            AgentKind.SECURITY:  StubSecurity,
            AgentKind.REVIEWER:  StubReviewer,
            AgentKind.DEPLOYER:  StubDeployer,
        }

    def run(self, kind: AgentKind, stage: str, workflow: Any, **kwargs: Any) -> dict[str, Any]:
        """Run the agent for the given stage. Returns a contract-shaped dict."""
        agent_cls = self._stub_agents.get(kind)
        if agent_cls is None:
            return {
                "status": "blocked",
                "summary": f"No agent implementation for {kind.value}",
                "requires_human_approval": False,
                "artifacts": [],
                "findings": [{"severity": "info", "title": "No agent", "description": f"Agent kind {kind.value} has no implementation"}],
            }
        agent = agent_cls(self.project_root, workflow, stage, **kwargs)
        return agent.run()


# ---------------------------------------------------------------------------
# Stub agents
# ---------------------------------------------------------------------------


class StubAgent:
    """Base stub — every real agent will subclass this and override run()."""

    def __init__(self, project_root: Path, workflow: Any, stage: str, **kwargs: Any) -> None:
        self.project_root = project_root
        self.workflow = workflow
        self.stage = stage

    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": f"{self.stage} stage — stub ran, no real work done",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


class StubAnalyst(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Analysis stage (stub): requirement received, no ambiguity found, ready for architecture",
            "output_path": str(self.project_root / ".ai" / "reports" / "analysis-stub.json"),
            "requires_human_approval": False,
            "artifacts": [{"path": ".ai/reports/analysis-stub.json", "type": "document"}],
            "findings": [],
        }


class StubArchitect(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Architecture stage (stub): clean architecture proposed, no major decisions needed",
            "output_path": str(self.project_root / ".ai" / "reports" / "design-stub.json"),
            "requires_human_approval": False,
            "artifacts": [{"path": ".ai/reports/design-stub.json", "type": "document"}],
            "findings": [],
        }


class StubPlanner(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Planning stage (stub): 3 tasks planned, no dependencies blocking",
            "output_path": str(self.project_root / ".ai" / "reports" / "plan-stub.json"),
            "requires_human_approval": False,
            "artifacts": [{"path": ".ai/reports/plan-stub.json", "type": "document"}],
            "findings": [],
        }


class StubDeveloper(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Development stage (stub): code generation not implemented yet",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


class StubTester(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Testing stage (stub): no tests run, implementation not yet available",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


class StubSecurity(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Security stage (stub): no scans run, pipeline not ready",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


class StubReviewer(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Review stage (stub): no diff to review",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


class StubDeployer(StubAgent):
    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": "Deployment stage (stub): no deployment target configured",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


# ---------------------------------------------------------------------------
# invoke_agent — convenience wrapper used by run.py
# ---------------------------------------------------------------------------


def invoke_agent(
    runner: AgentRunner,
    kind: AgentKind,
    stage: str,
    workflow: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run an agent for a stage. Thin wrapper around AgentRunner.run()."""
    return runner.run(kind, stage, workflow, **kwargs)
