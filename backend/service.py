from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import date, datetime
from .config import get_settings
from .db import DatabasePool, DBConnector
from .exceptions import ConflictError, DatabaseError, DomainError, NotFoundError
from .api.schemas import (
  Recipe,
  RecipeCreateResponse,
  RecipeListItem,
  RecipeRequest,
  RecipeVersion,
  RecipeVersionRequest,
)
from .models import (
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse,
)
from typing import List, Optional
from uuid import UUID

import logging

from .application.recipe_service import RecipeService
from .infrastructure.unit_of_work import UnitOfWork

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("service")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Open the database pool on startup, close it on shutdown."""
  app.state.pool = DatabasePool(get_settings())
  logger.info("database pool opened")
  try:
    yield
  finally:
    app.state.pool.close()
    logger.info("database pool closed")


app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
  CORSMiddleware,
  allow_origins=list(get_settings().allowed_origins),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# --- Exception handlers --------------------------------------------------
# One place translates application/domain errors to HTTP responses, so the
# recipe routes stay free of try/except ladders. (Timing routes still handle
# their own errors inline until Part IV.)


@app.exception_handler(NotFoundError)
async def _handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
  return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def _handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
  return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DomainError)
async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
  return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(DatabaseError)
async def _handle_database_error(request: Request, exc: DatabaseError) -> JSONResponse:
  logger.error(f"{request.method} {request.url.path} - database error: {exc}")
  return JSONResponse(status_code=500, content={"detail": f"Database error: {exc}"})


# --- Dependency providers -------------------------------------------------
# Wiring lives here and only here: routes receive their collaborators, they
# never reach for a module global.


def get_pool(request: Request) -> DatabasePool:
  return request.app.state.pool


def get_db(pool: DatabasePool = Depends(get_pool)) -> DBConnector:
  return DBConnector(pool)


def get_recipe_service(pool: DatabasePool = Depends(get_pool)) -> RecipeService:
  return RecipeService(lambda: UnitOfWork(pool))


# Versioned recipe endpoints. These routes only translate HTTP <-> service call;
# errors are turned into responses by the handlers registered above.


@app.post("/recipes/", response_model=Recipe, status_code=201)
def create_recipe(
  recipe: RecipeRequest,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Create a new versioned recipe with initial version 1."""
  return recipe_service.create_recipe(recipe)


