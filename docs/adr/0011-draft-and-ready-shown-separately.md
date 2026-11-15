# 0011. A recipe's representation shows its Draft and latest Ready version separately

Status: Accepted

## Context

A recipe can have only a Draft (new), only Ready versions (released), or both (released and
being edited) (ADR 0007). Clients need to edit the Draft, show what is released, and
compare the two.

## Decision

A recipe's representation to clients carries two separate, optional parts: its latest
Ready version and its Draft. Each is present when it exists and absent when it does not;
neither is substituted for the other. A recipe with neither part never exists.

## Alternatives

- One "working version" that is the Draft if present, otherwise the latest Ready, with a
  state flag. Simpler for an edit screen, but the same part means different things
  depending on the flag, and the released version is hidden whenever a Draft exists.

## Consequences

- (+) The two states stay distinct; nothing is shown as released that is not.
- (+) A client can compare the Draft with the latest release from a single response.
- (−) Clients must handle either part being absent.
- (−) The response is larger for a recipe being edited, since it carries both.
