"""Updated SQLAlchemy models with many-to-many relationships and credential storage."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column, DateTime, String, ForeignKey, Table, Boolean, 
    LargeBinary, JSON, Integer, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Association table: Admin grants tenants access to servers
tenant_server_access = Table(
    "tenant_server_access",
    Base.metadata,
    Column("tenant_id", UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
    Column("server_id", UUID(as_uuid=True), ForeignKey("mcp_servers.id", ondelete="CASCADE"), primary_key=True),
    Column("granted_at", DateTime(timezone=True), default=datetime.utcnow),
    Column("granted_by", UUID(as_uuid=True), ForeignKey("tenants.id")),  # Admin who granted
    Column("permission_level", String(32), default="use"),  # 'use', 'manage'
)


class TenantModel(Base):
    """Updated Tenant model with admin flag."""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)  # NEW: Admin flag
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    allowed_origins: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    
    # Relationships
    accessible_servers = relationship(
        "MCPServerModel",
        secondary=tenant_server_access,
        back_populates="authorized_tenants"
    )
    
    credentials = relationship(
        "TenantServerCredential",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )


class MCPServerModel(Base):
    """Updated MCP Server - now global/admin-owned, not tenant-specific."""
    __tablename__ = "mcp_servers"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Admin who registered this server
    created_by_admin_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    
    # Base configuration (without sensitive tenant-specific creds)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    
    # Health tracking
    last_health_check: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    health_status: Mapped[str] = mapped_column(String(64), nullable=True)
    
    # Relationships
    authorized_tenants = relationship(
        "TenantModel",
        secondary=tenant_server_access,
        back_populates="accessible_servers"
    )
    
    tenant_credentials = relationship(
        "TenantServerCredential",
        back_populates="server",
        cascade="all, delete-orphan"
    )


class TenantServerCredential(Base):
    """Encrypted credentials for a tenant to use with a specific server."""
    __tablename__ = "tenant_server_credentials"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    server_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Encrypted credential blob
    encrypted_credentials: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    tenant = relationship("TenantModel", back_populates="credentials")
    server = relationship("MCPServerModel", back_populates="tenant_credentials")
    
    __table_args__ = (
        # Unique constraint: one credential entry per tenant-server pair
        {"postgresql_using": "gin"},
    )
