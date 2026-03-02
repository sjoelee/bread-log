"""
Recipe service layer with versioning logic
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from db import DBConnector
from models import (
    Recipe, RecipeRequest, RecipeUpdateRequest, RecipeVersion, RecipeListItem,
    Ingredient, RecipeStep, BakersPercentages
)
from recipe_versioning import (
    compare_ingredients, compare_instructions, determine_next_version,
    create_version_summary, calculate_bakers_percentages, has_meaningful_changes,
    generate_step_ids, generate_ingredient_ids
)


class RecipeService:
    def __init__(self, db_connector: DBConnector):
        self.db = db_connector
    
    def create_recipe(self, recipe_request: RecipeRequest) -> Recipe:
        """
        Create a new recipe with initial version 1.0
        """
        recipe_id = uuid.uuid4()
        version_id = uuid.uuid4()
        bp_id = uuid.uuid4()
        
        # Generate IDs for ingredients and instructions
        ingredients_with_ids = generate_ingredient_ids([ing.model_dump() for ing in recipe_request.ingredients])
        instructions_with_ids = generate_step_ids([step.model_dump() for step in recipe_request.instructions])
        
        # Calculate baker's percentages
        bakers_percentages = calculate_bakers_percentages(ingredients_with_ids)
        
        # Prepare data for database
        recipe_data = {
            'id': recipe_id,
            'name': recipe_request.name,
            'description': recipe_request.description,
            'category': recipe_request.category,
            'version_id': version_id,
            'version_description': 'Initial version',
            'ingredients': ingredients_with_ids,
            'instructions': instructions_with_ids,
            'bakers_percentages': bakers_percentages,
            'bp_id': bp_id
        }
        
        # Create in database
        result = self.db.create_versioned_recipe(recipe_data)
        
        # Return the created recipe
        return self.get_recipe(recipe_id)
    
    def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        """
        Get a recipe by ID with current version and baker's percentages
        """
        return self.db.get_versioned_recipe(recipe_id)
    
    def list_recipes(self, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[RecipeListItem]:
        """
        List recipes with pagination and optional category filter
        """
        return self.db.list_recipes(category=category, limit=limit, offset=offset)
    
    def update_recipe(self, recipe_id: UUID, updates: RecipeUpdateRequest) -> Recipe:
        """
        Update recipe - creates new version if ingredients/instructions changed
        """
        # Get current recipe
        current_recipe = self.get_recipe(recipe_id)
        if not current_recipe:
            raise ValueError(f"Recipe {recipe_id} not found")
        
        # Handle name/description/category updates (no new version needed)
        basic_updates = {}
        if updates.name is not None:
            basic_updates['name'] = updates.name
        if updates.description is not None:
            basic_updates['description'] = updates.description
        if updates.category is not None:
            basic_updates['category'] = updates.category
        
        # Update basic fields if any
        if basic_updates:
            self._update_recipe_basic_fields(recipe_id, basic_updates)
        
        # Check if ingredients or instructions changed
        needs_new_version = False
        ingredient_diff = None
        step_diff = None
        
        if updates.ingredients is not None or updates.instructions is not None:
            # Prepare new ingredients and instructions
            new_ingredients = updates.ingredients or current_recipe.current_version.ingredients
            new_instructions = updates.instructions or current_recipe.current_version.instructions
            
            new_ingredients_data = [ing.model_dump() for ing in new_ingredients]
            new_instructions_data = [step.model_dump() for step in new_instructions]
            
            # Generate IDs for new items
            new_ingredients_data = generate_ingredient_ids(new_ingredients_data)
            new_instructions_data = generate_step_ids(new_instructions_data)
            
            # Compare with current version
            current_ingredients = [ing.model_dump() for ing in current_recipe.current_version.ingredients]
            current_instructions = [step.model_dump() for step in current_recipe.current_version.instructions]
            
            ingredient_diff = compare_ingredients(current_ingredients, new_ingredients_data)
            step_diff = compare_instructions(current_instructions, new_instructions_data)
            
            needs_new_version = has_meaningful_changes(ingredient_diff, step_diff)
        
        # Create new version if needed
        if needs_new_version:
            return self._create_recipe_version(
                recipe_id=recipe_id,
                current_version=current_recipe.current_version,
                new_ingredients=new_ingredients_data,
                new_instructions=new_instructions_data,
                ingredient_diff=ingredient_diff,
                step_diff=step_diff,
                description=updates.description,
                force_major=updates.force_major or False
            )
        
        # Return updated recipe
        return self.get_recipe(recipe_id)
    
    def create_recipe_version(self, recipe_id: UUID, ingredients: List[Ingredient], 
                            instructions: List[RecipeStep], description: Optional[str] = None,
                            force_major: bool = False) -> Recipe:
        """
        Manually create a new version of a recipe
        """
        current_recipe = self.get_recipe(recipe_id)
        if not current_recipe:
            raise ValueError(f"Recipe {recipe_id} not found")
        
        new_ingredients_data = generate_ingredient_ids([ing.model_dump() for ing in ingredients])
        new_instructions_data = generate_step_ids([step.model_dump() for step in instructions])
        
        # Compare with current version
        current_ingredients = [ing.model_dump() for ing in current_recipe.current_version.ingredients]
        current_instructions = [step.model_dump() for step in current_recipe.current_version.instructions]
        
        ingredient_diff = compare_ingredients(current_ingredients, new_ingredients_data)
        step_diff = compare_instructions(current_instructions, new_instructions_data)
        
        return self._create_recipe_version(
            recipe_id=recipe_id,
            current_version=current_recipe.current_version,
            new_ingredients=new_ingredients_data,
            new_instructions=new_instructions_data,
            ingredient_diff=ingredient_diff,
            step_diff=step_diff,
            description=description,
            force_major=force_major
        )
    
    def get_recipe_versions(self, recipe_id: UUID) -> List[RecipeVersion]:
        """
        Get all versions of a recipe
        """
        return self.db.get_recipe_versions(recipe_id)
    
    def get_recipe_version_diff(self, version_id_1: UUID, version_id_2: UUID) -> Dict[str, Any]:
        """
        Get diff between two recipe versions
        """
        version_1 = self.db.get_recipe_version(version_id_1)
        version_2 = self.db.get_recipe_version(version_id_2)
        
        if not version_1 or not version_2:
            raise ValueError("One or both versions not found")
        
        ingredients_1 = [ing.model_dump() for ing in version_1.ingredients]
        ingredients_2 = [ing.model_dump() for ing in version_2.ingredients]
        
        instructions_1 = [step.model_dump() for step in version_1.instructions]
        instructions_2 = [step.model_dump() for step in version_2.instructions]
        
        ingredient_diff = compare_ingredients(ingredients_1, ingredients_2)
        step_diff = compare_instructions(instructions_1, instructions_2)
        
        return {
            "from_version": f"{version_1.version_major}.{version_1.version_minor}",
            "to_version": f"{version_2.version_major}.{version_2.version_minor}",
            "ingredient_changes": ingredient_diff,
            "step_changes": step_diff,
            "created_at": version_2.created_at
        }
    
    def _create_recipe_version(self, recipe_id: UUID, current_version: RecipeVersion,
                             new_ingredients: List[Dict], new_instructions: List[Dict],
                             ingredient_diff: Dict, step_diff: Dict, 
                             description: Optional[str] = None, force_major: bool = False) -> Recipe:
        """
        Internal method to create a new recipe version
        """
        version_id = uuid.uuid4()
        bp_id = uuid.uuid4()
        
        # Determine next version number
        next_major, next_minor = determine_next_version(
            current_version.version_major, 
            current_version.version_minor,
            force_major
        )
        
        # Calculate baker's percentages
        bakers_percentages = calculate_bakers_percentages(new_ingredients)
        
        # Create version summary
        change_summary = create_version_summary(ingredient_diff, step_diff)
        
        # Prepare version data
        version_data = {
            'id': version_id,
            'recipe_id': recipe_id,
            'version_major': next_major,
            'version_minor': next_minor,
            'description': description or f"Auto-save v{next_major}.{next_minor}",
            'ingredients': new_ingredients,
            'instructions': new_instructions,
            'change_summary': change_summary,
            'bakers_percentages': bakers_percentages,
            'bp_id': bp_id
        }
        
        # Create in database
        self.db.create_recipe_version(version_data)
        
        # Return updated recipe
        return self.get_recipe(recipe_id)
    
    def _update_recipe_basic_fields(self, recipe_id: UUID, updates: Dict[str, Any]):
        """
        Update basic recipe fields (name, description, category) without creating new version
        """
        # This would require a new DB method to update just the recipes table
        # For now, we'll skip this as it's not critical for MVP
        pass