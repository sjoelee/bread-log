ALTER TABLE bread_timings
  ADD COLUMN timezone VARCHAR(50) NOT NULL DEFAULT 'UTC';

-- Treat existing naive timestamps as UTC before converting to timestamptz
ALTER TABLE bread_timings
  ALTER COLUMN autolyse_ts   TYPE timestamptz USING autolyse_ts   AT TIME ZONE 'UTC',
  ALTER COLUMN mix_ts        TYPE timestamptz USING mix_ts        AT TIME ZONE 'UTC',
  ALTER COLUMN bulk_ts       TYPE timestamptz USING bulk_ts       AT TIME ZONE 'UTC',
  ALTER COLUMN preshape_ts   TYPE timestamptz USING preshape_ts   AT TIME ZONE 'UTC',
  ALTER COLUMN final_shape_ts TYPE timestamptz USING final_shape_ts AT TIME ZONE 'UTC',
  ALTER COLUMN final_proof_ts TYPE timestamptz USING final_proof_ts AT TIME ZONE 'UTC',
  ALTER COLUMN bake_ts       TYPE timestamptz USING bake_ts       AT TIME ZONE 'UTC';
