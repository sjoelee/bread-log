# Recipe Creation TDD Test Cases

## Overview
This document contains comprehensive test cases for the recipe creation feature using Test-Driven Development (TDD) methodology. Tests cover happy paths, edge cases, validation, and error handling scenarios.

## Test Categories

### 1. Happy Path Tests

#### Test 1.1: Create Basic Recipe - Minimal Required Fields
```python
def test_create_basic_recipe():
    """Test creating a simple recipe with only required fields"""
    
    # GIVEN: Minimal valid recipe data
    recipe_data = {
        "name": "Simple Bread",
        "ingredients": [
            {
                "name": "bread flour",
                "amount": 1000,
                "unit": "grams", 
                "type": "flour"
            },
            {
                "name": "water",
                "amount": 700,
                "unit": "grams",
                "type": "liquid"
            }
        ],
        "instructions": [
            {
                "order": 1,
                "instruction": "Mix flour and water"
            }
        ]
    }
    
    # WHEN: Recipe is created via API
    response = client.post("/recipes/", json=recipe_data)
    
    # THEN: Recipe is successfully created
    assert response.status_code == 201
    data = response.json()
    
    # Verify basic recipe info
    assert data["name"] == "Simple Bread"
    assert data["description"] is None
    assert data["category"] is None
    assert data["current_version"]["version_number"] == 1
    
    # Verify ingredients have generated IDs
    ingredients = data["current_version"]["ingredients"]
    assert len(ingredients) == 2
    assert all("id" in ing for ing in ingredients)
    assert ingredients[0]["name"] == "bread flour"
    assert ingredients[0]["amount"] == 1000
    
    # Verify instructions have generated IDs
    instructions = data["current_version"]["instructions"]
    assert len(instructions) == 1
    assert "id" in instructions[0]
    assert instructions[0]["order"] == 1
    
    # Verify baker's percentages calculated
    percentages = data["bakers_percentages"]
    assert percentages["total_flour_weight"] == 1000.0
    assert len(percentages["flour_ingredients"]) == 1
    assert percentages["flour_ingredients"][0]["percentage"] == 100.0
    assert len(percentages["other_ingredients"]) == 1
    assert percentages["other_ingredients"][0]["percentage"] == 70.0  # water
```

#### Test 1.2: Create Complete Recipe - All Fields
```python
def test_create_complete_recipe():
    """Test creating a recipe with all optional fields populated"""
    
    # GIVEN: Complete recipe data
    recipe_data = {
        "name": "Artisan Sourdough",
        "description": "Traditional country-style sourdough bread",
        "category": "sourdough",
        "ingredients": [
            {
                "name": "bread flour",
                "amount": 1000,
                "unit": "grams",
                "type": "flour",
                "notes": "High protein flour, 12-14%"
            },
            {
                "name": "water",
                "amount": 750,
                "unit": "grams",
                "type": "liquid",
                "notes": "Filtered water at room temperature"
            },
            {
                "name": "levain",
                "amount": 200,
                "unit": "grams",
                "type": "liquid",
                "notes": "100% hydration sourdough starter"
            },
            {
                "name": "salt",
                "amount": 20,
                "unit": "grams",
                "type": "other",
                "notes": "Fine sea salt"
            }
        ],
        "instructions": [
            {
                "order": 1,
                "instruction": "Autolyse flour and water for 30 minutes at room temperature"
            },
            {
                "order": 2,
                "instruction": "Add active levain and mix until well incorporated"
            },
            {
                "order": 3,
                "instruction": "Add salt and mix thoroughly, then perform 3 sets of stretch and folds"
            },
            {
                "order": 4,
                "instruction": "Bulk ferment for 3-4 hours at 78°F until doubled in size"
            }
        ]
    }
    
    # WHEN: Recipe is created
    response = client.post("/recipes/", json=recipe_data)
    
    # THEN: All fields are saved correctly
    assert response.status_code == 201
    data = response.json()
    
    assert data["name"] == "Artisan Sourdough"
    assert data["description"] == "Traditional country-style sourdough bread"
    assert data["category"] == "sourdough"
    
    # Verify all ingredients with notes
    ingredients = data["current_version"]["ingredients"]
    assert len(ingredients) == 4
    flour_ing = next(ing for ing in ingredients if ing["name"] == "bread flour")
    assert flour_ing["notes"] == "High protein flour, 12-14%"
    
    # Verify all instructions
    instructions = data["current_version"]["instructions"]
    assert len(instructions) == 4
    assert "Autolyse" in instructions[0]["instruction"]
    assert "levain" in instructions[1]["instruction"]
    
    # Verify baker's percentages
    percentages = data["bakers_percentages"]
    assert percentages["total_flour_weight"] == 1000.0
    
    # Check specific percentages
    other_ings = percentages["other_ingredients"]
    water_pct = next(ing["percentage"] for ing in other_ings if ing["name"] == "water")
    levain_pct = next(ing["percentage"] for ing in other_ings if ing["name"] == "levain")
    salt_pct = next(ing["percentage"] for ing in other_ings if ing["name"] == "salt")
    
    assert water_pct == 75.0
    assert levain_pct == 20.0
    assert salt_pct == 2.0
```

