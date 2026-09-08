"""
STEP 2.2 — Filesystem Scanner.

Produces project.json: top-level identity of the scanned project.
The project name is taken from the repo root directory name.

This detector is intentionally simple. Downstream detectors add depth;
this one establishes the root path and a human name for the project.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field

from ..Core import ProjectContext
from ..Core.detector import Detector


class FilesystemDetector(Detector):
    """STEP 2.2 — Filesystem Scanner.

    Enumerates the repo tree enough to produce project.json.
    """

    @property
    def block_name(self) -> str:
        return "project"

    def detect(self) -> dict:
        return ProjectContext(
            project_name=self.root.name,
            root_path=str(self.root),
            scanned_at=datetime.now(timezone.utc).isoformat(),
        ).model_dump()
