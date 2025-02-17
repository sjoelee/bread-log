from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional

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

# Updates
class DoughMakeUpdate(BaseModel):
    # Make all fields optional by using Optional
    autolyse: Optional[datetime] = None
    start: Optional[datetime] = None
    pull: Optional[datetime] = None
    preshape: Optional[datetime] = None
    final_shape: Optional[datetime] = None
    fridge: Optional[datetime] = None

    room_temp: Optional[float] = None
    preferment_temp: Optional[float] = None
    water_temp: Optional[float] = None
    flour_temp: Optional[float] = None

# New request
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

class DoughMake(DoughMakeRequest):
  name: str
  date: date