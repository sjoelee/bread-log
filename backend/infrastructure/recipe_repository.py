"""Recipe persistence. Speaks domain objects; callers never see a row or a query.

Each instance is bound to one connection (handed in by ``UnitOfWork``) and never
commits — the Unit of Work owns the transaction boundary.

``recipes.current_version_id`` always points at the latest Ready version (NULL
when there is none); the Draft is the recipe's one row with ``state = 'draft'``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import List, Optional
from uuid import UUID

from psycopg.rows import dict_row

from ..domain import models as domain
from ..exceptions import DatabaseError, NotFoundError
from . import mappers

logger = logging.getLogger("recipe_repository")

_RECIPE_COLS = "id, name, description, category, created_at, updated_at"

_VERSION_COLS = """
  id, recipe_id, state, version_number, description,
  ingredients, instructions, created_at, change_summary
"""

# The two version parts a list row carries, aliased ``rv`` (latest Ready) and
# ``dv`` (Draft).
_LIST_BASE = """
  SELECT r.id, r.name, r.description, r.category, r.created_at, r.updated_at,
         rv.id AS ready_id, rv.version_number AS ready_number,
         jsonb_array_length(rv.ingredients->'ingredients')   AS ready_ingredient_count,
         jsonb_array_length(rv.instructions->'instructions') AS ready_step_count,
         dv.id AS draft_id,
         jsonb_array_length(dv.ingredients->'ingredients')   AS draft_ingredient_count,
         jsonb_array_length(dv.instructions->'instructions') AS draft_step_count
  FROM recipes r
  LEFT JOIN recipe_versions rv ON rv.id = r.current_version_id
  LEFT JOIN recipe_versions dv ON dv.recipe_id = r.id AND dv.state = 'draft'
"""

_LIST_SORT_COLUMNS = {"created_at": "r.created_at", "name": "r.name"}

_HAS_INGREDIENT = (
  "EXISTS (SELECT 1 FROM jsonb_array_elements({alias}.ingredients->'ingredients') "
  "AS ing WHERE ing->>'name' ILIKE %s)"
)

# Insert a version, or update it only while it is still a Draft: a Ready row is
# frozen, so re-saving one is a no-op. Promotion is the Draft row turning Ready.
_UPSERT_VERSION = """
  INSERT INTO recipe_versions
    (id, recipe_id, state, version_number, description, ingredients, instructions,
     created_at, change_summary)
  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
  ON CONFLICT (id) DO UPDATE SET
    state          = EXCLUDED.state,
    version_number = EXCLUDED.version_number,
    description    = EXCLUDED.description,
    ingredients    = EXCLUDED.ingredients,
    instructions   = EXCLUDED.instructions,
    created_at     = EXCLUDED.created_at,
    change_summary = EXCLUDED.change_summary
  WHERE recipe_versions.state = 'draft'
