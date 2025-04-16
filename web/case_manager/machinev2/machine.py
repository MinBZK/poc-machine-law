from datetime import datetime
from typing import Any

import httpx
from machine_client.law_as_code_client import Client
from machine_client.law_as_code_client.api.law import evaluate, rule_spec_get, service_laws_discoverable_list
from machine_client.law_as_code_client.api.profile import profile_get, profile_list
from machine_client.law_as_code_client.models import (
    Evaluate,
    EvaluateBody,
    EvaluateParameters,
    Profile,
    ProfileSources,
)

from ..machine_interface import MachineInterface


class GoMachineService(MachineInterface):
    """
    Implementation of MachineInterface using HTTP calls to the Go backend service.
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

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

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

        with client as client:
            response = rule_spec_get.sync_detailed(
                client=client, service=service, law=law, reference_date=reference_date
            )
            content = response.parsed

            return content.data

    async def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Evaluate rules using HTTP calls to the Go backend service.
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = Evaluate(
            service=service, law=law, parameters=EvaluateParameters().from_dict(parameters), approved=approved
        )

        if reference_date:
            data.date = datetime.strptime(reference_date, "%Y-%m-%d").date()

        if overwrite_input:
            data.input = overwrite_input

        if requested_output:
            data.output = requested_output

        body = EvaluateBody(data=data)

        with client as client:
            response = evaluate.sync_detailed(client=client, body=body)
            content = response.parsed

            return {
                "output": content.data.output.to_dict(),
                "requirements_met": content.data.requirements_met,
                "input": content.data.input_.to_dict(),
                "rulespec_uuid": content.data.rulespec_id,
                # "path": content.data.pat/c, // TODO
                "missing_required": content.data.missing_required,
            }

    async def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens using HTTP calls to the Go backend service.
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = service_laws_discoverable_list.sync_detailed(client=client, discoverable_by=discoverable_by)
            content = response.parsed

            result = []
            for item in content.data:
                for law in item.laws:
                    result.append(
                        {
                            "service": item.name,
                            "law": law.name,
                        }
                    )

            return result

    async def get_sorted_discoverable_service_laws(self, bsn: str, discoverable_by="CITIZEN") -> list[dict[str, Any]]:
        """
        Get sorted laws discoverable by citizens using HTTP calls to the Go backend service.
        """

        return await self.get_discoverable_service_laws()

    def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = profile_list.sync_detailed(client=client)
            content = response.parsed

            result = {}
            for item in content.data:
                result[item.bsn] = profile_transform(item)

            return result

    def get_profile_data(self, bsn: str) -> dict[str, Any] | None:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = profile_get.sync_detailed(client=client, bsn=bsn)
            content = response.parsed

            return profile_transform(content.data)

    def extract_value_tree(root):
        return root

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)


def profile_transform(profile: Profile) -> dict[str, Any]:
    p = profile.to_dict()
    p["sources"] = source_transform(profile.sources)

    return p


def source_transform(sources: ProfileSources) -> dict[str, Any]:
    s = sources.to_dict()
    return s
