import logging
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd

from machine.profile_loader import get_project_root, load_profiles_from_yaml
from machine.service import Services
from web.config_loader import ConfigLoader

from .case_manager_interface import CaseManagerInterface
from .claim_manager_interface import ClaimManagerInterface
from .engine_interface import EngineInterface
from .http_engine import CaseManager as HTTPCaseManager
from .http_engine import ClaimManager as HTTPClaimManager
from .http_engine import MachineService as HTTPMachineService
from .py_engine import CaseManager as PythonCaseManager
from .py_engine import ClaimManager as PythonClaimManager
from .py_engine import PythonMachineService

logger = logging.getLogger(__name__)


class MachineType(Enum):
    """Enum to specify which machine implementation to use."""

    INTERNAL = "internal"
    HTTP = "http"


config_loader = ConfigLoader()

# Configure service for the internal engine
services = Services(datetime.today().strftime("%Y-%m-%d"))


def _initialize_profiles(services_instance: Services) -> None:
    """
    Load all profiles from YAML and initialize them into the services instance.

    This ensures that all profile data (including related personas like partners and children)
    is available in the dataframes for query resolution.
    """
    try:
        # Load profiles from YAML
        project_root = get_project_root()
        profiles_path = project_root / "data" / "profiles.yaml"

        logger.info(f"Loading profiles from {profiles_path}")

        # Load the raw YAML to access globalServices
        import yaml
        with open(profiles_path, "r") as f:
            raw_data = yaml.safe_load(f)

        global_services = raw_data.get("globalServices", {})
        global_service_ids = {}  # Track object IDs of global service data

        # Load global services ONCE into dataframes
        logger.info(f"Loading {len(global_services)} global services")
        for service_name, tables in global_services.items():
            if service_name not in services_instance.services:
                logger.warning(f"Global service {service_name} not found in services, skipping")
                continue

            rule_service = services_instance.services[service_name]
            global_service_ids[service_name] = {}

            for table_name, data in tables.items():
                global_service_ids[service_name][table_name] = id(data)  # Store object ID

                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    logger.warning(f"Unexpected data type for global {service_name}.{table_name}: {type(data)}")
                    continue

                rule_service.source_dataframes[table_name] = df
                logger.debug(f"Loaded global {service_name}.{table_name}: {len(df)} rows")

        profiles = load_profiles_from_yaml(profiles_path)

        # Initialize each profile's data into the services
        for profile_id, profile_data in profiles.items():
            logger.debug(f"Initializing profile {profile_id}: {profile_data.get('name', 'Unknown')}")

            # Load source data into services
            for service_name, tables in profile_data.get("sources", {}).items():
                # Get the RuleService for this service
                if service_name not in services_instance.services:
                    logger.warning(f"Service {service_name} not found in services, skipping")
                    continue

                rule_service = services_instance.services[service_name]
                logger.debug(f"Processing {service_name} for profile {profile_id}, tables: {list(tables.keys())}")

                for table_name, data in tables.items():
                    # Skip if this is global data (check object ID to detect YAML anchor references)
                    if service_name in global_service_ids and table_name in global_service_ids[service_name]:
                        if id(data) == global_service_ids[service_name][table_name]:
                            logger.debug(f"Skipping global data reference for {service_name}.{table_name}")
                            continue

                    # Convert data to DataFrame
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        df = pd.DataFrame([data])
                    else:
                        logger.warning(f"Unexpected data type for {service_name}.{table_name}: {type(data)}")
                        continue

                    # Append to existing dataframe or create new one
                    if table_name in rule_service.source_dataframes:
                        # Append to existing dataframe
                        existing_df = rule_service.source_dataframes[table_name]
                        rule_service.source_dataframes[table_name] = pd.concat(
                            [existing_df, df], ignore_index=True
                        )
                        logger.debug(f"Appended {len(df)} rows to {service_name}.{table_name}")
                    else:
                        # Create new dataframe (this shouldn't happen if globals are loaded first)
                        rule_service.source_dataframes[table_name] = df
                        logger.debug(f"Created {service_name}.{table_name} with {len(df)} rows")

        logger.info(f"Successfully initialized {len(profiles)} profiles into services")

    except Exception as e:
        logger.error(f"Failed to initialize profiles: {e}")
        # Don't fail the application startup, just log the error
        # This allows the app to run even if profiles.yaml is missing


# Initialize all profiles at startup
_initialize_profiles(services)


class MachineFactory:
    """Factory for creating Machine service instances."""

    @staticmethod
    def create_machine_service(engine_id: str) -> EngineInterface:
        """
        Create a machine service of the specified type.

        Args:
            machine_type: The type of machine implementation to use
            services: The Services instance (required for PYTHON type)
            go_api_url: The URL for the Go API (used for GO type)

        Returns:
            An instance of a EngineInterface implementation

        Raises:
            ValueError: If machine_type is PYTHON and services is None
        """

        engine = config_loader.get_engine(engine_id)
        engine_type = MachineType(engine.type)

        if engine_type == MachineType.INTERNAL:
            if services is None:
                raise ValueError("Services instance is required for internal Python implementation")
            return PythonMachineService(services)
        elif engine_type == MachineType.HTTP:
            return HTTPMachineService(base_url=engine.domain, service_routing_config=engine.service_routing)
        else:
            raise ValueError(f"Unknown machine type: {engine_type}")


class CaseManagerFactory:
    """Factory for creating CaseManager instances."""

    @staticmethod
    def create_case_manager(engine_id: str) -> CaseManagerInterface:
        """
        Create a case manager of the specified type.

        Args:
            machine_type: The type of machine implementation to use
            services: The Services instance (required for PYTHON type)
            go_api_url: The URL for the Go API (used for GO type)

        Returns:
            An instance of a CaseManagerInterface implementation

        Raises:
            ValueError: If machine_type is PYTHON and services is None
        """

        engine = config_loader.get_engine(engine_id)
        engine_type = MachineType(engine.type)

        if engine_type == MachineType.INTERNAL:
            if services is None:
                raise ValueError("Services instance is required for internal Python implementation")
            return PythonCaseManager(services)
        elif engine_type == MachineType.HTTP:
            return HTTPCaseManager(base_url=engine.domain)
        else:
            raise ValueError(f"Unknown machine type: {engine_type}")


class ClaimManagerFactory:
    """Factory for creating ClaimManager instances."""

    @staticmethod
    def create_claim_manager(engine_id: str) -> ClaimManagerInterface:
        """
        Create a case manager of the specified type.

        Args:
            machine_type: The type of machine implementation to use
            services: The Services instance (required for PYTHON type)
            go_api_url: The URL for the Go API (used for GO type)

        Returns:
            An instance of a ClaimManagerInterface implementation

        Raises:
            ValueError: If machine_type is PYTHON and services is None
        """

        engine = config_loader.get_engine(engine_id)
        engine_type = MachineType(engine.type)

        if engine_type == MachineType.INTERNAL:
            if services is None:
                raise ValueError("Services instance is required for internal Python implementation")
            return PythonClaimManager(services)
        elif engine_type == MachineType.HTTP:
            return HTTPClaimManager(base_url=engine.domain)
        else:
            raise ValueError(f"Unknown machine type: {engine_type}")
