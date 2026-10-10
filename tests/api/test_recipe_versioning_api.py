"""
Tests for GET /recipes/{recipe_id}/versions/{v1_id}/diff/{v2_id}

Each test creates a recipe, modifies it via PATCH (creating a new version),
then calls the diff endpoint and asserts the returned JSON. Failures print
the raw diff so you can see exactly what changed.
"""

import json
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from backend.service import app

client = TestClient(app)


BASE_INGREDIENTS = [
  {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},
  {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"},
  {"name": "levain", "amount": 200, "unit": "grams", "type": "preferment"},
  {"name": "salt", "amount": 20, "unit": "grams", "type": "other"},
]

BASE_INSTRUCTIONS = [
  {"order": 1, "instruction": "Autolyse flour and water for 30 minutes"},
  {"order": 2, "instruction": "Add levain and mix thoroughly"},
  {"order": 3, "instruction": "Bulk ferment for 3 hours"},
]


def create_recipe(name=None):
  name = name or f"Test Recipe {uuid4().hex[:6]}"
  resp = client.post(
    "/recipes/",
    json={
      "name": name,
      "category": "sourdough",
      "ingredients": BASE_INGREDIENTS,
      "instructions": BASE_INSTRUCTIONS,
    },
  )
  assert resp.status_code == 201, resp.text
  return resp.json()


def patch_recipe(recipe_id, ingredients=None, instructions=None, name=None):
  """PATCH requires the full RecipeRequest body; defaults to base values when not overridden."""
  payload = {
    "name": name or "Test Recipe",
    "category": "sourdough",
    "ingredients": ingredients if ingredients is not None else BASE_INGREDIENTS,
    "instructions": instructions if instructions is not None else BASE_INSTRUCTIONS,
  }
  resp = client.patch(f"/recipes/{recipe_id}", json=payload)
  assert resp.status_code == 200, resp.text
  return resp.json()


def get_versions(recipe_id):
  resp = client.get(f"/recipes/{recipe_id}/versions")
  assert resp.status_code == 200, resp.text
  return resp.json()


def get_diff(recipe_id, v1_id, v2_id):
  resp = client.get(f"/recipes/{recipe_id}/versions/{v1_id}/diff/{v2_id}")
  return resp


@pytest.fixture
def recipe_with_cleanup():
  """Create a recipe and delete it after the test."""
  created_ids = []

  def _create(name=None):
    r = create_recipe(name)
    created_ids.append(r["id"])
    return r

  yield _create

  for rid in created_ids:
    client.delete(f"/recipes/{rid}")


class TestVersionDiffEndpoint:
  def test_ingredient_added(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    versions_before = get_versions(recipe_id)
    v1_id = versions_before[0]["id"]

    new_ingredients = BASE_INGREDIENTS + [
      {"name": "olive oil", "amount": 30, "unit": "grams", "type": "fat"}
    ]
    patch_recipe(recipe_id, ingredients=new_ingredients)

    versions_after = get_versions(recipe_id)
    v2_id = versions_after[0]["id"]

    resp = get_diff(recipe_id, v1_id, v2_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    added_names = [i["name"] for i in diff["ingredient_changes"]["added"]]
    assert "olive oil" in added_names, (
      f"Expected 'olive oil' in added. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_ingredient_removed(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    # Remove salt
    without_salt = [i for i in BASE_INGREDIENTS if i["name"] != "salt"]
    patch_recipe(recipe_id, ingredients=without_salt)

    v2_id = get_versions(recipe_id)[0]["id"]

    resp = get_diff(recipe_id, v1_id, v2_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    removed_names = [i["name"] for i in diff["ingredient_changes"]["removed"]]
    assert "salt" in removed_names, (
      f"Expected 'salt' in removed. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_ingredient_modified(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    # Change water amount 750 → 800
    modified = [
      {**i, "amount": 800} if i["name"] == "water" else i for i in BASE_INGREDIENTS
    ]
    patch_recipe(recipe_id, ingredients=modified)

    v2_id = get_versions(recipe_id)[0]["id"]

    resp = get_diff(recipe_id, v1_id, v2_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    modified_entries = diff["ingredient_changes"]["modified"]
    water_change = next(
      (m for m in modified_entries if m["old"]["name"] == "water"), None
    )
    assert water_change is not None, (
      f"Expected water in modified. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )
    assert water_change["old"]["amount"] == 750, (
      f"Expected old amount 750. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )
    assert water_change["new"]["amount"] == 800, (
      f"Expected new amount 800. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_instruction_added(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    new_instructions = BASE_INSTRUCTIONS + [
      {"order": 4, "instruction": "Final shape and cold proof overnight"}
    ]
    patch_recipe(recipe_id, instructions=new_instructions)

    v2_id = get_versions(recipe_id)[0]["id"]

    resp = get_diff(recipe_id, v1_id, v2_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    added_steps = [s["instruction"] for s in diff["step_changes"]["added"]]
    assert any("cold proof" in s for s in added_steps), (
      f"Expected new step in added. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_no_changes(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    resp = get_diff(recipe_id, v1_id, v1_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    ic = diff["ingredient_changes"]
    sc = diff["step_changes"]
    assert ic["added"] == [] and ic["removed"] == [] and ic["modified"] == [], (
      f"Expected no ingredient changes. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )
    assert sc["added"] == [] and sc["removed"] == [] and sc["modified"] == [], (
      f"Expected no step changes. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_multi_change(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    # Add olive oil AND modify water amount in one PATCH
    multi_changed = [
      {**i, "amount": 800} if i["name"] == "water" else i for i in BASE_INGREDIENTS
    ] + [{"name": "olive oil", "amount": 30, "unit": "grams", "type": "fat"}]
    patch_recipe(recipe_id, ingredients=multi_changed)

    v2_id = get_versions(recipe_id)[0]["id"]

    resp = get_diff(recipe_id, v1_id, v2_id)
    assert resp.status_code == 200, resp.text
    diff = resp.json()

    added_names = [i["name"] for i in diff["ingredient_changes"]["added"]]
    modified_names = [m["old"]["name"] for m in diff["ingredient_changes"]["modified"]]
    assert "olive oil" in added_names, (
      f"Expected olive oil added. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )
    assert "water" in modified_names, (
      f"Expected water modified. Diff:\n{json.dumps(diff, indent=2, default=str)}"
    )

  def test_wrong_recipe_id_returns_404(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    other_recipe = recipe_with_cleanup()
    wrong_recipe_id = other_recipe["id"]

    resp = get_diff(wrong_recipe_id, v1_id, v1_id)
    assert resp.status_code == 404, (
      f"Expected 404 for mismatched recipe_id. Got {resp.status_code}: {resp.text}"
    )

  def test_reversed_diff_flips_added_removed(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    recipe_id = recipe["id"]
    v1_id = get_versions(recipe_id)[0]["id"]

    new_ingredients = BASE_INGREDIENTS + [
      {"name": "honey", "amount": 15, "unit": "grams", "type": "other"}
    ]
    patch_recipe(recipe_id, ingredients=new_ingredients)
    v2_id = get_versions(recipe_id)[0]["id"]

    forward = get_diff(recipe_id, v1_id, v2_id).json()
    reverse = get_diff(recipe_id, v2_id, v1_id).json()

    forward_added = [i["name"] for i in forward["ingredient_changes"]["added"]]
    reverse_removed = [i["name"] for i in reverse["ingredient_changes"]["removed"]]
    assert "honey" in forward_added, (
      f"Expected honey added (forward). Diff:\n{json.dumps(forward, indent=2, default=str)}"
    )
    assert "honey" in reverse_removed, (
      f"Expected honey removed (reverse). Diff:\n{json.dumps(reverse, indent=2, default=str)}"
    )
