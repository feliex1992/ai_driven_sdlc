"""
STEP 2.3 — Language & Framework Detector.

Maps file extensions to languages, counts source files and lines of code,
and picks a dominant language when one is clear.

Framework hints are detected via lockfiles / manifest files (package.json,
go.mod, pom.xml, etc.) — those go into dependencies detection, not here.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic import Field

from ..Core import LanguageContext
from ..Core.detector import Detector

# (extension, language)
EXTENSION_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".html": "HTML",
    ".htm": "HTML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".astro": "Astro",
    ".mjml": "MJML",
    ".apex": "Apex",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".elm": "Elm",
    ".lua": "Lua",
    ".ml": "OCaml",
    ".mli": "OCaml",
    ".pl": "Perl",
    ".pm": "Perl",
    ".r": "R",
    ".R": "R",
    ".php": "PHP",
    ".dart": "Dart",
    ".kts": "Kotlin",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", "dist", "build", ".next", ".output",
    ".venv", "venv", ".venvs", ".cache", ".stack-work",
    ".turbo", ".gradle", ".idea", ".vscode", "bin", "obj",
}


class LanguageDetector(Detector):
    """STEP 2.3 — Language & Framework Detector."""

    @property
    def block_name(self) -> str:
        return "language"

    def detect(self) -> dict:
        ext_counts: defaultdict[str, int] = defaultdict(int)
        ext_locs: defaultdict[str, int] = defaultdict(int)
        total_source = 0
        total_loc = 0

        for path in _walk(self.root):
            ext = path.suffix.lower()
            ext_counts[ext] += 1
            loc = _count_lines(path)
            ext_locs[ext] += loc
            if ext in EXTENSION_MAP:
                total_source += 1
                total_loc += loc

        lang_counts: defaultdict[str, int] = defaultdict(int)
        lang_locs: defaultdict[str, int] = defaultdict(int)
        for ext, count in ext_counts.items():
            lang = EXTENSION_MAP.get(ext, "Other")
            lang_counts[lang] += count
            lang_locs[lang] += ext_locs.get(ext, 0)

        languages: list[dict[str, object]] = []
        dominant: str | None = None
        for lang, count in sorted(lang_counts.items(), key=lambda kv: -kv[1]):
            languages.append({
                "language": lang,
                "files": count,
                "lines_of_code": lang_locs[lang],
            })
            if dominant is None:
                dominant = lang

        return LanguageContext(
            languages=languages,
            dominant_language=dominant,
            total_source_files=total_source,
            total_lines_of_code=total_loc,
        ).model_dump()


def _walk(root) -> list:
    """Yield files under root, skipping junk directories."""
    files: list = []
    try:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            parts = path.relative_to(root).parts
            if any(part in SKIP_DIRS for part in parts):
                continue
            files.append(path)
    except OSError:
        # Permission errors on some subdir — just stop walking that tree.
        pass
    return files


def _count_lines(path) -> int:
    """Count non-empty lines, ignoring BOM. Returns 0 on unreadable files."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    if text.startswith("\ufeff"):
        text = text[1:]
    return sum(1 for line in text.splitlines() if line.strip())
