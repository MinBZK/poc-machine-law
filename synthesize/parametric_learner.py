"""
Parametric Formula Learner for Law Synthesis

Automatically derives a parametric formula structure from YAML law definitions,
then fits parameters via scipy optimization on simulation data.

Each law-component follows the pattern:
    component = max(0, BASE[partner] - RATE[partner] * max(0, income - THRESHOLD[partner]))

The total benefit is the sum of all components.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class FormulaComponent:
    """One component of the parametric formula (one source law)."""

    name: str
    base_single: float
    base_partner: float
    rate_single: float
    rate_partner: float
    threshold_single: float
    threshold_partner: float
    has_partner_variant: bool = True


@dataclass
class FormulaTemplate:
    """Template for the full parametric formula."""

    components: list[FormulaComponent]

    def param_count(self) -> int:
        """Number of fittable parameters."""
        count = 0
        for c in self.components:
            if c.has_partner_variant:
                count += 6  # base_s, base_p, rate_s, rate_p, thresh_s, thresh_p
            else:
                count += 3  # base, rate, threshold
        return count

    def to_vector(self) -> np.ndarray:
        """Convert all parameters to a flat vector."""
        params = []
        for c in self.components:
            params.extend([c.base_single, c.rate_single, c.threshold_single])
            if c.has_partner_variant:
                params.extend([c.base_partner, c.rate_partner, c.threshold_partner])
        return np.array(params)

    def from_vector(self, vec: np.ndarray) -> None:
        """Update components from flat vector."""
        idx = 0
        for c in self.components:
            c.base_single = vec[idx]
            c.rate_single = vec[idx + 1]
            c.threshold_single = vec[idx + 2]
            idx += 3
            if c.has_partner_variant:
                c.base_partner = vec[idx]
                c.rate_partner = vec[idx + 1]
                c.threshold_partner = vec[idx + 2]
                idx += 3

    def get_bounds(self) -> list[tuple[float, float]]:
        """Get optimization bounds for each parameter."""
        bounds = []
        for c in self.components:
            # base_single, rate_single, threshold_single
            bounds.extend(
                [
                    (0, 2000),  # base: 0 to €2000/month
                    (0, 1.0),  # rate: 0 to 100%
                    (0, 100000),  # threshold: 0 to €100k
                ]
            )
            if c.has_partner_variant:
                bounds.extend(
                    [
                        (0, 2000),
                        (0, 1.0),
                        (0, 100000),
                    ]
                )
        return bounds

    def evaluate(self, params_vec: np.ndarray, income: np.ndarray, has_partner: np.ndarray) -> np.ndarray:
        """Evaluate the formula for arrays of income and partner status."""
        total = np.zeros_like(income, dtype=float)
        idx = 0
        for c in self.components:
            base_s = params_vec[idx]
            rate_s = params_vec[idx + 1]
            thresh_s = params_vec[idx + 2]
            idx += 3

            if c.has_partner_variant:
                base_p = params_vec[idx]
                rate_p = params_vec[idx + 1]
                thresh_p = params_vec[idx + 2]
                idx += 3
            else:
                base_p = base_s
                rate_p = rate_s
                thresh_p = thresh_s

            # Select per-person parameters based on partner status
            base = np.where(has_partner, base_p, base_s)
            rate = np.where(has_partner, rate_p, rate_s)
            thresh = np.where(has_partner, thresh_p, thresh_s)

            component = np.maximum(0, base - rate * np.maximum(0, income - thresh))
            total += component

        return np.maximum(0, total)


@dataclass
class ParametricModel:
    """Fitted parametric model."""

    template: FormulaTemplate
    fitted_params: np.ndarray
    initial_params: np.ndarray
    metrics: dict = field(default_factory=dict)
    feature_names: list[str] = field(default_factory=list)


@dataclass
class ParametricConstraints:
    """Configuration for parametric learner."""

    rounding_base: float = 10.0  # round base amounts to €10
    rounding_rate: float = 0.005  # round rates to 0.5%
    rounding_threshold: float = 100.0  # round thresholds to €100


class ParametricLearner:
    """
    Learn parametric formula from simulation data.

    Steps:
    1. Build formula template (one component per source law)
    2. Initialize parameters from data statistics
    3. Optimize via scipy.optimize.minimize
    4. Round to human-friendly values
    5. Re-validate after rounding
    """

    def __init__(self, constraints: ParametricConstraints | None = None) -> None:
        self.constraints = constraints or ParametricConstraints()

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

    def build_template(self, df: pd.DataFrame, selected_laws: list[str]) -> FormulaTemplate:
        """Build formula template with initial parameter estimates from data."""
        components = []

        for law_name in selected_laws:
            elig_col = f"{law_name}_eligible"
            amt_col = f"{law_name}_amount"

            if elig_col not in df.columns or amt_col not in df.columns:
                continue

            eligible = df[elig_col].astype(bool)
            amounts = df[amt_col]

            if eligible.sum() == 0:
                continue

            # Check if partner variant exists in data
            has_partner_col = "has_partner" in df.columns
            has_partner_variant = False

            if has_partner_col:
                partner_mask = df["has_partner"].astype(bool)
                elig_with = eligible & partner_mask
                elig_without = eligible & ~partner_mask
                has_partner_variant = elig_with.sum() > 5 and elig_without.sum() > 5

            income = df.get("income", pd.Series(dtype=float))

            if has_partner_variant:
                base_s, rate_s, thresh_s = self._estimate_params(income[elig_without], amounts[elig_without])
                base_p, rate_p, thresh_p = self._estimate_params(income[elig_with], amounts[elig_with])
            else:
                base_s, rate_s, thresh_s = self._estimate_params(income[eligible], amounts[eligible])
                base_p, rate_p, thresh_p = base_s, rate_s, thresh_s

            components.append(
                FormulaComponent(
                    name=law_name,
                    base_single=base_s,
                    base_partner=base_p,
                    rate_single=rate_s,
                    rate_partner=rate_p,
                    threshold_single=thresh_s,
                    threshold_partner=thresh_p,
                    has_partner_variant=has_partner_variant,
                )
            )

        if not components:
            # Fallback: single generic component
            components.append(
                FormulaComponent(
                    name="generic",
                    base_single=200.0,
                    base_partner=150.0,
                    rate_single=0.05,
                    rate_partner=0.05,
                    threshold_single=20000.0,
                    threshold_partner=25000.0,
                )
            )

        return FormulaTemplate(components=components)

    def _estimate_params(self, income: pd.Series, amounts: pd.Series) -> tuple[float, float, float]:
        """Estimate base, rate, threshold from income-amount data."""
        if len(income) < 5:
            return 200.0, 0.05, 20000.0

        # Base: maximum typical amount (90th percentile)
        base = float(np.percentile(amounts[amounts > 0], 90)) if (amounts > 0).sum() > 0 else 200.0

        # Threshold: income where benefit starts declining
        # Approximate: income at which amount drops below 80% of base
        high_benefit = amounts > base * 0.8
        threshold = float(income[high_benefit].max()) if high_benefit.sum() > 0 else float(income.median())

        # Rate: approximate decline rate above threshold
        above_thresh = income > threshold
        if above_thresh.sum() > 5:
            avg_income_above = float(income[above_thresh].mean())
            avg_amount_above = float(amounts[above_thresh].mean())
            income_diff = avg_income_above - threshold
            if income_diff > 0 and base > avg_amount_above:
                rate = (base - avg_amount_above) / income_diff
                rate = max(0.001, min(1.0, rate))
            else:
                rate = 0.05
        else:
            rate = 0.05

        return base, rate, threshold

    def train(self, df: pd.DataFrame, selected_laws: list[str]) -> ParametricModel:
        """Train parametric model on simulation data."""
        from scipy.optimize import minimize

        X, y_eligible, y_amount = self.prepare_data(df)
        feature_names = list(X.columns)

        template = self.build_template(df, selected_laws)
        initial_params = template.to_vector()

        income = X["income"].values if "income" in X.columns else np.zeros(len(X))
        has_partner = X["has_partner"].values if "has_partner" in X.columns else np.zeros(len(X))

        # Objective: minimize MAE
        def objective(params):
            predictions = template.evaluate(params, income, has_partner)
            return np.mean(np.abs(y_amount.values - predictions))

        bounds = template.get_bounds()

        result = minimize(
            objective,
            initial_params,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-6},
        )

        fitted_params = result.x

        # Round parameters
        rounded_params = self._round_params(fitted_params, template)

        # Evaluate
        predictions = template.evaluate(rounded_params, income, has_partner)
        y_elig_pred = (predictions > 0.5).astype(int)

        from sklearn.metrics import accuracy_score

        elig_acc = float(accuracy_score(y_eligible, y_elig_pred))

        eligible_mask = y_eligible == 1
        if eligible_mask.sum() > 0:
            amt_mae = float(np.mean(np.abs(y_amount[eligible_mask] - predictions[eligible_mask])))
            ss_res = np.sum((y_amount.values[eligible_mask] - predictions[eligible_mask]) ** 2)
            ss_tot = np.sum((y_amount.values[eligible_mask] - y_amount.values[eligible_mask].mean()) ** 2)
            amt_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0
        else:
            amt_mae = 0.0
            amt_r2 = 1.0

        # Update template with rounded params
        template.from_vector(rounded_params)

        return ParametricModel(
            template=template,
            fitted_params=rounded_params,
            initial_params=initial_params,
            metrics={
                "eligibility_accuracy": elig_acc,
                "amount_mae": amt_mae,
                "amount_r2": amt_r2,
                "optimization_mae": float(result.fun),
                "optimization_success": bool(result.success),
            },
            feature_names=feature_names,
        )

    def _round_params(self, params: np.ndarray, template: FormulaTemplate) -> np.ndarray:
        """Round parameters to human-friendly values."""
        rounded = params.copy()
        idx = 0
        for c in template.components:
            for _ in range(1 if not c.has_partner_variant else 2):
                # base
                rounded[idx] = round(rounded[idx] / self.constraints.rounding_base) * self.constraints.rounding_base
                # rate
                rounded[idx + 1] = (
                    round(rounded[idx + 1] / self.constraints.rounding_rate) * self.constraints.rounding_rate
                )
                # threshold
                rounded[idx + 2] = (
                    round(rounded[idx + 2] / self.constraints.rounding_threshold) * self.constraints.rounding_threshold
                )
                idx += 3
        return rounded

    def evaluate(self, model: ParametricModel, df: pd.DataFrame) -> dict:
        """Evaluate model on data."""
        X, y_eligible, y_amount = self.prepare_data(df)

        income = X["income"].values if "income" in X.columns else np.zeros(len(X))
        has_partner = X["has_partner"].values if "has_partner" in X.columns else np.zeros(len(X))

        predictions = model.template.evaluate(model.fitted_params, income, has_partner)
        y_elig_pred = (predictions > 0.5).astype(int)

        from sklearn.metrics import accuracy_score

        elig_acc = float(accuracy_score(y_eligible, y_elig_pred))

        eligible_mask = y_eligible == 1
        if eligible_mask.sum() > 0:
            amt_mae = float(np.mean(np.abs(y_amount[eligible_mask] - predictions[eligible_mask])))
            ss_res = np.sum((y_amount.values[eligible_mask] - predictions[eligible_mask]) ** 2)
            ss_tot = np.sum((y_amount.values[eligible_mask] - y_amount.values[eligible_mask].mean()) ** 2)
            amt_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0
        else:
            amt_mae = 0.0
            amt_r2 = 1.0

        return {
            "eligibility_accuracy": elig_acc,
            "amount_mae": amt_mae,
            "amount_r2": amt_r2,
        }
