"""
Skill registry for SDLC agents.

Central registry that maps AgentKind -> Skill instance.
Provides lookup, list, and dispatch helpers.
"""

from __future__ import annotations

from typing import Any

from ..shared import AgentKind
from ..deepseek import DeepSeekClient
from .base import BaseSkill


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class SkillRegistry:
    """Registry mapping AgentKind to BaseSkill instances.

    Usage::

        registry = SkillRegistry()
        registry.register(AgentKind.ANALYST, AnalystSkill(client))
        skill = registry.get_skill(AgentKind.ANALYST)
        result = skill.execute(context)
    """

    def __init__(self) -> None:
        self._skills: dict[AgentKind, BaseSkill] = {}

    def register(self, kind: AgentKind, skill: BaseSkill) -> None:
        """Register a skill for a given AgentKind."""
        self._skills[kind] = skill

    def get_skill(self, kind: AgentKind) -> BaseSkill | None:
        """Get the skill registered for a given AgentKind, or None."""
        return self._skills.get(kind)

    def list_skills(self) -> list[tuple[AgentKind, BaseSkill]]:
        """Return all registered skills as (AgentKind, BaseSkill) pairs."""
        return list(self._skills.items())

    def has_skill(self, kind: AgentKind) -> bool:
        """Return True if a skill is registered for the given kind."""
        return kind in self._skills

    def execute(
        self,
        kind: AgentKind,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Convenience: get skill for kind and execute with context.

        Returns the contract-shaped result dict.
        If no skill is registered, returns a blocked result.
        """
        skill = self._skills.get(kind)
        if skill is None:
            return {
                "status": "blocked",
                "summary": f"No skill registered for {kind.value}",
                "output_path": None,
                "artifacts": [],
                "findings": [
                    {
                        "severity": "error",
                        "title": "No skill",
                        "description": f"No skill registered for {kind.value}",
                    }
                ],
                "requires_human_approval": False,
            }
        return skill.execute(context)
