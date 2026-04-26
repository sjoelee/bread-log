"""
Tests for GET /recipes/ list endpoint — sorting and ingredient filtering.
Each test class manages its own recipes and deletes them on teardown.
"""

import pytest
from fastapi.testclient import TestClient
from backend.service import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_recipe(name: str, ingredients: list, category: str = "sourdough") -> dict:
  """Create a recipe via the API and return the full response body."""
  payload = {
    "name": name,
    "description": f"Test recipe: {name}",
    "category": category,
    "ingredients": ingredients,
    "instructions": [
      {"order": 1, "instruction": "Mix ingredients"},
      {"order": 2, "instruction": "Bake until done"},
    ],
  }
  response = client.post("/recipes/", json=payload)
  assert response.status_code == 201, (
    f"Failed to create recipe '{name}': {response.text}"
  )
  return response.json()


def _delete_recipe(recipe_id: str) -> None:
  client.delete(f"/recipes/{recipe_id}")


def _flour(name: str, amount: int = 1000) -> dict:
  return {"name": name, "amount": amount, "unit": "grams", "type": "flour", "notes": ""}


def _liquid(name: str, amount: int = 750) -> dict:
  return {
    "name": name,
    "amount": amount,
    "unit": "grams",
    "type": "liquid",
    "notes": "",
  }


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


class TestRecipeListSorting:
  """Verify sort_by and sort_direction params on GET /recipes/"""

  @pytest.fixture(autouse=True)
  def recipes(self):
    # Create in reverse alpha order so insertion order ≠ sorted order
    self.recipe_z = _make_recipe("Zebra Rye", [_flour("rye flour"), _liquid("water")])
    self.recipe_a = _make_recipe(
      "Apple Focaccia", [_flour("bread flour"), _liquid("water")]
    )
    self.recipe_m = _make_recipe(
      "Miso Loaf", [_flour("whole wheat flour"), _liquid("water")]
    )
    self.ids = [self.recipe_z["id"], self.recipe_a["id"], self.recipe_m["id"]]
    yield
    for rid in self.ids:
      _delete_recipe(rid)

  def _list(self, **params) -> list:
    response = client.get("/recipes/", params=params)
    assert response.status_code == 200
    return response.json()

  def test_sort_by_name_ascending(self):
    # GIVEN: three recipes with distinct names
    # WHEN: listing sorted by name A→Z
    results = self._list(sort_by="name", sort_direction="asc")
    names = [r["name"] for r in results]

    # THEN: our recipes appear in alphabetical order relative to each other
    a_pos = names.index("Apple Focaccia")
    m_pos = names.index("Miso Loaf")
    z_pos = names.index("Zebra Rye")
    assert a_pos < m_pos < z_pos

  def test_sort_by_name_descending(self):
    # GIVEN: three recipes with distinct names
    # WHEN: listing sorted by name Z→A
    results = self._list(sort_by="name", sort_direction="desc")
    names = [r["name"] for r in results]

    # THEN: order is reversed
    a_pos = names.index("Apple Focaccia")
    m_pos = names.index("Miso Loaf")
    z_pos = names.index("Zebra Rye")
    assert z_pos < m_pos < a_pos

  def test_sort_by_created_at_descending(self):
    # GIVEN: three recipes created sequentially
    # WHEN: listing newest first
    results = self._list(sort_by="created_at", sort_direction="desc")
    ids = [r["id"] for r in results]

    # THEN: Miso Loaf (created last) appears before Apple Focaccia, which appears before Zebra Rye
    assert ids.index(self.recipe_m["id"]) < ids.index(self.recipe_a["id"])
    assert ids.index(self.recipe_a["id"]) < ids.index(self.recipe_z["id"])

  def test_sort_by_created_at_ascending(self):
    # GIVEN: three recipes created sequentially
    # WHEN: listing oldest first
    results = self._list(sort_by="created_at", sort_direction="asc")
    ids = [r["id"] for r in results]

    # THEN: Zebra Rye (created first) appears before Apple Focaccia, which appears before Miso Loaf
    assert ids.index(self.recipe_z["id"]) < ids.index(self.recipe_a["id"])
    assert ids.index(self.recipe_a["id"]) < ids.index(self.recipe_m["id"])

  def test_default_sort_is_created_at_descending(self):
    # GIVEN: three recipes created sequentially
    # WHEN: listing with no sort params
    results = self._list()
    ids = [r["id"] for r in results]

    # THEN: default behaves like created_at desc — newest first
    assert ids.index(self.recipe_m["id"]) < ids.index(self.recipe_z["id"])


