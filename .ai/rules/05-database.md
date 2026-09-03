# Database Rules

## Schema Changes

Database schema changes MUST be performed through migrations
or the project's established database deployment mechanism.

---

## Backward Compatibility

Database changes SHOULD consider compatibility with:

- Existing application versions
- Existing data
- Existing queries
- Existing integrations

---

## Destructive Changes

The AI MUST NOT automatically execute destructive operations such as:

- DROP TABLE
- DROP COLUMN
- TRUNCATE
- DELETE without appropriate filtering

Production destructive changes require human approval.

---

## Data Integrity

Consider:

- Primary keys
- Foreign keys
- Unique constraints
- Nullability
- Indexes
- Transaction boundaries

---

## Performance

Before adding indexes or changing queries, consider:

- Query frequency
- Existing indexes
- Data volume
- Execution plan
- Write/read trade-offs