"""
STEP 2.5 — Dependency Analyzer.

Reads ecosystem manifest/lock files and reports pinned versions.
Ecosystems detected right now:

  Python:  pyproject.toml, requirements.txt, setup.py, Pipfile, poetry.lock
  Node:    package.json (+ package-lock.json, pnpm-lock.yaml, yarn.lock)
  Go:      go.mod (+ go.sum)
  Rust:    Cargo.toml (+ Cargo.lock)
  JVM:     pom.xml, build.gradle, build.gradle.kts, gradle.lockfile
  PHP:     composer.json (+ composer.lock)
  Ruby:    Gemfile (+ Gemfile.lock)
  .NET:    *.csproj, packages.lock.json (if present)
  Elixir:  mix.exs (+ mix.lock)

Framework-level hints (next.js, django, rails, etc.) are captured by
the ArchitectureDetector and can be cross-referenced later.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import Field

from ..Core import DependencyContext
from ..Core.detector import Detector

LOCKFILE_BY_ECOSYSTEM: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "Pipfile.lock"],
    "node": ["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pnpm-lock.yaml"],
    "go": ["go.mod", "go.sum"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "jvm": ["pom.xml", "build.gradle", "build.gradle.kts", "gradle.lockfile"],
    "php": ["composer.json", "composer.lock"],
    "ruby": ["Gemfile", "Gemfile.lock"],
    "dotnet": ["*.csproj"],
    "elixir": ["mix.exs", "mix.lock"],
}


class DependencyDetector(Detector):
    """STEP 2.5 — Dependency Analyzer."""

    @property
    def block_name(self) -> str:
        return "dependencies"

    def detect(self) -> dict:
        ecosystems: dict[str, list[dict[str, object]]] = {}
        total = 0
        lockfile_present = False

        python_deps = _parse_python(self.root)
        if python_deps:
            ecosystems["python"] = python_deps
            total += len(python_deps)

        node_deps = _parse_node(self.root)
        if node_deps:
            ecosystems["node"] = node_deps
            total += len(node_deps)

        go_deps = _parse_go(self.root)
        if go_deps:
            ecosystems["go"] = go_deps
            total += len(go_deps)

        rust_deps = _parse_rust(self.root)
        if rust_deps:
            ecosystems["rust"] = rust_deps
            total += len(rust_deps)

        jvm_deps = _parse_jvm(self.root)
        if jvm_deps:
            ecosystems["jvm"] = jvm_deps
            total += len(jvm_deps)

        php_deps = _parse_php(self.root)
        if php_deps:
            ecosystems["php"] = php_deps
            total += len(php_deps)

        ruby_deps = _parse_ruby(self.root)
        if ruby_deps:
            ecosystems["ruby"] = ruby_deps
            total += len(ruby_deps)

        dotnet_deps = _parse_dotnet(self.root)
        if dotnet_deps:
            ecosystems["dotnet"] = dotnet_deps
            total += len(dotnet_deps)

        # lockfile signal
        for files in LOCKFILE_BY_ECOSYSTEM.values():
            for name in files:
                if "*" in name:
                    if list(self.root.glob(name)):
                        lockfile_present = True
                        break
                elif self.root.joinpath(name).exists():
                    lockfile_present = True
                    break

        return DependencyContext(
            ecosystems=ecosystems,
            total_dependencies=total,
            lockfile_present=lockfile_present,
        ).model_dump()


def _parse_python(root: Path) -> list[dict[str, object]] | None:
    """Returns a list of deps from pyproject.toml / requirements.txt / setup.py."""
    if not any(root.joinpath(n).exists() for n in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock")):
        return None

    deps: list[dict[str, object]] = []
    names: set[str] = set()

    # pyproject.toml (poetry/hatch/others)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8")
            # poetry-style: [tool.poetry.dependencies]
            if "[tool.poetry.dependencies]" in text:
                for line in text.splitlines():
                    if line.strip().startswith("[") or line.strip().startswith("#"):
                        continue
                    m = re.match(r"^(\S+)\s*=\s*\[?\s*[\"']?([\d\.\*a-zA-Z\-]+)", line)
                    if m:
                        name, ver = m.groups()
                        if name not in names:
                            names.add(name)
                            deps.append({"name": name, "version": ver, "source": "pyproject.toml"})
            # hatch-style / inline table
            if "dependencies" in text and "[tool.poetry" not in text:
                for line in text.splitlines():
                    if line.strip().startswith("[") or line.strip().startswith("#"):
                        continue
                    m = re.match(r"^(\S+)\s*([>=<~!][^\s#]+)?", line)
                    if m:
                        name, ver = m.groups()
                        if name not in names and name.lower() not in ("python",):
                            names.add(name)
                            deps.append({"name": name, "version": ver or "*", "source": "pyproject.toml"})
        except OSError:
            pass

    # requirements.txt
    req = root / "requirements.txt"
    if req.exists():
        try:
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.split("#", 1)[0].strip()
                if not line or line.startswith("-") or line.startswith("http"):
                    continue
                m = re.match(r"^([A-Za-z0-9_\-\.]+)\s*([>=<~!][^\s#]+)?", line)
                if m:
                    name, ver = m.groups()
                    if name.lower() not in ("python",) and name not in names:
                        names.add(name)
                        deps.append({"name": name, "version": ver or "*", "source": "requirements.txt"})
        except OSError:
            pass

    # setup.py (parse name/version fields only — fragile, but a signal)
    setup = root / "setup.py"
    if setup.exists():
        try:
            text = setup.read_text(encoding="utf-8")
            for key in ("install_requires", "packages"):
                if key in text:
                    # extremely rough: grab quoted strings that look like pkg names
                    for m in re.finditer(r"[\"'](\S+)[\"']", text):
                        pkg = m.group(1)
                        if pkg and pkg not in names and not pkg.startswith("__"):
                            names.add(pkg)
                            deps.append({"name": pkg, "version": "*", "source": "setup.py"})
        except OSError:
            pass

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_node(root: Path) -> list[dict[str, object]] | None:
    pkg = root / "package.json"
    if not pkg.exists():
        return None
    try:
        import json as _json
        data = _json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    deps: list[dict[str, object]] = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(section, {})
        if not block:
            continue
        for name, version in block.items():
            if name in ("@types/node",):
                continue
            deps.append({"name": name, "version": version, "source": "package.json"})

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_go(root: Path) -> list[dict[str, object]] | None:
    gomod = root / "go.mod"
    if not gomod.exists():
        return None
    try:
        text = gomod.read_text(encoding="utf-8")
    except OSError:
        return None
    deps: list[dict[str, object]] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("module") or line.startswith("go ") or line.startswith("//") or line == "":
            continue
        m = re.match(r"^(\S+)\s+([^\s#]+)", line)
        if m:
            name, version = m.groups()
            deps.append({"name": name, "version": version, "source": "go.mod"})
    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_rust(root: Path) -> list[dict[str, object]] | None:
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return None
    try:
        import tomllib as _toml
    except ImportError:
        try:
            import tomli as _toml
        except ImportError:
            return None
    try:
        data = _toml.loads(cargo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    deps: list[dict[str, object]] = []
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        block = data.get(section, {})
        if not block:
            continue
        for name, spec in block.items():
            if isinstance(spec, dict):
                ver = spec.get("version", "*")
                extra = spec.get("features", [])
                deps.append({"name": name, "version": ver, "features": extra, "source": "Cargo.toml"})
            elif isinstance(spec, str):
                deps.append({"name": name, "version": spec, "source": "Cargo.toml"})
            else:
                deps.append({"name": name, "version": "*", "source": "Cargo.toml"})

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_jvm(root: Path) -> list[dict[str, object]] | None:
    deps: list[dict[str, object]] = []

    # pom.xml
    pom = root / "pom.xml"
    if pom.exists():
        try:
            text = pom.read_text(encoding="utf-8")
            for m in re.finditer(r"<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>", text):
                name, ver = m.groups()
                deps.append({"name": name, "version": ver, "source": "pom.xml"})
        except OSError:
            pass

    # build.gradle / build.gradle.kts
    for gradle_name in ("build.gradle", "build.gradle.kts"):
        gradle = root / gradle_name
        if not gradle.exists():
            continue
        try:
            text = gradle.read_text(encoding="utf-8")
            # compileOnly / implementation / api with group:artifact:version
            for m in re.finditer(r"[\"']([^\"':]+):([^\"':]+):([^\"':]+)[\"']", text):
                group, artifact, ver = m.groups()
                deps.append({"name": f"{group}:{artifact}", "version": ver, "source": gradle_name})
        except OSError:
            pass

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_php(root: Path) -> list[dict[str, object]] | None:
    composer = root / "composer.json"
    if not composer.exists():
        return None
    try:
        import json as _json
        data = _json.loads(composer.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    deps: list[dict[str, object]] = []
    for section in ("require", "require-dev"):
        block = data.get(section, {})
        if not block:
            continue
        for name, version in block.items():
            if name == "php":
                continue
            deps.append({"name": name, "version": version, "source": "composer.json"})

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_ruby(root: Path) -> list[dict[str, object]] | None:
    gemfile = root / "Gemfile"
    if not gemfile.exists():
        return None
    try:
        text = gemfile.read_text(encoding="utf-8")
    except OSError:
        return None

    deps: list[dict[str, object]] = []
    gemfile_lock = root / "Gemfile.lock"
    lock_versions: dict[str, str] = {}
    if gemfile_lock.exists():
        try:
            in_gems = False
            for line in gemfile_lock.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("GEM"):
                    in_gems = True
                    continue
                if in_gems and line.startswith("  "):
                    parts = line.split()
                    if len(parts) >= 2:
                        lock_versions[parts[1]] = parts[0]
                if line.strip() == "":
                    in_gems = False
        except OSError:
            pass

    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("source") or line.startswith("git") or line.startswith("group"):
            continue
        # gem "name", "version"  or  gemname
        m = re.match(r'gem\s+([\'"])(\S+)\1\s*(?:,\s*([\'"])(\S+)\3)?', line)
        if m:
            quote, name, _, ver = m.groups()
            version = ver or lock_versions.get(name, "*")
            deps.append({"name": name, "version": version, "source": "Gemfile"})
        else:
            m2 = re.match(r"^\s*(\S+)\s*$", line)
            if m2:
                name = m2.group(1)
                if name not in ("gem", "source", "ruby") and name not in [d["name"] for d in deps]:
                    deps.append({"name": name, "version": lock_versions.get(name, "*"), "source": "Gemfile"})

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None


def _parse_dotnet(root: Path) -> list[dict[str, object]] | None:
    deps: list[dict[str, object]] = []
    for csproj in root.glob("*.csproj"):
        try:
            text = csproj.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in re.finditer(r"<PackageReference\s+Include[\"']=([\"'])(.+?)\1\s+Version[\"']=([\"'])(.+?)\3", text):
            _, name, _, version = m.groups()
            deps.append({"name": name, "version": version, "source": str(csproj.relative_to(root))})
        for m in re.finditer(r"<PackageReference\s+Include[\"']=([\"'])(.+?)\1[^>]*>", text):
            name = m.group(2)
            if not any(d["name"] == name for d in deps):
                deps.append({"name": name, "version": "*", "source": str(csproj.relative_to(root))})

    return sorted(deps, key=lambda d: str(d["name"])) if deps else None
