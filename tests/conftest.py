"""
Pytest configuration and fixtures for recipe testing
"""
import pytest
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any

@pytest.fixture
def sample_ingredient():
    """Basic ingredient fixture"""
    return {
        "id": str(uuid4()),
        "name": "bread flour",
        "amount": 1000,
        "unit": "grams",
        "type": "flour",
        "notes": "high protein flour"
    }

@pytest.fixture
def sample_ingredients():
    """Collection of sample ingredients for testing"""
    return [
        {
            "id": str(uuid4()),
            "name": "bread flour",
            "amount": 1000,
            "unit": "grams",
            "type": "flour",
            "notes": "high protein flour"
        },
        {
            "id": str(uuid4()),
            "name": "water",
            "amount": 750,
            "unit": "grams",
            "type": "liquid",
            "notes": "filtered water"
        },
        {
            "id": str(uuid4()),
            "name": "levain",
            "amount": 200,
            "unit": "grams",
            "type": "preferment",
            "notes": "100% hydration"
        },
        {
            "id": str(uuid4()),
            "name": "salt",
            "amount": 20,
            "unit": "grams",
            "type": "other",
            "notes": "fine sea salt"
        }
    ]

@pytest.fixture
def sample_instructions():
    """Sample recipe instructions"""
    return [
        {
            "id": str(uuid4()),
            "order": 1,
            "instruction": "Autolyse flour and water for 30 minutes"
        },
        {
            "id": str(uuid4()),
            "order": 2,
            "instruction": "Add levain and mix thoroughly"
        },
        {
            "id": str(uuid4()),
            "order": 3,
            "instruction": "Bulk ferment for 3 hours"
        },
        {
            "id": str(uuid4()),
            "order": 4,
            "instruction": "Pre-shape and rest 30 minutes"
        }
    ]

@pytest.fixture
def base_recipe(sample_ingredients, sample_instructions):
    """Complete recipe fixture for testing"""
    return {
        "id": str(uuid4()),
        "name": "Country Sourdough",
        "category": "sourdough",
        "ingredients": sample_ingredients,
        "instructions": sample_instructions,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def recipe_version_v1(base_recipe):
    """Recipe version 1.0 fixture"""
    return {
        "id": str(uuid4()),
        "recipe_id": base_recipe["id"],
        "version_number": 1,
        "description": "Initial version",
        "ingredients": base_recipe["ingredients"],
        "instructions": base_recipe["instructions"],
        "created_at": datetime.now(),
        "change_summary": {}
    }

@pytest.fixture
def modified_ingredients(sample_ingredients):
    """Modified ingredients for testing version changes"""
    modified = sample_ingredients.copy()
    # Change water amount
    modified[1] = {
        **modified[1],
        "amount": 800  # Changed from 750 to 800
    }
    # Add olive oil
    modified.append({
        "id": str(uuid4()),
        "name": "olive oil",
        "amount": 50,
        "unit": "grams",
        "type": "fat",
        "notes": "extra virgin"
    })
    return modified

@pytest.fixture
def modified_instructions(sample_instructions):
    """Modified instructions for testing step changes"""
    modified = sample_instructions.copy()
    # Change bulk ferment time
    modified[2] = {
        **modified[2],
        "instruction": "Bulk ferment for 4 hours at 78°F"  # Changed from 3 hours
    }
    return modified