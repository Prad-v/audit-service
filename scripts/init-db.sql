-- Initialize Audit Log Database
-- This script creates the main audit database and alerting database

-- Create audit_logs database (if not exists)
SELECT 'CREATE DATABASE audit_logs'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'audit_logs')\gexec

-- Create alerting_db database (if not exists)
SELECT 'CREATE DATABASE alerting_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'alerting_db')\gexec

-- Create events_db database (if not exists)
SELECT 'CREATE DATABASE events_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'events_db')\gexec

-- Create cloud_management_db database (if not exists)
SELECT 'CREATE DATABASE cloud_management_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cloud_management_db')\gexec

-- Grant privileges to audit_user
GRANT ALL PRIVILEGES ON DATABASE audit_logs TO audit_user;
GRANT ALL PRIVILEGES ON DATABASE alerting_db TO audit_user;
GRANT ALL PRIVILEGES ON DATABASE events_db TO audit_user;
GRANT ALL PRIVILEGES ON DATABASE cloud_management_db TO audit_user;

-- Connect to audit_logs
\c audit_logs;

-- Grant schema privileges for audit_logs
GRANT ALL ON SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Set default privileges for future tables in audit_logs
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audit_user;

-- Connect to alerting_db
\c alerting_db;

-- Grant schema privileges for alerting_db
GRANT ALL ON SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Set default privileges for future tables in alerting_db
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audit_user;

-- Connect to events_db
\c events_db;

-- Grant schema privileges for events_db
GRANT ALL ON SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Set default privileges for future tables in events_db
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audit_user;

-- Connect to cloud_management_db
\c cloud_management_db;

-- Grant schema privileges for cloud_management_db
GRANT ALL ON SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Set default privileges for future tables in cloud_management_db
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audit_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audit_user;
