# Development Guide - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry
**Type:** FastAPI Backend API

---

## Prerequisites

### Required Software
- **Python:** 3.11 or higher
- **PostgreSQL:** 14+ (for local development)
- **Redis:** 6.0+ (for caching and rate limiting)
- **Git:** For version control
- **Docker:** (Optional) For containerized development

### Recommended Tools
- **IDE:** VS Code with Python extension
- **API Testing:** curl, httpx, or Postman
- **Database Client:** pgAdmin, DBeaver, or psql CLI

---

## Local Development Setup

### 1. Clone and Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp-registry

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project with development dependencies
pip install -e ".[dev]"
```

**Installed Packages:**
- **Production:** FastAPI, Uvicorn, SQLAlchemy, AsyncPG, Alembic, Redis, Pydantic, Argon2-cffi, Langfuse, Structlog, Prometheus Client
- **Development:** pytest, pytest-asyncio, httpx, black, ruff

### 3. Database Setup

#### Option A: Local PostgreSQL

```bash
# Create database
createdb mcp_registry_dev

# Set database URL in environment
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/mcp_registry_dev"
```

#### Option B: Docker PostgreSQL

```bash
# Start PostgreSQL container
docker run -d \
  --name mcp-registry-postgres \
  -e POSTGRES_DB=mcp_registry_dev \
  -e POSTGRES_USER=mcp_user \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 \
  postgres:16-alpine

# Set database URL
export DATABASE_URL="postgresql+asyncpg://mcp_user:dev_password@localhost:5432/mcp_registry_dev"
```

### 4. Redis Setup

#### Option A: Local Redis

```bash
# Install and start Redis (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis

# Set Redis URL
export REDIS_URL="redis://localhost:6379/0"
```

#### Option B: Docker Redis

```bash
# Start Redis container
docker run -d \
  --name mcp-registry-redis \
  -p 6379:6379 \
  redis:7-alpine

# Set Redis URL
export REDIS_URL="redis://localhost:6379/0"
```

### 5. Environment Configuration

Create a `.env` file for application configuration (not included in .env.example):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://mcp_user:dev_password@localhost:5432/mcp_registry_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-fernet-key-here

# Admin Bootstrap
ADMIN_CREATION_SECRET=your-secure-secret-for-bootstrap

# Application
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
WORKERS=1

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Observability (Optional)
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Generating Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 6. Database Migrations

```bash
# Run migrations to create schema
alembic upgrade head

# Check migration status
alembic current

# View migration history
alembic history --verbose
```

**Migration Files Location:** `alembic/versions/`
- `001_initial.py` - Creates initial schema (tenants, mcp_servers, tenant_server_credentials, tenant_server_access)

---

## Running the Application

### Development Mode (Auto-reload)

```bash
# Using uvicorn with hot reload
uvicorn mcp_registry.main:app --reload --host 0.0.0.0 --port 8000

# With custom log level
uvicorn mcp_registry.main:app --reload --log-level debug --host 0.0.0.0 --port 8000
```

### Production Mode (Multi-worker)

```bash
# Run with 4 workers
uvicorn mcp_registry.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run as Python module
python -m mcp_registry.main
```

### Verify Application Started

```bash
# Health check
curl http://localhost:8000/health

# API documentation (if DEBUG=true)
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## Testing

### Test Structure (To Be Implemented)

```
tests/
├── unit/              # Unit tests for services, utilities
│   ├── test_auth.py
│   ├── test_encryption.py
│   └── test_validators.py
├── integration/       # API endpoint tests with database
│   ├── test_admin_endpoints.py
│   └── test_tenant_endpoints.py
└── e2e/              # End-to-end workflow tests
    └── test_full_workflow.py
```

### Running Tests (When Implemented)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_registry --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_auth.py

# Run with verbose output
pytest -v

# Run only integration tests
pytest tests/integration/

# View coverage report
open htmlcov/index.html  # or xdg-open on Linux
```

### Test Database Setup

```bash
# Create test database
createdb mcp_registry_test

# Set test database URL in pytest fixtures
export TEST_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/mcp_registry_test"
```

---

## Code Quality

### Formatting with Black

```bash
# Format all Python files
black src/

# Check formatting without changes
black --check src/

