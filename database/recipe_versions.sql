-- Recipe versioning system with unified ingredients and baker's percentages
-- Drop existing objects if they exist
DROP TABLE IF EXISTS bakers_percentages CASCADE;
DROP TABLE IF EXISTS recipe_versions CASCADE;
DROP TABLE IF EXISTS recipes CASCADE;
DROP TABLE IF EXISTS recipes_new CASCADE;

-- Updated main recipes table (current version pointer)
CREATE TABLE recipes (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    current_version_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipe versions table (stores all versions with unified ingredients)
CREATE TABLE recipe_versions (
    id UUID PRIMARY KEY,
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    description TEXT,
    
    -- Unified ingredients storage (all ingredients in one JSONB column)
    ingredients JSONB NOT NULL,
    
    -- Instructions with step IDs for tracking
    instructions JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary JSONB, -- diff metadata for UI display
    
    -- Ensure unique version numbers per recipe
    UNIQUE(recipe_id, version_number)
);

-- Baker's percentages calculation table
CREATE TABLE bakers_percentages (
    id UUID PRIMARY KEY,
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    recipe_version_id UUID REFERENCES recipe_versions(id) ON DELETE CASCADE,
    
    -- Calculated flour totals and percentages
    total_flour_weight DECIMAL(10,2) NOT NULL,
    flour_ingredients JSONB NOT NULL, -- flour types with percentages
    other_ingredients JSONB NOT NULL, -- non-flour with percentages relative to flour
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One percentage calculation per recipe version
    UNIQUE(recipe_id, recipe_version_id)
);

-- Update foreign key constraint for current_version_id
ALTER TABLE recipes ADD CONSTRAINT fk_recipes_current_version 
    FOREIGN KEY (current_version_id) REFERENCES recipe_versions(id);

-- Indexes for performance
CREATE INDEX idx_recipe_versions_recipe_id ON recipe_versions(recipe_id);
CREATE INDEX idx_recipe_versions_version ON recipe_versions(recipe_id, version_number DESC);
CREATE INDEX idx_recipe_versions_created ON recipe_versions(created_at DESC);
CREATE INDEX idx_recipes_category ON recipes(category);
CREATE INDEX idx_recipes_name ON recipes(name);
CREATE INDEX idx_recipes_updated ON recipes(updated_at DESC);
CREATE INDEX idx_bakers_percentages_recipe_version ON bakers_percentages(recipe_version_id);
CREATE INDEX idx_bakers_percentages_recipe ON bakers_percentages(recipe_id);

-- GIN indexes for JSONB searching
CREATE INDEX idx_recipe_versions_ingredients ON recipe_versions USING GIN (ingredients);
CREATE INDEX idx_recipe_versions_instructions ON recipe_versions USING GIN (instructions);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on recipes
CREATE TRIGGER update_recipes_updated_at 
    BEFORE UPDATE ON recipes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on baker's percentages
CREATE TRIGGER update_bakers_percentages_updated_at 
    BEFORE UPDATE ON bakers_percentages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Example data structure for ingredients (unified)
-- {
--   "ingredients": [
--     {
--       "id": "ing_abc123",
--       "name": "bread flour",
--       "amount": 1000,
--       "unit": "grams",
--       "type": "flour",
--       "notes": "high protein flour"
--     },
--     {
--       "id": "ing_def456",
--       "name": "water",
--       "amount": 750,
--       "unit": "grams",
--       "type": "liquid",
--       "notes": "filtered water"
--     }
--   ]
-- }

-- Example data structure for instructions (with step IDs)
-- {
--   "instructions": [
--     {
--       "id": "step_abc123",
--       "order": 1,
--       "instruction": "Autolyse flour and water for 30 minutes"
--     },
--     {
--       "id": "step_def456",
--       "order": 2,
--       "instruction": "Add levain and mix thoroughly"
--     }
--   ]
-- }

-- Example data structure for baker's percentages
-- {
--   "total_flour_weight": 1000,
--   "flour_ingredients": [
--     {
--       "ingredient_id": "ing_abc123",
--       "name": "bread flour",
--       "amount": 1000,
--       "percentage": 100.0
--     }
--   ],
--   "other_ingredients": [
--     {
--       "ingredient_id": "ing_def456", 
--       "name": "water",
--       "amount": 750,
--       "percentage": 75.0
--     }
--   ]
-- }

-- Example queries for common operations:

-- Get latest version of a recipe
-- SELECT rv.* FROM recipe_versions rv
-- JOIN recipes r ON r.current_version_id = rv.id
-- WHERE r.id = 'recipe-uuid';

-- Get all versions of a recipe ordered by version
-- SELECT * FROM recipe_versions 
-- WHERE recipe_id = 'recipe-uuid'
-- ORDER BY version_major DESC, version_minor DESC;

-- Search recipes by ingredient name
-- SELECT DISTINCT r.id, r.name, rv.version_major, rv.version_minor
-- FROM recipes r
-- JOIN recipe_versions rv ON r.current_version_id = rv.id
-- WHERE rv.ingredients @> '[{"name": "bread flour"}]';

-- Get baker's percentages for current version
-- SELECT bp.* FROM bakers_percentages bp
-- JOIN recipes r ON r.current_version_id = bp.recipe_version_id
-- WHERE r.id = 'recipe-uuid';