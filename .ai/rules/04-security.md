# Security Rules

## General Principle

Security MUST be considered during:

- Design
- Development
- Testing
- Code Review
- Deployment

---

## Input

All external input MUST be considered untrusted.

Validate input according to business and technical requirements.

---

## Authentication

Protected functionality MUST require appropriate authentication.

---

## Authorization

Authentication alone is NOT sufficient.

The AI MUST verify that the authenticated actor has permission
to access or modify the requested resource.

---

## Data Protection

Never expose:

- Passwords
- Tokens
- API keys
- Connection strings
- Secrets
- Sensitive internal information

---

## Database

Use parameterized queries or the project's safe database abstraction.

Never construct SQL using unsafe string concatenation.

---

## Dependencies

New dependencies SHOULD be checked for known security risks.

---

## Security Findings

Security findings MUST be classified:

- Critical
- High
- Medium
- Low
- Informational

Critical and High findings MUST block production deployment
unless explicitly approved by a human.