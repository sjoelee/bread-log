CREATE TABLE account_makes (
    account_id UUID NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    make_name VARCHAR(255) NOT NULL,
    make_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, make_key)
);