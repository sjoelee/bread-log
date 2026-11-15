# 0008. Only recipes with a Ready version can be used as sub-recipes

Status: Accepted

## Context

A sub-recipe reference is pinned to a specific version (ADR 0006), and a pin is only
meaningful if the version it points at cannot change. A Draft is mutable and has no number
(ADR 0007), so it cannot be pinned. A brand-new recipe has only a Draft.

## Decision

A recipe may be used as a sub-recipe only if it has at least one Ready version, and a
reference may only point at a Ready version. Attempting otherwise is rejected, not warned
about. Anywhere a baker chooses a sub-recipe, only eligible recipes are offered.

## Consequences

- (+) Every reference resolves to frozen content, so a parent's full tree of versions is
  always reproducible.
- (+) A baker's choices are limited to recipes that are ready to be reused, so there is
  nothing to explain or warn about.
- (−) A baker must promote a recipe at least once before using it elsewhere, even to try it
  out.
- (−) A new recipe cannot be composed from other recipes it depends on until those have
  been promoted.
