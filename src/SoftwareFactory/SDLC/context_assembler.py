"""
Context assembler for SDLC agents.

Gathers project context, rules, and schema into a single structure that
skills consume. The context package is the primary input to skill prompts.

This module reads .ai/context/*.json as plain dicts (not pydantic models),
so it does not depend on the Context Engine's pydantic models at the skill
layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Context package
# ---------------------------------------------------------------------------


def build_context(
    project_root: Path,
    *,
    load_files: bool = True,
) -> dict[str, Any]:
    """Assemble a context package for skills.

    Args:
        project_root: Root directory of the project.
        load_files: If True, load .ai/context/*.json and .ai/rules/*.md.

    Returns:
        A dict with keys:
        - project_root: str
        - workflow: dict (from workflow state, if available)
        - context: dict | None (loaded .ai/context/*.json files keyed by stem)
        - rules: dict[str, str] (rule name -> content)
        - schema: dict (the output schema for the current stage)
    """
    package: dict[str, Any] = {
        "project_root": str(project_root),
        "workflow": {},
        "context": None,
        "rules": {},
        "schema": {},
    }

    if not load_files:
        return package

    # Load context from .ai/context/*.json if present.
    context_dir = project_root / ".ai" / "context"
    if context_dir.is_dir():
        context_files: dict[str, Any] = {}
        for f in sorted(context_dir.glob("*.json")):
            try:
                context_files[f.stem] = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                # Skip files that can't be parsed.
                pass
        if context_files:
            package["context"] = context_files

    # Load rules from .ai/rules/*.md
    rules_dir = project_root / ".ai" / "rules"
    if rules_dir.is_dir():
        for rule_file in sorted(rules_dir.glob("*.md")):
            rule_name = rule_file.stem
            try:
                package["rules"][rule_name] = rule_file.read_text()
            except OSError:
                pass

    return package
