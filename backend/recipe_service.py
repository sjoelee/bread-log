"""Recipe use cases: DTO in, DTO out, domain objects in between."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Callable, List, Optional
from uuid import UUID

from .api import mappers, schemas
from .domain import models as domain
from .domain import versioning

if TYPE_CHECKING:
  from .infrastructure.unit_of_work import UnitOfWork


class RecipeService:
  """Recipe use cases. Each method takes/returns API DTOs (``api.schemas``) and
  works with domain objects and the repository in between.

  Every method opens a ``UnitOfWork`` for the duration of the use case: all its
  repository calls share one connection and one transaction, committed on a
  clean return and rolled back if anything raises.

  ``now`` is an injectable clock — override it in tests to get deterministic
  timestamps.
  """

  def __init__(
    self,
    uow_factory: Callable[[], "UnitOfWork"],
    *,
    now: Callable[[], datetime] = datetime.now,
  ):
    self._uow_factory = uow_factory
    self._now = now

  # --- commands ----------------------------------------------------------

  def create_recipe(self, request: schemas.RecipeRequest) -> schemas.Recipe:
    """Create a recipe and its first version (``version_number`` 1).

    Fills in a UUID for any step that lacks one, persists the recipe, and
    returns the freshly reloaded full recipe.
    """
    recipe = domain.Recipe.create(
      name=request.name,
      ingredients=mappers.ingredients_to_domain(request.ingredients),
      instructions=versioning.assign_step_ids(
        mappers.steps_to_domain(request.instructions)
      ),
      now=self._now(),
      description=request.description,
      category=request.category,
    )
    with self._uow_factory() as uow:
      uow.recipes.add(recipe)
      return self._reload(uow, recipe.id)

  def update_recipe_full(
    self, recipe_id: UUID, request: schemas.RecipeRequest
  ) -> schemas.Recipe:
    """Replace a recipe wholesale from a full request body.

    Adds a new version (with a computed ``change_summary`` against the previous
    one) and updates the recipe's ``name``/``description``/``category``. The
    read, the version bump, and the metadata update are one transaction.
    Raises ``ValueError`` if the recipe does not exist.
    """
    with self._uow_factory() as uow:
      recipe = uow.recipes.get(recipe_id)
      if recipe is None:
        raise ValueError(f"Recipe with ID {recipe_id} not found")

      new_ingredients = mappers.ingredients_to_domain(request.ingredients)
      new_steps = versioning.assign_step_ids(
        mappers.steps_to_domain(request.instructions)
      )

      recipe.add_version(
        ingredients=new_ingredients,
        instructions=new_steps,
        now=self._now(),
        description=request.description,
        change_summary=self._change_summary(
          recipe.current_version, new_ingredients, new_steps
        ),
      )
      recipe.name = request.name
      recipe.description = request.description
      recipe.category = request.category
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def create_recipe_version(
    self,
    recipe_id: UUID,
    ingredients: List[schemas.Ingredient],
    instructions: List[schemas.RecipeStep],
    description: Optional[str] = None,
  ) -> schemas.Recipe:
    """Add a new version to an existing recipe, leaving its name/category alone.

    Like ``update_recipe_full`` but scoped to version content only.
    ``version_number`` always increments by one. Raises ``ValueError`` if the
    recipe does not exist.
    """
    with self._uow_factory() as uow:
      recipe = uow.recipes.get(recipe_id)
      if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")

      new_ingredients = mappers.ingredients_to_domain(ingredients)
      new_steps = versioning.assign_step_ids(mappers.steps_to_domain(instructions))

      recipe.add_version(
        ingredients=new_ingredients,
        instructions=new_steps,
        now=self._now(),
        description=description,
        change_summary=self._change_summary(
          recipe.current_version, new_ingredients, new_steps
        ),
      )
      uow.recipes.save(recipe)
      return self._reload(uow, recipe_id)

  def delete_recipe(self, recipe_id: UUID) -> bool:
    """Delete a recipe and (via cascade) all its versions.

    Raises ``ValueError`` if it does not exist; otherwise returns ``True``.
    """
    with self._uow_factory() as uow:
      if uow.recipes.get(recipe_id) is None:
        raise ValueError(f"Recipe with ID {recipe_id} not found")
      return uow.recipes.delete(recipe_id)

  # --- queries -----------------------------------------------------------

  def get_recipe(self, recipe_id: UUID) -> Optional[schemas.Recipe]:
    """Return the full recipe (metadata + current version) or ``None`` if absent."""
    with self._uow_factory() as uow:
      recipe = uow.recipes.get(recipe_id)
      return mappers.recipe_to_dto(recipe) if recipe else None

  def list_recipes(
    self,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    ingredient: Optional[str] = None,
  ) -> List[schemas.RecipeListItem]:
    """Return a page of lightweight list items (no full version content).

    ``search`` matches the name; ``ingredient`` matches an ingredient name in the
    current version; ``category`` is an exact match. ``sort_by`` is ``created_at``
    or ``name``, ``sort_direction`` is ``asc`` or ``desc``.
    """
    with self._uow_factory() as uow:
      summaries = uow.recipes.list(
        category=category,
        search=search,
        ingredient=ingredient,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset,
      )
      return [mappers.summary_to_dto(s) for s in summaries]

  def get_recipe_versions(self, recipe_id: UUID) -> List[schemas.RecipeVersion]:
    """Return every version of the recipe, newest ``version_number`` first.

    Empty list if the recipe has no versions or does not exist.
    """
    with self._uow_factory() as uow:
      return [mappers.version_to_dto(v) for v in uow.recipes.get_versions(recipe_id)]

  def get_recipe_version_diff(
    self, recipe_id: UUID, version_id_1: UUID, version_id_2: UUID
  ) -> dict:
    """Compare two versions and return their ingredient and step changes.

    Both versions must exist and belong to ``recipe_id`` — otherwise
    ``ValueError``. The result is a plain dict (``from_version``, ``to_version``,
    ``ingredient_changes``, ``step_changes``, ``created_at``) shaped for the API.
    """
    with self._uow_factory() as uow:
      v1 = uow.recipes.get_version(version_id_1)
      v2 = uow.recipes.get_version(version_id_2)
      if not v1 or not v2:
        raise ValueError("One or both versions not found")
      if v1.recipe_id != recipe_id or v2.recipe_id != recipe_id:
        raise ValueError("One or both versions do not belong to the specified recipe")
      return {
        "from_version": str(v1.version_number),
        "to_version": str(v2.version_number),
        "ingredient_changes": versioning.compare_ingredients(
          [asdict(i) for i in v1.ingredients], [asdict(i) for i in v2.ingredients]
        ),
        "step_changes": versioning.compare_instructions(
          [asdict(s) for s in v1.instructions], [asdict(s) for s in v2.instructions]
        ),
        "created_at": v2.created_at,
      }

  # --- helpers ---------------------------------------------------------

  def _reload(self, uow: "UnitOfWork", recipe_id: UUID) -> schemas.Recipe:
    """Re-read a recipe inside the current transaction and map it to a DTO, so
    callers get the persisted view. Raises ``ValueError`` if it vanished."""
    recipe = uow.recipes.get(recipe_id)
    if recipe is None:
      raise ValueError(f"Failed to load recipe {recipe_id}")
    return mappers.recipe_to_dto(recipe)

  def _change_summary(
    self,
    previous: domain.RecipeVersion,
    new_ingredients: List[domain.Ingredient],
    new_steps: List[domain.RecipeStep],
  ) -> dict:
    """Diff the proposed content against ``previous`` and return the summary
    counts stored on the new version's ``change_summary``."""
    return versioning.create_version_summary(
      versioning.compare_ingredients(
        [asdict(i) for i in previous.ingredients],
        [asdict(i) for i in new_ingredients],
      ),
      versioning.compare_instructions(
        [asdict(s) for s in previous.instructions],
        [asdict(s) for s in new_steps],
      ),
    )
