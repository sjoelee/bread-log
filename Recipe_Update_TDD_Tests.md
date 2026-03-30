# Recipe Update TDD Test Cases

## Overview
This document contains comprehensive test cases for the recipe viewing and updating functionality using Test-Driven Development (TDD) methodology. Tests cover recipe retrieval, update scenarios, versioning, change detection, and error handling.

## Test Categories

### 1. Recipe Retrieval Tests (GET /recipes/{recipe_id})

#### Test 1.1: Retrieve Complete Recipe - Happy Path
```python
def test_get_complete_recipe():
    """Test retrieving a complete recipe with all related data"""
    
    # GIVEN: Existing recipe in database
    recipe = create_test_recipe({
        "name": "Test Sourdough",
        "description": "Test recipe",
        "category": "sourdough",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Mix ingredients"},
            {"order": 2, "instruction": "Bulk ferment"}
        ]
    })
    
    # WHEN: Recipe is retrieved by ID
    response = client.get(f"/recipes/{recipe.id}")
    
    # THEN: Complete recipe data is returned
    assert response.status_code == 200
    data = response.json()
    
    # Verify main recipe info
    assert data["id"] == str(recipe.id)
    assert data["name"] == "Test Sourdough"
    assert data["description"] == "Test recipe"
    assert data["category"] == "sourdough"
    assert data["current_version_id"] is not None
    
    # Verify current version data
    current_version = data["current_version"]
    assert current_version["version_number"] == 1
    assert len(current_version["ingredients"]) == 2
    assert len(current_version["instructions"]) == 2
    assert current_version["ingredients"][0]["name"] == "flour"
    assert current_version["instructions"][0]["order"] == 1
    
    # Verify baker's percentages
    percentages = data["bakers_percentages"]
    assert percentages["total_flour_weight"] == 1000.0
    assert len(percentages["flour_ingredients"]) == 1
    assert len(percentages["other_ingredients"]) == 1
    assert percentages["other_ingredients"][0]["percentage"] == 75.0  # water
    
    # Verify timestamps
    assert data["created_at"] is not None
    assert data["updated_at"] is not None

def test_get_recipe_not_found():
    """Test 404 response for non-existent recipe"""
    
    # GIVEN: Non-existent recipe ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # WHEN: Recipe retrieval is attempted
    response = client.get(f"/recipes/{fake_id}")
    
    # THEN: 404 error is returned
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()
    assert response.json()["recipe_id"] == fake_id

def test_get_recipe_invalid_uuid():
    """Test 422 response for invalid UUID format"""
    
    # GIVEN: Invalid UUID format
    invalid_id = "not-a-valid-uuid"
    
    # WHEN: Recipe retrieval is attempted
    response = client.get(f"/recipes/{invalid_id}")
    
    # THEN: 422 validation error is returned
    assert response.status_code == 422
    assert "invalid" in response.json()["error"].lower()
```

#### Test 1.2: Retrieve Recipe with Multiple Versions
```python
def test_get_recipe_with_version_history():
    """Test that GET returns current version even with multiple versions"""
    
    # GIVEN: Recipe with multiple versions
    recipe = create_test_recipe(basic_recipe_data)
    
    # Update recipe multiple times to create versions
    update_recipe(recipe.id, {"name": "Updated Name V2"})
    updated_recipe = update_recipe(recipe.id, {"description": "Updated Description V3"})
    
    # WHEN: Recipe is retrieved
    response = client.get(f"/recipes/{recipe.id}")
    
    # THEN: Latest version data is returned
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_version"]["version_number"] == 3
    assert data["name"] == "Updated Name V2"  # From version 2
    assert data["description"] == "Updated Description V3"  # From version 3
    assert data["current_version_id"] == updated_recipe["current_version_id"]
```

### 2. Basic Recipe Update Tests (PATCH /recipes/{recipe_id})

