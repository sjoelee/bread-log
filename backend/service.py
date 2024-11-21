from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date, datetime

app = FastAPI()

class DoughMake(BaseModel):
  company = "Rize Up Bakery"
  name: str # name of the make
  date: datetime # date of when the dough is made

  # Times needed to store 
  autolyse: datetime
  start: datetime
  pull: datetime
  preshape: datetime
  final_shape: datetime
  fridge: datetime
  
  # Temps for each of the components
  room_temp: int
  preferment_temp: int | None = None
  water_temp: int | None = None
  flour_temp: int | None = None

  notes: str=None


# Create make entries within the DB table 
@app.post("makes/{date}/{make_name}")
def create_make(date: str, make_name: str, make: DoughMake):
  pass

@app.get("/makes/{date}/{make_name}")
def get_make(make_name: str, date: str):
  pass

@app.get("/makes/{make_name}")
def get_makes_for_name(make_name: str):
  pass

@app.get("/makes/{date}")
def get_makes_for_date(date: str):
  pass