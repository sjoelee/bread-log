# Plan

Status and scope of the work, by phase and slice. **Decisions live in the ADRs**
([`adr/`](adr/README.md)); this file does not restate them. Terms are in
[`glossary.md`](glossary.md). Numbering is *phase.slice*.

## Execution protocol

Every slice follows the same loop:

1. **Walk through** — before any code, lay out what the slice touches (files, seams,
   risks, which tests change) and get explicit confirmation of the approach.
2. **Implement** — only after that confirmation.
3. **Tests** — rewrite or adjust the affected tests as part of the slice. It is not done
   until `uv run pytest` is green.
4. **Review** — stop. The user reviews the diff; no slice begins until the previous one
   is merged.
5. **PR** — one pull request per slice, off `main`.

Where a slice needs a decision no ADR covers, the ADR comes first (draft in chat, get
approval, then write the file).

## Phases

| Phase | Scope |
|---|---|
| 1 | Backend foundation: layered architecture for recipes |
| 2 | Recipe composition: Draft/Ready, sub-recipes, structured steps |
| 3 | Frontend |
| 4 | Recipe sessions (replaces bread timing) |

Slices 1.1–1.7 were called Stages 1–7, and slices 2.1–2.3 were called Slices A–C, in
earlier notes and in git history.

---

## Phase 1 — Backend foundation

Recipes only. Timing stays on the legacy `DBConnector` path, untouched, until Phase 4.

