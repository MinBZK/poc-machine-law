"""
Regeldrukvermindering (Regulatory Burden Reduction) Service

This module provides functionality to calculate regulatory burden metrics from
machine-readable law YAML specifications. It demonstrates how machine-readable
laws can reduce administrative burden for entrepreneurs by:

1. Automatically retrieving data from base registries
2. Deduplicating data requirements across multiple permits
3. Consolidating multiple applications into a single form
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LawMetrics:
    """Metrics for a single law specification."""

    service: str
    law: str
    name: str
    parameters_required: int  # Fields the entrepreneur must fill in
    parameters_total: int  # Total parameters (required + optional)
    sources_auto_retrieved: int  # Data points from own data sources
    inputs_auto_retrieved: int  # Data points from other services
    source_details: list[dict[str, Any]] = field(default_factory=list)
    input_details: list[dict[str, Any]] = field(default_factory=list)
    parameter_details: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RegeldrukMetrics:
    """Combined metrics showing regulatory burden reduction."""

    # Individual law metrics
    laws: list[LawMetrics] = field(default_factory=list)

    # Combined totals (with deduplication)
    parameters_required_unique: int = 0  # Unique fields entrepreneur must fill
    parameters_total_unique: int = 0  # Total unique parameters
    sources_auto_retrieved_unique: int = 0  # Unique auto-retrieved sources
    inputs_auto_retrieved_unique: int = 0  # Unique cross-service inputs

    # Cross-organization sources (registries consulted)
    cross_org_sources: list[str] = field(default_factory=list)

    # Time estimates
    estimated_time_traditional_minutes: int = 0
    estimated_time_machine_law_minutes: int = 0
    estimated_time_saved_minutes: int = 0

    # Consolidation stats
    forms_consolidated: int = 0  # Number of forms -> 1
    documents_not_needed: list[str] = field(default_factory=list)

    # Traditional process steps (for comparison display)
    traditional_steps: list[str] = field(default_factory=list)


def load_law_yaml(service: str, law: str) -> dict[str, Any] | None:
    """Load a law YAML file by service and law path."""
    # Try multiple possible locations
    base_paths = [
        Path("submodules/regelrecht-laws/laws"),
        Path("laws"),
    ]

    for base_path in base_paths:
        # Look for the law file
        law_dir = base_path / law
        if law_dir.exists():
            # Find YAML files for this service
            yaml_files = list(law_dir.glob(f"*{service}*.yaml"))
            if yaml_files:
                with open(yaml_files[0]) as f:
                    return yaml.safe_load(f)

        # Also check gemeenten subdirectory
        gemeenten_dir = base_path / law / "gemeenten"
        if gemeenten_dir.exists():
            yaml_files = list(gemeenten_dir.glob(f"*{service}*.yaml"))
            if yaml_files:
                with open(yaml_files[0]) as f:
                    return yaml.safe_load(f)

    return None


def extract_service_from_reference(ref: dict[str, Any]) -> str | None:
    """Extract the service organization from a service_reference."""
    if "service_reference" in ref:
        return ref["service_reference"].get("service")
    return None


def calculate_law_metrics(service: str, law: str) -> LawMetrics | None:
    """Calculate metrics for a single law specification."""
    law_data = load_law_yaml(service, law)
    if not law_data:
        return None

    properties = law_data.get("properties", {})
    parameters = properties.get("parameters", [])
    sources = properties.get("sources", [])
    inputs = properties.get("input", [])

    # Count required vs total parameters
    required_params = [p for p in parameters if p.get("required", False)]
    param_details = [
        {
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "required": p.get("required", False),
            "type": p.get("type", "string"),
        }
        for p in parameters
    ]

    # Extract source details
    source_details = [
        {
            "name": s.get("name", ""),
            "description": s.get("description", ""),
            "source_table": s.get("source_reference", {}).get("table", ""),
        }
        for s in sources
    ]

    # Extract input details with service references
    input_details = [
        {
            "name": i.get("name", ""),
            "description": i.get("description", ""),
            "service": extract_service_from_reference(i),
            "law": i.get("service_reference", {}).get("law", ""),
            "field": i.get("service_reference", {}).get("field", ""),
        }
        for i in inputs
    ]

    return LawMetrics(
        service=service,
        law=law,
        name=law_data.get("name", law),
        parameters_required=len(required_params),
        parameters_total=len(parameters),
        sources_auto_retrieved=len(sources),
        inputs_auto_retrieved=len(inputs),
        source_details=source_details,
        input_details=input_details,
        parameter_details=param_details,
    )


def calculate_combined_metrics(laws: list[tuple[str, str]]) -> RegeldrukMetrics:
    """
    Calculate combined metrics for multiple laws with deduplication.

    Args:
        laws: List of (service, law) tuples to analyze

    Returns:
        RegeldrukMetrics with combined totals and deduplication analysis
    """
    metrics = RegeldrukMetrics()
    metrics.forms_consolidated = len(laws)

    # Track unique items for deduplication
    unique_params: set[str] = set()
    unique_required_params: set[str] = set()
    unique_sources: set[str] = set()
    unique_inputs: set[str] = set()
    services_consulted: set[str] = set()

    for service, law in laws:
        law_metrics = calculate_law_metrics(service, law)
        if law_metrics:
            metrics.laws.append(law_metrics)

            # Collect unique parameters
            for p in law_metrics.parameter_details:
                param_name = p.get("name", "")
                unique_params.add(param_name)
                if p.get("required", False):
                    unique_required_params.add(param_name)

            # Collect unique sources
            for s in law_metrics.source_details:
                unique_sources.add(s.get("name", ""))

            # Collect unique inputs and services
            for i in law_metrics.input_details:
                unique_inputs.add(i.get("name", ""))
                svc = i.get("service")
                if svc:
                    services_consulted.add(svc)

    # Calculate unique totals
    metrics.parameters_required_unique = len(unique_required_params)
    metrics.parameters_total_unique = len(unique_params)
    metrics.sources_auto_retrieved_unique = len(unique_sources)
    metrics.inputs_auto_retrieved_unique = len(unique_inputs)
    metrics.cross_org_sources = sorted(services_consulted)

    # Time estimates (based on research and typical permit application times)
    # Traditional: ~45 min per form + 120 min for document gathering
    traditional_per_form = 45
    document_gathering = 120  # VOG requests, KVK extracts, etc.
    metrics.estimated_time_traditional_minutes = (len(laws) * traditional_per_form) + document_gathering

    # Machine Law: ~15 min single unified form (no document gathering needed)
    metrics.estimated_time_machine_law_minutes = 15

    metrics.estimated_time_saved_minutes = (
        metrics.estimated_time_traditional_minutes - metrics.estimated_time_machine_law_minutes
    )

    # Documents that are no longer manually required
    metrics.documents_not_needed = [
        "VOG (Verklaring Omtrent Gedrag)",
        "KVK-uittreksel",
        "Kadaster-inzage",
        "BAG-registratie",
        "BGT-kaartmateriaal",
        "Horecagebiedsplan controle",
    ]

    # Traditional process steps
    metrics.traditional_steps = get_traditional_process_steps(len(laws))

    return metrics


def get_traditional_process_steps(num_permits: int) -> list[str]:
    """Generate the traditional process steps for comparison."""
    steps = []

    for i in range(1, num_permits + 1):
        steps.append(f"Formulier {i} downloaden van gemeente website")
        steps.append(f"Formulier {i} handmatig invullen")
        steps.append(f"Bijlagen verzamelen voor formulier {i}")

    steps.extend(
        [
            "VOG aanvragen bij Justis (wachttijd: 1-4 weken)",
            "KVK-uittreksel opvragen",
            "Kadaster inzien voor pandgegevens",
            "Horecagebiedsplan controleren",
            "Omgevingsplan raadplegen",
            "Alle documenten verzamelen en uploaden",
            "Wachten op ontvangstbevestiging",
            f"Wachten op {num_permits} separate beslissingen",
        ]
    )

    return steps


def get_machine_law_process_steps() -> list[str]:
    """Generate the Machine Law process steps."""
    return [
        "KVK-nummer invullen",
        "Terrasgegevens invullen (indien van toepassing)",
        "Aanvraag versturen",
        "Direct resultaat ontvangen",
    ]
