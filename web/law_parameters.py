"""Stub for law parameter discovery.

The old auto-discovery mechanism walked the Python rules engine's
`engine.definitions` / `engine.property_specs`, which no longer exist.
The Rust engine does not (yet) expose an equivalent API, so parameter
introspection for the simulation UI returns an empty dict. The simulation
still runs — it just uses the YAML-defined defaults.
"""

from typing import Any


def get_default_law_parameters_subprocess(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """Return the set of overridable law parameters. Currently empty."""
    return {}
