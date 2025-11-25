from datetime import date, datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException

from machine.profile_loader import get_project_root, load_profiles_from_yaml
from machine.service import Services

from ..engine_interface import EngineInterface, PathNode, RuleResult


class PythonMachineService(EngineInterface):
    """
    Implementation of EngineInterface using the embedded Python machine.service library.
    """

    def __init__(self, services: Services):
        self.services = services

    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any]:
        """
        Get profile data for a specific BSN.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            Dictionary containing profile data or None if not found
        """
        profiles = self.get_all_profiles()
        return profiles.get(bsn)

    def get_all_profiles(self, effective_date: date | None = None) -> dict[str, dict[str, Any]]:
        """
        Get all available profiles.

        Returns:
            Dictionary mapping BSNs to profile data
        """
        project_root = get_project_root()
        profiles_path = project_root / "data" / "profiles.yaml"
        return load_profiles_from_yaml(profiles_path)

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        effective_date: str | None = None,
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

        Filters laws based on feature flags if they exist.
        """
        from web.feature_flags import FeatureFlags

        # Get discoverable laws from the service
        all_laws = self.services.get_discoverable_service_laws(discoverable_by)

        # Filter based on feature flags
        result = {}
        for service, laws in all_laws.items():
            result[service] = []
            for law in laws:
                # Check if the law is enabled in feature flags
                # If flag doesn't exist, law is enabled by default
                if FeatureFlags.is_law_enabled(service, law):
                    result[service].append(law)

        return result

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

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Set a source dataframe for a service and table."""
        self.services.set_source_dataframe(service, table, df)

    def get_toeslag_manager(self):
        """Get the ToeslagApplication for managing toeslag workflows."""
        return self.services.toeslag_manager

    def get_services(self):
        """Get the underlying Services instance."""
        return self.services


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
