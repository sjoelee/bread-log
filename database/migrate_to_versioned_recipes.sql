-- Migration script to convert existing recipes to versioned system
-- This script safely migrates data from the old recipes table to the new versioned structure

BEGIN;

-- Create new tables (if not already created)
\i recipe_versions.sql

-- Insert existing recipes into new structure
INSERT INTO recipes_new (id, name, created_at, updated_at)
SELECT 
    id,
    name,
    created_at,
    updated_at
FROM recipes
WHERE EXISTS (SELECT 1 FROM recipes); -- Only if old recipes table exists

-- Create initial versions (v1.0) for existing recipes
INSERT INTO recipe_versions (
    id, 
    recipe_id, 
    version_major, 
    version_minor, 
    description,
    ingredients,
    instructions,
    created_at
)
SELECT 
    gen_random_uuid() as id,
    r.id as recipe_id,
    1 as version_major,
    0 as version_minor,
    'Migrated from existing recipe' as description,
    -- Convert old structure to new unified ingredients
    jsonb_build_object(
        'ingredients',
        (
            -- Combine flour_ingredients and other_ingredients
            SELECT jsonb_agg(
                ingredient || jsonb_build_object('type', 
                    CASE 
                        WHEN ingredient->>'name' ILIKE '%flour%' THEN 'flour'
                        WHEN ingredient->>'name' ILIKE '%water%' THEN 'liquid'  
                        WHEN ingredient->>'name' ILIKE '%salt%' THEN 'other'
                        WHEN ingredient->>'name' ILIKE '%yeast%' THEN 'other'
                        WHEN ingredient->>'name' ILIKE '%levain%' OR ingredient->>'name' ILIKE '%starter%' THEN 'preferment'
                        ELSE 'other'
                    END,
                    'id', gen_random_uuid()::text
                )
            )
            FROM (
                SELECT jsonb_array_elements(flour_ingredients) as ingredient
                UNION ALL 
                SELECT jsonb_array_elements(other_ingredients) as ingredient
            ) combined
        )
    ),
    -- Convert instructions to new format with IDs
    jsonb_build_object(
        'instructions',
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', gen_random_uuid()::text,
                    'order', row_number() OVER (ORDER BY ordinality),
                    'instruction', instruction->>'instruction'
                )
            )
            FROM jsonb_array_elements(instructions) WITH ORDINALITY instruction
        )
    ),
    r.created_at
FROM recipes r
WHERE EXISTS (SELECT 1 FROM recipes); -- Only if old recipes table exists

-- Update current_version_id to point to the newly created v1.0 versions
UPDATE recipes_new 
SET current_version_id = rv.id
FROM recipe_versions rv
WHERE recipes_new.id = rv.recipe_id 
    AND rv.version_major = 1 
    AND rv.version_minor = 0;

-- Create baker's percentages for migrated recipes
INSERT INTO bakers_percentages (
    id,
    recipe_id,
    recipe_version_id,
    total_flour_weight,
    flour_ingredients,
    other_ingredients
)
SELECT 
    gen_random_uuid() as id,
    rv.recipe_id,
    rv.id as recipe_version_id,
    -- Calculate total flour weight
    COALESCE(
        (
            SELECT SUM((ingredient->>'amount')::decimal)
            FROM jsonb_array_elements(rv.ingredients->'ingredients') ingredient
            WHERE ingredient->>'type' = 'flour'
        ), 
        1000 -- Default if no flour found
    ) as total_flour_weight,
    -- Flour ingredients with percentages
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'ingredient_id', ingredient->>'id',
                'name', ingredient->>'name',
                'amount', (ingredient->>'amount')::decimal,
                'percentage', 
                CASE 
                    WHEN total_flour > 0 THEN ROUND(((ingredient->>'amount')::decimal / total_flour) * 100, 1)
                    ELSE 100.0
                END
            )
        )
        FROM jsonb_array_elements(rv.ingredients->'ingredients') ingredient
        CROSS JOIN (
            SELECT COALESCE(
                (
                    SELECT SUM((f->>'amount')::decimal)
                    FROM jsonb_array_elements(rv.ingredients->'ingredients') f
                    WHERE f->>'type' = 'flour'
                ), 
                1000
            ) as total_flour
        ) tf
        WHERE ingredient->>'type' = 'flour'
    ) as flour_ingredients,
    -- Other ingredients with percentages relative to flour
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'ingredient_id', ingredient->>'id',
                'name', ingredient->>'name', 
                'amount', (ingredient->>'amount')::decimal,
                'percentage',
                CASE 
                    WHEN total_flour > 0 THEN ROUND(((ingredient->>'amount')::decimal / total_flour) * 100, 1)
                    ELSE 0.0
                END
            )
        )
        FROM jsonb_array_elements(rv.ingredients->'ingredients') ingredient
        CROSS JOIN (
            SELECT COALESCE(
                (
                    SELECT SUM((f->>'amount')::decimal)
                    FROM jsonb_array_elements(rv.ingredients->'ingredients') f
                    WHERE f->>'type' = 'flour'
                ), 
                1000
            ) as total_flour
        ) tf
        WHERE ingredient->>'type' != 'flour'
    ) as other_ingredients
FROM recipe_versions rv
WHERE rv.version_major = 1 AND rv.version_minor = 0;

-- Rename old table to backup (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'recipes') THEN
        ALTER TABLE recipes RENAME TO recipes_backup_pre_versioning;
    END IF;
END
$$;

-- Rename new table to replace old one
ALTER TABLE recipes_new RENAME TO recipes;

-- Update any foreign key references to point to new recipes table
-- (This would depend on your specific foreign key relationships)

COMMIT;

-- Verification queries to run after migration:

-- Check migration was successful
-- SELECT 'Migration Summary' as info, 
--        (SELECT COUNT(*) FROM recipes) as total_recipes,
--        (SELECT COUNT(*) FROM recipe_versions) as total_versions,
--        (SELECT COUNT(*) FROM bakers_percentages) as total_percentages;

-- Sample recipe with baker's percentages
-- SELECT r.name, 
--        rv.version_major || '.' || rv.version_minor as version,
--        bp.total_flour_weight,
--        rv.ingredients,
--        bp.flour_ingredients,
--        bp.other_ingredients
-- FROM recipes r
-- JOIN recipe_versions rv ON r.current_version_id = rv.id  
-- JOIN bakers_percentages bp ON rv.id = bp.recipe_version_id
-- LIMIT 1;