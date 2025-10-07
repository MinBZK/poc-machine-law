"""
Configuration management for MCP law execution server.
Environment-based configuration with sensible defaults.
"""

import logging
import os
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Cache configuration"""

    law_execution_ttl: int = 300  # 5 minutes
    enabled: bool = True


@dataclass
class SecurityConfig:
    """Security configuration"""

    enable_input_sanitization: bool = True
    max_input_length: int = 1000
    rate_limit_per_minute: int = 60
    allowed_bsn_patterns: list[str] = None


@dataclass
class PerformanceConfig:
    """Performance configuration"""

    enable_lazy_loading: bool = True
    connection_timeout: float = 30.0
    execution_timeout: float = 120.0


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    audit_enabled: bool = True


@dataclass
class MCPConfig:
    """Main MCP server configuration"""

    cache: CacheConfig
    security: SecurityConfig
    performance: PerformanceConfig
    logging: LoggingConfig
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> "MCPConfig":
        """Load configuration from environment variables"""
        return cls(
            cache=CacheConfig(
                law_execution_ttl=int(os.getenv("MCP_CACHE_LAW_TTL", "300")),
                enabled=os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true",
            ),
            security=SecurityConfig(
                enable_input_sanitization=os.getenv("MCP_SECURITY_SANITIZE", "true").lower() == "true",
                max_input_length=int(os.getenv("MCP_SECURITY_MAX_INPUT", "1000")),
                rate_limit_per_minute=int(os.getenv("MCP_SECURITY_RATE_LIMIT", "60")),
            ),
            performance=PerformanceConfig(
                enable_lazy_loading=os.getenv("MCP_PERF_LAZY_LOADING", "true").lower() == "true",
                connection_timeout=float(os.getenv("MCP_PERF_CONN_TIMEOUT", "30.0")),
                execution_timeout=float(os.getenv("MCP_PERF_EXEC_TIMEOUT", "120.0")),
            ),
            logging=LoggingConfig(
                level=os.getenv("MCP_LOG_LEVEL", "INFO").upper(),
                audit_enabled=os.getenv("MCP_LOG_AUDIT", "true").lower() == "true",
            ),
            environment=os.getenv("MCP_ENVIRONMENT", "development").lower(),
        )


# Global configuration instance
config = MCPConfig.from_environment()


def setup_logging(config: LoggingConfig) -> None:
    """Setup logging with configuration"""
    logging.basicConfig(
        level=getattr(logging, config.level),
        format=config.format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add audit logging if enabled
    if config.audit_enabled:
        audit_logger = logging.getLogger("audit")
        audit_handler = logging.StreamHandler()
        audit_handler.setFormatter(logging.Formatter("AUDIT - %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)


def get_config() -> MCPConfig:
    """Get the global configuration instance"""
    return config
