# Frequently Asked Questions - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry

---

## General Questions

### What is the MCP Registry?

The MCP Registry is a multi-tenant backend API service that allows organizations to:
- Register Model Context Protocol (MCP) servers
- Discover available MCP servers
- Store encrypted credentials for MCP servers
- Manage access control for MCP servers across tenants

Think of it as a centralized directory and credential manager for MCP servers in an enterprise environment.

### Who is this service for?

**Primary Users:**
- **Platform Teams:** Managing MCP infrastructure across organizations
- **DevOps Engineers:** Deploying and operating MCP servers at scale
- **Security Teams:** Centrally managing credentials and access control
- **Application Developers:** Discovering and connecting to available MCP servers

### What is MCP (Model Context Protocol)?

MCP is a standardized protocol for connecting AI models with external tools, data sources, and services. MCP servers expose capabilities (tools, resources, prompts) that AI models can use during conversations.

**Example Use Cases:**
- Documentation search servers
- Database query servers
- API integration servers
- File system access servers

---

## Authentication & Security

### How do I get an API key?

**For the first admin tenant:**
1. Use the bootstrap endpoint: `POST /api/v1/admin/bootstrap`
2. Provide the `X-Bootstrap-Secret` header (set during deployment)
3. The response includes a one-time API key - save it immediately

**For additional tenants:**
1. Admin creates tenant via: `POST /api/v1/admin/tenants`
2. The response includes a one-time API key
3. The tenant saves the key securely

**Important:** API keys are shown only once during creation and cannot be retrieved later.

### What if I lose my API key?

Currently, there is no API key recovery mechanism. If a key is lost:

**Option 1 (Admin):** Create a new tenant for the user
**Option 2 (Future):** API key rotation feature (planned)

**Best Practice:** Store API keys in a secure secrets manager (AWS Secrets Manager, HashiCorp Vault, 1Password, etc.)

### How are API keys stored?

API keys are hashed using Argon2 (a memory-hard password hashing algorithm) before storage. The plaintext key is never stored in the database.

**Security Benefits:**
- Irreversible hashing (cannot recover plaintext from hash)
- Resistant to brute-force attacks (memory-hard)
- Constant-time comparison (prevents timing attacks)

### How are credentials encrypted?

Credentials are encrypted using Fernet symmetric encryption before storage:

1. Tenant provides credentials as JSON
2. JSON is encrypted with Fernet using master encryption key
3. Encrypted blob (bytes) is stored in database
4. On retrieval, blob is decrypted and returned as JSON

**Encryption Algorithm:**
- AES-128 in CBC mode
- HMAC for integrity verification
- Timestamp for optional expiration

### Where is the encryption key stored?

**Development:** `.env` file (not committed to git)
**Production:** Kubernetes Secret (`k8s/02-secret.yaml`)

**Generation:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Can I rotate the encryption key?

Currently, key rotation is not supported. This is a planned enhancement.

**Workaround:** Would require decrypting all credentials with old key and re-encrypting with new key (manual migration).

---

## Multi-tenancy

### What's the difference between admin and regular tenants?

**Admin Tenants (`is_admin: true`):**
- Create and manage other tenants
- Register global MCP servers
- Grant/revoke server access to tenants
- View all registered servers

**Regular Tenants (`is_admin: false`):**
- View servers they have access to
- Store/retrieve/update/delete credentials for accessible servers
- Cannot create other tenants
- Cannot register global servers

### How does tenant isolation work?

