# Recipe Creation Design Document

## Overview
This document outlines the technical design for the recipe creation feature, including the frontend flow, backend database operations, and transaction management.

## Frontend User Flow
1. User enters recipe name (required)
2. User enters description (optional) 
3. User selects category from dropdown (sourdough, enriched, lean, sweet, other)
4. User adds flour ingredients with amounts and units
5. User adds liquid ingredients with amounts, units, and liquid types
6. User enters step-by-step instructions in order
7. User clicks Save button
8. System displays success message with calculated baker's percentages

## Backend Database Process for Recipe Creation

### Database Transaction Flow
All recipe creation operations must be wrapped in a single database transaction to ensure atomicity:

```sql
BEGIN;
  -- Step 1: Create main recipe record
  -- Step 2: Create first recipe version
  -- Step 3: Update recipe with current_version_id pointer
  -- Step 4: Calculate and store baker's percentages
COMMIT;
-- If any step fails, ROLLBACK automatically
```

### Step 1: Create Main Recipe Record
```sql
INSERT INTO recipes (
    id, 
    name, 
    description, 
    category, 
    created_at, 
    updated_at
)
VALUES (
    uuid_generate_v4(),
    $1,  -- name (required)
    $2,  -- description (optional, can be NULL)
    $3,  -- category (optional, can be NULL)
    NOW(), 
    NOW()
)
RETURNING id as recipe_id;
```

### Step 2: Create First Recipe Version
```sql
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
    $1,  -- recipe_id from Step 1
    1,   -- First version
    'Initial version',
    $2,  -- ingredients as JSONB
    $3,  -- instructions as JSONB
    NOW(),
    '{}'::jsonb  -- Empty change summary for initial version
)
RETURNING id as version_id;
```

**Ingredients JSONB Structure:**
```json
[
  {
    "id": "ing_001",
    "name": "bread flour",
    "amount": 1000,
    "unit": "grams",
    "type": "flour",
    "notes": "high protein flour"
  },
  {
    "id": "ing_002", 
    "name": "water",
    "amount": 750,
    "unit": "grams",
    "type": "liquid",
    "notes": "filtered water"
  }
]
```

**Instructions JSONB Structure:**
```json
[
  {
    "id": "step_001",
    "order": 1,
    "instruction": "Autolyse flour and water for 30 minutes"
  },
  {
    "id": "step_002",
    "order": 2,
    "instruction": "Add levain and mix thoroughly"
  }
]
```

### Step 3: Update Recipe with Current Version Pointer
```sql
UPDATE recipes 
SET 
    current_version_id = $1,  -- version_id from Step 2
    updated_at = NOW()
WHERE id = $2;  -- recipe_id from Step 1
```

### Step 4: Calculate and Store Baker's Percentages
```sql
INSERT INTO bakers_percentages (
    id,
    recipe_id,
    recipe_version_id,
    total_flour_weight,
    flour_ingredients,
    other_ingredients,
    created_at,
    updated_at
)
VALUES (
    uuid_generate_v4(),
    $1,  -- recipe_id
    $2,  -- recipe_version_id
    $3,  -- calculated total flour weight
    $4,  -- flour ingredients with percentages as JSONB
    $5,  -- other ingredients with percentages as JSONB
    NOW(),
    NOW()
);
```

**Baker's Percentages JSONB Structure:**
```json
{
  "flour_ingredients": [
    {
      "ingredient_id": "ing_001",
      "name": "bread flour",
      "amount": 1000,
      "percentage": 100.0
    }
  ],
  "other_ingredients": [
    {
      "ingredient_id": "ing_002",
      "name": "water",
      "amount": 750,
      "percentage": 75.0
    },
    {
      "ingredient_id": "ing_003",
      "name": "levain",
      "amount": 200,
      "percentage": 20.0
    }
  ]
}
```

## Backend Business Logic

### Input Validation
1. **Required Fields Check**: Ensure name, ingredients array, and instructions array are provided
2. **Ingredient Validation**: 
   - Each ingredient must have name, amount > 0, valid unit, and valid type
   - Amount must be a positive number
   - Type must be one of: flour, liquid, preferment, fat, other
   - Unit must be one of: grams, kg, ml, cups, tbsp, tsp
3. **Instruction Validation**:
   - Each instruction must have non-empty instruction text
   - Order numbers should be sequential starting from 1
4. **Category Validation**: If provided, must be one of: sourdough, enriched, lean, sweet, other

### ID Generation
- Generate UUID for recipe if not provided
- Generate UUIDs for ingredient IDs if not provided (format: "ing_" + uuid or full uuid)
- Generate UUIDs for instruction IDs if not provided (format: "step_" + uuid or full uuid)

