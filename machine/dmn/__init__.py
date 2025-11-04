"""
DMN (Decision Model and Notation) execution engine.

This package provides a custom DMN 1.3 interpreter for executing
DMN XML files with FEEL expressions.

Main components:
- DMNEngine: Main execution engine
- DMNSpec: Parsed DMN model
- DMNResult: Execution results
- FEELEvaluator: FEEL expression evaluator
"""

from .context import DMNContext
from .engine import DMNEngine
from .exceptions import (
    CircularDependencyError,
    DecisionNotFoundError,
    DecisionServiceNotFoundError,
    DMNError,
    DMNExecutionError,
    DMNFileNotFoundError,
    DMNParseError,
    DMNValidationError,
    FEELEvaluationError,
    FEELSyntaxError,
    UnsupportedFEELFeatureError,
)
from .feel_evaluator import FEELEvaluator
from .models import (
    BusinessKnowledgeModel,
    DecisionService,
    DecisionTable,
    DecisionTableInput,
    DecisionTableOutput,
    DecisionTableRule,
    DMNDecision,
    DMNEvaluationTrace,
    DMNImport,
    DMNInput,
    DMNOutput,
    DMNResult,
    DMNSpec,
    ExpressionType,
    HitPolicy,
    LiteralExpression,
)
from .xml_parser import DMNXMLParser

__all__ = [
    # Main engine
    'DMNEngine',
    # Parsers and evaluators
    'DMNXMLParser',
    'FEELEvaluator',
    # Models
    'DMNSpec',
    'DMNDecision',
    'DMNInput',
    'DMNOutput',
    'DMNResult',
    'DMNImport',
    'DecisionService',
    'DecisionTable',
    'DecisionTableInput',
    'DecisionTableOutput',
    'DecisionTableRule',
    'LiteralExpression',
    'BusinessKnowledgeModel',
    'DMNEvaluationTrace',
    # Enums
    'ExpressionType',
    'HitPolicy',
    # Context
    'DMNContext',
    # Exceptions
    'DMNError',
    'DMNFileNotFoundError',
    'DMNParseError',
    'DMNValidationError',
    'DMNExecutionError',
    'FEELSyntaxError',
    'FEELEvaluationError',
    'DecisionNotFoundError',
    'DecisionServiceNotFoundError',
    'CircularDependencyError',
    'UnsupportedFEELFeatureError',
]