#### Test 2.1: Update Recipe Name Only
```python
def test_update_recipe_name():
    """Test updating only the recipe name"""
    
    # GIVEN: Existing recipe
    original_recipe = create_test_recipe({
        "name": "Original Name",
        "description": "Original description",
        "ingredients": [{"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    })
    
    # WHEN: Only name is updated
    update_data = {"name": "Updated Recipe Name"}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: New version is created with updated name
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Updated Recipe Name"
    assert data["description"] == "Original description"  # Unchanged
    assert data["current_version"]["version_number"] == 2
    
    # Verify change tracking
    change_summary = data["current_version"]["change_summary"]
    assert "name" in change_summary["changed_fields"]
    assert "Updated recipe name" in change_summary["summary"]
    
    # Verify other data unchanged
    assert len(data["current_version"]["ingredients"]) == 1
    assert len(data["current_version"]["instructions"]) == 1
    
    # Baker's percentages should remain the same
    assert data["bakers_percentages"]["total_flour_weight"] == 1000.0

def test_update_multiple_basic_fields():
    """Test updating name, description, and category together"""
    
    # GIVEN: Existing recipe
    original_recipe = create_test_recipe({
        "name": "Original Name",
        "description": "Original description",
        "category": "sourdough",
        "ingredients": [{"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    })
    
    # WHEN: Multiple fields are updated
    update_data = {
        "name": "New Recipe Name",
        "description": "New description with more details",
        "category": "enriched"
    }
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: All fields are updated in new version
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "New Recipe Name"
    assert data["description"] == "New description with more details"
    assert data["category"] == "enriched"
    assert data["current_version"]["version_number"] == 2
    
    # Verify change tracking
    change_summary = data["current_version"]["change_summary"]
    expected_fields = {"name", "description", "category"}
    assert set(change_summary["changed_fields"]) == expected_fields
```

#### Test 2.2: Update Ingredients with Recalculation
```python
def test_update_ingredients_recalculates_percentages():
    """Test that updating ingredients triggers baker's percentage recalculation"""
    
    # GIVEN: Recipe with known percentages
    original_recipe = create_test_recipe({
        "name": "Hydration Test",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"}  # 70% hydration
        ],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    })
    
    # WHEN: Water amount is increased
    updated_ingredients = [
        {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
        {"name": "water", "amount": 800, "unit": "grams", "type": "liquid"}  # 80% hydration
    ]
    update_data = {"ingredients": updated_ingredients}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: New percentages are calculated
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_version"]["version_number"] == 2
    
    # Verify updated ingredients
    ingredients = data["current_version"]["ingredients"]
    water_ingredient = next(ing for ing in ingredients if ing["name"] == "water")
    assert water_ingredient["amount"] == 800
    
    # Verify recalculated percentages
    percentages = data["bakers_percentages"]
    water_percentage = next(ing for ing in percentages["other_ingredients"] if ing["name"] == "water")
    assert water_percentage["percentage"] == 80.0
    
    # Verify change tracking
    change_summary = data["current_version"]["change_summary"]
    assert "ingredients" in change_summary["changed_fields"]
    assert "ingredient_changes" in change_summary

def test_update_ingredients_preserve_ids():
    """Test that existing ingredient IDs are preserved when possible"""
    
    # GIVEN: Recipe with ingredients that have specific IDs
    original_recipe = create_test_recipe({
        "name": "ID Preservation Test",
        "ingredients": [
            {"id": "flour_id_123", "name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"id": "water_id_456", "name": "water", "amount": 700, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    })
    
    # WHEN: Ingredient amounts are updated (same ingredients, different amounts)
    updated_ingredients = [
        {"id": "flour_id_123", "name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},  # Unchanged
        {"id": "water_id_456", "name": "water", "amount": 750, "unit": "grams", "type": "liquid"}   # Amount changed
    ]
    update_data = {"ingredients": updated_ingredients}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: Original IDs are preserved
    assert response.status_code == 200
    data = response.json()
    
    ingredients = data["current_version"]["ingredients"]
    flour_ing = next(ing for ing in ingredients if ing["name"] == "flour")
    water_ing = next(ing for ing in ingredients if ing["name"] == "water")
    
    assert flour_ing["id"] == "flour_id_123"
    assert water_ing["id"] == "water_id_456"
    assert water_ing["amount"] == 750
```

