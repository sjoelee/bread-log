from fastapi import FastAPI, HTTPException
from datetime import date, datetime
from db import DBConnector
from exceptions import DatabaseError
from models import DoughMake, DoughMakeRequest, DoughMakeUpdate, MAKE_NAMES

import logging

app = FastAPI()
DBNAME = 'bread_makes'
db_conn = DBConnector(dbname=DBNAME)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('service')
logger.setLevel(logging.DEBUG)
logger.info("app brought up")

# Create make entries within the DB table 
@app.post("/makes/{year}/{month}/{day}/{make_name}")
def create_make(year: int, month: int, day: int, make_name: str, dough_make_req: DoughMakeRequest) -> None:
  date = validate_date(year, month, day)
  dough_make = DoughMake(
    name=make_name,
    date=date,
    **dough_make_req.model_dump()
  )

  logger.info(f"Inserting dough make: {dough_make.name}")
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
      if ts1 >= ts2:
          raise ValueError(f"{earlier_name} time must occur before {later_name} time")

  def validate_timestamps(autolyse_ts, start_ts, pull_ts, preshape_ts, final_shape_ts, fridge_ts):
      validate_timestamp_order(autolyse_ts, start_ts, "Autolyse", "Start")
      validate_timestamp_order(start_ts, pull_ts, "Start", "Pull")
      validate_timestamp_order(pull_ts, preshape_ts, "Pull", "Preshape")
      validate_timestamp_order(preshape_ts, final_shape_ts, "Preshape", "Final shape")
      validate_timestamp_order(final_shape_ts, fridge_ts, "Final shape", "Fridge")
      return True
  
  return True if validate_timestamps(make.autolyse_ts, make.start_ts, make.pull_ts, make.preshape_ts, make.final_shape_ts, make.fridge_ts) else False