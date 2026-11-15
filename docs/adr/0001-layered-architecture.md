# 0001. Layered architecture with dependencies pointing toward the domain

Status: Accepted

## Context

The system serves recipes to clients and stores them. The recipe business logic
(versioning, comparison, composition) is the part most likely to grow and the part most
worth testing. If it lives in the request handling or is mixed with storage code, every
test needs the whole system, and no rule can be changed without reading the code around it.

## Decision

Four layers. Dependencies point toward the domain.

```
Interface       the boundary clients talk to: receives a request, converts between
                client-facing shapes (and their input validation) and domain objects,
                makes one application call, shapes the response
Application     one method per use case; coordinates the work, holds no business logic
Domain          the business logic; pure, no I/O, no dependence on a web, validation
                or storage framework
Infrastructure  storage and other external systems
```

The domain depends on nothing. Application depends only on the domain. Interface depends
on application and domain. Infrastructure depends on the domain, by implementing the
interfaces the domain declares.

The interface layer contains no business logic, storage code, or transaction handling.
Failures are raised as intent-revealing errors (not found, conflict, rule violated,
storage failure) and translated to client responses in one place.

## Alternatives

- Request handlers call storage directly. Least code, but business logic and storage are
  inseparable and nothing is testable without a database.
- One service holding business logic and storage code together. Fewer files, but the same
  coupling one level down.

## Consequences

- (+) Business logic is unit-testable with no database or client.
- (+) Storage or framework changes stay inside one layer.
- (−) More files and more translation code between layers.
- (−) A new feature touches several layers, even a small one.
