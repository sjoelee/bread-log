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


_NAME = Field(..., min_length=1, max_length=255, description="Recipe name is required")
_NOTES = Field(None, max_length=1000)
_CATEGORY = Field(None, pattern=r"^(sourdough|enriched|lean|sweet|other)$")
_INGREDIENTS = Field(
  ..., min_length=1, description="At least one ingredient is required"
)
_INSTRUCTIONS = Field(
  ..., min_length=1, description="At least one instruction is required"
)


def _name_not_empty(v):
  if not v or not v.strip():
    raise ValueError("Recipe name cannot be empty")
  return v.strip()


class RecipeRequest(BaseModel):
  """Create a recipe: its details plus the content of its first Draft."""

  name: str = _NAME
  description: Optional[str] = _NOTES
  category: Optional[str] = _CATEGORY
  ingredients: List[Ingredient] = _INGREDIENTS
  instructions: List[RecipeStep] = _INSTRUCTIONS

  _check_name = field_validator("name")(_name_not_empty)


class RecipeDetailsRequest(BaseModel):
  """Edit the recipe-level fields. ``description`` holds the notes."""

  name: str = _NAME
  description: Optional[str] = _NOTES
  category: Optional[str] = _CATEGORY

  _check_name = field_validator("name")(_name_not_empty)


class DraftRequest(BaseModel):
  """Save the Draft's content."""

  ingredients: List[Ingredient] = _INGREDIENTS
  instructions: List[RecipeStep] = _INSTRUCTIONS


class ChangesResponse(BaseModel):
  has_changes: bool


class PromoteRequest(BaseModel):
  release_note: Optional[str] = Field(None, max_length=1000)


# --- Response DTOs -----------------------------------------------------------


class RecipeVersion(BaseModel):
  id: UUID
  recipe_id: UUID
  state: str
  version_number: Optional[int] = None
  release_note: Optional[str] = None
  ingredients: List[Ingredient]
  instructions: List[RecipeStep]
  created_at: datetime
  change_summary: Optional[dict] = None


class Recipe(BaseModel):
  """A recipe with its latest Ready version and its Draft, each present only if
  it exists (at least one always does)."""

  id: UUID
  name: str
  description: Optional[str] = None
  category: Optional[str] = None
  created_at: datetime
  updated_at: datetime
  latest_ready: Optional[RecipeVersion] = None
  draft: Optional[RecipeVersion] = None


class VersionSummary(BaseModel):
  version_id: UUID
  version_number: Optional[int] = None
  ingredient_count: int
  step_count: int


class RecipeListItem(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  category: Optional[str] = None
  created_at: datetime
  updated_at: datetime
  latest_ready: Optional[VersionSummary] = None
  draft: Optional[VersionSummary] = None
