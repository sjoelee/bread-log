# 0009. A recipe is not told when its sub-recipes change

Status: Accepted

## Context

Sub-recipe references are pinned to a version (ADR 0006). A sub-recipe keeps being edited
and promoted after others have pinned it, so recipes will often reference a version that is
no longer the newest.

## Decision

Nothing tells a recipe that a sub-recipe it uses has a newer Ready version. The baker
moves a pin by editing the reference, which changes the parent's Draft; the parent's
released versions never change.

## Alternatives

- Flag recipes whose sub-recipes have newer Ready versions ("updates available"). Helps a
  baker notice stale references, but needs a rule for what counts as stale and invites the
  question of when to update automatically.

## Consequences

- (+) A recipe changes only when its baker changes it, so what a baker made last month
  still means the same thing.
- (+) No tracking of which recipe is behind which.
- (−) A baker can keep using an old sub-recipe version without realising a newer one
  exists. Finding out means looking at the sub-recipe.
