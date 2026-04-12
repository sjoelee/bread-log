from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import date, datetime
from .db import DBConnector
from .exceptions import DatabaseError
from .models import (
  CreateMakeRequest,
  DoughMake,
  DoughMakeRequest,
  DoughMakeUpdate,
  Recipe,
  RecipeRequest,
  RecipeVersionRequest,
  RecipeListItem,
  RecipeVersion,
  SimpleMake,
  RecipeCreateResponse,
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse,
)
from typing import List, Optional
from uuid import UUID

import json
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


# Getting and retrieving dough makes for the acccount
@app.get("/makes", response_model=List[SimpleMake])
def get_makes_for_account(user: UserContext = Depends(get_current_user)):
  logger.info(f"GET /makes - Getting account makes for user: {user.account_id}")
  try:
    result = db_conn.get_account_makes(user.account_id)
    logger.info(f"GET /makes - Successfully retrieved {len(result)} account makes")
    return result
  except Exception as e:
    logger.error(f"GET /makes - Error occurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/makes", response_model=SimpleMake)
def create_make_for_account(
  make: CreateMakeRequest, user: UserContext = Depends(get_current_user)
):
  logger.info(f"POST /makes - Creating account make: {make.dict()}")
  try:
    # Check if the key already exists for this account
    existing_makes = db_conn.get_account_makes(user.account_id)
    existing_makes = [SimpleMake(**make) for make in existing_makes]
    if any(existing_make.key == make.key for existing_make in existing_makes):
      logger.warning(f"POST /makes - Make with key '{make.key}' already exists")
      raise HTTPException(
        status_code=400, detail="A make with a similar name already exists"
      )

    # Add the make to the database
    new_make = db_conn.add_account_make(
      account_id=user.account_id,
      account_name=user.account_name,
      display_name=make.display_name,
      key=make.key,
    )

    logger.info(f"POST /makes - Successfully created make: {new_make.dict()}")
    return new_make
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"POST /makes - Error occurred while creating make: {e}")
    raise HTTPException(status_code=500, detail=str(e))


