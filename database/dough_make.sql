DROP TABLE IF EXISTS dough_makes;
DROP SEQUENCE IF EXISTS daily_make_num;
CREATE SEQUENCE daily_make_num;
CREATE TABLE dough_makes (
    dough_name VARCHAR(100) NOT NULL,
    make_date DATE NOT NULL,
    -- make_num autoincrements for the same day, and reset to 1 for a new day, see implementaion in daily_make_num.sql
    make_num INTEGER nextval('daily_make_num'),

    -- Temperature measurements in Fahrenheit
    -- DECIMAL(5,1) allows for numbers like 100.5, -10.5, etc.
    room_temp DECIMAL(5,1),
    water_temp DECIMAL(5,1),
    flour_temp DECIMAL(5,1),
    preferment_temp DECIMAL(5,1),
    
    -- Timestamps for each stage of the process
    autolyse_ts TIMESTAMP,
    start_ts TIMESTAMP NOT NULL,
    pull_ts TIMESTAMP NOT NULL,
    preshape_ts TIMESTAMP NOT NULL,
    final_shape_ts TIMESTAMP NOT NULL,
    fridge_ts TIMESTAMP NOT NULL,
    
    -- Audit fields for record keeping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (dough_name, make_date, make_num)
);
