"""Database row -> domain object mapping.

Rows are psycopg dicts (``dict_row``) keyed by the column names/aliases the queries
in ``recipe_repository.py`` select (see the ``_*`` SQL constants there).
"""

from __future__ import annotations

from typing import Optional

from ..domain import models as domain


def _ingredient(raw: dict) -> domain.Ingredient:
  return domain.Ingredient(
    name=raw["name"],
    amount=raw["amount"],
    unit=raw["unit"],
    type=raw.get("type"),
    notes=raw.get("notes"),
  )


def _ingredients(jsonb) -> list[domain.Ingredient]:
  items = jsonb.get("ingredients", []) if jsonb else []
  return [_ingredient(x) for x in items]


def _steps(jsonb) -> list[domain.RecipeStep]:
  items = jsonb.get("instructions", []) if jsonb else []
  return [
    domain.RecipeStep(order=x["order"], instruction=x["instruction"], id=x.get("id"))
    for x in items
    if x.get("instruction", "").strip()
  ]


def version_from_row(row: dict) -> domain.RecipeVersion:
  return domain.RecipeVersion(
    id=row["id"],
    recipe_id=row["recipe_id"],
    version_number=row["version_number"],
    description=row["description"],
    ingredients=_ingredients(row["ingredients"]),
    instructions=_steps(row["instructions"]),
    created_at=row["created_at"],
    change_summary=row["change_summary"],
  )


def recipe_from_joined_row(row: Optional[dict]) -> Optional[domain.Recipe]:
  """Build a ``Recipe`` from a recipe row LEFT JOINed to its current version row.

  Recipe columns are keyed by name; version columns carry a ``v_`` alias so the
  two sides' ``id`` / ``description`` / ``created_at`` don't collide.

  Returns ``None`` if the row is missing or the recipe has no current version.
  """
  if row is None or row["v_id"] is None:
    return None
  version = domain.RecipeVersion(
    id=row["v_id"],
    recipe_id=row["id"],
    version_number=row["v_number"],
    description=row["v_description"],
    ingredients=_ingredients(row["v_ingredients"]),
    instructions=_steps(row["v_instructions"]),
    created_at=row["v_created_at"],
  )
  return domain.Recipe(
    id=row["id"],
    name=row["name"],
    description=row["description"],
    category=row["category"],
    current_version=version,
    created_at=row["created_at"],
    updated_at=row["updated_at"],
  )


def summary_from_row(row: dict) -> domain.RecipeSummary:
  return domain.RecipeSummary(
    id=row["id"],
    name=row["name"],
    description=row["description"],
    category=row["category"],
    version_number=row["version_number"],
    current_version_id=row["current_version_id"],
    ingredient_count=row["ingredient_count"] or 0,
    step_count=row["step_count"] or 0,
    created_at=row["created_at"],
    updated_at=row["updated_at"],
  )
