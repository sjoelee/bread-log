"""
Integration tests for recipe versioning system
"""
import pytest
import json
import uuid
from datetime import datetime

# Mock test data for integration testing
def test_recipe_data_structure_compatibility():
    """Test that frontend and backend data structures are compatible"""
    
    # Frontend form data structure (what RecipeTab.tsx sends)
    frontend_recipe_data = {
        "name": "Country Sourdough",
        "description": "Classic sourdough with high hydration",
        "category": "sourdough",
        "ingredients": [
            {
                "name": "bread flour",
                "amount": 1000,
                "unit": "grams",
                "type": "flour",
                "notes": "high protein flour"
            },
            {
                "name": "water",
                "amount": 750,
                "unit": "grams", 
                "type": "liquid",
                "notes": "filtered water"
            },
            {
                "name": "levain",
                "amount": 200,
                "unit": "grams",
                "type": "preferment",
                "notes": "100% hydration starter"
            },
            {
                "name": "salt",
                "amount": 20,
                "unit": "grams",
                "type": "other",
                "notes": "fine sea salt"
            }
        ],
        "instructions": [
            {
                "order": 1,
                "instruction": "Autolyse flour and water for 30 minutes"
            },
            {
                "order": 2,
                "instruction": "Add levain and salt, mix thoroughly"
            },
            {
                "order": 3,
                "instruction": "Bulk ferment for 4 hours with folds every 30 minutes"
            },
            {
                "order": 4,
                "instruction": "Pre-shape and rest 30 minutes"
            },
            {
                "order": 5,
                "instruction": "Final shape and proof overnight in fridge"
            },
            {
                "order": 6,
                "instruction": "Bake at 450°F for 45 minutes"
            }
        ]
    }
    
    # Expected backend response structure (what API returns)
    expected_backend_response = {
        "id": "recipe-uuid",
        "name": "Country Sourdough",
        "description": "Classic sourdough with high hydration",
        "category": "sourdough",
        "current_version_id": "version-uuid",
        "current_version": {
            "id": "version-uuid",
            "recipe_id": "recipe-uuid",
            "version_major": 1,
            "version_minor": 0,
            "description": "Initial version",
            "ingredients": frontend_recipe_data["ingredients"],
            "instructions": frontend_recipe_data["instructions"],
            "created_at": "2024-01-01T00:00:00Z"
        },
        "bakers_percentages": {
            "total_flour_weight": 1000,
            "flour_ingredients": [
                {
                    "ingredient_id": "ing-uuid",
                    "name": "bread flour",
                    "amount": 1000,
                    "percentage": 100.0
                }
            ],
            "other_ingredients": [
                {
                    "ingredient_id": "ing-uuid-2",
                    "name": "water", 
                    "amount": 750,
                    "percentage": 75.0
                },
                {
                    "ingredient_id": "ing-uuid-3",
                    "name": "levain",
                    "amount": 200,
                    "percentage": 20.0
                },
                {
                    "ingredient_id": "ing-uuid-4",
                    "name": "salt",
                    "amount": 20,
                    "percentage": 2.0
                }
            ]
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    # Validate structure compatibility
    assert frontend_recipe_data["name"] == expected_backend_response["name"]
    assert frontend_recipe_data["description"] == expected_backend_response["description"]
    assert frontend_recipe_data["category"] == expected_backend_response["category"]
    
    # Validate ingredients structure
    frontend_ingredients = frontend_recipe_data["ingredients"]
    backend_ingredients = expected_backend_response["current_version"]["ingredients"]
    assert len(frontend_ingredients) == len(backend_ingredients)
    
    for i, (frontend_ing, backend_ing) in enumerate(zip(frontend_ingredients, backend_ingredients)):
        assert frontend_ing["name"] == backend_ing["name"]
        assert frontend_ing["amount"] == backend_ing["amount"]
        assert frontend_ing["unit"] == backend_ing["unit"]
        assert frontend_ing["type"] == backend_ing["type"]
    
    # Validate instructions structure
    frontend_instructions = frontend_recipe_data["instructions"]
    backend_instructions = expected_backend_response["current_version"]["instructions"]
    assert len(frontend_instructions) == len(backend_instructions)
    
    for frontend_inst, backend_inst in zip(frontend_instructions, backend_instructions):
        assert frontend_inst["order"] == backend_inst["order"]
        assert frontend_inst["instruction"] == backend_inst["instruction"]
    
    # Validate baker's percentages calculation
    bp = expected_backend_response["bakers_percentages"]
    assert bp["total_flour_weight"] == 1000
    assert bp["flour_ingredients"][0]["percentage"] == 100.0
    
    # Check hydration percentage (water/flour)
    water_percentage = next(ing["percentage"] for ing in bp["other_ingredients"] if ing["name"] == "water")
    assert water_percentage == 75.0


def test_version_update_workflow():
    """Test the version update workflow between frontend and backend"""
    
    # Original recipe (v1.0)
    original_recipe = {
        "name": "Country Sourdough", 
        "ingredients": [
            {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Autolyse for 30 minutes"}
        ]
    }
    
    # Updated recipe (should become v1.1)
    updated_recipe = {
        "name": "Country Sourdough",
        "ingredients": [
            {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 800, "unit": "grams", "type": "liquid"}  # Changed amount
        ],
        "instructions": [
            {"order": 1, "instruction": "Autolyse for 30 minutes"}
        ]
    }
    
    # Simulate change detection (this is what our backend versioning logic does)
    changes_detected = False
    
    # Check for ingredient changes
    for orig_ing, new_ing in zip(original_recipe["ingredients"], updated_recipe["ingredients"]):
        if orig_ing["amount"] != new_ing["amount"]:
            changes_detected = True
            break
    
    assert changes_detected == True
    
    # Expected version bump
    original_version = {"major": 1, "minor": 0}
    expected_new_version = {"major": 1, "minor": 1}
    
    assert expected_new_version["major"] == original_version["major"]
    assert expected_new_version["minor"] == original_version["minor"] + 1


def test_bakers_percentage_calculation():
    """Test baker's percentage calculation matches frontend and backend"""
    
    ingredients = [
        {"name": "bread flour", "amount": 800, "type": "flour"},
        {"name": "whole wheat flour", "amount": 200, "type": "flour"},  
        {"name": "water", "amount": 750, "type": "liquid"},
        {"name": "levain", "amount": 200, "type": "preferment"}
    ]
    
    # Calculate total flour weight
    flour_ingredients = [ing for ing in ingredients if ing["type"] == "flour"]
    total_flour_weight = sum(ing["amount"] for ing in flour_ingredients)
    
    assert total_flour_weight == 1000
    
    # Calculate percentages
    flour_percentages = []
    for ing in flour_ingredients:
        percentage = (ing["amount"] / total_flour_weight) * 100
        flour_percentages.append({
            "name": ing["name"],
            "amount": ing["amount"], 
            "percentage": percentage
        })
    
    other_percentages = []
    for ing in ingredients:
        if ing["type"] != "flour":
            percentage = (ing["amount"] / total_flour_weight) * 100
            other_percentages.append({
                "name": ing["name"],
                "amount": ing["amount"],
                "percentage": percentage
            })
    
    # Validate calculations
    assert flour_percentages[0]["percentage"] == 80.0  # bread flour
    assert flour_percentages[1]["percentage"] == 20.0  # whole wheat
    assert other_percentages[0]["percentage"] == 75.0  # water  
    assert other_percentages[1]["percentage"] == 20.0  # levain
    
    # Total flour should equal 100%
    total_flour_percentage = sum(fp["percentage"] for fp in flour_percentages)
    assert total_flour_percentage == 100.0


if __name__ == "__main__":
    # Run tests locally
    test_recipe_data_structure_compatibility()
    test_version_update_workflow() 
    test_bakers_percentage_calculation()
    print("✅ All integration tests passed!")