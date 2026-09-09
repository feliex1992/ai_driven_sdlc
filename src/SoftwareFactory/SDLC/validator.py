"""
Validator for SDLC agent contract output.

Validates agent output against the corresponding JSON Schema and returns
(success, parsed_result_or_error_message).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JSValidationError


def validate_contract(
    result: dict[str, Any],
    schema_path: str | Path,
) -> tuple[bool, dict[str, Any] | str]:
    """Validate an agent result against a JSON Schema.

    Args:
        result: The output dict from the agent.
        schema_path: Path to the JSON Schema file.

    Returns:
        (True, parsed_result) if valid.
        (False, error_message) if invalid.
    """
    schema_file = Path(schema_path)
    if not schema_file.is_file():
        return False, f"Schema file not found: {schema_file}"

    schema = json.loads(schema_file.read_text())
    try:
        jsonschema_validate(instance=result, schema=schema)
        return True, result
    except JSValidationError as exc:
        return False, f"Schema validation failed: {exc.message}"
