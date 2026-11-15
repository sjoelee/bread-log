# 0003. API DTOs are separate from domain objects

Status: Accepted

## Context

The shapes clients send and receive and the objects the business logic operates on change
for different reasons. If one type served as both, renaming a field clients see, or adding
a response-only field, would force changes to the objects the business logic uses, and the
domain would depend on a validation framework.

## Decision

Two sets of types, converted by pure mapping functions.

- DTOs: request and response shapes, plus input validation, i.e. checks that a request is
  well-formed (non-empty names, allowed units, positive amounts). They belong to the
  interface layer.
- Domain objects: carry the business logic. Invariants that depend on a recipe's state
  (e.g. at most one Draft) are enforced here, never in a DTO, which only sees one request.
- Mappers: DTO ↔ domain in the interface layer; stored records → domain in the
  infrastructure layer.

Application services take and return domain objects only.

## Alternatives

- One type for API and domain. Fewer types and no mappers, but the domain depends on a
  validation framework and API changes become domain changes.
- Return domain objects directly to clients. Leaks internal fields and still needs
  framework-aware domain types.

## Consequences

- (+) The domain stays framework-free and testable on its own.
- (+) The API shape can change without touching the business logic.
- (−) A field exists in several places (DTO, domain, stored record); adding one means
  editing each and its mapper.
- (−) Mapper round-trips need tests so the copies do not drift.