#### Test 2.3: Update Instructions
```python
def test_update_instructions():
    """Test updating recipe instructions"""
    
    # GIVEN: Recipe with original instructions
    original_recipe = create_test_recipe({
        "name": "Instruction Update Test",
        "ingredients": [{"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}],
        "instructions": [
            {"order": 1, "instruction": "Original step 1"},
            {"order": 2, "instruction": "Original step 2"}
        ]
    })
    
    # WHEN: Instructions are updated
    updated_instructions = [
        {"order": 1, "instruction": "Updated step 1 with more detail"},
        {"order": 2, "instruction": "Original step 2"},  # Unchanged
        {"order": 3, "instruction": "New step 3"}         # Added
    ]
    update_data = {"instructions": updated_instructions}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: Instructions are updated in new version
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_version"]["version_number"] == 2
    
    instructions = data["current_version"]["instructions"]
    assert len(instructions) == 3
    assert instructions[0]["instruction"] == "Updated step 1 with more detail"
    assert instructions[2]["instruction"] == "New step 3"
    
    # Verify change tracking
    change_summary = data["current_version"]["change_summary"]
    assert "instructions" in change_summary["changed_fields"]

def test_update_instruction_order():
    """Test reordering instructions"""
    
    # GIVEN: Recipe with ordered instructions
    original_recipe = create_test_recipe({
        "name": "Reorder Test",
        "ingredients": [{"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}],
        "instructions": [
            {"order": 1, "instruction": "First step"},
            {"order": 2, "instruction": "Second step"},
            {"order": 3, "instruction": "Third step"}
        ]
    })
    
    # WHEN: Instructions are reordered
    reordered_instructions = [
        {"order": 1, "instruction": "Third step"},   # Was order 3
        {"order": 2, "instruction": "First step"},  # Was order 1
        {"order": 3, "instruction": "Second step"}  # Was order 2
    ]
    update_data = {"instructions": reordered_instructions}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: New order is preserved
    assert response.status_code == 200
    data = response.json()
    
    instructions = data["current_version"]["instructions"]
    assert instructions[0]["instruction"] == "Third step"
    assert instructions[1]["instruction"] == "First step"
    assert instructions[2]["instruction"] == "Second step"
```

### 3. Change Detection and Versioning Tests

#### Test 3.1: No Changes Detection
```python
def test_no_changes_detected():
    """Test that submitting identical data doesn't create a new version"""
    
    # GIVEN: Existing recipe
    original_recipe = create_test_recipe(basic_recipe_data)
    original_version_number = get_recipe(original_recipe.id)["current_version"]["version_number"]
    
    # WHEN: Identical data is submitted
    identical_data = {
        "name": original_recipe["name"],
        "description": original_recipe["description"],
        "ingredients": original_recipe["current_version"]["ingredients"],
        "instructions": original_recipe["current_version"]["instructions"]
    }
    response = client.patch(f"/recipes/{original_recipe.id}", json=identical_data)
    
    # THEN: No new version is created
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_version"]["version_number"] == original_version_number
    assert data["updated_at"] == original_recipe["updated_at"]  # No update timestamp change

def test_minimal_change_detection():
    """Test detection of minimal changes like single character edits"""
    
    # GIVEN: Recipe with specific content
    original_recipe = create_test_recipe({
        "name": "Minimal Change Test",
        "description": "Original description",
        "ingredients": [{"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"}],
        "instructions": [{"order": 1, "instruction": "Mix well"}]
    })
    
    test_cases = [
        {"field": "name", "original": "Minimal Change Test", "updated": "Minimal Change Test!"},
        {"field": "description", "original": "Original description", "updated": "Original description."},
        {"field": "instruction", "original": "Mix well", "updated": "Mix well for 5 minutes"}
    ]
    
    for case in test_cases:
        # WHEN: Minimal change is made
        if case["field"] == "instruction":
            update_data = {
                "instructions": [{"order": 1, "instruction": case["updated"]}]
            }
        else:
            update_data = {case["field"]: case["updated"]}
        
        response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
        
        # THEN: Change is detected and new version created
        assert response.status_code == 200
        data = response.json()
        assert data["current_version"]["version_number"] > 1
        
        # Reset for next test case
        original_recipe = data
```

