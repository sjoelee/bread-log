# 0014. A Draft can be discarded

Status: Accepted

## Context

A baker may abandon a Draft. A recipe has at most one Draft (ADR 0007), and a recipe with
neither a Draft nor a Ready version never exists (ADR 0011).

## Decision

The baker can discard a recipe's Draft. The recipe is then left with its Ready versions,
unchanged, and no Draft. If the recipe has no Ready version, discarding its Draft deletes
the recipe. Deleting a recipe is a separate action that removes the recipe with its Draft
and all its Ready versions.

## Alternatives

- Refuse to discard the Draft of a recipe with no Ready version, and require deleting the
  recipe instead. Keeps discard and delete distinct, but leaves one case where discard is
  unavailable.

## Consequences

- (+) A baker can abandon an edit and return to the last release.
- (+) No recipe is left with nothing in it.
- (−) Discarding the Draft of a new recipe deletes the recipe; a client must make that
  clear before the baker confirms.
- (−) A discarded Draft cannot be recovered.
