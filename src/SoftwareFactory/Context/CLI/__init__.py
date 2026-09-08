"""
AI Software Factory command-line interface.

This is STEP 3 — the control plane for the factory. Today it exposes:

    ai context scan [path]

Later it will grow into:

    ai analyze
    ai design
    ai plan
    ai implement
    ai test
    ai security
    ai review
    ai deploy
    ai run <feature>

Rules: 00-core — understand before changing. The CLI reads repos and
writes structured context; it never mutates the target repo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..Core import scan_root

# NOTE: Detector and the concrete detectors are imported by Core.ContextEngine
# only when install_detectors() runs. The CLI does not need them at import time.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ai",
        description="AI Software Factory — control plane for the SDLC",
    )
    sub = parser.add_subparsers(dest="command")

    # ai context
    context_parser = sub.add_parser("context", help="Context Engine commands")
    context_sub = context_parser.add_subparsers(dest="context_cmd")

    scan_parser = context_sub.add_parser("scan", help="Scan a repo and write .ai/context/*.json")
    scan_parser.add_argument("root", nargs="?", default=".", help="Path to the repo root (default: .)")
    scan_parser.add_argument("--out", "-o", help="Directory to write context files (default: <root>/.ai/context)")
    scan_parser.add_argument("--json", action="store_true", help="Print the full context as JSON to stdout")

    # ai status (placeholder — wired to workflow state in a later step)
    status_parser = sub.add_parser("status", help="Show current workflow status (placeholder)")

    args = parser.parse_args(argv)

    if args.command == "context" and args.context_cmd == "scan":
        return _cmd_scan(args)
    elif args.command == "status":
        return _cmd_status()
    else:
        parser.print_help()
        return 1


def _cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        return 2

    try:
        ctx = scan_root(root, out_dir=args.out)
    except Exception as exc:
        print(f"Error scanning {root}: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(ctx.model_dump_json(indent=2))

    written = ctx.model_dump()
    _print_summary(ctx, root)
    return 0


def _cmd_status() -> int:
    print("ai status is not wired yet.")
    print("This placeholder will read .ai/workflow/state.json in a later step.")
    return 0


def _print_summary(ctx, root: Path) -> None:
    print()
    print("Context Engine — scan complete")
    print("=" * 50)
    print(f"Project : {ctx.project.project_name}")
    print(f"Root    : {root}")
    print(f"Scanned : {ctx.project.scanned_at}")
    print()
    print("Languages")
    if ctx.language.languages:
        for entry in ctx.language.languages[:10]:
            print(f"  - {entry['language']:<15} files={entry['files']:<6} loc={entry['lines_of_code']}")
        if len(ctx.language.languages) > 10:
            print(f"  ... and {len(ctx.language.languages) - 10} more")
    else:
        print("  (none detected)")
    print()
    print(f"Dominant language : {ctx.language.dominant_language or '-'}")
    print(f"Source files      : {ctx.language.total_source_files}")
    print(f"Lines of code     : {ctx.language.total_lines_of_code}")
    print()
    print("Architecture")
    if ctx.architecture.detected_styles:
        print(f"  Styles : {', '.join(ctx.architecture.detected_styles)}")
    else:
        print("  Styles : (none detected)")
    print(f"  Confidence : {ctx.architecture.confidence:.2f}")
    print(f"  Components : {len(ctx.architecture.components)}")
    print()
    print("Dependencies")
    for eco, deps in ctx.dependencies.ecosystems.items():
        print(f"  {eco}: {len(deps)} package(s)")
    print(f"  Total dependencies: {ctx.dependencies.total_dependencies}")
    print(f"  Lockfile present   : {ctx.dependencies.lockfile_present}")
    print()
    print("Database")
    if ctx.database.technologies:
        print(f"  Technologies : {', '.join(ctx.database.technologies)}")
    else:
        print("  Technologies : (none detected)")
    print(f"  Migrations   : {len(ctx.database.migration_files)}")
    print(f"  Schema hints : {len(ctx.database.schema_hints)}")
    print()
    print("API")
    if ctx.api.styles:
        print(f"  Styles : {', '.join(ctx.api.styles)}")
    else:
        print("  Styles : (none detected)")
    print(f"  Routing files : {len(ctx.api.routing_files)}")
    print(f"  Endpoints     : {len(ctx.api.endpoints)}")
    print()
    print("Tests")
    if ctx.test.frameworks:
        print(f"  Frameworks : {', '.join(ctx.test.frameworks)}")
    else:
        print("  Frameworks : (none detected)")
    print(f"  Test files  : {ctx.test.test_file_count}")
    print(f"  Test dirs   : {', '.join(ctx.test.test_directories) or '-'}")
    print(f"  Coverage    : {'yes' if ctx.test.coverage_configured else 'no'}")
    print()
    print("Git")
    print(f"  Repository   : {'yes' if ctx.git.is_git_repo else 'no'}")
    print(f"  Branch       : {ctx.git.current_branch or '-'}")
    print(f"  Commits      : {ctx.git.commit_count}")
    print(f"  Authors      : {len(ctx.git.authors)}")
    print(f"  Has remote   : {ctx.git.has_remote}")
    print()
    print("=" * 50)
    print(f"Wrote context to: {root / '.ai' / 'context'}")
    print()


if __name__ == "__main__":
    sys.exit(main())
