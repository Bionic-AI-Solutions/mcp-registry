# Glossary - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry

---

## Technical Terms

### MCP (Model Context Protocol)
A standardized protocol for connecting AI models with external tools, data sources, and services. MCP servers expose tools, resources, and prompts that AI models can use during conversations.

**Related Terms:** MCP Server, MCP Client

### MCP Server
A service that implements the Model Context Protocol, exposing capabilities (tools, resources, prompts) for AI models to use. Examples include documentation search servers, database query servers, API integration servers.

**Example Config:**
```json
{
  "transport": "stdio",
  "command": "python",
  "args": ["/app/server.py"],
  "capabilities": {
    "tools": [...],
    "resources": [...],
    "prompts": [...]
  }
}
```

### MCP Registry
This system. A multi-tenant service for registering, discovering, and managing MCP servers with credential storage.

---

## Authentication & Security

### API Key
A secret token used for authenticating API requests. Format: `sk_` followed by 32 random characters.

**Usage:**
```bash
curl -H "X-API-Key: sk_abc123..."
```

**Security:** Hashed with Argon2 before storage. Never stored in plaintext.

### Argon2
A memory-hard password hashing algorithm that won the Password Hashing Competition (2015). Used to securely hash API keys before storage.

**Properties:**
- Resistant to GPU/ASIC attacks
- Configurable memory and time costs
- Produces irreversible hashes

**Alternative to:** bcrypt, scrypt, PBKDF2

### Fernet
A symmetric encryption specification that provides confidentiality and integrity for data at rest.

**Used for:** Encrypting tenant credentials before database storage

**Algorithm:**
- AES-128 in CBC mode
- HMAC for integrity verification
- Timestamp for expiration (optional)

**Python Library:** `cryptography.fernet`

### Encryption Key
The master secret key used by Fernet to encrypt/decrypt credentials. Must be kept secure and never committed to version control.

**Generation:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

**Storage:** Kubernetes Secret in production

### X-Tenant-ID
HTTP header containing the tenant's unique identifier (UUID). Required for all authenticated requests.

**Example:** `X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000`

### X-API-Key
HTTP header containing the tenant's secret API key. Required for all authenticated requests.

**Example:** `X-API-Key: sk_abc123xyz...`

### Bootstrap Secret
A secure secret used to protect the initial admin tenant creation endpoint. Prevents unauthorized admin account creation.

**Environment Variable:** `ADMIN_CREATION_SECRET`

---

## Architecture & Design Patterns

### Monolith
An application architecture where all components run in a single process, as opposed to microservices. The MCP Registry is a monolithic backend API.

**Benefits:**
- Simpler deployment
- Lower operational complexity
- Easier debugging
- Good for moderate scale

### Layered Architecture
A design pattern that organizes code into horizontal layers with unidirectional dependencies:
- API Layer → Service Layer → Repository Layer → Data Layer

**Benefits:**
- Separation of concerns
- Testability
- Maintainability

### Repository Pattern
A design pattern that abstracts data access logic behind repository interfaces. All database operations go through repository classes.

**Example:**
```python
class TenantRepository:
    async def create(self, data): ...
    async def get_by_id(self, id): ...
    async def update(self, id, updates): ...
```

**Benefits:**
- Database independence
- Consistent data access patterns
- Easier testing with mocks

### Dependency Injection
A design pattern where dependencies are provided to components rather than created internally. FastAPI uses this extensively.

**Example:**
```python
@router.get("/servers")
async def list_servers(
    repo: MCPServerRepository = Depends(get_server_repo)
):
    return await repo.list_all()
```

### Middleware
Software components that intercept and process HTTP requests/responses before they reach route handlers.

**Example Middleware:**
- CORS (Cross-Origin Resource Sharing)
- Rate Limiting
- Audit Logging
- Authentication

---

## Database & Data

### PostgreSQL
An open-source relational database management system (RDBMS) known for reliability, ACID compliance, and advanced features.

**Used for:** Primary data store (tenants, servers, credentials, access mappings)

### AsyncPG
A high-performance async Python driver for PostgreSQL. Faster than psycopg2 for async applications.

**Integration:** Used by SQLAlchemy for database connections

### SQLAlchemy
A Python SQL toolkit and Object-Relational Mapping (ORM) library. Allows working with databases using Python objects.

**Version:** 2.0+ with async support

**Example:**
```python
class TenantModel(Base):
    __tablename__ = "tenants"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
```

### Alembic
A database migration tool for SQLAlchemy. Tracks schema changes over time and applies them to databases.

**Commands:**
- `alembic revision --autogenerate`: Create migration from model changes
- `alembic upgrade head`: Apply all pending migrations
- `alembic downgrade -1`: Rollback one migration

### ORM (Object-Relational Mapping)
A technique for converting data between incompatible type systems (relational databases and object-oriented programming).

**Example:** `TenantModel` Python class ↔ `tenants` database table

