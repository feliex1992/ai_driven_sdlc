"""
AI Software Factory command-line interface.

This is STEP 3 — the control plane for the factory. It delegates to
`run.py`, which implements:

    ai status                     Show current workflow / stage status
    ai init [feature] [requirement]   Start a new workflow
    ai run <feature> [requirement]    Run full pipeline end-to-end
    ai analyze|design|plan|implement|test|security|review|deploy   Run single stage

The Context Engine (`ai context scan`) is also available under this CLI.

Rules: 00-core — understand before changing. The CLI reads repos and
writes structured context; it never mutates the target repo.
"""

from __future__ import annotations

from .run import main


if __name__ == "__main__":
    sys.exit(main())
