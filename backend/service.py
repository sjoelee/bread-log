from fastapi import FastAPI
from datetime import date, datetime
from db import DBConnector
from models import DoughMake

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
def create_make(date: str, make_name: str, dough_make: DoughMake):
  def validate_dough_make(dough_make: DoughMake):
    if dough_make.start < dough_make.autolyse:
        raise ValueError("Start time must be after autolyse time")
  logger.info(f"Inserting dough make: {dough_make.name}")
  validate_dough_make(dough_make)
  make_id = db_conn.insert_dough_make(dough_make)
  logger.info(f"Successfully inserted dough make {make_id}")
  return make_id

@app.patch("/makes/{date}/{make_name}")
def update_make(make_name: str, date: str):
  """
  Updates the dough_make {make_name} that was made on {date}
  """
  pass

@app.get("/makes/{date}/{make_name}")
def get_make(make_name: str, date: str):
  """
  Retrieves the dough_make that have {make_name} for made on {date}
  """
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