"""
AI Software Factory - Context Engine Core

STEP 2 - Context Engine Core.

Reads a repository and produces structured .ai/context/*.json files
so downstream agents (Analyst, Architect, Planner, Developer, Tester,
Security) start from evidence, not guesses.

Design:
  - Detector interface: each detector is a small, focused module.
  - Models: pydantic models define the shape of each context file.
  - CLI: `ai context scan` runs the engine against a target repo.
  - Deterministic first; LLM interpretation comes later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from .detector import Detector


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ProjectContext(BaseModel):
    """project.json - top-level identity of the scanned project."""

    project_name: str = Field(description="Human-readable project name")
    root_path: str = Field(description="Absolute path to the repo root")
    scanned_at: str = Field(description="ISO-8601 timestamp of the scan")
    version: str = "1.0.0"


class LanguageContext(BaseModel):
    """language.json - languages and their confidence."""

    languages: list[dict[str, object]] = Field(default_factory=list)
    dominant_language: str | None = Field(default=None, description="Most likely primary language")
    total_source_files: int = 0
    total_lines_of_code: int = 0


class ArchitectureContext(BaseModel):
    """architecture.json - detected architectural style and component map."""

    detected_styles: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    components: list[dict[str, object]] = Field(default_factory=list)
    layers: list[dict[str, object]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DependencyContext(BaseModel):
    """dependencies.json - pinned and transitive dependencies per ecosystem."""

    ecosystems: dict[str, list[dict[str, object]]] = Field(default_factory=dict)
    total_dependencies: int = 0
    lockfile_present: bool = False


class DatabaseContext(BaseModel):
    """database.json - detected database tech, schema hints, migrations."""

    technologies: list[str] = Field(default_factory=list)
    migration_files: list[str] = Field(default_factory=list)
    schema_hints: list[dict[str, object]] = Field(default_factory=list)
    detected: bool = False


class ApiContext(BaseModel):
    """api.json - detected API surfaces and styles."""

    styles: list[str] = Field(default_factory=list)
    endpoints: list[dict[str, object]] = Field(default_factory=list)
    routing_files: list[str] = Field(default_factory=list)
    detected: bool = False


class TestContext(BaseModel):
    """tests.json - test framework, count, coverage signals."""

    frameworks: list[str] = Field(default_factory=list)
    test_file_count: int = 0
    test_directories: list[str] = Field(default_factory=list)
    coverage_configured: bool = False


class GitContext(BaseModel):
    """git.json - repository metadata and history signals."""

    is_git_repo: bool = False
    current_branch: str | None = None
    commit_count: int = 0
    authors: list[str] = Field(default_factory=list)
    recent_messages: list[str] = Field(default_factory=list)
    has_remote: bool = False


class FullContext(BaseModel):
    """Aggregated context - one object that holds every context file's data."""

    project: ProjectContext
    language: LanguageContext
    architecture: ArchitectureContext
    dependencies: DependencyContext
    database: DatabaseContext
    api: ApiContext
    test: TestContext
    git: GitContext


# ---------------------------------------------------------------------------
# ContextWriter - handles writing validated JSON to .ai/context/
# ---------------------------------------------------------------------------


class ContextWriter:
    """Writes each context model as a JSON file under .ai/context/."""

    def __init__(self, context_dir: Path) -> None:
        self.context_dir = context_dir
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def write(self, ctx: FullContext) -> list[Path]:
        """Write every context file. Returns the paths written."""
        mappings: list[tuple[str, BaseModel]] = [
            ("project.json", ctx.project),
            ("language.json", ctx.language),
            ("architecture.json", ctx.architecture),
            ("dependencies.json", ctx.dependencies),
            ("database.json", ctx.database),
            ("api.json", ctx.api),
            ("tests.json", ctx.test),
            ("git.json", ctx.git),
        ]
        written: list[Path] = []
        for filename, model in mappings:
            path = self.context_dir / filename
            path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
            written.append(path)
        return written


# ---------------------------------------------------------------------------
# ContextEngine - orchestrates detectors
# ---------------------------------------------------------------------------


class ContextEngine:
    """STEP 2.1 + 2.10 - Core engine that runs detectors and aggregates.

    Usage:
        engine = ContextEngine(root=Path("/path/to/repo"))
        context = engine.scan()
        writer = ContextWriter(Path("/path/to/repo/.ai/context"))
        writer.write(context)

    Rules: 00-core - understand before changing. The engine does not
    modify the target repo; it only reads.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._detectors: list[Detector] = []

    def register(self, detector: Detector) -> None:
        """Register a detector. Called automatically by install_detectors()."""
        self._detectors.append(detector)

    def install_detectors(self) -> None:
        """Install every built-in detector."""
        from ..Detectors import (
            ArchitectureDetector,
            ApiDetector,
            DatabaseDetector,
            DependencyDetector,
            FilesystemDetector,
            GitDetector,
            LanguageDetector,
            TestDetector,
        )

        self.register(FilesystemDetector(self.root))
        self.register(LanguageDetector(self.root))
        self.register(ArchitectureDetector(self.root))
        self.register(DependencyDetector(self.root))
        self.register(DatabaseDetector(self.root))
        self.register(ApiDetector(self.root))
        self.register(TestDetector(self.root))
        self.register(GitDetector(self.root))

    def scan(self) -> FullContext:
        """Run every detector and aggregate into a FullContext."""
        if not self._detectors:
            self.install_detectors()

        now = datetime.now(timezone.utc).isoformat()
        blocks: dict[str, object] = {}
        for detector in self._detectors:
            try:
                blocks[detector.block_name] = detector.detect()
            except Exception as exc:
                # A single detector failure must not kill the whole scan.
                blocks[detector.block_name] = {
                    "error": str(exc),
                    "partial": getattr(exc, "partial", None),
                }

        return FullContext(
            project=blocks.get("project", ProjectContext(
                project_name=self.root.name,
                root_path=str(self.root),
                scanned_at=now,
            )),
            language=blocks.get("language", LanguageContext()),
            architecture=blocks.get("architecture", ArchitectureContext()),
            dependencies=blocks.get("dependencies", DependencyContext()),
            database=blocks.get("database", DatabaseContext()),
            api=blocks.get("api", ApiContext()),
            test=blocks.get("test", TestContext()),
            git=blocks.get("git", GitContext()),
        )


# ---------------------------------------------------------------------------
# Public API for the CLI and for downstream code
# ---------------------------------------------------------------------------


def scan_root(root: Path | str, out_dir: Path | str | None = None) -> FullContext:
    """Convenience: scan a repo and write context files in one call.

    Returns the FullContext so callers can inspect it programmatically.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Root is not a directory: {root}")

    engine = ContextEngine(root)
    engine.install_detectors()
    ctx = engine.scan()

    out = Path(out_dir) if out_dir else root / ".ai" / "context"
    writer = ContextWriter(out)
    writer.write(ctx)
    return ctx


__all__ = [
    "ContextEngine",
    "ContextWriter",
    "FullContext",
    "ProjectContext",
    "LanguageContext",
    "ArchitectureContext",
    "DependencyContext",
    "DatabaseContext",
    "ApiContext",
    "TestContext",
    "GitContext",
    "scan_root",
]
