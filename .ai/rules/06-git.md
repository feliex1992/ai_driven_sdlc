# Git Rules

## Branching

AI MUST work on the appropriate feature or task branch.

Do not directly modify the production/main branch unless explicitly
authorized.

---

## Commits

Commits SHOULD represent a logical change.

Prefer:

feat:
fix:
refactor:
test:
docs:
chore:
security:

---

## Commit Safety

The AI MUST NOT execute destructive Git operations without approval.

Examples:

- git reset --hard
- git clean -fd
- force push
- deleting branches

---

## Pull Request

A completed task SHOULD provide:

- Summary
- Changes
- Tests
- Security findings
- Known limitations
- Related task / requirement