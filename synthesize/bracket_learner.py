"""
Bracket (Staffel) Learner for Law Synthesis

Trains a piecewise-linear lookup table model that assigns benefits based on
income brackets and household type. The benefit at each income boundary is
computed via linear regression within each segment, guaranteeing a smooth,
continuous function with no cliff effects.

The resulting table is simple to read: at each income boundary you see the
exact benefit amount. Between boundaries the amount is linearly interpolated.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from synthesize.data_utils import prepare_synthesis_data


@dataclass
class BracketSegment:
    """One segment of the piecewise-linear staffel."""

    income_lower: float
    income_upper: float
    amount_at_lower: float
    amount_at_upper: float
    household_filter: dict[str, int | float] | None = None

    @property
    def slope(self) -> float:
        width = self.income_upper - self.income_lower
        if width == 0:
            return 0.0
        return (self.amount_at_upper - self.amount_at_lower) / width

    def predict(self, income: float) -> float:
        clamped = max(self.income_lower, min(income, self.income_upper))
        return max(0.0, self.amount_at_lower + self.slope * (clamped - self.income_lower))


@dataclass
class BracketModel:
    """Complete bracket/staffel model."""

    segments: list[BracketSegment]
    household_types: list[dict[str, int | float]]
    income_brackets: list[float]
    child_supplement: float = 0.0
    feature_names: list[str] = field(default_factory=list)
    eligibility_threshold: float = 0.5
    feature_influence: dict[str, float] = field(default_factory=dict)  # grouping key → eta-squared


@dataclass
class BracketLearnerConfig:
    """Configuration for bracket learner."""

    n_brackets: int = 5
    rounding_amount: float = 5.0  # round amounts to nearest €5
    rounding_bracket: float = 1000.0  # round bracket boundaries to nearest €1000
    min_group_size: int = 30  # minimum data points per household group
    max_grouping_keys: int = 4  # max grouping dimensions to prevent combinatorial explosion


class BracketLearner:
    """
    Learn a staffel/bracket model from simulation data.

    For each household type x income bracket, fits a linear regression
    (amount ~ income) and evaluates it at the bracket boundaries. This
    gives a clean, continuous piecewise-linear function.
    """

    HOUSEHOLD_KEYS = ["has_partner", "has_children", "housing_type_rent"]

    def __init__(self, config: BracketLearnerConfig | None = None) -> None:
        self.config = config or BracketLearnerConfig()

    def prepare_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Prepare data, same interface as SynthesisLearner."""
        return prepare_synthesis_data(df)

    def _fit_hinge(self, income: np.ndarray, amount: np.ndarray) -> tuple[float, float, float]:
        """Fit a hinge function: max(0, base - rate * max(0, income - threshold)).

        Tries a grid of candidate thresholds across the full income range
        and picks the best (lowest MAE).
        Returns (base, rate, threshold).
        """
        if len(income) < 5:
            return float(np.mean(amount)), 0.0, 0.0

        # Search thresholds across the full income range (5th to 90th percentile)
        candidates = np.percentile(income, np.arange(5, 91, 5))

        best_mae = float("inf")
        best_params = (float(np.mean(amount)), 0.0, float(np.median(income)))

        for thresh in candidates:
            above = income > thresh
            at_or_below = income <= thresh
            if above.sum() < 3 or at_or_below.sum() < 3:
                continue

            # base = average amount at/below threshold
            base = float(np.mean(amount[at_or_below]))

            # rate via least squares: amount_above ≈ base - rate * (income_above - thresh)
            excess = income[above] - thresh
            decline = base - amount[above]
            rate = float(np.sum(decline * excess) / np.sum(excess**2)) if np.sum(excess**2) > 0 else 0.0
            rate = max(0.0, rate)  # rate must be non-negative

            # Evaluate MAE
            predicted = np.maximum(0.0, base - rate * np.maximum(0.0, income - thresh))
            mae = float(np.mean(np.abs(amount - predicted)))

            if mae < best_mae:
                best_mae = mae
                best_params = (base, rate, thresh)

        return best_params

    def train(self, df: pd.DataFrame, grouping_keys: list[str] | None = None) -> BracketModel:
        """Train bracket model on simulation data.

        Strategy: fit a hinge function (max(0, base - rate * max(0, income - threshold)))
        per household type, then evaluate at bracket boundaries. This captures the
        typical benefit shape (flat then declining) without overfitting per bracket.

        Args:
            df: DataFrame with simulation data.
            grouping_keys: Optional list of column names to use for household grouping.
                If None, falls back to HOUSEHOLD_KEYS filtered by available columns.
        """
        X, y_eligible, y_amount = self.prepare_data(df)

        feature_names = list(X.columns)

        if "income" not in X.columns:
            raise ValueError("Income column required for bracket model")

        income = X["income"]
        quantiles = np.linspace(0, 1, self.config.n_brackets + 1)
        raw_boundaries = np.quantile(income, quantiles)

        # Round boundaries
        boundaries = [round(b / self.config.rounding_bracket) * self.config.rounding_bracket for b in raw_boundaries]
        boundaries = sorted(set(boundaries))
        if len(boundaries) < 2:
            boundaries = [float(income.min()), float(income.max())]

        # Determine household types — select the most impactful grouping keys
        candidate_keys = (
            [k for k in grouping_keys if k in X.columns]
            if grouping_keys is not None
            else [k for k in self.HOUSEHOLD_KEYS if k in X.columns]
        )

        # Rank all keys by how much they affect the benefit amount (eta-squared)
        feature_influence: dict[str, float] = {}
        key_impact = []
        overall_mean = y_amount.mean()
        ss_total = ((y_amount - overall_mean) ** 2).sum()
        for key in candidate_keys:
            group_means = X.groupby(key, observed=True).apply(lambda g: y_amount.loc[g.index].mean())
            ss_between = sum(
                len(y_amount.loc[X[key] == val]) * (mean - overall_mean) ** 2 for val, mean in group_means.items()
            )
            eta_sq = float(ss_between / ss_total) if ss_total > 0 else 0.0
            key_impact.append((key, eta_sq))
            feature_influence[key] = eta_sq
        key_impact.sort(key=lambda x: x[1], reverse=True)

        if len(candidate_keys) > self.config.max_grouping_keys:
            available_keys = [k for k, _ in key_impact[: self.config.max_grouping_keys]]
        else:
            available_keys = candidate_keys

        if available_keys:
            household_groups = X.groupby(available_keys, observed=True)
            household_types_raw = [dict(zip(available_keys, combo)) for combo in household_groups.groups]
            # Filter out groups that are too small
            household_types = []
            for ht in household_types_raw:
                mask = pd.Series(True, index=X.index)
                for key, val in ht.items():
                    mask &= X[key] == val
                if mask.sum() >= self.config.min_group_size:
                    household_types.append(ht)
            if not household_types:
                household_types = [{}]
        else:
            household_types = [{}]

        # Build segments: fit hinge function per household type,
        # then evaluate at bracket boundaries.
        segments = []
        for ht in household_types:
            ht_mask = pd.Series(True, index=X.index)
            for key, val in ht.items():
                ht_mask &= X[key] == val

            ht_income = income[ht_mask].values
            ht_amount = y_amount[ht_mask].values

            if len(ht_income) < 5:
                continue

            # Fit hinge: max(0, base - rate * max(0, income - threshold))
            base, rate, threshold = self._fit_hinge(ht_income, ht_amount)

            # Evaluate at each boundary
            boundary_amounts = []
            for b in boundaries:
                amt = max(0.0, base - rate * max(0.0, b - threshold))
                boundary_amounts.append(self._round_amount(amt))

            # Build segments from boundary amounts
            for i in range(len(boundaries) - 1):
                segments.append(
                    BracketSegment(
                        income_lower=boundaries[i],
                        income_upper=boundaries[i + 1],
                        amount_at_lower=boundary_amounts[i],
                        amount_at_upper=boundary_amounts[i + 1],
                        household_filter=ht if ht else None,
                    )
                )

        # Estimate child supplement
        child_supplement = 0.0
        if "children_count" in X.columns:
            has_kids = X["children_count"] > 0
            if has_kids.sum() > 10:
                avg_with = float(y_amount[has_kids].mean())
                avg_count = float(X.loc[has_kids, "children_count"].mean())
                avg_without = float(y_amount[~has_kids].mean())
                if avg_count > 0:
                    child_supplement = max(0.0, (avg_with - avg_without) / avg_count)
                    child_supplement = self._round_amount(child_supplement)

        return BracketModel(
            segments=segments,
            household_types=household_types,
            income_brackets=boundaries,
            child_supplement=child_supplement,
            feature_names=feature_names,
            feature_influence=feature_influence,
        )

    def _round_amount(self, val: float) -> float:
        return round(val / self.config.rounding_amount) * self.config.rounding_amount

    def predict(self, model: BracketModel, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Predict amounts and eligibility for a DataFrame."""
        predictions = np.zeros(len(X))

        for i in range(len(X)):
            row = X.iloc[i]
            row_income = row.get("income", 0)

            best_amount = 0.0
            for seg in model.segments:
                if seg.household_filter:
                    match = all(row.get(k, -999) == v for k, v in seg.household_filter.items())
                    if not match:
                        continue

                if row_income < seg.income_lower or row_income > seg.income_upper:
                    continue

                best_amount = seg.predict(row_income)
                break

            if model.child_supplement > 0 and "children_count" in X.columns:
                best_amount += model.child_supplement * row.get("children_count", 0)

            predictions[i] = max(0.0, best_amount)

        eligibility = (predictions > model.eligibility_threshold).astype(int)
        return eligibility, predictions

    def evaluate(self, model: BracketModel, df: pd.DataFrame) -> dict:
        """Evaluate model on data, return metrics."""
        X, y_eligible, y_amount = self.prepare_data(df)
        y_elig_pred, y_amt_pred = self.predict(model, X)

        from sklearn.metrics import accuracy_score

        elig_acc = accuracy_score(y_eligible, y_elig_pred)

        eligible_mask = y_eligible == 1
        if eligible_mask.sum() > 0:
            amt_mae = float(np.mean(np.abs(y_amount[eligible_mask] - y_amt_pred[eligible_mask])))
            ss_res = np.sum((y_amount[eligible_mask] - y_amt_pred[eligible_mask]) ** 2)
            ss_tot = np.sum((y_amount[eligible_mask] - y_amount[eligible_mask].mean()) ** 2)
            amt_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0
        else:
            amt_mae = 0.0
            amt_r2 = 1.0

        return {
            "eligibility_accuracy": float(elig_acc),
            "amount_mae": amt_mae,
            "amount_r2": amt_r2,
        }
