"""Domain model: value objects and the Recipe aggregate.

Plain dataclasses — no Pydantic, no psycopg, no FastAPI imports.
"""

from __future__ import annotations

import dataclasses
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..exceptions import DraftUnchangedError, NoDraftError
from . import versioning

DRAFT = "draft"
READY = "ready"


# --- Value objects (immutable, identity-free) ----------------------------------


@dataclass(frozen=True)
class Ingredient:
  name: str
  amount: float
  unit: str
  # optional classification, e.g. flour | liquid | preferment | fat | other
  type: Optional[str] = None
  notes: Optional[str] = None


@dataclass(frozen=True)
class RecipeStep:
  order: int
  instruction: str
  id: Optional[str] = None


@dataclass(frozen=True)
class VersionSummary:
  """Counts for one version in a list row."""

  version_id: UUID
  version_number: Optional[int]
  ingredient_count: int
  step_count: int


@dataclass(frozen=True)
class RecipeSummary:
  """Flat read model returned by ``RecipeRepository.list()`` — a database-computed
  projection, not part of any aggregate. Carries the latest Ready version and the
  Draft separately; at least one is present."""

  id: UUID
  name: str
  description: Optional[str]
  category: Optional[str]
  created_at: datetime
  updated_at: datetime
  latest_ready: Optional[VersionSummary]
  draft: Optional[VersionSummary]


# --- Entities -----------------------------------------------------------------


@dataclass
class RecipeVersion:
  """One snapshot of a recipe's content: its ingredients and steps.

  A Draft (``state == DRAFT``) is the single mutable working copy and has no
  number. A Ready version (``state == READY``) is numbered and frozen.
  """

  id: UUID
  recipe_id: UUID
  state: str
  version_number: Optional[int]
  ingredients: list[Ingredient]
  instructions: list[RecipeStep]
  created_at: datetime
  release_note: Optional[str] = None
  change_summary: Optional[dict] = None


@dataclass
class Recipe:
  """Aggregate root: the named recipe and the entry point for changing it.

  Name, category and notes (``description``) belong to the recipe and are edited
  directly. Content lives on versions: at most one ``draft`` and the
  ``latest_ready`` version; older Ready versions are a separate repository read.
  A recipe always has at least one of the two.
  """

  id: UUID
  name: str
  created_at: datetime
  updated_at: datetime
  description: Optional[str] = None
  category: Optional[str] = None
  latest_ready: Optional[RecipeVersion] = None
  draft: Optional[RecipeVersion] = None

  def __post_init__(self):
    if self.latest_ready is None and self.draft is None:
      raise ValueError(f"Recipe {self.id} has neither a Draft nor a Ready version")

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
    """Build a new recipe whose content is a Draft; it has no Ready version."""
    recipe_id = recipe_id or uuid.uuid4()
    draft = RecipeVersion(
      id=version_id or uuid.uuid4(),
      recipe_id=recipe_id,
      state=DRAFT,
      version_number=None,
      ingredients=list(ingredients),
      instructions=list(instructions),
      created_at=now,
    )
    return cls(
      id=recipe_id,
      name=name,
      description=description,
      category=category,
      draft=draft,
      created_at=now,
      updated_at=now,
    )

  def update_details(
    self,
    *,
    name: str,
    description: Optional[str],
    category: Optional[str],
    now: datetime,
  ) -> None:
    """Change the recipe-level fields. Versions are untouched."""
    self.name = name
    self.description = description
    self.category = category
    self.updated_at = now

  def save_draft(
    self,
    *,
    ingredients: list[Ingredient],
    instructions: list[RecipeStep],
    now: datetime,
  ) -> RecipeVersion:
    """Replace the Draft's content, creating the Draft if there is none."""
    if self.draft is None:
      self.draft = RecipeVersion(
        id=uuid.uuid4(),
        recipe_id=self.id,
        state=DRAFT,
        version_number=None,
        ingredients=list(ingredients),
        instructions=list(instructions),
        created_at=now,
      )
    else:
      self.draft = dataclasses.replace(
        self.draft, ingredients=list(ingredients), instructions=list(instructions)
      )
    self.updated_at = now
    return self.draft

  def draft_has_changes(self) -> bool:
    """True if there is a Draft and its content differs in any way from the latest
    Ready version (or there is no Ready version yet).

    Exact comparison: ingredient order, name spelling and every field count. Steps
    compare by order and text; step ids are identity, not content.
    """
    if self.draft is None:
      return False
    if self.latest_ready is None:
      return True
    return _content(self.draft) != _content(self.latest_ready)

  def promote(self, *, release_note: Optional[str], now: datetime) -> RecipeVersion:
    """Turn the Draft into the next Ready version and leave no Draft.

    Raises ``NoDraftError`` without a Draft, and ``DraftUnchangedError`` if the
    Draft's content equals the latest Ready version's.
    """
    if self.draft is None:
      raise NoDraftError(f"Recipe {self.id} has no Draft to promote")
    previous = self.latest_ready
    if previous is not None and not self.draft_has_changes():
      raise DraftUnchangedError(
        f"Draft has no changes since version {previous.version_number}"
      )
    promoted = dataclasses.replace(
      self.draft,
      state=READY,
      version_number=(previous.version_number or 0) + 1 if previous else 1,
      release_note=release_note,
      change_summary=_change_summary(previous, self.draft) if previous else None,
      created_at=now,
    )
    self.latest_ready = promoted
    self.draft = None
    self.updated_at = now
    return promoted

  def discard_draft(self) -> bool:
    """Throw away the Draft. Returns True if the recipe is now empty (it had no
    Ready version) and must be deleted. Raises ``NoDraftError`` without a Draft."""
    if self.draft is None:
      raise NoDraftError(f"Recipe {self.id} has no Draft to discard")
    self.draft = None
    return self.latest_ready is None


def _content(version: RecipeVersion) -> tuple:
  return (
    tuple(version.ingredients),
    tuple((s.order, s.instruction) for s in version.instructions),
  )


def _change_summary(old: RecipeVersion, new: RecipeVersion) -> dict:
  return versioning.create_version_summary(
    versioning.compare_ingredients(
      [asdict(i) for i in old.ingredients], [asdict(i) for i in new.ingredients]
    ),
    versioning.compare_instructions(
      [asdict(s) for s in old.instructions], [asdict(s) for s in new.instructions]
    ),
  )
