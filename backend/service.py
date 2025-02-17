from fastapi import FastAPI, HTTPException
from datetime import date, datetime
from db import DBConnector
from models import DoughMake, DoughMakeRequest, MAKE_NAMES

import logging

app = FastAPI()
DBNAME = 'bread_makes'
db_conn = DBConnector(dbname=DBNAME)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('service')
logger.setLevel(logging.DEBUG)
logger.info("app brought up")

# Create make entries within the DB table 
# TODO: update endpoint to just /makes because the date and make_name are within the request body
@app.post("/makes/{year}/{month}/{day}/{make_name}")
def create_make(year: int, month: int, day: int, make_name: str, dough_make_req: DoughMakeRequest) -> int:
  date = validate_date(year, month, day)
  dough_make = DoughMake(
    name=make_name,
    date=date,
    num=0, #TODO: autoincrement
    **dough_make_req.model_dump()
  )
  def validate_dough_make(dough_make: DoughMake):
    if dough_make.start < dough_make.autolyse:
        raise ValueError("Start time must be after autolyse time")
  logger.info(f"Inserting dough make: {dough_make.name}")
  try: 
    validate_dough_make(dough_make)
    make_id = db_conn.insert_dough_make(dough_make)
    logger.info(f"Successfully inserted dough make {make_id}")
  except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error("Error ocurred: {e}")
    raise HTTPException(status_code=500, detail=str(e))

  return make_id

@app.patch("/makes/{year}/{month}/{day}/{make_name}")
def update_make(make_name: str, year: int, month: int, day: int, dough_make: DoughMakeRequest) -> int:
  """
  Updates the dough_make {make_name} that was made on {date}
  """
  date = validate_date(year, month, day)

  old_dough_make = get_make(make_name, year, month, day)
  if not old_dough_make:
    raise HTTPException(status_code=404, detail=f"Make {dough_make} for {str(date)} not found")
  # get diff
  # perform inserts on teh diff fields
  make_id = db_conn.insert_dough_make(dough_make)
  # we should return the same make_id as before since we're not creating a new entry
  return make_id

@app.get("/makes/{year}/{month}/{day}/{make_name}")
def get_make(make_name: str, year: int, month: int, day: int):
  """
  Retrieves the dough_make that have {make_name} for made on {date}
  """
  date = validate_date(year, month, day)

  logger.info(f"Getting make: {make_name} for date: {str(date)}")

  # check that make_name is valid
  if make_name not in MAKE_NAMES:
    raise HTTPException(status_code=400, detail=f"The make name must be one of these {MAKE_NAMES}")

  dough_make = db_conn.get_dough_make(date, make_name)
  logger.info(f"Make retrieved: {dough_make}")
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
