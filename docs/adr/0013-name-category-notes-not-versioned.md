# 0013. A recipe's name, category and notes are not versioned

Status: Accepted

## Context

A recipe's content is versioned through a Draft and Ready versions (ADR 0007). Some of a
recipe's attributes describe the recipe as a whole rather than one version of it. They
must either change through the Draft and freeze on promotion, or change directly.

## Decision

A recipe's name, category and notes belong to the recipe, not to its versions. They are
edited directly, take effect immediately, and are not part of a Draft or a Ready version.
Names need not be unique.

## Alternatives

- Version them with the content. Each Ready version would record the name and category it
  was released under, but renaming or recategorizing would require a Draft and a
  promotion, and two Ready versions could differ only in their notes.

## Consequences

- (+) Fixing a name or adding a note never creates a Draft or needs a promotion.
- (+) Versions differ only in content: ingredients and steps.
- (−) A Ready version does not record the name or category it had when released; history
  shows the current values.
- (−) Two recipes can share a name, so anywhere a baker picks a recipe by name, two may
  look alike.
