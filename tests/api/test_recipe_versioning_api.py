"""
Draft/Ready lifecycle over HTTP (spec 2.1 acceptance scenarios), and
GET /recipes/{recipe_id}/versions/{v1_id}/diff/{v2_id}.

Diff tests create a recipe, promote it to v1, save a changed Draft and promote
it to v2, then call the diff endpoint. Failures print the raw diff.
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


def save_draft(recipe_id, ingredients=None, instructions=None, status=200):
  payload = {
    "ingredients": ingredients if ingredients is not None else BASE_INGREDIENTS,
    "instructions": instructions if instructions is not None else BASE_INSTRUCTIONS,
  }
  resp = client.put(f"/recipes/{recipe_id}/draft", json=payload)
  assert resp.status_code == status, resp.text
  return resp.json()


def promote(recipe_id, release_note=None, status=200):
  resp = client.post(
    f"/recipes/{recipe_id}/promote", json={"release_note": release_note}
  )
  assert resp.status_code == status, resp.text
  return resp.json()


def patch_recipe(recipe_id, ingredients=None, instructions=None):
  """Save a changed Draft and promote it: the new latest Ready version."""
  save_draft(recipe_id, ingredients, instructions)
  return promote(recipe_id)


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

  def _create(name=None, *, ready=True):
    r = create_recipe(name)
    created_ids.append(r["id"])
    return promote(r["id"]) if ready else r

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


class TestDraftReadyLifecycle:
  def test_new_recipe_is_draft_only_and_not_listed_as_ready(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup(ready=False)
    assert recipe["latest_ready"] is None
    assert recipe["draft"]["state"] == "draft"
    assert recipe["draft"]["version_number"] is None
    ready_ids = [r["id"] for r in client.get("/recipes/?state=ready&limit=500").json()]
    assert recipe["id"] not in ready_ids

  def test_saving_twice_keeps_one_draft_and_empty_history(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup(ready=False)
    save_draft(recipe["id"])
    saved = save_draft(recipe["id"], ingredients=BASE_INGREDIENTS[:2])
    assert saved["draft"]["id"] == recipe["draft"]["id"]
    assert len(saved["draft"]["ingredients"]) == 2
    assert get_versions(recipe["id"]) == []

  def test_promote_without_note_gives_v1(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup(ready=False)
    v1 = promote(recipe["id"])
    assert v1["draft"] is None
    assert v1["latest_ready"]["id"] == recipe["draft"]["id"]
    assert v1["latest_ready"]["version_number"] == 1
    assert v1["latest_ready"]["release_note"] is None
    assert [v["version_number"] for v in get_versions(recipe["id"])] == [1]

  def test_promote_without_a_draft_is_422(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    promote(recipe["id"], status=422)
    assert [v["version_number"] for v in get_versions(recipe["id"])] == [1]

  def test_promote_unchanged_draft_is_422(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    v1 = recipe["latest_ready"]
    save_draft(
      recipe["id"], ingredients=v1["ingredients"], instructions=v1["instructions"]
    )
    promote(recipe["id"], status=422)

  def test_promote_changed_draft_gives_v2_and_keeps_v1(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    v1 = recipe["latest_ready"]
    more_water = [
      {**i, "amount": 800} if i["name"] == "water" else i for i in BASE_INGREDIENTS
    ]
    save_draft(recipe["id"], ingredients=more_water, instructions=v1["instructions"])
    v2 = promote(recipe["id"], release_note="more water")["latest_ready"]
    assert v2["version_number"] == 2
    assert v2["release_note"] == "more water"
    assert v2["change_summary"]["ingredients"]["modified"] == 1
    history = get_versions(recipe["id"])
    assert [v["version_number"] for v in history] == [2, 1]
    assert history[1]["ingredients"] == v1["ingredients"]

  def test_details_change_at_once_and_versions_stay(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    with_draft = save_draft(recipe["id"], ingredients=BASE_INGREDIENTS[:2])
    resp = client.patch(
      f"/recipes/{recipe['id']}",
      json={"name": "Renamed", "description": "cold water", "category": "lean"},
    )
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert (updated["name"], updated["description"], updated["category"]) == (
      "Renamed",
      "cold water",
      "lean",
    )
    assert updated["draft"] == with_draft["draft"]
    assert updated["latest_ready"] == recipe["latest_ready"]

  def test_patch_rejects_content(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    resp = client.patch(
      f"/recipes/{recipe['id']}",
      json={"name": "x", "ingredients": BASE_INGREDIENTS},
    )
    # Unknown fields are ignored; content is unchanged.
    assert resp.status_code == 200
    assert resp.json()["latest_ready"] == recipe["latest_ready"]
    assert resp.json()["draft"] is None

  def test_discard_keeps_ready_versions(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    save_draft(recipe["id"], ingredients=BASE_INGREDIENTS[:2])
    resp = client.delete(f"/recipes/{recipe['id']}/draft")
    assert resp.status_code == 200, resp.text
    assert resp.json()["draft"] is None
    assert [v["version_number"] for v in get_versions(recipe["id"])] == [1]

  def test_discard_of_draft_only_recipe_deletes_it(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup(ready=False)
    resp = client.delete(f"/recipes/{recipe['id']}/draft")
    assert resp.status_code == 204
    assert client.get(f"/recipes/{recipe['id']}").status_code == 404

  def test_discard_without_a_draft_is_422(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    assert client.delete(f"/recipes/{recipe['id']}/draft").status_code == 422

  def test_delete_removes_everything(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    patch_recipe(recipe["id"], ingredients=BASE_INGREDIENTS[:2])
    save_draft(recipe["id"], ingredients=BASE_INGREDIENTS[:3])
    assert client.delete(f"/recipes/{recipe['id']}").status_code == 204
    assert client.get(f"/recipes/{recipe['id']}").status_code == 404
    assert client.get(f"/recipes/{recipe['id']}/versions").status_code == 404

  def test_names_need_not_be_unique(self, recipe_with_cleanup):
    name = f"Tangzhong {uuid4().hex[:6]}"
    a = recipe_with_cleanup(name, ready=False)
    b = recipe_with_cleanup(name, ready=False)
    assert a["id"] != b["id"]
    assert len(client.get(f"/recipes/?search={name}").json()) == 2

  def test_diff_draft_against_ready(self, recipe_with_cleanup):
    recipe = recipe_with_cleanup()
    v1 = recipe["latest_ready"]
    with_draft = save_draft(
      recipe["id"], ingredients=BASE_INGREDIENTS[:2], instructions=v1["instructions"]
    )
    diff = get_diff(recipe["id"], v1["id"], with_draft["draft"]["id"]).json()
    assert diff["from_version"] == "1"
    assert diff["to_version"] == "draft"
    assert sorted(i["name"] for i in diff["ingredient_changes"]["removed"]) == [
      "levain",
      "salt",
    ]

  def test_list_state_filter(self, recipe_with_cleanup):
    """Spec scenario 13: v1 contains rye, the Draft removed it."""
    tag = uuid4().hex[:6]
    rye = {"name": f"rye-{tag}", "amount": 100, "unit": "grams", "type": "flour"}
    recipe = recipe_with_cleanup(f"Rye {tag}", ready=False)
    save_draft(recipe["id"], ingredients=BASE_INGREDIENTS + [rye])
    promote(recipe["id"])
    save_draft(recipe["id"], ingredients=BASE_INGREDIENTS)

    def ids(**params):
      resp = client.get("/recipes/", params={"ingredient": rye["name"], **params})
      assert resp.status_code == 200, resp.text
      return [r["id"] for r in resp.json()]

    assert ids() == [recipe["id"]]
    assert ids(state="draft") == []
    assert ids(state="ready") == [recipe["id"]]

    row = client.get("/recipes/", params={"search": f"Rye {tag}"}).json()[0]
    assert row["latest_ready"]["version_number"] == 1
    assert row["latest_ready"]["ingredient_count"] == 5
    assert row["draft"]["version_number"] is None
    assert row["draft"]["ingredient_count"] == 4

  def test_invalid_state_filter_is_422(self):
    assert client.get("/recipes/?state=bogus").status_code == 422
