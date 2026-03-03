"""
Shared data preparation utilities for law synthesis learners.

Provides a single prepare_synthesis_data() function used by SynthesisLearner,
BracketLearner, and ParametricLearner to avoid code duplication.
"""

import pandas as pd


def prepare_synthesis_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare simulation data for learning.

    Performs the following transformations:
    1. Encodes housing_type to a binary housing_type_rent column
    2. Encodes childcare_type to binary dummy columns (dagopvang, bso)
    3. Converts boolean columns (has_partner, has_children, is_student) to int
    4. Fills missing values with sensible defaults
    5. Detects eligibility and amount columns dynamically (endswith("_eligible"))
    6. Filters to feature columns only (drops eligibility/amount targets)

    Args:
        df: Simulation results DataFrame with feature and target columns.

    Returns:
        X: Feature matrix (DataFrame)
        y_eligible: Combined eligibility target -- 1 if eligible for ANY law (Series)
        y_amount: Combined amount target -- SUM of all law amounts (Series)

    Raises:
        ValueError: If no eligibility or amount columns are found in the data.
    """
    X = df.copy()

    # Encode categorical variables
    if "housing_type" in X.columns:
        X["housing_type_rent"] = (X["housing_type"] == "rent").astype(int)
        X = X.drop(columns=["housing_type"])

    if "childcare_type" in X.columns:
        X["childcare_type"] = X["childcare_type"].fillna("none")
        X["childcare_type_dagopvang"] = (X["childcare_type"] == "dagopvang").astype(int)
        X["childcare_type_bso"] = (X["childcare_type"] == "bso").astype(int)
        X = X.drop(columns=["childcare_type"])

    # Convert booleans to int
    for col in [
        "has_partner",
        "has_children",
        "is_student",
        "type_bedrijf_horeca",
        "is_onder_curatele",
        "sbi_is_food",
        "bereidt_of_serveert_voedsel",
        "is_woonfunctie",
        "is_geselecteerd_cbs_enquete",
        "rechtsvorm_vereist_jaarrekening",
        "heeft_actief_incident",
        "has_terrace",
    ]:
        if col in X.columns:
            X[col] = X[col].astype(int)

    # Handle missing values -- columns with sensible defaults
    _fillna_defaults: dict[str, int | float] = {
        "youngest_child_age": -1,
        "rent_amount": 0,
        "children_count": 0,
        "business_income": 0,
        "work_hours_per_week": 0,
        "childcare_hours_per_child": 0,
        "childcare_hourly_rate": 0,
    }
    for col, default in _fillna_defaults.items():
        if col in X.columns:
            X[col] = X[col].fillna(default)

    # Detect eligibility columns dynamically
    elig_cols = [c for c in df.columns if c.endswith("_eligible")]
    if not elig_cols:
        raise ValueError("No eligibility columns found in data")

    # Create combined eligibility target (eligible for ANY selected law)
    y_eligible = df[elig_cols].any(axis=1).astype(int)

    # Detect matching amount columns
    amount_cols = [c for c in df.columns if c.endswith("_amount") and c.replace("_amount", "_eligible") in elig_cols]
    if not amount_cols:
        raise ValueError("No amount columns found in data")

    # Create combined amount target (SUM of all selected laws)
    y_amount = df[amount_cols].sum(axis=1)

    # Select only feature columns (drop target columns)
    target_cols = elig_cols + amount_cols
    feature_cols = [c for c in X.columns if c not in target_cols]
    X = X[feature_cols]

    return X, y_eligible, y_amount
