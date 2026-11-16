# Architecture Decision Records

One file per design decision, so humans and Claude sessions stay aligned. Terms are
defined in [`../glossary.md`](../glossary.md).

## Writing rules

- **Technology-agnostic.** State the general decision to follow when implementing. No
  framework, library, database product, file path, or table name. That detail lives in the
  glossary ("Here: …") and the code.
- **Only reference earlier ADRs.** Never point at a later one.
- **No future phases.** Write as if from scratch; do not discuss unbuilt work.
- **Alternatives are ones actually weighed.** Do not invent history.
- Say "business logic" for domain decisions. Input validation (does this request look
  well-formed?) is not business logic.
- One decision per ADR. Keep it under a page.
- **Accepted ADRs are frozen.** Never edit one, not even to fix wording. The only
  permitted change is its `Status` line. To change a decision, write a new ADR and set the
  old one to `Superseded by NNNN`. One exception has been made: ADR 0001 was revised in
  place (2026-11-15) to align with Evans' layered architecture, before any later work
  depended on its earlier wording.

## Template

```
# NNNN. Title
Status: Accepted | Superseded by NNNN

## Context        why we had to decide; the forces at play
## Decision       what we chose
## Alternatives   what we rejected and why (omit if none were weighed)
## Consequences   what gets easier, what gets harder
```

## Index

| # | Decision |
|---|---|
| [0001](0001-layered-architecture.md) | Layered architecture with dependencies pointing downward |
| [0002](0002-unit-of-work.md) | Unit of Work: one transaction per use case |
| [0003](0003-dtos-separate-from-domain.md) | API DTOs are separate from domain objects |
| [0004](0004-repository-interface-owned-by-domain.md) | The domain declares the repository interface |
| [0005](0005-testing-strategy.md) | Testing strategy: tests by layer, with a dedicated test database |
| [0006](0006-pinned-sub-recipe-references.md) | Sub-recipe references are pinned to a version |
| [0007](0007-draft-and-ready-versions.md) | Recipes have a Draft and numbered Ready versions |
| [0008](0008-only-ready-recipes-can-be-sub-recipes.md) | Only recipes with a Ready version can be used as sub-recipes |
| [0009](0009-no-sub-recipe-update-notifications.md) | A recipe is not told when its sub-recipes change |
| [0010](0010-no-circular-sub-recipes.md) | A recipe cannot be its own sub-recipe, directly or indirectly |
| [0011](0011-draft-and-ready-shown-separately.md) | A recipe's representation shows its Draft and latest Ready version separately |
