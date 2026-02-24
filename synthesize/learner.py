"""
Law Synthesis Learner

Trains interpretable ML models on simulation data to learn simplified
eligibility rules and amount formulas. Uses a Decision Tree Regressor
on the combined benefit amount as the primary model — this naturally
captures which features drive the amount (age for AOW, income for
toeslagen, etc.) without needing separate eligibility classification.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from synthesize.data_utils import prepare_synthesis_data


@dataclass
class InterpretabilityConstraints:
    """Constraints for model interpretability."""

    max_tree_depth: int = 5  # Max decision tree depth
    min_samples_leaf: int = 50  # Minimum samples per leaf (prevents overfitting)
    max_rules: int = 10  # Maximum number of eligibility rules


@dataclass
class ExtractedRule:
    """A rule extracted from the decision tree."""

    conditions: list[str]
    prediction: str  # "eligible" or "not_eligible"
    samples: int
    confidence: float


@dataclass
class LinearFormula:
    """A linear formula for amount calculation in a tree leaf."""

    intercept: float
    coefficients: dict[str, float]
    segment_conditions: list[str]
    r2_score: float
    samples: int


@dataclass
class LearnedModel:
    """Container for learned eligibility and amount models."""

    eligibility_rules: list[ExtractedRule]
    amount_formulas: list[LinearFormula]
    feature_names: list[str]
    eligibility_accuracy: float
    amount_r2: float
    amount_mae: float
    # Store sklearn models for prediction
    _eligibility_tree: DecisionTreeClassifier | None = field(default=None, repr=False)
    _amount_tree: DecisionTreeRegressor | None = field(default=None, repr=False)


class SynthesisLearner:
    """
    Learns simplified laws from simulation data.

    Uses a Decision Tree Regressor on the combined benefit amount as the
    primary model. The regressor naturally splits on the features that
    matter most for each law (e.g. age > 67 for AOW, income for toeslagen).
    Eligibility is derived from the amount predictions (amount > 0 = eligible).

    A separate Decision Tree Classifier is trained for eligibility rules
    extraction and cross-validation metrics.
    """

    # Feature name mapping from simulation to YAML
    FEATURE_NAME_MAPPING = {
        "age": "AGE",
        "income": "INCOME",
        "net_worth": "NET_WORTH",
        "rent_amount": "RENT_AMOUNT",
        "has_partner": "HAS_PARTNER",
        "has_children": "HAS_CHILDREN",
        "children_count": "CHILDREN_COUNT",
        "youngest_child_age": "YOUNGEST_CHILD_AGE",
        "housing_type_rent": "IS_RENTER",
        "is_student": "IS_STUDENT",
    }

    def __init__(self, constraints: InterpretabilityConstraints | None = None) -> None:
        self.constraints = constraints or InterpretabilityConstraints()

    def prepare_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare simulation data for learning.

        Returns:
            X: Feature matrix
            y_eligible: Combined eligibility target (OR of all selected laws)
            y_amount: Combined amount target (SUM of all selected laws)
        """
        return prepare_synthesis_data(df)

    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> LearnedModel:
        """
        Train eligibility and amount models on simulation data.

        Uses a DecisionTreeRegressor on the amount as primary model.
        This directly optimizes for predicting the benefit amount and
        naturally discovers the right splits (age>67 for AOW, etc.).
        """
        X, y_eligible, y_amount = self.prepare_data(df)

        # Split data
        X_train, X_test, y_elig_train, y_elig_test, y_amt_train, y_amt_test = train_test_split(
            X, y_eligible, y_amount, test_size=test_size, random_state=42, stratify=y_eligible
        )

        # Primary model: Decision Tree Regressor on amount
        amount_tree = DecisionTreeRegressor(
            max_depth=self.constraints.max_tree_depth,
            min_samples_leaf=self.constraints.min_samples_leaf,
            random_state=42,
        )
        amount_tree.fit(X_train, y_amt_train)

        # Calculate amount metrics on test set
        y_amt_pred = np.maximum(0, amount_tree.predict(X_test))
        ss_res = np.sum((y_amt_test - y_amt_pred) ** 2)
        ss_tot = np.sum((y_amt_test - y_amt_test.mean()) ** 2)
        amount_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0
        amount_mae = float(np.mean(np.abs(y_amt_test - y_amt_pred)))

        # Eligibility derived from amount predictions
        y_elig_pred = (y_amt_pred > 0).astype(int)
        eligibility_accuracy = float(np.mean(y_elig_pred == y_elig_test))

        # Also train a classifier for rule extraction and CV metrics
        elig_tree = DecisionTreeClassifier(
            max_depth=self.constraints.max_tree_depth,
            min_samples_leaf=self.constraints.min_samples_leaf,
            random_state=42,
        )
        elig_tree.fit(X_train, y_elig_train)

        # Extract rules from the eligibility tree
        eligibility_rules = self._extract_rules(elig_tree, list(X.columns))

        # Extract amount formulas from the regressor tree leaves
        amount_formulas = self._extract_amount_formulas(amount_tree, X_train, y_amt_train, list(X.columns))

        return LearnedModel(
            eligibility_rules=eligibility_rules,
            amount_formulas=amount_formulas,
            feature_names=list(X.columns),
            eligibility_accuracy=eligibility_accuracy,
            amount_r2=amount_r2,
            amount_mae=amount_mae,
            _eligibility_tree=elig_tree,
            _amount_tree=amount_tree,
        )

    def predict(self, model: LearnedModel, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Predict eligibility and amounts using the amount regressor tree."""
        if model._amount_tree is not None:
            amounts = np.maximum(0, model._amount_tree.predict(X))
            eligibility = (amounts > 0).astype(int)
            return eligibility, amounts
        return np.zeros(len(X), dtype=int), np.zeros(len(X))

    def _extract_rules(self, tree: DecisionTreeClassifier, feature_names: list[str]) -> list[ExtractedRule]:
        """Extract human-readable rules from the eligibility decision tree."""
        rules = []
        tree_ = tree.tree_

        def recurse(node: int, conditions: list[str]) -> None:
            if tree_.feature[node] == -2:  # Leaf node
                value = tree_.value[node]
                total = value[0].sum()
                positive = value[0][1]
                prediction = "eligible" if positive > value[0][0] else "not_eligible"
                samples = int(tree_.n_node_samples[node])

                # Only include rules that lead to "eligible" and have enough samples
                if prediction == "eligible" and samples >= self.constraints.min_samples_leaf:
                    rules.append(
                        ExtractedRule(
                            conditions=conditions.copy(),
                            prediction=prediction,
                            samples=samples,
                            confidence=float(positive / total) if total > 0 else 0,
                        )
                    )
            else:
                feature_name = feature_names[tree_.feature[node]]
                threshold = tree_.threshold[node]
                threshold_str = str(int(threshold)) if threshold == int(threshold) else f"{threshold:.2f}"
                recurse(tree_.children_left[node], conditions + [f"{feature_name} <= {threshold_str}"])
                recurse(tree_.children_right[node], conditions + [f"{feature_name} > {threshold_str}"])

        recurse(0, [])
        return rules[: self.constraints.max_rules]

    def _extract_amount_formulas(
        self, tree: DecisionTreeRegressor, X: pd.DataFrame, y: pd.Series, feature_names: list[str]
    ) -> list[LinearFormula]:
        """Extract amount formulas from the regressor tree.

        Each leaf in the regressor tree predicts a constant amount.
        We extract these as LinearFormula objects with zero coefficients
        (constant prediction) plus the path conditions to reach the leaf.
        """
        leaf_ids = tree.apply(X)
        unique_leaves = np.unique(leaf_ids)
        formulas = []

        for leaf_id in unique_leaves:
            mask = leaf_ids == leaf_id
            y_segment = y[mask]

            if len(y_segment) < self.constraints.min_samples_leaf:
                continue

            mean_amount = float(y_segment.mean())
            if mean_amount <= 0:
                continue

            conditions = self._get_leaf_conditions(tree, feature_names, leaf_id)

            # Regressor leaves predict a constant — R² is 0 within a single leaf
            r2 = 0.0

            formulas.append(
                LinearFormula(
                    intercept=mean_amount,
                    coefficients={},
                    segment_conditions=conditions,
                    r2_score=r2,
                    samples=int(len(y_segment)),
                )
            )

        return formulas

    def _get_leaf_conditions(
        self, tree: DecisionTreeClassifier | DecisionTreeRegressor, feature_names: list[str], target_leaf: int
    ) -> list[str]:
        """Extract path conditions to reach a specific leaf."""
        tree_ = tree.tree_
        conditions: list[str] = []

        def find_path(node: int, path: list[str]) -> bool:
            if node == target_leaf:
                conditions.extend(path)
                return True

            if tree_.feature[node] == -2:  # Leaf but not target
                return False

            feature_name = feature_names[tree_.feature[node]]
            threshold = tree_.threshold[node]
            threshold_str = str(int(threshold)) if threshold == int(threshold) else f"{threshold:.2f}"

            if find_path(tree_.children_left[node], path + [f"{feature_name} <= {threshold_str}"]):
                return True

            return find_path(tree_.children_right[node], path + [f"{feature_name} > {threshold_str}"])

        find_path(0, [])
        return conditions

    def cross_validate(self, df: pd.DataFrame, cv: int = 5) -> dict[str, float]:
        """Perform cross-validation to estimate model performance."""
        X, y_eligible, _ = self.prepare_data(df)

        tree = DecisionTreeClassifier(
            max_depth=self.constraints.max_tree_depth,
            min_samples_leaf=self.constraints.min_samples_leaf,
            random_state=42,
        )

        accuracy_scores = cross_val_score(tree, X, y_eligible, cv=cv, scoring="accuracy")
        f1_scores = cross_val_score(tree, X, y_eligible, cv=cv, scoring="f1")
        recall_scores = cross_val_score(tree, X, y_eligible, cv=cv, scoring="recall")

        return {
            "accuracy_mean": float(accuracy_scores.mean()),
            "accuracy_std": float(accuracy_scores.std()),
            "f1_mean": float(f1_scores.mean()),
            "f1_std": float(f1_scores.std()),
            "recall_mean": float(recall_scores.mean()),
            "recall_std": float(recall_scores.std()),
        }
