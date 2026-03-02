"""
Tests for name-based ingredient matching functionality
"""
import pytest
import re
import copy
from typing import List, Dict, Any


class TestIngredientNormalization:
    """Test cases for ingredient name normalization"""
    
    def test_normalize_removes_whitespace(self):
        """Test that normalization removes all whitespace"""
        assert normalize_ingredient_name("bread flour") == "breadflour"
        assert normalize_ingredient_name("bread  flour") == "breadflour"
        assert normalize_ingredient_name("bread\t\nflour") == "breadflour"
        assert normalize_ingredient_name("  bread flour  ") == "breadflour"
    
    def test_normalize_converts_to_lowercase(self):
        """Test that normalization converts to lowercase"""
        assert normalize_ingredient_name("BREAD FLOUR") == "breadflour"
        assert normalize_ingredient_name("Bread Flour") == "breadflour"
        assert normalize_ingredient_name("BrEaD fLoUr") == "breadflour"
    
    def test_normalize_handles_special_characters(self):
        """Test normalization with special characters"""
        assert normalize_ingredient_name("whole-wheat flour") == "whole-wheatflour"
        assert normalize_ingredient_name("salt (fine)") == "salt(fine)"
        assert normalize_ingredient_name("olive oil, extra virgin") == "oliveoil,extravirgin"
    
    def test_normalize_empty_and_edge_cases(self):
        """Test normalization edge cases"""
        assert normalize_ingredient_name("") == ""
        assert normalize_ingredient_name("   ") == ""
        assert normalize_ingredient_name("a") == "a"


