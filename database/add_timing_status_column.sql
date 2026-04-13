-- Migration: Add status column to bread_timings table
-- This adds state management to track timing completion status

BEGIN;

-- Add status column with default value and constraint
ALTER TABLE bread_timings 
ADD COLUMN status VARCHAR(20) DEFAULT 'in_progress' 
CHECK (status IN ('in_progress', 'completed'));

-- Create index for efficient filtering by status
CREATE INDEX idx_bread_timings_status ON bread_timings(status);

-- Create composite index for status + updated_at for efficient filtering and sorting
CREATE INDEX idx_bread_timings_status_updated_at ON bread_timings(status, updated_at DESC);

-- Update existing records to have correct status based on data completeness
-- A timing is considered complete if all required fields are populated
UPDATE bread_timings 
SET status = CASE 
    WHEN recipe_name IS NOT NULL 
         AND date IS NOT NULL
         AND autolyse_ts IS NOT NULL 
         AND mix_ts IS NOT NULL 
         AND bulk_ts IS NOT NULL
         AND preshape_ts IS NOT NULL 
         AND final_shape_ts IS NOT NULL 
         AND fridge_ts IS NOT NULL
         AND room_temp IS NOT NULL 
         AND water_temp IS NOT NULL 
         AND flour_temp IS NOT NULL
         AND preferment_temp IS NOT NULL 
         AND dough_temp IS NOT NULL
         AND temperature_unit IS NOT NULL 
    THEN 'completed'
    ELSE 'in_progress'
END;

COMMIT;

-- Verification query to check the migration results
SELECT 
    status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM bread_timings 
GROUP BY status
ORDER BY status;

-- Show some sample records to verify the migration
SELECT 
    id,
    recipe_name,
    date,
    status,
    created_at,
    updated_at
FROM bread_timings 
ORDER BY updated_at DESC 
LIMIT 10;