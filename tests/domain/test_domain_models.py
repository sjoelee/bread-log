"""Unit tests for the domain dataclasses (no DB, no framework).

Covers the Recipe aggregate's Draft/Ready lifecycle and value-object immutability.
"""

import dataclasses
from datetime import datetime, timedelta

import pytest

from backend.domain.models import DRAFT, READY, Ingredient, Recipe, RecipeStep
from backend.exceptions import DraftUnchangedError, NoDraftError

NOW = datetime(2024, 5, 1, 12, 0, 0)
LATER = NOW + timedelta(days=1)


def _ingredients():
  return [
    Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
    Ingredient(name="water", amount=750, unit="grams", type="liquid"),
  ]


def _steps():
  return [
    RecipeStep(order=1, instruction="Mix", id="s1"),
    RecipeStep(order=2, instruction="Bake", id="s2"),
  ]


def _new_recipe():
  return Recipe.create(
    name="Country Sourdough",
    ingredients=_ingredients(),
    instructions=_steps(),
    now=NOW,
  )


def _promoted_recipe():
  recipe = _new_recipe()
  recipe.promote(release_note=None, now=NOW)
  return recipe


def _more_water():
  return [
    Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
    Ingredient(name="water", amount=800, unit="grams", type="liquid"),
  ]


class TestCreate:
  def test_starts_as_a_draft_with_no_ready_version(self):
    recipe = _new_recipe()
    assert recipe.latest_ready is None
    assert recipe.draft is not None
    assert recipe.draft.state == DRAFT
    assert recipe.draft.version_number is None
    assert recipe.draft.recipe_id == recipe.id
    assert recipe.created_at == recipe.updated_at == NOW

  def test_a_recipe_with_neither_part_cannot_exist(self):
    with pytest.raises(ValueError):
      Recipe(id=_new_recipe().id, name="x", created_at=NOW, updated_at=NOW)


class TestSaveDraft:
  def test_replaces_content_in_place(self):
    recipe = _new_recipe()
    draft_id = recipe.draft.id
    recipe.save_draft(ingredients=_more_water(), instructions=_steps(), now=LATER)
    assert recipe.draft.id == draft_id
    assert recipe.draft.ingredients == _more_water()
    assert recipe.draft.version_number is None
    assert recipe.updated_at == LATER

  def test_creates_a_draft_when_there_is_none(self):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=_more_water(), instructions=_steps(), now=LATER)
    assert recipe.draft is not None
    assert recipe.draft.id != recipe.latest_ready.id
    assert recipe.draft.created_at == LATER
    assert recipe.latest_ready.version_number == 1


