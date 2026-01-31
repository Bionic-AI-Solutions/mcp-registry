# Architecture Document - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry
**Version:** 1.0.0
**Type:** Backend API (Monolith)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Patterns](#architecture-patterns)
4. [Technology Stack](#technology-stack)
5. [Component Architecture](#component-architecture)
6. [Data Architecture](#data-architecture)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Integration Points](#integration-points)
10. [Quality Attributes](#quality-attributes)
11. [Architectural Decisions](#architectural-decisions)

---

## Executive Summary

The MCP Registry is a multi-tenant backend API service that provides registration, discovery, and credential management for Model Context Protocol (MCP) servers. Built on FastAPI with PostgreSQL and Redis, the system follows a layered architecture pattern with strong separation of concerns, enabling enterprise features including audit logging, rate limiting, and observability.

**Key Characteristics:**
- **Type:** Monolithic backend API
- **Deployment:** Kubernetes-native with horizontal pod autoscaling
- **Tenancy:** Multi-tenant with isolation via tenant_id
- **Authentication:** Header-based API key authentication (X-Tenant-ID + X-API-Key)
- **Security:** Fernet encryption for credentials, Argon2 for API key hashing
- **Scalability:** Stateless application pods, horizontal scaling via HPA

---

## System Overview

### Context Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    External Actors                          │
│                                                             │
│  ┌──────────────┐              ┌──────────────┐           │
│  │   Admin      │              │   Tenant     │           │
│  │  (is_admin)  │              │   (User)     │           │
│  └──────┬───────┘              └──────┬───────┘           │
│         │                             │                    │
│         │ X-Tenant-ID + X-API-Key     │                    │
│         │                             │                    │
└─────────┼─────────────────────────────┼────────────────────┘
          │                             │
          │         HTTPS (TLS)         │
          ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Registry API Service                      │
│                  (FastAPI Application)                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │               Request Pipeline                        │ │
│  │  CORS → Rate Limit → Audit → Authentication → Routes │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Admin Endpoints:                 Tenant Endpoints:        │
│  • Bootstrap admin               • List accessible servers │
│  • CRUD tenants                  • Store credentials       │
│  • CRUD MCP servers              • Retrieve credentials    │
│  • Grant/revoke access           • Update credentials      │
│  • List global servers           • Delete credentials      │
│                                  • Health check            │
└──────────┬──────────────────────┬────────────┬─────────────┘
           │                      │            │
           │                      │            │
           ▼                      ▼            ▼
   ┌──────────────┐      ┌──────────────┐  ┌──────────┐
   │  PostgreSQL  │      │    Redis     │  │ Langfuse │
   │   Database   │      │    Cache     │  │(Optional)│
   │              │      │              │  │          │
   │ • Tenants    │      │ • Rate limit │  │ • Traces │
   │ • Servers    │      │   counters   │  │ • Metrics│
   │ • Credentials│      │ • Session    │  └──────────┘
   │ • Access     │      │   data       │
   └──────────────┘      └──────────────┘
```

### System Capabilities

**Admin Capabilities:**
1. Bootstrap initial admin tenant
2. Create and manage tenant accounts
3. Register global MCP servers to registry
4. Grant server access to specific tenants
5. Revoke server access from tenants
6. View all registered servers

**Tenant Capabilities:**
1. List MCP servers accessible to their tenant
2. Store encrypted credentials for MCP servers
3. Retrieve encrypted credentials for MCP servers
4. Update stored credentials
5. Delete stored credentials
6. Health check monitoring

---

## Architecture Patterns

### 1. Layered Architecture

The system follows a strict layered architecture with unidirectional dependencies:

```
┌────────────────────────────────────────────────┐
│           API Layer (api/)                     │
│  • HTTP request/response handling              │
│  • Route definitions                           │
│  • Request validation (Pydantic)               │
│  • Authentication dependencies                 │
│  • Middleware (CORS, rate limit, audit)        │
└────────────────┬───────────────────────────────┘
                 │ Depends on
                 ▼
┌────────────────────────────────────────────────┐
│        Service Layer (services/)               │
│  • Business logic                              │
│  • Authentication (API key verification)       │
│  • Encryption/Decryption (Fernet)              │
│  • Audit logging (structured logs)             │
│  • Registry operations                         │
└────────────────┬───────────────────────────────┘
                 │ Depends on
                 ▼
┌────────────────────────────────────────────────┐
│     Repository Layer (db/repositories.py)      │
│  • Data access abstraction                     │
│  • CRUD operations                             │
│  • Query encapsulation                         │
│  • Transaction management                      │
└────────────────┬───────────────────────────────┘
                 │ Depends on
                 ▼
┌────────────────────────────────────────────────┐
│      Data Layer (db/base.py, db/session.py)    │
│  • SQLAlchemy ORM models                       │
│  • Database session management                 │
│  • Connection pooling                          │
│  • Async database operations (AsyncPG)         │
└────────────────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Testability (each layer can be tested independently)
- Maintainability (changes localized to specific layers)
- Reusability (services can be used by multiple routes)

### 2. Repository Pattern

All database access is abstracted through repository classes:

```python
# Repository Pattern Structure
TenantRepository:
  - create(tenant_data) → TenantModel
  - get_by_id(tenant_id) → TenantModel
  - get_by_api_key_hash(hash) → TenantModel
  - update(tenant_id, updates) → TenantModel
  - delete(tenant_id) → bool

MCPServerRepository:
  - create(server_data) → MCPServerModel
  - get_by_id(server_id) → MCPServerModel
  - list_all(filters) → List[MCPServerModel]
  - list_accessible(tenant_id) → List[MCPServerModel]
  - grant_access(server_id, tenant_id) → bool
  - revoke_access(server_id, tenant_id) → bool

CredentialRepository:
  - store(tenant_id, server_id, encrypted_blob) → CredentialModel
  - retrieve(tenant_id, server_id) → CredentialModel
  - update(credential_id, encrypted_blob) → CredentialModel
  - delete(credential_id) → bool
```

**Benefits:**
- Database independence (can swap out database without changing business logic)
- Query optimization in one place
- Easier testing with repository mocks
- Consistent data access patterns

### 3. Dependency Injection

FastAPI's built-in dependency injection manages:

```python
# Dependency Injection Pattern
@router.post("/admin/servers")
async def register_server(
    request: Request,
    data: ServerRegistrationRequest,
    admin: TenantModel = Depends(get_current_admin),      # Auth dependency
    repo: MCPServerRepository = Depends(get_server_repo), # Repository dependency
    db: AsyncSession = Depends(get_db_session)            # Database session
):
    # Route logic with injected dependencies
```

**Benefits:**
- Loose coupling between components
- Easy mocking for tests
- Clear dependency requirements
- Automatic resource cleanup (DB sessions)

### 4. Middleware Pipeline

Request processing flows through middleware stack:

```
HTTP Request
    ↓
[CORS Middleware]
    ↓ (allows cross-origin requests)
[Rate Limit Middleware]
    ↓ (enforces per-tenant rate limits via Redis)
[Audit Middleware]
    ↓ (logs all requests with trace IDs)
[Authentication Dependencies]
    ↓ (verifies tenant + API key)
[Route Handler]
    ↓
HTTP Response
```

---

## Technology Stack

### Core Framework
- **FastAPI 0.104+:** Modern async web framework with automatic OpenAPI documentation
- **Uvicorn:** ASGI server for production deployment
- **Pydantic 2.5+:** Data validation and settings management

### Database & Persistence
- **PostgreSQL 14+:** Relational database for structured data
- **AsyncPG:** High-performance async PostgreSQL driver
- **SQLAlchemy 2.0+ (async):** ORM for database abstraction
- **Alembic 1.12+:** Database migration management

### Caching & Performance
- **Redis 5.0+:** In-memory cache for rate limiting and session data
- **Connection Pooling:** SQLAlchemy engine with configurable pool

### Security
- **Argon2-cffi:** Password-strength hashing for API keys
- **Cryptography (Fernet):** Symmetric encryption for credentials
- **Email Validator:** Email validation for contact fields

### Observability
- **Structlog:** Structured logging with JSON output
- **Python-JSON-Logger:** JSON log formatting
- **Langfuse 2.0+:** LLM observability (optional)
- **Prometheus Client:** Metrics exposition

### Development Tools
- **pytest:** Testing framework
- **pytest-asyncio:** Async test support
- **httpx:** HTTP client for integration tests
- **black:** Code formatting (88 char line length)
- **ruff:** Fast Python linter

### Deployment
- **Docker:** Containerization with multi-stage builds
- **Kubernetes 1.25+:** Container orchestration
- **HPA:** Horizontal Pod Autoscaler for dynamic scaling

### Python Version
- **Python 3.11+:** Required for performance and modern async features

---

## Component Architecture

### 1. API Layer (`src/mcp_registry/api/`)

#### routes.py (396 lines)
**Responsibility:** Define all HTTP endpoints

**Admin Routes:**
```
POST   /api/v1/admin/bootstrap          - Create initial admin tenant
POST   /api/v1/admin/tenants            - Create new tenant
GET    /api/v1/admin/servers            - List all global servers
POST   /api/v1/admin/servers            - Register new MCP server
POST   /api/v1/admin/servers/{id}/access - Grant server access to tenant
DELETE /api/v1/admin/servers/{id}/access - Revoke server access from tenant
```

**Tenant Routes:**
```
GET    /api/v1/tenants/servers                    - List accessible servers
POST   /api/v1/tenants/credentials                - Store credentials
GET    /api/v1/tenants/credentials/{server_id}    - Retrieve credentials
PUT    /api/v1/tenants/credentials/{credential_id} - Update credentials
DELETE /api/v1/tenants/credentials/{credential_id} - Delete credentials
```

**Health Route:**
```
GET    /health                          - Health check endpoint
```

#### middleware.py
**Components:**
- `RateLimitMiddleware`: Redis-backed per-tenant rate limiting
- `AuditMiddleware`: Automatic request/response logging with trace IDs

#### dependencies.py
**Provides:**
- `get_db_session()`: Async database session factory
- `get_current_admin()`: Admin authentication dependency
- `get_current_tenant()`: Tenant authentication dependency
- Repository factory functions

### 2. Service Layer (`src/mcp_registry/services/`)

#### auth.py
**Responsibilities:**
- Generate cryptographically secure API keys
- Hash API keys with Argon2 (irreversible)
- Verify API key against stored hash
- Check admin privileges

**Key Functions:**
```python
generate_api_key() → str                           # sk_<random>
hash_api_key(key: str) → str                       # Argon2 hash
verify_api_key(key: str, hash: str) → bool         # Constant-time comparison
is_admin(tenant: TenantModel) → bool               # Check admin flag
```

#### encryption.py
**Responsibilities:**
- Encrypt credential payloads with Fernet
- Decrypt credential payloads
- Key derivation from master secret

**Key Functions:**
```python
encrypt_credentials(data: dict, key: str) → bytes  # Fernet encrypt
decrypt_credentials(blob: bytes, key: str) → dict  # Fernet decrypt
```

**Encryption Flow:**
```
User Credentials (JSON)
    ↓
JSON.stringify()
    ↓
Fernet.encrypt(json_bytes, encryption_key)
    ↓
Encrypted Blob (bytes)
    ↓
Store in database (BYTEA column)
```

#### audit.py
**Responsibilities:**
- Generate unique trace IDs per request
- Log structured events (JSON format)
- Track actions (CREATE, UPDATE, DELETE, GRANT_ACCESS, etc.)
- Redact sensitive data (API keys, credentials)

**Log Structure:**
```json
{
  "timestamp": "2026-01-31T20:30:00Z",
  "trace_id": "uuid-v4",
  "action": "CREATE_TENANT",
  "tenant_id": "tenant-uuid",
  "actor": "admin-uuid",
  "resource_type": "tenant",
  "resource_id": "new-tenant-uuid",
  "status": "success",
  "metadata": {...}
}
```

#### registry.py
**Responsibilities:**
- MCP server lifecycle management
- Access control logic
- Server health check coordination
- Business rule enforcement

### 3. Repository Layer (`src/mcp_registry/db/repositories.py`)

Encapsulates all database operations using async SQLAlchemy sessions.

**Repositories:**
- `TenantRepository`: Tenant CRUD + authentication lookups
- `MCPServerRepository`: Server CRUD + access control queries
- `CredentialRepository`: Encrypted credential management

**Transaction Management:**
```python
async with db.begin():  # Automatic commit/rollback
    tenant = await tenant_repo.create(data)
    await server_repo.grant_access(server_id, tenant.id)
    # Both operations succeed or both rollback
```

### 4. Data Layer (`src/mcp_registry/db/`)

#### base.py (151 lines)
**SQLAlchemy Models:**

```python
class TenantModel(Base):
    id: UUID (primary key)
    name: str
    api_key_hash: str (Argon2)
    is_admin: bool
    contact_email: str (optional)
    settings: JSON
    created_at: datetime
    updated_at: datetime

class MCPServerModel(Base):
    id: UUID (primary key)
    name: str
    description: str
    version: str
    config: JSON (transport, command, args, env, timeout)
    capabilities: JSON (tools, resources, prompts)
    tags: List[str]
    status: str (active, maintenance, deprecated)
    access_control: JSON (public, allowed_tenants)
    created_at: datetime
    updated_at: datetime

class TenantServerCredential(Base):
    id: UUID (primary key)
    tenant_id: UUID (foreign key)
    server_id: UUID (foreign key)
    credentials_encrypted: bytes (Fernet encrypted)
    created_at: datetime
    updated_at: datetime

# Many-to-many association table
tenant_server_access:
    tenant_id: UUID
    server_id: UUID
    granted_at: datetime
```

#### session.py
**Database Configuration:**
```python
engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,              # Log queries in debug mode
    pool_size=20,            # Connection pool
    max_overflow=10,
    pool_pre_ping=True,      # Verify connections before use
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)
```

### 5. Configuration (`src/mcp_registry/config.py`)

**Pydantic Settings:**
```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Security
    ENCRYPTION_KEY: str
    ADMIN_CREATION_SECRET: str

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # CORS
    CORS_ORIGINS: List[str] = []

    # Features
    RATE_LIMIT_ENABLED: bool = True

    # Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
```

---

## Data Architecture

### Entity Relationship Diagram

```
┌─────────────────────────────┐
│       TenantModel           │
│ ───────────────────────────│
│ PK: id (UUID)               │
│     name (str)              │
│     api_key_hash (str)      │◄─────────┐
│     is_admin (bool)         │          │
│     contact_email (str?)    │          │
│     settings (JSON)         │          │
│     created_at (datetime)   │          │
│     updated_at (datetime)   │          │
└─────────────┬───────────────┘          │
              │                          │
              │ 1                        │
              │                          │
              │ M                        │
              ▼                          │
┌───────────────────────────────┐        │
│   tenant_server_access        │        │
│   (Association Table)         │        │
│ ─────────────────────────────│        │
│ FK: tenant_id (UUID) ─────────┼────────┘
│ FK: server_id (UUID) ─────────┼───────┐
│     granted_at (datetime)     │       │
└───────────────────────────────┘       │
                                        │
              ┌─────────────────────────┘
              │
              │ M
              │
              │ 1
              ▼
┌─────────────────────────────┐
│     MCPServerModel          │
│ ───────────────────────────│
│ PK: id (UUID)               │◄──────────┐
│     name (str)              │           │
│     description (str)       │           │
│     version (str)           │           │
│     config (JSON)           │           │
│     capabilities (JSON)     │           │
│     tags (List[str])        │           │
│     status (str)            │           │
│     access_control (JSON)   │           │
│     created_at (datetime)   │           │
│     updated_at (datetime)   │           │
└─────────────────────────────┘           │
                                          │
                                          │ 1
                                          │
                                          │ M
┌─────────────────────────────────────┐   │
│   TenantServerCredential            │   │
│ ───────────────────────────────────│   │
│ PK: id (UUID)                       │   │
│ FK: tenant_id (UUID) ───────────────┼───┼──► TenantModel
│ FK: server_id (UUID) ───────────────┼───┘
│     credentials_encrypted (bytes)   │
│     created_at (datetime)           │
│     updated_at (datetime)           │
└─────────────────────────────────────┘
```

### Data Flow Diagrams

#### Admin Registers MCP Server & Grants Access

```
┌─────────┐
│  Admin  │
└────┬────┘
     │ 1. POST /admin/servers
     │    (server config + capabilities)
     ▼
┌─────────────────────────────┐
│  API Layer (routes.py)      │
│  • Validate admin auth      │
│  • Validate request schema  │
└────┬────────────────────────┘
     │ 2. Call service layer
     ▼
┌─────────────────────────────┐
│  Service Layer              │
│  (registry.py)              │
│  • Validate business rules  │
└────┬────────────────────────┘
     │ 3. Call repository
     ▼
┌─────────────────────────────┐
│  MCPServerRepository        │
│  • INSERT INTO mcp_servers  │
└────┬────────────────────────┘
     │ 4. Return server model
     ▼
┌─────────────────────────────┐
│  PostgreSQL Database        │
│  • mcp_servers table        │
│  • New row created          │
└─────────────────────────────┘

     Admin then grants access:

     │ 5. POST /admin/servers/{id}/access
     │    (tenant_id to grant)
     ▼
┌─────────────────────────────┐
│  MCPServerRepository        │
│  • INSERT INTO              │
│    tenant_server_access     │
└────┬────────────────────────┘
     │ 6. Access granted
     ▼
┌─────────────────────────────┐
│  tenant_server_access       │
│  (tenant_id, server_id)     │
└─────────────────────────────┘
```

#### Tenant Stores Credentials

```
┌─────────┐
│ Tenant  │
└────┬────┘
     │ 1. POST /tenants/credentials
     │    (server_id + credentials JSON)
     ▼
┌──────────────────────────────────┐
│  API Layer                       │
│  • Verify tenant auth            │
│  • Check tenant has access       │
│    to server (via join query)    │
└────┬─────────────────────────────┘
     │ 2. Access verified
     ▼
┌──────────────────────────────────┐
│  Encryption Service              │
│  • JSON.stringify(credentials)   │
│  • Fernet.encrypt(json, key)     │
└────┬─────────────────────────────┘
     │ 3. Encrypted blob
     ▼
┌──────────────────────────────────┐
│  CredentialRepository            │
│  • INSERT INTO                   │
│    tenant_server_credentials     │
│    (tenant_id, server_id, blob)  │
└────┬─────────────────────────────┘
     │ 4. Stored
     ▼
┌──────────────────────────────────┐
│  PostgreSQL Database             │
│  • credentials_encrypted (bytes) │
└──────────────────────────────────┘
     │ 5. Audit log (no credentials)
     ▼
┌──────────────────────────────────┐
│  Audit Service                   │
│  • Log: STORE_CREDENTIALS action │
│  • Redact sensitive data         │
└──────────────────────────────────┘
```

---

## Security Architecture

### Authentication Flow

```
HTTP Request
    ↓
Headers:
  X-Tenant-ID: "550e8400-..."
  X-API-Key: "sk_abc123..."
    ↓
┌─────────────────────────────────┐
│  Authentication Dependency      │
│  (get_current_admin or          │
│   get_current_tenant)           │
└────┬────────────────────────────┘
     │ 1. Extract headers
     ▼
┌─────────────────────────────────┐
│  TenantRepository               │
│  • Query by tenant_id           │
│  • Retrieve api_key_hash        │
└────┬────────────────────────────┘
     │ 2. Get tenant record
     ▼
┌─────────────────────────────────┐
│  Auth Service                   │
│  • verify_api_key(              │
│      provided_key,              │
│      stored_hash                │
│    )                            │
│  • Constant-time comparison     │
└────┬────────────────────────────┘
     │ 3. If valid
     ▼
┌─────────────────────────────────┐
│  Return TenantModel to route    │
│  (inject via Depends())         │
└─────────────────────────────────┘
     │ 4. If admin required
     ▼
┌─────────────────────────────────┐
│  Check tenant.is_admin == True  │
│  Raise 403 if False             │
└─────────────────────────────────┘
```

### API Key Lifecycle

```
1. Creation (Admin creates tenant):
   ┌──────────────────────────────┐
   │ generate_api_key()           │
   │ → "sk_" + random(32 bytes)   │
   └────┬─────────────────────────┘
        │
        ▼
   ┌──────────────────────────────┐
   │ hash_api_key(key)            │
   │ → Argon2 hash                │
   └────┬─────────────────────────┘
        │
        ▼
   ┌──────────────────────────────┐
   │ Store hash in database       │
   │ Return raw key to user       │
   │ (ONLY ONCE - never stored)   │
   └──────────────────────────────┘

2. Authentication (Every request):
   ┌──────────────────────────────┐
   │ User provides key in header  │
   └────┬─────────────────────────┘
        │
        ▼
   ┌──────────────────────────────┐
   │ Retrieve hash from database  │
   └────┬─────────────────────────┘
        │
        ▼
   ┌──────────────────────────────┐
   │ Argon2.verify(key, hash)     │
   │ → True/False                 │
   └──────────────────────────────┘
```

### Credential Encryption

**Encryption Algorithm:** Fernet (symmetric)
- AES-128 in CBC mode
- HMAC for integrity verification
- Timestamp for expiration (not enforced in current implementation)

**Encryption Flow:**
```python
# Store
credentials = {"api_key": "secret", "endpoint": "https://..."}
json_bytes = json.dumps(credentials).encode()
encrypted = Fernet(encryption_key).encrypt(json_bytes)
# Store encrypted bytes in database

# Retrieve
encrypted_blob = db.query(...)
json_bytes = Fernet(encryption_key).decrypt(encrypted_blob)
credentials = json.loads(json_bytes)
```

**Key Management:**
- Encryption key stored in Kubernetes Secret
- Key rotation not yet implemented (future enhancement)
- Single master key for all tenants (consider per-tenant keys for multi-tier security)

### Rate Limiting

**Implementation:** Redis-backed sliding window counter

```python
# Rate limit check (per tenant)
key = f"rate_limit:{tenant_id}:{window}"
count = redis.incr(key)
if count == 1:
    redis.expire(key, window_seconds)
if count > limit:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

**Configuration:**
- Configurable limits per tenant (in tenant.settings JSON)
- Global default: 100 requests/minute
- Redis key TTL matches window duration

### Audit Logging

**Logged Events:**
- All API requests (except health checks)
- Tenant creation
- Server registration
- Access grants/revokes
- Credential storage (data redacted)
- Authentication failures

**Log Format:** JSON (structured logging via structlog)

**Sensitive Data Handling:**
- API keys: Redacted (only last 4 chars shown)
- Credentials: Never logged
- Passwords: N/A (not used in this system)

---

## Deployment Architecture

### Kubernetes Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                     │
│                                                           │
│  Namespace: mcp-registry                                  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  Ingress                            │ │
│  │  (nginx-ingress)                                    │ │
│  │  TLS: cert-manager (Let's Encrypt)                  │ │
│  │  Host: mcp-registry.yourdomain.com                  │ │
│  └─────────────────┬───────────────────────────────────┘ │
│                    │                                      │
│                    ▼                                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Service (LoadBalancer/ClusterIP)       │ │
│  │              Port: 80 → 8000                        │ │
│  └─────────────────┬───────────────────────────────────┘ │
│                    │                                      │
│         ┌──────────┴──────────┐                          │
│         │                     │                          │
│         ▼                     ▼                          │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │   Pod 1      │      │   Pod 2      │ ... (HPA)       │
│  │ ────────────│      │ ────────────│                 │
│  │ Container:   │      │ Container:   │                 │
│  │ mcp-registry │      │ mcp-registry │                 │
│  │              │      │              │                 │
│  │ Resources:   │      │ Resources:   │                 │
│  │ 256Mi / 100m │      │ 256Mi / 100m │                 │
│  │ 512Mi / 500m │      │ 512Mi / 500m │                 │
│  │              │      │              │                 │
│  │ Probes:      │      │ Probes:      │                 │
│  │ Liveness     │      │ Liveness     │                 │
│  │ Readiness    │      │ Readiness    │                 │
│  └──────┬───────┘      └──────┬───────┘                 │
│         │                     │                          │
│         └──────────┬──────────┘                          │
│                    │                                      │
│         ┌──────────┴──────────┐                          │
│         │                     │                          │
│         ▼                     ▼                          │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │  PostgreSQL  │      │    Redis     │                 │
│  │  StatefulSet │      │  Deployment  │                 │
│  │              │      │              │                 │
│  │  PVC: 10Gi   │      │  (Ephemeral) │                 │
│  │  Service:    │      │  Service:    │                 │
│  │  postgres:   │      │  redis:6379  │                 │
│  │  5432        │      │              │                 │
│  └──────────────┘      └──────────────┘                 │
│                                                           │
│  HPA: 2-10 replicas based on CPU (70%) & Memory (80%)    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Container Architecture

**Multi-stage Dockerfile:**

```
Stage 1: Builder
├─ Base: python:3.11-slim
├─ Install build dependencies (gcc, postgresql-client)
├─ Install Python packages from pyproject.toml
└─ Create wheel distributions

Stage 2: Production
├─ Base: python:3.11-slim
├─ Create non-root user (mcp:mcp)
├─ Copy Python dependencies from builder
├─ Copy application source code
├─ Set environment variables
├─ Configure health check
├─ Expose port 8000
└─ Run as non-root user
```

**Security Features:**
- Non-root user execution
- Read-only root filesystem (future enhancement)
- Minimal base image
- No unnecessary tools in production image

### Scalability Strategy

**Horizontal Scaling:**
- HPA monitors CPU and memory usage
- Min replicas: 2 (high availability)
- Max replicas: 10 (cost control)
- Scale up: CPU > 70% or Memory > 80%
- Scale down: Stabilization period 300s

**Stateless Design:**
- No session state in application pods
- All state in PostgreSQL or Redis
- Pods can be added/removed freely

**Database Scaling:**
- Connection pooling (20 connections/pod)
- Read replicas for heavy read workloads (future)
- Vertical scaling for write-heavy scenarios

---

## Integration Points

### Internal Integrations

**PostgreSQL:**
- Protocol: PostgreSQL wire protocol (AsyncPG)
- Connection: Async connection pool
- Transactions: ACID guarantees
- Migrations: Alembic for schema versioning

**Redis:**
- Protocol: RESP (REdis Serialization Protocol)
- Use cases:
  - Rate limiting counters
  - Session data (future)
  - Cache (future)
- Persistence: Optional (configure RDB/AOF)

### External Integrations (Optional)

**Langfuse:**
- Protocol: HTTPS REST API
- Purpose: LLM observability and tracing
- Data sent: Request traces, metadata, performance metrics
- Authentication: API key (public + secret)

**Prometheus:**
- Protocol: HTTP (metrics exposition)
- Endpoint: `/metrics`
- Format: Prometheus text format
- Metrics: HTTP request duration, count, database pool stats

---

## Quality Attributes

### Performance

**Latency:**
- Target: p50 < 50ms, p95 < 200ms, p99 < 500ms
- Optimization: Connection pooling, async I/O, minimal middleware

**Throughput:**
- Target: 1000 req/s per pod (depends on endpoint)
- Bottleneck: Database queries (optimize with indexes and read replicas)

**Resource Usage:**
- Memory: 256Mi request, 512Mi limit per pod
- CPU: 100m request, 500m limit per pod

### Reliability

**Availability:**
- Target: 99.9% uptime (8.76 hours downtime/year)
- Strategy: Multiple replicas, health checks, automatic restarts

**Fault Tolerance:**
- Database connection failures: Retry with exponential backoff
- Redis unavailable: Degrade gracefully (disable rate limiting)
- Pod crashes: Kubernetes automatically restarts

**Data Durability:**
- PostgreSQL: ACID transactions, persistent volumes
- Backups: Daily pg_dump (recommended via CronJob)

### Security

**Authentication:** Header-based API keys with Argon2 hashing
**Authorization:** Role-based (admin vs tenant)
**Encryption:** Fernet for credentials at rest, TLS for data in transit
**Audit:** Comprehensive logging of all actions

### Scalability

**Horizontal:** 2-10 pods via HPA
**Vertical:** Increase pod resources as needed
**Database:** Connection pooling, future read replicas

### Maintainability

**Code Quality:** Black formatting, Ruff linting, type hints
**Testing:** Unit, integration, E2E tests (to be implemented)
**Documentation:** OpenAPI/Swagger, README, architecture docs
**Monitoring:** Structured logs, Prometheus metrics, Langfuse traces

---

## Architectural Decisions

### ADR-001: Layered Architecture

**Decision:** Implement strict layered architecture (API → Service → Repository → Data)

**Rationale:**
- Clear separation of concerns
- Testability (mock layers independently)
- Maintainability (changes localized to layers)

**Consequences:**
- More files and classes
- Requires discipline to maintain boundaries
- Benefits increase with system complexity

### ADR-002: Repository Pattern

**Decision:** Abstract all database access through repository classes

**Rationale:**
- Database independence
- Consistent data access patterns
- Easier testing with mocks

**Consequences:**
- Additional abstraction layer
- Potential performance overhead (minimal with SQLAlchemy)

### ADR-003: Async/Await Throughout

**Decision:** Use async/await for all I/O operations

**Rationale:**
- Better performance for I/O-bound workload
- Non-blocking database and Redis operations
- Efficient connection pooling

**Consequences:**
- Requires async-compatible libraries
- Slightly more complex code
- Significant performance gains

### ADR-004: PostgreSQL for Primary Database

**Decision:** Use PostgreSQL instead of NoSQL

**Rationale:**
- Structured data with clear relationships
- ACID transactions required for consistency
- Rich querying capabilities (joins, complex filters)
- Battle-tested reliability

**Consequences:**
- Requires schema migrations
- Potential scaling challenges at massive scale (mitigated with read replicas)

### ADR-005: Fernet for Credential Encryption

**Decision:** Use Fernet symmetric encryption for credentials

**Rationale:**
- Simple and secure
- Built-in integrity verification (HMAC)
- Standard library support (cryptography package)
- Appropriate for at-rest encryption

**Consequences:**
- Single master key (consider key rotation strategy)
- All tenants use same key (consider per-tenant keys)

### ADR-006: Header-based Authentication

**Decision:** Use X-Tenant-ID + X-API-Key headers instead of JWT

**Rationale:**
- Simpler implementation for API-to-API communication
- No token expiration complexity
- Stateless (no session management)

**Consequences:**
- API keys must be securely stored by clients
- No built-in expiration (must implement rotation manually)
- Less suitable for browser-based clients

### ADR-007: Multi-tenancy via tenant_id Column

**Decision:** Single database with tenant_id filtering instead of database-per-tenant

**Rationale:**
- Simpler infrastructure
- Cost-effective for moderate scale
- Easier cross-tenant admin operations

**Consequences:**
- Must ensure proper tenant_id filtering in all queries
- Risk of data leakage if filter missing (mitigated by repository pattern)
- Scaling limits at very high tenant count

### ADR-008: Kubernetes Deployment

**Decision:** Deploy on Kubernetes instead of serverless or VMs

**Rationale:**
- Horizontal scaling with HPA
- Rolling updates with zero downtime
- Consistent infrastructure across environments
- Rich ecosystem (Ingress, cert-manager, monitoring)

**Consequences:**
- Operational complexity (requires Kubernetes knowledge)
- Minimum resource overhead (even at low scale)
- Excellent for production workloads

---

## Future Enhancements

### Short-term (Next 3 months)

1. **Comprehensive Testing:**
   - Unit tests for all services
   - Integration tests for API endpoints
   - E2E tests for complete workflows

2. **CI/CD Pipeline:**
   - Automated builds on commit
   - Automated testing
   - Automated deployment to staging
   - Manual approval for production

3. **Monitoring Dashboard:**
   - Grafana dashboards for metrics
   - Alerting on errors and performance degradation

### Medium-term (3-6 months)

1. **API Key Rotation:**
   - Implement rotation workflow
   - Grace period for old keys
   - Admin-initiated rotation

2. **Read Replicas:**
   - PostgreSQL read replicas for heavy read workloads
   - Query routing (writes to primary, reads to replicas)

3. **Advanced Caching:**
   - Redis caching for frequently accessed data
   - Cache invalidation strategies

4. **MCP Server Health Checks:**
   - Periodic connectivity tests
   - Server status updates
   - Alerting on server failures

### Long-term (6-12 months)

1. **Multi-region Deployment:**
   - Deploy to multiple regions
   - Cross-region database replication
   - Latency-based routing

2. **Per-tenant Encryption Keys:**
   - Separate encryption keys per tenant
   - Key rotation automation

3. **Advanced Access Control:**
   - RBAC within tenants
   - Fine-grained permissions
   - Audit trail improvements

4. **GraphQL API:**
   - Alternative to REST API
   - Efficient client queries
   - Real-time subscriptions

---

## Appendix

### Key Metrics

**Application Metrics:**
- HTTP request count (by endpoint, status code)
- HTTP request duration (p50, p95, p99)
- Active connections
- Database connection pool stats
- Redis cache hit/miss ratio

**Infrastructure Metrics:**
- Pod CPU usage
- Pod memory usage
- Pod restart count
- Database size
- Database connection count

### Related Documents

- [API Contracts](./api-contracts-mcp-registry.md)
- [Data Models](./data-models-mcp-registry.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)

---

**Document Control:**
- **Version:** 1.0
- **Last Updated:** 2026-01-31
- **Authors:** Development Team
- **Review Cycle:** Quarterly
- **Next Review:** 2026-04-30
