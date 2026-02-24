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
from sklearn.linear_model import LinearRegression


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


@dataclass
class BracketLearnerConfig:
    """Configuration for bracket learner."""

    n_brackets: int = 5
    rounding_amount: float = 5.0  # round amounts to nearest €5
    rounding_bracket: float = 1000.0  # round bracket boundaries to nearest €1000


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
        X = df.copy()

        if "housing_type" in X.columns:
            X["housing_type_rent"] = (X["housing_type"] == "rent").astype(int)
            X = X.drop(columns=["housing_type"])

        for col in ["has_partner", "has_children", "is_student"]:
            if col in X.columns:
                X[col] = X[col].astype(int)

        if "youngest_child_age" in X.columns:
            X["youngest_child_age"] = X["youngest_child_age"].fillna(-1)
        if "rent_amount" in X.columns:
            X["rent_amount"] = X["rent_amount"].fillna(0)
        if "children_count" in X.columns:
            X["children_count"] = X["children_count"].fillna(0)

        elig_cols = [c for c in df.columns if c.endswith("_eligible")]
        amount_cols = [
            c for c in df.columns if c.endswith("_amount") and c.replace("_amount", "_eligible") in elig_cols
        ]

        if elig_cols:
            y_eligible = df[elig_cols].any(axis=1).astype(int)
        else:
            raise ValueError("No eligibility columns found")

        if amount_cols:
            y_amount = df[amount_cols].sum(axis=1)
        else:
            raise ValueError("No amount columns found")

        target_cols = elig_cols + amount_cols
        feature_cols = [c for c in X.columns if c not in target_cols]
        X = X[feature_cols]

        return X, y_eligible, y_amount

    def train(self, df: pd.DataFrame) -> BracketModel:
        """Train bracket model on simulation data."""
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

        # Determine household types
        available_keys = [k for k in self.HOUSEHOLD_KEYS if k in X.columns]
        if available_keys:
            household_groups = X.groupby(available_keys, observed=True)
            household_types = [dict(zip(available_keys, combo)) for combo in household_groups.groups]
        else:
            household_types = [{}]

        # Build segments: fit linear regression per household type x bracket
        segments = []
        for ht in household_types:
            ht_mask = pd.Series(True, index=X.index)
            for key, val in ht.items():
                ht_mask &= X[key] == val

            for i in range(len(boundaries) - 1):
                lower = boundaries[i]
                upper = boundaries[i + 1]

                bracket_mask = ht_mask & (income >= lower)
                if i < len(boundaries) - 2:
                    bracket_mask &= income < upper
                else:
                    bracket_mask &= income <= upper

                seg_income = income[bracket_mask].values.reshape(-1, 1)
                seg_amount = y_amount[bracket_mask].values

                if len(seg_income) < 3:
                    # Not enough data: use mean or zero
                    mean_amt = float(seg_amount.mean()) if len(seg_amount) > 0 else 0.0
                    mean_amt = self._round_amount(max(0.0, mean_amt))
                    segments.append(
                        BracketSegment(
                            income_lower=lower,
                            income_upper=upper,
                            amount_at_lower=mean_amt,
                            amount_at_upper=mean_amt,
                            household_filter=ht if ht else None,
                        )
                    )
                    continue

                # Fit linear regression: amount = a + b * income
                reg = LinearRegression()
                reg.fit(seg_income, seg_amount)

                amt_lower = self._round_amount(max(0.0, float(reg.predict([[lower]])[0])))
                amt_upper = self._round_amount(max(0.0, float(reg.predict([[upper]])[0])))

                segments.append(
                    BracketSegment(
                        income_lower=lower,
                        income_upper=upper,
                        amount_at_lower=amt_lower,
                        amount_at_upper=amt_upper,
                        household_filter=ht if ht else None,
                    )
                )

        # Ensure continuity: where adjacent segments meet, use the average
        for ht in household_types:
            ht_segs = [s for s in segments if s.household_filter == (ht if ht else None)]
            for j in range(len(ht_segs) - 1):
                # The upper of segment j should equal the lower of segment j+1
                avg = (ht_segs[j].amount_at_upper + ht_segs[j + 1].amount_at_lower) / 2
                avg = self._round_amount(max(0.0, avg))
                ht_segs[j].amount_at_upper = avg
                ht_segs[j + 1].amount_at_lower = avg

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