"""


def _ingredients_json(ingredients: List[domain.Ingredient]) -> str:
  return json.dumps({"ingredients": [asdict(i) for i in ingredients]})


def _instructions_json(steps: List[domain.RecipeStep]) -> str:
  return json.dumps({"instructions": [asdict(s) for s in steps]})


class PostgresRecipeRepository:
  def __init__(self, conn):
    self._conn = conn

  # --- reads ---------------------------------------------------------------

  def get(self, recipe_id: UUID) -> Optional[domain.Recipe]:
    row = self._fetchone(
      f"SELECT {_RECIPE_COLS}, current_version_id FROM recipes WHERE id = %s",
      [recipe_id],
      "get recipe",
    )
    if row is None:
      return None
    version_rows = self._fetchall(
      f"SELECT {_VERSION_COLS} FROM recipe_versions "
      "WHERE id = %s OR (recipe_id = %s AND state = 'draft')",
      [row["current_version_id"], recipe_id],
      "get recipe versions",
    )
    return mappers.recipe_from_rows(row, version_rows)

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
      "WHERE recipe_id = %s AND state = 'ready' ORDER BY version_number DESC",
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
    state: str = "any",
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    limit: int = 50,
    offset: int = 0,
  ) -> List[domain.RecipeSummary]:
    """``state`` limits the list to recipes with a Draft (``draft``) or a Ready
    version (``ready``); ``ingredient`` then matches that part only. With ``any``
    it matches either the Draft or the latest Ready version."""
    conditions: List[str] = []
    params: List[object] = []
    if category:
      conditions.append("r.category = %s")
      params.append(category)
    if search:
      conditions.append("r.name ILIKE %s")
      params.append(f"%{search}%")
    if state == "draft":
      conditions.append("dv.id IS NOT NULL")
    elif state == "ready":
      conditions.append("rv.id IS NOT NULL")
    if ingredient:
      pattern = f"%{ingredient}%"
      if state == "draft":
        conditions.append(_HAS_INGREDIENT.format(alias="dv"))
        params.append(pattern)
      elif state == "ready":
        conditions.append(_HAS_INGREDIENT.format(alias="rv"))
        params.append(pattern)
      else:
        conditions.append(
          f"({_HAS_INGREDIENT.format(alias='dv')} OR "
          f"{_HAS_INGREDIENT.format(alias='rv')})"
        )
        params.extend([pattern, pattern])

    query = _LIST_BASE + (" WHERE " + " AND ".join(conditions) if conditions else "")
    sort_col = _LIST_SORT_COLUMNS.get(sort_by, "r.created_at")
    sort_dir = "ASC" if sort_direction.lower() == "asc" else "DESC"
    query += f" ORDER BY {sort_col} {sort_dir} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    rows = self._fetchall(query, params, "list recipes")
    return [mappers.summary_from_row(r) for r in rows]

  # --- writes -----------------------------------------------------------

  def add(self, recipe: domain.Recipe) -> None:
    """Insert a new recipe and its versions."""
    try:
      with self._conn.cursor() as cur:
        cur.execute(
          f"INSERT INTO recipes ({_RECIPE_COLS}) VALUES (%s, %s, %s, %s, %s, %s)",
          [
            recipe.id,
            recipe.name,
            recipe.description,
            recipe.category,
            recipe.created_at,
            recipe.updated_at,
          ],
        )
        self._write_versions(cur, recipe)
    except Exception as e:
      logger.error(f"Error adding recipe {recipe.id}: {e}")
      raise DatabaseError(f"Error adding recipe: {e}") from e

  def save(self, recipe: domain.Recipe) -> None:
    """Persist an existing recipe: its fields, its latest Ready version, and its
    Draft or the Draft's removal. Raises ``NotFoundError`` if the recipe row is
    gone."""
    try:
      with self._conn.cursor() as cur:
        cur.execute(
          "UPDATE recipes SET name = %s, description = %s, category = %s, "
          "updated_at = %s WHERE id = %s",
          [
            recipe.name,
            recipe.description,
            recipe.category,
            recipe.updated_at,
            recipe.id,
          ],
        )
        if cur.rowcount == 0:
          raise NotFoundError(f"Recipe {recipe.id} not found")
        self._write_versions(cur, recipe)
    except NotFoundError:
      raise
    except Exception as e:
      logger.error(f"Error saving recipe {recipe.id}: {e}")
      raise DatabaseError(f"Error saving recipe: {e}") from e

  def delete(self, recipe_id: UUID) -> bool:
    """Delete a recipe. Cascades to its versions. Returns False if it did not exist."""
    try:
      with self._conn.cursor() as cur:
        cur.execute("DELETE FROM recipes WHERE id = %s", [recipe_id])
        return cur.rowcount > 0
    except Exception as e:
      logger.error(f"Error deleting recipe {recipe_id}: {e}")
      raise DatabaseError(f"Error deleting recipe: {e}") from e

  # --- helpers --------------------------------------------------------

  def _write_versions(self, cur, recipe: domain.Recipe) -> None:
    """Write the latest Ready version first (on promotion this turns the Draft
    row Ready), then drop any other Draft row, then upsert the current Draft.
    Finally point ``current_version_id`` at the latest Ready version."""
    ready, draft = recipe.latest_ready, recipe.draft
    if ready is not None:
      self._upsert_version(cur, ready)
    cur.execute(
      "DELETE FROM recipe_versions WHERE recipe_id = %s AND state = 'draft' "
      "AND id IS DISTINCT FROM %s",
      [recipe.id, draft.id if draft else None],
    )
    if draft is not None:
      self._upsert_version(cur, draft)
    cur.execute(
      "UPDATE recipes SET current_version_id = %s WHERE id = %s",
      [ready.id if ready else None, recipe.id],
    )

  def _upsert_version(self, cur, v: domain.RecipeVersion) -> None:
    cur.execute(
      _UPSERT_VERSION,
      [
        v.id,
        v.recipe_id,
        v.state,
        v.version_number,
        v.release_note,
        _ingredients_json(v.ingredients),
        _instructions_json(v.instructions),
        v.created_at,
        json.dumps(v.change_summary) if v.change_summary is not None else None,
      ],
    )

  def _fetchone(self, query: str, params, what: str):
    try:
      with self._conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchone()
    except Exception as e:
      logger.error(f"Error ({what}): {e}")
      raise DatabaseError(f"Error {what}: {e}") from e

  def _fetchall(self, query: str, params, what: str):
    try:
      with self._conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()
    except Exception as e:
      logger.error(f"Error ({what}): {e}")
      raise DatabaseError(f"Error {what}: {e}") from e
