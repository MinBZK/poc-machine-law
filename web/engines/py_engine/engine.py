from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException

from machine.service import Services

from ..engine_interface import EngineInterface, PathNode, RuleResult
from .services.profiles import get_all_profiles, get_profile_data


class PythonMachineService(EngineInterface):
    """
    Implementation of EngineInterface using the embedded Python machine.service library.
    """

    def __init__(self, services: Services):
        self.services = services

    def get_profile_data(self, bsn: str) -> dict[str, Any]:
        """
        Get profile data for a specific BSN.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            Dictionary containing profile data or None if not found
        """
        return get_profile_data(bsn)

    def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """
        Get all available profiles.

        Returns:
            Dictionary mapping BSNs to profile data
        """
        return get_all_profiles()

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules using the embedded Python machine.service library.
        """

        # Get the rule specification
        rule_spec = self.get_rule_spec(law, datetime.today().strftime("%Y-%m-%d"), service)
        if not rule_spec:
            raise HTTPException(status_code=400, detail="Invalid law specified")

        self.set_profile_data(parameters["BSN"])

        result = self.services.evaluate(
            service=service,
            law=law,
            parameters=parameters,
            reference_date=reference_date,
            overwrite_input=overwrite_input,
            requested_output=requested_output,
            approved=approved,
        )

        # Convert RuleResult to dictionary
        return RuleResult(
            input=result.input,
            output=result.output,
            requirements_met=result.requirements_met,
            missing_required=result.missing_required,
            rulespec_uuid=result.rulespec_uuid,
            path=to_path_node(result.path),
        )

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens using the embedded Python machine.service library.
        """
        return self.services.get_discoverable_service_laws(discoverable_by)

    def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        """
        Get the rule specification for a specific law.

        Args:
            law: Law identifier
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service: Service provider code (e.g., "TOESLAGEN")

        Returns:
            Dictionary containing the rule specification
        """
        return self.services.resolver.get_rule_spec(law, reference_date, service)

    def set_profile_data(self, bsn: str) -> None:
        """
        Load profile data for a BSN into the machine service.

        Args:
            bsn: BSN identifier for the individual
        """
        # Get profile data for the BSN
        profile_data = get_profile_data(bsn)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Load source data into services
        for service_name, tables in profile_data["sources"].items():
            for table_name, data in tables.items():
                df = pd.DataFrame(data)
                self.set_source_dataframe(service_name, table_name, df)

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        self.services.set_source_dataframe(service, table, df)


def to_path_node(path_node) -> PathNode:
    return PathNode(
        type=path_node.type if path_node.type is not None else "",
        name=path_node.name if path_node.name is not None else "",
        result=path_node.result if path_node.result is not None else {},
        resolve_type=path_node.resolve_type if path_node.resolve_type is not None else "",
        required=path_node.required if path_node.required is not None else False,
        details=path_node.details if path_node.details is not None else {},
        children=[to_path_node(child) for child in path_node.children] if path_node.children else [],
    )
