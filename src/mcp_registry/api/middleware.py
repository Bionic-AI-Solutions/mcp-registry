"""Custom middleware."""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_registry.config import get_settings
from mcp_registry.services.audit import AuditLogger, MetricsCollector
from mcp_registry.utils.cache import RateLimiter

settings = get_settings()
metrics = MetricsCollector()
limiter = RateLimiter()


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for request auditing."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Log request metrics
        tenant_id = request.headers.get(settings.tenant_id_header.lower())
        
        metrics.request_count.labels(
            tenant_id=tenant_id or "anonymous",
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        metrics.request_duration.labels(
            tenant_id=tenant_id or "anonymous",
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        tenant_id = request.headers.get(settings.tenant_id_header.lower())
        client_ip = request.client.host if request.client else "unknown"
        
        key = f"ratelimit:{tenant_id or 'anonymous'}:{client_ip}"
        
        # Parse limit
        max_req = 100
        window = 60
        if "/" in settings.rate_limit_default:
            max_req = int(settings.rate_limit_default.split("/")[0])
        
        allowed, remaining = await limiter.is_allowed(key, max_req, window)
        
        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(window)}
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