### Baker's Percentage Calculation
```python
def calculate_bakers_percentages(ingredients):
    flour_ingredients = [ing for ing in ingredients if ing['type'] == 'flour']
    other_ingredients = [ing for ing in ingredients if ing['type'] != 'flour']
    
    if not flour_ingredients:
        return None  # Cannot calculate without flour
    
    total_flour_weight = sum(ing['amount'] for ing in flour_ingredients)
    
    flour_percentages = []
    for ing in flour_ingredients:
        flour_percentages.append({
            'ingredient_id': ing['id'],
            'name': ing['name'],
            'amount': ing['amount'],
            'percentage': (ing['amount'] / total_flour_weight) * 100
        })
    
    other_percentages = []
    for ing in other_ingredients:
        other_percentages.append({
            'ingredient_id': ing['id'],
            'name': ing['name'],
            'amount': ing['amount'],
            'percentage': (ing['amount'] / total_flour_weight) * 100
        })
    
    return {
        'total_flour_weight': total_flour_weight,
        'flour_ingredients': flour_percentages,
        'other_ingredients': other_percentages
    }
```

### Error Handling
- **Validation Errors**: Return 422 with specific field errors
- **Database Errors**: Return 500 with generic error message (log details server-side)
- **Transaction Rollback**: Automatically rollback on any step failure
- **Duplicate Name**: Handle potential unique constraint violations gracefully

## API Endpoint Design

### POST /recipes/

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {token}  # If authentication implemented
```

**Request Body Schema:**
```typescript
interface CreateRecipeRequest {
  name: string;                    // required, 1-255 characters
  description?: string;            // optional, max 1000 characters
  category?: 'sourdough' | 'enriched' | 'lean' | 'sweet' | 'other';
  ingredients: Array<{
    id?: string;                   // optional, auto-generated if not provided
    name: string;                  // required, 1-100 characters
    amount: number;                // required, > 0
    unit: 'grams' | 'kg' | 'ml' | 'cups' | 'tbsp' | 'tsp';
    type: 'flour' | 'liquid' | 'preferment' | 'fat' | 'other';
    notes?: string;                // optional, max 500 characters
  }>;
  instructions: Array<{
    id?: string;                   // optional, auto-generated if not provided
    order: number;                 // required, sequential starting from 1
    instruction: string;           // required, non-empty, max 2000 characters
  }>;
}
```

**Success Response (201 Created):**
```typescript
interface CreateRecipeResponse {
  id: string;
  name: string;
  description?: string;
  category?: string;
  current_version_id: string;
  current_version: {
    id: string;
    recipe_id: string;
    version_number: 1;
    description: "Initial version";
    ingredients: Array<{
      id: string;                  // auto-generated if not in request
      name: string;
      amount: number;
      unit: string;
      type: string;
      notes?: string;
    }>;
    instructions: Array<{
      id: string;                  // auto-generated if not in request
      order: number;
      instruction: string;
    }>;
    created_at: string;            // ISO 8601 format
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
  created_at: string;              // ISO 8601 format
  updated_at: string;              // ISO 8601 format
}
```

**Error Responses:**
```typescript
// 422 Unprocessable Entity - Validation Errors
{
  "error": "Validation failed",
  "details": {
    "name": ["Name is required"],
    "ingredients[0].amount": ["Amount must be greater than 0"],
    "instructions": ["At least one instruction is required"]
  }
}

// 500 Internal Server Error - System Errors  
{
  "error": "Internal server error",
  "message": "Failed to create recipe"
}
```

## Database Transaction Implementation

### Python/FastAPI Example
```python
async def create_recipe(recipe_data: CreateRecipeRequest, db: Session):
    try:
        # Begin transaction
        db.begin()
        
        # Step 1: Create recipe
        recipe_id = await create_recipe_record(db, recipe_data)
        
        # Step 2: Create version
        version_id = await create_recipe_version(db, recipe_id, recipe_data)
        
        # Step 3: Update current version pointer
        await update_current_version(db, recipe_id, version_id)
        
        # Step 4: Calculate and store percentages
        if has_flour_ingredients(recipe_data.ingredients):
            await store_bakers_percentages(db, recipe_id, version_id, recipe_data.ingredients)
        
        # Commit transaction
        db.commit()
        
        # Return complete recipe data
        return await get_complete_recipe(db, recipe_id)
        
    except Exception as e:
        # Rollback on any error
        db.rollback()
        raise e
```

## Performance Considerations

### Database Indexes
- `recipes.name` - for recipe search
- `recipe_versions.recipe_id` - for version queries
- `recipe_versions.created_at DESC` - for latest version queries
- `bakers_percentages.recipe_version_id` - for percentage lookups

### JSONB Optimization
- Use GIN indexes on `ingredients` and `instructions` JSONB columns for search
- Consider partial indexes if common query patterns emerge

### Caching Strategy
- Cache calculated baker's percentages since they don't change for a given version
- Consider caching popular recipes for faster retrieval

This design ensures atomic recipe creation with proper data integrity, validation, and performance optimization.