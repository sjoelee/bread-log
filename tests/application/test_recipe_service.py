"""RecipeService against an in-memory repository — no database.

Walks the Draft/Ready lifecycle (spec 2.1 acceptance scenarios) through the
use cases.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from backend.application.recipe_service import RecipeService
from backend.domain import models as domain
from backend.exceptions import DraftUnchangedError, NoDraftError, NotFoundError
from tests.fakes import FakeRecipeRepository, FakeUnitOfWork

FIXED_NOW = datetime(2024, 5, 1, 12, 0, 0)

FLOUR = domain.Ingredient(name="bread flour", amount=1000, unit="grams", type="flour")
WATER = domain.Ingredient(name="water", amount=750, unit="grams", type="liquid")
MORE_WATER = domain.Ingredient(name="water", amount=800, unit="grams", type="liquid")
RYE = domain.Ingredient(name="rye", amount=100, unit="grams", type="flour")


def _service():
  repo = FakeRecipeRepository()
  return RecipeService(lambda: FakeUnitOfWork(repo), now=lambda: FIXED_NOW)


def _steps():
  return [
    domain.RecipeStep(order=1, instruction="Autolyse"),
    domain.RecipeStep(order=2, instruction="Mix"),
  ]


def _create(svc, name="Simple Sourdough", ingredients=None):
  return svc.create_recipe(
    name=name,
    description="Basic country bread",
    category="sourdough",
    ingredients=ingredients or [FLOUR, WATER],
    instructions=_steps(),
  )


def _save(svc, recipe, ingredients):
  """Save a Draft with new ingredients, keeping the recipe's current step ids."""
  source = recipe.draft or recipe.latest_ready
  return svc.save_draft(
    recipe.id, ingredients=ingredients, instructions=source.instructions
  )


class TestCreate:
  def test_new_recipe_is_a_draft_with_generated_step_ids(self):
    recipe = _create(_service())
    assert recipe.latest_ready is None
    assert recipe.draft.state == domain.DRAFT
    assert recipe.draft.version_number is None
    assert all(s.id for s in recipe.draft.instructions)
    assert recipe.created_at == FIXED_NOW

  def test_names_need_not_be_unique(self):
    svc = _service()
    a, b = _create(svc, name="Tangzhong"), _create(svc, name="Tangzhong")
    assert a.id != b.id
    assert len(svc.list_recipes(search="Tangzhong")) == 2


class TestSaveDraft:
  def test_saving_twice_keeps_one_draft_and_no_history(self):
    svc = _service()
    recipe = _create(svc)
    first = _save(svc, recipe, [FLOUR, MORE_WATER])
    second = _save(svc, first, [FLOUR, WATER, RYE])
    assert second.draft.id == recipe.draft.id
    assert [i.name for i in second.draft.ingredients] == ["bread flour", "water", "rye"]
    assert svc.get_recipe_versions(recipe.id) == []

  def test_missing_recipe_raises(self):
    with pytest.raises(NotFoundError):
      _service().save_draft(uuid4(), ingredients=[FLOUR], instructions=_steps())


