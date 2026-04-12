"""
Tests for recipe versioning functionality
"""

from datetime import datetime
from uuid import uuid4


class TestRecipeVersionCreation:
  """Test cases for recipe version creation logic"""

  def test_create_initial_recipe_version(self, base_recipe):
    """Test creating initial recipe version v1.0"""
    # Given: A new recipe
    recipe_id = base_recipe["id"]

    # When: Creating the first version
    version = create_recipe_version(
      recipe_id=recipe_id,
      ingredients=base_recipe["ingredients"],
      instructions=base_recipe["instructions"],
      description="Initial version",
    )

    # Then: Version should be v1.0
    assert version["version_major"] == 1
    assert version["version_minor"] == 0
    assert version["recipe_id"] == recipe_id
    assert version["description"] == "Initial version"
    assert len(version["ingredients"]) == 4
    assert len(version["instructions"]) == 4

  def test_auto_minor_version_bump_on_ingredient_change(
    self, recipe_version_v1, modified_ingredients
  ):
    """Test auto-save as v1.1 when editing ingredient amount"""
    # Given: Existing recipe v1.0
    existing_version = recipe_version_v1

    # When: Changing water amount from 750g to 800g
    new_version = create_recipe_version(
      recipe_id=existing_version["recipe_id"],
      ingredients=modified_ingredients,
      instructions=existing_version["instructions"],
      previous_version=existing_version,
    )

    # Then: Version should auto-bump to v1.1
    assert new_version["version_major"] == 1
    assert new_version["version_minor"] == 1
    assert new_version["recipe_id"] == existing_version["recipe_id"]

    # And: Water amount should be updated
    water_ingredient = next(
      ing for ing in new_version["ingredients"] if ing["name"] == "water"
    )
    assert water_ingredient["amount"] == 800

  def test_auto_minor_version_bump_on_ingredient_addition(
    self, recipe_version_v1, modified_ingredients
  ):
    """Test auto-save as v1.2 when adding new ingredient"""
    # Given: Recipe v1.1 (simulated)
    v1_1 = {**recipe_version_v1, "version_minor": 1}

    # When: Adding olive oil ingredient
    new_version = create_recipe_version(
      recipe_id=v1_1["recipe_id"],
      ingredients=modified_ingredients,
      instructions=v1_1["instructions"],
      previous_version=v1_1,
    )

    # Then: Version should auto-bump to v1.2
    assert new_version["version_major"] == 1
    assert new_version["version_minor"] == 2

    # And: Should have 5 ingredients (added olive oil)
    assert len(new_version["ingredients"]) == 5
    olive_oil = next(
      ing for ing in new_version["ingredients"] if ing["name"] == "olive oil"
    )
    assert olive_oil["amount"] == 50

  def test_manual_major_version_bump(self, recipe_version_v1):
    """Test manual 'Save New Version' creates v2.0"""
    # Given: Recipe v1.3 (simulated with some changes)
    v1_3 = {**recipe_version_v1, "version_minor": 3}

    # When: Manually saving new major version
    new_version = create_recipe_version(
      recipe_id=v1_3["recipe_id"],
      ingredients=v1_3["ingredients"],
      instructions=v1_3["instructions"],
      previous_version=v1_3,
      description="Increased hydration",
      force_major=True,
    )

    # Then: Version should jump to v2.0
    assert new_version["version_major"] == 2
    assert new_version["version_minor"] == 0
    assert new_version["description"] == "Increased hydration"

  def test_step_reordering_creates_new_version(
    self, recipe_version_v1, sample_instructions
  ):
    """Test that reordering steps creates v2.1"""
    # Given: Recipe v2.0 (simulated)
    v2_0 = {**recipe_version_v1, "version_major": 2, "version_minor": 0}

    # When: Reordering steps (move step 4 to position 2)
    reordered_instructions = sample_instructions.copy()
    step_to_move = reordered_instructions.pop(3)  # Remove step 4
    step_to_move["order"] = 2
    reordered_instructions.insert(1, step_to_move)  # Insert at position 2

    # Renumber remaining steps
    for i, step in enumerate(reordered_instructions):
      step["order"] = i + 1

    new_version = create_recipe_version(
      recipe_id=v2_0["recipe_id"],
      ingredients=v2_0["ingredients"],
      instructions=reordered_instructions,
      previous_version=v2_0,
    )

    # Then: Version should auto-bump to v2.1
    assert new_version["version_major"] == 2
    assert new_version["version_minor"] == 1

    # And: Step order should be changed
    assert (
      new_version["instructions"][1]["instruction"] == "Pre-shape and rest 30 minutes"
    )

  def test_step_content_modification_creates_new_version(
    self, recipe_version_v1, modified_instructions
  ):
    """Test editing step content creates new version"""
    # Given: Existing recipe version
    existing_version = recipe_version_v1

    # When: Modifying bulk ferment instruction
    new_version = create_recipe_version(
      recipe_id=existing_version["recipe_id"],
      ingredients=existing_version["ingredients"],
      instructions=modified_instructions,
      previous_version=existing_version,
    )

    # Then: New version should be created
    assert new_version["version_minor"] == existing_version["version_minor"] + 1

    # And: Bulk ferment step should be updated
    bulk_step = next(
      step
      for step in new_version["instructions"]
      if "bulk ferment" in step["instruction"].lower()
    )
    assert "4 hours at 78°F" in bulk_step["instruction"]


def create_recipe_version(
  recipe_id: str,
  ingredients: list,
  instructions: list,
  previous_version=None,
  description=None,
  force_major=False,
):
  """
  Mock function for creating recipe versions
  This will be replaced with actual implementation
  """
  if previous_version is None:
    # First version
    return {
      "id": str(uuid4()),
      "recipe_id": recipe_id,
      "version_major": 1,
      "version_minor": 0,
      "description": description or "Initial version",
      "ingredients": ingredients,
      "instructions": instructions,
      "created_at": datetime.now(),
      "change_summary": {},
    }

  # Determine version numbers
  if force_major:
    major = previous_version["version_major"] + 1
    minor = 0
  else:
    major = previous_version["version_major"]
    minor = previous_version["version_minor"] + 1

  return {
    "id": str(uuid4()),
    "recipe_id": recipe_id,
    "version_major": major,
    "version_minor": minor,
    "description": description or f"Auto-save v{major}.{minor}",
    "ingredients": ingredients,
    "instructions": instructions,
    "created_at": datetime.now(),
    "change_summary": {},  # This would contain diff information
  }
