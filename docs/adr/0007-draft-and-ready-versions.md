# 0007. Recipes have a Draft and numbered Ready versions

Status: Accepted

## Context

If every save of a recipe created a new numbered version, history would fill with
half-finished states, version numbers would lose meaning, and any of those states could be
used by another recipe. Bakers iterate on a recipe many times before it is good.

## Decision

A recipe's content exists in one of two states.

- Draft: the single mutable working copy. A recipe has at most one. Editing changes the
  Draft in place and never creates a version. It has no version number.
- Ready: a frozen, numbered version. Ready versions are never modified.

Promotion turns the Draft into the next Ready version, numbered one higher than the
recipe's latest Ready version (1 if it has none), and records a release note supplied by
the baker and a summary of what changed since the previous Ready version. Editing a recipe
whose latest version is Ready starts a new Draft copied from it. A new recipe begins as a
Draft with no Ready version. Version numbers are plain increasing integers; there is no
major/minor scheme.

## Alternatives

- Every save creates a new numbered version. History becomes noise and every intermediate
  state is importable.
- Major/minor numbering. Needs a rule for deciding which kind of change a save is; that
  has no meaning when numbers are assigned only on promotion.

## Consequences

- (+) History lists only versions the baker chose to release.
- (+) Other recipes can only depend on stable, frozen versions.
- (+) Editing freely cannot disturb anything that already depends on a Ready version.
- (−) Every place that shows or lists a recipe must handle two states, and a recipe with no
  Ready version.
- (−) The Draft is mutable while everything else is frozen, so history views must show it
  apart from released versions.
