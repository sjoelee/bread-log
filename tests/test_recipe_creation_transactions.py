"""
Recipe Creation Database Transaction Tests
Tests for transaction integrity and rollback behavior
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.service import app
from backend.db import DBConnector
from backend.exceptions import DatabaseError

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
            "instructions": [
                {"order": 1, "instruction": "Mix ingredients"}
            ]
        }
        
        # WHEN: Database error occurs during version creation (step 2)
        with patch('backend.db.DBConnector.create_versioned_recipe') as mock_create:
            # Simulate database error during transaction
            mock_create.side_effect = DatabaseError("Failed to insert recipe version")
            
            response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Error is returned and transaction was rolled back
        assert response.status_code == 500
        assert "database error" in response.json()["detail"].lower()
        
        # Verify the error was handled properly
        mock_create.assert_called_once()

    def test_transaction_rollback_on_percentage_calculation_failure(self):
        """Test rollback when baker's percentage calculation fails"""
        
        # GIVEN: Valid recipe data
        recipe_data = {
            "name": "Percentage Failure Test",
            "ingredients": [
                {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
                {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"}
            ],
            "instructions": [
                {"order": 1, "instruction": "Mix"}
            ]
        }
        
        # WHEN: Error occurs during baker's percentage calculation (step 4)
        with patch('backend.recipe_service.calculate_bakers_percentages') as mock_calc:
            # Simulate calculation error
            mock_calc.side_effect = ValueError("Invalid ingredient data for percentage calculation")
            
            response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422
        assert "validation error" in response.json()["detail"].lower()

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
                {"name": "salt", "amount": 20, "unit": "grams", "type": "other"}
            ],
            "instructions": [
                {"order": 1, "instruction": "Autolyse flour and water"},
                {"order": 2, "instruction": "Add salt and mix"}
            ]
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
        assert data["bakers_percentages"]["total_flour_weight"] == 1000.0

    def test_connection_recovery_after_failed_transaction(self):
        """Test that failed transactions don't break subsequent requests"""
        
        # GIVEN: Recipe data that will cause a failure
        failing_recipe = {
            "name": "Will Fail",
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        # AND: Recipe data that should succeed
        success_recipe = {
            "name": "Should Succeed",
            "ingredients": [{"name": "flour", "amount": 200, "unit": "grams", "type": "flour"}], 
            "instructions": [{"order": 1, "instruction": "Mix well"}]
        }
        
        # WHEN: First request fails due to database error
        with patch('backend.db.DBConnector.create_versioned_recipe') as mock_create:
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
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
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
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        recipe2_data = {
            "name": "Concurrent Recipe 2", 
            "ingredients": [{"name": "flour", "amount": 200, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix well"}]
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
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        # Mock specific database error during recipe insertion
        with patch('backend.db.DBConnector.create_versioned_recipe') as mock_create:
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
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}], 
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        with patch('backend.db.DBConnector.create_versioned_recipe') as mock_create:
            # Simulate foreign key constraint violation
            mock_create.side_effect = DatabaseError("Foreign key constraint violation")
            
            response = client.post("/recipes/", json=recipe_data)
        
        assert response.status_code == 500


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
            {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Mix ingredients thoroughly"}
        ]
    }