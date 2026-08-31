"""Domain model: value objects and the Recipe aggregate.

Plain dataclasses — no Pydantic, no psycopg, no FastAPI. Introduced in Stage 2 as
scaffolding; nothing wires through these yet. Stage 3 (DTOs + mappers) gives them
their first real consumer, and Part II grows the aggregate (Draft/Ready lifecycle,
components).

Current field names mirror today's reality (a step's text is ``instruction``,
ingredient ``type`` is the old five-value vocab). Part II renames/extends.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


# --- Value objects (immutable, identity-free) ----------------------------------


@dataclass(frozen=True)
class Ingredient:
  name: str
  amount: float
  unit: str
  # flour | liquid | preferment | fat | other — optional; a user may not classify
  # an ingredient.
  # TODO: `type` is bread-specific. A candidate to move to a bread specialization
  # of Recipe (e.g. BreadRecipe, by inheritance or a BreadFormula value object)
  # once the domain is recipe-general.
  type: Optional[str] = None
  notes: Optional[str] = None
  id: Optional[str] = None


@dataclass(frozen=True)
class RecipeStep:
  order: int
  instruction: str
  id: Optional[str] = None


# --- Entities -----------------------------------------------------------------


@dataclass
class RecipeVersion:
  id: UUID
  recipe_id: UUID
  version_number: int
  ingredients: list[Ingredient]
  instructions: list[RecipeStep]
  created_at: datetime
  description: Optional[str] = None
  change_summary: Optional[dict] = None


@dataclass
class Recipe:
  """Aggregate root: identity, metadata, and the current version.

  A ``RecipeVersion`` has no lifecycle of its own — it lives and dies with the
  Recipe. Full version history is a separate repository read, not held here.
  """

  id: UUID
  name: str
  created_at: datetime
  updated_at: datetime
  current_version: RecipeVersion
  description: Optional[str] = None
  category: Optional[str] = None

  @classmethod
  def create(
    cls,
    *,
    name: str,
    ingredients: list[Ingredient],
    instructions: list[RecipeStep],
    now: datetime,
    description: Optional[str] = None,
    category: Optional[str] = None,
    recipe_id: Optional[UUID] = None,
    version_id: Optional[UUID] = None,
  ) -> "Recipe":
    """Build a new recipe with its initial version (number 1)."""
    recipe_id = recipe_id or uuid.uuid4()
    version_id = version_id or uuid.uuid4()
    first_version = RecipeVersion(
      id=version_id,
      recipe_id=recipe_id,
      version_number=1,
      description=description or "Initial version",
      ingredients=list(ingredients),
      instructions=list(instructions),
      created_at=now,
    )
    return cls(
      id=recipe_id,
      name=name,
      description=description,
      category=category,
      current_version=first_version,
      created_at=now,
      updated_at=now,
    )

  def add_version(
    self,
    *,
    ingredients: list[Ingredient],
    instructions: list[RecipeStep],
    now: datetime,
    description: Optional[str] = None,
    change_summary: Optional[dict] = None,
  ) -> RecipeVersion:
    """Replace the current version with a new one, ``version_number`` += 1.

    Behavior-preserving mirror of ``RecipeService._create_recipe_version``.
    Part II Slice A replaces this with ``edit_draft()`` + ``promote()``.
    """
    next_number = self.current_version.version_number + 1
    version = RecipeVersion(
      id=uuid.uuid4(),
      recipe_id=self.id,
      version_number=next_number,
      description=description or f"Auto-save v{next_number}",
      ingredients=list(ingredients),
      instructions=list(instructions),
      created_at=now,
      change_summary=change_summary,
    )
    self.current_version = version
    self.updated_at = now
    return version
