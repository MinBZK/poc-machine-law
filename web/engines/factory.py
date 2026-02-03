import logging
from datetime import datetime
from enum import Enum

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

        with open(profiles_path) as f:
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
                    if (
                        service_name in global_service_ids
                        and table_name in global_service_ids[service_name]
                        and id(data) == global_service_ids[service_name][table_name]
                    ):
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
                        rule_service.source_dataframes[table_name] = pd.concat([existing_df, df], ignore_index=True)
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


def _seed_historical_cases(services_instance: Services) -> None:
    """
    Seed historical cases from profiles.yaml into the CaseManager.

    This uses the `case_seeds` configuration in profiles.yaml to determine which
    historical data tables should be loaded as cases. This enables source_type: "cases"
    queries to count historical approvals.

    Example configuration in profiles.yaml:
    ```yaml
    case_seeds:
      - service: "GEMEENTE_ROTTERDAM"
        law: "algemene_plaatselijke_verordening/ontheffingspas_geluid"
        table: "ontheffingen_geluid_historie"
        bsn_lookup:
          table: "inschrijvingen"
          match_field: "kvk_nummer"
          bsn_field: "bsn_eigenaar"
        parameters:
          KVK_NUMMER: "kvk_nummer"
          ACTIVITEITSDATUM: "datum"
        result:
          komt_in_aanmerking_voor_geluidsontheffing: true
    ```
    """
    try:
        project_root = get_project_root()
        profiles_path = project_root / "data" / "profiles.yaml"

        import yaml

        with open(profiles_path) as f:
            raw_data = yaml.safe_load(f)

        case_seeds_config = raw_data.get("case_seeds", [])
        if not case_seeds_config:
            logger.debug("No case_seeds configuration found in profiles.yaml")
            return

        profiles = raw_data.get("profiles", {})
        seeded_count = 0

        for seed_config in case_seeds_config:
            service = seed_config.get("service")
            law = seed_config.get("law")
            table_name = seed_config.get("table")
            bsn_lookup = seed_config.get("bsn_lookup", {})
            param_mapping = seed_config.get("parameters", {})
            result_template = seed_config.get("result", {})

            if not all([service, law, table_name]):
                logger.warning(f"Incomplete case_seeds config: {seed_config}")
                continue

            # Process each profile
            for profile_id, profile_data in profiles.items():
                sources = profile_data.get("sources", {})
                service_data = sources.get(service, {})

                # Get the historical data table
                historie = service_data.get(table_name, [])
                if not historie:
                    continue

                # Get BSN lookup table if configured
                lookup_table = []
                if bsn_lookup:
                    lookup_table = service_data.get(bsn_lookup.get("table", ""), [])

                for record in historie:
                    # Build parameters from mapping
                    parameters = {}
                    for param_name, field_name in param_mapping.items():
                        value = record.get(field_name)
                        if value is not None:
                            parameters[param_name] = value

                    # Extract year from date field if present
                    for param_name, value in parameters.items():
                        if "datum" in param_name.lower() or "date" in param_name.lower():
                            if isinstance(value, str) and len(value) >= 4:
                                parameters["year"] = int(value[:4])
                            break

                    # Find BSN via lookup table
                    bsn = None
                    if bsn_lookup and lookup_table:
                        match_field = bsn_lookup.get("match_field")
                        bsn_field = bsn_lookup.get("bsn_field")
                        match_value = record.get(match_field)

                        for lookup_record in lookup_table:
                            if lookup_record.get(match_field) == match_value:
                                bsn = lookup_record.get(bsn_field)
                                break
                    else:
                        # Try to get BSN directly from record or profile
                        bsn = record.get("bsn") or profile_id

                    if not bsn:
                        logger.warning(f"No BSN found for record in {table_name}, skipping")
                        continue

                    # Seed the historical case
                    services_instance.case_manager.seed_historical_case(
                        bsn=bsn,
                        service_type=service,
                        law=law,
                        parameters=parameters,
                        result=result_template,
                    )
                    seeded_count += 1

        logger.info(f"Seeded {seeded_count} historical cases from {len(case_seeds_config)} configurations")

    except Exception as e:
        logger.error(f"Failed to seed historical cases: {e}")


# Seed historical cases after profiles are loaded
_seed_historical_cases(services)


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
            logger.info(f"[MachineFactory] Creating PythonMachineService for engine: {engine_id}")
            return PythonMachineService(services)
        elif engine_type == MachineType.HTTP:
            logger.info(
                f"[MachineFactory] Creating HTTPMachineService for engine: {engine_id}, domain: {engine.domain}"
            )
            if engine.service_routing:
                logger.info(f"[MachineFactory] Service routing config: enabled={engine.service_routing.enabled}")
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
            logger.info(f"[CaseManagerFactory] Creating PythonCaseManager for engine: {engine_id}")
            return PythonCaseManager(services)
        elif engine_type == MachineType.HTTP:
            logger.info(
                f"[CaseManagerFactory] Creating HTTPCaseManager for engine: {engine_id}, domain: {engine.domain}"
            )
            if engine.service_routing:
                logger.info(f"[CaseManagerFactory] Service routing config: enabled={engine.service_routing.enabled}")
            return HTTPCaseManager(base_url=engine.domain, service_routing_config=engine.service_routing)
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
            logger.info(f"[ClaimManagerFactory] Creating PythonClaimManager for engine: {engine_id}")
            return PythonClaimManager(services)
        elif engine_type == MachineType.HTTP:
            logger.info(
                f"[ClaimManagerFactory] Creating HTTPClaimManager for engine: {engine_id}, domain: {engine.domain}"
            )
            if engine.service_routing:
                logger.info(f"[ClaimManagerFactory] Service routing config: enabled={engine.service_routing.enabled}")
            return HTTPClaimManager(base_url=engine.domain, service_routing_config=engine.service_routing)
        else:
            raise ValueError(f"Unknown machine type: {engine_type}")
