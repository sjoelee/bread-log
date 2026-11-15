# 0005. Testing strategy: tests by layer, with a dedicated test database

Status: Accepted

## Context

Business logic should be testable with no I/O, and storage code can only be verified
against a real database. Tests that share a database with development mix test records
with real recipes, and a destructive schema change made for development also destroys test
data.

## Decision

Tests mirror the layers:

- Domain: no I/O. Plain objects in, results out.
- Application: in-memory implementations of the repository and unit of work (ADR 0004).
- Infrastructure and interface: a real database of the same kind as production. No mocking
  of the database.

Storage-touching tests run against a dedicated test database, built from the schema
definition. The test run refuses to start unless the configured database is identifiably a
test database.

## Alternatives

- Test against the development database. No setup, but tests can leave records behind, can
  be affected by real data, and share its fate when the schema is recreated.

## Consequences

- (+) Tests cannot touch development data, and schema changes can be tried safely.
- (+) The guard stops a misconfigured run from using the wrong database.
- (−) A manual setup, repeated whenever the schema definition changes.
- (−) Tests that need the database still depend on it being available.
