# 0006. Sub-recipe references are pinned to a version

Status: Accepted

## Context

A recipe can use other recipes as sub-recipes (a tangzhong inside a milk bread). Each
sub-recipe is itself versioned and edited on its own. We must decide what a reference
points at, and how references are stored.

## Decision

A reference is pinned: it records the child recipe and a specific child version, never
"latest" (see glossary: Pinned reference). References are stored as individual records
owned by the parent version, each linked to an existing child recipe and child version, so
the storage layer can enforce that links are valid and can look references up from the
child's side.

## Alternatives

- Follow the child's latest Ready version. Parents change silently when a child is
  promoted, so a recipe that worked yesterday can differ today and old bakes cannot be
  reproduced.
- Embed references inside the parent version's own content, like its ingredients. Simpler
  to read and write, but the storage layer cannot enforce that they point at real
  versions, and "which recipes use this one?" requires scanning every version.

## Consequences

- (+) A promoted version is a frozen snapshot: it always resolves to the same tree of
  child versions.
- (+) "Which recipes import this one?" and a transitive dependency tree are simple queries.
- (+) A reference to a version that does not exist is rejected.
- (−) A parent is not told when a child gains a newer version; the baker repoints the pin
  by hand.
- (−) Reading a recipe takes an extra lookup for its references.
- (−) Writes must be ordered carefully, because versions, recipes and references depend on
  each other.
