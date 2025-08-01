"""
Comprehensive data minimization metrics tracking and reporting system.

This module provides detailed metrics and analytics for measuring the effectiveness
of data minimization optimizations in the law execution engine.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class LawExecutionRecord:
    """Record of a single law execution with data minimization metrics"""

    bsn_hash: str  # Hashed BSN for privacy
    law_name: str
    service: str
    timestamp: datetime
    was_eliminated_early: bool
    sensitivity_score: Optional[Tuple[int, float, int]]  # (max, avg, field_count)
    fields_accessed: List[Dict]  # List of {service, field, sensitivity}
    execution_time_ms: float
    data_sources_called: List[str]
    early_elimination_reason: Optional[str]


@dataclass
class SessionMetrics:
    """Metrics for a complete law evaluation session"""

    session_id: str
    bsn_hash: str
    start_time: datetime
    end_time: Optional[datetime]
    total_laws_considered: int
    laws_eliminated_early: int
    laws_executed: int
    max_sensitivity_accessed: int
    total_fields_accessed: int
    unique_services_called: int
    total_execution_time_ms: float
    early_elimination_rate: float
    sensitivity_distribution: Dict[int, int]
    elimination_reasons: Dict[str, int]


class AdvancedDataMinimizationMetrics:
    """Advanced metrics tracking and analytics for data minimization effectiveness"""

    def __init__(self):
        self.reset()
        self.historical_sessions: List[SessionMetrics] = []
        self.law_execution_history: List[LawExecutionRecord] = []

    def reset(self):
        """Reset current session metrics"""
        self.current_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "bsn_hash": None,
            "start_time": datetime.now(),
            "laws_eliminated_early": 0,
            "laws_executed": 0,
            "max_sensitivity_accessed": 0,
            "fields_accessed": [],
            "services_called": set(),
            "elimination_reasons": defaultdict(int),
            "execution_times": [],
            "sensitivity_scores": [],
        }

    def start_session(self, bsn: str):
        """Start a new evaluation session"""
        # Hash BSN for privacy while maintaining uniqueness
        import hashlib

        bsn_hash = hashlib.sha256(bsn.encode()).hexdigest()[:16]

        self.current_session["bsn_hash"] = bsn_hash
        self.current_session["start_time"] = datetime.now()
        logger.info(f"Started data minimization session {self.current_session['session_id']} for BSN hash {bsn_hash}")

    def record_early_elimination(self, law_name: str, reason: str = "age_filter"):
        """Record that a law was eliminated early"""
        self.current_session["laws_eliminated_early"] += 1
        self.current_session["elimination_reasons"][reason] += 1

        # Create execution record
        record = LawExecutionRecord(
            bsn_hash=self.current_session["bsn_hash"],
            law_name=law_name,
            service=law_name.split(".")[0] if "." in law_name else "unknown",
            timestamp=datetime.now(),
            was_eliminated_early=True,
            sensitivity_score=None,
            fields_accessed=[],
            execution_time_ms=0,
            data_sources_called=[],
            early_elimination_reason=reason,
        )
        self.law_execution_history.append(record)

        logger.debug(f"Early elimination: {law_name} (reason: {reason})")

    def record_law_execution(
        self, law_name: str, sensitivity_score: Tuple[int, float, int], execution_time_ms: float = 0
    ):
        """Record execution of a law with its sensitivity metrics"""
        self.current_session["laws_executed"] += 1
        self.current_session["sensitivity_scores"].append(sensitivity_score)
        self.current_session["execution_times"].append(execution_time_ms)

        max_sens, avg_sens, field_count = sensitivity_score
        self.current_session["max_sensitivity_accessed"] = max(
            self.current_session["max_sensitivity_accessed"], max_sens
        )

        # Create execution record
        record = LawExecutionRecord(
            bsn_hash=self.current_session["bsn_hash"],
            law_name=law_name,
            service=law_name.split(".")[0] if "." in law_name else "unknown",
            timestamp=datetime.now(),
            was_eliminated_early=False,
            sensitivity_score=sensitivity_score,
            fields_accessed=self.current_session["fields_accessed"].copy(),
            execution_time_ms=execution_time_ms,
            data_sources_called=list(self.current_session["services_called"]),
            early_elimination_reason=None,
        )
        self.law_execution_history.append(record)

        logger.debug(f"Law executed: {law_name}, sensitivity: max={max_sens}, avg={avg_sens:.2f}")

    def record_field_access(self, service: str, field: str, sensitivity: int):
        """Record access to a specific data field"""
        field_access = {
            "service": service,
            "field": field,
            "sensitivity": sensitivity,
            "timestamp": datetime.now().isoformat(),
        }

        self.current_session["fields_accessed"].append(field_access)
        self.current_session["services_called"].add(service)
        self.current_session["max_sensitivity_accessed"] = max(
            self.current_session["max_sensitivity_accessed"], sensitivity
        )

        logger.debug(f"Field access: {service}.{field} (sensitivity: {sensitivity})")

    def end_session(self) -> SessionMetrics:
        """End current session and return comprehensive metrics"""
        end_time = datetime.now()
        session_duration = (end_time - self.current_session["start_time"]).total_seconds() * 1000

        total_laws = self.current_session["laws_eliminated_early"] + self.current_session["laws_executed"]
        elimination_rate = self.current_session["laws_eliminated_early"] / total_laws * 100 if total_laws > 0 else 0

        # Calculate sensitivity distribution
        sensitivity_dist = defaultdict(int)
        for field_access in self.current_session["fields_accessed"]:
            sensitivity_dist[field_access["sensitivity"]] += 1

        session_metrics = SessionMetrics(
            session_id=self.current_session["session_id"],
            bsn_hash=self.current_session["bsn_hash"],
            start_time=self.current_session["start_time"],
            end_time=end_time,
            total_laws_considered=total_laws,
            laws_eliminated_early=self.current_session["laws_eliminated_early"],
            laws_executed=self.current_session["laws_executed"],
            max_sensitivity_accessed=self.current_session["max_sensitivity_accessed"],
            total_fields_accessed=len(self.current_session["fields_accessed"]),
            unique_services_called=len(self.current_session["services_called"]),
            total_execution_time_ms=session_duration,
            early_elimination_rate=elimination_rate,
            sensitivity_distribution=dict(sensitivity_dist),
            elimination_reasons=dict(self.current_session["elimination_reasons"]),
        )

        self.historical_sessions.append(session_metrics)

        logger.info(
            f"Session completed: {elimination_rate:.1f}% elimination rate, "
            f"max sensitivity: {self.current_session['max_sensitivity_accessed']}"
        )

        return session_metrics

    def get_current_summary(self) -> Dict:
        """Get summary of current session metrics"""
        total_laws = self.current_session["laws_eliminated_early"] + self.current_session["laws_executed"]
        elimination_rate = self.current_session["laws_eliminated_early"] / total_laws * 100 if total_laws > 0 else 0

        avg_sensitivity = 0
        if self.current_session["sensitivity_scores"]:
            avg_sensitivity = sum(score[1] for score in self.current_session["sensitivity_scores"]) / len(
                self.current_session["sensitivity_scores"]
            )

        return {
            "session_id": self.current_session["session_id"],
            "total_laws_considered": total_laws,
            "laws_eliminated_early": self.current_session["laws_eliminated_early"],
            "laws_executed": self.current_session["laws_executed"],
            "early_elimination_rate_percent": round(elimination_rate, 2),
            "max_sensitivity_accessed": self.current_session["max_sensitivity_accessed"],
            "average_sensitivity_score": round(avg_sensitivity, 2),
            "services_called_count": len(self.current_session["services_called"]),
            "services_called": list(self.current_session["services_called"]),
            "total_fields_accessed": len(self.current_session["fields_accessed"]),
            "elimination_reasons": dict(self.current_session["elimination_reasons"]),
            "sensitivity_distribution": self._get_sensitivity_distribution(),
        }

    def get_historical_analysis(self, days_back: int = 30) -> Dict:
        """Get historical analysis of data minimization effectiveness"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_sessions = [session for session in self.historical_sessions if session.start_time >= cutoff_date]

        if not recent_sessions:
            return {"error": "No historical data available"}

        # Aggregate metrics
        total_sessions = len(recent_sessions)
        avg_elimination_rate = sum(s.early_elimination_rate for s in recent_sessions) / total_sessions
        avg_max_sensitivity = sum(s.max_sensitivity_accessed for s in recent_sessions) / total_sessions
        avg_fields_accessed = sum(s.total_fields_accessed for s in recent_sessions) / total_sessions

        # Most common elimination reasons
        all_elimination_reasons = Counter()
        for session in recent_sessions:
            all_elimination_reasons.update(session.elimination_reasons)

        # Service usage patterns
        service_usage = Counter()
        for record in self.law_execution_history:
            if record.timestamp >= cutoff_date:
                service_usage.update(record.data_sources_called)

        return {
            "analysis_period_days": days_back,
            "total_sessions": total_sessions,
            "average_elimination_rate_percent": round(avg_elimination_rate, 2),
            "average_max_sensitivity": round(avg_max_sensitivity, 2),
            "average_fields_accessed": round(avg_fields_accessed, 1),
            "top_elimination_reasons": dict(all_elimination_reasons.most_common(5)),
            "most_used_services": dict(service_usage.most_common(10)),
            "data_minimization_trend": self._calculate_trend(recent_sessions),
            "sessions_by_elimination_rate": self._group_sessions_by_elimination_rate(recent_sessions),
        }

    def get_law_specific_metrics(self, law_name: str = None) -> Dict:
        """Get metrics for specific laws or all laws"""
        law_metrics = defaultdict(
            lambda: {
                "executions": 0,
                "early_eliminations": 0,
                "avg_sensitivity": 0,
                "avg_execution_time": 0,
                "services_used": set(),
            }
        )

        for record in self.law_execution_history:
            if law_name and record.law_name != law_name:
                continue

            metrics = law_metrics[record.law_name]

            if record.was_eliminated_early:
                metrics["early_eliminations"] += 1
            else:
                metrics["executions"] += 1
                if record.sensitivity_score:
                    metrics["avg_sensitivity"] += record.sensitivity_score[1]
                metrics["avg_execution_time"] += record.execution_time_ms
                metrics["services_used"].update(record.data_sources_called)

        # Calculate averages
        for law, metrics in law_metrics.items():
            if metrics["executions"] > 0:
                metrics["avg_sensitivity"] /= metrics["executions"]
                metrics["avg_execution_time"] /= metrics["executions"]
            metrics["services_used"] = list(metrics["services_used"])
            metrics["elimination_rate"] = (
                metrics["early_eliminations"] / (metrics["early_eliminations"] + metrics["executions"]) * 100
                if (metrics["early_eliminations"] + metrics["executions"]) > 0
                else 0
            )

        if law_name:
            return dict(law_metrics.get(law_name, {}))
        else:
            return dict(law_metrics)

    def export_metrics(self, filepath: str, format: str = "json"):
        """Export metrics to file"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "current_session": self.get_current_summary(),
            "historical_sessions": [asdict(session) for session in self.historical_sessions],
            "law_execution_history": [asdict(record) for record in self.law_execution_history],
            "historical_analysis": self.get_historical_analysis(),
            "law_metrics": self.get_law_specific_metrics(),
        }

        if format.lower() == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Data minimization metrics exported to {filepath}")

    def _get_sensitivity_distribution(self) -> Dict[int, int]:
        """Get distribution of field accesses by sensitivity level"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for field_access in self.current_session["fields_accessed"]:
            sensitivity = field_access["sensitivity"]
            if sensitivity in distribution:
                distribution[sensitivity] += 1
        return distribution

    def _calculate_trend(self, sessions: List[SessionMetrics]) -> str:
        """Calculate trend in elimination rate over time"""
        if len(sessions) < 2:
            return "insufficient_data"

        # Sort by time and calculate trend
        sorted_sessions = sorted(sessions, key=lambda x: x.start_time)
        first_half = sorted_sessions[: len(sorted_sessions) // 2]
        second_half = sorted_sessions[len(sorted_sessions) // 2 :]

        avg_first = sum(s.early_elimination_rate for s in first_half) / len(first_half)
        avg_second = sum(s.early_elimination_rate for s in second_half) / len(second_half)

        if avg_second > avg_first + 5:
            return "improving"
        elif avg_second < avg_first - 5:
            return "declining"
        else:
            return "stable"

    def _group_sessions_by_elimination_rate(self, sessions: List[SessionMetrics]) -> Dict:
        """Group sessions by elimination rate ranges"""
        ranges = {"0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0}

        for session in sessions:
            rate = session.early_elimination_rate
            if rate < 25:
                ranges["0-25%"] += 1
            elif rate < 50:
                ranges["25-50%"] += 1
            elif rate < 75:
                ranges["50-75%"] += 1
            else:
                ranges["75-100%"] += 1

        return ranges
