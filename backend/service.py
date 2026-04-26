from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import date, datetime
from .db import DBConnector
from .exceptions import DatabaseError
from .models import (
  Recipe,
  RecipeRequest,
  RecipeVersionRequest,
  RecipeListItem,
  RecipeVersion,
  RecipeCreateResponse,
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse,
)
from typing import List, Optional
from uuid import UUID

import logging

# Import recipe service
from .recipe_service import RecipeService

app = FastAPI()

# Configure CORS
app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "*"
  ],  # For development only - replace with specific origins in production
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

DBNAME = "bread_makes"
db_conn = DBConnector(dbname=DBNAME)
recipe_service = RecipeService(db_conn)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("service")
logger.setLevel(logging.DEBUG)
logger.info("app brought up")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# UserContext class to hold user information
class UserContext:
  def __init__(self, user_id: UUID, account_id: UUID, account_name: str):
    self.user_id = user_id
    self.account_id = account_id
    self.account_name = account_name


# Dependency to get the current user context
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
  """
  Verify the authentication token and return user context
  In a real implementation, you would:
  1. Validate the JWT token
  2. Extract user_id from token
  3. Look up user and account information
  """
  try:
    # Mock implementation - in reality, you'd decode the JWT and look up user info
    # This would be replaced with actual token validation and user lookup
    user_id = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")  # Example user ID
    account_id = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")  # Example account ID
    account_name = "Rize Up"

    return UserContext(
      user_id=user_id, account_id=account_id, account_name=account_name
    )
  except Exception as e:
    logger.error(f"Authentication error: {str(e)}")
    raise HTTPException(
      status_code=401,
      detail="Invalid authentication credentials",
      headers={"WWW-Authenticate": "Bearer"},
    )


# New versioned recipe endpoints
@app.post("/recipes/", response_model=Recipe, status_code=201)
def create_recipe(recipe: RecipeRequest):
  """
  Create a new versioned recipe with initial version 1.0
  """
  logger.info(f"POST /recipes/ - Creating recipe: {recipe.model_dump()}")
  try:
    recipe_obj = recipe_service.create_recipe(recipe)
    logger.info(
      f"POST /recipes/ - Successfully created recipe '{recipe_obj.name}' with ID: {recipe_obj.id}"
    )
    return recipe_obj

  except DatabaseError as e:
    logger.error(f"POST /recipes/ - Database error creating recipe: {str(e)}")
    raise HTTPException(
      status_code=500, detail="Failed to create recipe due to database error"
    )

  except ValueError as e:
    logger.error(f"POST /recipes/ - Validation error creating recipe: {str(e)}")
    raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

  except Exception as e:
    logger.error(f"POST /recipes/ - Unexpected error creating recipe: {str(e)}")
    raise HTTPException(
      status_code=500,
      detail="An unexpected error occurred while creating the recipe",
    )


