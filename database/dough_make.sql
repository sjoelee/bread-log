CREATE TABLE dough_makes (
    make_id SERIAL PRIMARY KEY,
    dough_name VARCHAR(100) NOT NULL,
    make_date DATE NOT NULL,
    
    -- Temperature measurements in Fahrenheit
    -- DECIMAL(5,1) allows for numbers like 100.5, -10.5, etc.
    room_temp DECIMAL(5,1),
    water_temp DECIMAL(5,1),
    flour_temp DECIMAL(5,1),
    preferment_temp DECIMAL(5,1),
    
    -- Time duration (in minutes)
    autolyse_time INTEGER,
    
    -- Timestamps for each stage of the process
    start_time TIMESTAMP NOT NULL,
    pull_time TIMESTAMP,
    pre_shape_time TIMESTAMP,
    final_shape_time TIMESTAMP,
    fridge_time TIMESTAMP,
    
    -- Audit fields for record keeping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure logical time sequence
    CONSTRAINT valid_time_sequence CHECK (
        start_time <= pull_time 
        AND pull_time <= pre_shape_time 
        AND pre_shape_time <= final_shape_time 
        AND final_shape_time <= fridge_time
    ),
    
    -- Add temperature range constraints for Fahrenheit
    -- Not sure if this is needed, if we have frontend performing the check.
    CONSTRAINT valid_temperature_ranges CHECK (
        room_temp BETWEEN 0 AND 120
        AND water_temp BETWEEN 32 AND 212
        AND flour_temp BETWEEN 0 AND 120
        AND preferment_temp BETWEEN 0 AND 120
    )
);
