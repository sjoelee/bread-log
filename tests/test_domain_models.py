"""Stage 2 — unit tests for the domain dataclasses (no DB, no framework).

Covers Recipe.create / add_version / current_version and value-object immutability.
This is scaffolding: nothing in the app wires through these yet.
"""

import dataclasses
from datetime import datetime, timedelta

import pytest

from backend.domain.models import Ingredient, Recipe, RecipeStep

NOW = datetime(2024, 5, 1, 12, 0, 0)


def _ingredients():
  return [
    Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
    Ingredient(name="water", amount=750, unit="grams", type="liquid"),
  ]


def _steps():
  return [
    RecipeStep(order=1, instruction="Mix"),
    RecipeStep(order=2, instruction="Bake"),
  ]


class TestRecipeCreate:
  def test_creates_initial_version_one(self):
    recipe = Recipe.create(
      name="Country Sourdough",
      ingredients=_ingredients(),
      instructions=_steps(),
      now=NOW,
    )
    assert recipe.current_version.version_number == 1
    assert recipe.current_version.recipe_id == recipe.id
    assert recipe.created_at == recipe.updated_at == NOW


class TestAddVersion:
  def test_increments_number_and_replaces_current(self):
    recipe = Recipe.create(
      name="x", ingredients=_ingredients(), instructions=_steps(), now=NOW
    )
    later = NOW + timedelta(days=1)

    new_ingredients = _ingredients() + [
      Ingredient(name="salt", amount=20, unit="grams", type="other")
    ]
    v2 = recipe.add_version(
      ingredients=new_ingredients, instructions=_steps(), now=later
    )

    assert v2.version_number == 2
    assert recipe.current_version is v2
    assert recipe.updated_at == later

  def test_default_description_is_autosave_label(self):
    recipe = Recipe.create(
      name="x", ingredients=_ingredients(), instructions=_steps(), now=NOW
    )
    v2 = recipe.add_version(ingredients=_ingredients(), instructions=_steps(), now=NOW)
    assert v2.description == "Auto-save v2"


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
