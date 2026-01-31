"""Enhanced authentication with admin support."""

import hashlib
import secrets
from uuid import UUID

from fastapi import HTTPException, status

from mcp_registry.db.repositories import TenantRepository
from mcp_registry.config import get_settings

settings = get_settings()


class AuthService:
    """Handle API key authentication with role checking."""
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Securely hash API key."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new secure API key."""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    async def authenticate(
        self, 
        repo: TenantRepository, 
        tenant_id: UUID, 
        api_key: str
    ) -> "TenantModel":
        """
        Authenticate and return tenant.
        Raises HTTPException if invalid.
        """
        from mcp_registry.utils.cache import cache_get, cache_set
        
        # Check cache
        cache_key = f"auth:{tenant_id}:{self.hash_api_key(api_key)}"
        cached_id = await cache_get(cache_key)
        
        if cached_id:
            tenant = await repo.get_by_id(UUID(cached_id))
        else:
            api_key_hash = self.hash_api_key(api_key)
            tenant = await repo.get_by_api_key_hash(api_key_hash)
        
        if not tenant or str(tenant.id) != str(tenant_id) or not tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Cache valid auth
        if not cached_id:
            await cache_set(cache_key, str(tenant.id), ttl=300)
        
        return tenant
    
    async def authenticate_admin(
        self,
        repo: TenantRepository,
        tenant_id: UUID,
        api_key: str
    ) -> "TenantModel":
        """
        Authenticate and verify admin privileges.
        """
        tenant = await self.authenticate(repo, tenant_id, api_key)
        
        if not tenant.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return tenant


auth_service = AuthService()
