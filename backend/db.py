from contextlib import contextmanager
from datetime import date
from .config import Settings, get_settings
from .exceptions import DatabaseError
from .models import (
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse,
)
from psycopg_pool import ConnectionPool
from typing import Optional
from uuid import UUID

import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("psycopg")
logger.setLevel(logging.DEBUG)

db_logger = logging.getLogger("db")


def _build_conninfo(settings: Settings) -> str:
  url = urlparse(settings.database_url)
  parts = [
    f"host={url.hostname or 'localhost'}",
    f"port={url.port or 5432}",
    f"dbname={url.path.lstrip('/')}",
    f"user={url.username or ''}",
  ]
  if url.password:
    parts.append(f"password={url.password}")
  return " ".join(parts)


class DatabasePool:
  """Owns a psycopg connection pool. Construct one per process, in the app
  lifespan (or per test session); call ``close()`` on shutdown."""

  def __init__(self, settings: Optional[Settings] = None):
    settings = settings or get_settings()
    self.pool = ConnectionPool(
      _build_conninfo(settings),
      min_size=settings.pool_min_size,
      max_size=settings.pool_max_size,
      open=False,
    )
    self.pool.open()

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

  def getconn(self):
    """Check out a raw connection. The caller owns commit/rollback and must
    return it with ``putconn``. Used by ``UnitOfWork``."""
    conn = self.pool.getconn()
    logger.debug(f"Checked out connection: {conn}")
    return conn

  def putconn(self, conn):
    logger.debug(f"Returning connection: {conn}")
    self.pool.putconn(conn)

  def close(self):
    self.pool.close()


