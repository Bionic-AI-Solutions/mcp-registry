"""Rate limiting middleware integration."""

from fastapi import Request, HTTPException, status
from mcp_registry.config import get_settings
from mcp_registry.utils.cache import RateLimiter

settings = get_settings()
limiter = RateLimiter()


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip rate limiting if disabled
        if not settings.rate_limit_enabled:
            await self.app(scope, receive, send)
            return
        
        # Get tenant ID from header
        tenant_id = request.headers.get(settings.tenant_id_header.lower())
        
        # Create rate limit key
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{tenant_id or 'anonymous'}:{client_ip}"
        
        # Parse rate limit (e.g., "100/minute")
        parts = settings.rate_limit_default.split("/")
        max_requests = int(parts[0])
        window = 60  # default minute
        
        if len(parts) > 1:
            unit = parts[1]
            if "second" in unit:
                window = 1
            elif "minute" in unit:
                window = 60
            elif "hour" in unit:
                window = 3600
        
        # Check rate limit
        allowed, remaining = await limiter.is_allowed(key, max_requests, window)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(window)}
            )
        
        # Add rate limit headers to response
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"X-RateLimit-Limit", str(max_requests).encode()))
                headers.append((b"X-RateLimit-Remaining", str(remaining).encode()))
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_headers)
