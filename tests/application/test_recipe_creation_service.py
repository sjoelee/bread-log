"""RecipeService against an in-memory repository — no database."""

from datetime import datetime
from uuid import uuid4

import pytest

from backend.application.recipe_service import RecipeService
from backend.domain import models as domain
from backend.exceptions import NotFoundError
from tests.fakes import FakeRecipeRepository, FakeUnitOfWork

FIXED_NOW = datetime(2024, 5, 1, 12, 0, 0)


def _service():
  repo = FakeRecipeRepository()
  return RecipeService(lambda: FakeUnitOfWork(repo), now=lambda: FIXED_NOW)


def _content(**overrides):
  data = dict(
    name="Simple Sourdough",
    description="Basic country bread",
    category="sourdough",
    ingredients=[
      domain.Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
      domain.Ingredient(name="water", amount=750, unit="grams", type="liquid"),
    ],
    instructions=[
      domain.RecipeStep(order=1, instruction="Autolyse"),
      domain.RecipeStep(order=2, instruction="Mix"),
    ],
  )
  data.update(overrides)
  return data


class TestCreateRecipe:
  def test_creates_version_one_with_generated_ids(self):
    svc = _service()
    recipe = svc.create_recipe(**_content())

    assert isinstance(recipe, domain.Recipe)
    assert recipe.name == "Simple Sourdough"
    assert recipe.category == "sourdough"
    assert recipe.current_version.version_number == 1
    assert recipe.current_version.description == "Initial version"
    assert all(s.id for s in recipe.current_version.instructions)
    assert recipe.created_at == FIXED_NOW


class TestUpdateRecipe:
  def test_full_update_bumps_version_and_updates_metadata(self):
    svc = _service()
    created = svc.create_recipe(**_content())

    updated = svc.update_recipe_full(
      created.id,
      **_content(
        name="Renamed",
        category="lean",
        ingredients=[
          domain.Ingredient(name="rye", amount=900, unit="grams", type="flour")
        ],
        instructions=[domain.RecipeStep(order=1, instruction="Mix well")],
      ),
    )

    assert updated.name == "Renamed"
    assert updated.category == "lean"
    assert updated.current_version.version_number == 2
    assert [i.name for i in updated.current_version.ingredients] == ["rye"]
    assert updated.current_version.change_summary["total_changes"] > 0

  def test_update_missing_recipe_raises(self):
    with pytest.raises(NotFoundError, match="not found"):
      _service().update_recipe_full(uuid4(), **_content())


class TestQueries:
  def test_get_and_list_and_delete(self):
    svc = _service()
    created = svc.create_recipe(**_content(name="Findable"))

    assert svc.get_recipe(created.id).name == "Findable"

    listed = svc.list_recipes(search="findable")
    assert [item.name for item in listed] == ["Findable"]
    assert listed[0].version_number == 1

    assert svc.delete_recipe(created.id) is True
    with pytest.raises(NotFoundError):
      svc.get_recipe(created.id)

  def test_get_missing_raises(self):
    with pytest.raises(NotFoundError, match="Recipe not found"):
      _service().get_recipe(uuid4())

  def test_delete_missing_raises(self):
    with pytest.raises(NotFoundError):
      _service().delete_recipe(uuid4())

  def test_version_history_and_diff(self):
    svc = _service()
    created = svc.create_recipe(**_content())
    svc.update_recipe_full(
      created.id,
      **_content(
        ingredients=[
          domain.Ingredient(name="bread flour", amount=1000, unit="grams", type="flour")
        ],
        instructions=[domain.RecipeStep(order=1, instruction="Autolyse")],
      ),
    )

    versions = svc.get_recipe_versions(created.id)
    assert [v.version_number for v in versions] == [2, 1]

    diff = svc.get_recipe_version_diff(created.id, versions[1].id, versions[0].id)
    assert diff["from_version"] == "1"
    assert diff["to_version"] == "2"
