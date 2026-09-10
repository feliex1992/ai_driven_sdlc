"""
DeepSeek client abstraction for the AI Software Factory.

Provides a thin wrapper around the DeepSeek API that skill implementations
can use without knowing API specifics. Configuration is read from environment
variables and .env files; no secrets are hardcoded or written to disk.

Configuration priority (highest to lowest):
1. Explicit arguments passed to DeepSeekClient()
2. Values from .env file in project root
3. System environment variables (DEEPSEEK_API_KEY, etc.)
4. Built-in defaults

Usage::

    client = DeepSeekClient()
    text = client.chat([...messages...], temperature=0.7)
    structured = client.chat_structured([...messages...], schema)
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import resolve_config

try:
    import certifi
    _CA_CERTS = certifi.where()
except ImportError:
    _CA_CERTS = None

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class DeepSeekClient:
    """Wrapper around the DeepSeek chat completions API.

    Configuration is resolved in this order:
    1. Arguments passed to the constructor (api_key, model, base_url)
    2. Variables from .env file in the project root (if project_root given)
    3. Environment variables (DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL)
    4. Built-in defaults for model and base_url

    If api_key is not resolved from any source, the constructor raises RuntimeError.
    """

    api_key: str
    model: str
    base_url: str

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        project_root: Path | str | None = None,
    ) -> None:
        # Build explicit dict for config resolution.
        explicit: dict[str, str | None] = {}
        if api_key is not None:
            explicit["DEEPSEEK_API_KEY"] = api_key
        if model is not None:
            explicit["DEEPSEEK_MODEL"] = model
        if base_url is not None:
            explicit["DEEPSEEK_BASE_URL"] = base_url

        # Resolve with .env support if project_root is given.
        if project_root is not None:
            resolved = resolve_config(explicit, dotenv_path=Path(project_root) / ".env")
        else:
            resolved = resolve_config(explicit)

        resolved_key = resolved.get("api_key", "")
        if not resolved_key:
            raise RuntimeError(
                "DeepSeek API key is required. Set one of:\n"
                "  - DEEPSEEK_API_KEY environment variable\n"
                "  - .env file in project root (DEEPSEEK_API_KEY=...)\n"
                "  - api_key= argument to DeepSeekClient()"
            )
        self.api_key = resolved_key
        self.model = resolved.get("model") or DEFAULT_MODEL
        self.base_url = resolved.get("base_url") or DEFAULT_BASE_URL

    # -- chat ----------------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completions request and return the assistant text."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        # Use certifi CA bundle if available (fixes macOS SSL issues).
        if _CA_CERTS:
            ctx = ssl.create_default_context(cafile=_CA_CERTS)
            https_handler = urllib.request.HTTPSHandler(context=ctx)
            opener = urllib.request.build_opener(https_handler)
            try:
                with opener.open(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                raise RuntimeError(
                    f"DeepSeek API error {exc.code}: {exc.reason}"
                ) from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"DeepSeek request failed: {exc.reason}") from exc
        else:
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                raise RuntimeError(
                    f"DeepSeek API error {exc.code}: {exc.reason}"
                ) from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"DeepSeek request failed: {exc.reason}") from exc

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"DeepSeek returned no choices. Response: {data}")
        message = choices[0].get("message", {})
        text = message.get("content", "")
        if not text:
            raise RuntimeError("DeepSeek returned empty content.")
        return text

    # -- structured ---------------------------------------------------------

    def chat_structured(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Chat with a schema hint, then parse+return the result.

        DeepSeek does not guarantee structured JSON output, so this helper
        sends the schema as part of the system prompt, then parses the reply
        and raises on invalid JSON. Callers (validator layer) should still
        validate the result against the real JSON Schema.
        """
        schema_text = json.dumps(schema, indent=2)
        system = (
            "You are a deterministic assistant. Respond ONLY with valid JSON "
            "that matches the schema below. Do not include markdown fences, "
            "explanations, or any text outside the JSON object.\n\n"
            f"Schema:\n{schema_text}"
        )
        messages = [{"role": "system", "content": system}] + messages

        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        text = text.strip()

        # Strip markdown code fences if the model added them anyway.
        text = _strip_code_fences(text)

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "DeepSeek did not return valid JSON. Raw reply:\n" + text
            ) from exc
        if not isinstance(result, dict):
            raise RuntimeError(
                "DeepSeek returned a JSON array or primitive, expected object. "
                f"Raw reply:\n{text}"
            )
        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences if present."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        while lines and lines[0].strip().startswith("```"):
            lines.pop(0)
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        t = "\n".join(lines).strip()
    return t
