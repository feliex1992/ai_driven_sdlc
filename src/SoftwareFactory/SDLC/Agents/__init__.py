"""
SDLC Agents package.

Contains agent runner infrastructure and, later, real agent implementations.
Today only stubs exist — the runner returns structured results without
invoking an LLM. When Steps 4-11 land, each stub is replaced with a
real agent.
"""

from .runner import AgentKind, AgentRunner, invoke_agent

__all__ = ["AgentKind", "AgentRunner", "invoke_agent"]
