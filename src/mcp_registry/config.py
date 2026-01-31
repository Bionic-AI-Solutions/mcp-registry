"""Application configuration with Kubernetes-native support."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "mcp-registry"
    app_env: str = Field(default="production", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/mcp_registry",
        alias="DATABASE_URL"
    )
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, alias="DB_MAX_OVERFLOW")
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    
    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    redis_pool_size: int = Field(default=50, alias="REDIS_POOL_SIZE")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_default: str = Field(default="100/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")
    
    # Langfuse (Observability)
    langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")
    langfuse_public_key: Optional[str] = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: SecretStr = Field(default=SecretStr(""), alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    
    # Encryption
    credential_encryption_key: str = Field(
        default="your-32-byte-base64-encoded-key-here=",
        alias="CREDENTIAL_ENCRYPTION_KEY"
    )
    
    # Admin creation secret (bootstrap)
    admin_creation_secret: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        alias="ADMIN_CREATION_SECRET"
    )
    
    # Security
    api_key_header: str = "X-API-Key"
    tenant_id_header: str = "X-Tenant-ID"
    request_timeout: int = 30
    allowed_hosts: List[str] = Field(default=["*"], alias="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")
    
    # Audit Logging
    audit_log_to_stdout: bool = Field(default=True, alias="AUDIT_LOG_TO_STDOUT")
    audit_sensitive_fields: List[str] = Field(
        default=["api_key", "password", "secret", "token"],
        alias="AUDIT_SENSITIVE_FIELDS"
    )

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