class TestIngredientMatching:
    """Test cases for name-based ingredient matching"""
    
    def test_detect_modified_ingredient_amount(self, sample_ingredients):
        """Test detecting ingredient amount changes"""
        # Given: Original ingredients
        old_ingredients = copy.deepcopy(sample_ingredients)
        
        # When: Water amount changes from 750g to 800g
        new_ingredients = copy.deepcopy(sample_ingredients)
        for ing in new_ingredients:
            if ing["name"] == "water":
                ing["amount"] = 800
        
        # Then: Should detect modification
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["amount"] == 750
        assert diff["modified"][0]["new"]["amount"] == 800
        assert diff["modified"][0]["old"]["name"] == "water"
    
    def test_detect_ingredient_with_different_whitespace(self):
        """Test matching ingredients with different whitespace"""
        # Given: Ingredients with different whitespace
        old_ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"}
        ]
        new_ingredients = [
            {"id": "2", "name": "bread  flour", "amount": 1000, "unit": "grams", "type": "flour"}  # Extra space
        ]
        
        # When: Comparing ingredients
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        # Then: Should be detected as unchanged (same ingredient)
        assert len(diff["unchanged"]) == 1
        assert len(diff["added"]) == 0
        assert len(diff["removed"]) == 0
        assert len(diff["modified"]) == 0
    
    def test_detect_ingredient_case_variations(self):
        """Test matching ingredients with case variations"""
        old_ingredients = [
            {"id": "1", "name": "Bread Flour", "amount": 1000, "unit": "grams", "type": "flour"}
        ]
        new_ingredients = [
            {"id": "2", "name": "BREAD FLOUR", "amount": 1000, "unit": "grams", "type": "flour"}
        ]
        
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["unchanged"]) == 1
        assert len(diff["added"]) == 0
        assert len(diff["removed"]) == 0
    
    def test_detect_added_ingredient(self, sample_ingredients):
        """Test detecting new ingredients"""
        # Given: Original ingredients
        old_ingredients = copy.deepcopy(sample_ingredients)
        
        # When: Adding olive oil
        new_ingredients = copy.deepcopy(sample_ingredients)
        new_ingredients.append({
            "id": "new_1",
            "name": "olive oil",
            "amount": 50,
            "unit": "grams",
            "type": "fat"
        })
        
        # Then: Should detect addition
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["added"]) == 1
        assert diff["added"][0]["name"] == "olive oil"
        assert diff["added"][0]["amount"] == 50
    
    def test_detect_removed_ingredient(self, sample_ingredients):
        """Test detecting removed ingredients"""
        # Given: Original ingredients
        old_ingredients = sample_ingredients.copy()
        
        # When: Removing salt
        new_ingredients = [ing for ing in sample_ingredients if ing["name"] != "salt"]
        
        # Then: Should detect removal
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["removed"]) == 1
        assert diff["removed"][0]["name"] == "salt"
    
    def test_detect_ingredient_unit_change(self, sample_ingredients):
        """Test detecting unit changes as modifications"""
        # Given: Original ingredients
        old_ingredients = copy.deepcopy(sample_ingredients)
        
        # When: Water unit changes from grams to ml with amount adjustment
        new_ingredients = copy.deepcopy(sample_ingredients)
        for ing in new_ingredients:
            if ing["name"] == "water":
                ing["unit"] = "ml"
                ing["amount"] = 750  # Same volume, different unit
        
        # Then: Should detect modification
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["unit"] == "grams"
        assert diff["modified"][0]["new"]["unit"] == "ml"
    
    def test_detect_ingredient_notes_change(self, sample_ingredients):
        """Test detecting notes changes as modifications"""
        old_ingredients = copy.deepcopy(sample_ingredients)
        
        new_ingredients = copy.deepcopy(sample_ingredients)
        for ing in new_ingredients:
            if ing["name"] == "bread flour":
                ing["notes"] = "organic high protein flour"  # Changed notes
        
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["old"]["notes"] == "high protein flour"
        assert diff["modified"][0]["new"]["notes"] == "organic high protein flour"
    
    def test_complex_ingredient_changes(self, sample_ingredients):
        """Test multiple types of changes at once"""
        # Given: Original ingredients
        old_ingredients = copy.deepcopy(sample_ingredients)
        
        # When: Multiple changes
        new_ingredients = []
        for ing in sample_ingredients:
            if ing["name"] == "water":
                # Modify water amount
                new_ing = copy.deepcopy(ing)
                new_ing["amount"] = 800
                new_ingredients.append(new_ing)
            elif ing["name"] == "salt":
                # Remove salt (don't add to new_ingredients)
                continue
            else:
                # Keep others unchanged
                new_ingredients.append(copy.deepcopy(ing))
        
        # Add new ingredient
        new_ingredients.append({
            "id": "new_1",
            "name": "olive oil",
            "amount": 50,
            "unit": "grams",
            "type": "fat"
        })
        
        # Then: Should detect all change types
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        assert len(diff["modified"]) == 1  # water
        assert len(diff["removed"]) == 1   # salt
        assert len(diff["added"]) == 1     # olive oil
        assert len(diff["unchanged"]) == 2 # bread flour, levain
    
    def test_similar_ingredient_names_not_matched(self):
        """Test that similar but different ingredients are not matched"""
        old_ingredients = [
            {"id": "1", "name": "bread flour", "amount": 1000, "unit": "grams", "type": "flour"}
        ]
        new_ingredients = [
            {"id": "2", "name": "whole wheat flour", "amount": 1000, "unit": "grams", "type": "flour"}
        ]
        
        diff = compare_ingredients(old_ingredients, new_ingredients)
        
        # Should be treated as remove + add, not modification
        assert len(diff["removed"]) == 1
        assert len(diff["added"]) == 1
        assert len(diff["modified"]) == 0
        assert len(diff["unchanged"]) == 0


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient name by removing whitespace and converting to lowercase
    """
    return re.sub(r'\s+', '', name.lower().strip())


def compare_ingredients(old_ingredients: List[Dict], new_ingredients: List[Dict]) -> Dict:
    """
    Compare two ingredient lists and return differences
    Mock implementation for testing
    """
    result = {
        "added": [],
        "removed": [],
        "modified": [],
        "unchanged": []
    }
    
    # Create maps for efficient lookup
    old_map = {normalize_ingredient_name(ing["name"]): ing for ing in old_ingredients}
    new_map = {normalize_ingredient_name(ing["name"]): ing for ing in new_ingredients}
    
    # Find modified and unchanged ingredients
    for normalized_name, old_ing in old_map.items():
        new_ing = new_map.get(normalized_name)
        
        if new_ing:
            if ingredients_equal(old_ing, new_ing):
                result["unchanged"].append(new_ing)
            else:
                result["modified"].append({"old": old_ing, "new": new_ing})
        else:
            result["removed"].append(old_ing)
    
    # Find added ingredients
    for normalized_name, new_ing in new_map.items():
        if normalized_name not in old_map:
            result["added"].append(new_ing)
    
    return result


def ingredients_equal(ing1: Dict, ing2: Dict) -> bool:
    """
    Check if two ingredients are equal in all properties except ID
    """
    return (ing1["amount"] == ing2["amount"] and
            ing1["unit"] == ing2["unit"] and
            ing1.get("notes") == ing2.get("notes") and
            ing1.get("type") == ing2.get("type"))