#### Test 1.3: Create Recipe with Multiple Flour Types
```python
def test_create_multiple_flour_recipe():
    """Test baker's percentage calculation with multiple flour types"""
    
    # GIVEN: Recipe with multiple flours
    recipe_data = {
        "name": "Mixed Flour Bread",
        "ingredients": [
            {"name": "bread flour", "amount": 700, "unit": "grams", "type": "flour"},
            {"name": "whole wheat flour", "amount": 200, "unit": "grams", "type": "flour"},
            {"name": "rye flour", "amount": 100, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [{"order": 1, "instruction": "Mix all ingredients"}]
    }
    
    # WHEN: Recipe is created
    response = client.post("/recipes/", json=recipe_data)
    
    # THEN: Flour percentages are calculated correctly
    assert response.status_code == 201
    percentages = response.json()["bakers_percentages"]
    
    assert percentages["total_flour_weight"] == 1000.0
    assert len(percentages["flour_ingredients"]) == 3
    
    # Verify individual flour percentages
    flour_ings = percentages["flour_ingredients"]
    bread_flour = next(f for f in flour_ings if f["name"] == "bread flour")
    wheat_flour = next(f for f in flour_ings if f["name"] == "whole wheat flour")
    rye_flour = next(f for f in flour_ings if f["name"] == "rye flour")
    
    assert bread_flour["percentage"] == 70.0
    assert wheat_flour["percentage"] == 20.0
    assert rye_flour["percentage"] == 10.0
    
    # Total flour percentages should sum to 100
    total_flour_pct = sum(f["percentage"] for f in flour_ings)
    assert total_flour_pct == 100.0
    
    # Water should be 75% of total flour
    other_ings = percentages["other_ingredients"]
    water_pct = next(ing["percentage"] for ing in other_ings if ing["name"] == "water")
    assert water_pct == 75.0
```

### 2. Validation Tests

#### Test 2.1: Missing Required Fields
```python
def test_missing_required_name():
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
    error_data = response.json()
    assert "name" in str(error_data).lower()

def test_missing_ingredients():
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
    assert "ingredients" in str(response.json()).lower()

def test_missing_instructions():
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
    assert "instructions" in str(response.json()).lower()
```

#### Test 2.2: Invalid Ingredient Data
```python
def test_invalid_ingredient_amounts():
    """Test validation of ingredient amounts"""
    
    invalid_amounts = [
        {"amount": -100, "description": "negative amount"},
        {"amount": 0, "description": "zero amount"},
        {"amount": "not_a_number", "description": "non-numeric amount"}
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
        assert "amount" in str(response.json()).lower()

def test_invalid_ingredient_fields():
    """Test validation of required ingredient fields"""
    
    invalid_ingredients = [
        {"amount": 100, "unit": "grams", "type": "flour"},  # Missing name
        {"name": "flour", "unit": "grams", "type": "flour"},  # Missing amount
        {"name": "flour", "amount": 100, "type": "flour"},  # Missing unit
        {"name": "flour", "amount": 100, "unit": "grams"},  # Missing type
        {"name": "", "amount": 100, "unit": "grams", "type": "flour"},  # Empty name
        {"name": "flour", "amount": 100, "unit": "invalid", "type": "flour"},  # Invalid unit
        {"name": "flour", "amount": 100, "unit": "grams", "type": "invalid"}  # Invalid type
    ]
    
    for i, invalid_ingredient in enumerate(invalid_ingredients):
        recipe_data = {
            "name": f"Test Recipe {i}",
            "ingredients": [invalid_ingredient],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 422
```

#### Test 2.3: Invalid Instructions
```python
def test_invalid_instructions():
    """Test validation of instruction data"""
    
    invalid_instructions = [
        {"order": 1},  # Missing instruction text
        {"instruction": "Mix well"},  # Missing order
        {"order": 0, "instruction": "Mix well"},  # Invalid order (must be > 0)
        {"order": 1, "instruction": ""},  # Empty instruction
        {"order": "not_a_number", "instruction": "Mix well"}  # Non-numeric order
    ]
    
    for i, invalid_instruction in enumerate(invalid_instructions):
        recipe_data = {
            "name": f"Test Recipe {i}",
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [invalid_instruction]
        }
        
        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 422

def test_duplicate_instruction_orders():
    """Test validation of duplicate instruction order numbers"""
    
    # GIVEN: Instructions with duplicate order numbers
    recipe_data = {
        "name": "Duplicate Orders",
        "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
        "instructions": [
            {"order": 1, "instruction": "First step"},
            {"order": 1, "instruction": "Duplicate step"}  # Same order number
        ]
    }
    
    # WHEN: Recipe creation is attempted
    response = client.post("/recipes/", json=recipe_data)
    
    # THEN: Validation error is returned
    assert response.status_code == 422
    assert "order" in str(response.json()).lower()
```

