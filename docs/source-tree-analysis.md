# Source Tree Analysis - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry
**Type:** Monolith Backend API

---

## Annotated Directory Tree

```
/workspaces/mcp-registry/
│
├── src/                           # Application source code
│   └── mcp_registry/              # Main Python package
│       ├── __init__.py            # Package initialization
│       ├── main.py                # ⭐ APPLICATION ENTRY POINT
│       ├── config.py              # Configuration management (Pydantic Settings)
│       ├── models.py              # Pydantic models (request/response schemas)
│       │
│       ├── api/                   # API layer (FastAPI routes & middleware)
│       │   ├── __init__.py
│       │   ├── routes.py          # ⭐ ALL REST ENDPOINTS (admin + tenant)
│       │   ├── middleware.py     # Custom middleware (rate limiting, audit)
│       │   └── dependencies.py   # Dependency injection (DB sessions, auth)
│       │
│       ├── db/                    # Data layer (database access)
│       │   ├── __init__.py
│       │   ├── base.py            # ⭐ SQLALCHEMY MODELS (tables schema)
│       │   ├── session.py         # Database session management (async)
│       │   └── repositories.py   # Repository pattern (data access logic)
│       │
│       ├── services/              # Business logic layer
│       │   ├── __init__.py
│       │   ├── auth.py            # Authentication service (API key validation)
│       │   ├── encryption.py      # Credential encryption service (Fernet)
│       │   ├── audit.py           # Audit logging service
│       │   └── registry.py        # MCP registry business logic
│       │
│       └── utils/                 # Utility functions
│           ├── __init__.py
│           ├── validators.py      # Custom validation logic
│           └── cache.py           # Caching utilities (Redis)
│
├── alembic/                       # Database migrations (Alembic)
│   ├── env.py                     # Migration environment configuration
│   ├── script.py.mako             # Migration template
│   └── versions/                  # Migration version files
│       └── 001_initial.py         # Initial schema migration
│
├── k8s/                           # Kubernetes deployment manifests
│   ├── 00-namespace.yaml          # Namespace definition
│   ├── 01-configmap.yaml          # Application configuration
│   ├── 02-secret.yaml             # Secrets (DB credentials, API keys)
│   ├── 03-postgres.yaml           # PostgreSQL deployment + service
│   ├── 04-redis.yaml              # Redis deployment + service
│   ├── 05-deployment.yaml         # Application deployment (replicas, env, health checks)
│   └── 06-service.yaml            # Application service (LoadBalancer/ClusterIP)
│
├── scripts/                       # Utility scripts
│   └── (deployment, setup, maintenance scripts)
│
├── modules/                       # Module definitions (BMAD integration)
│   └── module.yaml
│
├── docs/                          # Generated documentation
│   ├── project-scan-report.json  # Workflow state file
│   ├── api-contracts-mcp-registry.md
│   ├── data-models-mcp-registry.md
│   └── source-tree-analysis.md   # This file
│
├── pyproject.toml                 # ⭐ PROJECT METADATA & DEPENDENCIES
├── alembic.ini                    # Alembic configuration
├── .env.example                   # Environment variable template
├── Dockerfile                     # Container image definition
├── README.md                      # Project overview
├── USAGE.md                       # Usage instructions
└── DEPLOYMENT.md                  # Deployment guide
```

---

## Critical Directories

### `/src/mcp_registry/` - Main Application Package

**Purpose:** Core application code following layered architecture pattern

**Subdirectories:**
- `api/` - REST API layer (routes, middleware, dependencies)
- `db/` - Data access layer (models, repositories, sessions)
- `services/` - Business logic layer (auth, encryption, audit, registry)
- `utils/` - Shared utilities (validation, caching)

**Entry Points:**
- **main.py** - FastAPI application factory
  - Creates app instance
  - Configures middleware (CORS, rate limiting, audit)
  - Registers routes at `/api/v1`
  - Lifecycle management (DB connection pooling)
  - Can be run directly: `python -m mcp_registry.main`
  - Or via uvicorn: `uvicorn mcp_registry.main:app`

---

### `/src/mcp_registry/api/` - API Layer

**Purpose:** HTTP request/response handling, routing, authentication

**Key Files:**
- **routes.py** (396 lines) - All API endpoints
  - 5 admin endpoints (`/admin/*`)
  - 6 tenant endpoints (`/tenants/*`)
  - 1 bootstrap endpoint (`/admin/bootstrap`)
  - Authentication dependencies

