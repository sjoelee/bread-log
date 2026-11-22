"""In-memory RecipeRepository + UnitOfWork for tests that don't need a database."""

from __future__ import annotations

import copy
from uuid import UUID

from backend.application.unit_of_work import UnitOfWork
from backend.domain import models as domain
from backend.domain.repositories import RecipeRepository
from backend.exceptions import NotFoundError


class FakeUnitOfWork:
  """Stands in for ``infrastructure.unit_of_work.UnitOfWork``.

  Holds one ``FakeRecipeRepository`` so state survives across use cases in a
  test. Records whether the block committed or rolled back.
  """

  def __init__(self, recipes: "FakeRecipeRepository | None" = None):
    self.recipes = recipes if recipes is not None else FakeRecipeRepository()
    self.committed = False
    self.rolled_back = False

  def __enter__(self) -> "FakeUnitOfWork":
    return self

  def __exit__(self, exc_type, exc, tb) -> bool:
    if exc_type is None:
      self.committed = True
    else:
      self.rolled_back = True
    return False


class FakeRecipeRepository:
  """Keeps each recipe (with its Draft and latest Ready version) plus the full
  Ready history, mirroring what ``PostgresRecipeRepository`` stores."""

  def __init__(self):
    self._recipes: dict[UUID, domain.Recipe] = {}
    self._ready: dict[UUID, list[domain.RecipeVersion]] = {}

  def get(self, recipe_id: UUID):
    recipe = self._recipes.get(recipe_id)
    return copy.deepcopy(recipe) if recipe else None

  def get_version(self, version_id: UUID):
    for recipe in self._recipes.values():
      if recipe.draft is not None and recipe.draft.id == version_id:
        return copy.deepcopy(recipe.draft)
    for versions in self._ready.values():
      for v in versions:
        if v.id == version_id:
          return copy.deepcopy(v)
    return None

  def get_versions(self, recipe_id: UUID):
    versions = self._ready.get(recipe_id, [])
    return [
      copy.deepcopy(v)
      for v in sorted(versions, key=lambda v: v.version_number or 0, reverse=True)
    ]

  def list(
    self,
    *,
    category=None,
    search=None,
    ingredient=None,
    state="any",
    sort_by="created_at",
    sort_direction="desc",
    limit=50,
    offset=0,
  ):
    def parts(r: domain.Recipe):
      if state == "draft":
        return [r.draft]
      if state == "ready":
        return [r.latest_ready]
      return [r.draft, r.latest_ready]

    def has_ingredient(v, needle: str):
      return v is not None and any(needle in i.name.lower() for i in v.ingredients)

    recipes = list(self._recipes.values())
    if category:
      recipes = [r for r in recipes if r.category == category]
    if search:
      recipes = [r for r in recipes if search.lower() in r.name.lower()]
    recipes = [r for r in recipes if any(v is not None for v in parts(r))]
    if ingredient:
      needle = ingredient.lower()
      recipes = [r for r in recipes if any(has_ingredient(v, needle) for v in parts(r))]
    key = (lambda r: r.name) if sort_by == "name" else (lambda r: r.created_at)
    recipes.sort(key=key, reverse=sort_direction.lower() != "asc")
    return [_summary(r) for r in recipes[offset : offset + limit]]

  def add(self, recipe: domain.Recipe) -> None:
    self._recipes[recipe.id] = copy.deepcopy(recipe)
    self._record_ready(recipe)

  def save(self, recipe: domain.Recipe) -> None:
    if recipe.id not in self._recipes:
      raise NotFoundError(f"Recipe {recipe.id} not found")
    stored = copy.deepcopy(recipe)
    # Like the real repository, a Ready version that is already stored is frozen:
    # rewriting it is ignored.
    frozen = next(
      (
        v
        for v in self._ready.get(recipe.id, [])
        if recipe.latest_ready is not None and v.id == recipe.latest_ready.id
      ),
      None,
    )
    if frozen is not None:
      stored.latest_ready = copy.deepcopy(frozen)
    self._recipes[recipe.id] = stored
    self._record_ready(recipe)

  def delete(self, recipe_id: UUID) -> bool:
    existed = recipe_id in self._recipes
    self._recipes.pop(recipe_id, None)
    self._ready.pop(recipe_id, None)
    return existed

  def _record_ready(self, recipe: domain.Recipe) -> None:
    history = self._ready.setdefault(recipe.id, [])
    ready = recipe.latest_ready
    if ready is not None and not any(v.id == ready.id for v in history):
      history.append(copy.deepcopy(ready))


def _version_summary(v):
  if v is None:
    return None
  return domain.VersionSummary(
    version_id=v.id,
    version_number=v.version_number,
    ingredient_count=len(v.ingredients),
    step_count=len(v.instructions),
  )


def _summary(r: domain.Recipe) -> domain.RecipeSummary:
  return domain.RecipeSummary(
    id=r.id,
    name=r.name,
    description=r.description,
    category=r.category,
    created_at=r.created_at,
    updated_at=r.updated_at,
    latest_ready=_version_summary(r.latest_ready),
    draft=_version_summary(r.draft),
  )


# Never used at runtime: these assignments make pyright check that the fakes
# still satisfy the interfaces the application layer depends on.
_repository: RecipeRepository = FakeRecipeRepository()
_unit_of_work: UnitOfWork = FakeUnitOfWork()