# Format specific file
black src/mcp_registry/api/routes.py
```

**Configuration:** `pyproject.toml`
- Line length: 88 characters

### Linting with Ruff

```bash
# Lint all files
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Lint specific file
ruff check src/mcp_registry/services/auth.py
```

**Configuration:** `pyproject.toml`
- Line length: 88 characters

### Pre-commit Workflow

```bash
# Before committing code
black src/                    # Format code
ruff check --fix src/         # Fix linting issues
pytest                        # Run tests (when implemented)
```

---

## Database Management

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to tenants table"

# Create empty migration (for manual SQL)
alembic revision -m "Add custom index"

# Edit generated migration
# File: alembic/versions/002_<timestamp>_description.py
```

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Upgrade one step
alembic upgrade +1
```

### Rolling Back Migrations

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

### Useful Alembic Commands

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show SQL for migration (dry-run)
alembic upgrade head --sql

# Check if database is up to date
alembic current | grep "head"
```

---

## API Development

### Testing Endpoints with curl

#### 1. Bootstrap Admin Tenant

```bash
curl -X POST http://localhost:8000/api/v1/admin/bootstrap \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Secret: your-admin-creation-secret" \
  -d '{
    "name": "Admin Tenant",
    "contact_email": "admin@example.com"
  }'
```

**Save the returned `api_key` - it will not be shown again!**

#### 2. Register MCP Server (Admin Only)

```bash
curl -X POST http://localhost:8000/api/v1/admin/servers \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <admin-tenant-id>" \
  -H "X-API-Key: <admin-api-key>" \
  -d '{
    "name": "Test Server",
    "description": "Test MCP server",
    "version": "1.0.0",
    "config": {
      "transport": "stdio",
      "command": "python",
      "args": ["/app/server.py"],
      "timeout": 30
    },
    "capabilities": {
      "tools": [],
      "resources": [],
      "prompts": []
    }
  }'
```

#### 3. Create Regular Tenant (Admin Only)

```bash
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <admin-tenant-id>" \
  -H "X-API-Key: <admin-api-key>" \
  -d '{
    "name": "Acme Corporation",
    "contact_email": "admin@acme.com",
    "settings": {
      "max_servers": 50
    }
  }'
```

#### 4. Grant Server Access to Tenant (Admin Only)

```bash
curl -X POST http://localhost:8000/api/v1/admin/servers/<server-id>/access \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <admin-tenant-id>" \
  -H "X-API-Key: <admin-api-key>" \
  -d '{
    "tenant_id": "<target-tenant-id>"
  }'
```

#### 5. List Accessible Servers (Tenant)

```bash
curl http://localhost:8000/api/v1/tenants/servers \
  -H "X-Tenant-ID: <tenant-id>" \
  -H "X-API-Key: <tenant-api-key>"
```

#### 6. Store Credentials (Tenant)

```bash
curl -X POST http://localhost:8000/api/v1/tenants/credentials \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <tenant-id>" \
  -H "X-API-Key: <tenant-api-key>" \
  -d '{
    "server_id": "<server-id>",
    "credentials": {
      "api_key": "sk_test_123",
      "endpoint": "https://api.example.com"
    }
  }'
```

### Using httpx for Testing

```python
import httpx

async def test_list_servers():
    headers = {
        "X-Tenant-ID": "your-tenant-id",
        "X-API-Key": "your-api-key"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/tenants/servers",
            headers=headers
        )
        print(response.json())
```

---

## Debugging

### Enable Debug Mode

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

This enables:
- Detailed error messages
- SQLAlchemy query logging
- Swagger UI at `/docs`
- ReDoc at `/redoc`

### Viewing Logs

```bash
# Application logs (structured JSON)
tail -f logs/app.log  # if file logging configured

# Database query logs (when DEBUG=true)
# Queries are logged to stdout
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### Testing Database Connections

```python
# Test PostgreSQL connection
python -c "
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test():
    engine = create_async_engine('postgresql+asyncpg://user:pass@localhost/db')
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print(result.scalar())
    await engine.dispose()

asyncio.run(test())
"

