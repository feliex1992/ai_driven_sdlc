"""
Skill base classes for SDLC agents.

Defines BaseSkill with the interface that all concrete skills share:
- build_prompt(context) -> str
- execute(context) -> dict (contract-shaped result)

Also provides helpers for loading schemas, writing artifacts, and
assembling prompts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JSValidationError

from ..deepseek import DeepSeekClient


# ---------------------------------------------------------------------------
# BaseSkill
# ---------------------------------------------------------------------------


class BaseSkill:
    """Base class for all SDLC agent skills.

    Subclasses must override:
    - name: str
    - stage: str
    - output_schema_path: Path | str
    - build_prompt(context: dict) -> str
    """

    name: str = ""
    stage: str = ""
    output_schema_path: str = ""
    context_fields: list[str] = []

    def __init__(self, client: DeepSeekClient) -> None:
        self.client = client

    # -- public interface ---------------------------------------------------

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the skill: build prompt, call DeepSeek, validate, persist.

        Returns a dict shaped like the STEP 1.5 contract.
        """
        prompt = self.build_prompt(context)
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt(context)},
            {"role": "user", "content": prompt},
        ]

        try:
            raw_result = self.client.chat_structured(
                messages,
                self._load_schema(),
                temperature=0.2,
                max_tokens=8192,
            )
        except Exception as exc:
            return {
                "status": "blocked",
                "summary": f"Skill execution failed: {exc}",
                "output_path": None,
                "artifacts": [],
                "findings": [
                    {
                        "severity": "error",
                        "title": "Skill execution error",
                        "description": str(exc),
                    }
                ],
                "requires_human_approval": False,
            }

        valid, parsed_or_error = self._validate(raw_result)
        if not valid:
            return {
                "status": "blocked",
                "summary": f"Validation failed: {parsed_or_error}",
                "output_path": None,
                "artifacts": [],
                "findings": [
                    {
                        "severity": "error",
                        "title": "Contract validation failed",
                        "description": parsed_or_error,
                    }
                ],
                "requires_human_approval": False,
            }

        artifact_path = self._write_artifact(parsed_or_error, context)
        return {
            "status": "completed",
            "summary": f"{self.name} skill completed: {parsed_or_error.get('summary', '')}",
            "output_path": str(artifact_path),
            "artifacts": [
                {
                    "path": str(artifact_path),
                    "type": "contract",
                    "stage": self.stage,
                }
            ],
            "findings": parsed_or_error.get("findings", []),
            "requires_human_approval": parsed_or_error.get(
                "requires_human_approval", False
            ),
        }

    def build_prompt(self, context: dict[str, Any]) -> str:
        """Build the user-facing prompt for this skill.

        Override in subclasses to produce a stage-specific prompt.
        """
        raise NotImplementedError

    # -- helpers ------------------------------------------------------------

    def _system_prompt(self, context: dict[str, Any]) -> str:
        """Default system prompt — override or extend in subclasses."""
        return (
            "You are a deterministic assistant. Respond ONLY with valid JSON "
            "matching the schema provided in the user message. Do not include "
            "markdown fences, explanations, or any text outside the JSON object."
        )

    def _load_schema(self) -> dict[str, Any]:
        path = Path(self.output_schema_path)
        if not path.is_file():
            raise FileNotFoundError(f"Schema not found: {path}")
        return json.loads(path.read_text())

    def _validate(self, result: dict[str, Any]) -> tuple[bool, str | dict[str, Any]]:
        schema = self._load_schema()
        try:
            jsonschema_validate(instance=result, schema=schema)
            return True, result
        except JSValidationError as exc:
            return False, f"Schema validation failed: {exc.message}"

    def _write_artifact(self, result: dict[str, Any], context: dict[str, Any]) -> Path:
        """Persist the validated result to .ai/reports/<stage>-<ts>.json."""
        project_root = Path(context.get("project_root", ".")) if isinstance(
            context.get("project_root"), str
        ) else None
        if not project_root:
            project_root = Path.cwd()

        reports_dir = project_root / ".ai" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"{self.stage}-{timestamp}.json"
        artifact_path = reports_dir / filename
        artifact_path.write_text(json.dumps(result, indent=2))
        return artifact_path
