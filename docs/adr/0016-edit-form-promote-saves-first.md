# 0016. The edit form's Promote saves the Draft first

Status: Accepted

## Context

Promotion acts on the saved Draft (ADR 0015). A baker editing in the form expects one
action to release what they see.

## Decision

The edit form's Promote first saves the form's content to the Draft, then promotes it.
The two remain separate operations, and promotion still never receives content.

## Alternatives

- Promote disabled until the Draft is saved (ADR 0015's two-action flow). Rejected as
  friction.

## Consequences

- (+) One click releases what is on screen.
- (−) The baker releases edits they have not separately saved.
- (−) The form must know, before saving, whether its content differs from the latest
  Ready version; otherwise a rejected promotion would leave behind a saved Draft
  identical to it.
