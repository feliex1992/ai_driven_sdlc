"""
Environment configuration loader for the AI Software Factory.

Loads configuration from .env files with the following priority:
1. Explicit env vars passed to the constructor
2. .env file in the project root (or parent directories)
3. System environment variables

The .env file format is simple KEY=VALUE, one per line.
Lines starting with # are comments. Whitespace is stripped.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# .env file loading
# ---------------------------------------------------------------------------


def load_dotenv(dotenv_path: Path | str | None = None) -> dict[str, str]:
    """Load a .env file and return its variables as a dict.

    If dotenv_path is a directory, looks for .env inside it.
    If dotenv_path is None, searches upward from CWD for .env.

    Lines starting with # are comments. Blank lines are skipped.
    KEY=VALUE format, whitespace stripped from both sides.
    No variable expansion is performed.
    """
    path = _resolve_dotenv_path(dotenv_path)
    if path is None or not path.is_file():
        return {}

    variables: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key:
            variables[key] = value
    return variables


def _resolve_dotenv_path(dotenv_path: Path | str | None) -> Path | None:
    """Resolve the .env file path to use."""
    if dotenv_path is None:
        # Search upward from cwd for .env
        candidate = Path.cwd()
        for p in [candidate] + list(candidate.parents):
            env_file = p / ".env"
            if env_file.is_file():
                return env_file
        return None

    path = Path(dotenv_path)
    if path.is_dir():
        return path / ".env"
    return path


# ---------------------------------------------------------------------------
# Integration with DeepSeekClient
# ---------------------------------------------------------------------------

_ENV_KEYS = {
    "DEEPSEEK_API_KEY": "api_key",
    "DEEPSEEK_MODEL": "model",
    "DEEPSEEK_BASE_URL": "base_url",
}


def resolve_config(
    explicit: dict[str, str | None] | None = None,
    dotenv_path: Path | str | None = None,
) -> dict[str, str]:
    """Resolve DeepSeek configuration with .env support.

    Priority (highest to lowest):
    1. Explicit values passed in the ``explicit`` dict
    2. Values from .env file
    3. System environment variables
    4. Defaults (handled by the caller)

    Args:
        explicit: Dict of explicit overrides, e.g. {"api_key": "xxx"}.
        dotenv_path: Path to .env file, or directory containing .env.

    Returns:
        Dict with resolved values for api_key, model, base_url.
    """
    explicit = explicit or {}
    env_vars = load_dotenv(dotenv_path)
    result: dict[str, str] = {}

    for env_key, attr_name in _ENV_KEYS.items():
        # 1. Explicit override
        if env_key in explicit and explicit[env_key]:
            result[attr_name] = str(explicit[env_key])
            continue

        # 2. .env file
        if env_key in env_vars:
            result[attr_name] = env_vars[env_key]
            continue

        # 3. System environment variable
        sys_val = os.environ.get(env_key)
        if sys_val:
            result[attr_name] = sys_val
            continue

        # 4. Not found — leave out; caller handles defaults
        result[attr_name] = ""

    return result


# ---------------------------------------------------------------------------
# Convenience: load .env relative to a project root
# ---------------------------------------------------------------------------


def load_env_for_project(project_root: Path | str) -> dict[str, str]:
    """Load .env from the given project root directory.

    Convenience wrapper around ``resolve_config`` that searches for .env
    in the project root.
    """
    return resolve_config(dotenv_path=Path(project_root) / ".env")
