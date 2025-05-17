from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class MakeNames(Enum):
  # Sticks
  DEMI_BAGUETTE = "demi"
  HOAGIE = "hoagie"

  # Sourdough
  UBE = "ube"
  TEAM = "team"

MAKE_NAMES = set(e.value for e in MakeNames.__members__.values())

# Updates
class DoughMakeUpdate(BaseModel):
  # Make all fields optional by using Optional
  autolyse_ts: Optional[datetime] = None
  start_ts: Optional[datetime] = None
  pull_ts: Optional[datetime] = None
  preshape_ts: Optional[datetime] = None
  final_shape_ts: Optional[datetime] = None
  fridge_ts: Optional[datetime] = None

  room_temp: Optional[float] = None
  preferment_temp: Optional[float] = None
  water_temp: Optional[float] = None
  flour_temp: Optional[float] = None
  dough_temp: Optional[float] = None
  temp_unit: Optional[str] = None

# New request
class DoughMakeRequest(BaseModel):
  # Times needed to store
  autolyse_ts: datetime
  start_ts: datetime
  pull_ts: datetime
  preshape_ts: datetime
  final_shape_ts: datetime
  fridge_ts: datetime

  # Temps for each of the components
  room_temp: int
  preferment_temp: int | None = None
  water_temp: int | None = None
  flour_temp: int | None = None
  dough_temp: int | None = None

  temp_unit: str | None = None

class DoughMake(DoughMakeRequest):
  name: str
  date: date

# Request model for creating a new account make
class AccountMakeRequest(BaseModel):
    make_name: str
    make_key: str

# Response model for account make
class AccountMake(BaseModel):
    account_id: UUID
    account_name: str
    make_name: str
    make_key: str
    created_at: datetime

# Simplified response model for account make
class SimpleMake(BaseModel):
   display_name: str
   key: str

# New model for creating a make
class CreateMakeRequest(BaseModel):
    display_name: str
    key: str