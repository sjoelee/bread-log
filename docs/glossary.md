# Glossary

Shared vocabulary for the bread-log recipe domain and its architecture. Use these exact
terms in code, comments, commits, and conversation so humans and Claude sessions stay
aligned. Design decisions are recorded in [`adr/`](adr/README.md); entries below say
"Here: …" where a term maps to a concrete technology or location.

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

---

## Architecture

### ADR — Architecture Decision Record
A short document recording one design decision: context, the choice, alternatives
rejected, consequences. Lives in `docs/adr/`. A changed decision gets a new ADR that
supersedes the old one.

### API — Application Programming Interface
Here, the HTTP endpoints the frontend calls (e.g. `POST /recipes/`).

### DTO — Data Transfer Object
A type defining the shape of data crossing the client boundary: a request body or a
response body, including input validation. Kept separate from domain objects (ADR 0003).
Here: the Pydantic classes in `backend/api/schemas.py`.

### Layer
One of four tiers of the backend. The domain depends on nothing; application depends only
on the domain; interface depends on application and domain; infrastructure depends on the
domain (ADR 0001).

| Layer | Job | Here |
|---|---|---|
| Interface | the boundary clients talk to: request in, one application call, response out | `backend/service.py`, `backend/api/` |
| Application | orchestrates use cases | `backend/application/` |
| Domain | business logic; pure, no I/O | `backend/domain/` |
| Infrastructure | storage and external systems | `backend/infrastructure/` |

### Use case
One thing a user can ask the system to do, e.g. "create a recipe" or "promote a draft".
Each is one method on an application service.

### Application service
The class holding the use cases. It is a thin coordination layer: it holds no business
logic. A method opens a unit of work, loads aggregates through repositories, tells the
domain objects one layer down to do the work, then saves. The business logic lives in the
domain; the service only sequences the steps. Here: `RecipeService`.

### Domain model
The plain objects and functions that hold the business logic. Imports nothing from a web,
validation or storage framework, so it runs in a test with no database or HTTP. Here:
dataclasses in `backend/domain/models.py`.

### Business logic
The decisions about how recipes behave, independent of HTTP and storage: how versions are
compared, when a change counts as meaningful, which recipes may be imported, how version
numbers are assigned. Lives in the domain layer.

### Input validation
Checking that a request is well-formed (non-empty name, positive amount, allowed unit)
before it reaches the application. Lives in the DTOs. Not business logic: it looks at one
request, not at a recipe's state.

### Mapper
A pure function converting one representation to another. Here: DTO ↔ domain in
`backend/api/mappers.py`; stored row → domain in `backend/infrastructure/mappers.py`.

### Aggregate
A cluster of objects loaded, changed and saved as one unit, entered through one root.
`Recipe` is the aggregate root; its versions have no lifecycle of their own (deleting a
recipe deletes them). You load and save the whole `Recipe`, never a version alone.

### Repository
The object that loads and saves one aggregate, hiding all storage detail. Callers pass and
receive domain objects (e.g. `Recipe`), never rows. Never commits; the unit of work does.
The domain declares the interface it needs (ADR 0004); the production and in-memory
implementations both satisfy it. Here: `RecipeRepository` (PostgreSQL) and
`FakeRecipeRepository` in `tests/fakes.py`.

### Protocol
A Python type (`typing.Protocol`) declaring a set of methods. Any class with matching
methods satisfies it without inheriting from it, like a Go interface. Checked only by the
type checker (pyright); Python does not check at runtime. Here: how the repository
interface is expressed.

### Fake
A simple working stand-in used in tests, e.g. an in-memory repository that keeps recipes in
a dict. Unlike a mock, it has real behavior; tests assert on results, not on which calls
were made.

### Unit of Work
A scope that owns one storage session and one transaction for a single use case. Commits
when the use case completes normally, discards everything if it fails, always releases the
session (ADR 0002). Exposes the repositories, bound to that session. Here:
`UnitOfWork` in `backend/infrastructure/unit_of_work.py`, over a psycopg connection pool.

### Test database
A dedicated database, separate from development, that storage-touching tests run against
(ADR 0005). Here: PostgreSQL, built from `database/schema.sql`; the test run must refuse
any database whose name does not end in `_test`.
