"""FastAPI dependencies."""

from fastapi import Header, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from mcp_registry.config import get_settings
from mcp_registry.db.session import get_db_session
from mcp_registry.db.repositories import TenantRepository, MCPServerRepository
from mcp_registry.services.auth import AuthService

settings = get_settings()
auth_service = AuthService()
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def get_current_tenant(
    x_tenant_id: str = Header(..., alias=settings.tenant_id_header),
    x_api_key: str = Depends(api_key_header),
    session: AsyncSession = Depends(get_db_session)
) -> UUID:
    """
    Dependency to validate tenant authentication.
    Returns tenant_id if valid, raises 401 otherwise.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format"
        )
    
    repo = TenantRepository(session)
    is_valid = await auth_service.authenticate(repo, tenant_id, x_api_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or tenant"
        )
    
    return tenant_id


async def get_tenant_repo(session: AsyncSession = Depends(get_db_session)):
    """Dependency for tenant repository."""
    return TenantRepository(session)


async def get_server_repo(session: AsyncSession = Depends(get_db_session)):
    """Dependency for server repository."""
    return MCPServerRepository(session)
