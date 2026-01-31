# Generate secure passwords
export DB_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# Base64 encode for Kubernetes (though stringData handles this)
echo -n "postgresql+asyncpg://mcp_user:${DB_PASSWORD}@mcp-postgres:5432/mcp_registry"
