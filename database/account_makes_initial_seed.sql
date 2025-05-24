-- Create UUID for Rize Up company
DO $$
DECLARE
    rize_up_uuid UUID := 'f47ac10b-58cc-4372-a567-0e02b2c3d479'; -- Generated UUID for Rize Up
BEGIN

-- Insert statements for the specified makes
INSERT INTO account_makes (account_id, account_name, display_name, key, created_at)
VALUES
    (rize_up_uuid, 'Rize Up', 'Hoagie', 'hoagie', CURRENT_TIMESTAMP),
    (rize_up_uuid, 'Rize Up', 'Ube', 'ube', CURRENT_TIMESTAMP),
    (rize_up_uuid, 'Rize Up', 'Team Make', 'team-make', CURRENT_TIMESTAMP),
    (rize_up_uuid, 'Rize Up', 'Demi Baguette', 'demi-baguette', CURRENT_TIMESTAMP);

END $$;