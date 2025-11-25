# Legacy module - Toeslag aggregate and application have been moved to Case aggregate
# Only TimeSimulator remains here for time-based simulation
from .timesimulator import MonthResult, TimeSimulator, YearResult

__all__ = [
    "TimeSimulator",
    "MonthResult",
    "YearResult",
]
