from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import date, datetime
from db import DBConnector
from exceptions import DatabaseError
from models import AccountMake, CreateMakeRequest, DoughMake, DoughMakeRequest, DoughMakeUpdate, MAKE_NAMES, RecipeRequest, SimpleMake
from typing import List
from uuid import UUID, uuid4

import json
import logging
import re

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DBNAME = 'bread_makes'
db_conn = DBConnector(dbname=DBNAME)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('service')
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
      user_id=user_id,
      account_id=account_id,
      account_name=account_name
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
def get_makes_for_account(user: UserContext=Depends(get_current_user)):
  try:
    return db_conn.get_account_makes(user.account_id)
  except Exception as e:
    logger.error(f"Error occurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/makes", response_model=SimpleMake)
def create_make_for_account(make: CreateMakeRequest, user: UserContext=Depends(get_current_user)):
    logger.info(f"Received POST request to /makes with data: {make}")
    try:
        # Check if the key already exists for this account
        existing_makes = db_conn.get_account_makes(user.account_id)
        existing_makes = [SimpleMake(**make) for make in existing_makes]
        if any(existing_make.key == make.key for existing_make in existing_makes):
            raise HTTPException(status_code=400, detail="A make with a similar name already exists")

        # Add the make to the database
        new_make = db_conn.add_account_make(
            account_id=user.account_id,
            account_name=user.account_name,
            display_name=make.display_name,
            key=make.key
        )

        return new_make
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error occurred while creating make: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Create make entries within the DB table
@app.post("/makes/{year}/{month}/{day}/{name}")
def create_make(year: int, month: int, day: int, name: str, dough_make_req: DoughMakeRequest) -> None:
  date = validate_date(year, month, day)
  
  # Set created_at server-side if not provided
  if dough_make_req.created_at is None:
    dough_make_req.created_at = datetime.now()
  
  dough_make = DoughMake(
    name=name,
    date=date,
    **dough_make_req.model_dump()
  )
  field_values = {
    field: getattr(dough_make, field)
    for field in dough_make.__fields__.keys()
  }

  logger.info(f"Inserting dough make: {dough_make.name}, {dough_make}")
  logger.info(f"Dough make details: {json.dumps(field_values, default=str, indent=2)}")
  try:
    validate_dough_make(dough_make)
    db_conn.insert_dough_make(dough_make)
    logger.info(f"Successfully inserted dough make")
  except Exception as e:
    logger.error("Error ocurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))

  return


@app.patch("/makes/{year}/{month}/{day}/{name}/{created_at}")
def update_make(name: str, created_at: str, year: int, month: int, day: int, updates: DoughMakeUpdate):
  """
  Updates the dough_make {name} that was made on {date} with {created_at}
  """
  date = validate_date(year, month, day)
  
  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  try:
    # Convert the updates to a dictionary, excluding None values
    update_data = updates.model_dump(exclude_none=True)
    if not update_data:
      raise HTTPException(
        status_code=400,
        detail="No valid fields to update were provided"
      )

    existing_make = get_make(name, created_at, year, month, day).model_dump(exclude_none=True)
    # Add logging to see the data structure
    logger.info(f"Existing make data: {existing_make}")
    logger.info(f"Update data: {update_data}")
    logger.info(f"Combined data: {{**existing_make, **update_data}}")
    updated_make = DoughMake(**{**existing_make, **update_data})
    validate_dough_make(updated_make)
    logger.info(f"Updating make to {updated_make.model_dump()}")
    db_conn.update_dough_make(
      date=date,
      name=name,
      created_at=created_at_dt,
      updates=updated_make.model_dump()
    )
  except ValueError as e:  # Add this before DatabaseError
    raise HTTPException(
        status_code=400,
        detail=f"Validation error: {str(e)}"
    )
  except DatabaseError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Database error: {e.message}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Unexpected error occurred: {str(e)}"
    )

@app.get("/makes/{year}/{month}/{day}")
def get_makes_date(year: int, month: int, day: int) -> List[DoughMake]:
  """
  Retrieves the list of makes for a date
  """
  date = validate_date(year, month, day)
  try:
     dough_makes = db_conn.get_dough_makes(date)
     return dough_makes or []
  except DatabaseError as e:
     logger.error(f"Database error getting makes for date {date}: {e}")
     raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
  except Exception as e:
     logger.error(f"Unexpected error getting makes for date {date}: {e}")
     raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/makes/{year}/{month}/{day}/{name}/{created_at}")
def get_make(name: str, created_at: str, year: int, month: int, day: int) -> DoughMake | None:
  """
  Retrieves the dough_make that have {name} for make on {date} with {created_at}
  """
  date = validate_date(year, month, day)
  
  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  # separate the application logic from DB logic. This service app doesn't know how many makes there are for a specific dough on a given date. But it knows what's an allowed name.

  logger.info(f"Getting dough make: {name} created at {created_at} for date: {str(date)}")
  try:
    dough_make = db_conn.get_dough_make(date, name, created_at_dt)
  except DatabaseError as e:
    raise HTTPException(
      status_code=400,
      detail=f"Database error: {e.message}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Unexpected error ocurred: {str(e)}"
    )
  logger.info(f"Make retrieved")
  return dough_make


@app.delete("/makes/{year}/{month}/{day}/{name}/{created_at}")
def delete_make(name: str, created_at: str, year: int, month: int, day: int):
  date = validate_date(year, month, day)
  
  # Parse the created_at timestamp
  try:
    created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid created_at timestamp format")

  logger.info(f"Deleting dough make: {name} created at {created_at} for date: {str(date)}")
  try:
    db_conn.delete_dough_make(date, name, created_at_dt)
  except DatabaseError as e:
    logger.error(f"Error deleting dough make ({name} created at {created_at}): {str(e)}")
    raise HTTPException(
      status_code=400,
      detail=f"Database error: {e.message}"
    )
  logger.info(f"Make deleted")



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

@app.post("/recipes/")
def create_recipe(recipe: RecipeRequest):
  """
  Create a new recipe
  """
  try:
    # Generate UUID for the recipe
    recipe_id = uuid4()
    
    # Convert RecipeRequest to dict format for database insertion
    recipe_data = {
      "id": recipe_id,
      "name": recipe.name,
      "description": recipe.description,
      "instructions": [step.model_dump() for step in recipe.instructions],
      "ingredients": [ingredient.model_dump() for ingredient in recipe.ingredients]
    }
    
    # Insert into database
    db_conn.create_recipe(recipe_data)
    
    return {"id": recipe_id, "message": "Recipe created successfully"}
    
  except Exception as e:
    logger.error(f"Error creating recipe: {str(e)}")
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

  def validate_timestamps(autolyse_ts, mix_ts, bulk_ts, preshape_ts, final_shape_ts, fridge_ts):
    # Create list of timestamps with their names for validation
    timestamps = [autolyse_ts, mix_ts, bulk_ts, preshape_ts, final_shape_ts, fridge_ts]
    names = ["Autolyse", "Mix", "Bulk", "Preshape", "Final shape", "Fridge"]
    
    # Adjust timestamps to handle day boundary crossings
    adjusted_timestamps = adjust_for_day_boundaries(timestamps)
    
    # Now validate that adjusted timestamps are in order
    for i in range(len(adjusted_timestamps) - 1):
      if adjusted_timestamps[i] > adjusted_timestamps[i + 1]:
        raise ValueError(f"{names[i]} time must occur before {names[i + 1]} time")
    
    return True

  return True if validate_timestamps(make.autolyse_ts, make.mix_ts, make.bulk_ts, make.preshape_ts, make.final_shape_ts, make.fridge_ts) else False