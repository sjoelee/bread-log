"""
Baker's Percentage Calculation Tests
Tests for recipe baker's percentage calculation logic
"""
import pytest
from backend.recipe_versioning import calculate_bakers_percentages


class TestBakerPercentageCalculations:
    """Test baker's percentage calculations with various scenarios"""
    
    def test_basic_bread_recipe_percentages(self):
        """Test basic sourdough recipe with standard percentages"""
        
        # GIVEN: Standard sourdough ingredients 
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "type": "flour"},
            {"id": "2", "name": "water", "amount": 750, "type": "liquid"},
            {"id": "3", "name": "salt", "amount": 20, "type": "other"}
        ]
        
        # WHEN: Baker's percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Correct percentages are returned
        assert result["total_flour_weight"] == 1000
        assert len(result["flour_ingredients"]) == 1
        assert len(result["other_ingredients"]) == 2
        
        # Flour should be 100%
        flour_item = result["flour_ingredients"][0]
        assert flour_item["name"] == "bread flour"
        assert flour_item["amount"] == 1000
        assert flour_item["percentage"] == 100.0
        
        # Water should be 75%
        water_item = [ing for ing in result["other_ingredients"] if ing["name"] == "water"][0]
        assert water_item["amount"] == 750
        assert water_item["percentage"] == 75.0
        
        # Salt should be 2%
        salt_item = [ing for ing in result["other_ingredients"] if ing["name"] == "salt"][0]
        assert salt_item["amount"] == 20
        assert salt_item["percentage"] == 2.0

    def test_multiple_flour_types_percentages(self):
        """Test recipe with multiple flour types"""
        
        # GIVEN: Recipe with different flour types
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 800, "type": "flour"},
            {"id": "2", "name": "whole wheat flour", "amount": 200, "type": "flour"},
            {"id": "3", "name": "water", "amount": 650, "type": "liquid"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Total flour weight includes all flours
        assert result["total_flour_weight"] == 1000
        assert len(result["flour_ingredients"]) == 2
        
        # Bread flour should be 80%
        bread_flour = [f for f in result["flour_ingredients"] if f["name"] == "bread flour"][0]
        assert bread_flour["percentage"] == 80.0
        
        # Whole wheat should be 20%
        ww_flour = [f for f in result["flour_ingredients"] if f["name"] == "whole wheat flour"][0]
        assert ww_flour["percentage"] == 20.0
        
        # Water should be 65% of total flour
        water_item = result["other_ingredients"][0]
        assert water_item["percentage"] == 65.0

    def test_no_flour_ingredients_default_behavior(self):
        """Test behavior when no flour ingredients are present"""
        
        # GIVEN: Recipe without flour (edge case)
        ingredients = [
            {"id": "1", "name": "water", "amount": 500, "type": "liquid"},
            {"id": "2", "name": "salt", "amount": 10, "type": "other"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Default flour weight is used
        assert result["total_flour_weight"] == 1000  # Default
        assert len(result["flour_ingredients"]) == 0
        assert len(result["other_ingredients"]) == 2
        
        # Percentages calculated against default 1000g flour
        water_item = [ing for ing in result["other_ingredients"] if ing["name"] == "water"][0]
        assert water_item["percentage"] == 50.0  # 500/1000 * 100
        
        salt_item = [ing for ing in result["other_ingredients"] if ing["name"] == "salt"][0]
        assert water_item["percentage"] == 50.0  # 500/1000 * 100

    def test_high_hydration_recipe_percentages(self):
        """Test high hydration recipe with complex ingredients"""
        
        # GIVEN: High hydration ciabatta recipe
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "type": "flour"},
            {"id": "2", "name": "water", "amount": 850, "type": "liquid"},
            {"id": "3", "name": "olive oil", "amount": 30, "type": "fat"},
            {"id": "4", "name": "salt", "amount": 18, "type": "other"},
            {"id": "5", "name": "active dry yeast", "amount": 3, "type": "other"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: High hydration percentage is correct
        assert result["total_flour_weight"] == 1000
        
        water_item = [ing for ing in result["other_ingredients"] if ing["name"] == "water"][0]
        assert water_item["percentage"] == 85.0
        
        oil_item = [ing for ing in result["other_ingredients"] if ing["name"] == "olive oil"][0]
        assert oil_item["percentage"] == 3.0
        
        salt_item = [ing for ing in result["other_ingredients"] if ing["name"] == "salt"][0]
        assert salt_item["percentage"] == 1.8
        
        yeast_item = [ing for ing in result["other_ingredients"] if ing["name"] == "active dry yeast"][0]
        assert yeast_item["percentage"] == 0.3

    def test_preferment_calculations(self):
        """Test recipe with preferment (starter/poolish)"""
        
        # GIVEN: Recipe with sourdough starter
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 900, "type": "flour"},
            {"id": "2", "name": "sourdough starter", "amount": 200, "type": "preferment"},
            {"id": "3", "name": "water", "amount": 600, "type": "liquid"},
            {"id": "4", "name": "salt", "amount": 18, "type": "other"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Preferment is treated as other ingredient
        assert result["total_flour_weight"] == 900
        
        starter_item = [ing for ing in result["other_ingredients"] if ing["name"] == "sourdough starter"][0]
        assert starter_item["percentage"] == 22.2  # 200/900 * 100, rounded to 1 decimal

    def test_decimal_precision_rounding(self):
        """Test that percentages are properly rounded to 1 decimal place"""
        
        # GIVEN: Recipe that produces non-round percentages
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 333, "type": "flour"},
            {"id": "2", "name": "water", "amount": 250, "type": "liquid"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Results are rounded to 1 decimal
        water_item = result["other_ingredients"][0]
        # 250/333 * 100 = 75.075... should round to 75.1
        assert water_item["percentage"] == 75.1

    def test_zero_amount_ingredients(self):
        """Test handling of zero-amount ingredients"""
        
        # GIVEN: Recipe with zero amount ingredient
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "type": "flour"},
            {"id": "2", "name": "water", "amount": 700, "type": "liquid"},
            {"id": "3", "name": "sugar", "amount": 0, "type": "other"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Zero amount ingredients have 0% 
        sugar_item = [ing for ing in result["other_ingredients"] if ing["name"] == "sugar"][0]
        assert sugar_item["percentage"] == 0.0

    def test_missing_ingredient_ids(self):
        """Test that missing ingredient IDs are handled gracefully"""
        
        # GIVEN: Ingredients without IDs
        ingredients = [
            {"name": "bread flour", "amount": 1000, "type": "flour"},
            {"name": "water", "amount": 750, "type": "liquid"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Calculation works despite missing IDs
        assert result["total_flour_weight"] == 1000
        flour_item = result["flour_ingredients"][0]
        water_item = result["other_ingredients"][0]
        
        assert flour_item["ingredient_id"] is None
        assert water_item["ingredient_id"] is None
        assert flour_item["percentage"] == 100.0
        assert water_item["percentage"] == 75.0

    def test_edge_case_very_small_amounts(self):
        """Test with very small ingredient amounts"""
        
        # GIVEN: Recipe with very small amounts (like salt, yeast)
        ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "type": "flour"},
            {"id": "2", "name": "active dry yeast", "amount": 2.5, "type": "other"},
            {"id": "3", "name": "salt", "amount": 18.5, "type": "other"}
        ]
        
        # WHEN: Percentages are calculated
        result = calculate_bakers_percentages(ingredients)
        
        # THEN: Small percentages are calculated correctly
        yeast_item = [ing for ing in result["other_ingredients"] if ing["name"] == "active dry yeast"][0]
        assert yeast_item["percentage"] == 0.2  # 2.5/1000 * 100 = 0.25, rounded to 0.2
        
        salt_item = [ing for ing in result["other_ingredients"] if ing["name"] == "salt"][0]
        assert salt_item["percentage"] == 1.8  # 18.5/1000 * 100 = 1.85, rounded to 1.8


class TestBakerPercentageIntegration:
    """Test baker's percentage calculations integrated with recipe creation"""
    
    def test_recipe_creation_includes_correct_percentages(self):
        """Test that recipe creation API includes correct baker's percentages"""
        from fastapi.testclient import TestClient
        from backend.service import app
        
        client = TestClient(app)
        
        # GIVEN: Recipe data for creation
        recipe_data = {
            "name": "Baker's Percentage Test Recipe",
            "description": "Testing percentage calculations in API",
            "ingredients": [
                {"name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"},
                {"name": "water", "amount": 700, "unit": "grams", "type": "liquid"},
                {"name": "salt", "amount": 20, "unit": "grams", "type": "other"}
            ],
            "instructions": [
                {"order": 1, "instruction": "Mix flour and water"}
            ]
        }
        
        # WHEN: Recipe is created via API
        response = client.post("/recipes/", json=recipe_data)
        
        # THEN: Response includes correct baker's percentages
        assert response.status_code == 201
        data = response.json()
        
        bp = data["bakers_percentages"]
        assert bp["total_flour_weight"] == 1000.0
        assert len(bp["flour_ingredients"]) == 1
        assert len(bp["other_ingredients"]) == 2
        
        # Verify flour percentage
        flour_item = bp["flour_ingredients"][0]
        assert flour_item["name"] == "bread flour"
        assert flour_item["percentage"] == 100.0
        
        # Verify water percentage (70% hydration)
        water_item = [ing for ing in bp["other_ingredients"] if ing["name"] == "water"][0]
        assert water_item["percentage"] == 70.0
        
        # Verify salt percentage (2%)
        salt_item = [ing for ing in bp["other_ingredients"] if ing["name"] == "salt"][0]
        assert salt_item["percentage"] == 2.0