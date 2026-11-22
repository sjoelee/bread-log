"""RecipeRepository round-trips against the real database, driven through a
UnitOfWork (which owns the connection + commit).

Each test cleans up the rows it creates.
"""

import os
from datetime import datetime, timedelta
from uuid import uuid4

import psycopg
import pytest

from backend.infrastructure.pool import DatabasePool
from backend.domain import models as domain
from backend.infrastructure.unit_of_work import UnitOfWork

NOW = datetime(2024, 5, 1, 12, 0, 0)
LATER = NOW + timedelta(hours=1)
RYE = domain.Ingredient(name="rye", amount=100, unit="grams", type="flour")


@pytest.fixture(scope="module")
def uow_factory():
  pool = DatabasePool()
  try:
    yield lambda: UnitOfWork(pool)
  finally:
    pool.close()


@pytest.fixture
def stored(uow_factory):
  """Add recipes through the repository and delete them after the test."""
  ids = []

  def add(recipe):
    with uow_factory() as uow:
      uow.recipes.add(recipe)
    ids.append(recipe.id)
    return recipe

  yield add
  with uow_factory() as uow:
    for recipe_id in ids:
      uow.recipes.delete(recipe_id)


def _rows(sql, params):
  """Read raw rows, bypassing the repository."""
  with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    return conn.execute(sql, params).fetchall()


def _recipe(name: str, *, category="sourdough", ingredients=None):
  return domain.Recipe.create(
    name=name,
    ingredients=ingredients
    or [domain.Ingredient(name="flour", amount=1000, unit="grams", type="flour")],
    instructions=[domain.RecipeStep(order=1, instruction="Mix", id=str(uuid4()))],
    now=NOW,
    description="round-trip",
    category=category,
  )


def _change_content(recipe, ingredients):
  recipe.save_draft(
    ingredients=ingredients,
    instructions=(recipe.draft or recipe.latest_ready).instructions,
    now=LATER,
  )


