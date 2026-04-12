from contextlib import contextmanager
from datetime import date, datetime
from .exceptions import DatabaseError
from .models import (
  Recipe,
  RecipeStep,
  Ingredient,
  RecipeVersion,
  RecipeListItem,
  BakersPercentages,
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse,
  StretchFold,
)
from psycopg_pool import ConnectionPool
from psycopg import sql
from typing import List, Optional
from uuid import UUID

import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("psycopg")
logger.setLevel(logging.DEBUG)


class DatabasePool:
  _instance: Optional["DatabasePool"] = None

  def __init__(self, dbname: str, user: str, min_size: int = 2, max_size: int = 10):
    self.pool = ConnectionPool(
      f"dbname={dbname} user={user}", min_size=min_size, max_size=max_size
    )
    self.pool.open()

  @classmethod
  def get_instance(cls, dbname: str, user: str) -> "DatabasePool":
    if cls._instance is None:
      cls._instance = DatabasePool(dbname, user)
    return cls._instance

  @contextmanager
  def get_connection(self):
    conn = self.pool.getconn()
    logger.debug(f"Got connection from pool: {conn}")
    try:
      yield conn
    except Exception as e:
      logger.error(f"Error during database operation: {str(e)}")
      raise
    finally:
      logger.debug(f"Returning connection to pool: {conn}")
      self.pool.putconn(conn)

  def close(self):
    self.pool.close()