class DBConnector:
  """Bread-timing persistence. (Recipe persistence moved to
  ``infrastructure/recipe_repository.py``.)"""

  def __init__(self, db_pool: DatabasePool):
    self.db_pool = db_pool

  @staticmethod
  def _compute_timing_status(
    autolyse_ts,
    mix_ts,
    bulk_ts,
    preshape_ts,
    final_shape_ts,
    final_proof_ts,
    bake_ts,
  ) -> str:
    """A timing is complete when all 7 process timestamps are present."""
    complete = all(
      [
        autolyse_ts,
        mix_ts,
        bulk_ts,
        preshape_ts,
        final_shape_ts,
        final_proof_ts,
        bake_ts,
      ]
    )
    return "completed" if complete else "in_progress"

  def create_bread_timing(self, timing_data: BreadTimingCreate) -> BreadTiming:
    """Create a new bread timing record"""
    try:
      # Convert stretch_folds to JSON
      status = self._compute_timing_status(
        timing_data.autolyse_ts,
        timing_data.mix_ts,
        timing_data.bulk_ts,
        timing_data.preshape_ts,
        timing_data.final_shape_ts,
        timing_data.final_proof_ts,
        timing_data.bake_ts,
      )

      query = """
        INSERT INTO bread_timings (
          recipe_name, recipe_id, recipe_version_id,
          date, status, autolyse_ts, mix_ts, bulk_ts, preshape_ts,
          final_shape_ts, final_proof_ts, bake_ts, room_temp, water_temp, flour_temp,
          preferment_temp, dough_temp, temperature_unit, stretch_fold_count, notes, timezone
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id, created_at, updated_at
      """

      params = [
        timing_data.recipe_name,
        timing_data.recipe_id,
        timing_data.recipe_version_id,
        timing_data.date,
        status,
        timing_data.autolyse_ts,
        timing_data.mix_ts,
        timing_data.bulk_ts,
        timing_data.preshape_ts,
        timing_data.final_shape_ts,
        timing_data.final_proof_ts,
        timing_data.bake_ts,
        timing_data.room_temp,
        timing_data.water_temp,
        timing_data.flour_temp,
        timing_data.preferment_temp,
        timing_data.dough_temp,
        timing_data.temperature_unit,
        timing_data.stretch_fold_count,
        timing_data.notes,
        timing_data.timezone,
      ]

      with self.db_pool.get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(query, params)
          result = cur.fetchone()
          timing_id, created_at, updated_at = result
          conn.commit()

          return BreadTiming(
            id=timing_id,
            recipe_name=timing_data.recipe_name,
            recipe_id=timing_data.recipe_id,
            recipe_version_id=timing_data.recipe_version_id,
            date=timing_data.date,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            autolyse_ts=timing_data.autolyse_ts,
            mix_ts=timing_data.mix_ts,
            bulk_ts=timing_data.bulk_ts,
            preshape_ts=timing_data.preshape_ts,
            final_shape_ts=timing_data.final_shape_ts,
            final_proof_ts=timing_data.final_proof_ts,
            bake_ts=timing_data.bake_ts,
            room_temp=timing_data.room_temp,
            water_temp=timing_data.water_temp,
            flour_temp=timing_data.flour_temp,
            preferment_temp=timing_data.preferment_temp,
            dough_temp=timing_data.dough_temp,
            temperature_unit=timing_data.temperature_unit,
            stretch_fold_count=timing_data.stretch_fold_count,
            notes=timing_data.notes,
            timezone=timing_data.timezone,
          )

    except Exception as e:
      logger.error(f"Error creating bread timing: {str(e)}")
      raise DatabaseError(f"Failed to create bread timing: {str(e)}") from e

  def get_bread_timing(self, timing_id: UUID) -> Optional[BreadTiming]:
    """Get a specific bread timing by ID"""
    try:
      query = """
        SELECT id, recipe_name, recipe_id, recipe_version_id, date, status, created_at, updated_at,
               autolyse_ts, mix_ts, bulk_ts, preshape_ts, final_shape_ts, final_proof_ts, bake_ts,
               room_temp, water_temp, flour_temp, preferment_temp, dough_temp, temperature_unit,
               stretch_fold_count, notes, timezone
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
      raise DatabaseError(f"Failed to get bread timing: {str(e)}") from e

  def list_bread_timings(
    self,
    limit: int = 20,
    offset: int = 0,
    recipe_name: Optional[str] = None,
    status: Optional[str] = None,
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

      if status:
        where_conditions.append("status = %s")
        params.append(status)

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
      valid_order_fields = [
        "created_at",
        "updated_at",
        "date",
        "recipe_name",
        "bake_ts",
      ]
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
        SELECT id, recipe_name, recipe_id, recipe_version_id, date, status, created_at, updated_at,
               autolyse_ts, mix_ts, bulk_ts, preshape_ts, final_shape_ts, final_proof_ts, bake_ts,
               room_temp, water_temp, flour_temp, preferment_temp, dough_temp, temperature_unit,
               stretch_fold_count, notes, timezone
        FROM bread_timings
        {where_clause}
        ORDER BY {order_by} {order_direction.upper()} NULLS LAST
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
      raise DatabaseError(f"Failed to list bread timings: {str(e)}") from e

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
          conn.commit()

      # Re-fetch to get full current state, then recompute status
      updated_timing = self.get_bread_timing(timing_id)
      if not updated_timing:
        raise DatabaseError("Failed to retrieve updated timing")

      new_status = self._compute_timing_status(
        updated_timing.autolyse_ts,
        updated_timing.mix_ts,
        updated_timing.bulk_ts,
        updated_timing.preshape_ts,
        updated_timing.final_shape_ts,
        updated_timing.final_proof_ts,
        updated_timing.bake_ts,
      )
      if new_status != updated_timing.status:
        with self.db_pool.get_connection() as conn:
          with conn.cursor() as cur:
            cur.execute(
              "UPDATE bread_timings SET status = %s WHERE id = %s",
              [new_status, timing_id],
            )
            conn.commit()
        updated_timing = self.get_bread_timing(timing_id)

      return updated_timing

    except Exception as e:
      logger.error(f"Error updating bread timing {timing_id}: {str(e)}")
      raise DatabaseError(f"Failed to update bread timing: {str(e)}") from e

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
      raise DatabaseError(f"Failed to delete bread timing: {str(e)}") from e

  def _parse_timing_row(self, row) -> BreadTiming:
    """Helper method to parse a database row into a BreadTiming object"""
    (
      timing_id,
      recipe_name,
      recipe_id,
      recipe_version_id,
      date,
      status,
      created_at,
      updated_at,
      autolyse_ts,
      mix_ts,
      bulk_ts,
      preshape_ts,
      final_shape_ts,
      final_proof_ts,
      bake_ts,
      room_temp,
      water_temp,
      flour_temp,
      preferment_temp,
      dough_temp,
      temperature_unit,
      stretch_fold_count,
      notes,
      timezone,
    ) = row

    return BreadTiming(
      id=timing_id,
      recipe_name=recipe_name,
      recipe_id=recipe_id,
      recipe_version_id=recipe_version_id,
      date=date,
      status=status or "in_progress",
      created_at=created_at,
      updated_at=updated_at,
      autolyse_ts=autolyse_ts,
      mix_ts=mix_ts,
      bulk_ts=bulk_ts,
      preshape_ts=preshape_ts,
      final_shape_ts=final_shape_ts,
      final_proof_ts=final_proof_ts,
      bake_ts=bake_ts,
      room_temp=float(room_temp) if room_temp is not None else None,
      water_temp=float(water_temp) if water_temp is not None else None,
      flour_temp=float(flour_temp) if flour_temp is not None else None,
      preferment_temp=float(preferment_temp) if preferment_temp is not None else None,
      dough_temp=float(dough_temp) if dough_temp is not None else None,
      temperature_unit=temperature_unit or "Fahrenheit",
      stretch_fold_count=stretch_fold_count or 0,
      notes=notes,
      timezone=timezone or "UTC",
    )
