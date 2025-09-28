from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
import json

class MakeNames(Enum):
  # Sticks
  DEMI_BAGUETTE = "demi-baguette"
  HOAGIE = "hoagie"

  # Sourdough
  UBE = "ube"
  TEAM = "team"

class TempUnit(Enum):
  FAHRENHEIT = "Fahrenheit"
  CELSIUS = "Celsius"

MAKE_NAMES = set(e.value for e in MakeNames.__members__.values())

class StretchFoldCreate(BaseModel):
  fold_number: int
  timestamp: datetime

# Updates
class DoughMakeUpdate(BaseModel):
  # Make all fields optional by using Optional
  autolyse_ts: Optional[datetime] = None
  mix_ts: Optional[datetime] = None
  bulk_ts: Optional[datetime] = None
  preshape_ts: Optional[datetime] = None
  final_shape_ts: Optional[datetime] = None
  fridge_ts: Optional[datetime] = None

  room_temp: Optional[float] = None
  preferment_temp: Optional[float] = None
  water_temp: Optional[float] = None
  flour_temp: Optional[float] = None
  dough_temp: Optional[float] = None
  temperature_unit: Optional[str] = None
  
  # Add new fields
  stretch_folds: Optional[List[StretchFoldCreate]] = None
  notes: Optional[str] = None

# New request
class DoughMakeRequest(BaseModel):
  # Times needed to store
  autolyse_ts: datetime
  mix_ts: datetime
  bulk_ts: datetime
  preshape_ts: datetime
  final_shape_ts: datetime
  fridge_ts: datetime

  temperature_unit: str = TempUnit.FAHRENHEIT.value

  # Temps for each of the components
  room_temp: int
  preferment_temp: int
  water_temp: int
  flour_temp: int
  dough_temp: int
  
  created_at: Optional[datetime] = None
  
  stretch_folds: List[StretchFoldCreate] = []
  notes: Optional[str] = None

class DoughMake(DoughMakeRequest):
  name: str
  date: date

# Request model for creating a new account make
class AccountMakeRequest(BaseModel):
  name: str
  key: str

# Response model for account make
class AccountMake(BaseModel):
  account_id: UUID
  account_name: str
  name: str
  key: str
  created_at: datetime

# Simplified response model for account make
class SimpleMake(BaseModel):
  display_name: str
  key: str

# New model for creating a make
class CreateMakeRequest(BaseModel):
  display_name: str
  key: str

# Recipe models
class Ingredient(BaseModel):
  name: str
  amount: float
  unit: str
  notes: Optional[str] = None

class RecipeStep(BaseModel):
  instruction: str

class RecipeRequest(BaseModel):
  name: str
  description: Optional[str] = None
  instructions: List[RecipeStep]
  ingredients: List[Ingredient]