#### Test 3.2: Custom Version Description
```python
def test_custom_version_description():
    """Test providing custom description for new version"""
    
    # GIVEN: Existing recipe
    original_recipe = create_test_recipe(basic_recipe_data)
    
    # WHEN: Update includes custom version description
    update_data = {
        "name": "Updated Name",
        "version_description": "Custom description for this version change"
    }
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: Custom description is used
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_version"]["description"] == "Custom description for this version change"
    assert data["current_version"]["version_number"] == 2

def test_auto_generated_version_description():
    """Test automatic generation of version descriptions"""
    
    # GIVEN: Existing recipe
    original_recipe = create_test_recipe(basic_recipe_data)
    
    # WHEN: Multiple fields are updated without custom description
    update_data = {
        "name": "New Name",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 800, "unit": "grams", "type": "liquid"}  # Changed amount
        ]
    }
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: Description is auto-generated based on changes
    assert response.status_code == 200
    data = response.json()
    
    description = data["current_version"]["description"]
    assert "Updated recipe name" in description
    assert "Modified" in description and "ingredients" in description
```

### 4. Validation and Error Tests

#### Test 4.1: Update Validation Errors
```python
def test_update_invalid_ingredient_amounts():
    """Test validation errors when updating with invalid ingredient data"""
    
    # GIVEN: Existing recipe
    recipe = create_test_recipe(basic_recipe_data)
    
    invalid_updates = [
        {"ingredients": [{"name": "flour", "amount": -100, "unit": "grams", "type": "flour"}]},  # Negative amount
        {"ingredients": [{"name": "flour", "amount": 0, "unit": "grams", "type": "flour"}]},     # Zero amount
        {"ingredients": [{"amount": 100, "unit": "grams", "type": "flour"}]},                     # Missing name
        {"ingredients": [{"name": "flour", "amount": 100, "unit": "invalid", "type": "flour"}]}, # Invalid unit
    ]
    
    for invalid_update in invalid_updates:
        # WHEN: Invalid update is attempted
        response = client.patch(f"/recipes/{recipe.id}", json=invalid_update)
        
        # THEN: Validation error is returned
        assert response.status_code == 422
        assert "validation" in response.json()["error"].lower()

def test_update_empty_arrays():
    """Test validation when trying to update with empty ingredients or instructions"""
    
    # GIVEN: Existing recipe
    recipe = create_test_recipe(basic_recipe_data)
    
    # WHEN: Empty arrays are provided
    invalid_updates = [
        {"ingredients": []},     # No ingredients
        {"instructions": []}     # No instructions
    ]
    
    for invalid_update in invalid_updates:
        response = client.patch(f"/recipes/{recipe.id}", json=invalid_update)
        
        # THEN: Validation error is returned
        assert response.status_code == 422

def test_update_nonexistent_recipe():
    """Test 404 error when updating non-existent recipe"""
    
    # GIVEN: Non-existent recipe ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # WHEN: Update is attempted
    update_data = {"name": "New Name"}
    response = client.patch(f"/recipes/{fake_id}", json=update_data)
    
    # THEN: 404 error is returned
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()
```

### 5. Transaction and Concurrency Tests

