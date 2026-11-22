"""Database row -> domain object mapping.

Rows are psycopg dicts (``dict_row``) keyed by the column names/aliases the queries
in ``recipe_repository.py`` select (see the ``_*`` SQL constants there).
"""

from __future__ import annotations

from typing import List, Optional

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
    state=row["state"],
    version_number=row["version_number"],
    release_note=row["description"],
    ingredients=_ingredients(row["ingredients"]),
    instructions=_steps(row["instructions"]),
    created_at=row["created_at"],
    change_summary=row["change_summary"],
  )


def recipe_from_rows(row: dict, version_rows: List[dict]) -> Optional[domain.Recipe]:
  """Build a ``Recipe`` from its ``recipes`` row and its latest Ready and Draft
  version rows. Returns ``None`` if it has neither (not a valid recipe)."""
  versions = [version_from_row(v) for v in version_rows]
  ready = next((v for v in versions if v.id == row["current_version_id"]), None)
  draft = next((v for v in versions if v.state == domain.DRAFT), None)
  if ready is None and draft is None:
    return None
  return domain.Recipe(
    id=row["id"],
    name=row["name"],
    description=row["description"],
    category=row["category"],
    created_at=row["created_at"],
    updated_at=row["updated_at"],
    latest_ready=ready,
    draft=draft,
  )


def _version_summary(row: dict, prefix: str) -> Optional[domain.VersionSummary]:
  if row[f"{prefix}_id"] is None:
    return None
  return domain.VersionSummary(
    version_id=row[f"{prefix}_id"],
    version_number=row.get(f"{prefix}_number"),
    ingredient_count=row[f"{prefix}_ingredient_count"] or 0,
    step_count=row[f"{prefix}_step_count"] or 0,
  )


def summary_from_row(row: dict) -> domain.RecipeSummary:
  return domain.RecipeSummary(
    id=row["id"],
    name=row["name"],
    description=row["description"],
    category=row["category"],
    created_at=row["created_at"],
    updated_at=row["updated_at"],
    latest_ready=_version_summary(row, "ready"),
    draft=_version_summary(row, "draft"),
  )
