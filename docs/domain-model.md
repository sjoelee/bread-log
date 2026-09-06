# Domain Model

DDD view of the recipe domain — entities, the aggregate boundary, and value
objects — plus the database ERD it maps to. Companion to `glossary.md`.

Status: as of Stage 3. Part II additions shown separately at the bottom.

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
        +str id
    }

    class RecipeStep {
        <<value object (frozen)>>
        +int order
        +str instruction
        +str id
    }

    class RecipeListItem {
        <<read projection>>
        +UUID id
        +str name
        +str version
        +int ingredient_count
        +int step_count
        +str flour_ingredient_names
    }

    class BreadTiming {
        <<separate aggregate root>>
        +UUID id
        +UUID recipe_id
        +UUID recipe_version_id
        +str status
    }

    Recipe "1" *-- "1" RecipeVersion : current_version
    RecipeVersion "1" *-- "0..*" Ingredient : ingredients
    RecipeVersion "1" *-- "1..*" RecipeStep : instructions
    BreadTiming ..> Recipe : references by id only

    note for Recipe "Aggregate boundary: Recipe + its RecipeVersion + the embedded value objects. Loaded and saved as ONE unit (RecipeRepository, Stage 4). Full version history is a separate repo read, not held on the aggregate."
    note for RecipeListItem "Not a domain object. A flat summary the database computes in one query (jsonb_array_length, string_agg). repo.list() returns it directly."
```

`*--` (filled diamond) = composition: the part has no independent lifecycle and
is owned by the whole. `..>` = the timing merely references a recipe by id.
Fields typed `str` / `dict` above are `Optional` in the code where shown with `?`
in the glossary — Mermaid drops the `?`.

**No `RecipeHistory` type.** Version history is a repository query —
`RecipeRepository.get_versions(recipe_id) -> list[RecipeVersion]`, ordered by
`created_at` — not an object on the aggregate. The aggregate hydrates only the
current version (+ the Draft, in Part II). "Recipe specification" is a synonym
for `RecipeVersion` you may see in design notes.

### Why each class is what it is

| Class | Kind | Reason |
|---|---|---|
| `Recipe` | aggregate root, entity | UUID identity that persists; mutable; the consistency + transaction boundary |
| `RecipeVersion` | entity | own UUID identity; a distinct thing pointed at by `current_version_id` and by timings' `recipe_version_id` |
| `Ingredient` | value object (`frozen=True`) | fully defined by its attributes ("1000 g bread flour"); no identity; change = new value |
| `RecipeStep` | value object (`frozen=True`) | defined by `order` + `instruction`; the optional `id` is a soft diff-matching key, not identity |
| `RecipeListItem` | DTO / read model | DB-computed projection; never mutated, no invariants — pure query side |
| `BreadTiming` | separate aggregate | own root; its invariants (timestamp ordering, status) are unrelated to a recipe's |

---

## Database ERD

```mermaid
erDiagram
    recipes ||--o{ recipe_versions : "recipe_id"
    recipes |o--|| recipe_versions : "current_version_id (circular)"
    recipe_versions |o--o| bakers_percentages : "one per version"
    recipes |o--o{ bread_timings : "recipe_id · SET NULL"
    recipe_versions |o--o{ bread_timings : "recipe_version_id · SET NULL"

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
    bakers_percentages {
        uuid id PK
        uuid recipe_id FK
        uuid recipe_version_id FK
        numeric total_flour_weight
        jsonb flour_ingredients
        jsonb other_ingredients
    }
    bread_timings {
        uuid id PK
        varchar recipe_name
        uuid recipe_id FK
        uuid recipe_version_id FK
        varchar status
    }
```

- `Ingredient[]` / `RecipeStep[]` are **not tables** — they live in the
  `recipe_versions` JSONB columns (`{"ingredients": [...]}`, `{"instructions": [...]}`).
- `bakers_percentages` is a table but **not part of the domain aggregate**; the
  mapper passes it to `recipe_to_dto` as an argument.
- The circular FK (`recipes.current_version_id` ↔ `recipe_versions.recipe_id`)
  is why inserts are staged (insert recipe → insert version → set pointer).

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
