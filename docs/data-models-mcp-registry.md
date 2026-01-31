# Data Models - MCP Registry Backend

**Generated:** 2026-01-31
**Project:** mcp-registry
**Database:** PostgreSQL with SQLAlchemy (Async)

---

## Overview

The MCP Registry uses a multi-tenant architecture with role-based access control. The database schema supports:
- **Admin** tenants who manage the global server registry
- **Regular** tenants who use assigned MCP servers
- **Encrypted credential storage** per tenant-server pair
- **Audit trail** via access grants tracking

---

## Database Tables

### 1. `tenants` Table

**Purpose:** Stores tenant accounts (both admins and regular tenants)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique tenant identifier |
| `created_at` | TIMESTAMP | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `name` | VARCHAR(256) | NOT NULL | Tenant name |
| `api_key_hash` | VARCHAR(256) | NOT NULL, INDEXED | Hashed API key (Argon2) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active status |
| `is_admin` | BOOLEAN | DEFAULT FALSE | Admin flag |
| `settings` | JSONB | DEFAULT {} | Tenant-specific settings |
| `allowed_origins` | JSONB | DEFAULT [] | CORS allowed origins |
| `metadata` | JSONB | DEFAULT {} | Additional metadata |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `api_key_hash` (for authentication lookups)

**Relationships:**
- `accessible_servers` → Many-to-many with `mcp_servers` via `tenant_server_access`
- `credentials` → One-to-many with `tenant_server_credentials` (cascade delete)

---

### 2. `mcp_servers` Table

**Purpose:** Global registry of MCP servers (admin-managed)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique server identifier |
| `created_at` | TIMESTAMP | NOT NULL | Registration timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `created_by_admin_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Admin who registered |
| `name` | VARCHAR(256) | NOT NULL, UNIQUE | Server name |
| `description` | TEXT | DEFAULT '' | Server description |
| `version` | VARCHAR(32) | NOT NULL | Semantic version |
| `status` | VARCHAR(32) | DEFAULT 'active' | Status (active/inactive/error/maintenance) |
| `config` | JSONB | NOT NULL | Server configuration (transport, command, etc.) |
| `capabilities` | JSONB | DEFAULT {} | MCP capabilities (tools, resources, prompts) |
| `tags` | JSONB | DEFAULT [] | Searchable tags |
| `metadata` | JSONB | DEFAULT {} | Additional metadata |
| `last_health_check` | TIMESTAMP | NULLABLE | Last health check time |
| `health_status` | VARCHAR(64) | NULLABLE | Health check result |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `name`
- INDEX on `created_by_admin_id`

**Foreign Keys:**
- `created_by_admin_id` → `tenants.id`

**Relationships:**
- `authorized_tenants` → Many-to-many with `tenants` via `tenant_server_access`
- `tenant_credentials` → One-to-many with `tenant_server_credentials` (cascade delete)

---

### 3. `tenant_server_credentials` Table

**Purpose:** Encrypted credential storage per tenant-server pair

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique credential identifier |
| `tenant_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Tenant who owns credentials |
| `server_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Server these credentials are for |
| `encrypted_credentials` | BYTEA | NOT NULL | Encrypted credential blob |
| `created_at` | TIMESTAMP | NOT NULL | Credential creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `tenant_id`
- INDEX on `server_id`

**Foreign Keys:**
- `tenant_id` → `tenants.id` (ON DELETE CASCADE)
- `server_id` → `mcp_servers.id` (ON DELETE CASCADE)

**Constraints:**
- One credential entry per tenant-server pair (enforced by application logic)

**Relationships:**
- `tenant` → Many-to-one with `tenants`
- `server` → Many-to-one with `mcp_servers`

---

### 4. `tenant_server_access` Association Table

**Purpose:** Many-to-many relationship tracking which tenants can access which servers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `tenant_id` | UUID | PRIMARY KEY (composite), FOREIGN KEY | Tenant being granted access |
| `server_id` | UUID | PRIMARY KEY (composite), FOREIGN KEY | Server being accessed |
| `granted_at` | TIMESTAMP | DEFAULT NOW | When access was granted |
| `granted_by` | UUID | FOREIGN KEY | Admin who granted access |
| `permission_level` | VARCHAR(32) | DEFAULT 'use' | Permission level ('use' or 'manage') |

**Primary Key:** Composite (`tenant_id`, `server_id`)

**Foreign Keys:**
- `tenant_id` → `tenants.id` (ON DELETE CASCADE)
- `server_id` → `mcp_servers.id` (ON DELETE CASCADE)
- `granted_by` → `tenants.id`

---

## Entity Relationships

```
┌────────────────┐           ┌──────────────────────────┐           ┌────────────────┐
│    Tenants     │◄─────────►│  tenant_server_access    │◄─────────►│  MCP Servers   │
│                │ many-many  │                          │  many-many│                │
│ - Admin        │            │ - granted_by (admin_id)  │           │ - Global       │
│ - Regular      │            │ - permission_level       │           │ - Admin-owned  │
└────────┬───────┘            └──────────────────────────┘           └────────┬───────┘
         │                                                                     │
         │ 1:N                                                                 │ 1:N
         │                                                                     │
         │                  ┌──────────────────────────────┐                  │
         └─────────────────►│ tenant_server_credentials    │◄─────────────────┘
                            │                              │
                            │ - encrypted_credentials      │
                            │ - Per tenant-server pair     │
                            └──────────────────────────────┘
