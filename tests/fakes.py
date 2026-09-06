"""In-memory RecipeRepository for tests that don't need a database."""

from __future__ import annotations

import copy
from uuid import UUID

from backend.domain import models as domain


class FakeRecipeRepository:
  def __init__(self):
    self._recipes: dict[UUID, domain.Recipe] = {}
    self._history: dict[UUID, list[domain.RecipeVersion]] = {}

  def get(self, recipe_id: UUID):
    recipe = self._recipes.get(recipe_id)
    return copy.deepcopy(recipe) if recipe else None

  def get_version(self, version_id: UUID):
    for versions in self._history.values():
      for v in versions:
        if v.id == version_id:
          return copy.deepcopy(v)
    return None

  def get_versions(self, recipe_id: UUID):
    versions = self._history.get(recipe_id, [])
    return [
      copy.deepcopy(v)
      for v in sorted(versions, key=lambda v: v.version_number, reverse=True)
    ]

  def list(self, *, category=None, search=None, **_ignored):
    summaries = []
    for r in self._recipes.values():
      cv = r.current_version
      summaries.append(
        domain.RecipeSummary(
          id=r.id,
          name=r.name,
          description=r.description,
          category=r.category,
          version_number=cv.version_number,
          current_version_id=cv.id,
          ingredient_count=len(cv.ingredients),
          step_count=len(cv.instructions),
          created_at=r.created_at,
          updated_at=r.updated_at,
        )
      )
    if category:
      summaries = [s for s in summaries if s.category == category]
    if search:
      summaries = [s for s in summaries if search.lower() in s.name.lower()]
    return summaries

  def add(self, recipe: domain.Recipe) -> None:
    self._recipes[recipe.id] = copy.deepcopy(recipe)
    self._history.setdefault(recipe.id, []).append(
      copy.deepcopy(recipe.current_version)
    )

  def save(self, recipe: domain.Recipe) -> None:
    if recipe.id not in self._recipes:
      raise ValueError(f"Recipe {recipe.id} not found")
    self._recipes[recipe.id] = copy.deepcopy(recipe)
    history = self._history.setdefault(recipe.id, [])
    if not any(v.id == recipe.current_version.id for v in history):
      history.append(copy.deepcopy(recipe.current_version))

  def delete(self, recipe_id: UUID) -> bool:
    existed = recipe_id in self._recipes
    self._recipes.pop(recipe_id, None)
    self._history.pop(recipe_id, None)
    return existed
