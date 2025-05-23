"""
Model Context Protocol (MCP) services for Dutch legal regulations.
This module wraps law execution engines as MCP-compatible services based on the
Model Context Protocol specification: https://contextprovider.ai/
"""

from typing import Any

from web.dependencies import TODAY
from web.engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface


class MCPServiceRegistry:
    """Registry for MCP services related to Dutch laws"""

    def __init__(
        self,
        services: EngineInterface,
        case_manager: CaseManagerInterface,
        claim_manager: ClaimManagerInterface,
    ):
        self.services = services
        self.case_manager = case_manager
        self.claim_manager = claim_manager

        self.law_services = {}
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all available law services by discovering available laws"""
        self.law_services = {}

        # Generate default service mapping from resolver data

        # Common name transformations for better display
        name_transformations = {
            "zorgtoeslagwet": "zorgtoeslag",
            "wet_op_de_huurtoeslag": "huurtoeslag",
            "participatiewet/bijstand": "bijstand",
            "kieswet": "kieswet",
            "algemene_ouderdomswet": "aow",
            "wet_inkomstenbelasting": "inkomstenbelasting",
            "wet_kinderopvang": "kinderopvangtoeslag",
        }

        # Get all discoverable services for citizens
        try:
            # Get discoverable service laws from the resolver for citizens
            discoverable_laws = self.services.get_discoverable_service_laws("CITIZEN")
            print(f"Discovered services and laws: {discoverable_laws}")

            # Generate service instances for each discoverable law
            for service_type, laws in discoverable_laws.items():
                for law_path in laws:
                    # Create a user-friendly name for the service
                    service_name = None

                    # Try to match with our name transformations
                    for prefix, friendly_name in name_transformations.items():
                        if law_path.startswith(prefix):
                            service_name = friendly_name
                            break

                    # If no match, generate a name from the law path
                    if not service_name:
                        # Extract the base name from the law path
                        base_name = law_path.split("/")[0]
                        service_name = base_name.lower().replace("_", "")

                    # Prevent duplicate services
                    if service_name not in self.law_services:
                        try:
                            # Get rule spec to extract metadata
                            rule_spec = self.services.get_rule_spec(law_path, "2025-01-01", service_type)

                            # Use the official name from the rule spec if available
                            description = rule_spec.get("name", service_name.capitalize())

                            # Create and register the service
                            service = GenericMCPService(
                                self.services,
                                name=service_name,
                                description=description,
                                law_path=law_path,
                                service_type=service_type,
                            )
                            self.law_services[service_name] = service
                            print(f"Added service: {service_name} ({description}) for law {law_path}")
                        except Exception as e:
                            print(f"Error adding service for {law_path}: {e}")
                            import traceback

                            traceback.print_exc()
        except Exception as e:
            print(f"Error discovering laws: {e}")
            import traceback

            traceback.print_exc()

    def get_service_names(self) -> list[str]:
        """Get all available service names"""
        return list(self.law_services.keys())

    def get_service(self, name: str):
        """Get a specific service by name"""
        return self.law_services.get(name)

    def execute_law(self, law_name: str, bsn: str, params: dict | None = None) -> dict[str, Any]:
        """Execute a law for a specific BSN with optional additional parameters"""
        service = self.get_service(law_name)
        if not service:
            return {"error": f"Law service '{law_name}' not found"}

        return service.execute(bsn, params or {})


class BaseMCPService:
    """Base class for MCP services"""

    def __init__(self, services: EngineInterface):
        self.services = services
        self.name = "base"
        self.description = "Base MCP service"
        self.law_path = ""
        self.service_type = ""

    def execute(self, bsn: str, params: dict) -> dict[str, Any]:
        """Execute the law for a specific BSN with parameters"""
        # Get the rule specification
        rule_spec = self.services.get_rule_spec(self.law_path, TODAY, self.service_type)
        if not rule_spec:
            return {"error": f"Invalid law specified: {self.law_path}"}

        # Execute the law
        parameters = {"BSN": bsn, **params}
        result = self.services.evaluate(
            self.service_type, law=self.law_path, parameters=parameters, reference_date=TODAY, approved=False
        )

        # Extract missing fields if any required values are missing
        missing_fields = []
        if result.missing_required:
            # Extract missing required fields from the value tree
            value_tree = self.services.extract_value_tree(result.path)

            for path, node_info in value_tree.items():
                if node_info.get("required") and not node_info.get("result"):
                    # Get the field name (last part of the path)
                    field_name = path.split(".")[-1]
                    missing_fields.append(field_name)

        # Format the result
        return {
            "eligibility": result.requirements_met,
            "requirements_met": result.requirements_met,
            "result": result.output,
            "input_data": result.input,
            "missing_requirements": result.missing_required,
            "missing_required": result.missing_required,
            "missing_fields": missing_fields,
            "explanation": self._format_explanation(result, rule_spec),
        }

    def _format_explanation(self, result, rule_spec):
        """Format a simple explanation of the result"""
        if result.requirements_met:
            return f"U voldoet aan alle voorwaarden voor {self.description}."
        elif result.missing_required:
            # Use the missing_fields that were extracted in the execute method
            missing_fields = []
            value_tree = self.services.extract_value_tree(result.path)

            for path, node_info in value_tree.items():
                if node_info.get("required") and not node_info.get("result"):
                    # Get the field name (last part of the path)
                    field_name = path.split(".")[-1]
                    missing_fields.append(field_name)

            if missing_fields:
                return (
                    f"U voldoet niet aan alle voorwaarden voor {self.description}. "
                    + f"U mist de volgende voorwaarden: {', '.join(missing_fields)}."
                )
            else:
                return f"U voldoet niet aan alle voorwaarden voor {self.description}. Er ontbreken essentiële gegevens."
        else:
            return f"Er kan niet worden vastgesteld of u recht heeft op {self.description}."


class GenericMCPService(BaseMCPService):
    """Generic MCP service for any law calculation"""

    def __init__(self, services: EngineInterface, name: str, description: str, law_path: str, service_type: str):
        super().__init__(services)
        self.name = name
        self.description = description
        self.law_path = law_path
        self.service_type = service_type

    def __str__(self):
        return f"MCP Service: {self.name} ({self.description}) - Path: {self.law_path}, Type: {self.service_type}"
