"""The recipe routes carry no try/except — the app's exception handlers turn
application errors into HTTP responses. These pin that mapping."""

from uuid import uuid4

from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.exceptions import DatabaseError
from backend.infrastructure.recipe_repository import RecipeRepository
from backend.service import app

client = TestClient(app)

MISSING = "00000000-0000-0000-0000-000000000000"

_FULL_BODY = {
  "name": "x",
  "ingredients": [{"name": "flour", "amount": 1, "unit": "grams", "type": "flour"}],
  "instructions": [{"order": 1, "instruction": "mix"}],
}


class TestNotFoundMapsTo404:
  def test_get_missing_recipe(self):
    assert client.get(f"/recipes/{MISSING}").status_code == 404

  def test_patch_missing_recipe(self):
    resp = client.patch(f"/recipes/{MISSING}", json=_FULL_BODY)
    assert resp.status_code == 404

  def test_delete_missing_recipe(self):
    assert client.delete(f"/recipes/{MISSING}").status_code == 404

  def test_add_version_to_missing_recipe(self):
    resp = client.post(f"/recipes/{MISSING}/versions", json=_FULL_BODY)
    assert resp.status_code == 404

  def test_diff_unknown_versions(self):
    resp = client.get(f"/recipes/{MISSING}/versions/{uuid4()}/diff/{uuid4()}")
    assert resp.status_code == 404


class TestDatabaseErrorMapsTo500:
  def test_create_surfaces_500_with_database_error_detail(self):
    with patch.object(RecipeRepository, "add", side_effect=DatabaseError("boom")):
      resp = client.post("/recipes/", json=_FULL_BODY)
    assert resp.status_code == 500
    assert "database error" in resp.json()["detail"].lower()
