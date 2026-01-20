"""
Law Synthesis Learner

Trains interpretable ML models (Decision Tree + Linear Regression) on simulation data
to learn simplified eligibility rules and amount formulas.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier


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
    """A linear formula for amount calculation."""

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
    _eligibility_tree: DecisionTreeClassifier = field(default=None, repr=False)
    _amount_models: dict[int, LinearRegression] = field(default_factory=dict, repr=False)


class SynthesisLearner:
    """
    Learns simplified laws from simulation data.

    Uses Decision Tree for eligibility classification and
    Linear Regression for amount calculation per tree segment.
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
            y_eligible: Combined eligibility target (OR of three toeslagen)
            y_amount: Combined amount target (SUM of three toeslagen)
        """
        X = df.copy()

        # Encode categorical variables
        if "housing_type" in X.columns:
            X["housing_type_rent"] = (X["housing_type"] == "rent").astype(int)
            X = X.drop(columns=["housing_type"])

        # Convert booleans to int
        for col in ["has_partner", "has_children", "is_student"]:
            if col in X.columns:
                X[col] = X[col].astype(int)

        # Handle missing values
        if "youngest_child_age" in X.columns:
            X["youngest_child_age"] = X["youngest_child_age"].fillna(-1)
        if "rent_amount" in X.columns:
            X["rent_amount"] = X["rent_amount"].fillna(0)
        if "children_count" in X.columns:
            X["children_count"] = X["children_count"].fillna(0)

        # Create combined eligibility target (eligible for ANY of the three)
        eligibility_cols = [
            "zorgtoeslag_eligible",
            "huurtoeslag_eligible",
            "kindgebonden_budget_eligible",
        ]
        available_elig = [c for c in eligibility_cols if c in df.columns]
        if available_elig:
            y_eligible = df[available_elig].any(axis=1).astype(int)
        else:
            raise ValueError("No eligibility columns found in data")

        # Create combined amount target (SUM of all three)
        amount_cols = [
            "zorgtoeslag_amount",
            "huurtoeslag_amount",
            "kindgebonden_budget_amount",
        ]
        available_amt = [c for c in amount_cols if c in df.columns]
        if available_amt:
            y_amount = df[available_amt].sum(axis=1)
        else:
            raise ValueError("No amount columns found in data")

        # Select only feature columns (drop target columns)
        target_cols = eligibility_cols + amount_cols
        feature_cols = [c for c in X.columns if c not in target_cols]
        X = X[feature_cols]

        return X, y_eligible, y_amount

    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> LearnedModel:
        """
        Train eligibility and amount models on simulation data.

        Args:
            df: Simulation results DataFrame
            test_size: Fraction of data to hold out for testing

        Returns:
            LearnedModel with extracted rules and formulas
        """
        # Prepare data
        X, y_eligible, y_amount = self.prepare_data(df)

        # Split data
        X_train, X_test, y_elig_train, y_elig_test, y_amt_train, y_amt_test = train_test_split(
            X, y_eligible, y_amount, test_size=test_size, random_state=42, stratify=y_eligible
        )

        # Train eligibility decision tree
        tree = DecisionTreeClassifier(
            max_depth=self.constraints.max_tree_depth,
            min_samples_leaf=self.constraints.min_samples_leaf,
            random_state=42,
        )
        tree.fit(X_train, y_elig_train)

        # Calculate eligibility accuracy
        eligibility_accuracy = tree.score(X_test, y_elig_test)

        # Extract rules from tree
        eligibility_rules = self._extract_rules(tree, list(X.columns))

        # Train linear regression per tree segment (leaf)
        amount_formulas, amount_models = self._train_segmented_regression(tree, X_train, y_amt_train, list(X.columns))

        # Calculate amount metrics on test set
        y_amt_pred = self._predict_amount(tree, amount_models, X_test)
        amount_r2 = 1 - np.sum((y_amt_test - y_amt_pred) ** 2) / np.sum((y_amt_test - y_amt_test.mean()) ** 2)
        amount_mae = np.mean(np.abs(y_amt_test - y_amt_pred))

        return LearnedModel(
            eligibility_rules=eligibility_rules,
            amount_formulas=amount_formulas,
            feature_names=list(X.columns),
            eligibility_accuracy=eligibility_accuracy,
            amount_r2=amount_r2,
            amount_mae=amount_mae,
            _eligibility_tree=tree,
            _amount_models=amount_models,
        )

    def _extract_rules(self, tree: DecisionTreeClassifier, feature_names: list[str]) -> list[ExtractedRule]:
        """Extract human-readable rules from decision tree."""
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

                # Format threshold nicely
                threshold_str = str(int(threshold)) if threshold == int(threshold) else f"{threshold:.2f}"

                # Left branch (<=)
                recurse(tree_.children_left[node], conditions + [f"{feature_name} <= {threshold_str}"])

                # Right branch (>)
                recurse(tree_.children_right[node], conditions + [f"{feature_name} > {threshold_str}"])

        recurse(0, [])
        return rules[: self.constraints.max_rules]

    def _train_segmented_regression(
        self, tree: DecisionTreeClassifier, X: pd.DataFrame, y: pd.Series, feature_names: list[str]
    ) -> tuple[list[LinearFormula], dict[int, LinearRegression]]:
        """Train linear regression models for each decision tree segment."""
        leaf_ids = tree.apply(X)
        unique_leaves = np.unique(leaf_ids)

        formulas = []
        models = {}

        for leaf_id in unique_leaves:
            mask = leaf_ids == leaf_id
            X_segment = X[mask]
            y_segment = y[mask]

            # Skip if too few samples or no positive amounts
            if len(X_segment) < self.constraints.min_samples_leaf:
                continue
            if y_segment.sum() == 0:
                continue

            # Train linear regression
            model = LinearRegression()
            model.fit(X_segment, y_segment)

            # Calculate R² for this segment
            y_pred = model.predict(X_segment)
            ss_res = np.sum((y_segment - y_pred) ** 2)
            ss_tot = np.sum((y_segment - y_segment.mean()) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            # Get conditions for this leaf
            conditions = self._get_leaf_conditions(tree, feature_names, leaf_id)

            # Filter coefficients to only significant ones
            coefficients = {}
            for feat, coef in zip(feature_names, model.coef_):
                if abs(coef) > 0.01:  # Skip negligible coefficients
                    coefficients[feat] = float(coef)

            formulas.append(
                LinearFormula(
                    intercept=float(model.intercept_),
                    coefficients=coefficients,
                    segment_conditions=conditions,
                    r2_score=float(r2),
                    samples=int(len(X_segment)),
                )
            )
            models[leaf_id] = model

        return formulas, models

    def _get_leaf_conditions(
        self, tree: DecisionTreeClassifier, feature_names: list[str], target_leaf: int
    ) -> list[str]:
        """Extract path conditions to reach a specific leaf."""
        tree_ = tree.tree_
        conditions = []

        def find_path(node: int, path: list[str]) -> bool:
            if node == target_leaf:
                conditions.extend(path)
                return True

            if tree_.feature[node] == -2:  # Leaf but not target
                return False

            feature_name = feature_names[tree_.feature[node]]
            threshold = tree_.threshold[node]

            # Format threshold
            threshold_str = str(int(threshold)) if threshold == int(threshold) else f"{threshold:.2f}"

            # Try left branch
            if find_path(tree_.children_left[node], path + [f"{feature_name} <= {threshold_str}"]):
                return True

            # Try right branch
            return find_path(tree_.children_right[node], path + [f"{feature_name} > {threshold_str}"])

        find_path(0, [])
        return conditions

    def _predict_amount(
        self, tree: DecisionTreeClassifier, models: dict[int, LinearRegression], X: pd.DataFrame
    ) -> np.ndarray:
        """Predict amounts using segmented regression models."""
        leaf_ids = tree.apply(X)
        predictions = np.zeros(len(X))

        for leaf_id, model in models.items():
            mask = leaf_ids == leaf_id
            if mask.any():
                predictions[mask] = model.predict(X[mask])

        # Ensure non-negative predictions
        predictions = np.maximum(predictions, 0)
        return predictions

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
