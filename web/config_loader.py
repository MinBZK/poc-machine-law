import os
from dataclasses import dataclass
from typing import Any, TypedDict

import yaml


class EngineConfig(TypedDict):
    id: str
    name: str
    description: str
    type: str
    default: bool
    domain: str | None


@dataclass
class AppConfig:
    engines: list[EngineConfig]

    def get_default_engine(self) -> EngineConfig | None:
        """Get the default engine configuration"""
        for engine in self.engines:
            if engine.get("default", False):
                return engine
        return None if not self.engines else self.engines[0]

    def get_engines(self) -> EngineConfig | None:
        return self.engines


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
        engines = self._raw_config.get("engines", [])
        return AppConfig(engines=engines)

    def get_engine(self, id: str) -> EngineConfig | None:
        """Get a specific engine by id"""
        for engine in self.config.engines:
            if engine.get("id") == id:
                return engine
        return None
