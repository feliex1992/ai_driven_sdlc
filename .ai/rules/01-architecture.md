# Architecture Rules

## 1. Respect Existing Architecture

The AI MUST identify the existing architectural style before implementing
new functionality.

Examples:

- Clean Architecture
- Layered Architecture
- Hexagonal Architecture
- Modular Monolith
- Microservices

Do not introduce a different architectural style without explicit approval.

---

## 2. Separation of Concerns

Each component MUST have a clear responsibility.

The AI SHOULD avoid:

- Business logic inside controllers
- Database access inside presentation layers
- Infrastructure concerns inside domain logic
- Large multi-purpose services

---

## 3. Dependency Direction

Dependencies SHOULD point toward abstractions and stable business logic.

High-level business rules SHOULD NOT depend directly on infrastructure details.

---

## 4. Existing Abstractions

The AI MUST reuse existing abstractions when appropriate.

Do not create duplicate:

- Services
- Repositories
- Utilities
- Validators
- Exception handlers
- Configuration mechanisms

without justification.

---

## 5. Architecture Changes

Any architectural change MUST include:

- Reason
- Alternatives considered
- Impact
- Migration strategy if applicable

Significant decisions MUST be recorded as an ADR.