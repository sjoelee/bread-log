DROP TABLE IF EXISTS dough_makes;
DROP SEQUENCE IF EXISTS daily_make_num;
DROP TYPE IF EXISTS temperature_unit_type;
CREATE TYPE temperature_unit_type AS ENUM ('Fahrenheit', 'Celsius');
CREATE SEQUENCE daily_make_num;
CREATE TABLE dough_makes (
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    -- make_num autoincrements for the same day, and reset to 1 for a new day, see implementaion in daily_make_num.sql
    make_num INTEGER DEFAULT nextval('daily_make_num'),

    -- Temperature measurements in Fahrenheit
    -- DECIMAL(5,1) allows for numbers like 100.5, -10.5, etc.
    room_temp DECIMAL(5,1),
    water_temp DECIMAL(5,1),
    flour_temp DECIMAL(5,1),
    preferment_temp DECIMAL(5,1),
    dough_temp DECIMAL(5,1),
    temperature_unit temperature_unit_type DEFAULT 'Fahrenheit',
    
    -- Timestamps for each stage of the process
    autolyse_ts TIMESTAMP,
    start_ts TIMESTAMP NOT NULL,
    pull_ts TIMESTAMP NOT NULL,
    preshape_ts TIMESTAMP NOT NULL,
    final_shape_ts TIMESTAMP NOT NULL,
    fridge_ts TIMESTAMP NOT NULL,
    ADD COLUMN stretch_folds JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN notes TEXT;
    
    -- Audit fields for record keeping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (name, date, make_num)
);
