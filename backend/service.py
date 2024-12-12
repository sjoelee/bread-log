from fastapi import FastAPI, HTTPException
from datetime import date, datetime
from db import DBConnector
from models import DoughMake, MAKE_NAMES

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
@app.post("/makes/{date}/{make_name}")
def create_make(date: str, make_name: str, dough_make: DoughMake) -> int:
  dough_make.name = make_name
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

@app.patch("/makes/{date}/{make_name}")
def update_make(make_name: str, date: str, dough_make: DoughMake) -> int:
  """
  Updates the dough_make {make_name} that was made on {date}
  """
  # look 
  pass

@app.get("/makes/{date}/{make_name}")
def get_make(make_name: str, date: str):
  """
  Retrieves the dough_make that have {make_name} for made on {date}
  """
  logger.info(f"Getting make: {make_name} for date: {date}")
  # check that date is valid
  try:
    validate_date(date)
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"Wrong date format")

  # check that make_name is valid
  if make_name not in MAKE_NAMES:
    raise HTTPException(status_code=400, detail=f"The make name must be one of these {MAKE_NAMES}")

  dough_make = db_conn.get_dough_make(date, make_name)
  logger.info(f"Make retrieved: {dough_make}")
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

def validate_date(date: str, date_format: str="%Y-%m-%d"):
  try: 
    datetime.strptime(date, date_format)
    return True
  except:
    return False
