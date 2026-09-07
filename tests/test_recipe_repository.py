"""RecipeRepository round-trips against the real database.

Each test cleans up the rows it creates.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from backend.db import DatabasePool
from backend.domain import models as domain
from backend.infrastructure.recipe_repository import RecipeRepository


@pytest.fixture(scope="module")
def repo():
  return RecipeRepository(DatabasePool())


def _recipe(name: str, *, category="sourdough"):
  return domain.Recipe.create(
    name=name,
    ingredients=[
      domain.Ingredient(name="flour", amount=1000, unit="grams", type="flour")
    ],
    instructions=[domain.RecipeStep(order=1, instruction="Mix", id=str(uuid4()))],
    now=datetime.now(),
    description="round-trip",
    category=category,
  )


class TestRoundTrip:
  def test_add_then_get(self, repo):
    recipe = _recipe("repo-add-get")
    repo.add(recipe)
    try:
      loaded = repo.get(recipe.id)
      assert loaded is not None
      assert loaded.name == "repo-add-get"
      assert loaded.description == "round-trip"
      assert loaded.current_version.version_number == 1
      assert loaded.current_version.description == "Initial version"
      assert [i.name for i in loaded.current_version.ingredients] == ["flour"]
      assert [s.instruction for s in loaded.current_version.instructions] == ["Mix"]
    finally:
      repo.delete(recipe.id)

  def test_save_adds_version_and_updates_scalars_atomically(self, repo):
    recipe = _recipe("repo-save")
    repo.add(recipe)
    try:
      recipe.add_version(
        ingredients=[
          domain.Ingredient(name="rye", amount=500, unit="grams", type="flour")
        ],
        instructions=[domain.RecipeStep(order=1, instruction="Fold", id=str(uuid4()))],
        now=datetime.now(),
        change_summary={"total_changes": 3},
      )
      recipe.name = "repo-save-renamed"
      recipe.category = "lean"
      repo.save(recipe)

      loaded = repo.get(recipe.id)
      assert loaded.name == "repo-save-renamed"
      assert loaded.category == "lean"
      assert loaded.current_version.version_number == 2
      assert [i.name for i in loaded.current_version.ingredients] == ["rye"]
      assert [v.version_number for v in repo.get_versions(recipe.id)] == [2, 1]

      v2 = repo.get_version(loaded.current_version.id)
      assert v2.change_summary == {"total_changes": 3}
    finally:
      repo.delete(recipe.id)

  def test_get_missing_returns_none(self, repo):
    assert repo.get(uuid4()) is None

  def test_delete_absent_returns_false(self, repo):
    assert repo.delete(uuid4()) is False

  def test_list_search_and_category_filter(self, repo):
    a = _recipe("repo-list-alpha", category="sourdough")
    b = _recipe("repo-list-beta", category="lean")
    repo.add(a)
    repo.add(b)
    try:
      names = {s.name for s in repo.list(search="repo-list")}
      assert {"repo-list-alpha", "repo-list-beta"} <= names

      lean = [s.name for s in repo.list(search="repo-list", category="lean")]
      assert lean == ["repo-list-beta"]

      summary = next(s for s in repo.list(search="repo-list-alpha"))
      assert summary.ingredient_count == 1
      assert summary.step_count == 1
    finally:
      repo.delete(a.id)
      repo.delete(b.id)
