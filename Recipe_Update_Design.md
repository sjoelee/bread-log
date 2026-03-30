# Recipe Viewing and Updating Design Document

## Overview
This document outlines the technical design for viewing and updating existing recipes, including the complete data retrieval flow and versioned update process with proper transaction management.

## Frontend User Flow

### Recipe Viewing Flow
1. User navigates to Saved recipes tab
2. User clicks "View & Edit" button on a specific recipe
3. Frontend makes GET request to `/recipes/{recipe_id}` 
4. Backend retrieves complete recipe data from all related tables
5. Frontend populates the recipe form with existing data
6. User can view current recipe details and baker's percentages

### Recipe Updating Flow  
1. User modifies any fields in the loaded recipe form (name, description, category, ingredients, instructions)
2. User clicks "Update" button
3. Frontend collects all form data and sends PATCH request to `/recipes/{recipe_id}`
4. Backend processes update in single transaction:
   - Determines what fields changed
   - Creates new recipe version (increments version_number)
   - Updates recipe with new current_version_id
   - Recalculates baker's percentages if ingredients changed
5. Frontend displays success message with new version number

## Backend Database Process for Recipe Retrieval

### GET /recipes/{recipe_id} - Complete Recipe Data Query

The backend must join multiple tables to return the complete recipe view:

```sql
-- Main query to get complete recipe with current version and percentages
SELECT 
    r.id,
    r.name,
    r.description,
    r.category,
    r.current_version_id,
    r.created_at,
    r.updated_at,
    
    -- Current version data
    rv.id as version_id,
    rv.version_number,
    rv.description as version_description,
    rv.ingredients,
    rv.instructions,
    rv.created_at as version_created_at,
    rv.change_summary,
    
    -- Baker's percentages
    bp.total_flour_weight,
    bp.flour_ingredients as flour_percentages,
    bp.other_ingredients as other_percentages

FROM recipes r
LEFT JOIN recipe_versions rv ON r.current_version_id = rv.id
LEFT JOIN bakers_percentages bp ON rv.id = bp.recipe_version_id
WHERE r.id = $1;
```

### Response Structure
The query returns complete recipe data that gets formatted into this response:

```json
{
  "id": "recipe_uuid",
  "name": "Artisan Sourdough",
  "description": "Traditional country sourdough",
  "category": "sourdough", 
  "current_version_id": "version_uuid",
  "current_version": {
    "id": "version_uuid",
    "recipe_id": "recipe_uuid",
    "version_number": 3,
    "description": "Updated hydration",
    "ingredients": [...],
    "instructions": [...],
    "created_at": "2024-01-15T14:30:00Z",
    "change_summary": {
      "changed_fields": ["ingredients"],
      "summary": "Increased water hydration from 75% to 80%"
    }
  },
  "bakers_percentages": {
    "total_flour_weight": 1000.0,
    "flour_ingredients": [...],
    "other_ingredients": [...]
  },
  "created_at": "2024-01-10T10:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

## Backend Database Process for Recipe Updating

### PATCH /recipes/{recipe_id} - Update Recipe Transaction

All update operations must be wrapped in a single database transaction:

```sql
BEGIN;
  -- Step 1: Get current version number for increment
  -- Step 2: Create new recipe version with updated data  
  -- Step 3: Update main recipe record with new current_version_id
  -- Step 4: Recalculate and store baker's percentages (if ingredients changed)
COMMIT;
-- If any step fails, ROLLBACK automatically
```

### Step 1: Get Current Version for Increment
```sql
-- Retrieve current version number to increment
SELECT rv.version_number
FROM recipes r
JOIN recipe_versions rv ON r.current_version_id = rv.id  
WHERE r.id = $1;
-- Result: current_version_number (e.g., 3)
```

### Step 2: Create New Recipe Version
```sql
-- Insert new version with incremented number and updated data
INSERT INTO recipe_versions (
    id,
    recipe_id, 
    version_number,
    description,
    ingredients,
    instructions,
    created_at,
    change_summary
)
VALUES (
    uuid_generate_v4(),
    $1,  -- recipe_id
    $2,  -- current_version_number + 1 (e.g., 4)
    $3,  -- version description (optional, can be auto-generated)
    $4,  -- updated ingredients JSONB
    $5,  -- updated instructions JSONB  
    NOW(),
    $6   -- change summary JSONB
)
RETURNING id as new_version_id;
```

### Step 3: Update Recipe with New Current Version
```sql
-- Update main recipe record
UPDATE recipes 
SET 
    name = COALESCE($1, name),                    -- Update only if provided
    description = COALESCE($2, description),      -- Update only if provided  
    category = COALESCE($3, category),            -- Update only if provided
    current_version_id = $4,                      -- New version ID (always updated)
    updated_at = NOW()
