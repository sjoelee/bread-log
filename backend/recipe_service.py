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
  from .infrastructure.recipe_repository import RecipeRepository


class RecipeService:
  def __init__(
    self,
    repo: "RecipeRepository",
    *,
    now: Callable[[], datetime] = datetime.now,
  ):
    self._repo = repo
    self._now = now

  # --- commands ----------------------------------------------------------

  def create_recipe(self, request: schemas.RecipeRequest) -> schemas.Recipe:
    recipe = domain.Recipe.create(
      name=request.name,
      ingredients=versioning.assign_ingredient_ids(
        mappers.ingredients_to_domain(request.ingredients)
      ),
      instructions=versioning.assign_step_ids(
        mappers.steps_to_domain(request.instructions)
      ),
      now=self._now(),
      description=request.description,
      category=request.category,
    )
    self._repo.add(recipe)
    return self._reload(recipe.id)

  def update_recipe_full(
    self, recipe_id: UUID, request: schemas.RecipeRequest
  ) -> schemas.Recipe:
    recipe = self._repo.get(recipe_id)
    if recipe is None:
      raise ValueError(f"Recipe with ID {recipe_id} not found")

    new_ingredients = versioning.assign_ingredient_ids(
      mappers.ingredients_to_domain(request.ingredients)
    )
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
    self._repo.save(recipe)
    return self._reload(recipe_id)

  def create_recipe_version(
    self,
    recipe_id: UUID,
    ingredients: List[schemas.Ingredient],
    instructions: List[schemas.RecipeStep],
    description: Optional[str] = None,
    force_major: bool = False,
  ) -> schemas.Recipe:
    recipe = self._repo.get(recipe_id)
    if recipe is None:
      raise ValueError(f"Recipe {recipe_id} not found")

    new_ingredients = versioning.assign_ingredient_ids(
      mappers.ingredients_to_domain(ingredients)
    )
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
    self._repo.save(recipe)
    return self._reload(recipe_id)

  def delete_recipe(self, recipe_id: UUID) -> bool:
    if self._repo.get(recipe_id) is None:
      raise ValueError(f"Recipe with ID {recipe_id} not found")
    return self._repo.delete(recipe_id)

  # --- queries -----------------------------------------------------------

  def get_recipe(self, recipe_id: UUID) -> Optional[schemas.Recipe]:
    recipe = self._repo.get(recipe_id)
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
    summaries = self._repo.list(
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
    return [mappers.version_to_dto(v) for v in self._repo.get_versions(recipe_id)]

  def get_recipe_version_diff(
    self, recipe_id: UUID, version_id_1: UUID, version_id_2: UUID
  ) -> dict:
    v1 = self._repo.get_version(version_id_1)
    v2 = self._repo.get_version(version_id_2)
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

  def _reload(self, recipe_id: UUID) -> schemas.Recipe:
    recipe = self._repo.get(recipe_id)
    if recipe is None:
      raise ValueError(f"Failed to load recipe {recipe_id}")
    return mappers.recipe_to_dto(recipe)

  def _change_summary(
    self,
    previous: domain.RecipeVersion,
    new_ingredients: List[domain.Ingredient],
    new_steps: List[domain.RecipeStep],
  ) -> dict:
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
