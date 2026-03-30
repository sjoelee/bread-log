-- Migration: Simplify recipe versioning to single version_number
-- Replace version_major/version_minor with single version_number field
-- Date: 2026-03-22

BEGIN;

-- First, let's add the new version_number column
ALTER TABLE recipe_versions 
ADD COLUMN version_number INT;

-- Populate version_number by combining major and minor versions
-- For existing data: version_number = version_major (ignoring minor for simplicity)
-- This assumes existing data uses mostly major version increments
UPDATE recipe_versions 
SET version_number = version_major;

-- Make version_number NOT NULL now that it's populated
ALTER TABLE recipe_versions 
ALTER COLUMN version_number SET NOT NULL;

-- Drop the old unique constraint on (recipe_id, version_major, version_minor)
ALTER TABLE recipe_versions 
DROP CONSTRAINT recipe_versions_recipe_id_version_major_version_minor_key;

-- Add new unique constraint on (recipe_id, version_number)
ALTER TABLE recipe_versions 
ADD CONSTRAINT recipe_versions_recipe_id_version_number_unique 
UNIQUE (recipe_id, version_number);

-- Drop the old version columns
ALTER TABLE recipe_versions 
DROP COLUMN version_major,
DROP COLUMN version_minor;

-- Drop and recreate the version index to use the new column
DROP INDEX IF EXISTS idx_recipe_versions_version;
CREATE INDEX idx_recipe_versions_version ON recipe_versions(recipe_id, version_number DESC);

-- Update the example queries in comments for future reference
COMMENT ON TABLE recipe_versions IS 'Recipe versions with simplified version_number field (1, 2, 3, etc.)';

-- Note: Update any application code that references version_major/version_minor
-- to use version_number instead

COMMIT;

-- Verification queries (run these after migration to verify success):
-- 
-- Check that version_number is populated and unique:
-- SELECT recipe_id, version_number, COUNT(*) 
-- FROM recipe_versions 
-- GROUP BY recipe_id, version_number 
-- HAVING COUNT(*) > 1;
-- 
-- Check table structure:
-- \d recipe_versions
--
-- Sample data check:
-- SELECT id, recipe_id, version_number, created_at 
-- FROM recipe_versions 
-- ORDER BY created_at DESC 
-- LIMIT 5;