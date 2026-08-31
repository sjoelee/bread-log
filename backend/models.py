from datetime import date as python_date, datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID

# Recipe DTOs moved to backend/api/schemas.py in Stage 3. Re-exported here so
# existing `from backend.models import Recipe` call sites keep working until they
# are updated (Stages 4/6). Dropped as dead: RecipeUpdateRequest, IngredientDiff,
# StepDiff, RecipeVersionDiff.
from .api.schemas import (  # noqa: F401
  BakersPercentages,
  Ingredient,
  Recipe,
  RecipeCreateResponse,
  RecipeListItem,
  RecipeRequest,
  RecipeStep,
  RecipeVersion,
  RecipeVersionRequest,
)


class TempUnit(Enum):
  FAHRENHEIT = "Fahrenheit"
  CELSIUS = "Celsius"


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
  date: python_date


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


# New Bread Timing Models for REST API


class BreadTimingCreate(BaseModel):
  """Request model for creating a new bread timing"""

  recipe_name: Optional[str] = Field(
    None, min_length=1, max_length=255, description="Recipe name"
  )
  recipe_id: Optional[UUID] = Field(None, description="Linked recipe ID")
  recipe_version_id: Optional[UUID] = Field(
    None, description="Linked recipe version ID"
  )
  date: Optional[python_date] = Field(None, description="Date when bread was made")
  status: Optional[str] = Field(None, pattern="^(in_progress|completed)$")

  # Process timestamps (all optional)
  autolyse_ts: Optional[datetime] = None
  mix_ts: Optional[datetime] = None
  bulk_ts: Optional[datetime] = None
  preshape_ts: Optional[datetime] = None
  final_shape_ts: Optional[datetime] = None
  final_proof_ts: Optional[datetime] = None
  bake_ts: Optional[datetime] = None

  # Temperature data (ranges accommodate both Celsius and Fahrenheit)
  room_temp: Optional[float] = Field(
    None, ge=-20, le=120, description="Room temperature (supports both C and F)"
  )
  water_temp: Optional[float] = Field(
    None, ge=0, le=212, description="Water temperature (supports both C and F)"
  )
  flour_temp: Optional[float] = Field(
    None, ge=0, le=120, description="Flour temperature (supports both C and F)"
  )
  preferment_temp: Optional[float] = Field(
    None, ge=0, le=120, description="Preferment temperature (supports both C and F)"
  )
  dough_temp: Optional[float] = Field(
    None, ge=0, le=120, description="Dough temperature (supports both C and F)"
  )
  temperature_unit: str = Field(default="Fahrenheit", pattern="^(Fahrenheit|Celsius)$")

  # Stretch & fold count
  stretch_fold_count: int = Field(default=0, ge=0, le=50)

  # Notes
  notes: Optional[str] = Field(
    None, max_length=2000, description="Notes cannot exceed 2000 characters"
  )

  # Timezone of the baker (IANA timezone string, e.g. "America/Los_Angeles")
  timezone: str = Field(default="UTC", max_length=50)

  @field_validator("recipe_name")
  @classmethod
  def recipe_name_not_empty(cls, v):
    if v is not None and (not v or not v.strip()):
      raise ValueError("Recipe name cannot be empty")
    return v.strip() if v else v

  @field_validator("date")
  @classmethod
  def date_not_future(cls, v):
    if v is not None:
      from datetime import date as date_type

      if v > date_type.today():
        raise ValueError("Cannot create timing for future dates")
    return v


class BreadTimingUpdate(BaseModel):
  """Request model for updating a bread timing"""

  recipe_name: Optional[str] = Field(None, min_length=1, max_length=255)
  recipe_id: Optional[UUID] = None
  recipe_version_id: Optional[UUID] = None

  # Status can be manually updated
  status: Optional[str] = Field(None, pattern="^(in_progress|completed)$")

  # Process timestamps (all optional)
  autolyse_ts: Optional[datetime] = None
  mix_ts: Optional[datetime] = None
  bulk_ts: Optional[datetime] = None
  preshape_ts: Optional[datetime] = None
  final_shape_ts: Optional[datetime] = None
  final_proof_ts: Optional[datetime] = None
  bake_ts: Optional[datetime] = None

  # Temperature data
  room_temp: Optional[float] = Field(None, ge=-20, le=120)
  water_temp: Optional[float] = Field(None, ge=32, le=212)
  flour_temp: Optional[float] = Field(None, ge=32, le=120)
  preferment_temp: Optional[float] = Field(None, ge=32, le=120)
  dough_temp: Optional[float] = Field(None, ge=32, le=120)
  temperature_unit: Optional[str] = Field(None, pattern="^(Fahrenheit|Celsius)$")

  # Stretch & fold count
  stretch_fold_count: Optional[int] = Field(None, ge=0, le=50)

  # Notes
  notes: Optional[str] = Field(None, max_length=2000)

  @field_validator("recipe_name")
  @classmethod
  def recipe_name_not_empty(cls, v):
    if v is not None and (not v or not v.strip()):
      raise ValueError("Recipe name cannot be empty")
    return v.strip() if v else v


class BreadTiming(BaseModel):
  """Response model for bread timing"""

  id: UUID = Field(..., description="Unique timing identifier")
  recipe_name: Optional[str] = None
  recipe_id: Optional[UUID] = None
  recipe_version_id: Optional[UUID] = None
  date: Optional[python_date] = None
  status: str = Field(default="in_progress", pattern="^(in_progress|completed)$")
  created_at: datetime
  updated_at: datetime

  # Process timestamps (all optional)
  autolyse_ts: Optional[datetime] = None
  mix_ts: Optional[datetime] = None
  bulk_ts: Optional[datetime] = None
  preshape_ts: Optional[datetime] = None
  final_shape_ts: Optional[datetime] = None
  final_proof_ts: Optional[datetime] = None
  bake_ts: Optional[datetime] = None

  # Temperature data
  room_temp: Optional[float] = None
  water_temp: Optional[float] = None
  flour_temp: Optional[float] = None
  preferment_temp: Optional[float] = None
  dough_temp: Optional[float] = None
  temperature_unit: str = "Fahrenheit"

  # Stretch & fold count
  stretch_fold_count: int = 0

  # Notes
  notes: Optional[str] = None

  # Timezone of the baker (IANA timezone string)
  timezone: str = "UTC"


class BreadTimingListResponse(BaseModel):
  """Paginated response for timing list"""

  timings: List[BreadTiming]
  total_count: int
  page: int
  limit: int
  total_pages: int
  has_next: bool
  has_previous: bool
