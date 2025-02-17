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
  def validate_dough_make(dough_make: DoughMake):
    if dough_make.start < dough_make.autolyse:
        raise ValueError("Start time must be after autolyse time")
  logger.info(f"Inserting dough make: {dough_make.name}")
  try: 
    validate_dough_make(dough_make)
    db_conn.insert_dough_make(dough_make)
    logger.info(f"Successfully inserted dough make")
  except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
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

  existing_make = get_make(make_name, make_num, year, month, day)
  if not existing_make:
    raise HTTPException(status_code=404, detail=f"Dough Make for {make_name} #{make_num} on {str(date)} not found")
 
      # Convert the updates to a dictionary, excluding None values
  update_data = updates.model_dump(exclude_none=True)
 
  if not update_data:
    raise HTTPException(
      status_code=400,
      detail="No valid fields to update were provided"
    )
  try:
    db_conn.update_dough_make(
      make_name=make_name,
      make_date=date,
      make_num=make_num,
      updates=update_data
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

  logger.info(f"Getting dough make: {make_name} #{make_num} for date: {str(date)}")

  # check that make_name is valid
  if make_name not in MAKE_NAMES:
    raise HTTPException(status_code=400, detail=f"The make name must be one of these {MAKE_NAMES}")

  dough_make = db_conn.get_dough_make(date, make_name, make_num)
  logger.info(f"Make retrieved")
  if not dough_make:
    raise HTTPException(status_code=404, detail=f"Make doesn't exist")
  return dough_make

@app.delete("/makes/{date}/{make_name}")
def delete_make(make_name: str, date: str):
  pass


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
