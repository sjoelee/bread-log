# 0004. The domain declares the repository interface

Status: Accepted

## Context

Application code needs to load and save recipes without knowing storage details, and its
tests should run without a database. There are two implementations that must behave alike:
the production store and an in-memory one for tests.

## Decision

The domain declares the repository interface: the operations it needs from storage. The
application layer depends only on that interface. The production implementation and the
in-memory test implementation both implement it, and conformance of every implementation,
including the test one, is checked automatically.

## Alternatives

- No interface; the application layer uses the production class directly. Fewer files, but
  the application layer depends on infrastructure, and the test implementation can drift
  from it unnoticed.

## Consequences

- (+) Dependencies point toward the domain (ADR 0001).
- (+) A change to an operation's signature surfaces as an error in every implementation.
- (−) One more file to maintain, and it must be kept in step with both implementations.
- (−) An interface checks signatures, not behavior. The implementations can still return
  different results for the same call.
