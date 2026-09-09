"""
STEP 3 — AI CLI

The control plane for the AI Software Factory.

Today:
  ai status                     Show current workflow / stage status
  ai init [feature] [requirement]   Start a new workflow
  ai run <feature> [requirement]    Run full pipeline end-to-end
  ai analyze|design|plan|implement|test|security|review|deploy   Run single stage

Later:
  ai deploy, ai review, per-stage flags, resume, etc.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ...SDLC.workflow import (
    Workflow,
    WorkflowStore,
    STAGES,
    STAGE_LABELS,
    stage_status_symbol,
    format_workflow,
)
from ...SDLC.Agents.runner import AgentRunner, AgentKind, invoke_agent
from ..Core import scan_root
from ..Core import FullContext

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _project_root() -> Path:
    """Resolve the project root as the directory containing ROADMAP.md."""
    candidate = Path.cwd()
    # Walk up until we find ROADMAP.md (the ai_driven_sdlc root).
    for p in [candidate] + list(candidate.parents):
        if (p / "ROADMAP.md").exists():
            return p
    # Fallback: cwd
    return candidate


def _default_store(project_root: Path) -> WorkflowStore:
    return WorkflowStore(project_root / ".ai")


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def cmd_init(store: WorkflowStore, project_root: Path,
             feature: str | None, requirement: str | None) -> int:
    """Start a new workflow."""
    wf = Workflow(
        workflow_id=store.next_id(),
        project_root=str(project_root),
        feature=feature,
        requirement=requirement,
    )
    wf.start_workflow(feature, requirement)
    store.save(wf)
    print(f"Workflow {wf.workflow_id} started.")
    print(f"  Project : {project_root}")
    if feature:
        print(f"  Feature : {feature}")
    if requirement:
        print(f"  Requirement : {requirement}")
    print(f"  Current stage : {STAGE_LABELS[wf.current_stage]}")
    print()
    return 0


def cmd_status(store: WorkflowStore) -> int:
    """Show workflow / stage status."""
    wf = store.load_current()
    if wf is None:
        print("No active workflow.")
        print()
        print("Start one with:  ai init <feature> <requirement>")
        print("                 ai run <feature> <requirement>")
        return 0
    print(format_workflow(wf))
    return 0


def cmd_run(store: WorkflowStore, project_root: Path,
            feature: str, requirement: str, stages: list[str] | None) -> int:
    """Run one or more stages (or entire pipeline) end to end."""
    wf = store.load_current()
    if wf is None:
        wf = Workflow(
            workflow_id=store.next_id(),
            project_root=str(project_root),
            feature=feature,
            requirement=requirement,
        )
        wf.start_workflow(feature, requirement)
        store.save(wf)

    if wf.status == "completed":
        print(f"Workflow {wf.workflow_id} is already complete.")
        print("Start a new one with:  ai init ...")
        return 1

    target_stages = stages or STAGES[:]
    # Determine start point: if workflow is in progress, start from current stage
    start_idx = 0
    if wf.current_stage and wf.current_stage in STAGES:
        start_idx = STAGES.index(wf.current_stage)
    exec_stages = [s for s in target_stages[start_idx:] if s in target_stages]

    if not exec_stages:
        print("Nothing to run — all target stages already completed or not selected.")
        return 0

    # When --stages is explicitly given, run exactly those stages (no skip).
    # Only apply resume-from-current-stage when --stages is NOT provided.
    if not stages:
        exec_stages = [s for s in exec_stages if wf.stages[s].status != "completed"]

    runner = AgentRunner(project_root=project_root)
    for stage in exec_stages:
        print(f"\n{'='*60}")
        print(f"▶ {STAGE_LABELS[stage].upper()}")
        print(f"{'='*60}")

        wf.current_stage = stage
        wf.stages[stage].status = "in_progress"
        store.save(wf)

        try:
            result = invoke_agent(
                runner=runner,
                kind=_agent_kind_for(stage),
                stage=stage,
                workflow=wf,
            )
        except Exception as exc:
            print(f"Error in {stage}: {exc}", file=sys.stderr)
            wf.stages[stage].status = "blocked"
            wf.stages[stage].note = str(exc)
            wf.status = "blocked"
            store.save(wf)
            return 1

        if _is_block(result):
            wf.stages[stage].status = "blocked"
            wf.stages[stage].note = result.get("summary", str(result))
            wf.status = "blocked"
            store.save(wf)
            print(f"\n⚠ {STAGE_LABELS[stage]} blocked.")
            continue

        wf.stages[stage].status = "completed"
        wf.stages[stage].output_path = result.get("output_path")
        wf.stages[stage].note = result.get("summary", "")
        store.save(wf)

        print(f"\n✓ {STAGE_LABELS[stage]} — {result.get('summary', '')}")

        if _needs_approval(result):
            print(f"\n⚠ {STAGE_LABELS[stage]} needs human approval before continuing.")
            wf.status = "blocked"
            store.save(wf)
            print("Resolve with:  ai approve <workflow_id>")
            return 0

    print(f"\n{'='*60}")
    print(f"Workflow {wf.workflow_id} — done.")
    print(f"{'='*60}")
    return 0


def _agent_kind_for(stage: str) -> AgentKind:
    return {
        "analysis":     AgentKind.ANALYST,
        "architecture": AgentKind.ARCHITECT,
        "planning":     AgentKind.PLANNER,
        "development":  AgentKind.DEVELOPER,
        "testing":      AgentKind.TESTER,
        "security":     AgentKind.SECURITY,
        "review":       AgentKind.REVIEWER,
        "deployment":   AgentKind.DEPLOYER,
    }[stage]


def _is_block(result: dict) -> bool:
    return result.get("status") in ("blocked", "failed", "needs_approval")


def _needs_approval(result: dict) -> bool:
    return bool(result.get("requires_human_approval", False))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    project_root = _project_root()
    store = _default_store(project_root)

    parser = argparse.ArgumentParser(
        prog="ai",
        description="AI Software Factory — control plane for the SDLC",
    )
    sub = parser.add_subparsers(dest="command")

    # ai context — Context Engine commands
    context_parser = sub.add_parser("context", help="Context Engine commands")
    context_sub = context_parser.add_subparsers(dest="context_cmd")

    scan_parser = context_sub.add_parser("scan", help="Scan a repo and write .ai/context/*.json")
    scan_parser.add_argument("root", nargs="?", default=".", help="Path to the repo root (default: .)")
    scan_parser.add_argument("--out", "-o", help="Directory to write context files (default: <root>/.ai/context)")
    scan_parser.add_argument("--json", action="store_true", help="Print the full context as JSON to stdout")

    # ai status
    sub.add_parser("status", help="Show current workflow status")

    # ai init
    init_p = sub.add_parser("init", help="Start a new workflow")
    init_p.add_argument("feature", nargs="?", default=None, help="Feature name")
    init_p.add_argument("requirement", nargs="?", default=None, help="Requirement text")

    # ai run
    run_p = sub.add_parser("run", help="Run stages end-to-end")
    run_p.add_argument("feature", help="Feature name")
    run_p.add_argument("requirement", nargs="?", default=None, help="Requirement text")
    run_p.add_argument("--stages", "-s", nargs="+",
                       help="Explicit stage list (default: all remaining stages)")

    # single-stage commands
    single_stages = ["analyze", "design", "plan", "implement", "test",
                     "security", "review", "deploy"]
    for stage_cmd in single_stages:
        p = sub.add_parser(stage_cmd, help=f"Run {stage_cmd} stage")
        p.add_argument("feature", nargs="?", default=None)
        p.add_argument("requirement", nargs="?", default=None)
        p.add_argument("--workflow", "-w", default=None, help="Workflow ID")

    args = parser.parse_args(argv)

    if args.command == "status":
        return cmd_status(store)
    elif args.command == "init":
        return cmd_init(store, project_root, args.feature, args.requirement)
    elif args.command == "run":
        feature = args.feature
        requirement = args.requirement or ""
        if not requirement:
            print("Usage: ai run <feature> <requirement> [--stages a b c]",
                  file=sys.stderr)
            return 2
        stages = getattr(args, "stages", None)
        return cmd_run(store, project_root, feature, requirement, stages)
    elif args.command in single_stages:
        stage_name = args.command
        wf = store.load_current()
        if wf is None:
            print("No active workflow. Start one with:  ai init <feature> <requirement>",
                  file=sys.stderr)
            return 2
        # if --workflow given, load that instead
        if args.workflow:
            wf = store.load(args.workflow)
            if wf is None:
                print(f"Workflow {args.workflow} not found.", file=sys.stderr)
                return 3
        runner = AgentRunner(project_root=project_root)
        stage_key = _stage_key(stage_name)
        wf.current_stage = stage_key
        wf.stages[stage_key].status = "in_progress"
        store.save(wf)

        try:
            result = invoke_agent(runner, _agent_kind_for(stage_key), stage_key, wf)
        except Exception as exc:
            print(f"Error in {stage_name}: {exc}", file=sys.stderr)
            wf.stages[stage_key].status = "blocked"
            wf.stages[stage_key].note = str(exc)
            wf.status = "blocked"
            store.save(wf)
            return 1

        if _is_block(result):
            wf.stages[stage_key].status = "blocked"
            wf.stages[stage_key].note = result.get("summary", str(result))
            wf.status = "blocked"
            store.save(wf)
            print(f"\n⚠ {STAGE_LABELS[stage_key]} blocked.")
            return 0

        wf.stages[stage_key].status = "completed"
        wf.stages[stage_key].output_path = result.get("output_path")
        wf.stages[stage_key].note = result.get("summary", "")
        store.save(wf)

        print(f"\n✓ {STAGE_LABELS[stage_key]} — {result.get('summary', '')}")

        if _needs_approval(result):
            print(f"\n⚠ {STAGE_LABELS[stage_key]} needs human approval before continuing.")
            wf.status = "blocked"
            store.save(wf)
            print("Resolve with:  ai approve <workflow_id>")
            return 0

        print(json.dumps(result, indent=2))
        return 0
    elif args.command == "context" and args.context_cmd == "scan":
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
        _print_context_summary(ctx, root)
        return 0
    else:
        parser.print_help()
        return 1


def _print_context_summary(ctx: FullContext, root: Path) -> None:
    """Print a human-readable summary of the scanned context."""
    print()
    print(f"Context scan: {root}")
    print(f"  Project  : {ctx.project.project_name} v{ctx.project.version}")
    print(f"  Language : {ctx.language.dominant_language or 'unknown'} "
          f"({ctx.language.total_source_files} files, {ctx.language.total_lines_of_code} LOC)")
    styles = ctx.architecture.detected_styles
    print(f"  Arch     : {', '.join(styles) if styles else 'none detected'} "
          f"(confidence {ctx.architecture.confidence:.0%})")
    print(f"  Deps     : {ctx.dependencies.total_dependencies} total, "
          f"lockfile={'yes' if ctx.dependencies.lockfile_present else 'no'}")
    if ctx.database.technologies:
        print(f"  Database : {', '.join(ctx.database.technologies)}")
    else:
        print("  Database : none detected")
    if ctx.api.styles:
        print(f"  API      : {', '.join(ctx.api.styles)}, "
              f"{len(ctx.api.endpoints)} endpoints")
    else:
        print("  API      : none detected")
    print(f"  Test     : {', '.join(ctx.test.frameworks)} "
          f"({ctx.test.test_file_count} test files)")
    print(f"  Git      : branch={ctx.git.current_branch} "
          f"commits={ctx.git.commit_count} authors={len(ctx.git.authors)}")


def _stage_key(cmd: str) -> str:
    mapping = {
        "analyze":     "analysis",
        "design":      "architecture",
        "plan":        "planning",
        "implement":   "development",
        "test":        "testing",
        "security":    "security",
        "review":      "review",
        "deploy":      "deployment",
    }
    return mapping[cmd]


if __name__ == "__main__":
    sys.exit(main())
