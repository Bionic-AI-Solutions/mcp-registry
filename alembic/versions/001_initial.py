"""Initial migration with multi-tenant credential support."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('api_key_hash', sa.String(256), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False, nullable=False),
        sa.Column('settings', postgresql.JSONB(), default={}),
        sa.Column('allowed_origins', postgresql.JSONB(), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
    )
    
    # MCP Servers table
    op.create_table(
        'mcp_servers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_admin_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('name', sa.String(256), nullable=False, unique=True),
        sa.Column('description', sa.Text(), default=''),
        sa.Column('version', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), default='active'),
        sa.Column('config', postgresql.JSONB(), nullable=False),
        sa.Column('capabilities', postgresql.JSONB(), default={}),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(64), nullable=True),
    )
    
    # Tenant-Server Access association
    op.create_table(
        'tenant_server_access',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('mcp_servers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id')),
        sa.Column('permission_level', sa.String(32), default='use'),
    )
    
    # Tenant Server Credentials
    op.create_table(
        'tenant_server_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('encrypted_credentials', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), 
                  onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('tenant_server_credentials')
    op.drop_table('tenant_server_access')
    op.drop_table('mcp_servers')
    op.drop_table('tenants')