- **middleware.py** - Custom middleware stack
  - `RateLimitMiddleware` - Request rate limiting
  - `AuditMiddleware` - Automatic audit logging

- **dependencies.py** - Dependency injection
  - `get_db_session()` - Provides async database session
  - Authentication helpers

**Integration Points:**
- Uses services layer for business logic
- Uses repositories for data access
- Returns Pydantic models for type safety

---

### `/src/mcp_registry/db/` - Data Layer

**Purpose:** Database models, session management, data access patterns

**Key Files:**
- **base.py** (151 lines) - SQLAlchemy ORM models
  - `Base` - Declarative base class
  - `TenantModel` - Tenant/admin accounts
  - `MCPServerModel` - Global MCP server registry
  - `TenantServerCredential` - Encrypted credentials
  - `tenant_server_access` - Association table (many-to-many)

- **session.py** - Database connection management
  - Async SQLAlchemy engine (AsyncPG driver)
  - Session factory with connection pooling
  - PostgreSQL-specific optimizations

- **repositories.py** - Repository pattern implementation
  - `TenantRepository` - Tenant CRUD operations
  - `MCPServerRepository` - Server CRUD + access control
  - `CredentialRepository` - Encrypted credential management
  - Encapsulates all SQL queries

---

### `/src/mcp_registry/services/` - Business Logic Layer

**Purpose:** Core business logic, isolated from HTTP and database concerns

**Key Services:**
- **auth.py** - Authentication & authorization
  - API key generation (cryptographically secure)
  - API key hashing (Argon2)
  - Authentication verification
  - Admin privilege checking

- **encryption.py** - Credential encryption
  - Fernet symmetric encryption
  - Encrypt/decrypt credential blobs
  - Key derivation from master secret

- **audit.py** - Audit logging
  - Structured logging (JSON output)
  - Trace ID generation for request correlation
  - Action tracking (CREATE, UPDATE, DELETE, GRANT_ACCESS, etc.)
  - Integration with observability stack

- **registry.py** - MCP registry business logic
  - Server lifecycle management
  - Access control logic
  - Health check coordination

---

### `/alembic/` - Database Migrations

**Purpose:** Version-controlled schema changes using Alembic

**Structure:**
- `versions/` - Migration files (timestamped)
  - `001_initial.py` - Initial schema creation
  - Future migrations added as numbered files

**Commands:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Integration:** Runs during deployment before application starts

---

### `/k8s/` - Kubernetes Manifests

**Purpose:** Production deployment configuration for Kubernetes

**Deployment Order:**
1. **00-namespace.yaml** - Creates isolated namespace
2. **01-configmap.yaml** - Non-sensitive configuration
3. **02-secret.yaml** - Sensitive data (DB credentials, encryption keys)
4. **03-postgres.yaml** - PostgreSQL StatefulSet + Service
5. **04-redis.yaml** - Redis Deployment + Service
6. **05-deployment.yaml** - Application Deployment
   - 3 replicas (configurable)
   - Health checks (liveness/readiness)
   - Resource limits
   - Environment variable injection
7. **06-service.yaml** - LoadBalancer service

**Apply Commands:**
```bash
kubectl apply -f k8s/
```

---

## Application Architecture Flow

### Request Flow (Admin Registers Server)

```
HTTP Request
    ↓
[FastAPI App] (main.py)
    ↓
[Middleware Stack]
    ├─ CORS Middleware
    ├─ Rate Limit Middleware
    └─ Audit Middleware
    ↓
[Router] (/api/v1/admin/servers) (api/routes.py)
    ↓
[Authentication] (api/dependencies.py → services/auth.py)
    ├─ Extract X-Tenant-ID, X-API-Key
    ├─ Verify API key hash
    └─ Check is_admin flag
    ↓
[Business Logic] (services/registry.py)
    ↓
[Repository] (db/repositories.py → MCPServerRepository)
    ↓
[Database] (PostgreSQL via AsyncPG)
    ↓
[Audit Log] (services/audit.py)
    ↓
HTTP Response (Pydantic ServerResponse model)
```

### Credential Storage Flow (Tenant Stores Credentials)