# Create make entries within the DB table
@app.post("/makes/{year}/{month}/{day}/{name}")
def create_make(
  year: int, month: int, day: int, name: str, dough_make_req: DoughMakeRequest
) -> None:
  logger.info(
    f"POST /makes/{year}/{month}/{day}/{name} - Creating dough make with data: {dough_make_req.dict()}"
  )
  date = validate_date(year, month, day)

  # Set created_at server-side if not provided
  if dough_make_req.created_at is None:
    dough_make_req.created_at = datetime.now()

  dough_make = DoughMake(name=name, date=date, **dough_make_req.model_dump())
  field_values = {
    field: getattr(dough_make, field) for field in dough_make.__fields__.keys()
  }

  logger.info(
    f"POST /makes/{year}/{month}/{day}/{name} - Inserting dough make: {dough_make.name}"
  )
  logger.debug(
    f"POST /makes/{year}/{month}/{day}/{name} - Dough make details: {json.dumps(field_values, default=str, indent=2)}"
  )
  try:
    validate_dough_make(dough_make)
    db_conn.insert_dough_make(dough_make)
    logger.info(
      f"POST /makes/{year}/{month}/{day}/{name} - Successfully inserted dough make"
    )
  except Exception as e:
    logger.error(f"POST /makes/{year}/{month}/{day}/{name} - Error occurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))

  return


@app.patch("/makes/{year}/{month}/{day}/{name}/{created_at}")
def update_make(
  name: str,
  created_at: str,
  year: int,
  month: int,
  day: int,
  updates: DoughMakeUpdate,
):
  """
  Updates the dough_make {name} that was made on {date} with {created_at}
  """
  logger.info(
    f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Updating dough make with data: {updates.dict()}"
  )
  date = validate_date(year, month, day)

  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    logger.info(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Parsed created_at: {created_at_dt}"
    )
  except ValueError:
    logger.error(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Invalid created_at timestamp format: {created_at}"
    )
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  try:
    # Convert the updates to a dictionary, excluding None values
    update_data = updates.model_dump(exclude_none=True)
    if not update_data:
      logger.warning(
        f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - No valid fields to update provided"
      )
      raise HTTPException(
        status_code=400, detail="No valid fields to update were provided"
      )

    existing_make = get_make(name, created_at, year, month, day).model_dump(
      exclude_none=True
    )
    logger.info(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Existing make data: {existing_make}"
    )
    logger.info(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Update data: {update_data}"
    )

    updated_make = DoughMake(**{**existing_make, **update_data})
    validate_dough_make(updated_make)

    logger.info(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Validated updated make"
    )
    db_conn.update_dough_make(
      date=date,
      name=name,
      created_at=created_at_dt,
      updates=updated_make.model_dump(),
    )
    logger.info(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Successfully updated dough make"
    )
  except ValueError as e:
    logger.error(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Validation error: {str(e)}"
    )
    raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
  except DatabaseError as e:
    logger.error(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Database error: {e.message}"
    )
    raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
  except Exception as e:
    logger.error(
      f"PATCH /makes/{year}/{month}/{day}/{name}/{created_at} - Unexpected error: {str(e)}"
    )
    raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")


@app.get("/makes/{year}/{month}/{day}")
def get_makes_date(year: int, month: int, day: int) -> List[DoughMake]:
  """
  Retrieves the list of makes for a date
  """
  logger.info(f"GET /makes/{year}/{month}/{day} - Getting makes for date")
  date = validate_date(year, month, day)
  try:
    dough_makes = db_conn.get_dough_makes(date)
    result = dough_makes or []
    logger.info(
      f"GET /makes/{year}/{month}/{day} - Successfully retrieved {len(result)} makes for date {date}"
    )
    return result
  except DatabaseError as e:
    logger.error(
      f"GET /makes/{year}/{month}/{day} - Database error getting makes for date {date}: {e}"
    )
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
  except Exception as e:
    logger.error(
      f"GET /makes/{year}/{month}/{day} - Unexpected error getting makes for date {date}: {e}"
    )
    raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/makes/{year}/{month}/{day}/{name}/{created_at}")
def get_make(
  name: str, created_at: str, year: int, month: int, day: int
) -> Optional[DoughMake]:
  """
  Retrieves the dough_make that have {name} for make on {date} with {created_at}
  """
  logger.info(
    f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Getting specific dough make"
  )
  date = validate_date(year, month, day)

  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    logger.info(
      f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Parsed created_at: {created_at_dt}"
    )
  except ValueError:
    logger.error(
      f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Invalid created_at timestamp format: {created_at}"
    )
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  logger.info(
    f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Getting dough make: {name} created at {created_at} for date: {str(date)}"
  )
  try:
    dough_make = db_conn.get_dough_make(date, name, created_at_dt)
    if dough_make:
      logger.info(
        f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Successfully retrieved dough make"
      )
    else:
      logger.info(
        f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - No dough make found"
      )
    return dough_make
  except DatabaseError as e:
    logger.error(
      f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Database error: {e.message}"
    )
    raise HTTPException(status_code=400, detail=f"Database error: {e.message}")
  except Exception as e:
    logger.error(
      f"GET /makes/{year}/{month}/{day}/{name}/{created_at} - Unexpected error: {str(e)}"
    )
    raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")


@app.delete("/makes/{year}/{month}/{day}/{name}/{created_at}")
def delete_make(name: str, created_at: str, year: int, month: int, day: int):
  date = validate_date(year, month, day)

  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  logger.info(
    f"Deleting dough make: {name} created at {created_at} for date: {str(date)}"
  )
  try:
    db_conn.delete_dough_make(date, name, created_at_dt)
  except DatabaseError as e:
    logger.error(
      f"Error deleting dough make ({name} created at {created_at}): {str(e)}"
    )
    raise HTTPException(status_code=400, detail=f"Database error: {e.message}")
  logger.info("Make deleted")


@app.get("/makes/recent")
def get_recent_makes(limit: int = 10, offset: int = 0):
  """
  Get recent dough makes for the account, sorted by creation date
  TODO: Add authentication when implementing proper auth
  """
  logger.info(
    f"GET /makes/recent - Getting recent makes with limit={limit}, offset={offset}"
  )
  try:
    # Use hardcoded account ID for now (same as in get_current_user mock)
    mock_account_id = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    logger.info(f"GET /makes/recent - Using mock account ID: {mock_account_id}")

    recent_makes = db_conn.get_recent_dough_makes(
      mock_account_id, limit=limit, offset=offset
    )
    logger.info(
      f"GET /makes/recent - Successfully retrieved {len(recent_makes)} recent makes"
    )
    return recent_makes
  except DatabaseError as e:
    logger.error(f"GET /makes/recent - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
  except Exception as e:
    logger.error(f"GET /makes/recent - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/makes/distinct-names")
def get_distinct_bread_names():
  """
  Get distinct bread names from dough_makes ordered by most recent created_at
  """
  logger.info("GET /makes/distinct-names - Getting distinct bread names")
  try:
    # Use hardcoded account ID for now (same as in get_current_user mock)
    mock_account_id = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    logger.info(f"GET /makes/distinct-names - Using mock account ID: {mock_account_id}")

    distinct_names = db_conn.get_distinct_bread_names(mock_account_id)
    logger.info(
      f"GET /makes/distinct-names - Successfully retrieved {len(distinct_names)} distinct names"
    )
    return {"names": distinct_names}
  except DatabaseError as e:
    logger.error(f"GET /makes/distinct-names - Database error: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
  except Exception as e:
    logger.error(f"GET /makes/distinct-names - Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/makes/{name}")
def get_makes_for_name(name: str):
  """
  Retrieves a list of dough_makes that have {name}
  """
  pass


@app.get("/makes/{date}")
def get_makes_for_date(date: str):
  """
  Retrieves a list of makes for that date
  """
  pass


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
def list_recipes(category: str = None, limit: int = 50, offset: int = 0):
  """
  List recipes with pagination and optional category filter
  """
  logger.info(
    f"GET /recipes/ - Listing recipes with category={category}, limit={limit}, offset={offset}"
  )
  try:
    recipes = recipe_service.list_recipes(category=category, limit=limit, offset=offset)
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


def validate_dough_make(make: DoughMake) -> bool:
  def adjust_for_day_boundaries(timestamps):
    """
    Detect day boundary crossings and adjust timestamps accordingly.
    If we see a significant backwards jump in time, assume it's the next day.
    """
    adjusted = []
    days_added = 0

    for i, ts in enumerate(timestamps):
      if i == 0:
        adjusted.append(ts)
        continue

      prev_ts = adjusted[-1]
      current_ts = ts

      # If current timestamp is significantly earlier than previous (more than 12 hours backwards),
      # assume it's the next day
      if current_ts < prev_ts:
        hours_backwards = (prev_ts - current_ts).total_seconds() / 3600
        if hours_backwards > 12:  # Crossed midnight boundary
          days_added += 1

      # Add accumulated days to current timestamp
      if days_added > 0:
        from datetime import timedelta

        current_ts = current_ts + timedelta(days=days_added)

      adjusted.append(current_ts)

    return adjusted

  def validate_timestamps(
    autolyse_ts, mix_ts, bulk_ts, preshape_ts, final_shape_ts, fridge_ts
  ):
    # Create list of timestamps with their names for validation
    timestamps = [
      autolyse_ts,
      mix_ts,
      bulk_ts,
      preshape_ts,
      final_shape_ts,
      fridge_ts,
    ]
    names = ["Autolyse", "Mix", "Bulk", "Preshape", "Final shape", "Fridge"]

    # Adjust timestamps to handle day boundary crossings
    adjusted_timestamps = adjust_for_day_boundaries(timestamps)

    # Now validate that adjusted timestamps are in order
    for i in range(len(adjusted_timestamps) - 1):
      if adjusted_timestamps[i] > adjusted_timestamps[i + 1]:
        raise ValueError(f"{names[i]} time must occur before {names[i + 1]} time")

    return True

  return (
    True
    if validate_timestamps(
      make.autolyse_ts,
      make.mix_ts,
      make.bulk_ts,
      make.preshape_ts,
      make.final_shape_ts,
      make.fridge_ts,
    )
    else False
  )


# New Bread Timing REST API Endpoints


@app.post("/timings", response_model=BreadTiming, status_code=201)
def create_timing(timing: BreadTimingCreate):
  """Create a new bread timing record"""
  logger.info(f"POST /timings - Creating timing: {timing.model_dump()}")
  try:
    # Validate timing data
    validate_timing_data(timing)

    created_timing = db_conn.create_bread_timing(timing)
    logger.info(
      f"POST /timings - Successfully created timing with ID: {created_timing.id}"
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
  date: Optional[str] = None,
  date_from: Optional[str] = None,
  date_to: Optional[str] = None,
  search: Optional[str] = None,
  order_by: str = "created_at",
  order_direction: str = "desc",
):
  """List bread timings with pagination and filtering"""
  logger.info(
    f"GET /timings - Listing timings with filters: page={page}, limit={limit}, recipe_name={recipe_name}"
  )

  try:
    # Validate pagination parameters
    if page < 1:
      raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if limit < 1 or limit > 100:
      raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

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
      date_from=date_from_obj,
      date_to=date_to_obj,
      search=search,
      order_by=order_by,
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

    updated_timing = db_conn.update_bread_timing(timing_id, updates)
    logger.info(f"PATCH /timings/{timing_id} - Successfully updated timing")
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


# Validation functions for timing data


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
