"""Stage 3 — round-trip tests for backend.api.mappers (no DB, no framework wiring).

Nothing in the request path calls these yet (Stage 6 wires them). The value is
pinning DTO <-> domain equivalence so the later wiring can't drift.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from backend.api import mappers, schemas
from backend.domain import models as domain

NOW = datetime(2024, 5, 1, 12, 0, 0)


def _dto_ingredient(**kw):
  base = dict(name="bread flour", amount=1000.0, unit="grams", type="flour")
  base.update(kw)
  return schemas.Ingredient(**base)


def _domain_recipe():
  return domain.Recipe.create(
    name="Country Sourdough",
    ingredients=[
      domain.Ingredient(name="bread flour", amount=1000, unit="grams", type="flour"),
      domain.Ingredient(name="water", amount=750, unit="grams", type="liquid"),
    ],
    instructions=[domain.RecipeStep(order=1, instruction="Mix")],
    now=NOW,
    description="weeknight loaf",
    category="sourdough",
  )


class TestDtoToDomain:
  def test_ingredient_round_trips(self):
    dto = _dto_ingredient(notes="high protein")
    back = mappers.ingredient_to_dto(mappers.ingredient_to_domain(dto))
    assert back == dto

  def test_step_round_trips(self):
    dto = schemas.RecipeStep(id=str(uuid4()), order=2, instruction="Bulk ferment")
    back = mappers.step_to_dto(mappers.step_to_domain(dto))
    assert back == dto

  def test_lists(self):
    ings = [_dto_ingredient(), _dto_ingredient(name="salt", amount=20, type="other")]
    assert len(mappers.ingredients_to_domain(ings)) == 2
    assert mappers.ingredients_to_domain(ings)[1].type == "other"


class TestDomainToDto:
  def test_new_recipe_has_only_a_draft(self):
    recipe = _domain_recipe()
    dto = mappers.recipe_to_dto(recipe)

    assert isinstance(dto, schemas.Recipe)
    assert dto.name == "Country Sourdough"
    assert dto.category == "sourdough"
    assert dto.latest_ready is None
    assert dto.draft.id == recipe.draft.id
    assert dto.draft.state == "draft"
    assert dto.draft.version_number is None
    assert [i.name for i in dto.draft.ingredients] == ["bread flour", "water"]

  def test_promoted_recipe_with_a_new_draft_has_both_parts(self):
    recipe = _domain_recipe()
    recipe.promote(release_note="first", now=NOW)
    recipe.save_draft(
      ingredients=[
        domain.Ingredient(name="rye", amount=200, unit="grams", type="flour")
      ],
      instructions=[domain.RecipeStep(order=1, instruction="Mix")],
      now=NOW,
    )
    dto = mappers.recipe_to_dto(recipe)
    assert dto.latest_ready.version_number == 1
    assert dto.latest_ready.release_note == "first"
    assert [i.name for i in dto.draft.ingredients] == ["rye"]

  def test_none_type_ingredient_cannot_be_serialized(self):
    # documents the known gap: domain allows type=None, the DTO does not
    unclassified = domain.Ingredient(name="mystery", amount=5, unit="grams")
    with pytest.raises(Exception):
      mappers.ingredient_to_dto(unclassified)
