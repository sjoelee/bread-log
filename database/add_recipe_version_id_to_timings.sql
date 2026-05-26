ALTER TABLE bread_timings
  ADD COLUMN recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL,
  ADD COLUMN recipe_version_id UUID REFERENCES recipe_versions(id) ON DELETE SET NULL;
