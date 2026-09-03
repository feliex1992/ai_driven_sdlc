# Core Engineering Rules

## Purpose

These rules define the fundamental behavior of all AI agents
working on this software project.

All AI agents MUST follow these rules.

---

## 1. Understand Before Changing

Before modifying the codebase, the AI MUST:

1. Understand the requested change.
2. Inspect the relevant existing implementation.
3. Identify dependencies and potential impact.
4. Identify applicable architecture and coding rules.
5. Clearly state assumptions when information is missing.

The AI MUST NOT modify code based only on the user's initial request
when additional repository context is required.

---

## 2. Minimal Change

The AI MUST make the smallest change required to satisfy the task.

The AI SHOULD NOT:

- Modify unrelated files.
- Refactor unrelated code.
- Change existing behavior without justification.
- Introduce new dependencies without justification.
- Rewrite existing implementations unnecessarily.

---

## 3. Follow Existing Patterns

Before introducing a new pattern, the AI MUST inspect the existing
codebase for an established pattern.

Existing project conventions take precedence over generic AI preferences.

---

## 4. No Assumptions Without Evidence

The AI MUST NOT invent:

- APIs
- database tables
- configuration
- business rules
- dependencies
- infrastructure
- external services

When information is unavailable, the AI MUST explicitly identify
the assumption.

---

## 5. Traceability

Every significant implementation MUST be traceable to:

Requirement
    ↓
Design
    ↓
Task
    ↓
Implementation
    ↓
Test
    ↓
Review

---

## 6. Preserve Existing Behavior

Existing functionality MUST remain unchanged unless the task explicitly
requires a behavioral change.

If existing behavior must change, the AI MUST identify:

- What changes
- Why it changes
- Potential impact
- Required tests

---

## 7. Evidence Over Opinion

AI decisions SHOULD be based on:

1. Existing code
2. Existing documentation
3. Existing tests
4. Project rules
5. Explicit requirements

Generic AI knowledge has lower priority than repository-specific evidence.

---

## 8. Human Approval

The AI MUST request human approval before:

- Destructive database changes
- Production deployment
- Security exceptions
- Breaking API changes
- Major architecture changes
- Removing existing functionality