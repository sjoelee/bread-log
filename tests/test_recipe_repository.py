"""RecipeRepository round-trips against the real database, driven through a
UnitOfWork (which owns the connection + commit).

Each test cleans up the rows it creates.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from backend.db import DatabasePool
from backend.domain import models as domain
from backend.infrastructure.unit_of_work import UnitOfWork


@pytest.fixture(scope="module")
def uow_factory():
  pool = DatabasePool()
  try:
    yield lambda: UnitOfWork(pool)
  finally:
    pool.close()


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
  def test_add_then_get(self, uow_factory):
    recipe = _recipe("repo-add-get")
    with uow_factory() as uow:
      uow.recipes.add(recipe)
    try:
      with uow_factory() as uow:
        loaded = uow.recipes.get(recipe.id)
      assert loaded is not None
      assert loaded.name == "repo-add-get"
      assert loaded.description == "round-trip"
      assert loaded.current_version.version_number == 1
      assert loaded.current_version.description == "Initial version"
      assert [i.name for i in loaded.current_version.ingredients] == ["flour"]
      assert [s.instruction for s in loaded.current_version.instructions] == ["Mix"]
    finally:
      with uow_factory() as uow:
        uow.recipes.delete(recipe.id)

  def test_save_adds_version_and_updates_scalars_atomically(self, uow_factory):
    recipe = _recipe("repo-save")
    with uow_factory() as uow:
      uow.recipes.add(recipe)
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
      with uow_factory() as uow:
        uow.recipes.save(recipe)

      with uow_factory() as uow:
        loaded = uow.recipes.get(recipe.id)
        assert loaded.name == "repo-save-renamed"
        assert loaded.category == "lean"
        assert loaded.current_version.version_number == 2
        assert [i.name for i in loaded.current_version.ingredients] == ["rye"]
        assert [v.version_number for v in uow.recipes.get_versions(recipe.id)] == [2, 1]

        v2 = uow.recipes.get_version(loaded.current_version.id)
        assert v2.change_summary == {"total_changes": 3}
    finally:
      with uow_factory() as uow:
        uow.recipes.delete(recipe.id)

  def test_get_missing_returns_none(self, uow_factory):
    with uow_factory() as uow:
      assert uow.recipes.get(uuid4()) is None

  def test_delete_absent_returns_false(self, uow_factory):
    with uow_factory() as uow:
      assert uow.recipes.delete(uuid4()) is False

  def test_list_search_and_category_filter(self, uow_factory):
    a = _recipe("repo-list-alpha", category="sourdough")
    b = _recipe("repo-list-beta", category="lean")
    with uow_factory() as uow:
      uow.recipes.add(a)
    with uow_factory() as uow:
      uow.recipes.add(b)
    try:
      with uow_factory() as uow:
        names = {s.name for s in uow.recipes.list(search="repo-list")}
        assert {"repo-list-alpha", "repo-list-beta"} <= names

        lean = [s.name for s in uow.recipes.list(search="repo-list", category="lean")]
        assert lean == ["repo-list-beta"]

        summary = next(s for s in uow.recipes.list(search="repo-list-alpha"))
        assert summary.ingredient_count == 1
        assert summary.step_count == 1
    finally:
      with uow_factory() as uow:
        uow.recipes.delete(a.id)
        uow.recipes.delete(b.id)


class TestTransactionBoundary:
  def test_rollback_on_exception_discards_the_write(self, uow_factory):
    recipe = _recipe("repo-rollback")

    with pytest.raises(RuntimeError):
      with uow_factory() as uow:
        uow.recipes.add(recipe)
        raise RuntimeError("boom after add")

    with uow_factory() as uow:
      assert uow.recipes.get(recipe.id) is None
