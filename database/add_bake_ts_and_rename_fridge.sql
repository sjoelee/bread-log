ALTER TABLE bread_timings RENAME COLUMN fridge_ts TO final_proof_ts;
ALTER TABLE bread_timings ADD COLUMN bake_ts TIMESTAMP;
