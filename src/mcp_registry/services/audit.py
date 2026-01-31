"""Audit logging with Langfuse integration."""

import json
import structlog
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from langfuse import Langfuse
from mcp_registry.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

# Initialize Langfuse if enabled
langfuse: Optional[Langfuse] = None
if settings.langfuse_enabled and settings.langfuse_public_key:
    langfuse = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        host=settings.langfuse_host,
    )


class AuditLogger:
    """Structured audit logging."""
    
    @staticmethod
    def _sanitize(data: dict) -> dict:
        """Remove sensitive fields from logs."""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        sensitive_fields = {f.lower() for f in settings.audit_sensitive_fields}
        
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = AuditLogger._sanitize(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    AuditLogger._sanitize(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    async def log(
        action: str,
        resource_type: str,
        tenant_id: Optional[UUID] = None,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Create audit log entry."""
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_type": resource_type,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "resource_id": resource_id,
            "success": success,
            "details": AuditLogger._sanitize(details or {}),
            "error_message": error_message,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "trace_id": trace_id,
        }
        
        # Structured logging to stdout (captured by Kubernetes)
        if success:
            logger.info("audit_log", **entry)
        else:
            logger.warning("audit_log", **entry)
        
        # Langfuse tracing for observability
        if langfuse and trace_id:
            span = langfuse.span(
                trace_id=trace_id,
                name=f"{action}_{resource_type}",
                input=entry["details"],
                output={"success": success},
                level="ERROR" if not success else "DEFAULT",
                status_message=error_message if error_message else None,
            )
            
            if not success:
                langfuse.score(
                    trace_id=trace_id,
                    name="operation_success",
                    value=0,
                    comment=error_message
                )
    
    @staticmethod
    def create_trace(tenant_id: Optional[UUID] = None, operation: str = "unknown") -> str:
        """Create a new Langfuse trace."""
        if not langfuse:
            return str(UUID(int=0))
        
        trace = langfuse.trace(
            name=operation,
            user_id=str(tenant_id) if tenant_id else "anonymous",
            metadata={"service": "mcp-registry"}
        )
        return trace.id


class MetricsCollector:
    """Prometheus metrics collection."""
    
    def __init__(self):
        from prometheus_client import Counter, Histogram, Gauge
        
        self.request_count = Counter(
            'mcp_registry_requests_total',
            'Total requests',
            ['tenant_id', 'method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'mcp_registry_request_duration_seconds',
            'Request duration',
            ['tenant_id', 'method', 'endpoint']
        )
        
        self.active_servers = Gauge(
            'mcp_registry_active_servers',
            'Number of active servers',
            ['tenant_id']
        )
        
        self.registry_operations = Counter(
            'mcp_registry_operations_total',
            'Registry operations',
            ['tenant_id', 'operation', 'status']
        )