class DBConnector:
  USER = "sammylee"

  def __init__(self, dbname):
    self.user = DBConnector.USER
    self.dbname = dbname
    self.db_pool = DatabasePool.get_instance(self.dbname, self.user)

  def create_recipe(self, recipe_data: dict):
    """
    Create a new recipe in the database
    """
    insert_data = {
      "id": recipe_data["id"],
      "name": recipe_data["name"],
      "description": recipe_data["description"],
      "instructions": json.dumps(recipe_data["instructions"]),
      "flour_ingredients": json.dumps(recipe_data["flour_ingredients"]),
      "other_ingredients": json.dumps(recipe_data["other_ingredients"]),
    }

    # Filter out None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    # Build query using psycopg.sql for safety
    columns = sql.SQL(", ").join([sql.Identifier(k) for k in insert_data.keys()])
    placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in insert_data])
    values = list(insert_data.values())

    query = sql.SQL("""
      INSERT INTO recipes ({})
      VALUES ({});
    """).format(columns, placeholders)

    logger.debug(f"SQL Command\n {query}")
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, values)
          conn.commit()
    except Exception as e:
      logger.error(f"Error creating recipe: {str(e)}")
      raise DatabaseError(f"Error creating recipe: {e}")

  # New versioned recipe methods
  def create_versioned_recipe(self, recipe_data: dict) -> dict:
    """
    Create a new versioned recipe with initial version 1.0
    """
    recipe_id = recipe_data["id"]
    version_id = recipe_data.get("version_id")

    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          # Insert into recipes table
          cur.execute(
            """
            INSERT INTO recipes (id, name, description, category, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
          """,
            [
              recipe_id,
              recipe_data["name"],
              recipe_data.get("description"),
              recipe_data.get("category"),
              datetime.now(),
              datetime.now(),
            ],
          )

          # Insert initial version (v1)
          cur.execute(
            """
            INSERT INTO recipe_versions (id, recipe_id, version_number, 
                                       description, ingredients, instructions, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
          """,
            [
              version_id,
              recipe_id,
              1,
              recipe_data.get("version_description", "Initial version"),
              json.dumps({"ingredients": recipe_data["ingredients"]}),
              json.dumps({"instructions": recipe_data["instructions"]}),
              datetime.now(),
            ],
          )

          # Update current_version_id
          cur.execute(
            """
            UPDATE recipes SET current_version_id = %s WHERE id = %s
          """,
            [version_id, recipe_id],
          )

          # Insert baker's percentages if provided
          if recipe_data.get("bakers_percentages"):
            bp = recipe_data["bakers_percentages"]
            cur.execute(
              """
              INSERT INTO bakers_percentages (id, recipe_id, recipe_version_id, 
                                            total_flour_weight, flour_ingredients, other_ingredients)
              VALUES (%s, %s, %s, %s, %s, %s)
            """,
              [
                recipe_data.get("bp_id"),
                recipe_id,
                version_id,
                bp["total_flour_weight"],
                json.dumps(bp["flour_ingredients"]),
                json.dumps(bp["other_ingredients"]),
              ],
            )

          conn.commit()
          return {"recipe_id": recipe_id, "version_id": version_id}

    except Exception as e:
      logger.error(f"Error creating versioned recipe: {str(e)}")
      raise DatabaseError(f"Error creating versioned recipe: {e}")

  def create_recipe_version(self, version_data: dict) -> dict:
    """
    Create a new version of an existing recipe
    """
    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          # Insert new version
          cur.execute(
            """
            INSERT INTO recipe_versions (id, recipe_id, version_number,
                                       description, ingredients, instructions, created_at, change_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
          """,
            [
              version_data["id"],
              version_data["recipe_id"],
              version_data["version_number"],
              version_data.get("description"),
              json.dumps({"ingredients": version_data["ingredients"]}),
              json.dumps({"instructions": version_data["instructions"]}),
              datetime.now(),
              json.dumps(version_data.get("change_summary", {})),
            ],
          )

          # Update current_version_id
          cur.execute(
            """
            UPDATE recipes SET current_version_id = %s, updated_at = %s WHERE id = %s
          """,
            [version_data["id"], datetime.now(), version_data["recipe_id"]],
          )

          # Insert baker's percentages if provided
          if version_data.get("bakers_percentages"):
            bp = version_data["bakers_percentages"]
            cur.execute(
              """
              INSERT INTO bakers_percentages (id, recipe_id, recipe_version_id,
                                            total_flour_weight, flour_ingredients, other_ingredients)
              VALUES (%s, %s, %s, %s, %s, %s)
            """,
              [
                version_data.get("bp_id"),
                version_data["recipe_id"],
                version_data["id"],
                bp["total_flour_weight"],
                json.dumps(bp["flour_ingredients"]),
                json.dumps(bp["other_ingredients"]),
              ],
            )

          conn.commit()
          return {"version_id": version_data["id"]}

    except Exception as e:
      logger.error(f"Error creating recipe version: {str(e)}")
      raise DatabaseError(f"Error creating recipe version: {e}")

  def get_versioned_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
    """
    Get a versioned recipe with current version and baker's percentages
    """
    query = """
      SELECT r.id, r.name, r.description, r.category, r.current_version_id, r.created_at, r.updated_at,
             rv.id, rv.version_number, rv.description, rv.ingredients, rv.instructions, rv.created_at,
             bp.total_flour_weight, bp.flour_ingredients, bp.other_ingredients
      FROM recipes r
      LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
      LEFT JOIN bakers_percentages bp ON rv.id = bp.recipe_version_id
      WHERE r.id = %s
    """

    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          result = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting versioned recipe: {str(e)}")
      raise DatabaseError(f"Error getting versioned recipe: {e}")

    if not result:
      return None

    (
      r_id,
      r_name,
      r_description,
      r_category,
      r_current_version_id,
      r_created_at,
      r_updated_at,
      rv_id,
      rv_version_number,
      rv_description,
      rv_ingredients,
      rv_instructions,
      rv_created_at,
      bp_total_flour,
      bp_flour_ingredients,
      bp_other_ingredients,
    ) = result

    # Parse ingredients and instructions
    ingredients_data = rv_ingredients.get("ingredients", []) if rv_ingredients else []
    instructions_data = (
      rv_instructions.get("instructions", []) if rv_instructions else []
    )

    ingredients = [Ingredient(**ing) for ing in ingredients_data]
    instructions = [RecipeStep(**step) for step in instructions_data]

    # Create current version
    current_version = RecipeVersion(
      id=rv_id,
      recipe_id=r_id,
      version_number=rv_version_number,
      description=rv_description,
      ingredients=ingredients,
      instructions=instructions,
      created_at=rv_created_at,
    )

    # Create baker's percentages if available
    bakers_percentages = None
    if bp_total_flour is not None:
      bakers_percentages = BakersPercentages(
        total_flour_weight=bp_total_flour,
        flour_ingredients=bp_flour_ingredients,
        other_ingredients=bp_other_ingredients,
      )

    return Recipe(
      id=r_id,
      name=r_name,
      description=r_description,
      category=r_category,
      current_version_id=r_current_version_id,
      current_version=current_version,
      bakers_percentages=bakers_percentages,
      created_at=r_created_at,
      updated_at=r_updated_at,
    )

  def list_recipes(
    self, category: Optional[str] = None, limit: int = 50, offset: int = 0
  ) -> List[RecipeListItem]:
    """
    List recipes with basic info and current version
    """
    base_query = """
      SELECT r.id, r.name, r.category, r.created_at, r.updated_at,
             rv.version_number,
             jsonb_array_length(rv.ingredients->'ingredients') as ingredient_count,
             jsonb_array_length(rv.instructions->'instructions') as step_count
      FROM recipes r
      LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
    """

    conditions = []
    params = []

    if category:
      conditions.append("r.category = %s")
      params.append(category)

    if conditions:
      query = base_query + " WHERE " + " AND ".join(conditions)
    else:
      query = base_query

    query += " ORDER BY r.updated_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          results = cur.fetchall()
    except Exception as e:
      logger.error(f"Error listing recipes: {str(e)}")
      raise DatabaseError(f"Error listing recipes: {e}")

    recipes = []
    for result in results:
      (
        r_id,
        r_name,
        r_category,
        r_created_at,
        r_updated_at,
        rv_version_number,
        ingredient_count,
        step_count,
      ) = result

      version_str = str(rv_version_number) if rv_version_number is not None else "1"

      recipes.append(
        RecipeListItem(
          id=r_id,
          name=r_name,
          category=r_category,
          version=version_str,
          ingredient_count=ingredient_count or 0,
          step_count=step_count or 0,
          created_at=r_created_at,
          updated_at=r_updated_at,
        )
      )

    return recipes

  def get_recipe_versions(self, recipe_id: UUID) -> List[RecipeVersion]:
    """
    Get all versions of a recipe ordered by version number
    """
    query = """
      SELECT id, recipe_id, version_number, description, 
             ingredients, instructions, created_at, change_summary
      FROM recipe_versions
      WHERE recipe_id = %s
      ORDER BY version_number DESC
    """

    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          results = cur.fetchall()
    except Exception as e:
      logger.error(f"Error getting recipe versions: {str(e)}")
      raise DatabaseError(f"Error getting recipe versions: {e}")

    versions = []
    for result in results:
      (
        rv_id,
        rv_recipe_id,
        rv_version_number,
        rv_description,
        rv_ingredients,
        rv_instructions,
        rv_created_at,
        rv_change_summary,
      ) = result

      ingredients_data = rv_ingredients.get("ingredients", []) if rv_ingredients else []
      instructions_data = (
        rv_instructions.get("instructions", []) if rv_instructions else []
      )

      ingredients = [Ingredient(**ing) for ing in ingredients_data]
      instructions = [RecipeStep(**step) for step in instructions_data]

      versions.append(
        RecipeVersion(
          id=rv_id,
          recipe_id=rv_recipe_id,
          version_number=rv_version_number,
          description=rv_description,
          ingredients=ingredients,
          instructions=instructions,
          created_at=rv_created_at,
          change_summary=rv_change_summary,
        )
      )

    return versions

  def get_recipe_version(self, version_id: UUID) -> Optional[RecipeVersion]:
    """
    Get a specific recipe version by ID
    """
    query = """
      SELECT id, recipe_id, version_number, description,
             ingredients, instructions, created_at, change_summary
      FROM recipe_versions
      WHERE id = %s
    """

    try:
      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [version_id])
          result = cur.fetchone()
    except Exception as e:
      logger.error(f"Error getting recipe version: {str(e)}")
      raise DatabaseError(f"Error getting recipe version: {e}")

    if not result:
      return None

    (
      rv_id,
      rv_recipe_id,
      rv_version_number,
      rv_description,
      rv_ingredients,
      rv_instructions,
      rv_created_at,
      rv_change_summary,
    ) = result

    ingredients_data = rv_ingredients.get("ingredients", []) if rv_ingredients else []
    instructions_data = (
      rv_instructions.get("instructions", []) if rv_instructions else []
    )

    ingredients = [Ingredient(**ing) for ing in ingredients_data]
    instructions = [RecipeStep(**step) for step in instructions_data]

    return RecipeVersion(
      id=rv_id,
      recipe_id=rv_recipe_id,
      version_number=rv_version_number,
      description=rv_description,
      ingredients=ingredients,
      instructions=instructions,
      created_at=rv_created_at,
      change_summary=rv_change_summary,
    )

  def update_recipe_basic_fields(self, recipe_id: UUID, updates: dict):
    """
    Update basic recipe fields (name, description, category, current_version_id, updated_at)
    Used by the PATCH endpoint to update recipe metadata after creating a new version.
    """
    try:
      # Build dynamic update query based on provided fields
      update_fields = []
      params = []

      for field, value in updates.items():
        if field in [
          "name",
          "description",
          "category",
          "current_version_id",
          "updated_at",
        ]:
          update_fields.append(f"{field} = %s")
          params.append(value)
        else:
          logger.warning(f"Skipping unknown field in update: {field}")

      if not update_fields:
        return  # Nothing to update

      # Add recipe_id parameter for WHERE clause
      params.append(recipe_id)

      query = f"UPDATE recipes SET {', '.join(update_fields)} WHERE id = %s"

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          if cur.rowcount == 0:
            raise ValueError(f"Recipe with ID {recipe_id} not found")

    except Exception as e:
      logger.error(f"Error updating recipe basic fields: {str(e)}")
      raise DatabaseError(f"Failed to update recipe basic fields: {str(e)}")

  def delete_recipe(self, recipe_id: UUID) -> bool:
    """
    Delete a recipe and all its associated data.
    The CASCADE constraints will automatically delete recipe_versions and bakers_percentages.
    """
    try:
      query = "DELETE FROM recipes WHERE id = %s"

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [recipe_id])
          rows_deleted = cur.rowcount

      # Return True if a row was deleted, False if recipe didn't exist
      return rows_deleted > 0

    except Exception as e:
      logger.error(f"Error deleting recipe: {str(e)}")
      raise DatabaseError(f"Failed to delete recipe: {str(e)}")

  # New Bread Timing Methods for REST API

  def create_bread_timing(self, timing_data: BreadTimingCreate) -> BreadTiming:
    """Create a new bread timing record"""
    try:
      # Convert stretch_folds to JSON
      stretch_folds_json = (
        json.dumps(
          [
            {"fold_number": sf.fold_number, "timestamp": sf.timestamp.isoformat()}
            for sf in timing_data.stretch_folds
          ]
        )
        if timing_data.stretch_folds
        else "[]"
      )

      query = """
        INSERT INTO bread_timings (
          recipe_name, date, autolyse_ts, mix_ts, bulk_ts, preshape_ts, 
          final_shape_ts, fridge_ts, room_temp, water_temp, flour_temp, 
          preferment_temp, dough_temp, temperature_unit, stretch_folds, notes
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id, created_at, updated_at
      """

      params = [
        timing_data.recipe_name,
        timing_data.date,
        timing_data.autolyse_ts,
        timing_data.mix_ts,
        timing_data.bulk_ts,
        timing_data.preshape_ts,
        timing_data.final_shape_ts,
        timing_data.fridge_ts,
        timing_data.room_temp,
        timing_data.water_temp,
        timing_data.flour_temp,
        timing_data.preferment_temp,
        timing_data.dough_temp,
        timing_data.temperature_unit,
        stretch_folds_json,
        timing_data.notes,
      ]

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          result = cur.fetchone()
          timing_id, created_at, updated_at = result
          conn.commit()  # Explicitly commit the transaction

          # Return the created timing
          return BreadTiming(
            id=timing_id,
            recipe_name=timing_data.recipe_name,
            date=timing_data.date,
            created_at=created_at,
            updated_at=updated_at,
            autolyse_ts=timing_data.autolyse_ts,
            mix_ts=timing_data.mix_ts,
            bulk_ts=timing_data.bulk_ts,
            preshape_ts=timing_data.preshape_ts,
            final_shape_ts=timing_data.final_shape_ts,
            fridge_ts=timing_data.fridge_ts,
            room_temp=timing_data.room_temp,
            water_temp=timing_data.water_temp,
            flour_temp=timing_data.flour_temp,
            preferment_temp=timing_data.preferment_temp,
            dough_temp=timing_data.dough_temp,
            temperature_unit=timing_data.temperature_unit,
            stretch_folds=timing_data.stretch_folds,
            notes=timing_data.notes,
          )

    except Exception as e:
      logger.error(f"Error creating bread timing: {str(e)}")
      raise DatabaseError(f"Failed to create bread timing: {str(e)}")

  def get_bread_timing(self, timing_id: UUID) -> Optional[BreadTiming]:
    """Get a specific bread timing by ID"""
    try:
      query = """
        SELECT id, recipe_name, date, created_at, updated_at, autolyse_ts, mix_ts, 
               bulk_ts, preshape_ts, final_shape_ts, fridge_ts, room_temp, water_temp, 
               flour_temp, preferment_temp, dough_temp, temperature_unit, stretch_folds, notes
        FROM bread_timings 
        WHERE id = %s
      """

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [timing_id])
          result = cur.fetchone()

          if not result:
            return None

          # Parse the row data
          return self._parse_timing_row(result)

    except Exception as e:
      logger.error(f"Error getting bread timing {timing_id}: {str(e)}")
      raise DatabaseError(f"Failed to get bread timing: {str(e)}")

  def list_bread_timings(
    self,
    limit: int = 20,
    offset: int = 0,
    recipe_name: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    order_by: str = "created_at",
    order_direction: str = "desc",
  ) -> BreadTimingListResponse:
    """List bread timings with pagination and filtering"""
    try:
      # Build WHERE clause
      where_conditions = []
      params = []

      if recipe_name:
        where_conditions.append("recipe_name = %s")
        params.append(recipe_name)

      if date_from:
        where_conditions.append("date >= %s")
        params.append(date_from)

      if date_to:
        where_conditions.append("date <= %s")
        params.append(date_to)

      if search:
        where_conditions.append("notes ILIKE %s")
        params.append(f"%{search}%")

      where_clause = (
        "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
      )

      # Validate order_by field
      valid_order_fields = ["created_at", "updated_at", "date", "recipe_name"]
      if order_by not in valid_order_fields:
        raise ValueError(
          f"Invalid order_by field. Must be one of: {valid_order_fields}"
        )

      # Validate order_direction
      if order_direction.lower() not in ["asc", "desc"]:
        raise ValueError("order_direction must be 'asc' or 'desc'")

      # Count total records
      count_query = f"SELECT COUNT(*) FROM bread_timings {where_clause}"

      # Main query
      main_query = f"""
        SELECT id, recipe_name, date, created_at, updated_at, autolyse_ts, mix_ts, 
               bulk_ts, preshape_ts, final_shape_ts, fridge_ts, room_temp, water_temp, 
               flour_temp, preferment_temp, dough_temp, temperature_unit, stretch_folds, notes
        FROM bread_timings 
        {where_clause}
        ORDER BY {order_by} {order_direction.upper()}
        LIMIT %s OFFSET %s
      """

      # Add limit and offset to params
      main_params = params + [limit, offset]

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          # Get total count
          cur.execute(count_query, params)
          total_count = cur.fetchone()[0]

          # Get paginated results
          cur.execute(main_query, main_params)
          results = cur.fetchall()

          # Parse timing records
          timings = [self._parse_timing_row(row) for row in results]

          # Calculate pagination metadata
          page = (offset // limit) + 1
          total_pages = (total_count + limit - 1) // limit
          has_next = offset + limit < total_count
          has_previous = offset > 0

          return BreadTimingListResponse(
            timings=timings,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
          )

    except Exception as e:
      logger.error(f"Error listing bread timings: {str(e)}")
      raise DatabaseError(f"Failed to list bread timings: {str(e)}")

  def update_bread_timing(
    self, timing_id: UUID, updates: BreadTimingUpdate
  ) -> BreadTiming:
    """Update a bread timing record"""
    try:
      # Build UPDATE clause dynamically
      update_fields = []
      params = []

      # Get update data, excluding None values
      update_data = updates.model_dump(exclude_none=True)

      if not update_data:
        raise ValueError("No valid fields to update")

      for field, value in update_data.items():
        if field == "stretch_folds":
          # Convert stretch folds to JSON
          if value:
            stretch_folds_list = []
            for sf in value:
              if hasattr(sf, "fold_number"):  # StretchFold object
                stretch_folds_list.append(
                  {"fold_number": sf.fold_number, "timestamp": sf.timestamp.isoformat()}
                )
              else:  # dict object
                stretch_folds_list.append(
                  {
                    "fold_number": sf["fold_number"],
                    "timestamp": sf["timestamp"].isoformat()
                    if hasattr(sf["timestamp"], "isoformat")
                    else sf["timestamp"],
                  }
                )
            stretch_folds_json = json.dumps(stretch_folds_list)
          else:
            stretch_folds_json = "[]"
          update_fields.append("stretch_folds = %s")
          params.append(stretch_folds_json)
        else:
          update_fields.append(f"{field} = %s")
          params.append(value)

      # Add timing_id for WHERE clause
      params.append(timing_id)

      query = f"""
        UPDATE bread_timings 
        SET {", ".join(update_fields)}
        WHERE id = %s
      """

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          if cur.rowcount == 0:
            raise ValueError(f"Bread timing with ID {timing_id} not found")
          conn.commit()  # Explicitly commit the transaction

      # Return the updated timing
      updated_timing = self.get_bread_timing(timing_id)
      if not updated_timing:
        raise DatabaseError("Failed to retrieve updated timing")

      return updated_timing

    except Exception as e:
      logger.error(f"Error updating bread timing {timing_id}: {str(e)}")
      raise DatabaseError(f"Failed to update bread timing: {str(e)}")

  def delete_bread_timing(self, timing_id: UUID) -> bool:
    """Delete a bread timing record"""
    try:
      query = "DELETE FROM bread_timings WHERE id = %s"

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, [timing_id])
          rows_deleted = cur.rowcount
          conn.commit()  # Explicitly commit the transaction

      return rows_deleted > 0

    except Exception as e:
      logger.error(f"Error deleting bread timing {timing_id}: {str(e)}")
      raise DatabaseError(f"Failed to delete bread timing: {str(e)}")

  def _parse_timing_row(self, row) -> BreadTiming:
    """Helper method to parse a database row into a BreadTiming object"""
    (
      timing_id,
      recipe_name,
      date,
      created_at,
      updated_at,
      autolyse_ts,
      mix_ts,
      bulk_ts,
      preshape_ts,
      final_shape_ts,
      fridge_ts,
      room_temp,
      water_temp,
      flour_temp,
      preferment_temp,
      dough_temp,
      temperature_unit,
      stretch_folds_json,
      notes,
    ) = row

    # Parse stretch_folds JSON
    stretch_folds = []
    if stretch_folds_json:
      try:
        if isinstance(stretch_folds_json, list):
          stretch_folds_data = stretch_folds_json
        else:
          stretch_folds_data = json.loads(stretch_folds_json)

        for fold in stretch_folds_data:
          if isinstance(fold, dict) and "fold_number" in fold and "timestamp" in fold:
            stretch_folds.append(
              StretchFold(
                fold_number=fold["fold_number"],
                timestamp=datetime.fromisoformat(fold["timestamp"]),
              )
            )
      except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"Invalid stretch_folds JSON for timing {timing_id}: {e}")

    return BreadTiming(
      id=timing_id,
      recipe_name=recipe_name,
      date=date,
      created_at=created_at,
      updated_at=updated_at,
      autolyse_ts=autolyse_ts,
      mix_ts=mix_ts,
      bulk_ts=bulk_ts,
      preshape_ts=preshape_ts,
      final_shape_ts=final_shape_ts,
      fridge_ts=fridge_ts,
      room_temp=float(room_temp) if room_temp is not None else None,
      water_temp=float(water_temp) if water_temp is not None else None,
      flour_temp=float(flour_temp) if flour_temp is not None else None,
      preferment_temp=float(preferment_temp) if preferment_temp is not None else None,
      dough_temp=float(dough_temp) if dough_temp is not None else None,
      temperature_unit=temperature_unit or "Fahrenheit",
      stretch_folds=stretch_folds,
      notes=notes,
    )
