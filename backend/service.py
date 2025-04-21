from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from datetime import date, datetime
from db import DBConnector
from exceptions import DatabaseError
from models import AccountMake, DoughMake, DoughMakeRequest, DoughMakeUpdate, MAKE_NAMES, SimpleMake
from typing import List
from uuid import UUID

import json
import logging

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

@app.get("/makes", response_model=List[SimpleMake])
def get_makes_for_account(user: UserContext=Depends(get_current_user)):
  try:
    return db_conn.get_account_makes(user.account_id)
  except Exception as e:
    logger.error("Error ocurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# Create make entries within the DB table
@app.post("/makes/{year}/{month}/{day}/{make_name}")
def create_make(year: int, month: int, day: int, make_name: str, dough_make_req: DoughMakeRequest) -> None:
  date = validate_date(year, month, day)
  dough_make = DoughMake(
    name=make_name,
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


@app.patch("/makes/{year}/{month}/{day}/{make_name}/{make_num}")
def update_make(make_name: str, make_num: int, year: int, month: int, day: int, updates: DoughMakeUpdate):
  """
  Updates the dough_make {make_name} that was made on {date}
  """
  date = validate_date(year, month, day)

  try:
    # Convert the updates to a dictionary, excluding None values
    update_data = updates.model_dump(exclude_none=True)
    if not update_data:
      raise HTTPException(
        status_code=400,
        detail="No valid fields to update were provided"
      )

    existing_make = get_make(make_name, make_num, year, month, day).model_dump(exclude_none=True)
    # Add logging to see the data structure
    logger.info(f"Existing make data: {existing_make}")
    logger.info(f"Update data: {update_data}")
    logger.info(f"Combined data: {{**existing_make, **update_data}}")
    updated_make = DoughMake(**{**existing_make, **update_data})
    validate_dough_make(updated_make)
    logger.info(f"Updating make to {updated_make.model_dump()}")
    db_conn.update_dough_make(
      make_date=date,
      make_name=make_name,
      make_num=make_num,
      updates=update_data
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


@app.get("/makes/{year}/{month}/{day}/{make_name}/{make_num}")
def get_make(make_name: str, make_num: int, year: int, month: int, day: int):
  """
  Retrieves the dough_make that have {make_name} for made on {date}
  """
  date = validate_date(year, month, day)

  # separate the application logic from DB logic. This service app doesn't know how many makes there are for a specific dough on a given date. But it knows what's an allowed name.
  if make_name not in MAKE_NAMES:
    raise HTTPException(status_code=400, detail=f"The make name must be one of these {MAKE_NAMES}")

  logger.info(f"Getting dough make: {make_name} #{make_num} for date: {str(date)}")
  try:
    dough_make = db_conn.get_dough_make(date, make_name, make_num)
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


@app.delete("/makes/{year}/{month}/{day}/{make_name}/{make_num}")
def delete_make(make_name: str, make_num: int, year: int, month: int, day: int):
  date = validate_date(year, month, day)

  logger.info(f"Deleting dough make: {make_name} #{make_num} for date: {str(date)}")
  try:
    db_conn.delete_dough_make(date, make_name, make_num)
  except DatabaseError as e:
    logger.error(f"Error deleting dough make ({make_name} #{make_num}): {str(e)}")
    raise HTTPException(
      status_code=400,
      detail=f"Database error: {e.message}"
    )
  logger.info(f"Make deleted")



@app.get("/makes/{make_name}")
def get_makes_for_name(make_name: str):
  """
  Retrieves a list of dough_makes that have {make_name}
  """
  pass

@app.get("/makes/{date}")
def get_makes_for_date(date: str):
  """
  Retrieves a list of makes for that date
  """
  pass

def validate_date(year: int, month: int, day: int) -> date:
  assert 1985 <= year, "Year must be valid"
  assert 1 <= month <= 12, "Month must be valid"
  assert 0 < day < 31, "Day must be valid"

  # Custom checks
  try:
    return datetime(year, month, day).date()
  except:
    return False

def validate_dough_make(make: DoughMake) -> bool:
  def validate_timestamp_order(ts1, ts2, earlier_name, later_name):
      if ts1 > ts2:
          raise ValueError(f"{earlier_name} time must occur before {later_name} time")

  def validate_timestamps(autolyse_ts, start_ts, pull_ts, preshape_ts, final_shape_ts, fridge_ts):
      validate_timestamp_order(autolyse_ts, start_ts, "Autolyse", "Start")
      validate_timestamp_order(start_ts, pull_ts, "Start", "Pull")
      validate_timestamp_order(pull_ts, preshape_ts, "Pull", "Preshape")
      validate_timestamp_order(preshape_ts, final_shape_ts, "Preshape", "Final shape")
      validate_timestamp_order(final_shape_ts, fridge_ts, "Final shape", "Fridge")
      return True

  return True if validate_timestamps(make.autolyse_ts, make.start_ts, make.pull_ts, make.preshape_ts, make.final_shape_ts, make.fridge_ts) else False