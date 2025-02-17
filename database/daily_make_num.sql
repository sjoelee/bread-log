DROP FUNCTION IF EXISTS reset_daily_make_num();

-- Create a function to reset sequence daily
CREATE OR REPLACE FUNCTION reset_daily_make_num()
RETURNS TRIGGER AS $$
DECLARE
    curr_date DATE;
    last_make_date DATE;
BEGIN
    -- Debug logging
    RAISE NOTICE 'New make_date: %', NEW.make_date;
    
    curr_date := NEW.make_date;
    
    SELECT make_date, make_num 
    INTO last_make_date, max_num
    FROM dough_makes 
    WHERE dough_name = NEW.dough_name 
    ORDER BY make_date DESC, make_num DESC 
    LIMIT 1;
    
    RAISE NOTICE 'Last make_date: %, max_num: %', last_make_date, max_num;
    
    IF last_make_date IS NULL OR curr_date > last_make_date THEN
        RAISE NOTICE 'Resetting sequence';
        ALTER SEQUENCE daily_make_num RESTART WITH 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to reset sequence
CREATE TRIGGER reset_make_num_trigger
    BEFORE INSERT ON dough_makes
    FOR EACH ROW
    EXECUTE FUNCTION reset_daily_make_num();