#### Test 5.1: Transaction Rollback on Update Error
```python
def test_update_transaction_rollback():
    """Test that recipe update is atomic - all or nothing"""
    
    # GIVEN: Existing recipe
    recipe = create_test_recipe(basic_recipe_data)
    original_version = get_recipe(recipe.id)["current_version"]["version_number"]
    
    # WHEN: Database error occurs during baker's percentage calculation
    with mock.patch('recipe_service.update_bakers_percentages') as mock_calc:
        mock_calc.side_effect = Exception("Database error during percentage update")
        
        update_data = {
            "name": "Should Not Save",
            "ingredients": [{"name": "flour", "amount": 1200, "unit": "grams", "type": "flour"}]
        }
        response = client.patch(f"/recipes/{recipe.id}", json=update_data)
    
    # THEN: Error is returned and no partial updates are saved
    assert response.status_code == 500
    
    # Verify no changes were persisted
    current_recipe = get_recipe(recipe.id)
    assert current_recipe["current_version"]["version_number"] == original_version
    assert current_recipe["name"] != "Should Not Save"
    
    # Verify no orphaned version records
    version_count = db.execute(
        "SELECT COUNT(*) FROM recipe_versions WHERE recipe_id = %s", 
        (recipe.id,)
    ).scalar()
    assert version_count == 1  # Only original version

def test_version_increment_atomicity():
    """Test that version numbers are properly incremented even with concurrent updates"""
    
    # GIVEN: Recipe that will be updated concurrently
    recipe = create_test_recipe(basic_recipe_data)
    
    # WHEN: Multiple updates are attempted simultaneously (simulate with threading)
    import threading
    import time
    
    results = []
    errors = []
    
    def update_recipe_concurrent(update_suffix):
        try:
            update_data = {"name": f"Updated Name {update_suffix}"}
            response = client.patch(f"/recipes/{recipe.id}", json=update_data)
            results.append(response.json())
        except Exception as e:
            errors.append(str(e))
    
    # Start multiple update threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=update_recipe_concurrent, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.01)  # Small delay to increase chance of conflict
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # THEN: All updates should succeed with sequential version numbers
    assert len(errors) == 0
    version_numbers = [result["current_version"]["version_number"] for result in results]
    version_numbers.sort()
    expected_versions = list(range(2, 7))  # Versions 2-6
    assert version_numbers == expected_versions
```

### 6. Complex Update Scenarios

#### Test 6.1: Add and Remove Ingredients
```python
def test_add_and_remove_ingredients():
    """Test updating recipe by adding new ingredients and removing existing ones"""
    
    # GIVEN: Recipe with multiple ingredients
    original_recipe = create_test_recipe({
        "name": "Ingredient Modification Test",
        "ingredients": [
            {"name": "bread flour", "amount": 800, "unit": "grams", "type": "flour"},
            {"name": "whole wheat", "amount": 200, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
            {"name": "salt", "amount": 20, "unit": "grams", "type": "other"}
        ],
        "instructions": [{"order": 1, "instruction": "Mix"}]
    })
    
    # WHEN: Ingredients are added and removed
    updated_ingredients = [
        {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},  # Amount changed
        # whole wheat removed
        {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},        # Unchanged
        {"name": "salt", "amount": 20, "unit": "grams", "type": "other"},          # Unchanged
        {"name": "olive oil", "amount": 30, "unit": "grams", "type": "fat"}        # Added
    ]
    
    update_data = {"ingredients": updated_ingredients}
    response = client.patch(f"/recipes/{original_recipe.id}", json=update_data)
    
    # THEN: Changes are properly tracked
    assert response.status_code == 200
    data = response.json()
    
    # Verify updated ingredients
    ingredients = data["current_version"]["ingredients"]
    assert len(ingredients) == 4
    
    ingredient_names = [ing["name"] for ing in ingredients]
    assert "bread flour" in ingredient_names
    assert "whole wheat" not in ingredient_names  # Removed
    assert "olive oil" in ingredient_names        # Added
    
    # Verify percentage recalculation (flour total changed from 1000g to 1000g)
    percentages = data["bakers_percentages"]
    assert percentages["total_flour_weight"] == 1000.0
    
    oil_percentage = next(ing for ing in percentages["other_ingredients"] if ing["name"] == "olive oil")
    assert oil_percentage["percentage"] == 3.0

def test_major_recipe_overhaul():
    """Test completely changing a recipe (name, ingredients, instructions)"""
    
    # GIVEN: Simple original recipe
    original_recipe = create_test_recipe({
        "name": "Simple Bread",
        "description": "Basic bread",
        "category": "lean",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 600, "unit": "grams", "type": "liquid"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Mix ingredients"},
            {"order": 2, "instruction": "Bake"}
        ]
    })
    
    # WHEN: Recipe is completely overhauled
    overhaul_data = {
        "name": "Artisan Sourdough",
        "description": "Complex sourdough with preferment",
        "category": "sourdough",
        "ingredients": [
            {"name": "bread flour", "amount": 800, "unit": "grams", "type": "flour"},
            {"name": "whole wheat", "amount": 200, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 750, "unit": "grams", "type": "liquid"},
            {"name": "levain", "amount": 200, "unit": "grams", "type": "preferment"},
            {"name": "salt", "amount": 20, "unit": "grams", "type": "other"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Autolyse flour and water for 1 hour"},
            {"order": 2, "instruction": "Add levain and mix until incorporated"},
            {"order": 3, "instruction": "Add salt and perform initial mixing"},
            {"order": 4, "instruction": "Bulk ferment with stretch and folds"},
            {"order": 5, "instruction": "Pre-shape and bench rest"},
            {"order": 6, "instruction": "Final shape and proof"},
            {"order": 7, "instruction": "Bake with steam"}
        ],
        "version_description": "Complete recipe overhaul to artisan sourdough"
    }
    
    response = client.patch(f"/recipes/{original_recipe.id}", json=overhaul_data)
    
    # THEN: All changes are properly applied and tracked
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Artisan Sourdough"
    assert data["category"] == "sourdough"
    assert data["current_version"]["version_number"] == 2
    assert data["current_version"]["description"] == "Complete recipe overhaul to artisan sourdough"
    
    # Verify all change types are detected
    change_summary = data["current_version"]["change_summary"]
    expected_changes = {"name", "description", "category", "ingredients", "instructions"}
    assert set(change_summary["changed_fields"]) == expected_changes
    
    # Verify new ingredient count and percentages
    assert len(data["current_version"]["ingredients"]) == 5
    assert len(data["current_version"]["instructions"]) == 7
    assert data["bakers_percentages"]["total_flour_weight"] == 1000.0
```

