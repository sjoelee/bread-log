from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
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

# Recipe models - Updated for versioning system
class Ingredient(BaseModel):
  id: Optional[str] = None
  name: str = Field(..., min_length=1, description="Ingredient name cannot be empty")
  amount: float = Field(..., gt=0, description="Amount must be greater than 0")
  unit: str = Field(..., pattern=r'^(grams|kg|ml|cups|tbsp|tsp)$', description="Must be valid unit")
  type: str = Field(..., pattern=r'^(flour|liquid|preferment|fat|other)$', description="Must be valid ingredient type")
  notes: Optional[str] = None

  @field_validator('name')
  @classmethod
  def name_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError('Ingredient name cannot be empty')
    return v.strip()

class RecipeStep(BaseModel):
  id: Optional[str] = None
  order: int = Field(..., gt=0, description="Order must be greater than 0")
  instruction: str = Field(..., min_length=1, description="Instruction cannot be empty")

  @field_validator('instruction')
  @classmethod
  def instruction_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError('Instruction cannot be empty')
    return v.strip()

class RecipeRequest(BaseModel):
  name: str = Field(..., min_length=1, max_length=255, description="Recipe name is required")
  description: Optional[str] = Field(None, max_length=1000)
  category: Optional[str] = Field(None, pattern=r'^(sourdough|enriched|lean|sweet|other)$')
  ingredients: List[Ingredient] = Field(..., min_length=1, description="At least one ingredient is required")
  instructions: List[RecipeStep] = Field(..., min_length=1, description="At least one instruction is required")

  @field_validator('name')
  @classmethod
  def name_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError('Recipe name cannot be empty')
    return v.strip()

class RecipeVersionRequest(BaseModel):
  ingredients: List[Ingredient]
  instructions: List[RecipeStep]
  description: Optional[str] = None
  force_major: bool = False

class RecipeUpdateRequest(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  category: Optional[str] = None
  ingredients: Optional[List[Ingredient]] = None
  instructions: Optional[List[RecipeStep]] = None
  force_major: Optional[bool] = False

# Response models
class RecipeVersion(BaseModel):
  id: UUID
  recipe_id: UUID
  version_number: int
  description: Optional[str] = None
  ingredients: List[Ingredient]
  instructions: List[RecipeStep]
  created_at: datetime
  change_summary: Optional[dict] = None

class BakersPercentages(BaseModel):
  total_flour_weight: float
  flour_ingredients: List[dict]
  other_ingredients: List[dict]

class Recipe(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  category: Optional[str] = None
  current_version_id: UUID
  current_version: RecipeVersion
  bakers_percentages: Optional[BakersPercentages] = None
  created_at: datetime
  updated_at: datetime

class RecipeListItem(BaseModel):
  id: UUID
  name: str
  category: Optional[str] = None
  version: str  # e.g., "2", "3"
  ingredient_count: int
  step_count: int
  created_at: datetime
  updated_at: datetime

class IngredientDiff(BaseModel):
  added: List[Ingredient]
  removed: List[Ingredient]
  modified: List[dict]  # {"old": Ingredient, "new": Ingredient}
  unchanged: List[Ingredient]

class StepDiff(BaseModel):
  added: List[RecipeStep]
  removed: List[RecipeStep]
  modified: List[dict]  # {"old": RecipeStep, "new": RecipeStep}
  reordered: List[dict]  # {"step_id": str, "old_order": int, "new_order": int}
  unchanged: List[RecipeStep]

class RecipeVersionDiff(BaseModel):
  from_version: str
  to_version: str
  ingredient_changes: IngredientDiff
  step_changes: StepDiff
  created_at: datetime

class RecipeCreateResponse(BaseModel):
  recipe: Recipe
  message: str
  success: bool = True