# Coding Rules

## General

Code MUST prioritize:

1. Correctness
2. Readability
3. Maintainability
4. Testability
5. Performance

Do not optimize prematurely.

---

## Existing Convention

The AI MUST follow existing:

- Naming conventions
- Formatting
- Error handling
- Logging
- Dependency injection
- Async patterns
- Project structure

---

## Code Quality

Avoid:

- Unnecessary abstraction
- Over-engineering
- Duplicate logic
- Dead code
- Magic values
- Excessive method complexity

---

## Dependencies

New dependencies require justification.

Before adding a dependency, check whether the existing codebase
already provides equivalent functionality.

---

## Error Handling

Errors MUST be handled consistently with existing project conventions.

The AI MUST NOT silently swallow exceptions.

---

## Logging

Logs MUST NOT contain:

- Passwords
- Access tokens
- API keys
- Secrets
- Sensitive personal information

Use existing logging infrastructure whenever available.