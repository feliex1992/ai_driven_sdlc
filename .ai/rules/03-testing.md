# Testing Rules

## Testing Requirement

Every new business behavior SHOULD have automated tests.

Tests MUST verify behavior, not implementation details.

---

## Test Levels

Use the appropriate level:

- Unit Test
- Integration Test
- API Test
- End-to-End Test

Prefer the lowest level that provides sufficient confidence.

---

## Required Scenarios

For business logic, consider:

- Happy path
- Invalid input
- Boundary conditions
- Authorization
- Failure scenarios
- Existing behavior regression

---

## Existing Tests

Before modifying functionality, the AI MUST inspect existing tests.

Existing tests MUST NOT be deleted merely to make the new implementation pass.

---

## Test Failure

When tests fail, the AI MUST determine whether:

1. Implementation is incorrect.
2. Test is incorrect.
3. Requirement changed.
4. Existing behavior was unintentionally changed.

Do not blindly modify tests to match the implementation.