WHERE id = $5;  -- recipe_id
```

### Step 4: Update Baker's Percentages (if ingredients changed)
```sql
-- First, check if a percentages record exists for this version
-- If ingredients changed, recalculate and update/insert percentages

-- Option A: Update existing percentages record
UPDATE bakers_percentages 
SET 
    total_flour_weight = $1,
    flour_ingredients = $2,
    other_ingredients = $3,
    updated_at = NOW()
WHERE recipe_version_id = $4;

-- Option B: Insert new percentages record (if above UPDATE affected 0 rows)
INSERT INTO bakers_percentages (
    id, recipe_id, recipe_version_id, total_flour_weight,
    flour_ingredients, other_ingredients, created_at, updated_at
)
VALUES (
    uuid_generate_v4(), $1, $2, $3, $4, $5, NOW(), NOW()
);
```

## Backend Business Logic for Updates

### Change Detection Algorithm
```python
def detect_changes(original_data, updated_data):
    """Detect which fields have changed between original and updated recipe data"""
    
    changes = {
        "changed_fields": [],
        "ingredient_changes": [],
        "instruction_changes": [],
        "summary": ""
    }
    
    # Check basic field changes
    basic_fields = ["name", "description", "category"]
    for field in basic_fields:
        if original_data.get(field) != updated_data.get(field):
            changes["changed_fields"].append(field)
    
    # Check ingredient changes
    original_ingredients = original_data.get("ingredients", [])
    updated_ingredients = updated_data.get("ingredients", [])
    
    if ingredients_differ(original_ingredients, updated_ingredients):
        changes["changed_fields"].append("ingredients")
        changes["ingredient_changes"] = calculate_ingredient_diff(
            original_ingredients, updated_ingredients
        )
    
    # Check instruction changes  
    original_instructions = original_data.get("instructions", [])
    updated_instructions = updated_data.get("instructions", [])
    
    if instructions_differ(original_instructions, updated_instructions):
        changes["changed_fields"].append("instructions")
        changes["instruction_changes"] = calculate_instruction_diff(
            original_instructions, updated_instructions
        )
    
    # Generate summary
    changes["summary"] = generate_change_summary(changes)
    
    return changes

def ingredients_differ(original, updated):
    """Deep comparison of ingredient arrays"""
    if len(original) != len(updated):
        return True
    
    # Sort by name for comparison
    orig_sorted = sorted(original, key=lambda x: x.get("name", ""))
    upd_sorted = sorted(updated, key=lambda x: x.get("name", ""))
    
    for orig, upd in zip(orig_sorted, upd_sorted):
        # Compare relevant fields (ignore generated IDs)
        compare_fields = ["name", "amount", "unit", "type", "notes"]
        for field in compare_fields:
            if orig.get(field) != upd.get(field):
                return True
    
    return False
```

### Version Description Generation
```python
def generate_version_description(changes):
    """Auto-generate description for new version based on changes"""
    
    if not changes["changed_fields"]:
        return "No changes"
    
    descriptions = []
    
    if "name" in changes["changed_fields"]:
        descriptions.append("Updated recipe name")
    
    if "ingredients" in changes["changed_fields"]:
        if changes["ingredient_changes"]:
            descriptions.append(f"Modified {len(changes['ingredient_changes'])} ingredients")
        else:
            descriptions.append("Updated ingredients")
    
    if "instructions" in changes["changed_fields"]:
        descriptions.append("Updated instructions")
    
    if "category" in changes["changed_fields"]:
        descriptions.append("Changed category")
    
    if "description" in changes["changed_fields"]:
        descriptions.append("Updated description")
    
    return "; ".join(descriptions)