```

---

## Data Flow

### Admin Workflow
1. **Bootstrap:** Admin created via `/admin/bootstrap` endpoint (one-time)
2. **Register Server:** Admin registers MCP server → Creates `mcp_servers` entry
3. **Grant Access:** Admin assigns server to tenant → Creates `tenant_server_access` entry

### Tenant Workflow
1. **View Servers:** Tenant lists accessible servers via `tenant_server_access` join
2. **Store Credentials:** Tenant saves encrypted credentials → Creates `tenant_server_credentials` entry
3. **Use Server:** Tenant retrieves decrypted credentials for MCP server usage

---

## Pydantic Models (Request/Response)

### Request Models
- **ServerRegistrationRequest** - Admin registers MCP server
- **TenantCreateRequest** - Create new tenant

### Response Models
- **ServerResponse** - MCP server details
- **TenantResponse** - Tenant details (excludes sensitive data)

### Validation Models
- **MCPServerConfig** - Transport-specific validation (stdio, http, sse, websocket)
- **MCPCapabilities** - Tools, resources, prompts, sampling, roots
- **MCPTool** - JSON Schema validation for tool definitions
- **MCPResource** - URI pattern validation
- **MCPPrompt** - Prompt definitions

---

## Security Features

1. **API Key Hashing:** Argon2-cffi for password-strength hashing
2. **Credential Encryption:** Encrypted blob storage (Fernet symmetric encryption)
3. **Multi-tenant Isolation:** Foreign keys + application-level access control
4. **Cascade Deletes:** Automatic cleanup of credentials when tenant/server deleted
5. **Audit Trail:** `granted_at`, `granted_by` tracked in access table

---

## Database Migrations

**Migration Tool:** Alembic

**Migration Files:**
- `alembic/versions/001_initial.py` - Initial schema creation

**Migration Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Indexes & Performance

**Primary Indexes:**
- All tables have UUID primary keys
- `api_key_hash` indexed for fast authentication
- `created_by_admin_id` indexed for admin queries
- `tenant_id`, `server_id` indexed in credentials table

**Query Patterns:**
- Tenant authentication: `SELECT * FROM tenants WHERE api_key_hash = ?`
- List tenant servers: `JOIN tenant_server_access ON tenant_id = ?`
- Get credentials: `SELECT * FROM tenant_server_credentials WHERE tenant_id = ? AND server_id = ?`

---

## JSON Schema Fields

### `config` JSONB (mcp_servers)
```json
{
  "transport": "stdio|sse|http|websocket",
  "command": "path/to/executable",
  "args": ["--flag", "value"],
  "env": {"KEY": "VALUE"},
  "url": "https://...",
  "headers": {"Authorization": "..."},
  "timeout": 30
}
```

### `capabilities` JSONB (mcp_servers)
```json
{
  "tools": [{"name": "...", "description": "...", "inputSchema": {...}}],
  "resources": [{"uri": "...", "name": "...", "mimeType": "..."}],
  "prompts": [{"name": "...", "description": "...", "arguments": [...]}],
  "sampling": false,
  "roots": ["/path/to/root"]
}
```

### `encrypted_credentials` BYTEA (tenant_server_credentials)
- Fernet encrypted JSON
- Decrypts to: `{"google_api_key": "...", "client_id": "...", ...}`

---

## Summary

- **3 core tables** + 1 association table
- **Multi-tenant architecture** with admin/tenant separation
- **Encrypted credential storage** per tenant-server pair
- **PostgreSQL JSONB** for flexible configuration storage
- **Alembic migrations** for schema version control
- **Cascade deletes** for data integrity
