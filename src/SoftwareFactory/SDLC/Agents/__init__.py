"""
SDLC Agents package.

Contains agent runner infrastructure and, later, real agent implementations.
Today only stubs exist — the runner returns structured results without
invoking an LLM. When Steps 4-11 land, each stub is replaced with a
real agent.
"""

from .runner import AgentRunner, invoke_agent

__all__ = ["AgentRunner", "invoke_agent"]

# AgentKind is defined in the shared SDLC layer, not in Agents/.
# Import it from the shared location to avoid circular imports.
from ..shared import AgentKind

__all__.insert(0, "AgentKind")
