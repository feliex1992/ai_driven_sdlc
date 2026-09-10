r"""
Agent runner with skill-based execution for the AI Software Factory.

This module provides the agent execution interface that the CLI's ``run.py``
depends on. Today, real skill implementations exist for the analyst stage
and stubs remain for the rest. When Steps 4-11 land, each stub is replaced
with a real skill that calls the LLM, validates its output against the
corresponding schema, and returns evidence.

Design:
  - ``AgentKind``: enum of all SDLC roles (shared via ``shared.py``)
  - ``AgentRunner``: holds project context, exposes ``run(kind, stage, workflow)``
  - ``invoke_agent``: convenience wrapper used by ``run.py``
  - ``SkillRegistry``: maps ``AgentKind`` -> ``BaseSkill``
  - ``DeepSeekClient``: abstraction over the DeepSeek API
  - Stub agents return completed status noting they are stubs.
  - Real skills call DeepSeek, validate against schema, write artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..shared import AgentKind
from ..deepseek import DeepSeekClient
from ..skills import BaseSkill, SkillRegistry, AnalystSkill
from ..context_assembler import build_context

# ---------------------------------------------------------------------------
# AgentRunner
# ---------------------------------------------------------------------------


class AgentRunner:
    """Holds project context and dispatches agent runs via skills.

    Uses ``SkillRegistry`` to look up the skill for each ``AgentKind``.
    If no skill is registered, returns a stub result.

    When a ``DeepSeekClient`` is attached, skills that need it will call
    the API. Otherwise skills may fall back to stub behaviour or raise.
    """

    def __init__(self, project_root: Path, client: DeepSeekClient | None = None) -> None:
        self.project_root = project_root.resolve()
        self.client = client or self._create_client_from_env()
        self.registry = SkillRegistry()
        self._seed_skills()

    def _create_client_from_env(self) -> DeepSeekClient:
        """Create a DeepSeekClient from .env in the project root."""
        return DeepSeekClient(project_root=self.project_root)

    def _seed_skills(self) -> None:
        """Register built-in skills. Extend here as new skills land."""
        if self.client is None:
            # Without a client, we can still register skills but they won't
            # be able to call DeepSeek. For now, only register the analyst
            # when a client is available so that run.py still works without
            # API key configured.
            return
        self.registry.register(AgentKind.ANALYST, AnalystSkill(self.client))

    def run(
        self,
        kind: AgentKind,
        stage: str,
        workflow: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run the skill for the given stage.

        Returns a contract-shaped dict.
        """
        skill = self.registry.get_skill(kind)
        if skill is None:
            return {
                "status": "blocked",
                "summary": f"No skill implementation for {kind.value}",
                "requires_human_approval": False,
                "artifacts": [],
                "findings": [
                    {
                        "severity": "info",
                        "title": "No skill",
                        "description": f"Agent kind {kind.value} has no registered skill",
                    }
                ],
            }

        # Build context package for the skill.
        ctx_package = build_context(self.project_root)
        ctx_package["workflow"] = {
            "feature": getattr(workflow, "feature", None),
            "requirement": getattr(workflow, "requirement", None),
            "workflow_id": getattr(workflow, "workflow_id", None),
            "status": getattr(workflow, "status", None),
            "current_stage": getattr(workflow, "current_stage", None),
        }

        return skill.execute(ctx_package)


# ---------------------------------------------------------------------------
# Stub agents (kept for fallback when no skill is registered)
# ---------------------------------------------------------------------------


class StubAgent:
    """Base stub — returned when no skill is registered for a kind."""

    def __init__(self, project_root: Path, workflow: Any, stage: str, **kwargs: Any) -> None:
        self.project_root = project_root
        self.workflow = workflow
        self.stage = stage

    def run(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "summary": f"{self.stage} stage — skill not yet implemented",
            "output_path": None,
            "requires_human_approval": False,
            "artifacts": [],
            "findings": [],
        }


def invoke_agent(
    runner: AgentRunner,
    kind: AgentKind,
    stage: str,
    workflow: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run an agent for a stage. Thin wrapper around ``AgentRunner.run()``."""
    return runner.run(kind, stage, workflow, **kwargs)
