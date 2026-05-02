-- Make bread_timings.date nullable and default to current date
-- Allows creating in-progress timings without explicitly supplying a date.

ALTER TABLE bread_timings
  ALTER COLUMN date DROP NOT NULL,
  ALTER COLUMN date SET DEFAULT CURRENT_DATE;
