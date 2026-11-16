# 0012. The application layer declares the unit-of-work interface

Status: Accepted

## Context

A use case runs inside a unit of work (ADR 0002) that exposes the repositories it needs.
Use case tests run against an in-memory unit of work so they need no database (ADR 0005).
The production and in-memory implementations must behave alike, and nothing ties one to
the other.

## Decision

The application layer declares the unit-of-work interface: open a scope, expose the
repositories, commit on normal completion, discard on failure. Use cases depend only on
that interface. The production and in-memory implementations both implement it, and
conformance of each is checked automatically.

## Alternatives

- Use cases depend on the production class directly. ADR 0001 permits this, but the
  in-memory implementation can drift from the production one unnoticed.
- The domain declares the interface, as it does for repositories (ADR 0004). Rejected:
  only use cases consume a unit of work, and the transaction boundary is a use case's
  concern (ADR 0002), not the domain's. Declaring it in the domain would also put
  commit and discard vocabulary there and let a domain object import and call it. With the
  interface in the application layer, that import cannot be written.

## Consequences

- (+) A change to the unit of work surfaces as an error in every implementation.
- (+) Transaction vocabulary stays out of the domain.
- (−) One more file to maintain, kept in step with both implementations.
- (−) Like ADR 0004, it checks signatures, not behavior.