@app.get("/recipes/", response_model=List[RecipeListItem])
def list_recipes(
  category: str = None,
  limit: int = 50,
  offset: int = 0,
  search: str = None,
  sort_by: str = "created_at",
  sort_direction: str = "desc",
  ingredient: str = None,
):
  """
  List recipes with pagination, optional category filter, search, ingredient filter, and sorting
  """
  logger.info(
    f"GET /recipes/ - Listing recipes with category={category}, search={search}, ingredient={ingredient}, sort_by={sort_by}, sort_direction={sort_direction}"
  )
  try:
    recipes = recipe_service.list_recipes(
      category=category,
      limit=limit,
      offset=offset,
      search=search,
      sort_by=sort_by,
      sort_direction=sort_direction,
      ingredient=ingredient,
    )
    logger.info(f"GET /recipes/ - Successfully retrieved {len(recipes)} recipes")
    return recipes

  except Exception as e:
    logger.error(f"GET /recipes/ - Error listing recipes: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: UUID):
  """
  Get a versioned recipe by ID with current version and baker's percentages
  """
  try:
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
      raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe

  except DatabaseError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"Error getting recipe: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.patch("/recipes/{recipe_id}", response_model=RecipeCreateResponse)
def update_recipe(recipe_id: UUID, recipe_data: RecipeRequest):
  """
  Update a recipe - creates new version and updates current_version_id
  Uses the same complete JSON body structure as POST creation
  """
  logger.info(
    f"PATCH /recipes/{recipe_id} - Updating recipe with data: {recipe_data.dict()}"
  )
  try:
    updated_recipe = recipe_service.update_recipe_full(recipe_id, recipe_data)
    response = RecipeCreateResponse(
      recipe=updated_recipe,
      message=f"Recipe '{updated_recipe.name}' updated successfully to version {updated_recipe.current_version.version_number}",
      success=True,
    )
    logger.info(
      f"PATCH /recipes/{recipe_id} - Successfully updated recipe to version {updated_recipe.current_version.version_number}"
    )
    return response

  except ValueError as e:
    logger.error(f"PATCH /recipes/{recipe_id} - Recipe not found: {str(e)}")
    raise HTTPException(status_code=404, detail=str(e))
  except DatabaseError as e:
    logger.error(f"PATCH /recipes/{recipe_id} - Database error: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"PATCH /recipes/{recipe_id} - Error updating recipe: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: UUID):
  """
  Delete a recipe and all its versions and baker's percentages
  """
  logger.info(f"DELETE /recipes/{recipe_id} - Deleting recipe")
  try:
    success = recipe_service.delete_recipe(recipe_id)
    if success:
      logger.info(f"DELETE /recipes/{recipe_id} - Successfully deleted recipe")
      return {"message": "Recipe deleted successfully", "success": True}
    else:
      logger.error(f"DELETE /recipes/{recipe_id} - Recipe not found")
      raise HTTPException(status_code=404, detail="Recipe not found")

  except ValueError as e:
    logger.error(f"DELETE /recipes/{recipe_id} - Recipe not found: {str(e)}")
    raise HTTPException(status_code=404, detail=str(e))
  except DatabaseError as e:
    logger.error(f"DELETE /recipes/{recipe_id} - Database error: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"DELETE /recipes/{recipe_id} - Error deleting recipe: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/recipes/{recipe_id}/versions", response_model=Recipe)
def create_recipe_version(recipe_id: UUID, version_request: RecipeVersionRequest):
  """
  Manually create a new version of a recipe
  """
  try:
    recipe = recipe_service.create_recipe_version(
      recipe_id=recipe_id,
      ingredients=version_request.ingredients,
      instructions=version_request.instructions,
      description=version_request.description,
      force_major=version_request.force_major,
    )
    return recipe

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    logger.error(f"Error creating recipe version: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/recipes/{recipe_id}/versions", response_model=List[RecipeVersion])
def get_recipe_versions(recipe_id: UUID):
  """
  Get all versions of a recipe
  """
  try:
    versions = recipe_service.get_recipe_versions(recipe_id)
    return versions

  except Exception as e:
    logger.error(f"Error getting recipe versions: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/recipes/versions/{version_id_1}/diff/{version_id_2}")
def get_version_diff(version_id_1: UUID, version_id_2: UUID):
  """
  Get diff between two recipe versions
  """
  try:
    diff = recipe_service.get_recipe_version_diff(version_id_1, version_id_2)
    return diff

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    logger.error(f"Error getting version diff: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


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
def create_timing(timing: BreadTimingCreate):
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
    valid_sort_fields = ["created_at", "updated_at", "date", "recipe_name"]
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
def get_timing(timing_id: UUID):
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
def update_timing(timing_id: UUID, updates: BreadTimingUpdate):
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
def delete_timing(timing_id: UUID):
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
  Returns 'completed' if all required fields are populated, 'in_progress' otherwise.
  """
  required_fields = [
    "recipe_name",
    "date",
    "autolyse_ts",
    "mix_ts",
    "bulk_ts",
    "preshape_ts",
    "final_shape_ts",
    "fridge_ts",
    "room_temp",
    "water_temp",
    "flour_temp",
    "preferment_temp",
    "dough_temp",
    "temperature_unit",
  ]

  # Check if all required fields have non-None values
  for field in required_fields:
    if timing_data.get(field) is None:
      return "in_progress"

  return "completed"


def validate_timing_data(timing: BreadTimingCreate) -> None:
  """Validate timing data for creation"""

  # Validate timestamp ordering
  timestamps = [
    ("autolyse_ts", timing.autolyse_ts),
    ("mix_ts", timing.mix_ts),
    ("bulk_ts", timing.bulk_ts),
    ("preshape_ts", timing.preshape_ts),
    ("final_shape_ts", timing.final_shape_ts),
    ("fridge_ts", timing.fridge_ts),
  ]

  # Filter out None timestamps and validate order
  valid_timestamps = [(name, ts) for name, ts in timestamps if ts is not None]

  for i in range(len(valid_timestamps) - 1):
    current_name, current_ts = valid_timestamps[i]
    next_name, next_ts = valid_timestamps[i + 1]

    if current_ts >= next_ts:
      raise ValueError(f"{next_name} must be after {current_name}")

  # Validate stretch folds
  if timing.stretch_folds:
    if len(timing.stretch_folds) > 8:
      raise ValueError("Maximum 8 stretch folds allowed")

    # Check for duplicate fold numbers
    fold_numbers = [sf.fold_number for sf in timing.stretch_folds]
    if len(fold_numbers) != len(set(fold_numbers)):
      raise ValueError("Stretch fold numbers must be unique")

    # Validate fold timestamps are within process time range
    earliest_process_ts = next((ts for _, ts in valid_timestamps if ts), None)
    if earliest_process_ts:
      for fold in timing.stretch_folds:
        if fold.timestamp < earliest_process_ts:
          raise ValueError("Stretch fold timestamp cannot be before process start")

  # Validate process duration (max 48 hours)
  if valid_timestamps and len(valid_timestamps) >= 2:
    start_ts = valid_timestamps[0][1]
    end_ts = valid_timestamps[-1][1]
    duration_hours = (end_ts - start_ts).total_seconds() / 3600

    if duration_hours > 48:
      raise ValueError("Process duration cannot exceed 48 hours")


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
      "fridge_ts": updates.fridge_ts
      if updates.fridge_ts is not None
      else existing.fridge_ts,
    }

    # Validate merged timestamps
    timestamps = [(name, ts) for name, ts in merged_data.items() if ts is not None]
    timestamps.sort(key=lambda x: x[1])  # Sort by timestamp

    for i in range(len(timestamps) - 1):
      current_name, current_ts = timestamps[i]
      next_name, next_ts = timestamps[i + 1]

      if current_ts >= next_ts:
        raise ValueError(f"{next_name} must be after {current_name}")
