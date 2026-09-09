"""
SDLC Workflow Engine — STEP 3 core.

Manages workflow state, stage transitions, and persistence to
.ai/workflow/state.json for the AI Software Factory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------

STAGES = [
    "analysis",
    "architecture",
    "planning",
    "development",
    "testing",
    "security",
    "review",
    "deployment",
]

STAGE_LABELS: dict[str, str] = {
    "analysis":     "Analysis",
    "architecture": "Architecture",
    "planning":     "Planning",
    "development":  "Development",
    "testing":      "Testing",
    "security":     "Security",
    "review":       "Code Review",
    "deployment":   "Deployment",
}

STAGE_AGENT: dict[str, Optional[str]] = {
    "analysis":     "analyst",
    "architecture": "architect",
    "planning":     "planner",
    "development":  "developer",
    "testing":      "tester",
    "security":     "security",
    "review":       "reviewer",
    "deployment":   "deployer",
}

# ---------------------------------------------------------------------------
# Stage state
# ---------------------------------------------------------------------------


@dataclass
class StageState:
    """Status of a single SDLC stage within a workflow."""

    status: str = "pending"  # pending | in_progress | completed | blocked
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    note: str = ""
    output_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "note": self.note,
            "output_path": self.output_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageState":
        return cls(
            status=data.get("status", "pending"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            note=data.get("note", ""),
            output_path=data.get("output_path"),
        )


# ---------------------------------------------------------------------------
# Workflow state
# ---------------------------------------------------------------------------


@dataclass
class Workflow:
    """A single SDLC workflow — e.g. WF-2026-001."""

    workflow_id: str
    project_root: str
    feature: Optional[str] = None
    requirement: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"  # pending | in_progress | blocked | completed
    stages: dict[str, StageState] = field(
        default_factory=lambda: {s: StageState() for s in STAGES}
    )
    current_stage: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "project_root": self.project_root,
            "feature": self.feature,
            "requirement": self.requirement,
            "created_at": self.created_at,
            "status": self.status,
            "current_stage": self.current_stage,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        wf = cls(
            workflow_id=data["workflow_id"],
            project_root=data["project_root"],
            feature=data.get("feature"),
            requirement=data.get("requirement"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            status=data.get("status", "pending"),
            current_stage=data.get("current_stage"),
            metadata=data.get("metadata", {}),
        )
        for s in STAGES:
            wf.stages[s] = StageState.from_dict(data.get("stages", {}).get(s, {}))
        return wf

    # -- transitions ---------------------------------------------------------

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"

    def next_stage(self) -> Optional[str]:
        """Return the next pending or in_progress stage after current_stage."""
        found_current = self.current_stage is not None
        for s in STAGES:
            if s == self.current_stage:
                found_current = True
                continue
            if found_current:
                st = self.stages[s]
                if st.status in ("pending", "in_progress"):
                    return s
        return None

    def advance_stage(self, stage: str, status: str = "completed", 
                      note: str = "", output_path: Optional[str] = None) -> None:
        """Mark a stage as completed (or blocked) and advance current_stage."""
        now = datetime.now(timezone.utc).isoformat()
        st = self.stages[stage]
        st.status = status
        st.note = note
        st.output_path = output_path
        if status == "in_progress":
            st.started_at = now
        else:
            st.completed_at = now

        if status == "completed":
            idx = STAGES.index(stage)
            if idx + 1 < len(STAGES):
                self.current_stage = STAGES[idx + 1]
            else:
                self.current_stage = None
                self.status = "completed"
        elif status == "blocked":
            self.current_stage = stage
            self.status = "blocked"
        elif status == "in_progress":
            self.current_stage = stage
            self.status = "in_progress"

    def start_workflow(self, feature: Optional[str] = None, 
                       requirement: Optional[str] = None) -> None:
        """Initialize a workflow for execution."""
        self.feature = feature or self.feature
        self.requirement = requirement or self.requirement
        self.status = "in_progress"
        self.current_stage = STAGES[0]
        self.advance_stage(STAGES[0], "pending")


# ---------------------------------------------------------------------------
# Workflow store — persistence to .ai/workflow/state.json
# ---------------------------------------------------------------------------


class WorkflowStore:
    """Reads/writes workflow state under .ai/workflow/."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.workflow_dir = self.project_root / ".ai" / "workflow"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.workflow_dir / "state.json"

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.state_path.exists():
            return {}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, dict[str, Any]]) -> None:
        tmp = self.state_path.read_text(encoding="utf-8") if self.state_path.exists() else "{}"
        self.state_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def save(self, wf: Workflow) -> None:
        data = self._read()
        data[wf.workflow_id] = wf.to_dict()
        self._write(data)

    def load(self, workflow_id: str) -> Optional[Workflow]:
        data = self._read().get(workflow_id)
        if data is None:
            return None
        return Workflow.from_dict(data)

    def load_current(self) -> Optional[Workflow]:
        """Return the most recent in-progress or blocked workflow, or None."""
        data = self._read()
        for wf_id in reversed(list(data.keys())):
            wf_data = data[wf_id]
            if wf_data.get("status") in ("in_progress", "blocked"):
                return Workflow.from_dict(wf_data)
        return None

    def list_all(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self._read().items())

    def delete(self, workflow_id: str) -> bool:
        data = self._read()
        if workflow_id not in data:
            return False
        del data[workflow_id]
        self._write(data)
        return True

    def next_id(self) -> str:
        count = len(self._read()) + 1
        return f"WF-{datetime.now().year}-{count:03d}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def stage_status_symbol(status: str) -> str:
    return {
        "completed": "✓",
        "in_progress": "→",
        "pending": "○",
        "blocked": "✗",
    }.get(status, "?")


def format_workflow(wf: Workflow) -> str:
    """Human-readable workflow summary (the `ai status` output format)."""
    lines: list[str] = []
    lines.append(f"Workflow: {wf.workflow_id}")
    lines.append(f"Status: {wf.status}")
    if wf.feature:
        lines.append(f"Feature: {wf.feature}")
    if wf.requirement:
        req = wf.requirement
        if len(req) > 120:
            req = req[:117] + "..."
        lines.append(f"Requirement: {req}")
    lines.append("")
    lines.append("Stages:")
    for s in STAGES:
        st = wf.stages[s]
        sym = stage_status_symbol(st.status)
        label = STAGE_LABELS[s]
        line = f"  {sym} {label}"
        if st.note:
            line += f" — {st.note}"
        if st.output_path:
            line += f"  → {st.output_path}"
        lines.append(line)
    if wf.status == "completed":
        lines.append("")
        lines.append("✓ Workflow complete.")
    elif wf.status == "blocked":
        lines.append("")
        lines.append("✗ Workflow blocked.")
    return "\n".join(lines)
