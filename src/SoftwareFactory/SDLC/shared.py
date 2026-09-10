"""
Shared types for the SDLC layer.

This module contains types used by multiple SDLC subpackages (Agents,
skills, workflow, etc) to avoid circular imports.
"""

from __future__ import annotations

from enum import Enum


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
