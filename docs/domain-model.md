# Domain Model

DDD view of the recipe domain — entities, the aggregate boundary, and value
objects — plus the database ERD it maps to. Companion to `glossary.md`.

Status: as of Stage 4. Part II additions shown separately at the bottom.

As of Stage 4 this model is **live on the recipe path**: `RecipeRepository`
loads and saves `Recipe` aggregates, `RecipeService` operates on domain objects,
and the `api/` mappers convert to/from DTOs at the HTTP edge. Recipe SQL no
longer lives in `DBConnector`.

---

## Current domain model (`backend/domain/models.py`)

```mermaid
classDiagram

    class Recipe {
        <<aggregate root>>
        +UUID id
        +str name
        +str description
        +str category
        +datetime created_at
        +datetime updated_at
        +create() Recipe
        +add_version() RecipeVersion
    }

    class RecipeVersion {
        <<entity>>
        +UUID id
        +UUID recipe_id
        +int version_number
        +str description
        +datetime created_at
        +dict change_summary
    }

    class Ingredient {
        <<value object (frozen)>>
        +str name
        +float amount
        +str unit
        +str type
        +str notes
    }

    class RecipeStep {
        <<value object (frozen)>>
        +int order
        +str instruction
        +str id
    }

    class RecipeSummary {
        <<read projection>>
        +UUID id
        +str name
        +str description
        +str category
        +int version_number
        +UUID current_version_id
        +int ingredient_count
        +int step_count
        +datetime created_at
        +datetime updated_at
    }

    Recipe "1" *-- "1" RecipeVersion : current_version
    RecipeVersion "1" *-- "0..*" Ingredient : ingredients
    RecipeVersion "1" *-- "1..*" RecipeStep : instructions

    note for Recipe "Aggregate boundary: Recipe + its current RecipeVersion + the embedded value objects. Loaded and saved as one unit by RecipeRepository. Full version history is a separate repo read, not held on the aggregate."
    note for RecipeSummary "Not a domain object. A flat DB-computed projection. RecipeRepository.list() returns it; mapped to the RecipeListItem DTO at the edge."
```

`*--` (filled diamond) = composition: the part has no independent lifecycle and
is owned by the whole.

**No `RecipeHistory` type.** Version history is a repository query —
`RecipeRepository.get_versions(recipe_id) -> list[RecipeVersion]`, ordered by
`version_number` descending — not an object on the aggregate. The aggregate
hydrates only the current version (+ the Draft, in Part II). "Recipe
specification" is a synonym for `RecipeVersion` you may see in design notes.

### Why each class is what it is

| Class | Kind | Reason |
|---|---|---|
| `Recipe` | aggregate root, entity | UUID identity that persists; mutable; the consistency + transaction boundary |
| `RecipeVersion` | entity | own UUID identity; a distinct thing pointed at by `recipes.current_version_id` (and, later, by component pins) |
| `Ingredient` | value object (`frozen=True`) | fully defined by its attributes ("1000 g bread flour"); no identity, no id field; diffed by name; change = new value |
| `RecipeStep` | value object (`frozen=True`) | defined by `order` + `instruction`; the optional `id` is a soft diff-matching key, not identity |
| `RecipeSummary` | read model | DB-computed projection; never mutated, no invariants — pure query side |

---

## Database ERD

```mermaid
erDiagram
    recipes ||--o{ recipe_versions : "recipe_id · CASCADE"
    recipes |o--|| recipe_versions : "current_version_id (circular)"

    recipes {
        uuid id PK
        varchar name
        varchar category
        text description
        uuid current_version_id FK
        timestamp created_at
        timestamp updated_at
    }
    recipe_versions {
        uuid id PK
        uuid recipe_id FK
        int version_number
        text description
        jsonb ingredients
        jsonb instructions
        jsonb change_summary
        timestamp created_at
    }
```

- `Ingredient[]` / `RecipeStep[]` are **not tables** — they live in the
  `recipe_versions` JSONB columns (`{"ingredients": [...]}`, `{"instructions": [...]}`).
- `change_summary` holds machine-generated diff counts for UI display; written
  by `RecipeRepository.save()`, left null on the first version.
- The circular FK (`recipes.current_version_id` → `recipe_versions.id`, and
  `recipe_versions.recipe_id` → `recipes.id`) is why inserts are staged
  (insert recipe → insert version → set the current pointer).

---

## Part II additions (target — not built yet)

```mermaid
classDiagram

    class Recipe {
        <<aggregate root>>
        +add_component(child, amount, unit, label)
        +promote(release_note)
        +bump_dependency(component_id)
    }
    class RecipeVersion {
        <<entity>>
        +str state
        +int version_number
    }
    class RecipeStep {
        <<value object>>
        +str kind
        +List~str~ uses
    }
    class Component {
        <<value object (frozen)>>
        +UUID child_recipe_id
        +UUID child_version_id
        +str label
        +float amount
        +str unit
        +int sort_order
        +str id
    }

    Recipe "1" *-- "1" RecipeVersion : current (latest Ready)
    Recipe "1" o-- "0..1" RecipeVersion : draft
    RecipeVersion "1" *-- "0..*" Component : components
    Component ..> RecipeVersion : pins a version of ANOTHER Recipe

    note for RecipeVersion "state = draft | ready. version_number is NULL on a draft, assigned only on promote."
    note for RecipeStep "kind = prep | mix | ferment | shape | bake | finish. uses = ids of the ingredients/components the step acts on."
    note for Component "Reference ACROSS the aggregate boundary — never nest one Recipe inside another. Invariants (Recipe.add_component): child must have a Ready version; the edge must not create a cycle."
```

New table:

```mermaid
erDiagram
    recipe_versions ||--o{ recipe_components : "parent_version_id · CASCADE"
    recipes ||--o{ recipe_components : "child_recipe_id · RESTRICT"
    recipe_versions ||--o{ recipe_components : "child_version_id · RESTRICT"

    recipe_components {
        uuid id PK
        uuid parent_version_id FK
        uuid child_recipe_id FK
        uuid child_version_id FK
        varchar label
        numeric amount
        varchar unit
        int sort_order
        timestamp created_at
    }
```