## Test Data Fixtures and Utilities

### Recipe Update Test Fixtures
```python
@pytest.fixture
def basic_recipe_data():
    """Basic recipe for update testing"""
    return {
        "name": "Basic Test Recipe",
        "description": "A simple recipe for testing updates",
        "category": "lean",
        "ingredients": [
            {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
            {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
            {"name": "salt", "amount": 20, "unit": "grams", "type": "other"}
        ],
        "instructions": [
            {"order": 1, "instruction": "Mix flour and water, autolyse 30 minutes"},
            {"order": 2, "instruction": "Add salt and knead until smooth"},
            {"order": 3, "instruction": "Bulk ferment until doubled"},
            {"order": 4, "instruction": "Shape and final proof"},
            {"order": 5, "instruction": "Bake until golden"}
        ]
    }

@pytest.fixture
def create_test_recipe():
    """Helper function to create recipes for testing"""
    def _create_recipe(recipe_data):
        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 201
        return response.json()
    return _create_recipe

@pytest.fixture
def get_recipe():
    """Helper function to retrieve recipes"""
    def _get_recipe(recipe_id):
        response = client.get(f"/recipes/{recipe_id}")
        assert response.status_code == 200
        return response.json()
    return _get_recipe

@pytest.fixture
def update_recipe():
    """Helper function to update recipes"""
    def _update_recipe(recipe_id, update_data):
        response = client.patch(f"/recipes/{recipe_id}", json=update_data)
        return response.json() if response.status_code == 200 else response
    return _update_recipe
```

### Change Detection Test Utilities
```python
def assert_version_incremented(original_version, updated_data):
    """Assert that version number was properly incremented"""
    assert updated_data["current_version"]["version_number"] == original_version + 1

def assert_change_detected(updated_data, expected_changed_fields):
    """Assert that specific fields were detected as changed"""
    changed_fields = set(updated_data["current_version"]["change_summary"]["changed_fields"])
    expected_fields = set(expected_changed_fields)
    assert changed_fields == expected_fields

def assert_baker_percentages_recalculated(original_percentages, updated_percentages):
    """Assert that baker's percentages were recalculated"""
    # Should have different timestamps if recalculated
    if original_percentages and updated_percentages:
        assert original_percentages != updated_percentages

def assert_ids_preserved(original_ingredients, updated_ingredients, preserved_names):
    """Assert that IDs were preserved for ingredients with matching names"""
    original_by_name = {ing["name"]: ing["id"] for ing in original_ingredients}
    updated_by_name = {ing["name"]: ing["id"] for ing in updated_ingredients}
    
    for name in preserved_names:
        assert name in original_by_name
        assert name in updated_by_name
        assert original_by_name[name] == updated_by_name[name]
```

This comprehensive test suite ensures reliable recipe updating functionality with proper versioning, change detection, validation, and transaction safety.