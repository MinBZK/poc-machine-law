"""
Validator for Law Synthesis

Validates synthesized laws against original simulation results
and generates comparison reports.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, precision_score, recall_score

from synthesize.learner import LearnedModel


@dataclass
class ValidationMetrics:
    """Metrics for synthesized law validation."""

    # Overall metrics
    overall_accuracy: float

    # Eligibility classification metrics
    eligibility_accuracy: float
    eligibility_precision: float
    eligibility_recall: float
    eligibility_f1: float

    # Amount regression metrics
    amount_mae: float
    amount_rmse: float
    amount_r2: float

    # Per-group metrics
    group_metrics: dict[str, dict[str, float]]


@dataclass
class ValidationReport:
    """Complete validation report."""

    metrics: ValidationMetrics
    problematic_cases: pd.DataFrame
    recommendations: list[str]
    passed: bool


class SynthesisValidator:
    """
    Validate synthesized law against original outcomes.

    Checks:
    - Overall accuracy >= 95%
    - Eligibility recall >= 98% (don't miss eligible people)
    - Per-group accuracy >= 90% (no discrimination)
    - Amount MAE <= 50 EUR/month
    """

    def __init__(
        self,
        accuracy_threshold: float = 0.95,
        recall_threshold: float = 0.98,
        group_accuracy_threshold: float = 0.90,
        amount_tolerance: float = 50.0,  # EUR per month
    ) -> None:
        self.accuracy_threshold = accuracy_threshold
        self.recall_threshold = recall_threshold
        self.group_accuracy_threshold = group_accuracy_threshold
        self.amount_tolerance = amount_tolerance

    def validate(self, model: LearnedModel, test_df: pd.DataFrame) -> ValidationReport:
        """
        Perform comprehensive validation of synthesized law.

        Args:
            model: Learned model from SynthesisLearner
            test_df: Test data (simulation results not used for training)

        Returns:
            ValidationReport with metrics, problematic cases, and recommendations
        """
        from synthesize.learner import SynthesisLearner

        learner = SynthesisLearner()
        X, y_elig_true, y_amt_true = learner.prepare_data(test_df)

        # Get predictions
        y_elig_pred = model._eligibility_tree.predict(X)
        y_amt_pred = learner._predict_amount(model._eligibility_tree, model._amount_models, X)

        # Calculate metrics
        metrics = self._calculate_metrics(X, y_elig_true, y_elig_pred, y_amt_true, y_amt_pred)

        # Find problematic cases
        problematic = self._find_problematic_cases(test_df, X, y_elig_true, y_elig_pred, y_amt_true, y_amt_pred)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, problematic)

        # Check if validation passed
        passed = self._check_passed(metrics)

        return ValidationReport(metrics=metrics, problematic_cases=problematic, recommendations=recommendations, passed=passed)

    def _calculate_metrics(
        self,
        X: pd.DataFrame,
        y_elig_true: pd.Series,
        y_elig_pred: np.ndarray,
        y_amt_true: pd.Series,
        y_amt_pred: np.ndarray,
    ) -> ValidationMetrics:
        """Calculate all validation metrics."""
        # Eligibility metrics
        elig_accuracy = accuracy_score(y_elig_true, y_elig_pred)
        elig_precision = precision_score(y_elig_true, y_elig_pred, zero_division=0)
        elig_recall = recall_score(y_elig_true, y_elig_pred, zero_division=0)
        elig_f1 = f1_score(y_elig_true, y_elig_pred, zero_division=0)

        # Amount metrics (only for truly eligible)
        true_eligible_mask = y_elig_true == 1
        if true_eligible_mask.any():
            amount_mae = mean_absolute_error(y_amt_true[true_eligible_mask], y_amt_pred[true_eligible_mask])
            amount_mse = np.mean((y_amt_true[true_eligible_mask] - y_amt_pred[true_eligible_mask]) ** 2)
            amount_rmse = np.sqrt(amount_mse)
            ss_res = np.sum((y_amt_true[true_eligible_mask] - y_amt_pred[true_eligible_mask]) ** 2)
            ss_tot = np.sum((y_amt_true[true_eligible_mask] - y_amt_true[true_eligible_mask].mean()) ** 2)
            amount_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
        else:
            amount_mae = 0.0
            amount_rmse = 0.0
            amount_r2 = 1.0

        # Overall accuracy: eligibility correct AND (not eligible OR amount within tolerance)
        correct_eligibility = y_elig_true == y_elig_pred
        amount_within_tolerance = np.abs(y_amt_true - y_amt_pred) <= self.amount_tolerance
        overall_correct = correct_eligibility & ((y_elig_true == 0) | amount_within_tolerance)
        overall_accuracy = overall_correct.mean()

        # Per-group metrics
        group_metrics = self._calculate_group_metrics(X, y_elig_true, y_elig_pred, y_amt_true, y_amt_pred)

        return ValidationMetrics(
            overall_accuracy=overall_accuracy,
            eligibility_accuracy=elig_accuracy,
            eligibility_precision=elig_precision,
            eligibility_recall=elig_recall,
            eligibility_f1=elig_f1,
            amount_mae=amount_mae,
            amount_rmse=amount_rmse,
            amount_r2=amount_r2,
            group_metrics=group_metrics,
        )

    def _calculate_group_metrics(
        self,
        X: pd.DataFrame,
        y_elig_true: pd.Series,
        y_elig_pred: np.ndarray,
        y_amt_true: pd.Series,
        y_amt_pred: np.ndarray,
    ) -> dict[str, dict[str, float]]:
        """Calculate metrics per demographic group."""
        group_metrics = {}

        # Age groups
        if "age" in X.columns:
            age_groups = [("18-30", 18, 30), ("30-50", 30, 50), ("50-67", 50, 67), ("67+", 67, 120)]

            for name, min_age, max_age in age_groups:
                mask = (X["age"] >= min_age) & (X["age"] < max_age)
                if mask.sum() > 0:
                    group_metrics[f"age_{name}"] = {
                        "accuracy": float(accuracy_score(y_elig_true[mask], y_elig_pred[mask])),
                        "count": int(mask.sum()),
                    }

        # Income groups (quartiles)
        if "income" in X.columns:
            try:
                quartiles = pd.qcut(X["income"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
                for q in ["Q1", "Q2", "Q3", "Q4"]:
                    mask = quartiles == q
                    if mask.sum() > 0:
                        group_metrics[f"income_{q}"] = {
                            "accuracy": float(accuracy_score(y_elig_true[mask], y_elig_pred[mask])),
                            "count": int(mask.sum()),
                        }
            except ValueError:
                pass  # Not enough variation for quartiles

        # Partner status
        if "has_partner" in X.columns:
            for has_partner in [0, 1]:
                mask = X["has_partner"] == has_partner
                if mask.sum() > 0:
                    label = "with_partner" if has_partner else "single"
                    group_metrics[label] = {
                        "accuracy": float(accuracy_score(y_elig_true[mask], y_elig_pred[mask])),
                        "count": int(mask.sum()),
                    }

        # Housing type
        if "housing_type_rent" in X.columns:
            for is_renter in [0, 1]:
                mask = X["housing_type_rent"] == is_renter
                if mask.sum() > 0:
                    label = "renters" if is_renter else "owners"
                    group_metrics[label] = {
                        "accuracy": float(accuracy_score(y_elig_true[mask], y_elig_pred[mask])),
                        "count": int(mask.sum()),
                    }

        # Children
        if "has_children" in X.columns:
            for has_children in [0, 1]:
                mask = X["has_children"] == has_children
                if mask.sum() > 0:
                    label = "with_children" if has_children else "no_children"
                    group_metrics[label] = {
                        "accuracy": float(accuracy_score(y_elig_true[mask], y_elig_pred[mask])),
                        "count": int(mask.sum()),
                    }

        return group_metrics

    def _find_problematic_cases(
        self,
        original_df: pd.DataFrame,
        X: pd.DataFrame,
        y_elig_true: pd.Series,
        y_elig_pred: np.ndarray,
        y_amt_true: pd.Series,
        y_amt_pred: np.ndarray,
    ) -> pd.DataFrame:
        """Find cases where synthesis differs significantly from original."""
        # Create results dataframe
        results = X.copy()
        results["true_eligible"] = y_elig_true.values
        results["pred_eligible"] = y_elig_pred
        results["true_amount"] = y_amt_true.values
        results["pred_amount"] = y_amt_pred

        # Calculate differences
        results["eligibility_error"] = results["true_eligible"] != results["pred_eligible"]
        results["amount_diff"] = np.abs(results["true_amount"] - results["pred_amount"])

        # Find problematic cases
        eligibility_mismatch = results["eligibility_error"]
        amount_mismatch = (results["true_eligible"] == 1) & (results["amount_diff"] > self.amount_tolerance)

        problematic = results[eligibility_mismatch | amount_mismatch].copy()
        problematic = problematic.sort_values("amount_diff", ascending=False)

        return problematic.head(100)  # Return top 100

    def _generate_recommendations(self, metrics: ValidationMetrics, problematic: pd.DataFrame) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Overall accuracy
        if metrics.overall_accuracy < self.accuracy_threshold:
            gap = self.accuracy_threshold - metrics.overall_accuracy
            recommendations.append(
                f"Algehele accuraatheid ({metrics.overall_accuracy:.1%}) ligt "
                f"{gap:.1%} onder het doel van {self.accuracy_threshold:.0%}. "
                f"Overweeg meer gedetailleerde regels toe te voegen."
            )

        # Recall
        if metrics.eligibility_recall < self.recall_threshold:
            missed_pct = (1 - metrics.eligibility_recall) * 100
            recommendations.append(
                f"Eligibility recall is {metrics.eligibility_recall:.1%}. "
                f"Dit betekent dat {missed_pct:.1f}% van de rechthebbenden niet wordt herkend. "
                f"Verlaag de drempels om meer mensen te identificeren."
            )

        # Amount MAE
        if metrics.amount_mae > self.amount_tolerance:
            recommendations.append(
                f"Gemiddelde afwijking in bedrag is EUR {metrics.amount_mae:.2f}/maand. "
                f"Dit overschrijdt de tolerantie van EUR {self.amount_tolerance:.2f}. "
                f"Overweeg meer segmentatie per inkomensgroep."
            )

        # Check group-specific issues
        for group_name, group_data in metrics.group_metrics.items():
            if group_data["accuracy"] < self.group_accuracy_threshold:
                recommendations.append(
                    f"Lage accuraatheid ({group_data['accuracy']:.1%}) voor groep '{group_name}' "
                    f"(n={group_data['count']}). Overweeg specifieke regels voor deze groep."
                )

        # Positive message if all good
        if not recommendations:
            recommendations.append("De geharmoniseerde wet voldoet aan alle kwaliteitscriteria.")

        return recommendations

    def _check_passed(self, metrics: ValidationMetrics) -> bool:
        """Check if validation criteria are met."""
        if metrics.overall_accuracy < self.accuracy_threshold:
            return False
        if metrics.eligibility_recall < self.recall_threshold:
            return False
        if metrics.amount_mae > self.amount_tolerance:
            return False

        # Check group accuracy
        for group_data in metrics.group_metrics.values():
            if group_data["accuracy"] < self.group_accuracy_threshold:
                return False

        return True

    def generate_report_markdown(self, report: ValidationReport) -> str:
        """Generate a markdown report from validation results."""
        lines = [
            "# Validatierapport Geharmoniseerde Toeslag",
            "",
            f"**Status**: {'GESLAAGD' if report.passed else 'NIET GESLAAGD'}",
            "",
            "## Metrics Overzicht",
            "",
            "### Eligibility Classificatie",
            f"- Accuraatheid: {report.metrics.eligibility_accuracy:.1%}",
            f"- Precision: {report.metrics.eligibility_precision:.1%}",
            f"- Recall: {report.metrics.eligibility_recall:.1%}",
            f"- F1-score: {report.metrics.eligibility_f1:.1%}",
            "",
            "### Bedrag Regressie",
            f"- Gemiddelde afwijking (MAE): EUR {report.metrics.amount_mae:.2f}/maand",
            f"- RMSE: EUR {report.metrics.amount_rmse:.2f}/maand",
            f"- R²: {report.metrics.amount_r2:.3f}",
            "",
            "### Totaal",
            f"- Algehele accuraatheid: {report.metrics.overall_accuracy:.1%}",
            "",
            "## Per-groep Accuraatheid",
            "",
        ]

        # Group metrics table
        lines.append("| Groep | Accuraatheid | Aantal |")
        lines.append("|-------|-------------|--------|")
        for group_name, group_data in report.metrics.group_metrics.items():
            status = "ok" if group_data["accuracy"] >= self.group_accuracy_threshold else "laag"
            lines.append(f"| {group_name} | {group_data['accuracy']:.1%} ({status}) | {group_data['count']} |")

        lines.extend(
            [
                "",
                "## Aanbevelingen",
                "",
            ]
        )

        for rec in report.recommendations:
            lines.append(f"- {rec}")

        if len(report.problematic_cases) > 0:
            lines.extend(
                [
                    "",
                    "## Problematische Gevallen",
                    "",
                    f"Er zijn {len(report.problematic_cases)} gevallen met significante afwijkingen geïdentificeerd.",
                    "",
                ]
            )

        return "\n".join(lines)
