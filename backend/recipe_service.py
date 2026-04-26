"""
Recipe service layer with versioning logic
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from .db import DBConnector
from .models import (
  Recipe,
  RecipeRequest,
  RecipeVersion,
  RecipeListItem,
  Ingredient,
  RecipeStep,
)
from .recipe_versioning import (
  compare_ingredients,
  compare_instructions,
  create_version_summary,
  calculate_bakers_percentages,
  generate_step_ids,
  generate_ingredient_ids,
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
    ingredients_with_ids = generate_ingredient_ids(
      [ing.model_dump() for ing in recipe_request.ingredients]
    )
    instructions_with_ids = generate_step_ids(
      [step.model_dump() for step in recipe_request.instructions]
    )

    # Calculate baker's percentages
    bakers_percentages = calculate_bakers_percentages(ingredients_with_ids)

    # Prepare data for database
    recipe_data = {
      "id": recipe_id,
      "name": recipe_request.name,
      "description": recipe_request.description,
      "category": recipe_request.category,
      "version_id": version_id,
      "version_description": "Initial version",
      "ingredients": ingredients_with_ids,
      "instructions": instructions_with_ids,
      "bakers_percentages": bakers_percentages,
      "bp_id": bp_id,
    }

    # Create in database
    self.db.create_versioned_recipe(recipe_data)

    # Return the created recipe
    created_recipe = self.get_recipe(recipe_id)
    if not created_recipe:
      raise ValueError(f"Failed to retrieve created recipe {recipe_id}")
    return created_recipe

  def get_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
    """
    Get a recipe by ID with current version and baker's percentages
    """
    return self.db.get_versioned_recipe(recipe_id)

  def list_recipes(
    self,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_direction: str = "desc",
    ingredient: Optional[str] = None,
  ) -> List[RecipeListItem]:
    return self.db.list_recipes(
      category=category,
      limit=limit,
      offset=offset,
      search=search,
      sort_by=sort_by,
      sort_direction=sort_direction,
      ingredient=ingredient,
    )

  def create_recipe_version(
    self,
    recipe_id: UUID,
    ingredients: List[Ingredient],
    instructions: List[RecipeStep],
    description: Optional[str] = None,
    force_major: bool = False,
  ) -> Recipe:
    """
    Manually create a new version of a recipe
    """
    current_recipe = self.get_recipe(recipe_id)
    if not current_recipe:
      raise ValueError(f"Recipe {recipe_id} not found")

    new_ingredients_data = generate_ingredient_ids(
      [ing.model_dump() for ing in ingredients]
    )
    new_instructions_data = generate_step_ids(
      [step.model_dump() for step in instructions]
    )

    # Compare with current version
    current_ingredients = [
      ing.model_dump() for ing in current_recipe.current_version.ingredients
    ]
    current_instructions = [
      step.model_dump() for step in current_recipe.current_version.instructions
    ]

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
      force_major=force_major,
    )

  def get_recipe_versions(self, recipe_id: UUID) -> List[RecipeVersion]:
    """
    Get all versions of a recipe
    """
    return self.db.get_recipe_versions(recipe_id)

  def get_recipe_version_diff(
    self, version_id_1: UUID, version_id_2: UUID
  ) -> Dict[str, Any]:
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
      "from_version": str(version_1.version_number),
      "to_version": str(version_2.version_number),
      "ingredient_changes": ingredient_diff,
      "step_changes": step_diff,
      "created_at": version_2.created_at,
    }

  def _create_recipe_version(
    self,
    recipe_id: UUID,
    current_version: RecipeVersion,
    new_ingredients: List[Dict],
    new_instructions: List[Dict],
    ingredient_diff: Dict,
    step_diff: Dict,
    description: Optional[str] = None,
    force_major: bool = False,
  ) -> Recipe:
    """
    Internal method to create a new recipe version
    """
    version_id = uuid.uuid4()
    bp_id = uuid.uuid4()

    # Determine next version number
    next_version_number = current_version.version_number + 1

    # Calculate baker's percentages
    bakers_percentages = calculate_bakers_percentages(new_ingredients)

    # Create version summary
    change_summary = create_version_summary(ingredient_diff, step_diff)

    # Prepare version data
    version_data = {
      "id": version_id,
      "recipe_id": recipe_id,
      "version_number": next_version_number,
      "description": description or f"Auto-save v{next_version_number}",
      "ingredients": new_ingredients,
      "instructions": new_instructions,
      "change_summary": change_summary,
      "bakers_percentages": bakers_percentages,
      "bp_id": bp_id,
    }

    # Create in database
    self.db.create_recipe_version(version_data)

    # Return updated recipe
    updated_recipe = self.get_recipe(recipe_id)
    if not updated_recipe:
      raise ValueError(f"Failed to retrieve updated recipe {recipe_id}")
    return updated_recipe

  def update_recipe_full(self, recipe_id: UUID, recipe_data: RecipeRequest) -> Recipe:
    """
    Update a recipe with complete new data - creates new version and updates current_version_id
    This implements the PATCH endpoint specification for full recipe updates.

    Steps:
    1. Get current recipe and version
    2. Create new version with incremented version_number
    3. Update current_version_id and updated_at in recipes table
    4. Recalculate baker's percentages if ingredients changed
    """
    # Get current recipe
    current_recipe = self.get_recipe(recipe_id)
    if not current_recipe:
      raise ValueError(f"Recipe with ID {recipe_id} not found")

    current_version = current_recipe.current_version

    # Prepare new ingredients and instructions with IDs
    new_ingredients = [ingredient.dict() for ingredient in recipe_data.ingredients]
    new_instructions = [instruction.dict() for instruction in recipe_data.instructions]

    # Add IDs if not present
    new_ingredients = generate_ingredient_ids(new_ingredients)
    new_instructions = generate_step_ids(new_instructions)

    # Compare with current version to detect changes
    current_ingredients = [
      ingredient.dict() for ingredient in current_version.ingredients
    ]
    current_instructions = [
      instruction.dict() for instruction in current_version.instructions
    ]

    ingredient_diff = compare_ingredients(current_ingredients, new_ingredients)
    step_diff = compare_instructions(current_instructions, new_instructions)

    # Create new version - this returns the updated recipe with new current_version_id
    self._create_recipe_version(
      recipe_id=recipe_id,
      current_version=current_version,
      new_ingredients=new_ingredients,
      new_instructions=new_instructions,
      ingredient_diff=ingredient_diff,
      step_diff=step_diff,
      description=recipe_data.description,
    )

    # Update basic recipe fields (name, description, category, updated_at)
    # Note: current_version_id is already updated by _create_recipe_version
    self.db.update_recipe_basic_fields(
      recipe_id,
      {
        "name": recipe_data.name,
        "description": recipe_data.description,
        "category": recipe_data.category,
        "updated_at": datetime.now(),
      },
    )

    # Return the updated recipe
    final_recipe = self.get_recipe(recipe_id)
    if not final_recipe:
      raise ValueError(f"Failed to retrieve updated recipe {recipe_id}")
    return final_recipe

  def delete_recipe(self, recipe_id: UUID) -> bool:
    """
    Delete a recipe and all its associated data (versions, baker's percentages)
    Returns True if successful, False if recipe not found
    """
    # Check if recipe exists first
    existing_recipe = self.get_recipe(recipe_id)
    if not existing_recipe:
      raise ValueError(f"Recipe with ID {recipe_id} not found")

    # Delete from database - CASCADE should handle versions and baker's percentages
    success = self.db.delete_recipe(recipe_id)
    return success