@app.get("/recipes/", response_model=List[RecipeListItem])
def list_recipes(
  category: str = None,
  limit: int = 50,
  offset: int = 0,
  search: str = None,
  sort_by: str = "created_at",
  sort_direction: str = "desc",
  ingredient: str = None,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """List recipes with pagination, optional category/ingredient filter, search, and sorting."""
  return recipe_service.list_recipes(
    category=category,
    limit=limit,
    offset=offset,
    search=search,
    sort_by=sort_by,
    sort_direction=sort_direction,
    ingredient=ingredient,
  )


@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(
  recipe_id: UUID,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Get a versioned recipe by ID with its current version."""
  recipe = recipe_service.get_recipe(recipe_id)
  if recipe is None:
    raise HTTPException(status_code=404, detail="Recipe not found")
  return recipe


@app.patch("/recipes/{recipe_id}", response_model=RecipeCreateResponse)
def update_recipe(
  recipe_id: UUID,
  recipe_data: RecipeRequest,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Update a recipe: add a new version and move the current-version pointer.

  Takes the same complete JSON body as recipe creation.
  """
  updated_recipe = recipe_service.update_recipe_full(recipe_id, recipe_data)
  return RecipeCreateResponse(
    recipe=updated_recipe,
    message=(
      f"Recipe '{updated_recipe.name}' updated successfully to version "
      f"{updated_recipe.current_version.version_number}"
    ),
    success=True,
  )


@app.delete("/recipes/{recipe_id}")
def delete_recipe(
  recipe_id: UUID,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Delete a recipe and (via cascade) all its versions."""
  recipe_service.delete_recipe(recipe_id)
  return {"message": "Recipe deleted successfully", "success": True}


@app.post("/recipes/{recipe_id}/versions", response_model=Recipe)
def create_recipe_version(
  recipe_id: UUID,
  version_request: RecipeVersionRequest,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Manually add a new version to an existing recipe."""
  return recipe_service.create_recipe_version(
    recipe_id=recipe_id,
    ingredients=version_request.ingredients,
    instructions=version_request.instructions,
    description=version_request.description,
  )


@app.get("/recipes/{recipe_id}/versions", response_model=List[RecipeVersion])
def get_recipe_versions(
  recipe_id: UUID,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Get all versions of a recipe, newest first."""
  return recipe_service.get_recipe_versions(recipe_id)


@app.get("/recipes/{recipe_id}/versions/{version_id_1}/diff/{version_id_2}")
def get_version_diff(
  recipe_id: UUID,
  version_id_1: UUID,
  version_id_2: UUID,
  recipe_service: RecipeService = Depends(get_recipe_service),
):
  """Get the diff between two versions of a recipe. Both must belong to ``recipe_id``."""
  return recipe_service.get_recipe_version_diff(recipe_id, version_id_1, version_id_2)


def validate_date(year: int, month: int, day: int) -> date:
  """
  Validate and return a date object.
  """
  try:
    return date(year, month, day)
  except ValueError as e:
    raise ValueError(f"Invalid date {month}/{day}/{year}: {str(e)}")


# New Bread Timing REST API Endpoints


@app.post("/timings", response_model=BreadTiming, status_code=201)
def create_timing(
  timing: BreadTimingCreate,
  db_conn: DBConnector = Depends(get_db),
):
  """Create a new bread timing record"""
  logger.info(f"POST /timings - Creating timing: {timing.model_dump()}")
  try:
    # Validate timing data (relaxed validation for partial data)
    validate_timing_data(timing)

    # Calculate status based on data completeness
    timing_dict = timing.model_dump(exclude_none=True)
    status = calculate_timing_status(timing_dict)

    # Create a new timing object with the calculated status
    timing_with_status = BreadTimingCreate(**timing_dict, status=status)

    created_timing = db_conn.create_bread_timing(timing_with_status)
    logger.info(
      f"POST /timings - Successfully created timing with ID: {created_timing.id}, status: {status}"
    )
    return created_timing

  except ValueError as e:
    logger.error(f"POST /timings - Validation error: {str(e)}")
    raise HTTPException(status_code=422, detail=str(e))
  except DatabaseError as e:
    logger.error(f"POST /timings - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  except Exception as e:
    logger.error(f"POST /timings - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/timings", response_model=BreadTimingListResponse)
def list_timings(
  page: int = 1,
  limit: int = 20,
  recipe_name: Optional[str] = None,
  status: Optional[str] = None,
  date: Optional[str] = None,
  date_from: Optional[str] = None,
  date_to: Optional[str] = None,
  search: Optional[str] = None,
  sort_by: str = "updated_at",
  order_direction: str = "desc",
  db_conn: DBConnector = Depends(get_db),
):
  """List bread timings with pagination and filtering"""
  logger.info(
    f"GET /timings - Listing timings with filters: page={page}, limit={limit}, recipe_name={recipe_name}, status={status}, sort_by={sort_by}"
  )

  try:
    # Validate pagination parameters
    if page < 1:
      raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if limit < 1 or limit > 100:
      raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    # Validate status filter
    if status and status not in ["in_progress", "completed"]:
      raise HTTPException(
        status_code=400, detail="Status must be 'in_progress' or 'completed'"
      )

    # Validate sort_by parameter
    valid_sort_fields = ["created_at", "updated_at", "date", "recipe_name", "bake_ts"]
    if sort_by not in valid_sort_fields:
      raise HTTPException(
        status_code=400, detail=f"sort_by must be one of {valid_sort_fields}"
      )

    # Calculate offset
    offset = (page - 1) * limit

    # Parse date filters
    date_from_obj = None
    date_to_obj = None

    if date:
      # Single date filter
      try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        date_from_obj = date_to_obj = date_obj
      except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")

    if date_from:
      try:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
      except ValueError:
        raise HTTPException(
          status_code=400, detail="date_from must be in YYYY-MM-DD format"
        )

    if date_to:
      try:
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
      except ValueError:
        raise HTTPException(
          status_code=400, detail="date_to must be in YYYY-MM-DD format"
        )

    response = db_conn.list_bread_timings(
      limit=limit,
      offset=offset,
      recipe_name=recipe_name,
      status=status,
      date_from=date_from_obj,
      date_to=date_to_obj,
      search=search,
      order_by=sort_by,
      order_direction=order_direction,
    )

    logger.info(
      f"GET /timings - Successfully retrieved {len(response.timings)} timings"
    )
    return response

  except HTTPException:
    raise
  except ValueError as e:
    logger.error(f"GET /timings - Validation error: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
  except DatabaseError as e:
    logger.error(f"GET /timings - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  except Exception as e:
    logger.error(f"GET /timings - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/timings/{timing_id}", response_model=BreadTiming)
def get_timing(
  timing_id: UUID,
  db_conn: DBConnector = Depends(get_db),
):
  """Get a specific bread timing by ID"""
  logger.info(f"GET /timings/{timing_id} - Getting timing")

  try:
    timing = db_conn.get_bread_timing(timing_id)
    if not timing:
      logger.info(f"GET /timings/{timing_id} - Timing not found")
      raise HTTPException(
        status_code=404,
        detail="Bread timing not found",
        headers={"timing_id": str(timing_id)},
      )

    logger.info(f"GET /timings/{timing_id} - Successfully retrieved timing")
    return timing

  except HTTPException:
    raise
  except DatabaseError as e:
    logger.error(f"GET /timings/{timing_id} - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  except Exception as e:
    logger.error(f"GET /timings/{timing_id} - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.patch("/timings/{timing_id}", response_model=BreadTiming)
def update_timing(
  timing_id: UUID,
  updates: BreadTimingUpdate,
  db_conn: DBConnector = Depends(get_db),
):
  """Update a bread timing record"""
  logger.info(
    f"PATCH /timings/{timing_id} - Updating timing with data: {updates.model_dump(exclude_none=True)}"
  )

  try:
    # Check if timing exists first
    existing_timing = db_conn.get_bread_timing(timing_id)
    if not existing_timing:
      logger.info(f"PATCH /timings/{timing_id} - Timing not found")
      raise HTTPException(
        status_code=404,
        detail="Bread timing not found",
        headers={"timing_id": str(timing_id)},
      )

    # Validate update data
    validate_timing_updates(updates, existing_timing)

    # Calculate new status if not explicitly set
    update_data = updates.model_dump(exclude_none=True)
    if "status" not in update_data:
      # Merge existing data with updates to calculate new status
      merged_data = existing_timing.model_dump()
      merged_data.update(update_data)
      new_status = calculate_timing_status(merged_data)
      update_data["status"] = new_status

      # Create a new BreadTimingUpdate object with the calculated status
      updates = BreadTimingUpdate(**update_data)

    updated_timing = db_conn.update_bread_timing(timing_id, updates)
    logger.info(
      f"PATCH /timings/{timing_id} - Successfully updated timing, new status: {updated_timing.status}"
    )
    return updated_timing

  except HTTPException:
    raise
  except ValueError as e:
    logger.error(f"PATCH /timings/{timing_id} - Validation error: {str(e)}")
    raise HTTPException(status_code=422, detail=str(e))
  except DatabaseError as e:
    logger.error(f"PATCH /timings/{timing_id} - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  except Exception as e:
    logger.error(f"PATCH /timings/{timing_id} - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.delete("/timings/{timing_id}")
def delete_timing(
  timing_id: UUID,
  db_conn: DBConnector = Depends(get_db),
):
  """Delete a bread timing record"""
  logger.info(f"DELETE /timings/{timing_id} - Deleting timing")

  try:
    deleted = db_conn.delete_bread_timing(timing_id)
    if not deleted:
      logger.info(f"DELETE /timings/{timing_id} - Timing not found")
      raise HTTPException(
        status_code=404,
        detail="Bread timing not found",
        headers={"timing_id": str(timing_id)},
      )

    logger.info(f"DELETE /timings/{timing_id} - Successfully deleted timing")
    return Response(status_code=204)

  except HTTPException:
    raise
  except DatabaseError as e:
    logger.error(f"DELETE /timings/{timing_id} - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  except Exception as e:
    logger.error(f"DELETE /timings/{timing_id} - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Status calculation and validation functions for timing data


def calculate_timing_status(timing_data: dict) -> str:
  """
  Calculate the completion status of a timing based on required fields.
  Returns 'completed' if all 7 process timestamps are populated, 'in_progress' otherwise.
  """
  required_fields = [
    "autolyse_ts",
    "mix_ts",
    "bulk_ts",
    "preshape_ts",
    "final_shape_ts",
    "final_proof_ts",
    "bake_ts",
  ]

  for field in required_fields:
    if timing_data.get(field) is None:
      return "in_progress"

  return "completed"


def validate_timing_data(timing: BreadTimingCreate) -> None:
  """Validate timing data for creation"""

  if not timing.recipe_name:
    raise ValueError("recipe_name is required")
  if not timing.date:
    raise ValueError("date is required")

  # Validate timestamp ordering
  timestamps = [
    ("autolyse_ts", timing.autolyse_ts),
    ("mix_ts", timing.mix_ts),
    ("bulk_ts", timing.bulk_ts),
    ("preshape_ts", timing.preshape_ts),
    ("final_shape_ts", timing.final_shape_ts),
    ("final_proof_ts", timing.final_proof_ts),
    ("bake_ts", timing.bake_ts),
  ]

  # Filter out None timestamps and validate order
  valid_timestamps = [(name, ts) for name, ts in timestamps if ts is not None]

  for i in range(len(valid_timestamps) - 1):
    current_name, current_ts = valid_timestamps[i]
    next_name, next_ts = valid_timestamps[i + 1]

    if current_ts > next_ts:
      raise ValueError(f"{next_name} must be after {current_name}")


def validate_timing_updates(updates: BreadTimingUpdate, existing: BreadTiming) -> None:
  """Validate timing update data"""

  # Prevent updating certain fields
  update_data = updates.model_dump(exclude_none=True)

  forbidden_fields = ["date", "created_at", "id"]
  for field in forbidden_fields:
    if field in update_data:
      raise ValueError(f"{field} cannot be modified")

  # If updating timestamps, validate ordering with existing data
  if any(field.endswith("_ts") for field in update_data):
    # Create merged timestamp data for validation
    merged_data = {
      "autolyse_ts": updates.autolyse_ts
      if updates.autolyse_ts is not None
      else existing.autolyse_ts,
      "mix_ts": updates.mix_ts if updates.mix_ts is not None else existing.mix_ts,
      "bulk_ts": updates.bulk_ts if updates.bulk_ts is not None else existing.bulk_ts,
      "preshape_ts": updates.preshape_ts
      if updates.preshape_ts is not None
      else existing.preshape_ts,
      "final_shape_ts": updates.final_shape_ts
      if updates.final_shape_ts is not None
      else existing.final_shape_ts,
      "final_proof_ts": updates.final_proof_ts
      if updates.final_proof_ts is not None
      else existing.final_proof_ts,
      "bake_ts": updates.bake_ts if updates.bake_ts is not None else existing.bake_ts,
    }

    # Validate merged timestamps
    timestamps = [(name, ts) for name, ts in merged_data.items() if ts is not None]
    timestamps.sort(key=lambda x: x[1])  # Sort by timestamp

    for i in range(len(timestamps) - 1):
      current_name, current_ts = timestamps[i]
      next_name, next_ts = timestamps[i + 1]

      if current_ts > next_ts:
        raise ValueError(f"{next_name} must be after {current_name}")
