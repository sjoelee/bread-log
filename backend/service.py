from fastapi import FastAPI
from datetime import date, datetime
from db import DBConnector
from models import DoughMake

app = FastAPI()
DBNAME = 'bread_makes'
db_conn = DBConnector(dbname=DBNAME)


# Create make entries within the DB table 
@app.post("makes/{date}/{make_name}")
def create_make(date: str, make_name: str, dough_make: DoughMake):
  def validate_dough_make(dough_make: DoughMake):
    if dough_make.start < dough_make.autolyse:
        raise ValueError("Start time must be after autolyse time")
  validate_dough_make(dough_make)
  db_conn.insert_dough_make(dough_make)

@app.get("/makes/{date}/{make_name}")
def get_make(make_name: str, date: str):
  pass

@app.get("/makes/{make_name}")
def get_makes_for_name(make_name: str):
  pass

@app.get("/makes/{date}")
def get_makes_for_date(date: str):
  pass