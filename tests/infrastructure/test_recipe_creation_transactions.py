"""
Recipe transaction integrity tests.

The use case runs inside one UnitOfWork transaction, so a failure anywhere in
the use case must leave the database untouched.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.service import app
from backend.exceptions import DatabaseError
from backend.infrastructure.recipe_repository import RecipeRepository

client = TestClient(app)


class TestRecipeTransactionIntegrity:
  """Test database transaction atomicity for recipe creation"""

  def test_transaction_rollback_on_version_creation_failure(self):
    """Test rollback when recipe version creation fails"""

    # GIVEN: Valid recipe data
    recipe_data = {
      "name": "Transaction Test Recipe",
      "description": "Testing transaction rollback",
      "ingredients": [
        {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix ingredients"}],
    }

    # WHEN: Database error occurs during version creation (step 2)
    with patch(
      "backend.infrastructure.recipe_repository.RecipeRepository.add"
    ) as mock_create:
      # Simulate database error during transaction
      mock_create.side_effect = DatabaseError("Failed to insert recipe version")

      response = client.post("/recipes/", json=recipe_data)

    # THEN: Error is returned and transaction was rolled back
    assert response.status_code == 500
    assert "database error" in response.json()["detail"].lower()

    # Verify the error was handled properly
    mock_create.assert_called_once()

  def test_successful_transaction_with_all_steps(self):
    """Test that successful recipe creation completes all transaction steps"""

    # GIVEN: Valid complete recipe data
    recipe_data = {
      "name": "Complete Transaction Test",
      "description": "Testing successful transaction",
      "category": "sourdough",
      "ingredients": [
        {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},
        {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"},
        {"name": "salt", "amount": 20, "unit": "grams", "type": "other"},
      ],
      "instructions": [
        {"order": 1, "instruction": "Autolyse flour and water"},
        {"order": 2, "instruction": "Add salt and mix"},
      ],
    }

    # WHEN: Recipe is created successfully
    response = client.post("/recipes/", json=recipe_data)

    # THEN: All transaction steps completed successfully
    assert response.status_code == 201
    data = response.json()

    # Verify all data was created
    assert data["name"] == "Complete Transaction Test"
    assert data["current_version"]["version_number"] == 1
    assert len(data["current_version"]["ingredients"]) == 3
    assert len(data["current_version"]["instructions"]) == 2

  def test_connection_recovery_after_failed_transaction(self):
    """Test that failed transactions don't break subsequent requests"""

    # GIVEN: Recipe data that will cause a failure
    failing_recipe = {
      "name": "Will Fail",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
    }

    # AND: Recipe data that should succeed
    success_recipe = {
      "name": "Should Succeed",
      "ingredients": [
        {"name": "flour", "amount": 200, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix well"}],
    }

    # WHEN: First request fails due to database error
    with patch(
      "backend.infrastructure.recipe_repository.RecipeRepository.add"
    ) as mock_create:
      mock_create.side_effect = DatabaseError("Simulated database failure")

      failing_response = client.post("/recipes/", json=failing_recipe)

    # THEN: First request fails
    assert failing_response.status_code == 500

    # WHEN: Second request is made after the failure
    success_response = client.post("/recipes/", json=success_recipe)

    # THEN: Second request should succeed (connection pool recovered)
    assert success_response.status_code == 201
    assert success_response.json()["name"] == "Should Succeed"


class TestDatabaseConnectionHandling:
  """Test database connection and pool behavior during transactions"""

  def test_connection_pool_usage_during_transaction(self):
    """Test that connections are properly acquired and released - simpler functional test"""

    # GIVEN: Valid recipe data
    recipe_data = {
      "name": "Connection Pool Test",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
    }

    # WHEN: Recipe is created (functional test - no mocking)
    response = client.post("/recipes/", json=recipe_data)

    # THEN: Connection pool handled the transaction successfully
    assert response.status_code == 201
    assert response.json()["name"] == "Connection Pool Test"

    # Verify the recipe exists and can be retrieved (another connection from pool)
    recipe_id = response.json()["id"]
    get_response = client.get(f"/recipes/{recipe_id}")
    assert get_response.status_code == 200

  def test_transaction_isolation_with_concurrent_requests(self):
    """Test that concurrent recipe creations don't interfere with each other"""

    # This test would require more complex setup with actual database
    # For now, we'll test the concept with mocks

    # GIVEN: Two different recipe requests
    recipe1_data = {
      "name": "Concurrent Recipe 1",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
    }

    recipe2_data = {
      "name": "Concurrent Recipe 2",
      "ingredients": [
        {"name": "flour", "amount": 200, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix well"}],
    }

    # WHEN: Recipes are created (simulating concurrent requests)
    response1 = client.post("/recipes/", json=recipe1_data)
    response2 = client.post("/recipes/", json=recipe2_data)

    # THEN: Both should succeed independently
    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["name"] == "Concurrent Recipe 1"
    assert response2.json()["name"] == "Concurrent Recipe 2"

    # AND: Each should have unique IDs
    assert response1.json()["id"] != response2.json()["id"]


class TestSpecificTransactionSteps:
  """Test individual steps of the recipe creation transaction"""

  def test_step1_recipe_creation_failure(self):
    """Test failure during step 1 - recipe table insertion"""

    recipe_data = {
      "name": "Step 1 Failure Test",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
    }

    # Mock specific database error during recipe insertion
    with patch(
      "backend.infrastructure.recipe_repository.RecipeRepository.add"
    ) as mock_create:
      mock_create.side_effect = DatabaseError("Failed to insert into recipes table")

      response = client.post("/recipes/", json=recipe_data)

    assert response.status_code == 500
    assert "database error" in response.json()["detail"].lower()

  def test_foreign_key_constraint_handling(self):
    """Test that foreign key constraint violations are handled properly"""

    # This would test if current_version_id properly references recipe_versions
    # In a real scenario, this might happen if there's a race condition

    recipe_data = {
      "name": "FK Constraint Test",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
    }

    with patch(
      "backend.infrastructure.recipe_repository.RecipeRepository.add"
    ) as mock_create:
      # Simulate foreign key constraint violation
      mock_create.side_effect = DatabaseError("Foreign key constraint violation")

      response = client.post("/recipes/", json=recipe_data)

    assert response.status_code == 500


class TestUseCaseAtomicity:
  """A failure partway through a use case rolls back the whole thing —
  against the real database, not a mock."""

  BASE = {
    "name": "Atomicity Base",
    "category": "sourdough",
    "ingredients": [
      {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"}
    ],
    "instructions": [{"order": 1, "instruction": "Mix"}],
  }

  def _create(self):
    resp = client.post("/recipes/", json={**self.BASE, "name": f"Atomicity {id(self)}"})
    assert resp.status_code == 201, resp.text
    return resp.json()

  def test_update_write_is_rolled_back_when_a_later_step_fails(self):
    created = self._create()
    recipe_id = created["id"]
    try:
      v2_body = {
        **self.BASE,
        "name": "Renamed v2",
        "ingredients": [
          {"name": "rye", "amount": 800, "unit": "grams", "type": "flour"}
        ],
        "instructions": [{"order": 1, "instruction": "Fold"}],
      }

      # save() runs for real (INSERT version + UPDATE recipe), then blows up
      # before the use case returns. The UnitOfWork must roll both statements back.
      real_save = RecipeRepository.save

      def save_then_fail(self, recipe):
        real_save(self, recipe)
        raise DatabaseError("failure after the write")

      with patch.object(RecipeRepository, "save", save_then_fail):
        resp = client.patch(f"/recipes/{recipe_id}", json=v2_body)
      assert resp.status_code == 500

      # Nothing from the failed update survived.
      got = client.get(f"/recipes/{recipe_id}").json()
      assert got["name"] == created["name"]
      assert got["current_version"]["version_number"] == 1
      assert [i["name"] for i in got["current_version"]["ingredients"]] == [
        "bread flour"
      ]

      versions = client.get(f"/recipes/{recipe_id}/versions").json()
      assert [v["version_number"] for v in versions] == [1]
    finally:
      client.delete(f"/recipes/{recipe_id}")

  def test_create_write_is_rolled_back_on_failure(self):
    real_add = RecipeRepository.add

    def add_then_fail(self, recipe):
      real_add(self, recipe)
      raise DatabaseError("failure after insert")

    with patch.object(RecipeRepository, "add", add_then_fail):
      resp = client.post("/recipes/", json={**self.BASE, "name": "Should Not Persist"})
    assert resp.status_code == 500

    listed = client.get("/recipes/?search=Should Not Persist").json()
    assert listed == []


# Test fixtures for transaction testing
@pytest.fixture
def valid_recipe_data():
  """Standard valid recipe data for transaction tests"""
  return {
    "name": "Transaction Test Recipe",
    "description": "For testing database transactions",
    "category": "lean",
    "ingredients": [
      {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
      {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
    ],
    "instructions": [{"order": 1, "instruction": "Mix ingredients thoroughly"}],
  }
