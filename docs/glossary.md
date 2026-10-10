# Glossary

Shared vocabulary for the bread-log recipe domain. Use these exact terms in
code, comments, commits, and conversation so humans and Claude sessions stay aligned.

---

## Domain language (recipes & baking)

### Recipe
The named thing — "Country Sourdough" — and its stable identity across edits: name,
category, and notes. Like a document across its revisions, it persists while its content
changes. Its ingredients and steps live on its *versions*; the current one is
`recipe.current_version`. Table: `recipes`. The aggregate root (see *Aggregate / aggregate root*): every change
goes through it.

### Recipe version
One snapshot of a recipe's content: its ingredients, steps, and sub-recipe
references, at a point in time. This is what a baker means by "the recipe" when looking at
a single version. Table: `recipe_versions`. Immutable once Ready (see *Draft* / *Ready*);
every save currently creates a new one; under the Draft/Ready model only *promotion* does. An **entity**
— it has its own id, which sub-recipe references pin. A *Draft* is also a version
(the one in progress); a *Ready version* is the numbered, frozen kind. (Sometimes called a
"recipe specification" in design discussion — same thing.)

### Recipe history
The set of a recipe's **Ready** versions, ordered by time. The Draft is not part of
history — it is shown separately. **Deliberately not an entity or value
object** — it has no identity of its own (1:1 with the recipe) and no behavior. It is a
repository query: `RecipeRepository.get_versions(recipe_id) -> list[RecipeVersion]` (Ready versions only). The
`Recipe` aggregate holds only the current version (+ the Draft, in Part II); history is
loaded on demand. Only promote it to a value object if real domain logic over the version
sequence appears (e.g. trend analysis, adjacent-version diffs).

### Draft
The single mutable working copy of a recipe. Editing changes the Draft in place — it does
**not** create a new version. `recipe_versions.state = 'draft'`, `version_number = NULL`.
A recipe has exactly **0 or 1** Drafts.

### Ready
A recipe version that has been promoted: frozen, numbered, and usable as a sub-recipe by other recipes.
`recipe_versions.state = 'ready'`. The opposite of Draft.

### Promotion / promote
The Draft → Ready transition. This is the **only** thing that assigns a `version_number`
(`MAX(existing ready number) + 1`). Triggered explicitly by the user, who supplies a
*release note*. Method: `Recipe.promote(release_note)`.

### Sub-recipe
An ordinary recipe that another recipe uses — e.g. a tangzhong used by a milk bread. It is
prepared separately and reused; contrast with an *inline preparation*. A recipe can only be
used as a sub-recipe if it has at least one Ready version (adding one that doesn't raises
`SubRecipeNotReady`); the sub-recipe picker lists only such recipes.

### Sub-recipe reference
One use of a sub-recipe inside a recipe version: a *pin* to a specific Ready version of the
child, plus the amount, unit, and label for this use. Value object `SubRecipeRef`; table
`recipe_sub_recipe_refs`. This is what scaling lives on — the child recipe itself is never
changed. (Not to be confused with the everyday word "component", e.g. "the filling"; that
is not a modeled concept.)

### Inline preparation
A step that cooks or transforms ingredients *within this recipe* (brown the butter,
toast the seeds). Not its own recipe, not versioned — just a step with `kind = 'prep'`.
The test vs a sub-recipe: *would you ever iterate it on its own, or use it in another recipe?*
Yes → sub-recipe. No → inline preparation.

### Pinned reference / pin
A sub-recipe reference stores the child's `recipe_id` **and** a specific `child_version_id`. It does not
float to "latest", and nothing tells the parent when the child gets a newer Ready version.
Analogous to a lockfile entry. The baker can repoint a pin to any Ready version of the same
child by editing the reference; that edits the parent's Draft, and a new parent version
exists only once it is promoted.

### Step
One instruction in a recipe version, with an order number and the instruction text.
Once steps are structured, each also has a `kind` (`prep`, `mix`, `ferment`, `shape`, `bake`
or `finish`) and `uses`, the ingredients or sub-recipe references it acts on. Stored in
`recipe_versions.instructions` (JSONB).

### Release note
Free text the user types at promotion, describing what changed. Stored in the
version's `recipe_versions.description` column (not the recipe's `description`, which holds *Notes*).

### Notes
One free-form text field on the recipe for tips, warnings, anything. Reuses the existing
`recipes.description` column (the recipe's, not the version's — that one holds the *release note*),
relabeled "Notes" in the UI.

### Change summary
Machine-generated counts of what changed between versions
(`{ingredients: {added, removed, modified}, steps: {...}, total_changes}`). Stored in
`recipe_versions.change_summary`. Computed at promotion, diffing against the previous
Ready version.

### Version diff
The structured comparison of two recipe versions (ingredients added/removed/modified,
steps added/removed/modified/reordered). Endpoint:
`GET /recipes/{id}/versions/{v1}/diff/{v2}`. Logic: `backend/domain/versioning.py`
(moved there from `recipe_versioning.py` in Stage 2).
