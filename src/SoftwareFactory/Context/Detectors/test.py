"""
STEP 2.8 - Test Analyzer.

Detects test frameworks, test file counts, test directories,
and coverage configuration signals.

Frameworks detected (best-effort, by filename + config):
  Python: pytest, unittest, nose2, tox, coverage.py, pytest-cov
  Node:   jest, mocha, vitest, tap, nyc, c8
  C#:     xUnit, NUnit, MSTest
  Java:   JUnit, TestNG, Mockito
  Ruby:   RSpec, Minitest
  Go:     testing package ( *_test.go ), testify
  PHP:    PHPUnit
  Rust:   cargo test ( built-in )
  Elixir: ExUnit
  Kotlin: JUnit, Kotest
  Swift:  XCTest

Coverage config: .coveragerc, setup.cfg [coverage:run], jest coverage,
nyc config, coverage.xml, .xcov, etc.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ..Core import TestContext
from ..Core.detector import Detector


TEST_DIR_HINTS = {
    "tests", "test", "spec", "specs", "__tests__", "e2e", "integration",
    "functional", "unit", "acceptance", "features",
}

FRAMEWORK_FILENAMES = {
    "pytest": {"pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"},
    "unittest": {"test*.py", "*_test.py"},
    "nose2": {"nose2.cfg"},
    "tox": {"tox.ini"},
    "jest": {"jest.config.js", "jest.config.ts", "jest.config.cjs", "jest.config.mjs"},
    "mocha": {".mocharc.js", ".mocharc.json", ".mocharc.yaml", "mocha.opts"},
    "vitest": {"vitest.config.ts", "vitest.config.js"},
    "cypress": {"cypress.config.js", "cypress.config.ts"},
    "playwright": {"playwright.config.ts", "playwright.config.js"},
    "webdriverio": {"wdio.conf.js", "wdio.conf.ts"},
    "phpunit": {"phpunit.xml", "phpunit.xml.dist", "phpunit.xml.dist"},
    "rspec": {".rspec", "spec/spec_helper.rb"},
    "minitest": {"test_helper.rb"},
    "xunit": {"xunit.runner.json"},
    "nunit": {"*Test.csproj"},
    "mstest": {"*Test.csproj"},
    "junit": {"pom.xml"},  # JUnit via Maven
    "testng": {"testng.xml"},
    "exunit": {"test/test_helper.exs", "test/support"},
    "kotest": {"kotest.properties"},
    "xcov": {".xcov.yml"},
}

COVERAGE_CONFIGS = {
    ".coveragerc", "setup.cfg", "pyproject.toml", "tox.ini",  # coverage:run sections
    "jest.config.js", "jest.config.ts", "vitest.config.ts", "nyc.config.js", "nyc.config.json",
    "cobertura.xml", "coverage.xml", "lcov.info", "lcov.dat",
    ".xcov.yml", "codecov.yml", "codecov.yaml",
}


class TestDetector(Detector):
    """STEP 2.8 - Test Analyzer."""

    @property
    def block_name(self) -> str:
        return "test"

    def detect(self) -> dict:
        frameworks: list[str] = []
        test_file_count = 0
        test_directories: list[str] = []
        coverage_configured = False

        # Detect test directories
        for entry in self.root.iterdir():
            if entry.is_dir() and entry.name in TEST_DIR_HINTS:
                test_directories.append(entry.name)

        # Count test files
        for pattern in ["test_*.py", "*_test.py", "test*.ts", "*_test.ts", "*_test.go",
                        "*Test.java", "*Tests.java", "*Spec.js", "*Spec.ts", "*_spec.rb",
                        "*Test.cs", "*Tests.cs", "*Test.kt", "*Spec.scala",
                        "e2e/*.js", "e2e/*.ts", "e2e/*.feature"]:
            test_file_count += len(list(self.root.glob(pattern)))

        # also walk for test directories
        for d in test_directories:
            d_path = self.root / d
            for p in d_path.rglob("*"):
                if p.is_file() and p.suffix in {".py", ".ts", ".js", ".go", ".java", ".cs", ".rb", ".kt", ".scala", ".feature"}:
                    test_file_count += 1

        # Framework detection
        frameworks = _detect_frameworks(self.root)

        # Coverage detection
        coverage_configured = _detect_coverage(self.root)

        return TestContext(
            frameworks=frameworks,
            test_file_count=test_file_count,
            test_directories=test_directories,
            coverage_configured=coverage_configured,
        ).model_dump()


def _detect_frameworks(root: Path) -> list[str]:
    frameworks: list[str] = []

    # Python
    if root.joinpath("pytest.ini").exists() or root.joinpath("pyproject.toml").exists():
        try:
            if root.joinpath("pyproject.toml").read_text(encoding="utf-8"):
                pass
        except OSError:
            pass
        frameworks.append("pytest")
    if root.joinpath("tox.ini").exists():
        frameworks.append("tox")
    if root.joinpath("setup.cfg").exists():
        try:
            text = root.joinpath("setup.cfg").read_text(encoding="utf-8")
            if "[tool:pytest]" in text or "[pytest]" in text:
                frameworks.append("pytest")
        except OSError:
            pass
    if list(root.glob("test_*.py")) or list(root.glob("**/test_*.py")):
        if "pytest" not in frameworks and "unittest" not in frameworks:
            frameworks.append("unittest (pytest-style file naming)")

    # Node
    pkg = root / "package.json"
    if pkg.exists():
        try:
            import json as _json
            data = _json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except (OSError, ValueError):
            deps = {}
        if any(k.startswith("jest") for k in deps):
            frameworks.append("jest")
        if any(k.startswith("mocha") for k in deps):
            frameworks.append("mocha")
        if any(k.startswith("vitest") for k in deps):
            frameworks.append("vitest")
        if any(k.startswith("cypress") for k in deps):
            frameworks.append("cypress")
        if any(k.startswith("@playwright") for k in deps):
            frameworks.append("playwright")
        if any(k.startswith("tap") for k in deps):
            frameworks.append("tap")
        if any(k.startswith("ava") for k in deps):
            frameworks.append("ava")

    # C#
    for csproj in root.glob("**/*.csproj"):
        try:
            text = csproj.read_text(encoding="utf-8")
        except OSError:
            continue
        if "xunit" in text.lower() or "xunit.runner" in text:
            frameworks.append("xUnit")
        if "nunit" in text.lower() or "nunit.framework" in text:
            frameworks.append("NUnit")
        if "MSTest" in text or "Microsoft.VisualStudio.TestTools.UnitTesting" in text:
            frameworks.append("MSTest")

    # Java
    pom = root / "pom.xml"
    if pom.exists():
        try:
            text = pom.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "junit" in text.lower():
            frameworks.append("JUnit")
        if "testng" in text.lower():
            frameworks.append("TestNG")
        if "mockito" in text.lower():
            frameworks.append("Mockito")
    testng = root / "testng.xml"
    if testng.exists():
        frameworks.append("TestNG")

    # Ruby
    if root.joinpath(".rspec").exists() or root.joinpath("spec/spec_helper.rb").exists():
        frameworks.append("RSpec")
    if root.joinpath("test_helper.rb").exists():
        frameworks.append("Minitest")

    # Go
    test_go = list(root.glob("**/*_test.go"))
    if test_go:
        frameworks.append("Go testing")
        if root.joinpath("go.mod").exists():
            try:
                text = root.joinpath("go.mod").read_text(encoding="utf-8")
                if "testify" in text:
                    frameworks.append("testify")
            except OSError:
                pass

    # PHP
    for phpunit in ["phpunit.xml", "phpunit.xml.dist"]:
        if root.joinpath(phpunit).exists():
            frameworks.append("PHPUnit")
            break

    # Rust
    if root.joinpath("Cargo.toml").exists():
        frameworks.append("cargo test (built-in)")

    # Elixir
    if root.joinpath("test/test_helper.exs").exists() or root.joinpath("mix.exs").exists():
        frameworks.append("ExUnit")

    # Kotlin
    for kt_test in root.glob("**/*Test.kt"):
        if kt_test.is_file():
            frameworks.append("JUnit/Kotest (Kotlin)")
            break

    # Scala
    for scala_test in root.glob("**/*Spec.scala"):
        if scala_test.is_file():
            frameworks.append("ScalaTest")
            break

    # Coverage config file presence
    coverage_names = {p for p in COVERAGE_CONFIGS if (root / p).exists()}
    if coverage_names:
        frameworks.append(f"coverage config: {', '.join(sorted(coverage_names))}")

    return frameworks


def _detect_coverage(root: Path) -> bool:
    if any((root / name).exists() for name in COVERAGE_CONFIGS):
        return True
    if root.joinpath("pom.xml").exists():
        try:
            if "jacoco" in root.joinpath("pom.xml").read_text(encoding="utf-8", errors="ignore").lower():
                return True
        except OSError:
            pass
    if root.joinpath("Cargo.toml").exists():
        try:
            if "tarpaulin" in root.joinpath("Cargo.toml").read_text(encoding="utf-8", errors="ignore").lower():
                return True
        except OSError:
            pass
    # simple heuristic: if there's a coverage/ directory
    if (root / "coverage").is_dir():
        return True
    return False
