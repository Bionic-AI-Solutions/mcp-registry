"""Updated API routes with Admin and Tenant separation."""

from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_registry.api.dependencies import get_db_session
from mcp_registry.db.repositories import CredentialRepository, MCPServerRepository, TenantRepository
from mcp_registry.db.base import MCPServerModel, TenantModel, TenantServerCredential
from mcp_registry.models import (
    ServerRegistrationRequest, 
    ServerResponse, 
    TenantCreateRequest,
    ServerStatus,
)
from mcp_registry.services.auth import auth_service
from mcp_registry.services.encryption import encryption_service
from mcp_registry.services.audit import AuditLogger
from mcp_registry.config import get_settings

router = APIRouter()
settings = get_settings()


# ==================== ADMIN ENDPOINTS ====================

async def get_current_admin(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: AsyncSession = Depends(get_db_session)
) -> TenantModel:
    """Dependency to verify admin access."""
    tenant_id = UUID(x_tenant_id)
    repo = TenantRepository(session)
    return await auth_service.authenticate_admin(repo, tenant_id, x_api_key)


@router.post("/admin/servers", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def admin_register_server(
    request: Request,
    data: ServerRegistrationRequest,
    admin: TenantModel = Depends(get_current_admin),
    repo: MCPServerRepository = Depends(get_server_repo),
):
    """
    **Admin Only**: Register a global MCP server.
    Servers registered here are initially not accessible to any tenant until granted.
    """
    trace_id = AuditLogger.create_trace(UUID(admin.id), "admin_register_server")
    
    server = MCPServerModel(
        created_by_admin_id=str(admin.id),
        name=data.name,
        description=data.description,
        version=data.version,
        config=data.config.model_dump(),
        capabilities=data.capabilities.model_dump(),
        tags=data.tags,
        metadata_json=data.metadata,
        status="active"
    )
    
    created = await repo.create(server)
    
    await AuditLogger.log(
        action="CREATE",
        resource_type="server",
        tenant_id=UUID(admin.id),
        resource_id=str(created.id),
        success=True,
        details={"name": data.name, "admin": admin.name},
        ip_address=request.client.host if request.client else None,
        trace_id=trace_id,
    )
    
    return ServerResponse.model_validate(created)


@router.post("/admin/servers/{server_id}/tenants/{tenant_id}")
async def admin_grant_server_access(
    request: Request,
    server_id: UUID,
    tenant_id: UUID,
    permission_level: str = Query(default="use", enum=["use", "manage"]),
    admin: TenantModel = Depends(get_current_admin),
    repo: MCPServerRepository = Depends(get_server_repo),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
):
    """
    **Admin Only**: Associate/Grant a tenant access to use a specific MCP server.
    """
    # Verify server exists
    server = await repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Grant access
    await repo.grant_access(server_id, tenant_id, UUID(admin.id), permission_level)
    
    await AuditLogger.log(
        action="GRANT_ACCESS",
        resource_type="server",
        tenant_id=tenant_id,  # Target tenant
        resource_id=str(server_id),
        success=True,
        details={
            "granted_by": str(admin.id),
            "permission_level": permission_level,
            "server_name": server.name
        },
        ip_address=request.client.host if request.client else None,
    )
    
    return {
        "message": f"Access granted to {tenant.name} for server {server.name}",
        "tenant_id": str(tenant_id),
        "server_id": str(server_id),
        "permission_level": permission_level
    }


@router.delete("/admin/servers/{server_id}/tenants/{tenant_id}")
async def admin_revoke_server_access(
    request: Request,
    server_id: UUID,
    tenant_id: UUID,
    admin: TenantModel = Depends(get_current_admin),
    repo: MCPServerRepository = Depends(get_server_repo),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **Admin Only**: Disassociate/Revoke a tenant's access to a server.
    Also cleans up stored credentials for that tenant-server pair.
    """
    # Revoke access
    success = await repo.revoke_access(server_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access grant not found")
    
    # Clean up credentials (optional but recommended for security)
    cred_repo = CredentialRepository(session)
    await cred_repo.delete_credentials(tenant_id, server_id)
    
    await AuditLogger.log(
        action="REVOKE_ACCESS",
        resource_type="server",
        tenant_id=tenant_id,
        resource_id=str(server_id),
        success=True,
        details={"revoked_by": str(admin.id)},
        ip_address=request.client.host if request.client else None,
    )
    
    return {"message": "Access revoked and credentials cleaned up"}


@router.get("/admin/servers", response_model=List[ServerResponse])
async def admin_list_all_servers(
    admin: TenantModel = Depends(get_current_admin),
    repo: MCPServerRepository = Depends(get_server_repo),
):
    """**Admin Only**: List all servers in the system."""
    servers = await repo.list_all()
    return [ServerResponse.model_validate(s) for s in servers]


@router.get("/admin/servers/{server_id}/tenants")
async def admin_list_server_tenants(
    server_id: UUID,
    admin: TenantModel = Depends(get_current_admin),
    repo: MCPServerRepository = Depends(get_server_repo),
):
    """**Admin Only**: List all tenants who have access to a specific server."""
    server = await repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    result = await repo.session.execute(
        select(TenantModel.id, TenantModel.name, tenant_server_access.c.permission_level)
        .join(tenant_server_access, TenantModel.id == tenant_server_access.c.tenant_id)
        .where(tenant_server_access.c.server_id == str(server_id))
    )
    
    tenants = []
    for row in result.all():
        tenants.append({
            "tenant_id": str(row.id),
            "name": row.name,
            "permission_level": row.permission_level
        })
    
    return {"server_id": str(server_id), "tenants": tenants}


# ==================== TENANT ENDPOINTS ====================

async def get_current_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: AsyncSession = Depends(get_db_session)
) -> TenantModel:
    """Dependency to verify tenant access (non-admin)."""
    tenant_id = UUID(x_tenant_id)
    repo = TenantRepository(session)
    tenant = await auth_service.authenticate(repo, tenant_id, x_api_key)
    return tenant


def get_server_repo(session: AsyncSession = Depends(get_db_session)):
    return MCPServerRepository(session)


@router.get("/tenants/servers", response_model=List[ServerResponse])
async def tenant_list_accessible_servers(
    tenant: TenantModel = Depends(get_current_tenant),
    repo: MCPServerRepository = Depends(get_server_repo),
):
    """
    **Tenant**: List all MCP servers that have been made available to me by admin.
    """
    servers = await repo.list_by_tenant(UUID(tenant.id))
    return [ServerResponse.model_validate(s) for s in servers]


@router.post("/tenants/credentials")
async def tenant_store_credentials(
    request: Request,
    server_id: UUID = Query(...),
    credentials: Dict[str, Any] = None,  # e.g., {"google_api_key": "...", "client_id": "..."}
    tenant: TenantModel = Depends(get_current_tenant),
    server_repo: MCPServerRepository = Depends(get_server_repo),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **Tenant**: Store my credentials for a specific MCP server.
    Credentials are encrypted and isolated to this tenant only.
    """
    if credentials is None:
        raise HTTPException(status_code=400, detail="Credentials body required")
        
    trace_id = AuditLogger.create_trace(UUID(tenant.id), "store_credentials")
    
    # Verify tenant has access to this server
    has_access = await server_repo.check_access(server_id, UUID(tenant.id))
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this server"
        )
    
    # Encrypt credentials
    encrypted = encryption_service.encrypt(credentials)
    
    # Store in DB
    cred_repo = CredentialRepository(session)
    await cred_repo.store_credentials(UUID(tenant.id), server_id, encrypted)
    
    await AuditLogger.log(
        action="STORE_CREDENTIALS",
        resource_type="credentials",
        tenant_id=UUID(tenant.id),
        resource_id=str(server_id),
        success=True,
        details={"server_id": str(server_id)},  # Don't log actual creds!
        ip_address=request.client.host if request.client else None,
        trace_id=trace_id,
    )
    
    return {
        "message": "Credentials stored securely",
        "server_id": str(server_id),
        "tenant_id": str(tenant.id)
    }


@router.get("/tenants/credentials")
async def tenant_list_my_credentials(
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **Tenant**: List my stored credentials (metadata only, not decrypted values).
    """
    cred_repo = CredentialRepository(session)
    creds = await cred_repo.list_tenant_credentials(UUID(tenant.id))
    
    # Return metadata only, not the encrypted blob
    results = []
    for cred in creds:
        results.append({
            "credential_id": str(cred.id),
            "server_id": str(cred.server_id),
            "server_name": cred.server.name if hasattr(cred, 'server') and cred.server else "Unknown",
            "created_at": cred.created_at.isoformat() if cred.created_at else None,
            "updated_at": cred.updated_at.isoformat() if cred.updated_at else None
        })
    
    return results


@router.get("/tenants/credentials/{server_id}")
async def tenant_get_credentials_for_server(
    server_id: UUID,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **Tenant**: Retrieve my decrypted credentials for a specific server.
    Use this when you need to actually use the credentials (e.g., to connect to Google API).
    """
    cred_repo = CredentialRepository(session)
    cred = await cred_repo.get_credentials(UUID(tenant.id), server_id)
    
    if not cred:
        raise HTTPException(status_code=404, detail="No credentials found for this server")
    
    # Decrypt and return
    try:
        decrypted = encryption_service.decrypt(cred.encrypted_credentials)
        return {
            "server_id": str(server_id),
            "credentials": decrypted,
            "updated_at": cred.updated_at.isoformat() if cred.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt credentials")


@router.delete("/tenants/credentials/{server_id}")
async def tenant_delete_credentials(
    server_id: UUID,
    tenant: TenantModel = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
):
    """**Tenant**: Delete my stored credentials for a server."""
    cred_repo = CredentialRepository(session)
    success = await cred_repo.delete_credentials(UUID(tenant.id), server_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    return {"message": "Credentials deleted"}


# ==================== BOOTSTRAP ====================

@router.post("/admin/bootstrap")
async def create_initial_admin(
    request: Request,
    data: TenantCreateRequest,
    admin_secret: str = Header(..., alias="X-Admin-Secret"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Bootstrap endpoint to create the first admin.
    Requires ADMIN_CREATION_SECRET from environment.
    """
    
    if admin_secret != settings.admin_creation_secret.get_secret_value():
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Check if any admin exists
    result = await session.execute(
        select(TenantModel).where(TenantModel.is_admin == True)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Admin already exists. Use normal creation flow.")
    
    api_key = auth_service.generate_api_key()
    admin = TenantModel(
        name=data.name,
        api_key_hash=auth_service.hash_api_key(api_key),
        is_admin=True,
        is_active=True,
        settings=data.settings,
        allowed_origins=data.allowed_origins
    )
    
    repo = TenantRepository(session)
    created = await repo.create(admin)
    
    return {
        "id": str(created.id),
        "name": created.name,
        "api_key": api_key,
        "is_admin": True,
        "warning": "SAVE THIS KEY. It will not be shown again."
    }
