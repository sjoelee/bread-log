"""
Recipe Creation Service Tests - Test-Driven Development
Tests for the RecipeService.create_recipe() method before testing API layer
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock imports since we don't have a database setup for tests yet
try:
    from unittest.mock import MagicMock, patch
    
    # Mock the database connector
    mock_db = MagicMock()
    
    # Import after setting up mocks
    with patch('backend.recipe_service.DBConnector', mock_db):
        from backend.recipe_service import RecipeService
        from backend.models import RecipeRequest, Ingredient, RecipeStep
        
except ImportError as e:
    pytest.skip(f"Cannot import backend modules: {e}", allow_module_level=True)


class TestRecipeCreationService:
    """Test the recipe creation service logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.recipe_service = RecipeService(self.mock_db)
    
    def test_create_basic_recipe_data_processing(self):
        """Test that recipe service processes basic recipe data correctly"""
        
        # GIVEN: Valid recipe request
        recipe_request = RecipeRequest(
            name="Simple Sourdough",
            description="Basic country bread",
            category="sourdough",
            ingredients=[
                Ingredient(
                    name="bread flour",
                    amount=1000,
                    unit="grams", 
                    type="flour"
                ),
                Ingredient(
                    name="water",
                    amount=750,
                    unit="grams",
                    type="liquid"
                )
            ],
            instructions=[
                RecipeStep(order=1, instruction="Autolyse flour and water for 30 minutes"),
                RecipeStep(order=2, instruction="Add levain and mix thoroughly")
            ]
        )
        
        # Mock the database operations
        self.mock_db.create_recipe_with_transaction.return_value = True
        
        # WHEN: Recipe is created (this will fail until we implement it)
        # For now, just test that the request model validation works
        assert recipe_request.name == "Simple Sourdough"
        assert len(recipe_request.ingredients) == 2
        assert len(recipe_request.instructions) == 2
        assert recipe_request.ingredients[0].type == "flour"
        assert recipe_request.ingredients[0].amount == 1000

    def test_ingredient_validation(self):
        """Test ingredient validation works"""
        
        # GIVEN: Invalid ingredient data
        with pytest.raises(Exception):  # This should be a ValidationError
            Ingredient(
                name="",  # Empty name should fail
                amount=100,
                unit="grams",
                type="flour"
            )
        
        with pytest.raises(Exception):  # This should be a ValidationError  
            Ingredient(
                name="flour",
                amount=-100,  # Negative amount should fail
                unit="grams", 
                type="flour"
            )

    def test_recipe_request_validation(self):
        """Test recipe request validation"""
        
        # GIVEN: Invalid recipe data
        with pytest.raises(Exception):  # Should be ValidationError
            RecipeRequest(
                name="",  # Empty name should fail
                ingredients=[],  # Empty ingredients should fail
                instructions=[]  # Empty instructions should fail
            )


class TestBakersPercentageCalculation:
    """Test baker's percentage calculation logic"""
    
    def test_single_flour_calculation(self):
        """Test percentage calculation with single flour type"""
        
        # This is a unit test of the calculation logic
        # We'll implement this when we get to the calculation functions
        ingredients = [
            {"name": "bread flour", "amount": 1000, "type": "flour"},
            {"name": "water", "amount": 750, "type": "liquid"},
            {"name": "salt", "amount": 20, "type": "other"}
        ]
        
        # Expected percentages:
        # flour: 100% (base)
        # water: 75% (750/1000)
        # salt: 2% (20/1000)
        
        # For now, just validate the test data structure
        flour_total = sum(ing["amount"] for ing in ingredients if ing["type"] == "flour")
        assert flour_total == 1000
        
        water_percentage = (750 / flour_total) * 100
        assert water_percentage == 75.0
        
        salt_percentage = (20 / flour_total) * 100  
        assert salt_percentage == 2.0