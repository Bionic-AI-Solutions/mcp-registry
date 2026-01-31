"""Pydantic models with JSON Schema validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransportType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WEBSOCKET = "websocket"


class ServerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MCPTool(BaseModel):
    """MCP Tool definition with JSON Schema validation."""
    model_config = ConfigDict(strict=True)
    
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., max_length=1024)
    input_schema: Dict[str, Any] = Field(..., alias="inputSchema")
    
    @field_validator("input_schema")
    @classmethod
    def validate_json_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that inputSchema is a valid JSON Schema."""
        if not isinstance(v, dict):
            raise ValueError("inputSchema must be an object")
        if v.get("type") not in ["object", "array", "string", "number", "boolean", "null"]:
            raise ValueError("inputSchema must have a valid type")
        return v


class MCPResource(BaseModel):
    """MCP Resource definition."""
    model_config = ConfigDict(strict=True)
    
    uri: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1024)
    mime_type: Optional[str] = Field(None, alias="mimeType")


class MCPPrompt(BaseModel):
    """MCP Prompt definition."""
    model_config = ConfigDict(strict=True)
    
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1024)
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPCapabilities(BaseModel):
    """MCP Server capabilities."""
    model_config = ConfigDict(strict=True)
    
    tools: List[MCPTool] = Field(default_factory=list)
    resources: List[MCPResource] = Field(default_factory=list)
    prompts: List[MCPPrompt] = Field(default_factory=list)
    sampling: bool = False
    roots: List[str] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    """MCP Server configuration with transport-specific validation."""
    model_config = ConfigDict(strict=True)
    
    transport: TransportType
    command: Optional[str] = Field(None, max_length=256)
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = Field(None, pattern=r"^https?://")
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300)
    
    @field_validator("command", mode="after")
    @classmethod
    def validate_stdio(cls, v: Optional[str], info) -> Optional[str]:
        """Validate stdio requires command."""
        values = info.data
        if values.get("transport") == TransportType.STDIO and not v:
            raise ValueError("command is required for stdio transport")
        return v
    
    @field_validator("url", mode="after")
    @classmethod
    def validate_http(cls, v: Optional[str], info) -> Optional[str]:
        """Validate HTTP/SSE requires URL."""
        values = info.data
        transport = values.get("transport")
        if transport in [TransportType.HTTP, TransportType.SSE, TransportType.WEBSOCKET] and not v:
            raise ValueError(f"url is required for {transport} transport")
        return v


class ServerRegistrationRequest(BaseModel):
    """Request model for registering an MCP server."""
    model_config = ConfigDict(strict=True)
    
    name: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=2048)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+")
    config: MCPServerConfig
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    tags: List[str] = Field(default_factory=list, max_length=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    access_control: Dict[str, Any] = Field(default_factory=dict)


class ServerResponse(BaseModel):
    """Response model for MCP server."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    version: str
    status: ServerStatus
    config: MCPServerConfig
    capabilities: MCPCapabilities
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    health_status: Optional[str] = None


class TenantCreateRequest(BaseModel):
    """Request to create a new tenant."""
    model_config = ConfigDict(strict=True)
    
    name: str = Field(..., min_length=1, max_length=256)
    settings: Dict[str, Any] = Field(default_factory=dict)
    allowed_origins: List[str] = Field(default_factory=list)


class TenantResponse(BaseModel):
    """Tenant response (excludes sensitive data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    created_at: datetime
    is_active: bool
    settings: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


class AuditLogEntry(BaseModel):
    """Audit log entry structure."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: Optional[UUID] = None
    user_id: Optional[str] = None
    action: str  # CREATE, READ, UPDATE, DELETE, AUTH_FAILURE
    resource_type: str  # server, tenant, config
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
