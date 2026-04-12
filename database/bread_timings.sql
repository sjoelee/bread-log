-- New bread_timings table for REST API with UUID primary keys
DROP TABLE IF EXISTS bread_timings;
DROP TYPE IF EXISTS temperature_unit_type CASCADE;

-- Create temperature unit enum if it doesn't exist
CREATE TYPE temperature_unit_type AS ENUM ('Fahrenheit', 'Celsius');

-- Create the new bread_timings table
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

-- Create indexes for common queries
CREATE INDEX idx_bread_timings_recipe_name ON bread_timings(recipe_name);
CREATE INDEX idx_bread_timings_date ON bread_timings(date);
CREATE INDEX idx_bread_timings_created_at ON bread_timings(created_at);
CREATE INDEX idx_bread_timings_date_recipe ON bread_timings(date, recipe_name);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at on updates
CREATE TRIGGER update_bread_timings_updated_at 
    BEFORE UPDATE ON bread_timings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();