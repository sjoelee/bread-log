-- Recipe storage with hybrid JSONB + generated array approach
-- Drop existing objects if they exist
-- DROP TABLE IF EXISTS recipes;

-- Main recipes table
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT NOT NULL,
    cook_time_minutes INTEGER,
    
    -- JSONB column for flexible ingredient storage
    ingredients JSONB NOT NULL,
    
    
    -- Standard timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to extract ingredient names from JSONB
CREATE OR REPLACE FUNCTION extract_ingredient_names(ingredients_json JSONB)
RETURNS TEXT[] AS $$
BEGIN
    RETURN ARRAY(
        SELECT ingredient ->> 'name'
        FROM jsonb_array_elements(ingredients_json) AS ingredient
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add the generated column using the function
ALTER TABLE recipes ADD COLUMN ingredient_names TEXT[] 
GENERATED ALWAYS AS (extract_ingredient_names(ingredients)) STORED;

-- Indexes for performance
CREATE INDEX idx_recipes_name ON recipes (name);
CREATE INDEX idx_recipes_ingredient_names ON recipes USING GIN (ingredient_names);
CREATE INDEX idx_recipes_ingredients ON recipes USING GIN (ingredients);

-- Example data insert
-- INSERT INTO recipes (name, description, instructions, cook_time_minutes, ingredients) VALUES
-- ('Basic Sourdough Bread', 'A classic sourdough bread recipe', 
-- '1. Mix flour and water for autolyse\n2. Add starter and salt\n3. Bulk fermentation with folds\n4. Pre-shape and final shape\n5. Cold ferment overnight\n6. Bake with steam', 
-- 45, 
-- '[
--   {"name": "bread flour", "amount": 500, "unit": "grams", "notes": "high protein flour"},
--   {"name": "water", "amount": 375, "unit": "grams", "notes": "filtered water"},
--   {"name": "sourdough starter", "amount": 100, "unit": "grams", "notes": "active starter"},
--   {"name": "salt", "amount": 10, "unit": "grams", "notes": "fine sea salt"}
-- ]'::jsonb);

-- Example queries you can run:

-- Find all recipes containing flour
-- SELECT * FROM recipes WHERE ingredient_names && ARRAY['bread flour'];

-- Find recipes with both flour and starter
-- SELECT * FROM recipes WHERE ingredient_names @> ARRAY['bread flour', 'sourdough starter'];

-- Search ingredients with JSONB path
-- SELECT name, ingredients FROM recipes WHERE ingredients @? '$[*] ? (@.amount > 300)';

