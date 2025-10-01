from dataclasses import dataclass
from typing import Any


@dataclass
class FactItemEvaluationResult:
    """Result of evaluating an NRML item"""

    Success: bool
    Value: Any
