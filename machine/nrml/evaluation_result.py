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

def success_result(
    value: Any,
    source: str,
    node: Any = None,
    sub_results: list[EvaluationResult] | None = None,
    action: str | None = None
) -> EvaluationResult:
    """Create a successful evaluation result"""
    return _create_result(success=True, value=value, source=source, node=node, sub_results=sub_results, action=action)

def evaluation_result(
    success: bool,
    value: Any,
    source: str,
    node: Any = None,
    sub_results: list[EvaluationResult] | None = None,
    action: str | None = None
) -> EvaluationResult:
    """Create a successful evaluation result"""
    return _create_result(success=success, value=value, source=source, node=node, sub_results=sub_results, action=action)

def failure_result(
    error_message: str,
    source: str,
    node: Any = None,
    sub_results: list[EvaluationResult] | None = None,
    action: str | None = None
) -> EvaluationResult:
    """Create a failed evaluation result"""
    return _create_result(success=False, error=error_message, source=source, node=node, sub_results=sub_results, action=action)

def nested_result(
    source: str,
    child_result: EvaluationResult,
    node: Any = None,
    action: str | None = None
) -> EvaluationResult:
    """Create a successful evaluation result"""
    if child_result.Success:
        return success_result(value=child_result.Value, source=source, node=node, action=action, sub_results=[child_result])
    else:
        return failure_result(error_message="Error occurred in dependency", source=source, node=node, sub_results=[child_result])

def _create_result(
    success: bool,
    value: Any = None,
    error: str | None = None,
    node: Any = None,
    sub_results: list[EvaluationResult] | None = None,
    source: str | None = None,
    action: str | None = None
) -> EvaluationResult:
    """Private function to create evaluation results with all properties"""
    return EvaluationResult(
        Success=success,
        Value=value,
        Error=error,
        Node=node,
        SubResults=sub_results or [],
        Source=source,
        Action=action
    )