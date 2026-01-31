# API Contracts - MCP Registry Backend

**Generated:** 2026-01-31
**Project:** mcp-registry
**Base URL:** `/api/v1`
**Authentication:** Header-based (X-Tenant-ID, X-API-Key)

---

## Overview

The MCP Registry API provides two distinct endpoint groups:
- **Admin Endpoints** - Global server management and tenant access control
- **Tenant Endpoints** - Access assigned servers and manage credentials
- **Bootstrap Endpoint** - One-time initial admin creation

All endpoints require authentication via headers:
- `X-Tenant-ID`: Tenant UUID
- `X-API-Key`: API key generated during tenant creation

---

## Admin Endpoints

Admin endpoints require `is_admin=true` on the authenticated tenant.

### 1. Register MCP Server

**POST** `/api/v1/admin/servers`

**Description:** Register a new global MCP server to the registry.

**Authentication:** Admin only

**Request Body:**
```json
{
  "name": "google-ai-mcp",
  "description": "Google AI Platform MCP Server",
  "version": "1.0.0",
  "config": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@google/mcp-server"],
    "env": {},
    "timeout": 30
  },
  "capabilities": {
    "tools": [
      {
        "name": "search",
        "description": "Search Google",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string"}
          }
        }
      }
    ],
    "resources": [],
    "prompts": [],
    "sampling": false,
    "roots": []
  },
  "tags": ["ai", "google", "search"],
  "metadata": {},
  "access_control": {}
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "admin-tenant-uuid",
  "name": "google-ai-mcp",
  "description": "Google AI Platform MCP Server",
  "version": "1.0.0",
  "status": "active",
  "config": {...},
  "capabilities": {...},
  "tags": ["ai", "google", "search"],
  "created_at": "2026-01-31T20:00:00Z",
  "updated_at": "2026-01-31T20:00:00Z",
  "health_status": null
}
```

**Audit:** Logs `CREATE` action with server name and admin details

---

### 2. Grant Tenant Access to Server

**POST** `/api/v1/admin/servers/{server_id}/tenants/{tenant_id}`

**Description:** Grant a tenant permission to use a specific MCP server.

**Authentication:** Admin only

**Path Parameters:**
- `server_id` (UUID) - Server to grant access to
- `tenant_id` (UUID) - Tenant receiving access

**Query Parameters:**
- `permission_level` (string, optional) - `"use"` (default) or `"manage"`

**Response:** `200 OK`
```json
{
  "message": "Access granted to TenantName for server google-ai-mcp",
  "tenant_id": "tenant-uuid",
  "server_id": "server-uuid",
  "permission_level": "use"
}
```

**Audit:** Logs `GRANT_ACCESS` action with granted_by admin ID

**Errors:**
- `404` - Server or tenant not found

---

### 3. Revoke Tenant Access

**DELETE** `/api/v1/admin/servers/{server_id}/tenants/{tenant_id}`

**Description:** Revoke tenant's access to a server and delete their stored credentials.

**Authentication:** Admin only

**Path Parameters:**
- `server_id` (UUID)
- `tenant_id` (UUID)

**Response:** `200 OK`
```json
{
  "message": "Access revoked and credentials cleaned up"
}
```

**Audit:** Logs `REVOKE_ACCESS` action

**Errors:**
- `404` - Access grant not found

**Side Effects:**
- Deletes tenant's stored credentials for this server

---

### 4. List All Servers

**GET** `/api/v1/admin/servers`

**Description:** List all MCP servers in the global registry.

**Authentication:** Admin only

**Response:** `200 OK`
```json
[
  {
    "id": "server-uuid",
    "tenant_id": "admin-uuid",
    "name": "google-ai-mcp",
    "description": "...",
    "version": "1.0.0",
    "status": "active",
    "config": {...},
    "capabilities": {...},
    "tags": ["ai", "google"],
    "created_at": "2026-01-31T20:00:00Z",
    "updated_at": "2026-01-31T20:00:00Z",
    "health_status": null
  }
]
```

---

### 5. List Server's Authorized Tenants

**GET** `/api/v1/admin/servers/{server_id}/tenants`

**Description:** List all tenants with access to a specific server.

**Authentication:** Admin only

**Path Parameters:**
- `server_id` (UUID)

**Response:** `200 OK`
```json
{
  "server_id": "server-uuid",
  "tenants": [
    {
      "tenant_id": "tenant-uuid-1",
      "name": "Acme Corp",
      "permission_level": "use"
    },
    {
      "tenant_id": "tenant-uuid-2",
      "name": "Widget Inc",
      "permission_level": "manage"
    }
  ]
}
```

**Errors:**
- `404` - Server not found

---

## Tenant Endpoints

Tenant endpoints are available to all authenticated tenants (admin flag not required).

### 6. List Accessible Servers

**GET** `/api/v1/tenants/servers`

**Description:** List all MCP servers that have been made available to this tenant by admin.

**Authentication:** Tenant (any)

**Response:** `200 OK`
```json
[
  {
    "id": "server-uuid",
    "tenant_id": "admin-uuid",
    "name": "google-ai-mcp",
    "description": "Google AI Platform MCP Server",
    "version": "1.0.0",
    "status": "active",
    "config": {...},
    "capabilities": {...},
    "tags": ["ai", "google"],
    "created_at": "2026-01-31T20:00:00Z",
    "updated_at": "2026-01-31T20:00:00Z",
    "health_status": null
  }
]
```

---

### 7. Store Credentials

**POST** `/api/v1/tenants/credentials`