| Slice | What | Status |
|---|---|---|
| 1.1 | `Settings`; pool in a FastAPI lifespan; `Depends` providers; typed exceptions | merged (#1) |
| 1.2 | `domain/` models (`Ingredient`, `RecipeStep`, `RecipeVersion`, `Recipe`) and `versioning.py` | merged (#2) |
| 1.3 | API DTOs (`api/schemas.py`) and DTO ↔ domain mappers | merged (#3) |
| 1.4 | Recipe repository and row → domain mappers; recipe SQL removed from `DBConnector` | merged (#4) |
| 1.5 | `UnitOfWork`: one transaction per use case, rollback on exception | merged (#5) |
| 1.6 | Thin recipe routes; exception handlers | merged (#6) |
| 1.7 | `row_factory` reads; dead code removed; `DatabasePool` moved to infrastructure | merged (#8) |
| 1.8 | Dedicated test database `bread_makes_test` (ADR 0005); `tests/test_integration.py` removed | branch `test-database` pushed, PR pending |
| 1.9 | Application layer speaks domain objects (ADR 0001, 0003) | merged (`fb4d60b`) |
| 1.10 | `RecipeRepository` interface in the domain (ADR 0004), `UnitOfWork` interface in the application layer (ADR 0012), `PostgresRecipeRepository` rename, pyright check of `tests/fakes.py` | branch `repository-interfaces`; rebase onto `main` and open PR once ADR 0012 and 1.8 merge |

### Known gaps in Phase 1

Not scheduled; pick up deliberately.

- `get_recipe_version_diff` returns an API-shaped dict from the application layer
  (departs from ADR 0003).
- `tests/fakes.py::FakeRecipeRepository.list()` ignores ingredient, sort, limit and offset.
- The timing API test fails on a fresh database: it expects naive timestamps and gets
  `-08:00` offsets. Cause untraced.
- Leftover baker's percentages code: `calculate_bakers_percentages`,
  `tests/domain/test_baker_percentages.py`, and a dead frontend branch at
  `BreadAppNew.tsx:730`.
- The test database keeps leftover recipe rows after a run.
- `service.py` still imports `DBConnector` for the legacy timing routes.

### Branch housekeeping

- `layering-app-speaks-domain` is contained in `main`; delete it.
- `slice-a-draft-ready-schema` (`ec9c7c0`) predates the regenerated `database/schema.sql`
  and will conflict; recreate it as the schema step of slice 2.1.

---

## Phase 2 — Recipe composition

Built on the Phase 1 seams. Each slice is independently shippable.

Schema changes are applied manually with `psql`, then `database/schema.sql` is
regenerated and the test database rebuilt with `scripts/reset_test_db.sh`.

### 2.1 Draft / Ready (ADR 0007, 0011, 0013, 0014, 0015)

Spec: [`specs/2.1-draft-ready.md`](specs/2.1-draft-ready.md) — the behavior, API and
acceptance scenarios live there.

Scope:
- Schema: already in `database/schema.sql`; wipe the existing dev rows (test data).
- Domain: `Recipe` holds `latest_ready` and `draft`; `save_draft`, `promote`,
  `discard_draft`, `update_details` replace `add_version()`.
- Repository and application: load and save both parts; new use cases per the spec.
- API: draft, promote and discard endpoints; `PATCH /recipes/{id}` edits details only;
  `state` list filter.
- Rewrite the recipe-versioning tests for this model.
- Resolve the spec's **Open** items before or during implementation.

### 2.2 Sub-recipes (ADR 0006, 0008, 0009, 0010)

- Schema: `recipe_sub_recipe_refs` (parent version, child recipe, pinned child version,
  label, amount, unit, sort order), indexed on parent version and child recipe; child
  references use `ON DELETE RESTRICT`. A table, not JSONB, so dependency queries stay a
  purely additive extension later.
- Domain: `SubRecipeRef` value object; `Recipe.add_sub_recipe`, `remove_sub_recipe`,
  `update_sub_recipe` (including repointing the pin to another Ready version of the same
  child), all acting on the Draft; `SubRecipeNotReady` and `CircularDependency` errors;
  a cycle-detection domain service that walks the graph through the repository.
- Repository: `imported_by(recipe_id)`, `ready_recipes()`; `save` replaces the reference rows
  of the affected version; `delete` raises `ConflictError` when the recipe is imported.
- API: `POST/PATCH/DELETE /recipes/{id}/sub-recipes[/{rid}]`; list gains `ready_only`;
  `GET /recipes/{id}` returns resolved sub-recipes; `DELETE` returns 409 listing the
  parents.
- Write order matters because of the circular foreign key between `recipes.current_version_id`
  and `recipe_versions.recipe_id`.
- **No ADR yet:** delete-while-imported behavior (409); deleting a single Ready version.

### 2.3 Structured steps

- **Needs an ADR first.**
- `RecipeStep` gains `kind` (`prep | mix | ferment | shape | bake | finish`) and
  `uses` (ids of the ingredients or sub-recipe references the step acts on); stored in the
  existing `instructions` JSONB, no DDL.
- The aggregate validates that each `uses` id resolves.
- `versioning.py` diff covers sub-recipe references and step references; the id-generation
  helper assigns step ids first.

---

## Phase 3 — Frontend

- `src/types/bread.ts`: real `Recipe`, `RecipeVersion`, `Ingredient`, `SubRecipeRef`, `Step`
  types in place of `any` and the file-local interfaces in `RecipeTab.tsx`.
- `src/services/api.ts`: extract recipe CRUD from the inline `fetch` calls in
  `BreadAppNew.tsx` into a `recipeApi`; add promote, sub-recipe and picker calls.
- `RecipeTab.tsx`: Draft/Ready indicator and Promote button with a release-note field; a
  sub-recipes section (picker filtered to Ready recipes, amount, label, pinned version);
  step `kind` and `uses` editor; one Notes textarea.
- `BreadAppNew.tsx`: Draft/Ready badge in the list; delete flow handles 409 ("imported by …").
  No "updates available" indicator (ADR 0009).
- `RecipeVersionHistory.tsx`: show the Draft as a mutable working copy; history lists only
  Ready versions.

---

## Phase 4 — Recipe sessions

Not designed in detail; captured so it is not lost. Sequenced after slice 2.3, because a
step-driven session needs steps with identity and a `kind`.

`BreadTiming` hardcodes a bread process into seven fixed timestamp columns plus bread-only
temperatures. The goal is to record "I followed recipe X and hit each step at these
times" for any recipe.

```
RecipeSession   (rename of BreadTiming; final name TBD: Session / Bake / CookLog)
  recipe_version_id   the version followed (pinned)
  step_timestamps     { step_id: timestamp }, replaces the fixed columns
  observations        temperatures, notes, free-form (typed vs key-value TBD)
  status              derived: all steps stamped -> completed, else in_progress
```

Work: new schema and migration (map existing `bread_timings` rows onto a canonical bread
recipe's steps); a session repository, service and thin routes following the recipe
pattern; fix the `update_bread_timing` double commit and the two dead checks in
`validate_timing_updates`; retire `DBConnector`; session UI driven by the recipe's steps.

---

## Open directions (not decided)

- **Baker's percentages.** Bread-specific; the frontend recomputes it. The backend value is
  not part of the domain model. Revisit later; not a decision yet.
- **Recipe-general vs bread-specific.** The domain is becoming general, but ingredient
  `type`, baker's percentages, hydration and prefermented flour are bread-only. A
  `BreadRecipe` specialization (inheritance, or a value object by composition) is likely.
  `Ingredient.type` is optional meanwhile (`None` = unclassified).

## Constraints

- Python 3.9.6 is pinned: no `match`, and `from __future__ import annotations` is needed
  for `X | Y`.
- The existing real-database suite is the regression guard; add characterization tests
  within a slice when its diff is large.
- `RecipeVersionHistory.tsx` assumes every version is immutable; the mutable Draft breaks
  that (Phase 3).
