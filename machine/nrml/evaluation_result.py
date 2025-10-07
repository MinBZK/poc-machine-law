from dataclasses import dataclass, field
from enum import nonmember
from typing import Any


@dataclass
class EvaluationResult:
    """Result of evaluating an NRML item"""

    Success: bool
    Source: str
    Node: Any = None
    Value: Any = None
    Error: str | None = None
    SubResults: list["EvaluationResult"] = field(default_factory=list)
    Action: str | None = None


def nested_result(
    source: str,
    child_result: EvaluationResult,
    node: Any = None,
    action: str | None = None,
    error: str | None = None,
) -> EvaluationResult:
    """Create a successful evaluation result"""
    if error is None:
        error = "Error occurred in dependency"

    return create_result(
        success=child_result.Success,
        value=child_result.Value,
        source=source,
        node=node,
        action=action,
        error=None if child_result.Success else error,
        sub_results=[child_result],
    )


def create_result(
    success: bool,
    value: Any = None,
    error: str | None = None,
    node: Any = None,
    sub_results: list[EvaluationResult] | None = None,
    source: str | None = None,
    action: str | None = None,
) -> EvaluationResult:
    """Create evaluation results with all properties"""
    return EvaluationResult(
        Success=success, Value=value, Error=error, Node=node, SubResults=sub_results or [], Source=source, Action=action
    )
