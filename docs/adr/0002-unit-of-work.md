# 0002. Unit of Work: one transaction per use case

Status: Accepted

## Context

A use case often writes several records across storage, for example saving a recipe's
details, appending a version and moving the current-version pointer. If each storage call
committed on its own, a failure partway would leave the data half-written. Repositories
also cannot know where a use case begins and ends.

## Decision

The application layer owns the transaction. Each use case runs inside one unit of work: a
scope that gives every repository the same storage session, commits when the use case
completes normally, discards all of its changes if it fails, and always releases the
session. Repositories never commit. The interface layer never sees the unit of work.

## Alternatives

- Each repository operation commits itself. Simple, but a multi-step use case is not
  atomic, and every operation must remember to commit.

## Consequences

- (+) A use case is all-or-nothing.
- (+) "Forgot to commit" cannot happen in a repository.
- (−) Every use case must fit in a single scope; work spanning two scopes is two
  transactions.
- (−) Reads also go through a unit of work, so they take a storage session and finish with
  a commit that has nothing to write.
