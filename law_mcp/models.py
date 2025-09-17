"""
Type definitions for MCP law execution server.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LawExecutionResult:
    """Result from law execution"""

    output: dict[str, Any]
    requirements_met: bool
    input_data: dict[str, Any]
    rulespec_uuid: str
    missing_required: bool = False
    execution_path: dict[str, Any] | None = None


@dataclass
class LawSpec:
    """Law specification metadata"""

    uuid: str
    name: str
    law: str
    service: str
    description: str
    valid_from: str
    references: list[dict[str, str]] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ProfileData:
    """Citizen profile data"""

    bsn: str
    data: dict[str, Any]
    last_updated: datetime | None = None


@dataclass
class LawExecutionRequest:
    """Request for law execution"""

    bsn: str
    service: str
    law: str
    reference_date: str | None = None
    overrides: dict[str, Any] | None = None
    requested_output: str | None = None
    approved: bool = False


@dataclass
class AvailableLaw:
    """Available law information"""

    service: str
    law: str
    name: str | None = None
    description: str | None = None
    discoverable: bool = True
