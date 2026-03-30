#!/usr/bin/env python3
"""
Demo script to test the recipe versioning integration
This simulates the complete workflow from frontend to backend
"""

import json
import uuid
from datetime import datetime

# Import our backend components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from recipe_versioning import (
    generate_ingredient_ids, 
    generate_step_ids, 
    calculate_bakers_percentages,
    compare_ingredients,
    compare_instructions,
    determine_next_version
)

def simulate_frontend_recipe_creation():
    """Simulate a user creating a recipe in the frontend"""
    
    print("🍞 Recipe Integration Test Demo")
    print("=" * 50)
    
    # Step 1: User fills out recipe form in RecipeTab.tsx
    frontend_form_data = {
        "name": "Country Sourdough",
        "description": "High hydration sourdough with overnight proof",
        "category": "sourdough",
        "ingredients": [
            {
                "name": "bread flour",
                "amount": 1000,
                "unit": "grams",
                "type": "flour",
                "notes": "King Arthur bread flour"
            },
            {
                "name": "water",
                "amount": 750,
                "unit": "grams",
                "type": "liquid", 
                "notes": "filtered water, room temperature"
            },
            {
                "name": "levain",
                "amount": 200,
                "unit": "grams",
                "type": "preferment",
                "notes": "100% hydration starter, ripe"
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
                "instruction": "Add levain and salt, mix thoroughly until combined"
            },
            {
                "order": 3,
                "instruction": "Bulk ferment for 4 hours with coil folds every 30 minutes for first 2 hours"
            },
            {
                "order": 4,
                "instruction": "Pre-shape into loose round, rest 30 minutes"
            },
            {
                "order": 5,
                "instruction": "Final shape into boule, place seam-side up in banneton"
            },
            {
                "order": 6,
                "instruction": "Proof overnight in refrigerator (12-18 hours)"
            },
            {
                "order": 7,
                "instruction": "Bake in Dutch oven at 450°F, 30 min covered + 15 min uncovered"
            }
        ]
    }
    
    print("✅ Frontend form data created:")
    print(f"   Name: {frontend_form_data['name']}")
    print(f"   Ingredients: {len(frontend_form_data['ingredients'])}")
    print(f"   Instructions: {len(frontend_form_data['instructions'])}")
    print()
    
    # Step 2: Frontend sends data to backend API
    print("📡 Sending to backend API...")
    
    # Step 3: Backend processes the data
    recipe_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    
    # Generate IDs for ingredients and steps
    ingredients_with_ids = generate_ingredient_ids(frontend_form_data['ingredients'])
    instructions_with_ids = generate_step_ids(frontend_form_data['instructions'])
    
    print("✅ Backend processing:")
    print(f"   Generated recipe ID: {recipe_id[:8]}...")
    print(f"   Generated version ID: {version_id[:8]}...")
    print(f"   Added IDs to {len(ingredients_with_ids)} ingredients")
    print(f"   Added IDs to {len(instructions_with_ids)} instructions")
    print()
    
    # Step 4: Calculate baker's percentages
    bakers_percentages = calculate_bakers_percentages(ingredients_with_ids)
    
    print("🧮 Baker's percentages calculated:")
    print(f"   Total flour weight: {bakers_percentages['total_flour_weight']}g")
    
    for flour in bakers_percentages['flour_ingredients']:
        print(f"   {flour['name']}: {flour['percentage']:.1f}% ({flour['amount']}g)")
    
    print("   Other ingredients:")
    for other in bakers_percentages['other_ingredients']:
        print(f"   {other['name']}: {other['percentage']:.1f}% ({other['amount']}g)")
    print()
    
    # Step 5: Simulate backend response
    backend_response = {
        "id": recipe_id,
        "name": frontend_form_data['name'],
        "description": frontend_form_data['description'],
        "category": frontend_form_data['category'],
        "current_version_id": version_id,
        "current_version": {
            "id": version_id,
            "recipe_id": recipe_id,
            "version_major": 1,
            "version_minor": 0,
            "description": "Initial version",
            "ingredients": ingredients_with_ids,
            "instructions": instructions_with_ids,
            "created_at": datetime.now().isoformat()
        },
        "bakers_percentages": bakers_percentages,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    print("✅ Backend response created (v1.0)")
    print()
    
    return backend_response

def simulate_recipe_update(original_recipe):
    """Simulate updating a recipe to test versioning"""
    
    print("📝 Simulating recipe update...")
    print("=" * 30)
    
    # User modifies the recipe in frontend
    updated_form_data = {
        "name": original_recipe['name'],
        "description": original_recipe['description'], 
        "category": original_recipe['category'],
        "ingredients": [
            # Keep flour the same
            original_recipe['current_version']['ingredients'][0],
            # Increase hydration: 750g → 800g water
            {
                **original_recipe['current_version']['ingredients'][1],
                "amount": 800  # Changed from 750
            },
            # Keep levain the same
            original_recipe['current_version']['ingredients'][2],
            # Keep salt the same  
            original_recipe['current_version']['ingredients'][3]
        ],
        "instructions": original_recipe['current_version']['instructions']
    }
    
    print(f"🔧 User changed water amount: 750g → 800g (hydration: 75% → 80%)")
    print()
    
    # Backend detects changes
    old_ingredients = original_recipe['current_version']['ingredients']
    new_ingredients = updated_form_data['ingredients']
    
    ingredient_diff = compare_ingredients(old_ingredients, new_ingredients)
    step_diff = compare_instructions(
        original_recipe['current_version']['instructions'],
        updated_form_data['instructions']
    )
    
    print("🔍 Change detection:")
    print(f"   Modified ingredients: {len(ingredient_diff['modified'])}")
    print(f"   Added ingredients: {len(ingredient_diff['added'])}")
    print(f"   Removed ingredients: {len(ingredient_diff['removed'])}")
    
    if ingredient_diff['modified']:
        for change in ingredient_diff['modified']:
            old_ing = change['old']
            new_ing = change['new']
            print(f"   - {old_ing['name']}: {old_ing['amount']}g → {new_ing['amount']}g")
    
    print()
    
    # Determine next version
    current_major = original_recipe['current_version']['version_major']
    current_minor = original_recipe['current_version']['version_minor']
    next_major, next_minor = determine_next_version(current_major, current_minor, force_major=False)
    
    print(f"📈 Version bump: v{current_major}.{current_minor} → v{next_major}.{next_minor}")
    print()
    
    # Calculate new baker's percentages
    new_bakers_percentages = calculate_bakers_percentages(new_ingredients)
    
    print("🧮 Updated baker's percentages:")
    for other in new_bakers_percentages['other_ingredients']:
        if other['name'] == 'water':
            print(f"   Hydration: {other['percentage']:.1f}% (was 75%)")
    
    return {
        "version_major": next_major,
        "version_minor": next_minor,
        "changes_detected": len(ingredient_diff['modified']) > 0,
        "new_hydration": new_bakers_percentages['other_ingredients'][0]['percentage']
    }

def main():
    """Run the complete integration demo"""
    
    # Test 1: Create new recipe
    recipe = simulate_frontend_recipe_creation()
    
    print("🎉 Recipe created successfully!")
    print(f"   Recipe ID: {recipe['id'][:8]}...")
    print(f"   Version: v{recipe['current_version']['version_major']}.{recipe['current_version']['version_minor']}")
    print(f"   Hydration: {recipe['bakers_percentages']['other_ingredients'][0]['percentage']:.1f}%")
    print()
    
    # Test 2: Update recipe
    update_result = simulate_recipe_update(recipe)
    
    print("🎉 Recipe updated successfully!")
    print(f"   New version: v{update_result['version_major']}.{update_result['version_minor']}")
    print(f"   Changes detected: {update_result['changes_detected']}")
    print(f"   New hydration: {update_result['new_hydration']:.1f}%")
    print()
    
    print("✅ Integration test completed successfully!")
    print("\n🚀 Ready for frontend integration!")

if __name__ == "__main__":
    main()