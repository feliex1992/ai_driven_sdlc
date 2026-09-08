"""
Base detector interface for the Context Engine.

Each detector is a small, focused module that:
  - has a block_name (the key under which its output lands in FullContext)
  - exposes detect() -> dict that is merged into the aggregated context
  - never modifies the target repo (rules: 00-core)

Detectors are registered with ContextEngine.install_detectors().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Detector(ABC):
    """Abstract base for every context detector.

    Subclass this and implement detect(). The ContextEngine calls
    detect() in registration order and aggregates results.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    @property
    @abstractmethod
    def block_name(self) -> str:
        """Key used in the aggregated context dict, e.g. 'language'."""
        ...

    @abstractmethod
    def detect(self) -> dict:
        """Inspect the repository and return a dict of findings.

        The dict is meant to be pydantic-model-friendly:
        bare dicts that match the corresponding *Context model.
        """
        ...
