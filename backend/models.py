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

# Request sent
class DoughMakeRequest(BaseModel):
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

class DoughMake(DoughMakeRequest):
  name: str
  date: date
  num: int # accounts for multiple makes of the same dough on the same day