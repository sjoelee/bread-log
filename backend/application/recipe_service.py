"""Recipe use cases: domain objects in, domain objects out."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Callable, List, Optional
from uuid import UUID

from ..domain import models as domain
from ..domain import versioning
from ..exceptions import NotFoundError
from .unit_of_work import UnitOfWork


class RecipeService:
  """Recipe use cases. Each method takes and returns domain objects; translating
  to and from API DTOs is the interface layer's job.

  Every method opens a ``UnitOfWork`` for the duration of the use case: all its
  repository calls share one connection and one transaction, committed on a
  clean return and rolled back if anything raises.

  ``now`` is an injectable clock — override it in tests to get deterministic
  timestamps.
  """

  def __init__(
    self,
    uow_factory: Callable[[], UnitOfWork],
    *,
    now: Callable[[], datetime] = datetime.now,
  ):
    self._uow_factory = uow_factory
    self._now = now

  # --- commands ----------------------------------------------------------

  def create_recipe(
    self,
    *,
    name: str,
    ingredients: List[domain.Ingredient],
    instructions: List[domain.RecipeStep],
    description: Optional[str] = None,
    category: Optional[str] = None,
  ) -> domain.Recipe:
    """Create a recipe whose content is a Draft (no Ready version yet).

    Fills in a UUID for any step that lacks one and returns the reloaded recipe.
    """
    recipe = domain.Recipe.create(
      name=name,
      ingredients=ingredients,
      instructions=versioning.assign_step_ids(instructions),
      now=self._now(),
      description=description,
      category=category,
    )
    with self._uow_factory() as uow:
      uow.recipes.add(recipe)
      return self._reload(uow, recipe.id)

  def update_details(
    self,
    recipe_id: UUID,
    *,
    name: str,
    description: Optional[str] = None,
    category: Optional[str] = None,
  ) -> domain.Recipe:
    """Change the recipe's name, notes and category. Versions are untouched.
    Raises ``NotFoundError`` if the recipe does not exist."""
    with self._uow_factory() as uow:
      recipe = self._get(uow, recipe_id)
      recipe.update_details(
        name=name, description=description, category=category, now=self._now()
      )
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def save_draft(
    self,
    recipe_id: UUID,
    *,
    ingredients: List[domain.Ingredient],
    instructions: List[domain.RecipeStep],
  ) -> domain.Recipe:
    """Replace the Draft's content, creating the Draft if there is none.
    Raises ``NotFoundError`` if the recipe does not exist."""
    with self._uow_factory() as uow:
      recipe = self._get(uow, recipe_id)
      recipe.save_draft(
        ingredients=ingredients,
        instructions=versioning.assign_step_ids(instructions),
        now=self._now(),
      )
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def promote(
    self, recipe_id: UUID, *, release_note: Optional[str] = None
  ) -> domain.Recipe:
    """Turn the Draft into the next Ready version.

    Raises ``NotFoundError`` if the recipe does not exist, ``NoDraftError`` if it
    has no Draft, and ``DraftUnchangedError`` if the Draft equals the latest
    Ready version.
    """
    with self._uow_factory() as uow:
      recipe = self._get(uow, recipe_id)
      recipe.promote(release_note=release_note, now=self._now())
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def discard_draft(self, recipe_id: UUID) -> Optional[domain.Recipe]:
    """Throw away the Draft. Returns the recipe, or ``None`` if it had no Ready
    version and was therefore deleted. Raises ``NotFoundError`` if the recipe
    does not exist and ``NoDraftError`` if it has no Draft."""
    with self._uow_factory() as uow:
      recipe = self._get(uow, recipe_id)
      if recipe.discard_draft():
        uow.recipes.delete(recipe_id)
        return None
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def delete_recipe(self, recipe_id: UUID) -> bool:
    """Delete a recipe and (via cascade) all its versions.

    Raises ``NotFoundError`` if it does not exist; otherwise returns ``True``.
    """
    with self._uow_factory() as uow:
      if uow.recipes.get(recipe_id) is None:
        raise NotFoundError(f"Recipe with ID {recipe_id} not found")
      return uow.recipes.delete(recipe_id)

  # --- queries -----------------------------------------------------------

  def get_recipe(self, recipe_id: UUID) -> domain.Recipe:
    """Return the full recipe: its fields, latest Ready version and Draft.

    Raises ``NotFoundError`` if the recipe does not exist.
    """
    with self._uow_factory() as uow:
      recipe = uow.recipes.get(recipe_id)
      if recipe is None:
        raise NotFoundError("Recipe not found")
      return recipe

  def list_recipes(
    self,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    ingredient: Optional[str] = None,
    state: str = "any",
  ) -> List[domain.RecipeSummary]:
    """Return a page of lightweight summaries (no full version content).

    ``search`` matches the name; ``category`` is an exact match. ``state`` is
    ``any``, ``draft`` (recipes with a Draft) or ``ready`` (recipes with a Ready
    version); ``ingredient`` matches an ingredient name in that part, or in either
    the Draft or the latest Ready version for ``any``. ``sort_by`` is ``created_at``
    or ``name``, ``sort_direction`` is ``asc`` or ``desc``.
    """
    with self._uow_factory() as uow:
      return uow.recipes.list(
        category=category,
        search=search,
        ingredient=ingredient,
        state=state,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset,
      )

  def get_recipe_versions(self, recipe_id: UUID) -> List[domain.RecipeVersion]:
    """Return the recipe's Ready versions, newest first. The Draft is not history.

    Empty list if the recipe has no Ready versions or does not exist.
    """
    with self._uow_factory() as uow:
      return uow.recipes.get_versions(recipe_id)

  def get_recipe_version_diff(
    self, recipe_id: UUID, version_id_1: UUID, version_id_2: UUID
  ) -> dict:
    """Compare two versions and return their ingredient and step changes.

    Both versions must exist and belong to ``recipe_id`` — otherwise
    ``NotFoundError``. Either may be the Draft. The result is a plain dict (``from_version``, ``to_version``,
    ``ingredient_changes``, ``step_changes``, ``created_at``) shaped for the API.
    """
    with self._uow_factory() as uow:
      v1 = uow.recipes.get_version(version_id_1)
      v2 = uow.recipes.get_version(version_id_2)
      if not v1 or not v2:
        raise NotFoundError("One or both versions not found")
      if v1.recipe_id != recipe_id or v2.recipe_id != recipe_id:
        raise NotFoundError(
          "One or both versions do not belong to the specified recipe"
        )
      return {
        "from_version": _label(v1),
        "to_version": _label(v2),
        "ingredient_changes": versioning.compare_ingredients(
          [asdict(i) for i in v1.ingredients], [asdict(i) for i in v2.ingredients]
        ),
        "step_changes": versioning.compare_instructions(
          [asdict(s) for s in v1.instructions], [asdict(s) for s in v2.instructions]
        ),
        "created_at": v2.created_at,
      }

  # --- helpers ---------------------------------------------------------

  def _reload(self, uow: UnitOfWork, recipe_id: UUID) -> domain.Recipe:
    """Re-read a recipe inside the current transaction, so callers get the
    persisted view. Raises ``ValueError`` if it vanished."""
    recipe = uow.recipes.get(recipe_id)
    if recipe is None:
      raise ValueError(f"Failed to load recipe {recipe_id}")
    return recipe

  def _get(self, uow: UnitOfWork, recipe_id: UUID) -> domain.Recipe:
    recipe = uow.recipes.get(recipe_id)
    if recipe is None:
      raise NotFoundError(f"Recipe with ID {recipe_id} not found")
    return recipe


def _label(version: domain.RecipeVersion) -> str:
  """``"draft"`` for the Draft, else the version number."""
  return "draft" if version.version_number is None else str(version.version_number)
