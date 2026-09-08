"""
STEP 2.6 - API Analyzer.

Detects API surfaces, styles, routing files, and endpoint patterns.

Signals:
  - REST:  presence of route registration (express Router, FastAPI
            @app.get, Spring @RequestMapping, ASP.NET [HttpGet], Laravel
            Route::, Django urls.py, Rails routes.rb)
  - GraphQL: schema.graphql / schema.ts / gql tags / codegen
  - gRPC:  *.proto, grpc.go / @grpc decorators
  - tRPC:  trpc routers
  - WebSockets / SSE: ws setup, event streams
  - SOAP:  wsdl, xml-based service descriptors

Endpoint extraction is best-effort and heuristic. The goal of v1 is to
surface routing files and a style guess, not to enumerate every endpoint.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import Field

from ..Core import ApiContext
from ..Core.detector import Detector

GRAPHQL_HINTS = ["schema.graphql", "schema.ts", "schema.js", "codegen.ts", "codegen.yml", ".graphqlconfig", "gql"]
GRPC_HINTS = ["*.proto", "protos/", "proto/"]

API_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    ".ruff_cache", "dist", "build", ".next", ".output",
    ".venv", "venv", ".venvs", ".cache", ".stack-work",
    ".turbo", ".gradle", ".idea", ".vscode", "bin", "obj",
    ".vite", ".eslintcache",
}


class ApiDetector(Detector):
    """STEP 2.6 - API Analyzer."""

    @property
    def block_name(self) -> str:
        return "api"

    def detect(self) -> dict:
        styles: list[str] = []
        routing_files: list[str] = []
        endpoints: list[dict[str, object]] = []

        routing_files = _discover_routing_files(self.root)
        styles = _infer_styles(self.root)
        endpoints = _extract_endpoints(self.root, routing_files)

        if not styles:
            if routing_files:
                styles.append("Custom / unclassified")

        return ApiContext(
            styles=styles,
            endpoints=endpoints,
            routing_files=routing_files,
            detected=bool(styles or routing_files),
        ).model_dump()


def _infer_styles(root: Path) -> list[str]:
    styles: list[str] = []

    # Node.js ecosystem
    pkg = root / "package.json"
    if pkg.exists():
        try:
            import json as _json
            data = _json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if any(k.startswith("express") for k in deps):
                styles.append("Express.js REST")
            if any(k.startswith("fastify") for k in deps):
                styles.append("Fastify REST")
            if any(k.startswith("next") for k in deps):
                styles.append("Next.js API Routes")
            if any(k.startswith("trpc") for k in deps):
                styles.append("tRPC")
            if any(k.startswith("apollo") or k.startswith("graphql") for k in deps):
                styles.append("GraphQL client/server")
            if any(k.startswith("@grpc") or k == "grpc" for k in deps):
                styles.append("gRPC")
            if any(k.startswith("svelte") and k.startswith("svelte-kit") for k in deps):
                styles.append("SvelteKit endpoints")
        except (OSError, ValueError):
            pass

    # GraphQL schema files
    if any(root.joinpath(h).exists() for h in GRAPHQL_HINTS):
        if "GraphQL" not in " ".join(styles):
            styles.append("GraphQL")

    # Python
    if root.joinpath("requirements.txt").exists():
        try:
            text = root.joinpath("requirements.txt").read_text(encoding="utf-8")
            if "fastapi" in text:
                styles.append("FastAPI REST")
            elif "flask" in text:
                styles.append("Flask REST")
            elif "django" in text:
                styles.append("Django REST")
        except OSError:
            pass

    # ASP.NET
    if list(root.glob("*.csproj")) or root.joinpath("Program.cs").exists():
        styles.append("ASP.NET Core Web API")

    # Java
    if root.joinpath("pom.xml").exists() or root.joinpath("build.gradle").exists():
        styles.append("Spring Boot REST")

    # PHP
    if root.joinpath("artisan").exists():
        styles.append("Laravel REST")
    elif root.joinpath("composer.json").exists():
        try:
            import json as _json
            pkg = _json.loads(root.joinpath("composer.json").read_text(encoding="utf-8"))
            if "laravel" in pkg.get("name", ""):
                styles.append("Laravel REST")
        except (OSError, ValueError):
            pass

    # Ruby
    if root.joinpath("Gemfile").exists():
        try:
            if "rails" in root.joinpath("Gemfile").read_text(encoding="utf-8", errors="ignore"):
                styles.append("Ruby on Rails REST")
        except OSError:
            pass

    # Go
    if root.joinpath("go.mod").exists():
        styles.append("Go net/http or framework REST")

    return styles


def _discover_routing_files(root: Path) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        rel = p.relative_to(root).as_posix()
        if rel not in seen and p.is_file():
            seen.add(rel)
            files.append(rel)

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        parts = rel.parts
        if any(part in API_SKIP_DIRS for part in parts):
            continue
        name = p.name
        if name in {
            "routes.py", "urls.py", "wsgi.py", "asgi.py", "main.py", "app.py",
            "api.py", "routes.js", "routes.ts", "router.ts", "router.js",
            "trpc.ts", "trpc.js", "routes.php", "web.php", "api.php",
            "routes.rb", "routes.go", "handlers.go", "server.go",
            "schema.graphql", "schema.ts", "schema.js",
            "Program.cs", "Startup.cs",
            "pom.xml", "build.gradle", "build.gradle.kts",
            "package.json", "composer.json",
        }:
            add(p)
        if p.is_dir() and p.name in {"routes", "router", "api", "controllers", "Controllers", "graphql", "protos", "proto"}:
            for child in p.glob("*"):
                if child.is_file():
                    add(child)

    return sorted(files)


def _extract_endpoints(root: Path, routing_files: list[str]) -> list[dict[str, object]]:
    endpoints: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    def add_ep(path: str, method: str, file: str, line_no: int) -> None:
        key = (method, path)
        if key in seen:
            return
        seen.add(key)
        endpoints.append({"path": path, "method": method, "file": file, "line": line_no})

    for rel in routing_files:
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()

        for i, line in enumerate(lines, start=1):
            # Express / Fastify: router.get('/path', ...)
            m = re.search(r"\.(get|post|put|patch|delete|head|options)\(\s*['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m:
                add_ep(m.group(2), m.group(1).upper(), rel, i)

        for i, line in enumerate(lines, start=1):
            # FastAPI / Flask: @app.get("/path")  / @router.get("/path")
            m = re.search(r"@(app|router|api)\.(get|post|put|patch|delete|head|options)\(\s*['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m:
                add_ep(m.group(3), m.group(2).upper(), rel, i)

        for i, line in enumerate(lines, start=1):
            # ASP.NET: [HttpGet("path")], [HttpPost("path")]
            m = re.search(r"\[(HttpGet|HttpPost|HttpPut|HttpPatch|HttpDelete|HttpHead|HttpOptions)\(\s*['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m:
                add_ep(m.group(2), m.group(1).replace("Http", "").upper(), rel, i)
            m2 = re.search(r"\.Map(Get|Post|Put|Patch|Delete|Head|Options)\(\s*['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m2:
                add_ep(m2.group(2), m2.group(1).upper(), rel, i)

        for i, line in enumerate(lines, start=1):
            # Spring: @GetMapping("/path"), @PostMapping("/path")
            m = re.search(r"@([A-Za-z]+Mapping)\(\s*['\"]([^'\"]+)['\"]", line)
            if m:
                mapping = m.group(1)
                path = m.group(2)
                method = {
                    "GetMapping": "GET", "PostMapping": "POST",
                    "PutMapping": "PUT", "DeleteMapping": "DELETE",
                    "PatchMapping": "PATCH",
                }.get(mapping, "GET")
                add_ep(path, method, rel, i)

        # Next.js route files
        if "route.ts" in rel or "route.js" in rel:
            for i, line in enumerate(lines, start=1):
                m = re.search(r"export\s+(async\s+)?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\(\s*(?:req|request)", line, re.IGNORECASE)
                if m:
                    method = m.group(2).upper()
                    parts = Path(rel).parts
                    try:
                        idx = parts.index("api")
                        path = "/" + "/".join(parts[idx + 1 : -1]).replace(".ts", "").replace(".js", "")
                        if path:
                            add_ep(path, method, rel, i)
                    except ValueError:
                        add_ep(f"/{rel}", method, rel, i)

        # Laravel: Route::get('/path', ...)
        for i, line in enumerate(lines, start=1):
            m = re.search(r"Route::(get|post|put|patch|delete|options|any|match)\(\s*['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m:
                add_ep(m.group(2), m.group(1).upper(), rel, i)

        # Ruby on Rails: resources :users  or  get '/path'
        for i, line in enumerate(lines, start=1):
            m = re.search(r"(get|post|put|patch|delete|head|options)\s+['\"]([^'\"]+)['\"]", line, re.IGNORECASE)
            if m:
                add_ep(m.group(2), m.group(1).upper(), rel, i)
            m2 = re.search(r"resources\s+:(\w+)", line)
            if m2:
                resource = m2.group(1)
                for method, suffix in [("GET", ""), ("POST", ""), ("PUT", "{id}"), ("PATCH", "{id}"), ("DELETE", "{id}")]:
                    add_ep(f"/{resource}/{suffix}".rstrip("/"), method, rel, i)

    return endpoints
