-- Replace stretch_folds JSONB array with a simple integer count.
ALTER TABLE bread_timings
  ADD COLUMN stretch_fold_count INTEGER NOT NULL DEFAULT 0;

-- Migrate existing data: count array elements from old JSONB column
UPDATE bread_timings
  SET stretch_fold_count = jsonb_array_length(stretch_folds)
  WHERE stretch_folds IS NOT NULL;

ALTER TABLE bread_timings DROP COLUMN stretch_folds;
