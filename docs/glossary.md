# Glossary

Shared vocabulary for the bread-log domain and its architecture. Use these exact terms in
code, comments, commits, and conversation so humans and Claude sessions stay aligned.

Status tags:
- **(live)** — exists in the codebase today
- **(target)** — agreed design, not built yet (see `~/.claude/plans/synchronous-shimmying-sedgewick.md`)

---

## Part A — Domain language (recipes & baking)

### Recipe **(live)**
The stable identity of a formula — its name, category, and notes. It does **not** hold
ingredients or steps directly; those live in its versions. Table: `recipes`. The aggregate
root (see Part B).

### Recipe version **(live)**
An immutable snapshot of a recipe's content: ingredients, steps, and (target) component
references. Table: `recipe_versions`. Today every save creates one; (target) that changes —
see *Draft* / *promotion*.

### Draft **(target)**
The single mutable working copy of a recipe. Editing changes the Draft in place — it does
**not** create a new version. `recipe_versions.state = 'draft'`, `version_number = NULL`.
A recipe has exactly **0 or 1** Drafts.

### Ready **(target)**
A recipe version that has been promoted: frozen, numbered, and importable by other recipes.
`recipe_versions.state = 'ready'`. The opposite of Draft.

### Promotion / promote **(target)**
The Draft → Ready transition. This is the **only** thing that assigns a `version_number`
(`MAX(existing ready number) + 1`). Triggered explicitly by the user, who supplies a
*release note*. Method: `Recipe.promote(release_note)`.

### Importable **(target)**
A recipe is importable iff it has at least one Ready version. A brand-new recipe (Draft only,
zero versions) is **not** importable. Enforced by the *hard gate*.

### Component / sub-recipe **(target)**
A pinned reference from one recipe version to a specific Ready version of another recipe —
e.g. a milk bread importing a tangzhong. Table: `recipe_components`. The child recipe is
prepared separately and reused; contrast with an *inline preparation*.

### Inline preparation **(target)**
A step that cooks or transforms leaf ingredients *within this recipe* (brown the butter,
toast the seeds). Not its own recipe, not versioned — just a step with `kind = 'prep'`.
The test vs a component: *would you ever iterate it on its own, or use it in another recipe?*
Yes → component. No → inline preparation.

### Pinned reference / pin **(target)**
A component stores the child's `recipe_id` **and** a specific `child_version_id`. It does not
float to "latest". Analogous to a lockfile entry. Changing the pin creates a new version of
the parent.

### Hard gate **(target)**
The rule that a recipe with no Ready version cannot be added as a component. The component
picker lists only importable recipes. Raised as `SubRecipeNotReady`.

### Bump / bump a dependency **(target)**
Repointing a component's pin from the child version it currently references to the child's
latest Ready version. One-click action; produces a new Draft (then version) of the parent.
Method: `Recipe.bump_dependency(component_id)`.

### Update available **(target)**
The signal shown when a component's pinned `child_version_id` is not the child recipe's
latest Ready version — i.e. a *bump* is possible.

### Circular dependency **(target)**
An import edge that would make a recipe (transitively) depend on itself (A → B → A).
Rejected before the edge is added. Raised as `CircularDependency`. Detected by a domain
service that walks the component graph.

### Leaf ingredient **(live)**
A single quantity of one thing: `{name, amount, unit, type, notes}`. `type` is `flour` or
`other` (was `flour | liquid | preferment | fat | other`; narrowed on the frontend).
Stored in `recipe_versions.ingredients` (JSONB).

### Step **(live)** / step `kind` + `uses` **(target)**
An ordered instruction. Today: `{order, text}` free text. (target) `{order, text, kind, uses[]}`
where `kind ∈ prep | mix | ferment | shape | bake | finish` and `uses[]` names the
ingredient/component ids the step acts on. Stored in `recipe_versions.instructions` (JSONB).

### Baker's percentage **(live)**
Each ingredient's weight as a percentage of **total flour weight**. Flour ingredients sum to
100%; everything else (water, salt, a component) is expressed relative to total flour.
`total_flour_weight = sum(amount where type == 'flour')`. A *component* (target) is treated as
a plain non-flour line item — no decomposition into its own flour/water. Table:
`bakers_percentages`; function: `calculate_bakers_percentages`.

### Overall formula vs final dough
Pro-baking terms. *Overall formula* folds pre-ferment flour/water back into the totals;
*final dough* is what's left after the pre-ferments. **We deliberately do NOT model this** —
components are flat line items (decided with the user).

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
`GET /recipes/{id}/versions/{v1}/diff/{v2}`. Logic: `recipe_versioning.py` (target:
`domain/versioning.py`).

### Bake / timing **(live)**
One bread-making session — the execution of a recipe. Records process timestamps
(`autolyse_ts` … `bake_ts`), temperatures, stretch-fold count, notes, and `status`
(`in_progress` | `completed`). Table: `bread_timings`. Links to a recipe via `recipe_name`
(required text) plus optional `recipe_id` / `recipe_version_id`. (target) the pinned version
alone makes the whole component tree reproducible — no extra snapshot needed.