#### Test 2.4: Category Validation
```python
def test_invalid_category():
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
    
    # THEN: Validation error is returned
    assert response.status_code == 422
    assert "category" in str(response.json()).lower()

def test_valid_categories():
    """Test that all valid categories are accepted"""
    
    valid_categories = ["sourdough", "enriched", "lean", "sweet", "other"]
    
    for category in valid_categories:
        recipe_data = {
            "name": f"Test {category.title()} Recipe",
            "category": category,
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        
        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 201
        assert response.json()["category"] == category
```

### 3. Edge Cases and Error Handling

#### Test 3.1: No Flour Recipe
```python
def test_no_flour_recipe():
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
```

#### Test 3.2: Very Large Recipe
```python
def test_large_recipe():
    """Test recipe with many ingredients and instructions"""
    
    # GIVEN: Recipe with many ingredients
    ingredients = [{"name": f"ingredient_{i}", "amount": 10, "unit": "grams", "type": "other"} 
                  for i in range(50)]
    ingredients[0]["type"] = "flour"  # At least one flour for percentages
    
    instructions = [{"order": i+1, "instruction": f"Step {i+1}: Do something"} 
                   for i in range(100)]
    
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
    
    assert len(data["current_version"]["ingredients"]) == 50
    assert len(data["current_version"]["instructions"]) == 100
    assert data["bakers_percentages"]["total_flour_weight"] == 10.0
```

### 4. Database Transaction Tests

#### Test 4.1: Transaction Rollback on Error
```python
def test_transaction_rollback():
    """Test that recipe creation is atomic - all or nothing"""
    
    # GIVEN: Valid recipe data but mock a database error during percentages calculation
    recipe_data = {
        "name": "Transaction Test Recipe",
        "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    }
    
    # WHEN: Database error occurs during baker's percentage calculation
    with mock.patch('recipe_service.store_bakers_percentages') as mock_calc:
        mock_calc.side_effect = Exception("Database error during percentages")
        response = client.post("/recipes/", json=recipe_data)
    
    # THEN: Error is returned and no partial data is saved
    assert response.status_code == 500
    
    # Verify no partial data was saved to any table
    recipes_count = db.execute("SELECT COUNT(*) FROM recipes").scalar()
    versions_count = db.execute("SELECT COUNT(*) FROM recipe_versions").scalar()
    percentages_count = db.execute("SELECT COUNT(*) FROM bakers_percentages").scalar()
    
    assert recipes_count == 0
    assert versions_count == 0
    assert percentages_count == 0

def test_version_creation_failure():
    """Test rollback when recipe version creation fails"""
    
    recipe_data = {
        "name": "Version Failure Test",
        "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    }
    
    # Mock failure during version creation
    with mock.patch('recipe_service.create_recipe_version') as mock_version:
        mock_version.side_effect = Exception("Version creation failed")
        response = client.post("/recipes/", json=recipe_data)
    
    assert response.status_code == 500
    
    # Verify no recipe record was left behind
    recipes_count = db.execute("SELECT COUNT(*) FROM recipes").scalar()
    assert recipes_count == 0
```

### 5. ID Generation Tests

#### Test 5.1: Auto-Generated IDs
```python
def test_ingredient_id_generation():
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

def test_preserve_provided_ids():
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
```

### 6. Performance Tests

#### Test 6.1: Concurrent Recipe Creation
```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_recipe_creation():
    """Test handling of simultaneous recipe creations"""
    
    # GIVEN: Multiple recipe creation requests
    async def create_recipe(name_suffix):
        recipe_data = {
            "name": f"Concurrent Recipe {name_suffix}",
            "ingredients": [{"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}],
            "instructions": [{"order": 1, "instruction": "Mix"}]
        }
        return await async_client.post("/recipes/", json=recipe_data)
    
    # WHEN: Multiple requests are made simultaneously
    tasks = [create_recipe(i) for i in range(10)]
    responses = await asyncio.gather(*tasks)
    
    # THEN: All recipes are created successfully
    for response in responses:
        assert response.status_code == 201
    
    # Verify all recipes have unique IDs
    recipe_ids = [resp.json()["id"] for resp in responses]
    assert len(set(recipe_ids)) == 10  # All IDs should be unique
```

## Test Data Fixtures

### Standard Test Recipe Data
```python
@pytest.fixture
def basic_recipe_data():
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
```

This comprehensive test suite ensures reliable recipe creation functionality with proper validation, error handling, and edge case coverage.