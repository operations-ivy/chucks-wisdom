-- Run this while connected to the 'postgres' database
-- (or any DB other than the one you're creating)

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE chuck'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'chuck'
)\gexec


-- Switch to the chuck database
\c chuck

-- Create the chuck table
CREATE TABLE IF NOT EXISTS chuck (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    value TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS chuck_id_value_index ON chuck (id, value);
CREATE INDEX IF NOT EXISTS chuck_category_value_index ON chuck (category, value);
CREATE INDEX IF NOT EXISTS chuck_id_idx ON chuck (id);
CREATE INDEX IF NOT EXISTS chuck_id_category_idx ON chuck (id, category);
CREATE INDEX IF NOT EXISTS chuck_id_category_value_idx ON chuck (id, category, value);

-- Create role/user if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zaphod'
    ) THEN
        CREATE ROLE zaphod LOGIN PASSWORD 'zaphod';
    END IF;
END
$$;

-- Grant all privileges on chuck table to zaphod
GRANT ALL PRIVILEGES ON TABLE chuck TO zaphod;

-- Optionally, make zaphod a superuser
ALTER ROLE zaphod WITH SUPERUSER;
