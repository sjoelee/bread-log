-- Migration script to rename dough_makes table to bread_timings
-- and update schema for new REST API

BEGIN;

-- Step 1: Rename the existing table
ALTER TABLE dough_makes RENAME TO bread_timings_old;

-- Step 2: Create the new bread_timings table with proper schema
CREATE TABLE bread_timings (
    -- Primary key and metadata
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Process timestamps (all optional)
    autolyse_ts TIMESTAMP,
    mix_ts TIMESTAMP,
    bulk_ts TIMESTAMP,
    preshape_ts TIMESTAMP,
    final_shape_ts TIMESTAMP,
    fridge_ts TIMESTAMP,
    
    -- Temperature measurements
    -- DECIMAL(5,1) allows for numbers like 100.5, -10.5, etc.
    room_temp DECIMAL(5,1),
    water_temp DECIMAL(5,1),
    flour_temp DECIMAL(5,1),
    preferment_temp DECIMAL(5,1),
    dough_temp DECIMAL(5,1),
    temperature_unit temperature_unit_type DEFAULT 'Fahrenheit',
    
    -- Stretch & folds and notes
    stretch_folds JSONB DEFAULT '[]'::jsonb,
    notes TEXT
);

-- Step 3: Migrate data from old table to new table
-- Map old column names to new column names
INSERT INTO bread_timings (
    recipe_name,
    date,
    created_at,
    updated_at,
    autolyse_ts,
    mix_ts,
    bulk_ts,
    preshape_ts,
    final_shape_ts,
    fridge_ts,
    room_temp,
    water_temp,
    flour_temp,
    preferment_temp,
    dough_temp,
    temperature_unit,
    stretch_folds,
    notes
)
SELECT 
    name as recipe_name,
    date,
    created_at,
    COALESCE(updated_at, created_at) as updated_at,
    autolyse_ts,
    mix_ts,
    bulk_ts,
    preshape_ts,
    final_shape_ts,
    fridge_ts,
    room_temp,
    water_temp,
    flour_temp,
    preferment_temp,
    dough_temp,
    temperature_unit,
    COALESCE(stretch_folds, '[]'::jsonb) as stretch_folds,
    notes
FROM bread_timings_old;

-- Step 4: Create indexes for common queries
CREATE INDEX idx_bread_timings_recipe_name ON bread_timings(recipe_name);
CREATE INDEX idx_bread_timings_date ON bread_timings(date);
CREATE INDEX idx_bread_timings_created_at ON bread_timings(created_at);
CREATE INDEX idx_bread_timings_date_recipe ON bread_timings(date, recipe_name);

-- Step 5: Create function and trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bread_timings_updated_at 
    BEFORE UPDATE ON bread_timings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Step 6: Drop the old table (commented out for safety)
-- Uncomment the next line after verifying data migration is successful
-- DROP TABLE bread_timings_old;

COMMIT;

-- Verification query to check migration
SELECT 
    'bread_timings' as table_name,
    COUNT(*) as record_count,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(DISTINCT recipe_name) as unique_recipes
FROM bread_timings
UNION ALL
SELECT 
    'bread_timings_old' as table_name,
    COUNT(*) as record_count,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(DISTINCT name) as unique_recipes
FROM bread_timings_old;