class TestPromote:
  def test_first_promotion_is_version_one(self):
    recipe = _new_recipe()
    draft_id = recipe.draft.id
    v1 = recipe.promote(release_note=None, now=LATER)
    assert v1.state == READY
    assert v1.version_number == 1
    assert v1.id == draft_id
    assert v1.created_at == LATER
    assert v1.release_note is None
    assert v1.change_summary is None
    assert recipe.latest_ready is v1
    assert recipe.draft is None

  def test_next_promotion_increments_and_summarizes_changes(self):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=_more_water(), instructions=_steps(), now=LATER)
    v2 = recipe.promote(release_note="more water", now=LATER)
    assert v2.version_number == 2
    assert v2.release_note == "more water"
    assert v2.change_summary["ingredients"]["modified"] == 1
    assert v2.change_summary["total_changes"] == 1

  def test_rejected_without_a_draft(self):
    recipe = _promoted_recipe()
    with pytest.raises(NoDraftError):
      recipe.promote(release_note=None, now=LATER)
    assert recipe.latest_ready.version_number == 1

  def test_rejected_when_draft_equals_latest_ready(self):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=_ingredients(), instructions=_steps(), now=LATER)
    with pytest.raises(DraftUnchangedError):
      recipe.promote(release_note=None, now=LATER)
    assert recipe.draft is not None
    assert recipe.latest_ready.version_number == 1

  @pytest.mark.parametrize(
    "draft_ingredients",
    [
      # ingredients reordered
      [
        Ingredient(name="water", amount=750, unit="grams", type="liquid"),
        Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
      ],
      # name capitalization changed
      [
        Ingredient(name="Bread Flour", amount=1000, unit="grams", type="flour"),
        Ingredient(name="water", amount=750, unit="grams", type="liquid"),
      ],
    ],
    ids=["reordered", "renamed-case"],
  )
  def test_any_ingredient_difference_counts_as_a_change(self, draft_ingredients):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=draft_ingredients, instructions=_steps(), now=LATER)
    assert recipe.promote(release_note=None, now=LATER).version_number == 2

  def test_removing_a_duplicate_named_ingredient_counts_as_a_change(self):
    flour = Ingredient(name="flour", amount=500, unit="grams", type="flour")
    extra = Ingredient(name="flour", amount=100, unit="grams", type="flour")
    recipe = Recipe.create(
      name="x", ingredients=[flour, extra], instructions=_steps(), now=NOW
    )
    recipe.promote(release_note=None, now=NOW)
    recipe.save_draft(ingredients=[extra], instructions=_steps(), now=LATER)
    assert recipe.promote(release_note=None, now=LATER).version_number == 2

  def test_new_step_ids_with_the_same_text_are_not_a_change(self):
    recipe = _promoted_recipe()
    same_text = [
      RecipeStep(order=1, instruction="Mix", id="other-1"),
      RecipeStep(order=2, instruction="Bake", id="other-2"),
    ]
    recipe.save_draft(ingredients=_ingredients(), instructions=same_text, now=LATER)
    with pytest.raises(DraftUnchangedError):
      recipe.promote(release_note=None, now=LATER)

  def test_reordering_steps_counts_as_a_change(self):
    recipe = _promoted_recipe()
    swapped = [
      RecipeStep(order=2, instruction="Mix", id="s1"),
      RecipeStep(order=1, instruction="Bake", id="s2"),
    ]
    recipe.save_draft(ingredients=_ingredients(), instructions=swapped, now=LATER)
    assert recipe.promote(release_note=None, now=LATER).version_number == 2


class TestDiscardDraft:
  def test_keeps_ready_versions(self):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=_more_water(), instructions=_steps(), now=LATER)
    assert recipe.discard_draft() is False
    assert recipe.draft is None
    assert recipe.latest_ready.version_number == 1

  def test_reports_an_empty_recipe_when_there_is_no_ready_version(self):
    assert _new_recipe().discard_draft() is True

  def test_rejected_without_a_draft(self):
    with pytest.raises(NoDraftError):
      _promoted_recipe().discard_draft()


class TestUpdateDetails:
  def test_changes_recipe_fields_and_leaves_versions_alone(self):
    recipe = _promoted_recipe()
    recipe.save_draft(ingredients=_more_water(), instructions=_steps(), now=NOW)
    ready, draft = recipe.latest_ready, recipe.draft
    recipe.update_details(
      name="Country Loaf", description="use cold water", category="lean", now=LATER
    )
    assert (recipe.name, recipe.description, recipe.category) == (
      "Country Loaf",
      "use cold water",
      "lean",
    )
    assert recipe.latest_ready is ready
    assert recipe.draft is draft
    assert recipe.updated_at == LATER


class TestIngredient:
  def test_type_is_optional(self):
    ing = Ingredient(name="mystery powder", amount=5, unit="grams")
    assert ing.type is None

  def test_is_immutable(self):
    ing = Ingredient(name="flour", amount=1, unit="grams", type="flour")
    with pytest.raises(dataclasses.FrozenInstanceError):
      ing.amount = 2

  def test_step_is_immutable(self):
    step = RecipeStep(order=1, instruction="Mix")
    with pytest.raises(dataclasses.FrozenInstanceError):
      step.order = 5