### Migration
A versioned script that modifies database schema (add tables, columns, indexes, etc.). Alembic manages migrations.

**Location:** `alembic/versions/`

### Redis
An in-memory data structure store used as a cache, message broker, and database. Fast read/write operations.

**Used for:**
- Rate limiting counters
- Session data (future)
- Cached frequently accessed data (future)

### Connection Pool
A cache of reusable database connections. Avoids overhead of creating new connections for each request.

**Configuration:** SQLAlchemy engine with `pool_size` and `max_overflow` settings

---

## Web Framework & APIs

### FastAPI
A modern, high-performance Python web framework for building APIs. Features automatic OpenAPI docs, type validation, and async support.

**Benefits:**
- Fast (comparable to NodeJS and Go)
- Automatic data validation via Pydantic
- Interactive API docs (/docs, /redoc)
- Native async/await support

### Uvicorn
An ASGI server for running FastAPI applications. Production-ready with worker support.

**Command:**
```bash
uvicorn mcp_registry.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### ASGI (Asynchronous Server Gateway Interface)
A standard interface between async Python web frameworks (like FastAPI) and web servers (like Uvicorn).

**Predecessor:** WSGI (synchronous)

### Pydantic
A Python library for data validation using type annotations. FastAPI uses Pydantic for request/response models.

**Example:**
```python
class ServerRegistrationRequest(BaseModel):
    name: str
    description: str
    version: str
    config: MCPServerConfig
```

### OpenAPI
A specification for describing REST APIs. FastAPI automatically generates OpenAPI specs.

**Access:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

### Swagger UI
An interactive API documentation interface generated from OpenAPI specs.

**URL:** `http://localhost:8000/docs`

---

## Deployment & Infrastructure

### Kubernetes (K8s)
An open-source container orchestration platform for automating deployment, scaling, and management of containerized applications.

**Resources Used:**
- Namespace, ConfigMap, Secret, Deployment, Service, Ingress, HPA, StatefulSet

### Docker
A platform for developing, shipping, and running applications in containers. Ensures consistent environments across development, testing, and production.

**File:** `Dockerfile` (multi-stage build)

### Container
A lightweight, standalone executable package that includes code, runtime, system tools, libraries, and settings.

**Benefits:**
- Isolation
- Portability
- Consistency across environments

### Pod
The smallest deployable unit in Kubernetes. Contains one or more containers that share networking and storage.

**Example:** Each MCP Registry replica runs in a separate pod

### Deployment
A Kubernetes resource that manages a set of identical pods, ensuring desired number of replicas are running.

**File:** `k8s/05-deployment.yaml`

### Service
A Kubernetes resource that exposes pods via a stable network endpoint (IP + port).

**Types:**
- ClusterIP: Internal cluster access only
- LoadBalancer: External access via cloud load balancer

**File:** `k8s/06-service.yaml`

### Ingress
A Kubernetes resource that manages external HTTP/HTTPS access to services. Provides load balancing, SSL termination, and name-based virtual hosting.

**File:** `k8s/07-ingress.yaml`

### HPA (Horizontal Pod Autoscaler)
A Kubernetes resource that automatically scales pod replicas based on metrics (CPU, memory, custom).

**Configuration:** 2-10 replicas, scale at 70% CPU or 80% memory

**File:** `k8s/08-hpa.yaml`

### StatefulSet
A Kubernetes resource for managing stateful applications (like databases). Provides stable pod identities and persistent storage.

**Used for:** PostgreSQL deployment

**File:** `k8s/03-postgres.yaml`

### PVC (PersistentVolumeClaim)
A request for storage in Kubernetes. Used by StatefulSets and Deployments to request persistent disks.

**Used for:** PostgreSQL data storage (10Gi)

### ConfigMap
A Kubernetes resource for storing non-sensitive configuration as key-value pairs.

**Contains:** Application settings (DEBUG, LOG_LEVEL, CORS_ORIGINS, etc.)

**File:** `k8s/01-configmap.yaml`

### Secret
A Kubernetes resource for storing sensitive data (passwords, API keys, tokens). Base64 encoded.

**Contains:** DATABASE_URL, REDIS_URL, ENCRYPTION_KEY, ADMIN_CREATION_SECRET

**File:** `k8s/02-secret.yaml`

### Namespace
A Kubernetes mechanism for isolating groups of resources. All MCP Registry resources run in the `mcp-registry` namespace.

**File:** `k8s/00-namespace.yaml`

---

## Multi-tenancy

### Tenant
An isolated customer/organization account in the MCP Registry. Each tenant has:
- Unique ID (UUID)
- API key for authentication
- Access to specific MCP servers
- Encrypted credentials for those servers

**Types:**
- Admin Tenant (`is_admin: true`)
- Regular Tenant (`is_admin: false`)