# ---------------------------------------------------------------------------
# Ingredient filtering
# ---------------------------------------------------------------------------


class TestRecipeListIngredientFilter:
  """Verify ingredient= param on GET /recipes/"""

  @pytest.fixture(autouse=True)
  def recipes(self):
    self.bread_flour_recipe = _make_recipe(
      "Classic Sourdough",
      [_flour("bread flour"), _liquid("water")],
    )
    self.rye_recipe = _make_recipe(
      "Dark Rye Loaf",
      [_flour("rye flour"), _liquid("water")],
    )
    self.mixed_recipe = _make_recipe(
      "Country Blend",
      [_flour("bread flour", 800), _flour("whole wheat flour", 200), _liquid("water")],
    )
    self.ids = [
      self.bread_flour_recipe["id"],
      self.rye_recipe["id"],
      self.mixed_recipe["id"],
    ]
    yield
    for rid in self.ids:
      _delete_recipe(rid)

  def _ids_for(self, **params) -> set:
    response = client.get("/recipes/", params=params)
    assert response.status_code == 200
    return {r["id"] for r in response.json()}

  def test_filter_returns_recipes_with_ingredient(self):
    # GIVEN: recipes with bread flour and without
    # WHEN: filtering by ingredient=bread flour
    ids = self._ids_for(ingredient="bread flour")

    # THEN: both bread-flour recipes are returned, rye-only is excluded
    assert self.bread_flour_recipe["id"] in ids
    assert self.mixed_recipe["id"] in ids
    assert self.rye_recipe["id"] not in ids

  def test_filter_excludes_recipes_without_ingredient(self):
    # GIVEN: three recipes
    # WHEN: filtering by rye flour
    ids = self._ids_for(ingredient="rye flour")

    # THEN: only the rye recipe matches
    assert self.rye_recipe["id"] in ids
    assert self.bread_flour_recipe["id"] not in ids
    assert self.mixed_recipe["id"] not in ids

  def test_filter_is_case_insensitive(self):
    # GIVEN: ingredient stored as "bread flour" (lowercase)
    # WHEN: filtering with mixed case
    ids_upper = self._ids_for(ingredient="Bread Flour")
    ids_lower = self._ids_for(ingredient="bread flour")

    # THEN: both return the same set
    assert ids_upper == ids_lower
    assert self.bread_flour_recipe["id"] in ids_upper

  def test_filter_supports_partial_match(self):
    # GIVEN: recipes with "bread flour", "rye flour", "whole wheat flour"
    # WHEN: filtering by partial term "flour"
    ids = self._ids_for(ingredient="flour")

    # THEN: all three recipes match (all have some kind of flour)
    assert self.bread_flour_recipe["id"] in ids
    assert self.rye_recipe["id"] in ids
    assert self.mixed_recipe["id"] in ids

  def test_filter_no_match_returns_empty_subset(self):
    # GIVEN: none of the test recipes contain spelt
    # WHEN: filtering by ingredient=spelt
    ids = self._ids_for(ingredient="spelt")

    # THEN: none of our test recipes are returned
    assert self.bread_flour_recipe["id"] not in ids
    assert self.rye_recipe["id"] not in ids
    assert self.mixed_recipe["id"] not in ids

  def test_filter_combined_with_search(self):
    # GIVEN: two bread-flour recipes, one named "Classic Sourdough"
    # WHEN: filtering by ingredient=bread flour AND search=classic
    ids = self._ids_for(ingredient="bread flour", search="classic")

    # THEN: only the matching recipe is returned
    assert self.bread_flour_recipe["id"] in ids
    assert self.mixed_recipe["id"] not in ids
    assert self.rye_recipe["id"] not in ids
