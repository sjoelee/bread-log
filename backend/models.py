from datetime import date, datetime
from pydantic import BaseModel

class DoughMake(BaseModel):
  # company = str # replace with user_id
  name: str # name of the make
  date: date # date of when the dough is made

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
