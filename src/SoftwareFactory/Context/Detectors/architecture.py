"""
STEP 2.4 — Architecture Detector.

Infers architectural style from folder layout, naming conventions,
and common project structures.

Heuristics (deterministic, no LLM):
  - Clean Architecture: src/{domain,application,infrastructure,presentation}
    or src/{Core,Application,Infrastructure,Presentation}
  - Layered: src/{controllers,services,repositories,models} or similar
  - Modular Monolith: src/modules/, src/features/, or src/modules/*.py
  - MVC: controllers + views + models, or app/{controllers,models,views}
  - Hexagonal: ports/adapters, or domain + primary/secondary adapters
  - Microservices: multiple independently-named service dirs at root
  - Django-style: app/*.py with models.py, views.py, admin.py
  - Rails-style: app/{models,controllers,views}, config/, db/
  - Next.js: app/ or pages/ + components/ + lib/
  - Flask-style: app.py or wsgi.py + blueprints/

Confidence is low unless a clear pattern matches. Notes carry what was seen.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ..Core import ArchitectureContext
from ..Core.detector import Detector

# patterns: (label, required_dirs, forbidden_dirs, optional_dirs)
ARCH_PATTERNS = [
    (
        "Clean Architecture",
        {"domain", "application", "infrastructure", "presentation"},
        set(),
        {"core", "common", "shared"},
    ),
    (
        "Clean Architecture (alt naming)",
        {"Core", "Application", "Infrastructure", "Presentation"},
        set(),
        {"Domain", "Shared"},
    ),
    (
        "Layered Architecture",
        {"controllers", "services", "repositories", "models"},
        set(),
        {"dto", "exceptions", "middleware"},
    ),
    (
        "Hexagonal Architecture",
        {"domain"},
        set(),
        {"ports", "adapters", "primary", "secondary"},
    ),
    (
        "MVC",
        {"controllers", "models", "views"},
        set(),
        {"middleware", "routes"},
    ),
    (
        "Modular Monolith",
        {"modules", "features", "bounded_contexts"},
        set(),
        {"common", "shared"},
    ),
]

MVC_LIKE = {
    "laravel": {"app/Http/Controllers", "app/Models", "resources/views"},
    "symfony": {"src/Controller", "src/Entity", "templates"},
    "rails": {"app/models", "app/controllers", "app/views"},
    "django": {"models.py", "views.py", "admin.py"},
}


class ArchitectureDetector(Detector):
    """STEP 2.4 — Architecture Detector."""

    @property
    def block_name(self) -> str:
        return "architecture"

    def detect(self) -> dict:
        dirs = _existing_dirs(self.root)
        subdirs = {d.relative_to(self.root).as_posix() for d in dirs}

        styles: list[str] = []
        notes: list[str] = []

        # Pattern-based detection
        for label, required, forbidden, optional in ARCH_PATTERNS:
            required_posix = {r for r in required}
            if required_posix and not required_posix.issubset(subdirs):
                continue
            if forbidden and forbidden & subdirs:
                continue
            if label not in styles:
                styles.append(label)
                if optional:
                    found_opt = optional & subdirs
                    if found_opt:
                        notes.append(f"{label}: optional dirs found: {sorted(found_opt)}")

        # Framework-specific heuristics
        fw = _framework_signal(self.root, subdirs)
        if fw:
            styles.append(fw)
            notes.append(f"framework-style layout detected: {fw}")

        # Component map: list top-level src/ subfolders as coarse components
        components = _component_map(self.root, subdirs)

        confidence = _confidence(styles, subdirs)

        return ArchitectureContext(
            detected_styles=styles,
            confidence=confidence,
            components=components,
            layers=[{"name": str(d.relative_to(self.root).as_posix())} for d in dirs][:20],
            notes=notes,
        ).model_dump()


ARCH_SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".output",
    ".venv", "venv", ".venvs", ".cache", ".stack-work",
    ".turbo", ".gradle", ".idea", ".vscode", "bin", "obj",
    ".vite", ".eslintcache",
}


def _existing_dirs(root: Path) -> list[Path]:
    try:
        return [
            p for p in root.iterdir()
            if p.is_dir()
            and not p.name.startswith(".")
            and p.name not in ARCH_SKIP_DIRS
        ]
    except OSError:
        return []


def _framework_signal(root: Path, subdirs: set[str]) -> str | None:
    # Next.js
    if root.joinpath("package.json").exists():
        try:
            import json as _json
            pkg = _json.loads(root.joinpath("package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "Next.js (React)"
            if "nuxt" in deps:
                return "Nuxt (Vue)"
            if "svelte" in deps and "svelte-kit" in deps:
                return "SvelteKit"
            if "react" in deps and "vite" in deps:
                return "React + Vite"
        except (OSError, ValueError):
            pass

    # Django
    if root.joinpath("manage.py").exists():
        return "Django"

    # Rails
    if root.joinpath("Gemfile").exists():
        try:
            text = root.joinpath("Gemfile").read_text(encoding="utf-8")
            if "rails" in text:
                return "Ruby on Rails"
        except OSError:
            pass

    # Laravel / Symfony via composer
    if root.joinpath("composer.json").exists():
        try:
            import json as _json
            pkg = _json.loads(root.joinpath("composer.json").read_text(encoding="utf-8"))
            name = pkg.get("name", "")
            if "laravel" in name:
                return "Laravel"
            if "symfony" in name:
                return "Symfony"
        except (OSError, ValueError):
            pass

    # Flask
    for name in ("app.py", "wsgi.py", "main.py"):
        if root.joinpath(name).exists():
            try:
                if "flask" in root.joinpath("requirements.txt").read_text(encoding="utf-8", errors="ignore"):
                    return "Flask"
            except OSError:
                pass

    # ASP.NET
    if list(root.glob("*.csproj")) or root.joinpath("Program.cs").exists():
        return "ASP.NET Core"

    return None


def _component_map(root: Path, subdirs: set[str]) -> list[dict[str, object]]:
    """Coarse component map: top-level directories that look like modules."""
    components: list[dict[str, object]] = []
    for d in _existing_dirs(root):
        name = d.name
        if name in (".git", "node_modules", "dist", "build", "venv", ".venv"):
            continue
        if name.startswith("."):
            continue
        count = len(list(d.glob("*")))
        components.append({
            "name": name,
            "type": "directory",
            "file_count": count,
            "path": d.relative_to(root).as_posix(),
        })
    return components


def _confidence(styles: list[str], subdirs: set[str]) -> float:
    if not styles:
        return 0.0
    if len(styles) == 1 and len(subdirs) >= 3:
        return 0.8
    if len(styles) >= 2:
        return 0.6
    return 0.4
