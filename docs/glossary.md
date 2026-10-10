# Glossary

Shared vocabulary for the bread-log recipe domain. Use these exact terms in
code, comments, commits, and conversation so humans and Claude sessions stay aligned.

Status tags:
- **(live)** — exists in the codebase today
- **(target)** — agreed design, not built yet (see `~/.claude/plans/synchronous-shimmying-sedgewick.md`)

---

## Domain language (recipes & baking)

### Recipe **(live)**
The named thing — "Country Sourdough" — and its stable identity across edits: name,
category, and notes. Like a document across its revisions, it persists while its content
changes. Its ingredients and steps live on its *versions*; the current one is
`recipe.current_version`. Table: `recipes`. The aggregate root (see *Aggregate / aggregate root*): every change
goes through it.

### Recipe version **(live)**
One snapshot of a recipe's content: its ingredients, steps, and (target) sub-recipe
references, at a point in time. This is what a baker means by "the recipe" when looking at
a single version. Table: `recipe_versions`. Immutable once Ready (see *Draft* / *Ready*);
today every save creates a new one, (target) that changes — see *promotion*. An **entity**
— it has its own id, which sub-recipe references pin. A *Draft* is also a version
(the one in progress); a *Ready version* is the numbered, frozen kind. (Sometimes called a
"recipe specification" in design discussion — same thing.)

### Recipe history **(concept — not a modeled type)**
The set of a recipe's **Ready** versions, ordered by time. The Draft is not part of
history — it is shown separately. **Deliberately not an entity or value
object** — it has no identity of its own (1:1 with the recipe) and no behavior. It is a
repository query: `RecipeRepository.get_versions(recipe_id) -> list[RecipeVersion]` (target: Ready only). The
`Recipe` aggregate holds only the current version (+ the Draft, in Part II); history is
loaded on demand. Only promote it to a value object if real domain logic over the version
sequence appears (e.g. trend analysis, adjacent-version diffs).

### Draft **(target)**
The single mutable working copy of a recipe. Editing changes the Draft in place — it does
**not** create a new version. `recipe_versions.state = 'draft'`, `version_number = NULL`.
A recipe has exactly **0 or 1** Drafts.

### Ready **(target)**
A recipe version that has been promoted: frozen, numbered, and usable as a sub-recipe by other recipes.
`recipe_versions.state = 'ready'`. The opposite of Draft.

### Promotion / promote **(target)**
The Draft → Ready transition. This is the **only** thing that assigns a `version_number`
(`MAX(existing ready number) + 1`). Triggered explicitly by the user, who supplies a
*release note*. Method: `Recipe.promote(release_note)`.

### Sub-recipe **(target)**
An ordinary recipe that another recipe uses — e.g. a tangzhong used by a milk bread. It is
prepared separately and reused; contrast with an *inline preparation*. A recipe can only be
used as a sub-recipe if it has at least one Ready version (adding one that doesn't raises
`SubRecipeNotReady`); the sub-recipe picker lists only such recipes.

### Sub-recipe reference **(target)**
One use of a sub-recipe inside a recipe version: a *pin* to a specific Ready version of the
child, plus the amount, unit, and label for this use. Value object `SubRecipeRef`; table
`recipe_sub_recipe_refs`. This is what scaling lives on — the child recipe itself is never
changed. (Not to be confused with the everyday word "component", e.g. "the filling"; that
is not a modeled concept.)

### Inline preparation **(target)**
A step that cooks or transforms leaf ingredients *within this recipe* (brown the butter,
toast the seeds). Not its own recipe, not versioned — just a step with `kind = 'prep'`.
The test vs a sub-recipe: *would you ever iterate it on its own, or use it in another recipe?*
Yes → sub-recipe. No → inline preparation.

### Pinned reference / pin **(target)**
A sub-recipe reference stores the child's `recipe_id` **and** a specific `child_version_id`. It does not
float to "latest", and nothing tells the parent when the child gets a newer Ready version.
Analogous to a lockfile entry. The baker can repoint a pin to any Ready version of the same
child by editing the reference; that edits the parent's Draft, and a new parent version
exists only once it is promoted.

### Leaf ingredient **(live)**
A single quantity of one thing: `{name, amount, unit, type, notes}`. `type` is `flour` or
`other` (was `flour | liquid | preferment | fat | other`; narrowed on the frontend).
Stored in `recipe_versions.ingredients` (JSONB).

### Step **(live)** / step `kind` + `uses` **(target)**
An ordered instruction. Today: `{order, text}` free text. (target) `{order, text, kind, uses[]}`
where `kind ∈ prep | mix | ferment | shape | bake | finish` and `uses[]` names the
ingredient/sub-recipe ref ids the step acts on. Stored in `recipe_versions.instructions` (JSONB).

### Release note **(target)**
Free text the user types at promotion, describing what changed. Stored in
`recipe_versions.description`.

### Notes **(target)**
One free-form text field on the recipe for tips, warnings, anything. Reuses the existing
`recipes.description` column, relabeled "Notes" in the UI.

### Change summary **(live)**
Machine-generated counts of what changed between versions
(`{ingredients: {added, removed, modified}, steps: {...}, total_changes}`). Stored in
`recipe_versions.change_summary`. (target) computed at promotion, diffing against the previous
Ready version.

### Version diff **(live)**
The structured comparison of two recipe versions (ingredients added/removed/modified,
steps added/removed/modified/reordered). Endpoint:
`GET /recipes/{id}/versions/{v1}/diff/{v2}`. Logic: `backend/domain/versioning.py`
(moved there from `recipe_versioning.py` in Stage 2).

## Deprecated / legacy terms (don't use going forward)

- **`DBConnector`** — the ~950-line god object holding all raw SQL. Being dismantled across
  Stages 4–7 into repositories.
- **`backend/recipe_versioning.py`** — moved to `backend/domain/versioning.py` in Stage 2.
- **`DBConnector._compute_timing_status` / `service.calculate_timing_status`** — duplicate
  "is this timing complete?" logic. Left as-is for now; consolidated during Part IV.
- **`force_major` / major-minor versioning** — vestigial. Version
  numbers are a single incrementing int, and (target) advance only on promotion.
- **`account_makes`, `dough_makes`, `DoughMake`, `AccountMake`** — legacy tables/models, not
  the current data model.
- **`fridge_ts`** — renamed to `final_proof_ts`.
