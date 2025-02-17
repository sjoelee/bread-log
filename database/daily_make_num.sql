DROP FUNCTION IF EXISTS reset_daily_make_num();
DROP TRIGGER IF EXISTS reset_make_num_trigger ON dough_makes;
-- Create a function to reset sequence daily
CREATE OR REPLACE FUNCTION reset_daily_make_num()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
BEGIN
    -- Find the highest make_num for this dough and date
    SELECT COALESCE(MAX(make_num) + 1, 1)
    INTO next_num
    FROM dough_makes 
    WHERE dough_name = NEW.dough_name 
        AND make_date = NEW.make_date;
    
    -- Directly set the new make_num
    NEW.make_num := next_num;
    
    RAISE NOTICE 'Setting make_num to % for % on %', next_num, NEW.dough_name, NEW.make_date;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to reset sequence
CREATE TRIGGER reset_make_num_trigger
    BEFORE INSERT ON dough_makes
    FOR EACH ROW
    EXECUTE FUNCTION reset_daily_make_num();