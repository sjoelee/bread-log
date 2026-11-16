# 0001. Layered architecture with dependencies pointing downward

Status: Accepted (revised 2026-11-15)

## Context

The system serves recipes to clients and stores them. The recipe business logic
(versioning, comparison, composition) is the part most likely to grow and the part most
worth testing. If it lives in the request handling or is mixed with storage code, every
test needs the whole system, and no rule can be changed without reading the code around it.

## Decision

Four layers, from top to bottom:

```
Interface       receives a request, converts between client-facing shapes (and their
                input validation) and domain objects, makes one application call,
                shapes the response
Application     one method per use case; kept thin: holds no business logic, only
                coordinates tasks and delegates the work to domain objects in the
                layer below
Domain          the business logic; free of storage, display and framework code
Infrastructure  generic technical capabilities that support the layers above:
                persistence, transactions, messaging
```

An element of a layer depends only on elements of its own layer or of the layers beneath
it, and calls them directly through their public interfaces. A lower layer does not depend
on a higher one; where it must communicate upward, it does so through an indirect
mechanism, such as an interface the higher layer declares or a callback.

One exception is accepted: repository implementations live in infrastructure and rebuild
domain objects from stored data, so infrastructure refers to domain types there. This is
our adaptation, not part of the layered pattern. A generic mapping tool would keep
infrastructure ignorant of the domain; we map by hand, so the mapping has to know both
sides and is kept in one place.

The interface layer contains no business logic. Failures are raised as intent-revealing
errors (not found, conflict, rule violated, storage failure) and translated to client
responses in one place.

## Alternatives

- Request handlers call storage directly. Least code, but business logic and storage are
  inseparable and nothing is testable without a database.
- One service holding business logic and storage code together. Fewer files, but the same
  coupling one level down.
- Dependency inversion on every layer: infrastructure depends on the domain and nothing
  may import it from above. Stricter, but needs extra interfaces and a separate wiring
  module, which this project does not need.
- Strict separation with no exception: the repository becomes a domain-layer class over a
  data-access service that exchanges plain rows. Infrastructure then knows nothing of the
  domain, but a storage change leaks into domain mapping, and the unit of work would need
  restructuring.

## Consequences

- (+) Business logic is unit-testable with no database or client.
- (+) The application layer can use infrastructure directly, for example to run several
  storage changes in one transaction.
- (+) The interface layer can wire concrete implementations without a special module.
- (+) Changing the storage technology means writing a new repository implementation
  behind the same interface.
- (−) More files and more translation code between layers.
- (−) A new feature touches several layers, even a small one.
- (−) Nothing stops the domain importing infrastructure if someone writes that import;
  the rule is kept by review, not by the language.
- (−) The repository exception means infrastructure is not fully ignorant of the domain.