class TestPromote:
  def test_promotes_draft_to_version_one_without_a_note(self):
    svc = _service()
    recipe = _create(svc)
    promoted = svc.promote(recipe.id)
    assert promoted.draft is None
    assert promoted.latest_ready.version_number == 1
    assert promoted.latest_ready.release_note is None
    assert [v.version_number for v in svc.get_recipe_versions(recipe.id)] == [1]

  def test_without_a_draft_is_rejected(self):
    svc = _service()
    recipe = _create(svc)
    svc.promote(recipe.id)
    with pytest.raises(NoDraftError):
      svc.promote(recipe.id)

  def test_unchanged_draft_is_rejected(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    _save(svc, v1, [FLOUR, WATER])
    with pytest.raises(DraftUnchangedError):
      svc.promote(v1.id)
    assert svc.get_recipe(v1.id).draft is not None

  def test_changed_draft_becomes_v2_and_v1_is_unchanged(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    _save(svc, v1, [FLOUR, MORE_WATER])
    v2 = svc.promote(v1.id, release_note="more water")
    assert v2.latest_ready.version_number == 2
    assert v2.latest_ready.release_note == "more water"
    assert v2.latest_ready.change_summary["ingredients"]["modified"] == 1
    history = svc.get_recipe_versions(v1.id)
    assert [v.version_number for v in history] == [2, 1]
    assert history[1].ingredients == [FLOUR, WATER]

  def test_missing_recipe_raises(self):
    with pytest.raises(NotFoundError):
      _service().promote(uuid4())


class TestUpdateDetails:
  def test_takes_effect_at_once_and_leaves_versions_alone(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    with_draft = _save(svc, v1, [FLOUR, MORE_WATER])
    updated = svc.update_details(
      v1.id, name="Country Loaf", description="cold water", category="lean"
    )
    assert (updated.name, updated.description, updated.category) == (
      "Country Loaf",
      "cold water",
      "lean",
    )
    assert updated.draft == with_draft.draft
    assert updated.latest_ready == v1.latest_ready

  def test_missing_recipe_raises(self):
    with pytest.raises(NotFoundError):
      _service().update_details(uuid4(), name="x")


class TestDiscardDraft:
  def test_keeps_ready_versions(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    _save(svc, v1, [FLOUR, MORE_WATER])
    remaining = svc.discard_draft(v1.id)
    assert remaining is not None
    assert remaining.draft is None
    assert [v.version_number for v in svc.get_recipe_versions(v1.id)] == [1]

  def test_deletes_a_recipe_with_no_ready_version(self):
    svc = _service()
    recipe = _create(svc)
    assert svc.discard_draft(recipe.id) is None
    with pytest.raises(NotFoundError):
      svc.get_recipe(recipe.id)

  def test_without_a_draft_is_rejected(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    with pytest.raises(NoDraftError):
      svc.discard_draft(v1.id)


class TestDelete:
  def test_removes_draft_and_all_ready_versions(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    _save(svc, v1, [FLOUR, MORE_WATER])
    svc.promote(v1.id)
    _save(svc, svc.get_recipe(v1.id), [FLOUR, WATER, RYE])
    assert svc.delete_recipe(v1.id) is True
    with pytest.raises(NotFoundError):
      svc.get_recipe(v1.id)
    with pytest.raises(NotFoundError):
      svc.get_recipe_versions(v1.id)

  def test_missing_recipe_raises(self):
    with pytest.raises(NotFoundError):
      _service().delete_recipe(uuid4())


class TestQueries:
  def test_get_missing_raises(self):
    with pytest.raises(NotFoundError, match="Recipe not found"):
      _service().get_recipe(uuid4())

  def test_history_of_missing_recipe_raises(self):
    with pytest.raises(NotFoundError):
      _service().get_recipe_versions(uuid4())


class TestFake:
  def test_stored_ready_versions_are_frozen_like_the_database(self):
    repo = FakeRecipeRepository()
    svc = RecipeService(lambda: FakeUnitOfWork(repo), now=lambda: FIXED_NOW)
    v1 = svc.promote(_create(svc).id)
    tampered = svc.get_recipe(v1.id)
    tampered.latest_ready.release_note = "tampered"
    repo.save(tampered)
    assert repo.get(v1.id).latest_ready.release_note is None
    assert svc.get_recipe_versions(v1.id)[0].release_note is None

  def test_diff_draft_against_ready(self):
    svc = _service()
    v1 = svc.promote(_create(svc).id)
    with_draft = _save(svc, v1, [FLOUR, MORE_WATER])
    diff = svc.get_recipe_version_diff(v1.id, v1.latest_ready.id, with_draft.draft.id)
    assert diff["from_version"] == "1"
    assert diff["to_version"] == "draft"
    assert len(diff["ingredient_changes"]["modified"]) == 1

  def test_list_state_filter_and_ingredient_match(self):
    """Spec scenario 13: v1 has rye, the Draft removed it."""
    svc = _service()
    v1 = svc.promote(_create(svc, ingredients=[FLOUR, WATER, RYE]).id)
    _save(svc, v1, [FLOUR, WATER])
    draft_only = _create(svc, name="Draft only")

    def names(**kw):
      return sorted(s.name for s in svc.list_recipes(**kw))

    assert names(ingredient="rye") == ["Simple Sourdough"]
    assert names(ingredient="rye", state="draft") == []
    assert names(ingredient="rye", state="ready") == ["Simple Sourdough"]
    assert names(state="ready") == ["Simple Sourdough"]
    assert names(state="draft") == ["Draft only", "Simple Sourdough"]
    summary = next(s for s in svc.list_recipes() if s.id == draft_only.id)
    assert summary.latest_ready is None
    assert summary.draft.version_number is None
