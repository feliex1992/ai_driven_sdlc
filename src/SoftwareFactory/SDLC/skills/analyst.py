"""
Analyst skill for the AI Software Factory (STEP 4).

Transforms a user requirement into a structured analysis following the
analysis.schema.json contract: business requirements, rules, actors,
constraints, assumptions, acceptance criteria, and findings.
"""

from __future__ import annotations

from typing import Any

from ..deepseek import DeepSeekClient
from .base import BaseSkill


class AnalystSkill(BaseSkill):
    """Business Analyst skill: requirement -> analysis.json."""

    name: str = "analyst"
    stage: str = "analysis"
    output_schema_path: str = ".ai/schemas/analysis.schema.json"
    context_fields: list[str] = ["requirement", "workflow", "context", "rules"]

    def __init__(self, client: DeepSeekClient) -> None:
        super().__init__(client)

    def build_prompt(self, context: dict[str, Any]) -> str:
        requirement = context.get("requirement") or context.get("workflow", {}).get("requirement", "")
        workflow = context.get("workflow", {})
        feature = workflow.get("feature", "") or context.get("feature", "")

        bits: list[str] = [
            "# Business Analyst — Requirement Analysis\n",
            f"**Feature:** {feature or 'N/A'}\n",
            f"**Requirement:** {requirement or 'N/A'}\n",
            "\n## Your task\n",
            "Analyze the requirement above and produce a structured analysis "
            "with the following sections:\n",
            "- Business requirements (list with id, description, priority)\n",
            "- Business rules\n",
            "- Actors\n",
            "- Constraints\n",
            "- Assumptions\n",
            "- Acceptance criteria\n",
            "- Findings (ambiguities, risks, questions)\n",
            "\n## Rules\n",
            "1. Do NOT invent requirements, APIs, database tables, or external "
            "services. Only analyse what is stated.\n",
            "2. If information is missing, state assumptions clearly in the "
            "assumptions section.\n",
            "3. Identify ambiguities as findings and list explicit clarification "
            "questions.\n",
            "4. Every significant requirement must have a unique ID in the form "
            "REQ-<number>.\n",
            "\n## Output\n",
            "Return ONLY a valid JSON object matching the analysis schema. "
            "No markdown, no explanations outside the JSON.\n",
        ]
        return "\n".join(bits)
