
### `USAGE.md`

```markdown
# MCP Registry Usage Guide

## Overview

The MCP Registry provides multi-tenant registration and discovery of Model Context Protocol (MCP) servers with enterprise features including audit logging, rate limiting, and observability.

## Authentication

All API requests require two headers:
- `X-Tenant-ID`: Your tenant UUID
- `X-API-Key`: Your secret API key (provided on tenant creation)

## API Endpoints

### 1. Create Tenant (Admin Only)

```bash
curl -X POST https://mcp-registry.yourdomain.com/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "settings": {"max_servers": 50},
    "allowed_origins": ["https://acme.com"]
  }'
#### Response
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "created_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "settings": {"max_servers": 50},
  "api_key": "sk_abc123xyz...",  // SAVE THIS - shown only once!
  "warning": "Save this API key, it will not be shown again"
}

### Register MCP Server
curl -X POST https://mcp-registry.yourdomain.com/api/v1/servers \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: sk_abc123xyz..." \
  -d '{
    "name": "Documentation Server",
    "description": "Internal documentation search",
    "version": "1.2.0",
    "config": {
      "transport": "stdio",
      "command": "python",
      "args": ["/app/server.py"],
      "env": {"API_KEY": "secret123"},
      "timeout": 30
    },
    "capabilities": {
      "tools": [{
        "name": "search_docs",
        "description": "Search documentation",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
      }],
      "resources": [{"uri": "docs://readme", "name": "Readme"}],
      "prompts": []
    },
    "tags": ["docs", "internal"],
    "access_control": {
      "public": false,
      "allowed_tenants": []
    }
  }'

### List Servres
curl "https://mcp-registry.yourdomain.com/api/v1/servers?status=active&tags=docs" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: sk_abc123xyz..."

### Update Server Status
curl -X PATCH "https://mcp-registry.yourdomain.com/api/v1/servers/{server_id}/status?status=maintenance" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: sk_abc123xyz..."

curl https://mcp-registry.yourdomain.com/health
