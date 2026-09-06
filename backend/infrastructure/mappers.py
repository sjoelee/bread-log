"""Database row -> domain object mapping.

Rows are psycopg tuples in the column order the queries in ``recipe_repository.py``
select (see the ``_*`` SQL constants there).
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
    id=raw.get("id"),
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


def version_from_row(row) -> domain.RecipeVersion:
  (
    vid,
    recipe_id,
    version_number,
    description,
    ingredients,
    instructions,
    created_at,
    change_summary,
  ) = row
  return domain.RecipeVersion(
    id=vid,
    recipe_id=recipe_id,
    version_number=version_number,
    description=description,
    ingredients=_ingredients(ingredients),
    instructions=_steps(instructions),
    created_at=created_at,
    change_summary=change_summary,
  )


def recipe_from_joined_row(row) -> Optional[domain.Recipe]:
  """Build a ``Recipe`` from a recipe row LEFT JOINed to its current version row.

  Returns ``None`` if the row is missing or the recipe has no current version.
  """
  if row is None:
    return None
  (
    rid,
    name,
    description,
    category,
    r_created_at,
    r_updated_at,
    v_id,
    v_number,
    v_description,
    v_ingredients,
    v_instructions,
    v_created_at,
  ) = row
  if v_id is None:
    return None
  version = domain.RecipeVersion(
    id=v_id,
    recipe_id=rid,
    version_number=v_number,
    description=v_description,
    ingredients=_ingredients(v_ingredients),
    instructions=_steps(v_instructions),
    created_at=v_created_at,
  )
  return domain.Recipe(
    id=rid,
    name=name,
    description=description,
    category=category,
    current_version=version,
    created_at=r_created_at,
    updated_at=r_updated_at,
  )


def summary_from_row(row) -> domain.RecipeSummary:
  (
    rid,
    name,
    description,
    category,
    created_at,
    updated_at,
    version_number,
    current_version_id,
    ingredient_count,
    step_count,
  ) = row
  return domain.RecipeSummary(
    id=rid,
    name=name,
    description=description,
    category=category,
    version_number=version_number,
    current_version_id=current_version_id,
    ingredient_count=ingredient_count or 0,
    step_count=step_count or 0,
    created_at=created_at,
    updated_at=updated_at,
  )
