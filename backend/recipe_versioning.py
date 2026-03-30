"""
Recipe versioning service with ingredient matching and version management
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from .models import Ingredient, RecipeStep, IngredientDiff, StepDiff, RecipeVersionDiff


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient name by removing whitespace and converting to lowercase
    """
    return re.sub(r'\s+', '', name.lower().strip())


def ingredients_equal(ing1: Dict, ing2: Dict) -> bool:
    """
    Check if two ingredients are equal in all properties except ID
    """
    return (ing1["amount"] == ing2["amount"] and
            ing1["unit"] == ing2["unit"] and
            ing1.get("notes") == ing2.get("notes") and
            ing1.get("type") == ing2.get("type"))


def compare_ingredients(old_ingredients: List[Dict], new_ingredients: List[Dict]) -> Dict:
    """
    Compare two ingredient lists and return differences using name-based matching
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


def calculate_step_similarity(old_step: str, new_step: str) -> Dict:
    """
    Calculate similarity between two recipe steps using content similarity
    """
    if old_step == new_step:
        return {"similarity": 1.0, "change_type": "identical", "changes": []}
    
    # Tokenize and normalize
    old_tokens = set(re.findall(r'\b\w+\b', old_step.lower()))
    new_tokens = set(re.findall(r'\b\w+\b', new_step.lower()))
    
    # Calculate Jaccard similarity
    if not old_tokens and not new_tokens:
        similarity = 1.0
    elif not old_tokens or not new_tokens:
        similarity = 0.0
    else:
        intersection = old_tokens.intersection(new_tokens)
        union = old_tokens.union(new_tokens)
        similarity = len(intersection) / len(union)
    
    # Detect specific changes
    changes = []
    
    # Time pattern changes
    time_regex = r'(\d+)\s*(hours?|minutes?|mins?)'
    old_times = re.findall(time_regex, old_step, re.IGNORECASE)
    new_times = re.findall(time_regex, new_step, re.IGNORECASE)
    if old_times != new_times:
        old_time_str = ' '.join([f"{num} {unit}" for num, unit in old_times])
        new_time_str = ' '.join([f"{num} {unit}" for num, unit in new_times])
        if old_time_str != new_time_str:
            changes.append(f"Timing changed: {old_time_str} → {new_time_str}")
    
    # Temperature pattern changes  
    temp_regex = r'(\d+)\s*°?[FC]'
    old_temps = re.findall(temp_regex, old_step, re.IGNORECASE)
    new_temps = re.findall(temp_regex, new_step, re.IGNORECASE)
    if old_temps != new_temps:
        old_temp_str = ', '.join([f"{temp}°" for temp in old_temps])
        new_temp_str = ', '.join([f"{temp}°" for temp in new_temps])
        if old_temp_str != new_temp_str:
            changes.append(f"Temperature changed: {old_temp_str} → {new_temp_str}")
    
    # Classify change type
    if similarity > 0.7:
        change_type = "modified"
    else:
        change_type = "completely_different"
    
    return {"similarity": similarity, "change_type": change_type, "changes": changes}


def compare_instructions(old_instructions: List[Dict], new_instructions: List[Dict]) -> Dict:
    """
    Compare two instruction lists and return differences
    Uses step IDs when available, falls back to content similarity
    """
    result = {
        "added": [],
        "removed": [],
        "modified": [],
        "reordered": [],
        "unchanged": []
    }
    
    # Create maps for lookup
    old_by_id = {step.get("id"): step for step in old_instructions if step.get("id")}
    new_by_id = {step.get("id"): step for step in new_instructions if step.get("id")}
    
    # Track which steps we've matched
    matched_old_ids = set()
    matched_new_ids = set()
    
    # First pass: match by ID
    for step_id, old_step in old_by_id.items():
        new_step = new_by_id.get(step_id)
        if new_step:
            matched_old_ids.add(step_id)
            matched_new_ids.add(step_id)
            
            if old_step["instruction"] == new_step["instruction"]:
                if old_step.get("order") == new_step.get("order"):
                    result["unchanged"].append(new_step)
                else:
                    result["reordered"].append({
                        "step_id": step_id,
                        "old_order": old_step.get("order"),
                        "new_order": new_step.get("order")
                    })
            else:
                result["modified"].append({"old": old_step, "new": new_step})
    
    # Second pass: handle unmatched steps (added/removed)
    for old_step in old_instructions:
        step_id = old_step.get("id")
        if step_id not in matched_old_ids:
            result["removed"].append(old_step)
    
    for new_step in new_instructions:
        step_id = new_step.get("id")
        if step_id not in matched_new_ids:
            result["added"].append(new_step)
    
    return result


def generate_step_ids(instructions: List[Dict]) -> List[Dict]:
    """
    Generate IDs for instructions that don't have them
    """
    updated_instructions = []
    for instruction in instructions:
        if not instruction.get("id"):
            instruction["id"] = str(uuid.uuid4())
        updated_instructions.append(instruction)
    return updated_instructions


def generate_ingredient_ids(ingredients: List[Dict]) -> List[Dict]:
    """
    Generate IDs for ingredients that don't have them
    """
    updated_ingredients = []
    for ingredient in ingredients:
        if not ingredient.get("id"):
            ingredient["id"] = str(uuid.uuid4())
        updated_ingredients.append(ingredient)
    return updated_ingredients


def determine_next_version(current_major: int, current_minor: int, force_major: bool = False) -> Tuple[int, int]:
    """
    Determine the next version number
    """
    if force_major:
        return current_major + 1, 0
    else:
        return current_major, current_minor + 1


def create_version_summary(ingredient_diff: Dict, step_diff: Dict) -> Dict:
    """
    Create a summary of changes for version metadata
    """
    summary = {
        "ingredients": {
            "added": len(ingredient_diff["added"]),
            "removed": len(ingredient_diff["removed"]), 
            "modified": len(ingredient_diff["modified"])
        },
        "steps": {
            "added": len(step_diff["added"]),
            "removed": len(step_diff["removed"]),
            "modified": len(step_diff["modified"]),
            "reordered": len(step_diff["reordered"])
        },
        "total_changes": (
            len(ingredient_diff["added"]) + len(ingredient_diff["removed"]) + 
            len(ingredient_diff["modified"]) + len(step_diff["added"]) + 
            len(step_diff["removed"]) + len(step_diff["modified"]) + 
            len(step_diff["reordered"])
        )
    }
    return summary


def calculate_bakers_percentages(ingredients: List[Dict]) -> Dict:
    """
    Calculate baker's percentages from ingredients list
    """
    # Find all flour ingredients
    flour_ingredients = [ing for ing in ingredients if ing.get("type") == "flour"]
    other_ingredients = [ing for ing in ingredients if ing.get("type") != "flour"]
    
    # Calculate total flour weight
    total_flour_weight = sum(ing["amount"] for ing in flour_ingredients)
    
    if total_flour_weight == 0:
        # Default to 1000g if no flour found
        total_flour_weight = 1000
    
    # Calculate percentages for flour ingredients
    flour_with_percentages = []
    for ing in flour_ingredients:
        percentage = (ing["amount"] / total_flour_weight) * 100 if total_flour_weight > 0 else 100
        flour_with_percentages.append({
            "ingredient_id": ing.get("id"),
            "name": ing["name"],
            "amount": ing["amount"],
            "percentage": round(percentage, 1)
        })
    
    # Calculate percentages for other ingredients relative to flour
    other_with_percentages = []
    for ing in other_ingredients:
        percentage = (ing["amount"] / total_flour_weight) * 100 if total_flour_weight > 0 else 0
        other_with_percentages.append({
            "ingredient_id": ing.get("id"),
            "name": ing["name"],
            "amount": ing["amount"],
            "percentage": round(percentage, 1)
        })
    
    return {
        "total_flour_weight": total_flour_weight,
        "flour_ingredients": flour_with_percentages,
        "other_ingredients": other_with_percentages
    }


def has_meaningful_changes(ingredient_diff: Dict, step_diff: Dict) -> bool:
    """
    Determine if there are meaningful changes that warrant a new version
    """
    total_changes = (
        len(ingredient_diff["added"]) + len(ingredient_diff["removed"]) + 
        len(ingredient_diff["modified"]) + len(step_diff["added"]) + 
        len(step_diff["removed"]) + len(step_diff["modified"]) + 
        len(step_diff["reordered"])
    )
    return total_changes > 0