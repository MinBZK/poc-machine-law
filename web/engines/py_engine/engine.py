from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException

from machine.service import Services

from ..engine_interface import EngineInterface, RuleResult
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

    async def evaluate(
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
        rule_spec = self.services.resolver.get_rule_spec(law, datetime.today().strftime("%Y-%m-%d"), service)
        if not rule_spec:
            raise HTTPException(status_code=400, detail="Invalid law specified")

        self.set_profile_data(parameters["BSN"])

        result = await self.services.evaluate(
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
            output=result.output,
            requirements_met=result.requirements_met,
            input=result.input,
            rulespec_uuid=result.rulespec_uuid,
            path=result.path,
            missing_required=result.missing_required,
        )

    async def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens using the embedded Python machine.service library.
        """
        return await self.services.get_discoverable_service_laws(discoverable_by)

    async def get_sorted_discoverable_service_laws(self, bsn: str) -> list[dict[str, Any]]:
        """
        Get sorted laws discoverable by citizens using the embedded Python machine.service library.
        """
        return await self.services.get_sorted_discoverable_service_laws(bsn)

    async def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
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
                self.services.set_source_dataframe(service_name, table_name, df)
