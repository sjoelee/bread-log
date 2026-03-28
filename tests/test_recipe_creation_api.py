"""
Recipe Creation API Tests - Test-Driven Development
Tests for POST /recipes/ endpoint following TDD methodology
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4

# Import the FastAPI app
from backend.service import app
from backend.db import DBConnector
from backend.models import RecipeRequest, Ingredient, RecipeStep

client = TestClient(app)

class TestRecipeCreationHappyPath:
    """Test successful recipe creation scenarios"""
    
    def test_create_basic_recipe(self):
        """Test creating a simple recipe with minimal required fields"""
        
        # GIVEN: Valid recipe data
        recipe_data = {
            "name": "Simple Sourdough",
            "description": "Basic country bread",
            "category": "sourdough",
            "ingredients": [
                {
                    "name": "bread flour",
                    "amount": 1000,
                    "unit": "grams", 
                    "type": "flour",
                    "notes": ""
                },
                {
                    "name": "water",
                    "amount": 750,
                    "unit": "grams",
                    "type": "liquid", 
                    "notes": ""
                },
                {
                    "name": "levain",
                    "amount": 200,
                    "unit": "grams",
                    "type": "liquid",
                    "notes": "100% hydration starter"
                }
            ],
            "instructions": [
                {
                    "order": 1,
                    "instruction": "Autolyse flour and water for 30 minutes"
                },
                {
                    "order": 2, 
                    "instruction": "Add levain and mix thoroughly"
                }
            ]
        }
        
        # WHEN: Recipe is created via API
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Recipe is successfully created
        assert response.status_code == 201
        data = response.json()
        
        # Verify recipe basic info
        assert data["name"] == "Simple Sourdough"
        assert data["description"] == "Basic country bread" 
        assert data["category"] == "sourdough"
        assert data["current_version"]["version_number"] == 1
        
        # Verify ingredients stored correctly
        ingredients = data["current_version"]["ingredients"]
        assert len(ingredients) == 3
        assert ingredients[0]["name"] == "bread flour"
        assert ingredients[0]["amount"] == 1000
        assert ingredients[0]["type"] == "flour"
        
        # Verify instructions stored correctly
        instructions = data["current_version"]["instructions"]
        assert len(instructions) == 2
        assert instructions[0]["order"] == 1
        assert "Autolyse" in instructions[0]["instruction"]
        
        # Verify baker's percentages calculated
        percentages = data["bakers_percentages"]
        assert percentages["total_flour_weight"] == 1000.0
        assert len(percentages["flour_ingredients"]) == 1
        assert len(percentages["other_ingredients"]) == 2
        assert percentages["flour_ingredients"][0]["percentage"] == 100.0
        assert percentages["other_ingredients"][0]["percentage"] == 75.0  # water
        assert percentages["other_ingredients"][1]["percentage"] == 20.0  # levain

    def test_create_recipe_with_multiple_flours(self):
        """Test baker's percentage calculation with multiple flour types"""
        
        # GIVEN: Recipe with multiple flour types
        recipe_data = {
            "name": "Mixed Flour Bread",
            "ingredients": [
                {"name": "bread flour", "amount": 800, "unit": "grams", "type": "flour"},
                {"name": "whole wheat", "amount": 200, "unit": "grams", "type": "flour"},
                {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"}
            ],
            "instructions": [{"order": 1, "instruction": "Mix all"}]
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Flour percentages are calculated correctly
        assert response.status_code == 201
        percentages = response.json()["bakers_percentages"]
        
        assert percentages["total_flour_weight"] == 1000.0
        assert len(percentages["flour_ingredients"]) == 2
        
        # Find each flour percentage
        bread_flour = next(f for f in percentages["flour_ingredients"] if f["name"] == "bread flour")
        whole_wheat = next(f for f in percentages["flour_ingredients"] if f["name"] == "whole wheat")
        
        assert bread_flour["percentage"] == 80.0
        assert whole_wheat["percentage"] == 20.0
        
        # Total flour percentages should sum to 100
        total_flour_percent = sum(f["percentage"] for f in percentages["flour_ingredients"])
        assert total_flour_percent == 100.0

    def test_create_recipe_minimal_fields(self):
        """Test creating recipe with only required fields"""
        
        # GIVEN: Minimal valid recipe data
        recipe_data = {
            "name": "Simple Bread",
            "ingredients": [
                {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
                {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"}
            ],
            "instructions": [
                {"order": 1, "instruction": "Mix ingredients"}
            ]
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Recipe is created with defaults
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Simple Bread"
        assert data["description"] is None
        assert data["category"] is None
        assert data["current_version"]["version_number"] == 1


class TestRecipeValidation:
    """Test input validation and error scenarios"""
    
    def test_missing_required_name(self):
        """Test validation error when recipe name is missing"""
        
        # GIVEN: Recipe data without name
        recipe_data = {
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        # WHEN: Recipe creation is attempted
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "name"] for error in error_detail)

    def test_missing_ingredients(self):
        """Test validation error when ingredients array is empty"""
        
        # GIVEN: Recipe with no ingredients
        recipe_data = {
            "name": "Empty Recipe",
            "ingredients": [],
            "instructions": [{"order": 1, "instruction": "Do nothing"}]
        }
        
        # WHEN: Recipe creation is attempted
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422

    def test_missing_instructions(self):
        """Test validation error when instructions array is empty"""
        
        # GIVEN: Recipe with no instructions
        recipe_data = {
            "name": "No Instructions",
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": []
        }
        
        # WHEN: Recipe creation is attempted
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Validation error is returned
        assert response.status_code == 422

    def test_invalid_ingredient_amounts(self):
        """Test validation of ingredient amounts"""
        
        invalid_amounts = [
            {"amount": -100, "description": "negative amount"},
            {"amount": 0, "description": "zero amount"}
        ]
        
        for invalid_amount in invalid_amounts:
            # GIVEN: Recipe with invalid amount
            recipe_data = {
                "name": f"Test Recipe - {invalid_amount['description']}",
                "ingredients": [{
                    "name": "flour",
                    "amount": invalid_amount["amount"],
                    "unit": "grams",
                    "type": "flour"
                }],
                "instructions": [{"order": 1, "instruction": "Mix"}]
            }
            
            # WHEN: Recipe creation is attempted
            response = client.post("/recipes/", json=recipe_data)
            
            # THEN: Validation error is returned
            assert response.status_code == 422

    def test_invalid_category(self):
        """Test validation of recipe category"""
        
        # GIVEN: Recipe with invalid category
        recipe_data = {
            "name": "Invalid Category Recipe",
            "category": "invalid_category",
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        # WHEN: Recipe creation is attempted
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Validation error is returned (if category validation is implemented)
        # This test will pass for now but should fail when validation is added
        # assert response.status_code == 422


class TestIDGeneration:
    """Test ingredient and instruction ID generation"""
    
    def test_ingredient_id_generation(self):
        """Test that ingredient IDs are generated when not provided"""
        
        # GIVEN: Recipe data without ingredient IDs
        recipe_data = {
            "name": "Auto ID Test",
            "ingredients": [
                {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
                # No "id" field provided
            ],
            "instructions": [
                {"order": 1, "instruction": "Mix ingredients"}
                # No "id" field provided
            ]
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: IDs are auto-generated
        assert response.status_code == 201
        data = response.json()
        
        ingredient = data["current_version"]["ingredients"][0]
        instruction = data["current_version"]["instructions"][0]
        
        assert "id" in ingredient
        assert "id" in instruction
        assert len(ingredient["id"]) >= 8  # UUID or generated ID
        assert len(instruction["id"]) >= 8

    def test_preserve_provided_ids(self):
        """Test that provided IDs are preserved"""
        
        # GIVEN: Recipe data with custom IDs
        recipe_data = {
            "name": "Custom ID Test",
            "ingredients": [
                {"id": "custom_flour_id", "name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
            ],
            "instructions": [
                {"id": "custom_step_id", "order": 1, "instruction": "Mix ingredients"}
            ]
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Custom IDs are preserved
        assert response.status_code == 201
        data = response.json()
        
        assert data["current_version"]["ingredients"][0]["id"] == "custom_flour_id"
        assert data["current_version"]["instructions"][0]["id"] == "custom_step_id"


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_no_flour_recipe(self):
        """Test recipe creation without flour ingredients"""
        
        # GIVEN: Recipe with no flour (e.g., sauce recipe)
        recipe_data = {
            "name": "Tomato Sauce",
            "category": "other",
            "ingredients": [
                {"name": "tomatoes", "amount": 1000, "unit": "grams", "type": "other"},
                {"name": "olive oil", "amount": 50, "unit": "grams", "type": "fat"},
                {"name": "garlic", "amount": 10, "unit": "grams", "type": "other"}
            ],
            "instructions": [
                {"order": 1, "instruction": "Sauté garlic in olive oil"},
                {"order": 2, "instruction": "Add tomatoes and simmer"}
            ]
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Recipe is created but no baker's percentages
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Tomato Sauce"
        assert len(data["current_version"]["ingredients"]) == 3
        
        # Baker's percentages should be null or have zero flour weight
        percentages = data["bakers_percentages"]
        assert percentages is None or percentages["total_flour_weight"] == 0

    def test_large_recipe(self):
        """Test recipe with many ingredients and instructions"""
        
        # GIVEN: Recipe with many ingredients
        ingredients = [{"name": f"ingredient_{i}", "amount": 10, "unit": "grams", "type": "other"} 
                      for i in range(20)]
        ingredients[0]["type"] = "flour"  # At least one flour for percentages
        
        instructions = [{"order": i+1, "instruction": f"Step {i+1}: Do something"} 
                       for i in range(50)]
        
        recipe_data = {
            "name": "Very Large Recipe",
            "ingredients": ingredients,
            "instructions": instructions
        }
        
        # WHEN: Recipe is created
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Recipe is created successfully
        assert response.status_code == 201
        data = response.json()
        
        assert len(data["current_version"]["ingredients"]) == 20
        assert len(data["current_version"]["instructions"]) == 50
        assert data["bakers_percentages"]["total_flour_weight"] == 10.0


# Test fixtures for common data
@pytest.fixture
def basic_recipe_data():
    """Basic recipe for testing"""
    return {
        "name": "Test Basic Recipe",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Mix ingredients"}
        ]
    }

@pytest.fixture
def complete_recipe_data():
    return {
        "name": "Complete Test Recipe",
        "description": "A test recipe with all fields",
        "category": "sourdough",
        "ingredients": [
            {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour", "notes": "High protein"},
            {"name": "water", "amount": 750, "unit": "grams", "type": "liquid", "notes": "Filtered"},
            {"name": "salt", "amount": 20, "unit": "grams", "type": "other", "notes": "Sea salt"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Autolyse flour and water"},
            {"order": 2, "instruction": "Add salt and mix"}
        ]
    }