"""Application entry point."""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_registry.config import get_settings
from mcp_registry.api.routes import router
from mcp_registry.db.base import Base
from mcp_registry.db.session import engine
from mcp_registry.api.middleware import RateLimitMiddleware, AuditMiddleware
from mcp_registry.services.audit import AuditLogger

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead
        # await conn.run_sync(Base.metadata.create_all)
        pass
    
    yield
    
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="MCP Registry",
    description="Multi-tenant Model Context Protocol Server Registry",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# Audit logging middleware
app.add_middleware(AuditMiddleware)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    await AuditLogger.log(
        action="ERROR",
        resource_type="system",
        success=False,
        error_message=str(exc),
        ip_address=request.client.host if request.client else None,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_registry.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