# Test Redis connection
python -c "
import redis
r = redis.from_url('redis://localhost:6379/0')
r.ping()
print('Redis connected!')
"
```

---

## Project Structure for Developers

```
/workspaces/mcp-registry/
│
├── src/mcp_registry/           # Application source
│   ├── main.py                 # FastAPI app entry point ⭐
│   ├── config.py               # Pydantic settings
│   ├── models.py               # Request/response schemas
│   │
│   ├── api/                    # API layer
│   │   ├── routes.py           # All endpoints ⭐
│   │   ├── middleware.py       # Rate limit, audit
│   │   └── dependencies.py     # Auth, DB injection
│   │
│   ├── db/                     # Data layer
│   │   ├── base.py             # SQLAlchemy models ⭐
│   │   ├── session.py          # Async DB sessions
│   │   └── repositories.py     # Data access patterns
│   │
│   ├── services/               # Business logic
│   │   ├── auth.py             # Authentication
│   │   ├── encryption.py       # Credential encryption
│   │   ├── audit.py            # Audit logging
│   │   └── registry.py         # MCP registry logic
│   │
│   └── utils/                  # Utilities
│       ├── validators.py       # Custom validation
│       └── cache.py            # Redis caching
│
├── alembic/                    # Database migrations
│   └── versions/
│       └── 001_initial.py      # Initial schema
│
├── tests/                      # Tests (to be implemented)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── pyproject.toml              # Dependencies ⭐
├── alembic.ini                 # Alembic config
└── .env                        # Local environment (create this)
```

---

## Common Development Tasks

### Add New API Endpoint

1. Define Pydantic models in `src/mcp_registry/models.py`
2. Add route in `src/mcp_registry/api/routes.py`
3. Implement business logic in appropriate service
4. Add repository method if database access needed
5. Test endpoint with curl or httpx

### Add Database Column

1. Modify SQLAlchemy model in `src/mcp_registry/db/base.py`
2. Generate migration: `alembic revision --autogenerate -m "Add column"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Update repository methods if needed

### Add Authentication Dependency

```python
# In src/mcp_registry/api/dependencies.py
async def get_current_user(
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    api_key: str = Header(..., alias="X-API-Key"),
    repo: TenantRepository = Depends(get_tenant_repo)
):
    # Authenticate and return tenant
    ...
```

### Add Middleware

```python
# In src/mcp_registry/api/middleware.py
class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response

# In src/mcp_registry/main.py
app.add_middleware(CustomMiddleware)
```

---

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL is running
pg_isready

# Check connection parameters
psql $DATABASE_URL -c "SELECT 1"

# Verify AsyncPG driver installed
pip show asyncpg
```

### Redis Connection Errors

```bash
# Check Redis is running
redis-cli ping

# Test connection
redis-cli -u $REDIS_URL ping
```

### Import Errors

```bash
# Ensure PYTHONPATH includes src/
export PYTHONPATH=/workspaces/mcp-registry/src

# Reinstall in editable mode
pip install -e .
```

### Migration Conflicts

```bash
# Check current state
alembic current

# If migrations are out of sync, stamp to specific revision
alembic stamp head

# Or rebuild database from scratch
dropdb mcp_registry_dev && createdb mcp_registry_dev
alembic upgrade head
```

---

## Performance Optimization

### Database Connection Pooling

Configure in `src/mcp_registry/db/session.py`:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Max connections
    max_overflow=10,       # Additional overflow
    pool_pre_ping=True,    # Verify connections
)
```

### Redis Caching Strategy

Use Redis for:
- Rate limiting (per-tenant request counts)
- Session data (if implementing sessions)
- Frequently accessed data (server lists, tenant metadata)

### Async Best Practices

- Use `async def` for I/O-bound operations
- Use `await` for database queries, Redis operations, HTTP calls
- Avoid blocking operations in async functions

---

## Security Considerations

### API Key Storage

- **Never log API keys** - configured in audit service
- API keys are hashed with Argon2 before storage
- Raw keys only returned once on creation

### Credential Encryption

- Fernet symmetric encryption for stored credentials
- Encryption key must be stored securely (K8s Secrets in production)
- Key rotation not yet implemented

### Input Validation

- All requests validated with Pydantic models
- SQL injection prevented by SQLAlchemy ORM
- Use parameterized queries for any raw SQL

### Rate Limiting

- Configured per tenant in middleware
- Redis-backed to work across workers
- Customizable limits in configuration

---

## Next Steps

1. **Implement Tests:** Create unit, integration, and E2E tests
2. **Add CI/CD:** Set up GitHub Actions or GitLab CI
3. **Observability:** Configure Langfuse, Prometheus, Grafana
4. **Documentation:** Generate OpenAPI spec, add docstrings
5. **Performance:** Add caching layer, optimize queries
6. **Security:** Implement key rotation, add security headers

---

## Useful Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Alembic Docs:** https://alembic.sqlalchemy.org
- **Pydantic Docs:** https://docs.pydantic.dev
- **Uvicorn Docs:** https://www.uvicorn.org

---

**Last Updated:** 2026-01-31
**Maintainers:** Development Team