**Description:** Store encrypted credentials for a specific MCP server.

**Authentication:** Tenant (any)

**Query Parameters:**
- `server_id` (UUID, required) - Server to store credentials for

**Request Body:**
```json
{
  "google_api_key": "AIzaSy...",
  "client_id": "123456.apps.googleusercontent.com",
  "client_secret": "GOCSPX-..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Credentials stored securely",
  "server_id": "server-uuid",
  "tenant_id": "tenant-uuid"
}
```

**Audit:** Logs `STORE_CREDENTIALS` action (credentials NOT logged)

**Errors:**
- `400` - Credentials body required
- `403` - Tenant does not have access to this server

**Security:**
- Credentials encrypted with Fernet symmetric encryption
- Stored as binary blob in database
- Isolated per tenant (cannot access other tenant's credentials)

---

### 8. List Credential Metadata

**GET** `/api/v1/tenants/credentials`

**Description:** List metadata for all stored credentials (does NOT return decrypted values).

**Authentication:** Tenant (any)

**Response:** `200 OK`
```json
[
  {
    "credential_id": "cred-uuid",
    "server_id": "server-uuid",
    "server_name": "google-ai-mcp",
    "created_at": "2026-01-31T20:00:00Z",
    "updated_at": "2026-01-31T20:05:00Z"
  }
]
```

---

### 9. Get Decrypted Credentials

**GET** `/api/v1/tenants/credentials/{server_id}`

**Description:** Retrieve decrypted credentials for a specific server.

**Authentication:** Tenant (any)

**Path Parameters:**
- `server_id` (UUID)

**Response:** `200 OK`
```json
{
  "server_id": "server-uuid",
  "credentials": {
    "google_api_key": "AIzaSy...",
    "client_id": "123456.apps.googleusercontent.com",
    "client_secret": "GOCSPX-..."
  },
  "updated_at": "2026-01-31T20:05:00Z"
}
```

**Errors:**
- `404` - No credentials found for this server
- `500` - Failed to decrypt credentials

**Use Case:** Retrieve credentials when connecting to downstream MCP server

---

### 10. Delete Credentials

**DELETE** `/api/v1/tenants/credentials/{server_id}`

**Description:** Delete stored credentials for a server.

**Authentication:** Tenant (any)

**Path Parameters:**
- `server_id` (UUID)

**Response:** `200 OK`
```json
{
  "message": "Credentials deleted"
}
```

**Errors:**
- `404` - Credentials not found

---

## Bootstrap Endpoint

### 11. Create Initial Admin

**POST** `/api/v1/admin/bootstrap`

**Description:** One-time endpoint to create the first admin account.

**Authentication:** Special header required

**Headers:**
- `X-Admin-Secret` - Must match `ADMIN_CREATION_SECRET` environment variable

**Request Body:**
```json
{
  "name": "Root Admin",
  "settings": {},
  "allowed_origins": ["https://console.example.com"]
}
```

**Response:** `200 OK`
```json
{
  "id": "admin-uuid",
  "name": "Root Admin",
  "api_key": "mcpreg_abc123xyz789...",
  "is_admin": true,
  "warning": "SAVE THIS KEY. It will not be shown again."
}
```

**Errors:**
- `403` - Invalid admin secret
- `400` - Admin already exists

**Important:** API key is only shown once. Must be saved immediately.

---

## Authentication

All endpoints (except bootstrap) require two headers:

```http
X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000
X-API-Key: mcpreg_abc123xyz789...
```

**Authentication Flow:**
1. Client sends headers with request
2. Server looks up tenant by `X-Tenant-ID`
3. Server hashes `X-API-Key` (Argon2) and compares with stored hash
4. If match and `is_active=true`, authentication succeeds
5. Admin endpoints additionally check `is_admin=true`

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Credentials body required"
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have access to this server"
}
```

### 404 Not Found
```json
{
  "detail": "Server not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

**Middleware:** `RateLimitMiddleware` (configurable)

**Default Limits:**
- Configurable via `settings.rate_limit_enabled`
- Implementation uses in-memory or Redis-based rate limiting

---

## CORS Configuration

**Middleware:** `CORSMiddleware`

**Settings:**
- `allow_origins`: From `settings.cors_origins`
- `allow_credentials`: `true`
- `allow_methods`: `["*"]`
- `allow_headers`: `["*"]`

---

## OpenAPI Documentation

**Development Mode Only:**
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

**Production:** Documentation endpoints disabled (`settings.debug=false`)

---

## Audit Logging

All endpoints log to audit system via `AuditLogger`:

**Logged Information:**
- `action`: CREATE, READ, UPDATE, DELETE, GRANT_ACCESS, REVOKE_ACCESS, STORE_CREDENTIALS
- `resource_type`: server, tenant, credentials
- `tenant_id`: Who performed the action
- `resource_id`: What was affected
- `success`: True/False
- `details`: Additional context (never includes sensitive data like credentials)
- `ip_address`: Client IP
- `trace_id`: Request correlation ID (for admin operations)

**Storage:** Audit logs written via structured logging (structlog) → JSON format

---

## Summary

- **12 total endpoints** (5 admin, 6 tenant, 1 bootstrap)
- **Header-based authentication** (X-Tenant-ID, X-API-Key)
- **Role-based access** (admin vs tenant)
- **Encrypted credential storage** (Fernet)
- **Comprehensive audit logging**
- **RESTful design** with standard HTTP methods
- **JSON request/response** format
- **OpenAPI documentation** (dev mode)
