-- Initialize Events Service Database
-- This script creates the events_db database and sets up the necessary permissions

-- Create events database
CREATE DATABASE events_db;

-- Grant permissions to audit_user
GRANT ALL PRIVILEGES ON DATABASE events_db TO audit_user;

-- Connect to events_db
\c events_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO audit_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual tables will be created by the Events Service using SQLAlchemy/Alembic
-- This script just ensures the database exists and has proper permissions
