"""Recipe request/response DTOs and API-level validation.

The HTTP edge shape — regex patterns and ``field_validator``s live here, not in
the domain model (``backend/domain/models.py``).
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# --- Request DTOs ------------------------------------------------------------


class Ingredient(BaseModel):
  name: str = Field(..., min_length=1, description="Ingredient name cannot be empty")
  amount: float = Field(..., gt=0, description="Amount must be greater than 0")
  unit: str = Field(
    ..., pattern=r"^(grams|kg|ml|cups|tbsp|tsp)$", description="Must be valid unit"
  )
  type: str = Field(
    ...,
    pattern=r"^(flour|liquid|preferment|fat|other)$",
    description="Must be valid ingredient type",
  )
  notes: Optional[str] = None

  @field_validator("name")
  @classmethod
  def name_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError("Ingredient name cannot be empty")
    return v.strip()


class RecipeStep(BaseModel):
  id: Optional[str] = None
  order: int = Field(..., gt=0, description="Order must be greater than 0")
  instruction: str = Field(..., min_length=1, description="Instruction cannot be empty")

  @field_validator("instruction")
  @classmethod
  def instruction_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError("Instruction cannot be empty")
    return v.strip()


class RecipeRequest(BaseModel):
  name: str = Field(
    ..., min_length=1, max_length=255, description="Recipe name is required"
  )
  description: Optional[str] = Field(None, max_length=1000)
  category: Optional[str] = Field(
    None, pattern=r"^(sourdough|enriched|lean|sweet|other)$"
  )
  ingredients: List[Ingredient] = Field(
    ..., min_length=1, description="At least one ingredient is required"
  )
  instructions: List[RecipeStep] = Field(
    ..., min_length=1, description="At least one instruction is required"
  )

  @field_validator("name")
  @classmethod
  def name_not_empty(cls, v):
    if not v or not v.strip():
      raise ValueError("Recipe name cannot be empty")
    return v.strip()


class RecipeVersionRequest(BaseModel):
  ingredients: List[Ingredient]
  instructions: List[RecipeStep]
  description: Optional[str] = None


# --- Response DTOs -----------------------------------------------------------


class RecipeVersion(BaseModel):
  id: UUID
  recipe_id: UUID
  version_number: int
  description: Optional[str] = None
  ingredients: List[Ingredient]
  instructions: List[RecipeStep]
  created_at: datetime
  change_summary: Optional[dict] = None


class Recipe(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  category: Optional[str] = None
  current_version_id: UUID
  current_version: RecipeVersion
  created_at: datetime
  updated_at: datetime


class RecipeListItem(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  category: Optional[str] = None
  version: str
  current_version_id: UUID
  ingredient_count: int
  step_count: int
  created_at: datetime
  updated_at: datetime


class RecipeCreateResponse(BaseModel):
  recipe: Recipe
  message: str
  success: bool = True
