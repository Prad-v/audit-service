-- Create required databases for audit service
CREATE DATABASE audit_logs;
CREATE DATABASE alerting_db;
CREATE DATABASE events_db;

-- Grant permissions to audit_user
GRANT ALL PRIVILEGES ON DATABASE audit_logs TO audit_user;
GRANT ALL PRIVILEGES ON DATABASE alerting_db TO audit_user;
GRANT ALL PRIVILEGES ON DATABASE events_db TO audit_user;