### Admin Tenant
A special tenant with elevated privileges. Can:
- Create other tenants
- Register global MCP servers
- Grant/revoke server access to tenants
- View all registered servers

**Creation:** Via `/api/v1/admin/bootstrap` endpoint (requires bootstrap secret)

### Tenant Isolation
The practice of ensuring data from one tenant is not accessible to another tenant.

**Implementation:**
- All queries filtered by `tenant_id`
- Credentials encrypted separately per tenant
- Access control via `tenant_server_access` table

### Multi-tenant Architecture
A software architecture where a single instance serves multiple tenants, with data isolation between them.

**Approach:** Single database with `tenant_id` column filtering (vs database-per-tenant)

---

## Observability & Monitoring

### Structured Logging
A logging approach where log entries are formatted as JSON with consistent fields (timestamp, level, trace_id, etc.).

**Library:** structlog, python-json-logger

**Example:**
```json
{
  "timestamp": "2026-01-31T20:00:00Z",
  "level": "INFO",
  "trace_id": "abc-123",
  "action": "CREATE_TENANT",
  "tenant_id": "tenant-uuid"
}
```

### Trace ID
A unique identifier assigned to each request, allowing correlation of logs across distributed systems.

**Format:** UUID v4

**Header:** `X-Trace-ID` (optional, auto-generated if missing)

### Audit Log
A record of significant actions in the system (tenant creation, server registration, access grants, credential storage).

**Purpose:**
- Security monitoring
- Compliance
- Debugging
- Analytics

**Sensitive Data:** API keys and credentials are redacted

### Langfuse
An open-source LLM observability platform. Tracks LLM interactions, costs, latency, and quality.

**Used for:** (Optional) Monitoring MCP server interactions if LLMs are involved

**Environment Variables:**
- LANGFUSE_PUBLIC_KEY
- LANGFUSE_SECRET_KEY
- LANGFUSE_HOST

### Prometheus
An open-source monitoring and alerting toolkit. Scrapes metrics from applications via HTTP.

**Endpoint:** `/metrics`

**Metrics Exposed:**
- HTTP request duration
- Request count by endpoint
- Database connection pool stats
- Custom business metrics

### Health Check
An endpoint that reports application status. Used by Kubernetes for liveness and readiness probes.

**Endpoint:** `/health`

**Response:** `{"status": "healthy", "timestamp": "..."}`

---

## Development Tools

### black
An opinionated Python code formatter. Enforces consistent code style.

**Configuration:** 88-character line length (pyproject.toml)

**Command:** `black src/`

### ruff
A fast Python linter written in Rust. Checks code for errors and style issues.

**Configuration:** 88-character line length (pyproject.toml)

**Command:** `ruff check src/`

### pytest
A Python testing framework. Supports unit, integration, and end-to-end tests.

**Extensions:**
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting

**Command:** `pytest --cov=mcp_registry`

### httpx
An async HTTP client for Python. Used for testing API endpoints.

**Alternative to:** requests (synchronous)

### venv (Virtual Environment)
An isolated Python environment for project dependencies. Avoids conflicts between projects.

**Creation:** `python -m venv .venv`

**Activation:** `source .venv/bin/activate`

---

## Acronyms

- **API:** Application Programming Interface
- **ASGI:** Asynchronous Server Gateway Interface
- **CRUD:** Create, Read, Update, Delete
- **HPA:** Horizontal Pod Autoscaler
- **JSON:** JavaScript Object Notation
- **JWT:** JSON Web Token
- **K8s:** Kubernetes
- **MCP:** Model Context Protocol
- **ORM:** Object-Relational Mapping
- **PVC:** PersistentVolumeClaim
- **RBAC:** Role-Based Access Control
- **REST:** Representational State Transfer
- **TLS:** Transport Layer Security
- **UUID:** Universally Unique Identifier

---

## Common Patterns

### UUID (Universally Unique Identifier)
A 128-bit identifier that is globally unique without central coordination.

**Format:** `550e8400-e29b-41d4-a716-446655440000`

**Used for:** Tenant IDs, Server IDs, Credential IDs

**Python:** `import uuid; uuid.uuid4()`

### JSON (JavaScript Object Notation)
A lightweight data interchange format. Human-readable and easy to parse.

**Used for:**
- Request/response bodies
- Configuration (MCP server config, capabilities)
- Structured logging
- Database columns (tenant settings, server capabilities)

### Base64 Encoding
An encoding scheme that converts binary data to ASCII text. Used for Kubernetes Secrets.

**Not encryption:** Easily decoded, provides no security

**Example:** `echo -n "password" | base64` → `cGFzc3dvcmQ=`

### Environment Variable
A variable set outside the application, used for configuration. Allows same code to run in different environments.

**Accessed via:** `os.getenv("DATABASE_URL")`

**Sources:**
- `.env` file (development)
- Kubernetes ConfigMap/Secret (production)

---

**Last Updated:** 2026-01-31
**Maintained by:** Development Team
