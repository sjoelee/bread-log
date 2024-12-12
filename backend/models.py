from datetime import date, datetime
from pydantic import BaseModel
from enum import Enum

class MakeNames(Enum):
  # Sticks
  DEMI_BAGUETTE = "demi_baguette"
  HOAGIE_A = "hoagie_a"
  HOAGIE_B = "hoagie_b"

  # Sourdough
  UBE = "ube"
  TEAM_A = "team_a"
  TEAM_B = "team_b"
  TEAM_C = "team_c"

MAKE_NAMES = set(e.value for e in MakeNames.__members__.values())


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

  notes: str | None = None
