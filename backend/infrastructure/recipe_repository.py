"""Recipe persistence. Speaks domain objects; callers never see a row or a query.

Each method opens a pooled connection and commits itself.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import List, Optional
from uuid import UUID

from ..db import DatabasePool
from ..domain import models as domain
from ..exceptions import DatabaseError
from . import mappers

logger = logging.getLogger("recipe_repository")

_RECIPE_JOINED = """
  SELECT r.id, r.name, r.description, r.category, r.created_at, r.updated_at,
         rv.id, rv.version_number, rv.description, rv.ingredients,
         rv.instructions, rv.created_at
  FROM recipes r
  LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
  WHERE r.id = %s
"""

_VERSION_COLS = """
  id, recipe_id, version_number, description,
  ingredients, instructions, created_at, change_summary
"""

_LIST_BASE = """
  SELECT r.id, r.name, r.description, r.category, r.created_at, r.updated_at,
         rv.version_number, r.current_version_id,
         jsonb_array_length(rv.ingredients->'ingredients')  AS ingredient_count,
         jsonb_array_length(rv.instructions->'instructions') AS step_count
  FROM recipes r
  LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
"""

_LIST_SORT_COLUMNS = {"created_at": "r.created_at", "name": "r.name"}


def _ingredients_json(ingredients: List[domain.Ingredient]) -> str:
  return json.dumps({"ingredients": [asdict(i) for i in ingredients]})


def _instructions_json(steps: List[domain.RecipeStep]) -> str:
  return json.dumps({"instructions": [asdict(s) for s in steps]})


class RecipeRepository:
  def __init__(self, pool: DatabasePool):
    self._pool = pool

  # --- reads ---------------------------------------------------------------

  def get(self, recipe_id: UUID) -> Optional[domain.Recipe]:
    row = self._fetchone(_RECIPE_JOINED, [recipe_id], "get recipe")
    return mappers.recipe_from_joined_row(row)

  def get_version(self, version_id: UUID) -> Optional[domain.RecipeVersion]:
    row = self._fetchone(
      f"SELECT {_VERSION_COLS} FROM recipe_versions WHERE id = %s",
      [version_id],
      "get recipe version",
    )
    return mappers.version_from_row(row) if row else None

  def get_versions(self, recipe_id: UUID) -> List[domain.RecipeVersion]:
    rows = self._fetchall(
      f"SELECT {_VERSION_COLS} FROM recipe_versions "
      "WHERE recipe_id = %s ORDER BY version_number DESC",
      [recipe_id],
      "get recipe versions",
    )
    return [mappers.version_from_row(r) for r in rows]

  def list(
    self,
    *,
    category: Optional[str] = None,
    search: Optional[str] = None,
    ingredient: Optional[str] = None,
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    limit: int = 50,
    offset: int = 0,
  ) -> List[domain.RecipeSummary]:
    conditions: List[str] = []
    params: List[object] = []
    if category:
      conditions.append("r.category = %s")
      params.append(category)
    if search:
      conditions.append("r.name ILIKE %s")
      params.append(f"%{search}%")
    if ingredient:
      conditions.append(
        "EXISTS (SELECT 1 FROM jsonb_array_elements(rv.ingredients->'ingredients') "
        "AS ing WHERE ing->>'name' ILIKE %s)"
      )
      params.append(f"%{ingredient}%")

    query = _LIST_BASE + (" WHERE " + " AND ".join(conditions) if conditions else "")
    sort_col = _LIST_SORT_COLUMNS.get(sort_by, "r.created_at")
    sort_dir = "ASC" if sort_direction.lower() == "asc" else "DESC"
    query += f" ORDER BY {sort_col} {sort_dir} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    rows = self._fetchall(query, params, "list recipes")
    return [mappers.summary_from_row(r) for r in rows]

  # --- writes -----------------------------------------------------------

  def add(self, recipe: domain.Recipe) -> None:
    """Insert a new recipe and its first version."""
    v = recipe.current_version
    try:
      with self._pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(
            "INSERT INTO recipes (id, name, description, category, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
              recipe.id,
              recipe.name,
              recipe.description,
              recipe.category,
              recipe.created_at,
              recipe.updated_at,
            ],
          )
          cur.execute(
            "INSERT INTO recipe_versions "
            "(id, recipe_id, version_number, description, ingredients, instructions, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [
              v.id,
              recipe.id,
              v.version_number,
              v.description,
              _ingredients_json(v.ingredients),
              _instructions_json(v.instructions),
              v.created_at,
            ],
          )
          cur.execute(
            "UPDATE recipes SET current_version_id = %s WHERE id = %s",
            [v.id, recipe.id],
          )
          conn.commit()
    except Exception as e:
      logger.error(f"Error adding recipe {recipe.id}: {e}")
      raise DatabaseError(f"Error adding recipe: {e}") from e

  def save(self, recipe: domain.Recipe) -> None:
    """Persist an existing recipe: upsert its current version, move the current
    pointer, and update the scalar fields — in one transaction. Raises
    ``ValueError`` if the recipe row is gone."""
    v = recipe.current_version
    try:
      with self._pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(
            "INSERT INTO recipe_versions "
            "(id, recipe_id, version_number, description, ingredients, instructions, created_at, change_summary) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET "
            "  version_number = EXCLUDED.version_number, "
            "  description    = EXCLUDED.description, "
            "  ingredients    = EXCLUDED.ingredients, "
            "  instructions   = EXCLUDED.instructions, "
            "  change_summary = EXCLUDED.change_summary",
            [
              v.id,
              recipe.id,
              v.version_number,
              v.description,
              _ingredients_json(v.ingredients),
              _instructions_json(v.instructions),
              v.created_at,
              json.dumps(v.change_summary or {}),
            ],
          )
          cur.execute(
            "UPDATE recipes SET name = %s, description = %s, category = %s, "
            "current_version_id = %s, updated_at = %s WHERE id = %s",
            [
              recipe.name,
              recipe.description,
              recipe.category,
              v.id,
              recipe.updated_at,
              recipe.id,
            ],
          )
          if cur.rowcount == 0:
            raise ValueError(f"Recipe {recipe.id} not found")
          conn.commit()
    except ValueError:
      raise
    except Exception as e:
      logger.error(f"Error saving recipe {recipe.id}: {e}")
      raise DatabaseError(f"Error saving recipe: {e}") from e

  def delete(self, recipe_id: UUID) -> bool:
    """Delete a recipe. Cascades to its versions. Returns False if it did not exist."""
    try:
      with self._pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute("DELETE FROM recipes WHERE id = %s", [recipe_id])
          deleted = cur.rowcount
          conn.commit()
      return deleted > 0
    except Exception as e:
      logger.error(f"Error deleting recipe {recipe_id}: {e}")
      raise DatabaseError(f"Error deleting recipe: {e}") from e

  # --- helpers --------------------------------------------------------

  def _fetchone(self, query: str, params, what: str):
    try:
      with self._pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          return cur.fetchone()
    except Exception as e:
      logger.error(f"Error ({what}): {e}")
      raise DatabaseError(f"Error {what}: {e}") from e

  def _fetchall(self, query: str, params, what: str):
    try:
      with self._pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          return cur.fetchall()
    except Exception as e:
      logger.error(f"Error ({what}): {e}")
      raise DatabaseError(f"Error {what}: {e}") from e