```
HTTP Request (POST /tenants/credentials)
    ↓
[Authentication] (Tenant verification)
    ↓
[Access Check] (Verify tenant has access to server)
    ↓
[Encryption] (services/encryption.py → Fernet encrypt)
    ↓
[Repository] (CredentialRepository → store encrypted blob)
    ↓
[Database] (tenant_server_credentials table)
    ↓
[Audit Log] (STORE_CREDENTIALS action - credentials NOT logged)
    ↓
HTTP Response
```

---

## Entry Points

### Primary Entry Point
**File:** `src/mcp_registry/main.py`
**Function:** `app = FastAPI(...)`
**How to Run:**
```bash
# Direct execution
python -m mcp_registry.main

# Via Uvicorn (production)
uvicorn mcp_registry.main:app --host 0.0.0.0 --port 8000 --workers 4

# With settings
uvicorn mcp_registry.main:app --host 0.0.0.0 --port 8080 --log-level info
```

### Docker Entry Point
**File:** `Dockerfile`
**CMD:** `uvicorn mcp_registry.main:app --host 0.0.0.0 --port 8000`

### Kubernetes Entry Point
**File:** `k8s/05-deployment.yaml`
**Container Command:** Uvicorn with environment-based configuration

---

## Configuration

### Environment Variables
Managed via `config.py` using Pydantic Settings:

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ENCRYPTION_KEY` - Fernet encryption key
- `ADMIN_CREATION_SECRET` - Bootstrap endpoint secret

**Optional:**
- `DEBUG` - Enable debug mode and docs endpoints
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- `CORS_ORIGINS` - Allowed CORS origins
- `RATE_LIMIT_ENABLED` - Enable rate limiting
- `WORKERS` - Uvicorn worker count (default: 4)
- `HOST` - Bind host (default: 0.0.0.0)
- `PORT` - Bind port (default: 8000)

### Configuration Sources (Priority Order)
1. Environment variables
2. `.env` file (development only)
3. Kubernetes ConfigMap + Secrets (production)
4. Default values in config.py

---

## Testing Strategy

### Test Organization
- **Unit Tests:** `tests/unit/` - Test individual functions/classes
- **Integration Tests:** `tests/integration/` - Test API endpoints with database
- **E2E Tests:** `tests/e2e/` - Test complete workflows

### Test Dependencies (from pyproject.toml)
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for API testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=mcp_registry --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py

# Integration tests only
pytest tests/integration/
```

---

## Development Workflow

### Local Setup
```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Set up environment
cp .env.example .env
# Edit .env with local database credentials

# 4. Run database migrations
alembic upgrade head

# 5. Start application
uvicorn mcp_registry.main:app --reload
```

### Code Quality Tools
- **black** - Code formatting (line-length: 88)
- **ruff** - Linting (line-length: 88)
- **pytest** - Testing

### Pre-commit Checks
```bash
# Format code
black src/

# Lint code
ruff check src/

# Run tests
pytest
```

---

## Deployment Architecture

### Production Stack
```
┌─────────────────────────────────────┐
│         Load Balancer               │
│    (k8s Service: LoadBalancer)      │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │  MCP Registry Pods  │
    │  (3 replicas)       │
    │  - FastAPI app      │
    │  - Uvicorn          │
    │  - Health checks    │
    └──────┬─────┬────────┘
           │     │
      ┌────┴─┐ ┌─┴────┐
      │ PG   │ │ Redis│
      │ DB   │ │Cache │
      └──────┘ └──────┘
```

---

## Key Integration Points

### External Services
- **PostgreSQL** - Primary data store (tenant, server, credentials)
- **Redis** - Caching layer (rate limiting, session data)
- **Langfuse** - LLM observability (optional)
- **Prometheus** - Metrics collection

### Internal Communication
- **API ↔ Services** - Dependency injection via FastAPI Depends()
- **Services ↔ Repositories** - Direct method calls
- **Repositories ↔ Database** - SQLAlchemy async sessions

---

## Summary

**Directory Count:** 6 critical directories
**Entry Point:** `src/mcp_registry/main.py`
**Architecture:** Layered (API → Services → Repositories → Database)
**Deployment:** Kubernetes with PostgreSQL + Redis
**Configuration:** Environment-based with Pydantic Settings
**Testing:** Pytest with async support

**Critical Paths:**
- Source code: `src/mcp_registry/`
- Migrations: `alembic/versions/`
- Deployment: `k8s/`
- Documentation: `docs/`
