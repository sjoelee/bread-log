-- Recipe storage with hybrid JSONB + generated array approach
-- Drop existing objects if they exist
DROP TABLE IF EXISTS recipes CASCADE;
DROP FUNCTION IF EXISTS extract_all_ingredient_names(JSONB, JSONB) CASCADE;
DROP FUNCTION IF EXISTS extract_ingredient_names(JSONB) CASCADE;

-- Function to extract ingredient names from both flour and other ingredients
CREATE OR REPLACE FUNCTION extract_all_ingredient_names(flour_ingredients_json JSONB, other_ingredients_json JSONB)
RETURNS TEXT[] AS $$
BEGIN
    RETURN ARRAY(
        SELECT ingredient ->> 'name'
        FROM (
            SELECT jsonb_array_elements(flour_ingredients_json) AS ingredient
            UNION ALL
            SELECT jsonb_array_elements(other_ingredients_json) AS ingredient
        ) combined_ingredients
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Main recipes table
CREATE TABLE recipes (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructions JSONB NOT NULL,
    
    -- JSONB columns for ingredient storage
    flour_ingredients JSONB NOT NULL,
    other_ingredients JSONB NOT NULL,
    
    -- Generated column for all ingredient names
    ingredient_names TEXT[] GENERATED ALWAYS AS (extract_all_ingredient_names(flour_ingredients, other_ingredients)) STORED,
    
    -- Standard timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Indexes for performance
CREATE INDEX idx_recipes_name ON recipes (name);
CREATE INDEX idx_recipes_ingredient_names ON recipes USING GIN (ingredient_names);
CREATE INDEX idx_recipes_flour_ingredients ON recipes USING GIN (flour_ingredients);
CREATE INDEX idx_recipes_other_ingredients ON recipes USING GIN (other_ingredients);

-- Example data insert
-- INSERT INTO recipes (name, description, instructions, flour_ingredients, other_ingredients) VALUES
-- ('Focaccia', 'Classic Italian focaccia with olive oil and herbs', 
-- '[
--   {"instruction": "Create ripe levain"},
--   {"instruction": "When levain is ripe, scale all the ingredients"},
--   {"instruction": "Mix all the ingredients together, except for the olive oil. Desired dough temp is about 80°F"},
--   {"instruction": "Bake for 30-40 minutes until golden brown. Internal temp should be about 210°F"}
-- ]'::jsonb,
-- '[
--   {"name": "bread flour", "amount": 1056, "unit": "grams", "notes": "high protein flour"}
-- ]'::jsonb,
-- '[
--   {"name": "water", "amount": 845, "unit": "grams", "notes": "filtered water"},
--   {"name": "levain", "amount": 211, "unit": "grams", "notes": "ripe sourdough starter"},
--   {"name": "salt", "amount": 17, "unit": "grams", "notes": "fine sea salt"},
--   {"name": "olive oil", "amount": 71, "unit": "grams", "notes": "extra virgin olive oil"}
-- ]'::jsonb);

-- Example queries you can run:

-- Find all recipes containing flour
-- SELECT * FROM recipes WHERE ingredient_names && ARRAY['bread flour'];

-- Find recipes with both flour and starter
-- SELECT * FROM recipes WHERE ingredient_names @> ARRAY['bread flour', 'levain'];

-- Search flour ingredients with high amounts
-- SELECT name, flour_ingredients FROM recipes WHERE flour_ingredients @? '$[*] ? (@.amount > 1000)';

-- Calculate baker's percentages on-the-fly
-- SELECT 
--   name,
--   (SELECT SUM((ingredient->>'amount')::numeric) 
--    FROM jsonb_array_elements(flour_ingredients) AS ingredient) AS total_flour_weight,
--   jsonb_agg(
--     jsonb_build_object(
--       'name', ingredient->>'name',
--       'amount', (ingredient->>'amount')::numeric,
--       'unit', ingredient->>'unit',
--       'notes', ingredient->>'notes',
--       'percentage', ((ingredient->>'amount')::numeric / 
--         (SELECT SUM((f->>'amount')::numeric) FROM jsonb_array_elements(flour_ingredients) AS f)) * 100
--     )
--   ) AS other_ingredients_with_percentages
-- FROM recipes, jsonb_array_elements(other_ingredients) AS ingredient
-- GROUP BY name, flour_ingredients, other_ingredients;

