# 0010. A recipe cannot be its own sub-recipe, directly or indirectly

Status: Accepted

## Context

Sub-recipes can themselves use sub-recipes (ADR 0006), so recipes form a web of
what-uses-what. Because every reference is pinned to an existing, frozen version, such a
web can always be resolved, even if recipes use each other in a loop. But a recipe that is
its own ingredient, directly or through others, has no sensible meaning for a baker.

## Decision

A recipe may not be used as a sub-recipe of itself, directly or through any chain of other
sub-recipes. Adding a reference that would complete such a loop is rejected. The check is
on recipes, not versions: a recipe using an earlier version of itself is also a loop.

## Alternatives

- Allow loops. Pinning already keeps every tree finite, so no check is needed, but a baker
  can build recipes that depend on themselves, which is confusing and has no real-world
  meaning.

## Consequences

- (+) Recipes always form a clear hierarchy of what uses what.
- (+) A recipe's full list of sub-recipes can be expanded without special handling for
  repeats.
- (−) Adding a reference means examining the chain of recipes beneath the chosen
  sub-recipe.
- (−) A recipe cannot build on an earlier version of itself, even where a baker might want
  that (for example, a starter recipe refreshed from its own previous batch).
