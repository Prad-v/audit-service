"""Initial schema for audit log framework

Revision ID: 0001
Revises: 
Create Date: 2025-08-27 05:06:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_is_active'), 'tenants', ['is_active'], unique=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('roles', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index('ix_users_tenant_active', 'users', ['tenant_id', 'is_active'], unique=False)
    op.create_index('ix_users_roles_gin', 'users', ['roles'], unique=False, postgresql_using='gin')
    
    # Create API keys table
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_tenant_active', 'api_keys', ['tenant_id', 'is_active'], unique=False)
    op.create_index('ix_api_keys_expires', 'api_keys', ['expires_at'], unique=False)
    op.create_index('ix_api_keys_permissions_gin', 'api_keys', ['permissions'], unique=False, postgresql_using='gin')
    
    # Create retention policies table
    op.create_table('retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('retention_days > 0 AND retention_days <= 2555', name='ck_retention_policies_days'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'event_type', 'resource_type', name='uq_retention_policies_tenant_event_resource')
    )
    op.create_index('ix_retention_policies_tenant_active', 'retention_policies', ['tenant_id', 'is_active'], unique=False)
    op.create_index('ix_retention_policies_event_type', 'retention_policies', ['event_type'], unique=False)
    op.create_index('ix_retention_policies_resource_type', 'retention_policies', ['resource_type'], unique=False)
    
    # Create export jobs table
    op.create_table('export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('query_params', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('processed_records', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('download_url', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'expired')", name='ck_export_jobs_status'),
        sa.CheckConstraint("format IN ('csv', 'json', 'xlsx')", name='ck_export_jobs_format'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_export_jobs_tenant_status', 'export_jobs', ['tenant_id', 'status'], unique=False)
    op.create_index('ix_export_jobs_user_created', 'export_jobs', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_export_jobs_expires', 'export_jobs', ['expires_at'], unique=False)
    
    # Create audit log partitions table
    op.create_table('audit_log_partitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('partition_name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_maintenance', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partition_name')
    )
    op.create_index('ix_audit_log_partitions_dates', 'audit_log_partitions', ['start_date', 'end_date'], unique=False)
    op.create_index('ix_audit_log_partitions_active', 'audit_log_partitions', ['is_active'], unique=False)
    
    # Create daily audit summary table
    op.create_table('daily_audit_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('unique_users', sa.Integer(), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('warning_count', sa.Integer(), nullable=False),
        sa.Column('avg_response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'service_name', 'event_type', 'date', name='uq_daily_audit_summary')
    )
    op.create_index('ix_daily_audit_summary_tenant_date', 'daily_audit_summary', ['tenant_id', 'date'], unique=False)
    op.create_index('ix_daily_audit_summary_service_date', 'daily_audit_summary', ['service_name', 'date'], unique=False)
    
    # Create main audit logs table (partitioned)
    op.create_table('audit_logs',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('request_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('partition_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('retention_period_days > 0 AND retention_period_days <= 2555', name='ck_audit_logs_retention_period'),
        sa.CheckConstraint("status IN ('success', 'error', 'warning', 'info')", name='ck_audit_logs_status'),
        sa.PrimaryKeyConstraint('audit_id', 'partition_date'),
        postgresql_partition_by='RANGE (partition_date)'
    )
    
    # Create indexes on audit_logs table
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'], unique=False)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'], unique=False)
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'], unique=False)
    op.create_index('ix_audit_logs_correlation_id', 'audit_logs', ['correlation_id'], unique=False)
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'], unique=False)
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'], unique=False)
    op.create_index('ix_audit_logs_partition_date', 'audit_logs', ['partition_date'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_status', 'audit_logs', ['status'], unique=False)
    op.create_index('ix_audit_logs_service_name', 'audit_logs', ['service_name'], unique=False)
    
    # Create composite indexes
    op.create_index('ix_audit_logs_tenant_timestamp', 'audit_logs', ['tenant_id', 'timestamp'], unique=False)
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'timestamp'], unique=False)
    op.create_index('ix_audit_logs_event_timestamp', 'audit_logs', ['event_type', 'timestamp'], unique=False)
    op.create_index('ix_audit_logs_partition_tenant', 'audit_logs', ['partition_date', 'tenant_id'], unique=False)
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    
    # Create GIN indexes for JSON fields
    op.create_index('ix_audit_logs_metadata_gin', 'audit_logs', ['metadata'], unique=False, postgresql_using='gin')
    op.create_index('ix_audit_logs_request_data_gin', 'audit_logs', ['request_data'], unique=False, postgresql_using='gin')
    
    # Create initial partitions for current and next month
    op.execute("""
        CREATE TABLE audit_logs_2025_08 PARTITION OF audit_logs
        FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
    """)
    
    op.execute("""
        CREATE TABLE audit_logs_2025_09 PARTITION OF audit_logs
        FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
    """)
    
    # Insert default tenant
    op.execute("""
        INSERT INTO tenants (id, name, description, settings, is_active)
        VALUES ('default', 'Default Tenant', 'Default tenant for development', '{}', true);
    """)
    
    # Insert default admin user (password: admin123)
    op.execute("""
        INSERT INTO users (username, email, password_hash, tenant_id, roles, is_active)
        VALUES (
            'admin',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgusgqHu',
            'default',
            ARRAY['audit_admin', 'system_admin'],
            true
        );
    """)


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('daily_audit_summary')
    op.drop_table('audit_log_partitions')
    op.drop_table('export_jobs')
    op.drop_table('retention_policies')
    op.drop_table('api_keys')
    op.drop_table('users')
    op.drop_table('tenants')