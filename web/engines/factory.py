from datetime import datetime
from enum import Enum

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


class MachineType(Enum):
    """Enum to specify which machine implementation to use."""

    INTERNAL = "internal"
    HTTP = "http"


config_loader = ConfigLoader()

# Configure service for the internal engine
services = Services(datetime.today().strftime("%Y-%m-%d"))


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
