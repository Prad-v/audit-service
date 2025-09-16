-- Initialize Alerting Database
-- This script creates the alerting database and user

-- Create alerting database
CREATE DATABASE alerting_db;

-- Grant privileges to audit_user
GRANT ALL PRIVILEGES ON DATABASE alerting_db TO audit_user;

-- Connect to alerting_db
\c alerting_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audit_user;
