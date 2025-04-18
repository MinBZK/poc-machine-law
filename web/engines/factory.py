from enum import Enum

from machine.service import Services

from .case_manager_interface import CaseManagerInterface
from .claim_manager_interface import ClaimManagerInterface
from .engine_interface import EngineInterface
from .http_engine import CaseManager as GoCaseManager
from .http_engine import ClaimManager as GoClaimManager
from .http_engine import GoMachineService
from .py_engine import CaseManager as PythonCaseManager
from .py_engine import ClaimManager as PythonClaimManager
from .py_engine import PythonMachineService


class MachineType(Enum):
    """Enum to specify which machine implementation to use."""

    PYTHON = "python"
    GO = "go"


class MachineFactory:
    """Factory for creating Machine service instances."""

    @staticmethod
    def create_machine_service(
        machine_type: MachineType, services: Services | None = None, go_api_url: str = "http://localhost:8081/v0"
    ) -> EngineInterface:
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
        if machine_type == MachineType.PYTHON:
            if services is None:
                raise ValueError("Services instance is required for Python implementation")
            return PythonMachineService(services)
        elif machine_type == MachineType.GO:
            return GoMachineService(base_url=go_api_url)
        else:
            raise ValueError(f"Unknown machine type: {machine_type}")


class CaseManagerFactory:
    """Factory for creating CaseManager instances."""

    @staticmethod
    def create_case_manager(
        machine_type: MachineType, services: Services | None = None, go_api_url: str = "http://localhost:8081/v0"
    ) -> CaseManagerInterface:
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
        if machine_type == MachineType.PYTHON:
            if services is None:
                raise ValueError("Services instance is required for Python implementation")
            return PythonCaseManager(services)
        elif machine_type == MachineType.GO:
            return GoCaseManager(base_url=go_api_url)
        else:
            raise ValueError(f"Unknown machine type: {machine_type}")


class ClaimManagerFactory:
    """Factory for creating ClaimManager instances."""

    @staticmethod
    def create_claim_manager(
        machine_type: MachineType, services: Services | None = None, go_api_url: str = "http://localhost:8081/v0"
    ) -> ClaimManagerInterface:
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
        if machine_type == MachineType.PYTHON:
            if services is None:
                raise ValueError("Services instance is required for Python implementation")
            return PythonClaimManager(services)
        elif machine_type == MachineType.GO:
            return GoClaimManager(base_url=go_api_url)
        else:
            raise ValueError(f"Unknown machine type: {machine_type}")
