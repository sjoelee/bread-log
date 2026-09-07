"""
Recipe Creation API Tests - Test-Driven Development
Tests for POST /recipes/ endpoint following TDD methodology
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from backend.service import app

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
          "notes": "",
        },
        {
          "name": "water",
          "amount": 750,
          "unit": "grams",
          "type": "liquid",
          "notes": "",
        },
        {
          "name": "levain",
          "amount": 200,
          "unit": "grams",
          "type": "liquid",
          "notes": "100% hydration starter",
        },
      ],
      "instructions": [
        {"order": 1, "instruction": "Autolyse flour and water for 30 minutes"},
        {"order": 2, "instruction": "Add levain and mix thoroughly"},
      ],
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

  def test_create_recipe_minimal_fields(self):
    """Test creating recipe with only required fields"""

    # GIVEN: Minimal valid recipe data
    recipe_data = {
      "name": "Simple Bread",
      "ingredients": [
        {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
        {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
      ],
      "instructions": [{"order": 1, "instruction": "Mix ingredients"}],
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
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [{"order": 1, "instruction": "Mix"}],
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
      "instructions": [{"order": 1, "instruction": "Do nothing"}],
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
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [],
    }

    # WHEN: Recipe creation is attempted
    response = client.post("/recipes/", json=recipe_data)

    # THEN: Validation error is returned
    assert response.status_code == 422

  def test_invalid_ingredient_amounts(self):
    """Test validation of ingredient amounts"""

    invalid_amounts = [
      {"amount": -100, "description": "negative amount"},
      {"amount": 0, "description": "zero amount"},
    ]

    for invalid_amount in invalid_amounts:
      # GIVEN: Recipe with invalid amount
      recipe_data = {
        "name": f"Test Recipe - {invalid_amount['description']}",
        "ingredients": [
          {
            "name": "flour",
            "amount": invalid_amount["amount"],
            "unit": "grams",
            "type": "flour",
          }
        ],
        "instructions": [{"order": 1, "instruction": "Mix"}],
      }

      # WHEN: Recipe creation is attempted
      response = client.post("/recipes/", json=recipe_data)

      # THEN: Validation error is returned
      assert response.status_code == 422


class TestIDGeneration:
  """Test instruction ID generation. Ingredients carry no id — they are diffed
  by name."""

  def test_instruction_id_generation(self):
    """Instruction IDs are generated when not provided; ingredients get none."""

    # GIVEN: Recipe data without any IDs
    recipe_data = {
      "name": "Auto ID Test",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [
        {"order": 1, "instruction": "Mix ingredients"}
        # No "id" field provided
      ],
    }

    # WHEN: Recipe is created
    response = client.post("/recipes/", json=recipe_data)

    # THEN: the instruction gets an id, the ingredient does not
    assert response.status_code == 201
    data = response.json()

    ingredient = data["current_version"]["ingredients"][0]
    instruction = data["current_version"]["instructions"][0]

    assert "id" not in ingredient
    assert "id" in instruction
    assert len(instruction["id"]) >= 8  # UUID or generated ID

  def test_preserve_provided_instruction_id(self):
    """A provided instruction id is preserved through creation."""

    # GIVEN: Recipe data with a custom instruction id
    recipe_data = {
      "name": "Custom ID Test",
      "ingredients": [
        {"name": "flour", "amount": 100, "unit": "grams", "type": "flour"}
      ],
      "instructions": [
        {"id": "custom_step_id", "order": 1, "instruction": "Mix ingredients"}
      ],
    }

    # WHEN: Recipe is created
    response = client.post("/recipes/", json=recipe_data)

    # THEN: the custom instruction id survives
    assert response.status_code == 201
    data = response.json()

    assert data["current_version"]["instructions"][0]["id"] == "custom_step_id"


class TestEdgeCases:
  """Test edge cases and special scenarios"""

  def test_large_recipe(self):
    """Test recipe with many ingredients and instructions"""

    # GIVEN: Recipe with many ingredients
    ingredients = [
      {"name": f"ingredient_{i}", "amount": 10, "unit": "grams", "type": "other"}
      for i in range(20)
    ]
    ingredients[0]["type"] = "flour"  # At least one flour for percentages

    instructions = [
      {"order": i + 1, "instruction": f"Step {i + 1}: Do something"} for i in range(50)
    ]

    recipe_data = {
      "name": "Very Large Recipe",
      "ingredients": ingredients,
      "instructions": instructions,
    }

    # WHEN: Recipe is created
    response = client.post("/recipes/", json=recipe_data)

    # THEN: Recipe is created successfully
    assert response.status_code == 201
    data = response.json()

    assert len(data["current_version"]["ingredients"]) == 20
    assert len(data["current_version"]["instructions"]) == 50


# Test fixtures for common data
@pytest.fixture
def basic_recipe_data():
  """Basic recipe for testing"""
  return {
    "name": "Test Basic Recipe",
    "ingredients": [
      {"name": "flour", "amount": 1000, "unit": "grams", "type": "flour"},
      {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
    ],
    "instructions": [{"order": 1, "instruction": "Mix ingredients"}],
  }


@pytest.fixture
def complete_recipe_data():
  return {
    "name": "Complete Test Recipe",
    "description": "A test recipe with all fields",
    "category": "sourdough",
    "ingredients": [
      {
        "name": "bread flour",
        "amount": 1000,
        "unit": "grams",
        "type": "flour",
        "notes": "High protein",
      },
      {
        "name": "water",
        "amount": 750,
        "unit": "grams",
        "type": "liquid",
        "notes": "Filtered",
      },
      {
        "name": "salt",
        "amount": 20,
        "unit": "grams",
        "type": "other",
        "notes": "Sea salt",
      },
    ],
    "instructions": [
      {"order": 1, "instruction": "Autolyse flour and water"},
      {"order": 2, "instruction": "Add salt and mix"},
    ],
  }
