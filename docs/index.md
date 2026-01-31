# MCP Registry - Documentation Index

**Project:** mcp-registry
**Version:** 1.0.0
**Type:** Multi-tenant Backend API
**Generated:** 2026-01-31

---

## Quick Start

New to MCP Registry? Start here:

1. **[README](../README.md)** - Project overview and structure
2. **[USAGE](../USAGE.md)** - API usage guide with examples
3. **[DEPLOYMENT](../DEPLOYMENT.md)** - Deployment quickstart

---

## Core Documentation

### Architecture & Design

**[Architecture Document](./architecture.md)**
Comprehensive system architecture covering:
- System overview and capabilities
- Architecture patterns (layered, repository, dependency injection)
- Technology stack (FastAPI, PostgreSQL, Redis, Kubernetes)
- Component architecture (API, Service, Repository, Data layers)
- Data architecture (ERD, data flows)
- Security architecture (authentication, encryption, audit)
- Deployment architecture (Kubernetes, scaling, monitoring)
- Quality attributes (performance, reliability, security, scalability)
- Architectural decisions (ADRs)
- Future enhancements roadmap

**Key Sections:**
- [System Overview](./architecture.md#system-overview) - Context diagram and capabilities
- [Technology Stack](./architecture.md#technology-stack) - All dependencies and versions
- [Security Architecture](./architecture.md#security-architecture) - Authentication and encryption
- [Deployment Architecture](./architecture.md#deployment-architecture) - Kubernetes setup

---

### API & Data

**[API Contracts](./api-contracts-mcp-registry.md)**
Complete REST API documentation:
- 12 endpoints (5 admin, 6 tenant, 1 health)
- Request/response schemas with examples
- Authentication requirements per endpoint
- Error responses and status codes
- Admin vs tenant endpoint separation

**Endpoints:**
- Bootstrap: Create initial admin
- Tenants: CRUD operations (admin only)
- Servers: Register and manage MCP servers (admin only)
- Access Control: Grant/revoke server access (admin only)
- Credentials: Store and retrieve encrypted credentials (tenant)
- Health: Application health check

**[Data Models](./data-models-mcp-registry.md)**
Database schema and relationships:
- 4 tables (tenants, mcp_servers, tenant_server_credentials, tenant_server_access)
- Entity relationship diagrams
- Column definitions with types and constraints
- Indexes and foreign keys
- Data flow diagrams for admin and tenant workflows

**Key Tables:**
- `tenants` - Admin and tenant accounts with API key hashes
- `mcp_servers` - Global registry of MCP servers
- `tenant_server_credentials` - Encrypted credentials (Fernet)
- `tenant_server_access` - Many-to-many access control

---

### Development

**[Development Guide](./development-guide.md)**
Complete local development setup:
- Prerequisites (Python 3.11+, PostgreSQL, Redis)
- Local setup (venv, dependencies, database)
- Environment configuration (.env file, encryption keys)
- Running the application (uvicorn, hot reload)
- Database migrations (Alembic commands)
- Testing strategy and commands
- Code quality tools (black, ruff)
- API development and testing (curl examples)
- Debugging techniques
- Common development tasks

**Quick Setup:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Configure DATABASE_URL, REDIS_URL, etc.
alembic upgrade head
uvicorn mcp_registry.main:app --reload
```

**[Deployment Guide](./deployment-guide.md)**
Production deployment on Kubernetes:
- Prerequisites (K8s 1.25+, kubectl, Docker registry)
- Container image build (multi-stage Dockerfile)
- Kubernetes manifest configuration (10 files)
- Deployment steps (namespace, secrets, database, app)
- Database migrations (via Job or manual)
- Verification and health checks
- Scaling and performance tuning
- Monitoring and observability (logs, metrics, Langfuse)
- Security hardening (network policies, TLS)
- Backup and disaster recovery
- Troubleshooting common issues
- Rolling updates and rollbacks
- Multi-environment strategy

**Deployment Order:**
1. Namespace → ConfigMap → Secret
2. PostgreSQL → Redis
3. Application Deployment → Service → Ingress
4. HPA (Horizontal Pod Autoscaler)

---

### Project Structure

**[Source Tree Analysis](./source-tree-analysis.md)**
Annotated directory tree with explanations:
- Complete directory structure with annotations
- Critical directories (src/mcp_registry, alembic, k8s)
- Application architecture flow
- Entry points (main.py, Docker, Kubernetes)
- Configuration management
- Testing strategy
- Development workflow
- Deployment architecture diagram

**Key Directories:**
- `src/mcp_registry/` - Application source code
  - `api/` - Routes, middleware, dependencies
  - `db/` - Models, repositories, sessions
  - `services/` - Business logic (auth, encryption, audit, registry)
  - `utils/` - Validators, cache
- `alembic/` - Database migrations
- `k8s/` - Kubernetes manifests

---

### Reference

**[Glossary](./glossary.md)**
Comprehensive terminology reference:
- Technical terms (MCP, Fernet, Argon2, layered architecture)
- Authentication & security concepts
- Database & data terms (PostgreSQL, SQLAlchemy, Alembic, ORM)
- Web framework & API concepts (FastAPI, ASGI, Pydantic)
- Deployment & infrastructure (Kubernetes, Docker, Ingress, HPA)
- Multi-tenancy patterns
- Observability & monitoring (structured logging, Prometheus)
- Development tools (black, ruff, pytest)
- Acronyms (API, ASGI, CRUD, K8s, MCP, UUID, etc.)

**[FAQ (Frequently Asked Questions)](./faq.md)**
Common questions and answers:
- General questions (What is MCP Registry? Who is it for?)
- Authentication & security (API keys, encryption, credential storage)
- Multi-tenancy (admin vs tenant, isolation, access control)
- MCP servers (registration, access grants, configuration)
- Credentials (storage, updates, encryption)
- Deployment (infrastructure requirements, scaling, latency)
- Troubleshooting (401/403 errors, database/Redis issues, pod crashes)
- Development (local setup, migrations, testing, IDE setup)
- Observability (logs, metrics, debug mode, Langfuse)
- Roadmap & future features

---

## Documentation by Role

### For Developers

**Getting Started:**
1. [Development Guide](./development-guide.md) - Local setup
2. [Source Tree Analysis](./source-tree-analysis.md) - Codebase navigation
3. [Architecture Document](./architecture.md) - Design patterns

**Implementation:**
4. [API Contracts](./api-contracts-mcp-registry.md) - Endpoint specs
5. [Data Models](./data-models-mcp-registry.md) - Database schema
6. [Glossary](./glossary.md) - Terms and concepts

**Daily Work:**
- Code formatting: `black src/`
- Linting: `ruff check src/`
- Run migrations: `alembic upgrade head`
- Run locally: `uvicorn mcp_registry.main:app --reload`

### For DevOps/SREs

**Deployment:**
1. [Deployment Guide](./deployment-guide.md) - K8s deployment
2. [Architecture Document](./architecture.md#deployment-architecture) - Infrastructure

**Operations:**
3. [FAQ - Troubleshooting](./faq.md#troubleshooting) - Common issues
4. [Deployment Guide - Monitoring](./deployment-guide.md#monitoring-and-observability) - Logs and metrics

**Daily Work:**
- View logs: `kubectl logs -f deployment/mcp-registry`
- Check health: `curl http://<service>/health`
- Scale pods: `kubectl scale deployment mcp-registry --replicas=5`
- Run migrations: `kubectl apply -f k8s/10-migration-job.yaml`

### For API Consumers

**Getting Started:**
1. [USAGE.md](../USAGE.md) - API usage examples
2. [API Contracts](./api-contracts-mcp-registry.md) - All endpoints
3. [FAQ - Authentication](./faq.md#authentication--security) - API keys

**Reference:**
4. [Glossary](./glossary.md) - Understand terms
5. [FAQ](./faq.md) - Common questions

**Daily Work:**
- List servers: `GET /api/v1/tenants/servers`
- Store credentials: `POST /api/v1/tenants/credentials`
- Retrieve credentials: `GET /api/v1/tenants/credentials/{server_id}`

### For Administrators

**Setup:**
1. [Deployment Guide](./deployment-guide.md) - Deploy to K8s
2. [FAQ - Deployment](./faq.md#deployment) - Infrastructure requirements

**Operations:**
3. [API Contracts - Admin Endpoints](./api-contracts-mcp-registry.md#admin-endpoints) - Admin operations
4. [USAGE.md](../USAGE.md) - Usage examples

**Daily Work:**
- Create tenant: `POST /api/v1/admin/tenants`
- Register server: `POST /api/v1/admin/servers`
- Grant access: `POST /api/v1/admin/servers/{id}/access`

### For Architects

**Design:**
1. [Architecture Document](./architecture.md) - Complete architecture
2. [Data Models](./data-models-mcp-registry.md) - Database design
3. [Source Tree Analysis](./source-tree-analysis.md) - Code organization

**Decisions:**
4. [Architecture - ADRs](./architecture.md#architectural-decisions) - Key decisions
5. [Architecture - Quality Attributes](./architecture.md#quality-attributes) - Non-functional requirements

---

## Documentation by Topic

### Authentication & Security
- [Architecture - Security Architecture](./architecture.md#security-architecture)
- [Glossary - Authentication & Security](./glossary.md#authentication--security)
- [FAQ - Authentication & Security](./faq.md#authentication--security)
- [Development Guide - Security Considerations](./development-guide.md#security-considerations)
- [Deployment Guide - Security Hardening](./deployment-guide.md#security-hardening)

### Multi-tenancy
- [Architecture - System Overview](./architecture.md#system-overview)
- [Data Models - Tenant Isolation](./data-models-mcp-registry.md#tenant-isolation-model)
- [Glossary - Multi-tenancy](./glossary.md#multi-tenancy)
- [FAQ - Multi-tenancy](./faq.md#multi-tenancy)

### Database & Migrations
- [Data Models](./data-models-mcp-registry.md) - Complete schema
- [Development Guide - Database Management](./development-guide.md#database-management)
- [Deployment Guide - Database Migrations](./deployment-guide.md#step-4-run-database-migrations)
- [Glossary - Database & Data](./glossary.md#database--data)

### Kubernetes Deployment
- [Deployment Guide](./deployment-guide.md) - Complete deployment
- [Architecture - Deployment Architecture](./architecture.md#deployment-architecture)
- [Source Tree Analysis - /k8s/](./source-tree-analysis.md#k8s---kubernetes-manifests)
- [FAQ - Deployment](./faq.md#deployment)

### API Development
- [API Contracts](./api-contracts-mcp-registry.md) - All endpoints
- [Development Guide - API Development](./development-guide.md#api-development)
- [Glossary - Web Framework & APIs](./glossary.md#web-framework--apis)

### Monitoring & Observability
- [Deployment Guide - Monitoring](./deployment-guide.md#monitoring-and-observability)
- [Architecture - Integration Points](./architecture.md#integration-points)
- [FAQ - Observability](./faq.md#observability)
- [Glossary - Observability & Monitoring](./glossary.md#observability--monitoring)

---

## File Inventory

### Generated Documentation (docs/)

| File | Description | Lines | Last Updated |
|------|-------------|-------|--------------|
| [index.md](./index.md) | This file - Master documentation index | ~400 | 2026-01-31 |
| [architecture.md](./architecture.md) | System architecture and design | ~1400 | 2026-01-31 |
| [api-contracts-mcp-registry.md](./api-contracts-mcp-registry.md) | Complete API documentation | ~800 | 2026-01-31 |
| [data-models-mcp-registry.md](./data-models-mcp-registry.md) | Database schema and relationships | ~600 | 2026-01-31 |
| [source-tree-analysis.md](./source-tree-analysis.md) | Annotated directory structure | ~470 | 2026-01-31 |
| [development-guide.md](./development-guide.md) | Local development setup | ~900 | 2026-01-31 |
| [deployment-guide.md](./deployment-guide.md) | Production deployment on K8s | ~1200 | 2026-01-31 |
| [glossary.md](./glossary.md) | Terms, acronyms, and concepts | ~700 | 2026-01-31 |
| [faq.md](./faq.md) | Frequently asked questions | ~900 | 2026-01-31 |
| [project-scan-report.json](./project-scan-report.json) | Workflow state tracking | ~70 | 2026-01-31 |

**Total Documentation:** ~7,500 lines

### Existing Documentation (project root)

| File | Description |
|------|-------------|
| [README.md](../README.md) | Project overview |
| [USAGE.md](../USAGE.md) | API usage guide |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Deployment quickstart |

---

## Document Dependencies

```
README.md
    ├─→ USAGE.md (API usage)
    ├─→ DEPLOYMENT.md (Deployment)
    └─→ docs/index.md (Full documentation)

docs/index.md (this file)
    ├─→ architecture.md
    │       ├─→ api-contracts-mcp-registry.md
    │       ├─→ data-models-mcp-registry.md
    │       └─→ source-tree-analysis.md
    │
    ├─→ development-guide.md
    │       ├─→ api-contracts-mcp-registry.md
    │       ├─→ data-models-mcp-registry.md
    │       ├─→ source-tree-analysis.md
    │       └─→ glossary.md
    │
    ├─→ deployment-guide.md
    │       ├─→ architecture.md
    │       ├─→ source-tree-analysis.md
    │       └─→ faq.md
    │
    ├─→ glossary.md
    └─→ faq.md
            ├─→ development-guide.md
            ├─→ deployment-guide.md
            ├─→ api-contracts-mcp-registry.md
            └─→ glossary.md
```

---

## Documentation Standards

### Markdown Conventions
- Headers: `#` for title, `##` for sections, `###` for subsections
- Code blocks: Triple backticks with language identifier
- Links: Relative paths for internal docs, absolute for external
- Tables: Markdown tables with headers
- Lists: `-` for unordered, `1.` for ordered
- Emphasis: `**bold**` for important, `*italic*` for emphasis
- Code: `` `inline code` `` for technical terms

### File Naming
- kebab-case for multi-word files: `api-contracts-mcp-registry.md`
- Suffix project part if multi-part: `-mcp-registry`
- Use `.md` extension for Markdown files
- Use `.json` for structured data (workflow state)

### Content Structure
1. **Title and Metadata:** Project name, date, version
2. **Table of Contents:** For documents > 300 lines
3. **Overview/Introduction:** Purpose and audience
4. **Main Content:** Organized by topic
5. **Related Documents:** Links to other docs
6. **Last Updated:** Date and maintainer info

### Code Examples
- Always include comments explaining non-obvious code
- Use realistic examples (not foo/bar)
- Show complete curl commands with headers
- Include expected responses
- Highlight security-sensitive operations

---

## Maintenance

### Update Schedule
- **Weekly:** Check for broken links
- **Per Release:** Update version numbers
- **Per Major Change:** Update architecture and API docs
- **Quarterly:** Review and refresh all docs

### Document Owners
- **Architecture:** Lead Architect
- **API Contracts:** Backend Team
- **Data Models:** Database Team
- **Development Guide:** Engineering Team
- **Deployment Guide:** DevOps Team
- **FAQ/Glossary:** Technical Writers

### Review Process
1. Author creates/updates document
2. Technical review by subject matter expert
3. Editorial review for clarity
4. Final approval by document owner
5. Publish to documentation site/repository

---

## Next Steps

### For New Developers
1. Read [README](../README.md) for project overview
2. Follow [Development Guide](./development-guide.md) to set up local environment
3. Read [Architecture Document](./architecture.md) to understand system design
4. Review [API Contracts](./api-contracts-mcp-registry.md) and [Data Models](./data-models-mcp-registry.md)
5. Make your first contribution!

### For New Operators
1. Read [Deployment Guide](./deployment-guide.md) for K8s setup
2. Review [Architecture - Deployment](./architecture.md#deployment-architecture) for infrastructure
3. Bookmark [FAQ - Troubleshooting](./faq.md#troubleshooting) for common issues
4. Set up monitoring and alerting

### For API Users
1. Read [USAGE.md](../USAGE.md) for quick start
2. Review [API Contracts](./api-contracts-mcp-registry.md) for complete endpoint reference
3. Check [FAQ](./faq.md) for common questions
4. Start building!

---

## External Resources

### FastAPI
- **Documentation:** https://fastapi.tiangolo.com
- **Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **Advanced User Guide:** https://fastapi.tiangolo.com/advanced/

### SQLAlchemy
- **Documentation:** https://docs.sqlalchemy.org
- **Async Tutorial:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **ORM Quickstart:** https://docs.sqlalchemy.org/en/20/orm/quickstart.html

### Kubernetes
- **Documentation:** https://kubernetes.io/docs/
- **Concepts:** https://kubernetes.io/docs/concepts/
- **Tutorials:** https://kubernetes.io/docs/tutorials/

### PostgreSQL
- **Documentation:** https://www.postgresql.org/docs/
- **Performance Tuning:** https://wiki.postgresql.org/wiki/Performance_Optimization

### Redis
- **Documentation:** https://redis.io/docs/
- **Commands:** https://redis.io/commands/

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-01-31 | Initial documentation generation | BMAD Analyst Agent |

---

**Document Control:**
- **Status:** Active
- **Review Cycle:** Quarterly
- **Next Review:** 2026-04-30
- **Maintained by:** Development Team
- **Contact:** development-team@example.com

---

**Generated by:** BMAD Document Project Workflow v1.2.0
**Scan Level:** Deep
**Project Type:** Backend API (Monolith)
**Workflow Mode:** Initial Scan
