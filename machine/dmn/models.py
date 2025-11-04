"""
Data models for DMN structures.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from machine.context import PathNode


class HitPolicy(Enum):
    """DMN decision table hit policies."""
    UNIQUE = "U"
    FIRST = "F"
    ANY = "A"
    PRIORITY = "P"
    COLLECT = "C"
    RULE_ORDER = "R"
    OUTPUT_ORDER = "O"


class ExpressionType(Enum):
    """Types of DMN expressions."""
    LITERAL = "literal"
    DECISION_TABLE = "decision_table"
    INVOCATION = "invocation"
    CONTEXT = "context"


@dataclass
class DMNInput:
    """Represents an input data element in a DMN model."""
    id: str
    name: str
    variable_name: str
    type_ref: str = "Any"


@dataclass
class DMNOutput:
    """Represents an output element in a decision."""
    id: str
    name: str
    variable_name: str
    type_ref: str = "Any"


@dataclass
class DecisionTableRule:
    """Represents a single rule in a decision table."""
    id: str
    input_entries: List[str]  # FEEL expressions for input conditions
    output_entries: List[str]  # FEEL expressions for outputs
    annotations: List[str] = field(default_factory=list)


@dataclass
class DecisionTableInput:
    """Represents an input column in a decision table."""
    id: str
    label: str
    input_expression: str  # FEEL expression
    type_ref: str = "Any"


@dataclass
class DecisionTableOutput:
    """Represents an output column in a decision table."""
    id: str
    label: str
    name: str
    type_ref: str = "Any"


@dataclass
class DecisionTable:
    """Represents a DMN decision table."""
    hit_policy: HitPolicy
    inputs: List[DecisionTableInput]
    outputs: List[DecisionTableOutput]
    rules: List[DecisionTableRule]


@dataclass
class LiteralExpression:
    """Represents a literal FEEL expression."""
    text: str
    type_ref: str = "Any"


@dataclass
class BusinessKnowledgeModel:
    """Represents a DMN Business Knowledge Model (BKM)."""
    id: str
    name: str
    variable_name: str
    parameters: List[DMNInput]  # Formal parameters
    expression: Any  # LiteralExpression or other
    type_ref: str = "Any"


@dataclass
class DMNDecision:
    """Represents a DMN decision element."""
    id: str
    name: str
    variable_name: str
    expression_type: ExpressionType
    expression: Any  # DecisionTable, LiteralExpression, etc.
    required_inputs: List[str] = field(default_factory=list)  # Input data IDs
    required_decisions: List[str] = field(default_factory=list)  # Decision IDs
    required_knowledge: List[str] = field(default_factory=list)  # BKM IDs
    type_ref: str = "Any"


@dataclass
class DMNImport:
    """Represents an import of another DMN model."""
    namespace: str
    location_uri: str
    import_type: str


@dataclass
class DecisionService:
    """Represents a DMN decision service."""
    id: str
    name: str
    output_decisions: List[str]  # Decision IDs
    input_data: List[str]  # Input data IDs


@dataclass
class DMNSpec:
    """Complete parsed DMN model specification."""
    id: str
    name: str
    namespace: str
    exporter: Optional[str]
    file_path: Path

    inputs: Dict[str, DMNInput] = field(default_factory=dict)
    decisions: Dict[str, DMNDecision] = field(default_factory=dict)
    bkms: Dict[str, BusinessKnowledgeModel] = field(default_factory=dict)
    decision_services: Dict[str, DecisionService] = field(default_factory=dict)
    imports: List[DMNImport] = field(default_factory=list)


@dataclass
class DMNResult:
    """Result of executing a DMN decision."""
    output: Dict[str, Any]
    decision_id: str
    requirements_met: bool
    input: Dict[str, Any]
    dmn_spec_id: str
    path: Optional[PathNode] = None
    missing_required: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class DMNEvaluationTrace:
    """Trace of a decision evaluation for debugging."""
    decision_id: str
    decision_name: str
    inputs_used: Dict[str, Any]
    output_produced: Any
    child_decisions: List['DMNEvaluationTrace'] = field(default_factory=list)
    execution_time_ms: float = 0.0