```

### Ingredient ID Preservation
```python
def preserve_ingredient_ids(original_ingredients, updated_ingredients):
    """Preserve existing ingredient IDs when possible, generate new ones for new ingredients"""
    
    # Create mapping of original ingredients by name for ID preservation
    original_by_name = {ing["name"]: ing for ing in original_ingredients}
    
    processed_ingredients = []
    for updated_ing in updated_ingredients:
        # If ingredient with same name exists, preserve its ID
        if updated_ing["name"] in original_by_name:
            original_ing = original_by_name[updated_ing["name"]]
            processed_ingredients.append({
                **updated_ing,
                "id": original_ing["id"]  # Preserve existing ID
            })
        else:
            # New ingredient - generate new ID
            processed_ingredients.append({
                **updated_ing,
                "id": generate_ingredient_id()
            })
    
    return processed_ingredients
```

## API Endpoint Specifications

### GET /recipes/{recipe_id}

**Purpose**: Retrieve complete recipe data for viewing/editing

**Path Parameters:**
- `recipe_id`: UUID of the recipe to retrieve

**Response (200 OK):**
```typescript
interface GetRecipeResponse {
  id: string;
  name: string;
  description?: string;
  category?: string;
  current_version_id: string;
  current_version: {
    id: string;
    recipe_id: string;
    version_number: number;
    description?: string;
    ingredients: Array<{
      id: string;
      name: string;
      amount: number;
      unit: string;
      type: string;
      notes?: string;
    }>;
    instructions: Array<{
      id: string;
      order: number;
      instruction: string;
    }>;
    created_at: string;
    change_summary?: {
      changed_fields: string[];
      summary: string;
      ingredient_changes?: any[];
      instruction_changes?: any[];
    };
  };
  bakers_percentages?: {
    total_flour_weight: number;
    flour_ingredients: Array<{
      ingredient_id: string;
      name: string;
      amount: number;
      percentage: number;
    }>;
    other_ingredients: Array<{
      ingredient_id: string;
      name: string;
      amount: number;
      percentage: number;
    }>;
  };
  created_at: string;
  updated_at: string;
}
```

**Error Responses:**
```typescript
// 404 Not Found
{
  "error": "Recipe not found",
  "recipe_id": "provided_uuid"
}

// 500 Internal Server Error
{
  "error": "Failed to retrieve recipe",
  "message": "Database error occurred"
}
```

### PATCH /recipes/{recipe_id}

**Purpose**: Update existing recipe with versioning

**Path Parameters:**
- `recipe_id`: UUID of the recipe to update

**Request Body** (all fields optional - only send what changed):
```typescript
interface UpdateRecipeRequest {
  name?: string;
  description?: string; 
  category?: 'sourdough' | 'enriched' | 'lean' | 'sweet' | 'other';
  ingredients?: Array<{
    id?: string;                   // Preserve existing IDs when possible
    name: string;
    amount: number;
    unit: string;
    type: string;
    notes?: string;
  }>;
  instructions?: Array<{
    id?: string;                   // Preserve existing IDs when possible
    order: number;
    instruction: string;
  }>;
  version_description?: string;    // Optional custom description for this version
}
```

**Response (200 OK):**
```typescript
interface UpdateRecipeResponse {
  id: string;
  name: string;
  description?: string;
  category?: string;
  current_version_id: string;     // New version ID
  current_version: {
    id: string;                   // New version ID
    recipe_id: string;
    version_number: number;       // Incremented version
    description?: string;
    ingredients: Array<{
      id: string;                 // Preserved or newly generated
      name: string;
      amount: number;
      unit: string;
      type: string;
      notes?: string;
    }>;
    instructions: Array<{
      id: string;                 // Preserved or newly generated
      order: number;
      instruction: string;
    }>;
    created_at: string;           // New version creation time
    change_summary: {
      changed_fields: string[];
      summary: string;
      ingredient_changes?: any[];
      instruction_changes?: any[];
    };
  };
  bakers_percentages?: {           // Recalculated if ingredients changed
    total_flour_weight: number;
    flour_ingredients: Array<{
      ingredient_id: string;
      name: string;
      amount: number;
      percentage: number;
    }>;
    other_ingredients: Array<{
      ingredient_id: string;
      name: string;
      amount: number;
      percentage: number;
    }>;
  };
  created_at: string;             // Original recipe creation time
  updated_at: string;             // Recipe last updated time (now)
  message: string;                // Success message with version info
}
```

**Error Responses:**
```typescript
// 404 Not Found
{
  "error": "Recipe not found",
  "recipe_id": "provided_uuid"
}

