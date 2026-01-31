"""Enhanced repositories with credential and association support."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_registry.db.base import (
    MCPServerModel, TenantModel, TenantServerCredential, tenant_server_access
)


class TenantRepository:
    """Extended tenant repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, tenant: TenantModel) -> TenantModel:
        self.session.add(tenant)
        await self.session.flush()
        return tenant
    
    async def get_by_id(self, tenant_id: UUID) -> Optional[TenantModel]:
        result = await self.session.execute(
            select(TenantModel).where(
                and_(
                    TenantModel.id == str(tenant_id),
                    TenantModel.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[TenantModel]:
        result = await self.session.execute(
            select(TenantModel).where(
                and_(
                    TenantModel.api_key_hash == api_key_hash,
                    TenantModel.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()


class MCPServerRepository:
    """Server repository with association methods."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, server: MCPServerModel) -> MCPServerModel:
        self.session.add(server)
        await self.session.flush()
        return server
    
    async def get_by_id(self, server_id: UUID) -> Optional[MCPServerModel]:
        result = await self.session.execute(
            select(MCPServerModel).where(MCPServerModel.id == str(server_id))
        )
        return result.scalar_one_or_none()
    
    async def list_all(self, status: Optional[str] = None) -> List[MCPServerModel]:
        """Admin: list all servers."""
        query = select(MCPServerModel)
        if status:
            query = query.where(MCPServerModel.status == status)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def list_by_tenant(self, tenant_id: UUID) -> List[MCPServerModel]:
        """Get servers accessible to a tenant."""
        result = await self.session.execute(
            select(MCPServerModel)
            .join(tenant_server_access)
            .where(tenant_server_access.c.tenant_id == str(tenant_id))
            .where(MCPServerModel.status == "active")
        )
        return result.scalars().all()
    
    async def grant_access(
        self, 
        server_id: UUID, 
        tenant_id: UUID, 
        granted_by: UUID,
        permission_level: str = "use"
    ) -> bool:
        """Grant tenant access to server."""
        stmt = insert(tenant_server_access).values(
            tenant_id=str(tenant_id),
            server_id=str(server_id),
            granted_by=str(granted_by),
            permission_level=permission_level
        ).on_conflict_do_nothing()  # Idempotent
        
        await self.session.execute(stmt)
        await self.session.flush()
        return True
    
    async def revoke_access(self, server_id: UUID, tenant_id: UUID) -> bool:
        """Revoke tenant access."""
        stmt = delete(tenant_server_access).where(
            and_(
                tenant_server_access.c.tenant_id == str(tenant_id),
                tenant_server_access.c.server_id == str(server_id)
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def check_access(self, server_id: UUID, tenant_id: UUID) -> bool:
        """Check if tenant has access to server."""
        result = await self.session.execute(
            select(tenant_server_access).where(
                and_(
                    tenant_server_access.c.tenant_id == str(tenant_id),
                    tenant_server_access.c.server_id == str(server_id)
                )
            )
        )
        return result.first() is not None


class CredentialRepository:
    """Repository for tenant server credentials."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def store_credentials(
        self, 
        tenant_id: UUID, 
        server_id: UUID, 
        encrypted_data: bytes
    ) -> TenantServerCredential:
        """Store or update credentials."""
        # Check if exists
        result = await self.session.execute(
            select(TenantServerCredential).where(
                and_(
                    TenantServerCredential.tenant_id == str(tenant_id),
                    TenantServerCredential.server_id == str(server_id)
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.encrypted_credentials = encrypted_data
            await self.session.flush()
            return existing
        else:
            cred = TenantServerCredential(
                tenant_id=str(tenant_id),
                server_id=str(server_id),
                encrypted_credentials=encrypted_data
            )
            self.session.add(cred)
            await self.session.flush()
            return cred
    
    async def get_credentials(
        self, 
        tenant_id: UUID, 
        server_id: UUID
    ) -> Optional[TenantServerCredential]:
        """Get credentials for tenant-server pair."""
        result = await self.session.execute(
            select(TenantServerCredential).where(
                and_(
                    TenantServerCredential.tenant_id == str(tenant_id),
                    TenantServerCredential.server_id == str(server_id)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_tenant_credentials(
        self, 
        tenant_id: UUID
    ) -> List[TenantServerCredential]:
        """List all credentials for a tenant (with server info)."""
        result = await self.session.execute(
            select(TenantServerCredential)
            .where(TenantServerCredential.tenant_id == str(tenant_id))
        )
        return result.scalars().all()
    
    async def delete_credentials(
        self, 
        tenant_id: UUID, 
        server_id: UUID
    ) -> bool:
        """Delete credentials."""
        stmt = delete(TenantServerCredential).where(
            and_(
                TenantServerCredential.tenant_id == str(tenant_id),
                TenantServerCredential.server_id == str(server_id)
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
