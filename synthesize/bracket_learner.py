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
    discretized_features: dict[str, tuple[str, float]] = field(
        default_factory=dict
    )  # derived_col → (source, threshold)
    primary_feature: str = "income"  # X-axis feature for bracket boundaries


@dataclass
class BracketLearnerConfig:
    """Configuration for bracket learner."""

    n_brackets: int = 5
    rounding_amount: float = 5.0  # round amounts to nearest €5
    rounding_bracket: float = 1000.0  # round bracket boundaries to nearest €1000
    min_group_size: int = 30  # minimum data points per household group
    max_grouping_keys: int = 4  # max grouping dimensions to prevent combinatorial explosion
    primary_feature: str = "income"  # X-axis feature for bracket model


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
        """Fit a hinge function, auto-detecting direction.

        For citizen benefits (amount decreases with income):
            max(0, base - rate * max(0, income - threshold))
        For business costs (amount increases with income):
            base + rate * max(0, income - threshold)

        Tries both directions and picks the best (lowest MAE).
        Returns (base, rate, threshold) where negative rate = increasing costs.
        """
        if len(income) < 5:
            return float(np.mean(amount)), 0.0, 0.0

        # Detect direction: positive correlation = costs increase with income
        correlation = float(np.corrcoef(income, amount)[0, 1]) if len(income) > 2 else 0.0

        candidates = np.percentile(income, np.arange(5, 91, 5))

        best_mae = float("inf")
        best_params = (float(np.mean(amount)), 0.0, float(np.median(income)))

        for thresh in candidates:
            above = income > thresh
            at_or_below = income <= thresh
            if above.sum() < 3 or at_or_below.sum() < 3:
                continue

            base = float(np.mean(amount[at_or_below]))
            excess = income[above] - thresh

            if correlation >= 0:
                # Increasing costs: amount ≈ base + rate * (income - thresh)
                increase = amount[above] - base
                rate = float(np.sum(increase * excess) / np.sum(excess**2)) if np.sum(excess**2) > 0 else 0.0
                rate = max(0.0, rate)
                predicted = base + rate * np.maximum(0.0, income - thresh)
            else:
                # Declining benefits: amount ≈ base - rate * (income - thresh)
                decline = base - amount[above]
                rate = float(np.sum(decline * excess) / np.sum(excess**2)) if np.sum(excess**2) > 0 else 0.0
                rate = max(0.0, rate)
                predicted = np.maximum(0.0, base - rate * np.maximum(0.0, income - thresh))

            mae = float(np.mean(np.abs(amount - predicted)))

            if mae < best_mae:
                best_mae = mae
                # Store negative rate for increasing costs so _compute_boundary_amounts works
                best_params = (base, -rate if correlation >= 0 else rate, thresh)

        return best_params

    def _find_best_split(self, values: np.ndarray, amounts: np.ndarray) -> tuple[float, float]:
        """Find the optimal binary split for a continuous feature.

        Tests candidate thresholds and returns the one that maximizes the
        difference in mean benefit amount between the two groups.
        Candidate thresholds include data percentiles plus round numbers
        (multiples of 5) within the data range, so splits land on
        human-readable values like 65, 67, 70 instead of 57.3.

        Returns (threshold, eta_squared).
        """
        # Data-driven candidates from percentiles
        pct_candidates = np.percentile(values, np.arange(10, 91, 10))
        # Round-number candidates within data range; step size depends on range
        vmin, vmax = float(np.min(values)), float(np.max(values))
        value_range = vmax - vmin
        if value_range <= 100:
            step = 1  # e.g. age 18-75: test every integer
        elif value_range <= 1000:
            step = 5  # e.g. moderate ranges
        else:
            step = max(10, round(value_range / 100))  # keep ~100 candidates max
        round_candidates = np.arange(np.ceil(vmin / step) * step, np.floor(vmax / step) * step + 1, step)
        candidates = np.unique(np.concatenate([pct_candidates, round_candidates]))

        best_eta = 0.0
        best_threshold = float(np.median(values))
        overall_mean = float(np.mean(amounts))
        ss_total = float(np.sum((amounts - overall_mean) ** 2))
        if ss_total == 0:
            return best_threshold, 0.0

        for thresh in candidates:
            below = values <= thresh
            above = ~below
            n_below, n_above = int(below.sum()), int(above.sum())
            if n_below < self.config.min_group_size or n_above < self.config.min_group_size:
                continue
            mean_below = float(np.mean(amounts[below]))
            mean_above = float(np.mean(amounts[above]))
            ss_between = n_below * (mean_below - overall_mean) ** 2 + n_above * (mean_above - overall_mean) ** 2
            eta = ss_between / ss_total
            if eta > best_eta:
                best_eta = eta
                best_threshold = float(thresh)

        return best_threshold, best_eta

    def train(
        self,
        df: pd.DataFrame,
        grouping_keys: list[str] | None = None,
        continuous_keys: list[str] | None = None,
    ) -> BracketModel:
        """Train bracket model on simulation data.

        Strategy: fit a hinge function (max(0, base - rate * max(0, income - threshold)))
        per household type, then evaluate at bracket boundaries. This captures the
        typical benefit shape (flat then declining) without overfitting per bracket.

        Args:
            df: DataFrame with simulation data.
            grouping_keys: Optional list of binary/categorical column names for grouping.
                If None, falls back to HOUSEHOLD_KEYS filtered by available columns.
            continuous_keys: Optional list of continuous column names (e.g. age) to
                consider for automatic discretization into grouping keys. The most
                impactful ones are split at their optimal threshold.
        """
        X, y_eligible, y_amount = self.prepare_data(df)

        feature_names = list(X.columns)

        pf = self.config.primary_feature
        if pf not in X.columns:
            raise ValueError(f"Primary feature '{pf}' column required for bracket model")

        primary_values = X[pf]
        quantiles = np.linspace(0, 1, self.config.n_brackets + 1)
        raw_boundaries = np.quantile(primary_values, quantiles)

        # Round boundaries
        boundaries = [round(b / self.config.rounding_bracket) * self.config.rounding_bracket for b in raw_boundaries]
        boundaries = sorted(set(boundaries))
        if len(boundaries) < 2:
            boundaries = [float(primary_values.min()), float(primary_values.max())]

        # Determine household types — select the most impactful grouping keys
        candidate_keys = (
            [k for k in grouping_keys if k in X.columns]
            if grouping_keys is not None
            else [k for k in self.HOUSEHOLD_KEYS if k in X.columns]
        )

        # Auto-discretize impactful continuous features into binary grouping keys
        discretized_info: dict[str, tuple[str, float]] = {}  # derived_col -> (source_col, threshold)
        if continuous_keys:
            for col in continuous_keys:
                if col not in X.columns or col == pf:
                    continue
                threshold, eta_sq = self._find_best_split(X[col].values, y_amount.values)
                if eta_sq <= 0.05:  # only if explains >5% of variance
                    continue
                # Check redundancy: skip if the discretized split is >85% correlated
                # with an existing binary grouping key (e.g. children_count vs has_children)
                candidate_binary = (X[col] > threshold).astype(int)
                is_redundant = False
                for existing_key in candidate_keys:
                    if existing_key in X.columns:
                        agreement = float((candidate_binary == X[existing_key]).mean())
                        if agreement > 0.85:
                            is_redundant = True
                            break
                if is_redundant:
                    continue
                derived_col = f"{col}_above_{int(threshold)}"
                X[derived_col] = candidate_binary
                candidate_keys.append(derived_col)
                discretized_info[derived_col] = (col, threshold)

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
                # Need enough data per bracket for reliable regression
                min_total = max(self.config.min_group_size, 10 * (len(boundaries) - 1))
                if mask.sum() >= min_total:
                    household_types.append(ht)
            if not household_types:
                household_types = [{}]
        else:
            household_types = [{}]

        # Build segments: compute median amount per bracket per household type,
        # then use linear regression within each bracket for smooth interpolation.
        segments = []
        for ht in household_types:
            ht_mask = pd.Series(True, index=X.index)
            for key, val in ht.items():
                ht_mask &= X[key] == val

            ht_income = primary_values[ht_mask].values
            ht_amount = y_amount[ht_mask].values

            if len(ht_income) < 5:
                continue

            # Compute median amount at each boundary by fitting a local linear
            # regression within each bracket and evaluating at its edges.
            boundary_amounts = self._compute_boundary_amounts(ht_income, ht_amount, boundaries)

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
            discretized_features=discretized_info,
            primary_feature=pf,
        )

    def _compute_boundary_amounts(self, income: np.ndarray, amount: np.ndarray, boundaries: list[float]) -> list[float]:
        """Compute the amount at each bracket boundary.

        Uses a hinge function fitted by _fit_hinge. Direction is encoded in rate sign:
        - Positive rate: declining benefits: max(0, base - rate * max(0, x - threshold))
        - Negative rate: increasing costs: base + |rate| * max(0, x - threshold)
        """
        base, rate, threshold = self._fit_hinge(income, amount)
        if rate < 0:
            # Increasing costs
            abs_rate = abs(rate)
            return [self._round_amount(base + abs_rate * max(0.0, b - threshold)) for b in boundaries]
        else:
            # Declining benefits
            return [self._round_amount(max(0.0, base - rate * max(0.0, b - threshold))) for b in boundaries]

    def _round_amount(self, val: float) -> float:
        return round(val / self.config.rounding_amount) * self.config.rounding_amount

    def predict(self, model: BracketModel, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Predict amounts and eligibility for a DataFrame."""
        predictions = np.zeros(len(X))

        for i in range(len(X)):
            row = X.iloc[i]
            row_primary = row.get(model.primary_feature, 0)

            best_amount = 0.0
            for seg in model.segments:
                if seg.household_filter:
                    match = all(row.get(k, -999) == v for k, v in seg.household_filter.items())
                    if not match:
                        continue

                if row_primary < seg.income_lower or row_primary > seg.income_upper:
                    continue

                best_amount = seg.predict(row_primary)
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
