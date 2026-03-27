"""
Parametric Formula Learner for Law Synthesis

Automatically derives a parametric formula structure from YAML law definitions,
then fits parameters via scipy optimization on simulation data.

Citizen mode (benefits, declining with income):
    component = max(0, BASE[partner] - RATE[partner] * max(0, income - THRESHOLD[partner]))

Business mode (costs, increasing with revenue):
    component = BASE + RATE * max(0, revenue - THRESHOLD)

The total is the sum of all components.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from synthesize.data_utils import prepare_synthesis_data


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
    cost_mode: bool = False  # True for business costs (increasing), False for citizen benefits (declining)

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
            if self.cost_mode:
                # Business costs: base=fixed cost, rate=marginal cost/€ revenue, threshold=exempt revenue
                bounds.extend(
                    [
                        (0, 50000),  # base: 0 to €50k fixed cost
                        (0, 0.5),  # rate: 0 to 50% of revenue above threshold
                        (0, 2000000),  # threshold: 0 to €2M revenue
                    ]
                )
            else:
                # Citizen benefits: base=max benefit, rate=phase-out %, threshold=income start
                bounds.extend(
                    [
                        (0, 2000),  # base: 0 to €2000/month
                        (0, 1.0),  # rate: 0 to 100%
                        (0, 100000),  # threshold: 0 to €100k
                    ]
                )
            if c.has_partner_variant:
                if self.cost_mode:
                    bounds.extend([(0, 50000), (0, 0.5), (0, 2000000)])
                else:
                    bounds.extend([(0, 2000), (0, 1.0), (0, 100000)])
        return bounds

    def evaluate(self, params_vec: np.ndarray, primary: np.ndarray, grouping: np.ndarray) -> np.ndarray:
        """Evaluate the formula for arrays of primary variable and grouping variable.

        For citizens: primary=income, grouping=has_partner
        For business: primary=jaaromzet, grouping=zeros (no grouping)
        """
        total = np.zeros_like(primary, dtype=float)
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

            # Select per-person parameters based on grouping
            base = np.where(grouping, base_p, base_s)
            rate = np.where(grouping, rate_p, rate_s)
            thresh = np.where(grouping, thresh_p, thresh_s)

            if self.cost_mode:
                # Business: cost = base + rate * max(0, revenue - threshold)
                component = base + rate * np.maximum(0, primary - thresh)
            else:
                # Citizen: benefit = max(0, base - rate * max(0, income - threshold))
                component = np.maximum(0, base - rate * np.maximum(0, primary - thresh))
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
        return prepare_synthesis_data(df)

    def _detect_primary_feature(self, df: pd.DataFrame) -> tuple[str, bool]:
        """Detect the primary continuous feature and whether this is a cost model.

        Returns:
            (primary_column_name, cost_mode)
        """
        if "income" in df.columns:
            return "income", False
        if "jaaromzet" in df.columns:
            return "jaaromzet", True
        if "vloeroppervlakte" in df.columns:
            return "vloeroppervlakte", True
        return "income", False

    def build_template(self, df: pd.DataFrame, selected_laws: list[str]) -> FormulaTemplate:
        """Build formula template with initial parameter estimates from data."""
        primary_col, cost_mode = self._detect_primary_feature(df)
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

            # Check if partner variant exists in data (only for citizen mode)
            has_partner_col = "has_partner" in df.columns and not cost_mode
            has_partner_variant = False

            if has_partner_col:
                partner_mask = df["has_partner"].astype(bool)
                elig_with = eligible & partner_mask
                elig_without = eligible & ~partner_mask
                has_partner_variant = elig_with.sum() > 5 and elig_without.sum() > 5

            primary = df.get(primary_col, pd.Series(dtype=float))

            if cost_mode:
                base_s, rate_s, thresh_s = self._estimate_cost_params(primary[eligible], amounts[eligible])
                base_p, rate_p, thresh_p = base_s, rate_s, thresh_s
            elif has_partner_variant:
                base_s, rate_s, thresh_s = self._estimate_benefit_params(primary[elig_without], amounts[elig_without])
                base_p, rate_p, thresh_p = self._estimate_benefit_params(primary[elig_with], amounts[elig_with])
            else:
                base_s, rate_s, thresh_s = self._estimate_benefit_params(primary[eligible], amounts[eligible])
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
            if cost_mode:
                components.append(
                    FormulaComponent(
                        name="generic",
                        base_single=500.0,
                        base_partner=500.0,
                        rate_single=0.01,
                        rate_partner=0.01,
                        threshold_single=50000.0,
                        threshold_partner=50000.0,
                        has_partner_variant=False,
                    )
                )
            else:
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

        return FormulaTemplate(components=components, cost_mode=cost_mode)

    def _estimate_benefit_params(self, primary: pd.Series, amounts: pd.Series) -> tuple[float, float, float]:
        """Estimate base, rate, threshold for declining benefit model."""
        if len(primary) < 5:
            return 200.0, 0.05, 20000.0

        # Base: maximum typical amount (90th percentile)
        base = float(np.percentile(amounts[amounts > 0], 90)) if (amounts > 0).sum() > 0 else 200.0

        # Threshold: primary value where benefit starts declining
        high_benefit = amounts > base * 0.8
        threshold = float(primary[high_benefit].max()) if high_benefit.sum() > 0 else float(primary.median())

        # Rate: approximate decline rate above threshold
        above_thresh = primary > threshold
        if above_thresh.sum() > 5:
            avg_primary_above = float(primary[above_thresh].mean())
            avg_amount_above = float(amounts[above_thresh].mean())
            diff = avg_primary_above - threshold
            if diff > 0 and base > avg_amount_above:
                rate = (base - avg_amount_above) / diff
                rate = max(0.001, min(1.0, rate))
            else:
                rate = 0.05
        else:
            rate = 0.05

        return base, rate, threshold

    def _estimate_cost_params(self, primary: pd.Series, amounts: pd.Series) -> tuple[float, float, float]:
        """Estimate base, rate, threshold for increasing cost model."""
        if len(primary) < 5:
            return 500.0, 0.01, 50000.0

        positive = amounts > 0
        if positive.sum() < 3:
            return 0.0, 0.01, 50000.0

        # Base: minimum typical cost (10th percentile of positive amounts)
        base = float(np.percentile(amounts[positive], 10))

        # Threshold: primary value below which cost is roughly constant at base
        low_cost = amounts <= base * 1.2
        threshold = float(primary[low_cost & positive].median()) if (low_cost & positive).sum() > 0 else 0.0

        # Rate: approximate cost increase per unit of primary above threshold
        above_thresh = primary > threshold
        if above_thresh.sum() > 5 and positive.sum() > 5:
            avg_primary_above = float(primary[above_thresh & positive].mean())
            avg_amount_above = float(amounts[above_thresh & positive].mean())
            diff = avg_primary_above - threshold
            if diff > 0 and avg_amount_above > base:
                rate = (avg_amount_above - base) / diff
                rate = max(0.0001, min(0.5, rate))
            else:
                rate = 0.01
        else:
            rate = 0.01

        return base, rate, threshold

    def train(self, df: pd.DataFrame, selected_laws: list[str]) -> ParametricModel:
        """Train parametric model on simulation data.

        Uses differential evolution (global optimizer) to avoid getting stuck
        in local minima where components collapse to zero.
        """
        from scipy.optimize import differential_evolution, minimize

        X, y_eligible, y_amount = self.prepare_data(df)
        feature_names = list(X.columns)

        template = self.build_template(df, selected_laws)
        initial_params = template.to_vector()

        primary_col, _ = self._detect_primary_feature(df)

        # Scale initial bases so their sum ≈ mean total amount for eligible people
        eligible_mask_init = y_eligible == 1
        if eligible_mask_init.sum() > 0:
            mean_total = float(y_amount[eligible_mask_init].mean())
            base_sum = sum(c.base_single for c in template.components)
            if base_sum > 0:
                max_base = 50000.0 if template.cost_mode else 2000.0
                scale = mean_total / base_sum
                for c in template.components:
                    c.base_single = min(c.base_single * scale, max_base)
                    c.base_partner = min(c.base_partner * scale, max_base)
                initial_params = template.to_vector()

        primary = X[primary_col].values if primary_col in X.columns else np.zeros(len(X))
        grouping = (
            X["has_partner"].values if "has_partner" in X.columns and not template.cost_mode else np.zeros(len(X))
        )

        def objective(params):
            predictions = template.evaluate(params, primary, grouping)
            return np.mean(np.abs(y_amount.values - predictions))

        bounds = template.get_bounds()

        # Clamp initial params to bounds
        initial_params = np.clip(
            initial_params,
            [b[0] for b in bounds],
            [b[1] for b in bounds],
        )

        # Phase 1: differential evolution for global search
        de_result = differential_evolution(
            objective,
            bounds=bounds,
            x0=initial_params,
            maxiter=200,
            seed=42,
            tol=1e-4,
            polish=False,
            workers=1,
        )

        # Phase 2: polish with L-BFGS-B from the DE result
        result = minimize(
            objective,
            de_result.x,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-8},
        )

        fitted_params = result.x

        # Round parameters
        rounded_params = self._round_params(fitted_params, template)

        # Evaluate
        predictions = template.evaluate(rounded_params, primary, grouping)
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

        primary_col, _ = self._detect_primary_feature(df)
        primary = X[primary_col].values if primary_col in X.columns else np.zeros(len(X))
        grouping = (
            X["has_partner"].values if "has_partner" in X.columns and not model.template.cost_mode else np.zeros(len(X))
        )

        predictions = model.template.evaluate(model.fitted_params, primary, grouping)
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