class TestRoundTrip:
  def test_add_then_get_a_draft_only_recipe(self, uow_factory, stored):
    recipe = stored(_recipe("repo-add-get"))
    with uow_factory() as uow:
      loaded = uow.recipes.get(recipe.id)
    assert loaded is not None
    assert (loaded.name, loaded.description) == ("repo-add-get", "round-trip")
    assert loaded.latest_ready is None
    assert loaded.draft.id == recipe.draft.id
    assert loaded.draft.state == domain.DRAFT
    assert loaded.draft.version_number is None
    assert [i.name for i in loaded.draft.ingredients] == ["flour"]
    assert _rows(
      "SELECT current_version_id FROM recipes WHERE id = %s", [recipe.id]
    ) == [(None,)]

  def test_promotion_turns_the_draft_row_ready_in_place(self, uow_factory, stored):
    recipe = stored(_recipe("repo-promote"))
    draft_id = recipe.draft.id
    recipe.promote(release_note="first bake", now=LATER)
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      loaded = uow.recipes.get(recipe.id)
      history = uow.recipes.get_versions(recipe.id)
    assert loaded.draft is None
    assert loaded.latest_ready.id == draft_id
    assert loaded.latest_ready.version_number == 1
    assert loaded.latest_ready.release_note == "first bake"
    assert loaded.latest_ready.created_at == LATER
    assert [v.id for v in history] == [draft_id]
    assert _rows(
      "SELECT r.current_version_id, v.state FROM recipes r "
      "JOIN recipe_versions v ON v.id = r.current_version_id WHERE r.id = %s",
      [recipe.id],
    ) == [(draft_id, "ready")]

  def test_draft_and_ready_load_together_and_history_is_ready_only(
    self, uow_factory, stored
  ):
    recipe = stored(_recipe("repo-both"))
    recipe.promote(release_note=None, now=NOW)
    _change_content(recipe, [RYE])
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      loaded = uow.recipes.get(recipe.id)
      history = uow.recipes.get_versions(recipe.id)
      draft = uow.recipes.get_version(recipe.draft.id)
    assert loaded.latest_ready.version_number == 1
    assert [i.name for i in loaded.latest_ready.ingredients] == ["flour"]
    assert [i.name for i in loaded.draft.ingredients] == ["rye"]
    assert [v.version_number for v in history] == [1]
    assert draft.state == domain.DRAFT

  def test_second_promotion_stores_change_summary(self, uow_factory, stored):
    recipe = stored(_recipe("repo-v2"))
    recipe.promote(release_note=None, now=NOW)
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    _change_content(recipe, [RYE])
    recipe.promote(release_note="rye", now=LATER)
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      history = uow.recipes.get_versions(recipe.id)
    assert [v.version_number for v in history] == [2, 1]
    assert history[0].change_summary["total_changes"] == 2

  def test_saving_without_a_draft_removes_the_draft_row(self, uow_factory, stored):
    recipe = stored(_recipe("repo-discard"))
    recipe.promote(release_note=None, now=NOW)
    _change_content(recipe, [RYE])
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    recipe.discard_draft()
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      loaded = uow.recipes.get(recipe.id)
    assert loaded.draft is None
    assert loaded.latest_ready.version_number == 1
    assert _rows(
      "SELECT state FROM recipe_versions WHERE recipe_id = %s", [recipe.id]
    ) == [("ready",)]

  def test_ready_rows_are_never_overwritten(self, uow_factory, stored):
    recipe = stored(_recipe("repo-frozen"))
    recipe.promote(release_note="original", now=NOW)
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    recipe.latest_ready.release_note = "tampered"
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      assert uow.recipes.get(recipe.id).latest_ready.release_note == "original"

  def test_save_updates_recipe_fields(self, uow_factory, stored):
    recipe = stored(_recipe("repo-details"))
    recipe.update_details(
      name="repo-details-renamed", description="notes", category="lean", now=LATER
    )
    with uow_factory() as uow:
      uow.recipes.save(recipe)
    with uow_factory() as uow:
      loaded = uow.recipes.get(recipe.id)
    assert (loaded.name, loaded.description, loaded.category) == (
      "repo-details-renamed",
      "notes",
      "lean",
    )

  def test_get_missing_returns_none(self, uow_factory):
    with uow_factory() as uow:
      assert uow.recipes.get(uuid4()) is None

  def test_delete_absent_returns_false(self, uow_factory):
    with uow_factory() as uow:
      assert uow.recipes.delete(uuid4()) is False

  def test_list_search_and_category_filter(self, uow_factory, stored):
    stored(_recipe("repo-list-alpha", category="sourdough"))
    stored(_recipe("repo-list-beta", category="lean"))
    with uow_factory() as uow:
      names = {s.name for s in uow.recipes.list(search="repo-list")}
      lean = [s.name for s in uow.recipes.list(search="repo-list", category="lean")]
      summary = next(s for s in uow.recipes.list(search="repo-list-alpha"))
    assert {"repo-list-alpha", "repo-list-beta"} <= names
    assert lean == ["repo-list-beta"]
    assert summary.latest_ready is None
    assert summary.draft.ingredient_count == 1
    assert summary.draft.step_count == 1

  def test_list_state_filter_matches_the_right_part(self, uow_factory, stored):
    """Spec scenario 13: v1 contains rye, the Draft removed it."""
    flour = domain.Ingredient(name="flour", amount=900, unit="grams", type="flour")
    recipe = _recipe("repo-state-rye", ingredients=[flour, RYE])
    recipe.promote(release_note=None, now=NOW)
    _change_content(recipe, [flour])
    stored(recipe)
    stored(_recipe("repo-state-draft-only"))

    def names(**kw):
      with uow_factory() as uow:
        return sorted(s.name for s in uow.recipes.list(search="repo-state", **kw))

    assert names(ingredient="rye") == ["repo-state-rye"]
    assert names(ingredient="rye", state="draft") == []
    assert names(ingredient="rye", state="ready") == ["repo-state-rye"]
    assert names(state="ready") == ["repo-state-rye"]
    assert names(state="draft") == ["repo-state-draft-only", "repo-state-rye"]
    with uow_factory() as uow:
      summary = uow.recipes.list(search="repo-state-rye")[0]
    assert summary.latest_ready.version_number == 1
    assert summary.latest_ready.ingredient_count == 2
    assert summary.draft.ingredient_count == 1


class TestTransactionBoundary:
  def test_rollback_on_exception_discards_the_write(self, uow_factory):
    recipe = _recipe("repo-rollback")

    with pytest.raises(RuntimeError):
      with uow_factory() as uow:
        uow.recipes.add(recipe)
        raise RuntimeError("boom after add")

    with uow_factory() as uow:
      assert uow.recipes.get(recipe.id) is None