// 422 Unprocessable Entity - Validation Errors
{
  "error": "Validation failed",
  "details": {
    "ingredients[0].amount": ["Amount must be greater than 0"],
    "instructions": ["At least one instruction is required"]
  }
}

// 500 Internal Server Error
{
  "error": "Failed to update recipe",
  "message": "Database transaction failed"
}
```

## Database Transaction Implementation

### Python/FastAPI Example
```python
async def update_recipe(recipe_id: str, update_data: UpdateRecipeRequest, db: Session):
    try:
        # Begin transaction
        db.begin()
        
        # Step 1: Get current recipe and version data
        current_recipe = await get_current_recipe_with_version(db, recipe_id)
        if not current_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Step 2: Detect changes and generate change summary
        changes = detect_changes(current_recipe.current_version, update_data)
        if not changes["changed_fields"]:
            # No changes detected, return current data
            return current_recipe
        
        # Step 3: Create new version with incremented number
        new_version_number = current_recipe.current_version.version_number + 1
        version_description = update_data.version_description or generate_version_description(changes)
        
        new_version_id = await create_recipe_version(
            db=db,
            recipe_id=recipe_id,
            version_number=new_version_number, 
            description=version_description,
            ingredients=update_data.ingredients or current_recipe.current_version.ingredients,
            instructions=update_data.instructions or current_recipe.current_version.instructions,
            change_summary=changes
        )
        
        # Step 4: Update main recipe record  
        await update_recipe_record(
            db=db,
            recipe_id=recipe_id,
            name=update_data.name,
            description=update_data.description,
            category=update_data.category,
            current_version_id=new_version_id
        )
        
        # Step 5: Recalculate baker's percentages if ingredients changed
        if "ingredients" in changes["changed_fields"]:
            ingredients = update_data.ingredients or current_recipe.current_version.ingredients
            await update_bakers_percentages(db, recipe_id, new_version_id, ingredients)
        
        # Commit transaction
        db.commit()
        
        # Return complete updated recipe data
        return await get_complete_recipe(db, recipe_id)
        
    except Exception as e:
        # Rollback on any error
        db.rollback()
        logger.error(f"Failed to update recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update recipe")
```

## Frontend Integration Notes

### Loading Recipe for Editing
```typescript
// When user clicks "View & Edit"
const loadRecipeForEditing = async (recipeId: string) => {
  try {
    setLoading(true);
    const response = await fetch(`/api/recipes/${recipeId}`);
    
    if (!response.ok) {
      throw new Error('Failed to load recipe');
    }
    
    const recipe = await response.json();
    
    // Populate form with existing data
    setFormData({
      name: recipe.name,
      description: recipe.description || '',
      category: recipe.category || '',
      ingredients: recipe.current_version.ingredients,
      instructions: recipe.current_version.instructions
    });
    
    setEditingRecipe(recipe);
    setActiveTab('create'); // Switch to edit form
    
  } catch (error) {
    setError('Failed to load recipe for editing');
  } finally {
    setLoading(false);
  }
};
```

### Updating Recipe
```typescript
// When user clicks "Update"
const updateRecipe = async (recipeId: string, formData: RecipeFormData) => {
  try {
    setLoading(true);
    
    const response = await fetch(`/api/recipes/${recipeId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update recipe');
    }
    
    const updatedRecipe = await response.json();
    
    setSuccess(true);
    setSuccessMessage(`Recipe updated successfully! New version: v${updatedRecipe.current_version.version_number}`);
    
    // Refresh recipe list to show updates
    refreshSavedRecipes();
    
  } catch (error) {
    setError('Failed to update recipe');
  } finally {
    setLoading(false);
  }
};
```

This design ensures proper recipe viewing and updating with full versioning support, transaction safety, and comprehensive change tracking.