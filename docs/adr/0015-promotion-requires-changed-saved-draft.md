# 0015. Promotion requires a saved Draft that differs from the latest Ready version

Status: Accepted

## Context

Promotion turns the Draft into the next Ready version (ADR 0007). A Draft can end up
identical to the latest Ready version, for example after edits are undone, and the baker
may have unsaved changes when they choose to promote.

## Decision

Promotion acts only on the saved Draft; content is saved to the Draft first and is never
supplied with the promotion itself. A Draft can be promoted only if its content differs
from the latest Ready version. A recipe with no Ready version can always promote its
Draft. The release note is optional.

## Alternatives

- Allow promoting an unchanged Draft, with a warning. Produces Ready versions identical to
  their predecessor.
- Accept content with the promotion and save and promote it in one step. Fewer actions,
  but unsaved changes could be released without the baker reviewing them as a Draft.
- A required release note. Rejected as friction for small changes.

## Consequences

- (+) Every Ready version differs from the one before it.
- (+) What gets released is exactly what the baker saved.
- (−) Promoting takes two actions: save, then promote.
- (−) A Ready version may have no release note.
