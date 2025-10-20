import os
from dataclasses import dataclass
from typing import Any, Optional

import yaml


@dataclass
class Service:
    domain: str


@dataclass
class ServiceRoutingConfig:
    enabled: bool
    services: dict[str, Service]
    query_all_for_cases: bool = True  # Query all services for get_cases_by_bsn
    query_all_for_claims: bool = True  # Query all services for get_claims_by_bsn
    query_all_for_profiles: bool = False  # Query all services for get_all_profiles (default: use default URL)

    @classmethod
    def from_dict(cls, data: dict) -> Optional["ServiceRoutingConfig"]:
        if not data:
            return None
        services = {
            service_name: Service(domain=service_data["domain"])
            for service_name, service_data in data.get("services", {}).items()
        }
        return cls(
            enabled=data.get("enabled", False),
            services=services,
            query_all_for_cases=data.get("query_all_for_cases", True),
            query_all_for_claims=data.get("query_all_for_claims", True),
            query_all_for_profiles=data.get("query_all_for_profiles", False),
        )


@dataclass
class EngineConfig:
    id: str
    name: str
    description: str
    type: str
    default: bool
    domain: str | None
    service_routing: ServiceRoutingConfig | None

    @classmethod
    def from_dict(cls, data: dict) -> "EngineConfig":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=data["type"],
            default=data.get("default", False),
            domain=data.get("domain"),
            service_routing=ServiceRoutingConfig.from_dict(data.get("service_routing", {})),
        )


@dataclass
class AppConfig:
    engines: list[EngineConfig]

    def get_default_engine(self) -> EngineConfig | None:
        """Get the default engine configuration"""
        for engine in self.engines:
            if engine.default:
                return engine
        return None if not self.engines else self.engines[0]

    def get_engine_by_id(self, engine_id: str) -> EngineConfig | None:
        """Get a specific engine by id"""
        for engine in self.engines:
            if engine.id == engine_id:
                return engine
        return None


class ConfigLoader:
    def __init__(self, config_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_config_path = os.path.join(base_dir, "config", "config.yaml")
        self.config_path = config_path or os.environ.get("APP_CONFIG_PATH", default_config_path)
        self._raw_config = self._load_config()
        self.config = self._parse_config()

    def _load_config(self) -> dict[str, Any]:
        """Load raw configuration from file"""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def _parse_config(self) -> AppConfig:
        """Parse raw config into typed AppConfig"""
        engines_raw = self._raw_config.get("engines", [])
        engines = [EngineConfig.from_dict(engine_data) for engine_data in engines_raw]
        return AppConfig(engines=engines)

    def get_engine(self, engine_id: str) -> EngineConfig | None:
        """Get a specific engine by id"""
        return self.config.get_engine_by_id(engine_id)

    def get_engines(self) -> EngineConfig | None:
        return self.config.engines
