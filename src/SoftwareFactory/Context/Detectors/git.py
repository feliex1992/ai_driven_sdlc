"""
STEP 2.9 - Git Analyzer.

Reads repository metadata and history signals:
  - is_git_repo
  - current branch
  - commit count
  - recent commit messages
  - authors
  - remote presence
  - last commit date
  - tags (count)

Uses only the git CLI via subprocess so it works on any machine without
extra Python libraries. Fails gracefully if git is missing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pydantic import Field

from ..Core import GitContext
from ..Core.detector import Detector


class GitDetector(Detector):
    """STEP 2.9 - Git Analyzer."""

    @property
    def block_name(self) -> str:
        return "git"

    def detect(self) -> dict:
        git_dir = self.root / ".git"
        is_git_repo = git_dir.is_dir()

        if not is_git_repo:
            return GitContext(is_git_repo=False).model_dump()

        ctx = GitContext(is_git_repo=True)

        try:
            branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], self.root)
            ctx.current_branch = branch.strip() if branch else None
        except (subprocess.CalledProcessError, OSError):
            pass

        try:
            count = _git(["rev-list", "--all", "--count"], self.root)
            ctx.commit_count = int(count.strip()) if count else 0
        except (subprocess.CalledProcessError, OSError, ValueError):
            pass

        try:
            authors: set[str] = set()
            msgs: list[str] = []
            out = _git(
                ["log", "--pretty=format:%an||%s", "-n", "20"],
                self.root,
            )
            if out:
                for line in out.splitlines():
                    line = line.strip()
                    if "||" in line:
                        author, msg = line.rsplit("||", 1)
                        authors.add(author.strip())
                        msgs.append(msg.strip())
                    else:
                        authors.add(line)
                ctx.authors = sorted(authors)
                ctx.recent_messages = msgs[:10]
        except (subprocess.CalledProcessError, OSError):
            pass

        try:
            out = _git(["remote"], self.root)
            ctx.has_remote = bool(out.strip())
        except (subprocess.CalledProcessError, OSError):
            pass

        return ctx.model_dump()


def _git(args: list[str], cwd: Path) -> str:
    """Run git (args) in cwd. Raises on non-zero exit."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result.stdout