### Stretch and fold **(live)**
A dough-handling action performed during bulk fermentation. The app tracks only a count
(`bread_timings.stretch_fold_count`); the per-fold JSONB (`stretch_folds`) is legacy.

---

## Part B — Architecture & DDD terms (as used in this project)

### Layer
This codebase targets four layers; **dependencies point inward only**:

| Layer | Directory | Job | May NOT contain |
|---|---|---|---|
| Interface / HTTP | `backend/service.py` | parse request → one service call → shape response | business rules, SQL, transactions |
| Application | `backend/application/` | orchestrate one use case: open transaction, call domain, persist, commit | business rules, SQL |
| Domain | `backend/domain/` | the rules; pure, no I/O | framework imports (FastAPI, psycopg) |
| Infrastructure | `backend/infrastructure/` | talk to Postgres; implement the repository ports | business rules |

### Aggregate / aggregate root **(target)**
A cluster of objects treated as one unit for consistency and persistence. `Recipe` is the
aggregate root; its `RecipeVersion`s, `Component`s, and baker's percentages live **inside**
the aggregate (no independent lifecycle — cascade delete confirms it). You load, mutate, and
save the whole `Recipe`, never a `RecipeVersion` on its own. `BreadTiming` is a **separate**
aggregate that references a recipe by id only.

### Entity **(target)**
An object with identity that persists over time. `Recipe`, `RecipeVersion`, `BreadTiming`.

### Value object **(target)**
An object defined only by its attributes, immutable, no identity. `Ingredient`, `Component`,
`Step`, `BakersPercentage`. A `@dataclass(frozen=True)`.

### Domain service **(target)**
Stateless domain logic that doesn't belong to a single entity: versioning/diff math, baker's
percentage calculation, cycle detection. Lives in `backend/domain/` (e.g. `versioning.py`).

### Application service **(live, being reshaped)**
One method per use case. Opens the *Unit of Work*, loads aggregates via *repositories*, calls
domain methods, commits. Holds the *sequence* of a use case but no rules and no SQL.
Today: `RecipeService` in `backend/recipe_service.py` (still muddy — mixes concerns).
Target: `backend/application/recipe_service.py` + `timing_service.py`.

### Repository **(target)**
A collection-like interface for loading and saving **one aggregate**, hiding SQL and the
multi-table span. Split into:
- **Port** — the interface (`Protocol`) the application depends on. `backend/domain/repositories.py`.
- **Adapter** — the Postgres implementation. `backend/infrastructure/recipe_repository.py`
  (`PgRecipeRepository`). A `FakeRecipeRepository` (in-memory) is used in unit tests.

### Unit of Work (UoW) **(target)**
A context manager that owns one database connection and one transaction. Entered once per
use case by the application service; exposes `.recipes` / `.timings` bound to that
connection; **commits on clean exit, rolls back on exception**. `backend/infrastructure/unit_of_work.py`.
Replaces today's pattern where every `DBConnector` method opens its own connection and commits.

### DTO (Data Transfer Object) **(target)**
The shape crossing the HTTP boundary — Pydantic request/response models. Kept **separate**
from domain objects. `backend/api/schemas.py`. API-level validation (regex on `unit`/`type`,
non-empty checks) lives here, not in the domain.

### Mapper **(target)**
Pure functions that convert between representations: `api/mappers.py` (DTO ↔ domain),
`infrastructure/mappers.py` (database row ↔ domain).

### Composition root **(live)**
The single place where concrete implementations are wired together. Here: the `Depends`
providers in `backend/service.py` (`get_pool`, `get_db`, `get_recipe_service`). A test's
composition root swaps in fakes via `app.dependency_overrides`.

### Dependency injection (DI) / provider **(live)**
Giving a function its collaborators as arguments instead of having it import or construct
them. In FastAPI: a **provider** is a function passed to `Depends(...)`; the route receives
its result as a parameter. Enables swapping implementations without touching the consumer.

### Lifespan **(live)**
The FastAPI startup/shutdown handler. Opens `app.state.pool` on startup, closes it on
shutdown. `TestClient(app)` used as a context manager runs it; a bare `TestClient(app)` does
not (see `tests/conftest.py::_app_lifespan`).

### Persistence ignorance
The property that domain (and, ideally, application) code has no knowledge of how or whether
objects are stored. The goal of the Part I refactor.

---

## Deprecated / legacy terms (don't use going forward)

- **`DBConnector`** — the ~950-line god object holding all raw SQL. Being dismantled across
  Stages 4–7 into repositories.
- **`force_major` / major-minor versioning / `determine_next_version`** — vestigial. Version
  numbers are a single incrementing int, and (target) advance only on promotion.
- **`account_makes`, `dough_makes`, `DoughMake`, `AccountMake`** — legacy tables/models, not
  the current data model.
- **`fridge_ts`** — renamed to `final_proof_ts`.