**Data Isolation:**
- All queries filtered by `tenant_id`
- Tenants can only see servers granted to them via `tenant_server_access` table
- Credentials are stored per-tenant (tenant cannot access another's credentials)

**Access Control:**
- Authentication required for all endpoints (except health check)
- Admin endpoints check `is_admin` flag
- Tenant endpoints filter by authenticated tenant's ID

### Can one tenant access another tenant's data?

No. The system enforces strict tenant isolation:

**Server Access:** Tenants only see servers explicitly granted to them by admins
**Credentials:** Stored with `tenant_id` foreign key, inaccessible to other tenants
**Repository Layer:** All queries automatically filter by authenticated tenant's ID

---

## MCP Servers

### What information is stored for each MCP server?

**Core Fields:**
- Name, description, version
- Configuration (transport, command, args, env, timeout)
- Capabilities (tools, resources, prompts)
- Tags (for categorization/search)
- Status (active, maintenance, deprecated)
- Access control (public, allowed_tenants)

**Example:**
```json
{
  "name": "Documentation Server",
  "version": "1.2.0",
  "config": {
    "transport": "stdio",
    "command": "python",
    "args": ["/app/server.py"],
    "timeout": 30
  },
  "capabilities": {
    "tools": [{...}],
    "resources": [{...}],
    "prompts": []
  },
  "tags": ["docs", "internal"]
}
```

### How do I grant a tenant access to a server?

**Admin Only:**
```bash
POST /api/v1/admin/servers/{server_id}/access
Headers:
  X-Tenant-ID: <admin-tenant-id>
  X-API-Key: <admin-api-key>
Body:
  {
    "tenant_id": "<target-tenant-id>"
  }
```

This creates an entry in the `tenant_server_access` table, allowing the tenant to see and use the server.

### Can I revoke access after granting it?

Yes. Use the delete access endpoint:

```bash
DELETE /api/v1/admin/servers/{server_id}/access?tenant_id=<tenant-id>
Headers:
  X-Tenant-ID: <admin-tenant-id>
  X-API-Key: <admin-api-key>
```

This removes the `tenant_server_access` entry. The tenant will immediately lose access to the server.

### What happens to credentials when access is revoked?

Currently, stored credentials remain in the database. The tenant cannot access them (due to authorization checks), but they are not automatically deleted.

**Future Enhancement:** Automatic credential cleanup on access revocation

### How do I update an MCP server's configuration?

Currently, there's no update endpoint. You must:
1. Delete the old server (if not in use)
2. Register a new server with updated config

**Future Enhancement:** `PATCH /api/v1/admin/servers/{id}` endpoint

---

## Credentials

### What types of credentials can be stored?

Any JSON-serializable credentials:

**Examples:**
```json
// API Key
{
  "api_key": "sk_test_123456",
  "endpoint": "https://api.example.com"
}

// OAuth
{
  "access_token": "ya29.a0...",
  "refresh_token": "1//0g...",
  "token_type": "Bearer",
  "expires_at": 1706745600
}

// Database
{
  "host": "db.example.com",
  "port": 5432,
  "username": "app_user",
  "password": "secret",
  "database": "production"
}
```

### Can I store multiple credentials for the same server?

No. The database constraint is `UNIQUE(tenant_id, server_id)`.

**Workaround:** Store all credentials in a single JSON object:
```json
{
  "primary": {"api_key": "..."},
  "secondary": {"api_key": "..."}
}
```

### How do I update stored credentials?

```bash
PUT /api/v1/tenants/credentials/{credential_id}
Headers:
  X-Tenant-ID: <tenant-id>
  X-API-Key: <tenant-api-key>
Body:
  {
    "credentials": {
      "api_key": "new_key",
      "endpoint": "https://new-endpoint.com"
    }
  }
```

This completely replaces the encrypted credential blob.

---

## Deployment

### What are the minimum infrastructure requirements?

**Development:**
- Python 3.11+
- PostgreSQL 14+
- Redis 6.0+

**Production:**
- Kubernetes 1.25+
- 3 worker nodes (minimum)
- Persistent storage (for PostgreSQL)
- Load balancer (cloud provider or MetalLB)

### Can I run this without Kubernetes?

Yes, but Kubernetes manifests are provided for production use.

**Alternative Deployments:**
- Docker Compose (for development/small scale)
- VM-based deployment with systemd
- Cloud PaaS (Heroku, Render, etc.) with managed PostgreSQL/Redis

### How many pods should I run?

**Minimum:** 2 (for high availability)
**Default:** 3 (configured in deployment)
**Maximum:** 10 (configured in HPA)

The Horizontal Pod Autoscaler automatically scales based on CPU (70%) and memory (80%) usage.

### How do I scale the database?

**Vertical Scaling:**
- Increase PostgreSQL pod resources
- Use cloud-managed databases (RDS, Cloud SQL) for easier scaling

**Horizontal Scaling (Read Replicas):**
- Add read replicas for heavy read workloads
- Route read queries to replicas (not yet implemented)

### What's the expected API latency?

**Targets:**
- p50: < 50ms
- p95: < 200ms
- p99: < 500ms

**Actual latency depends on:**
- Database query performance
- Network latency
- Encryption/decryption overhead (for credential endpoints)

---

## Troubleshooting

### API returns 401 Unauthorized

**Causes:**
- Missing `X-Tenant-ID` or `X-API-Key` headers
- Incorrect API key
- API key hash mismatch

**Solutions:**
1. Verify headers are present and correct
2. Check API key was saved correctly during tenant creation
3. Ensure no extra spaces or newlines in API key
4. Create a new tenant if key is lost

### API returns 403 Forbidden

**Causes:**
- Tenant trying to access admin-only endpoint
- Tenant trying to access server they don't have permission for

**Solutions:**
1. Check if endpoint requires admin privileges
2. Verify tenant has been granted access to server (via `tenant_server_access`)
3. Contact admin to grant access

### Database connection errors

**Causes:**
- PostgreSQL not running
- Incorrect `DATABASE_URL` environment variable
- Network connectivity issues
- Connection pool exhausted

**Solutions:**
1. Check PostgreSQL is running: `kubectl get pods -l app=postgres`
2. Verify DATABASE_URL in Secret: `kubectl get secret mcp-registry-secret -o yaml`
3. Check pod logs: `kubectl logs deployment/mcp-registry`
4. Increase connection pool size if exhausted

### Redis connection errors

**Causes:**
- Redis not running
- Incorrect `REDIS_URL` environment variable

**Solutions:**
1. Check Redis is running: `kubectl get pods -l app=redis`
2. Verify REDIS_URL in Secret
3. Test connection: `redis-cli -u $REDIS_URL ping`

### Pods stuck in CrashLoopBackOff

**Causes:**
- Database migrations not run
- Environment variables missing
- Application code errors

**Solutions:**
1. Check pod logs: `kubectl logs <pod-name>`
2. Run migrations: `kubectl exec deployment/mcp-registry -- alembic upgrade head`
3. Verify ConfigMap and Secret are applied
4. Check for Python import errors or config issues

### Health check endpoint returns 503

**Causes:**
- Application not fully started
- Database connection failed
- Application error

**Solutions:**
1. Wait for application startup (check liveness probe settings)
2. Check database connectivity
3. Review application logs for errors

---

## Development

### How do I run the application locally?

```bash
# 1. Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start PostgreSQL and Redis
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine

# 3. Configure .env file
cp .env.example .env
# Edit .env with database URL, Redis URL, encryption key

# 4. Run migrations
alembic upgrade head

# 5. Start application
uvicorn mcp_registry.main:app --reload
```

### How do I create a new database migration?

```bash
# 1. Modify SQLAlchemy models in src/mcp_registry/db/base.py

# 2. Auto-generate migration
alembic revision --autogenerate -m "Add new column"

# 3. Review generated migration in alembic/versions/

# 4. Apply migration
alembic upgrade head
```

### How do I run tests?

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_registry --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

**Note:** Test suite is not yet fully implemented.

### What's the recommended IDE setup?

**VS Code:**
- Install Python extension
- Install Black formatter extension
- Install Ruff linter extension
- Configure settings:
  ```json
  {
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "editor.formatOnSave": true
  }
  ```

**PyCharm:**
- Configure Black as external tool
- Enable Ruff in Inspections
- Set line length to 88

---

## Observability

### Where can I see application logs?

**Kubernetes:**
```bash
# View logs
kubectl logs -f deployment/mcp-registry -n mcp-registry

# View logs from all pods
kubectl logs -l app=mcp-registry -n mcp-registry --tail=100
```

**Docker:**
```bash
docker logs -f <container-id>
```

**Local Development:**
Logs are printed to stdout in JSON format (structured logging).

### What metrics are exposed?

**Prometheus Metrics (`/metrics`):**
- HTTP request count (by endpoint, status code)
- HTTP request duration (histogram)
- Active requests (gauge)
- Database connection pool stats
- Custom business metrics

**Grafana Dashboards:**
- Not yet provided (create custom dashboards from Prometheus metrics)

### How do I enable debug mode?

**Development:**
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

**Production (Kubernetes):**
```yaml
# In k8s/01-configmap.yaml
data:
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
```

**Effects:**
- Detailed error messages
- SQLAlchemy query logging
- Swagger UI enabled at `/docs`
- ReDoc enabled at `/redoc`

**Warning:** Never enable DEBUG mode in production (exposes sensitive information).

### What is Langfuse and do I need it?

Langfuse is an optional LLM observability platform for tracking:
- LLM interactions
- Request traces
- Costs and latency
- Quality metrics

**Required:** No (optional)
**Use Cases:** If your MCP servers involve LLM interactions, Langfuse provides visibility
**Configuration:** Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` in Secret

---

## Roadmap & Future Features

### What features are planned?

**Short-term (Next 3 months):**
- Comprehensive test suite
- CI/CD pipeline
- Monitoring dashboards

**Medium-term (3-6 months):**
- API key rotation
- Server update endpoint
- MCP server health checks
- Advanced caching with Redis

**Long-term (6-12 months):**
- Multi-region deployment
- Per-tenant encryption keys
- RBAC within tenants
- GraphQL API

### Can I contribute?

This project is currently internal/private. Contribution guidelines will be published if open-sourced.

**For Internal Contributors:**
- Follow the development guide
- Use black and ruff for code quality
- Write tests for new features
- Update documentation

### Is there a public roadmap?

Not yet. Check with the maintainers or project manager for upcoming features and priorities.

---

## Getting Help

### Where can I find more documentation?

- [README](../README.md) - Project overview
- [Architecture](./architecture.md) - System architecture
- [API Contracts](./api-contracts-mcp-registry.md) - API documentation
- [Data Models](./data-models-mcp-registry.md) - Database schema
- [Development Guide](./development-guide.md) - Local setup
- [Deployment Guide](./deployment-guide.md) - Production deployment
- [Glossary](./glossary.md) - Terms and concepts

### How do I report a bug?

**Internal:** Contact the development team or project maintainer
**If open-sourced:** Create an issue on GitHub with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (dev/staging/prod)
- Logs or error messages

### How do I request a feature?

**Internal:** Contact the product team or project manager
**If open-sourced:** Create a feature request on GitHub with:
- Description of the feature
- Use case and motivation
- Proposed implementation (optional)

---

**Last Updated:** 2026-01-31
**Maintained by:** Development Team
