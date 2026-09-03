# AI Engineering Context

This directory contains the rules, context, tasks, decisions,
and reports used by AI agents working on this project.

## Directory Structure

### rules/

Engineering rules that MUST be followed by AI agents.

### context/

Project-specific context and supporting information.

### tasks/

Task definitions and implementation requirements.

### decisions/

Architecture Decision Records (ADR).

### reports/

Analysis, testing, security, and review reports.

---

## Rule Priority

When rules conflict, use this priority:

1. Explicit user requirement
2. Security requirements
3. Project-specific rules
4. Architecture decisions
5. Existing project conventions
6. General engineering best practices
7. AI preferences

---

## AI Behavior

AI agents MUST:

1. Read relevant rules before working.
2. Inspect existing code before modifying it.
3. Avoid unrelated changes.
4. Explain assumptions.
5. Produce evidence for important decisions.
6. Run appropriate tests after implementation.
7. Report failures instead of hiding them.

AI agents MUST NOT:

- Invent requirements.
- Invent architecture.
- Ignore existing conventions.
- Disable tests to make builds pass.
- Hide security findings.
- Perform destructive production actions without approval.
