"""
Unit tests for the law synthesis module.
"""

import numpy as np
import pandas as pd
import pytest
import yaml

from synthesize.learner import ExtractedRule, InterpretabilityConstraints, LearnedModel, LinearFormula, SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerationConfig, YAMLGenerator


@pytest.fixture
def sample_simulation_data() -> pd.DataFrame:
    """Create sample simulation data for testing."""
    np.random.seed(42)
    n = 200

    data = {
        "age": np.random.randint(18, 80, n),
        "income": np.random.uniform(10000, 80000, n),
        "net_worth": np.random.uniform(0, 100000, n),
        "rent_amount": np.random.uniform(0, 1000, n),
        "has_partner": np.random.choice([True, False], n),
        "has_children": np.random.choice([True, False], n),
        "children_count": np.random.randint(0, 4, n),
        "youngest_child_age": np.random.randint(-1, 18, n),
        "housing_type": np.random.choice(["rent", "owned"], n),
        "is_student": np.random.choice([True, False], n, p=[0.1, 0.9]),
    }

    df = pd.DataFrame(data)

    # Create realistic eligibility based on income
    df["zorgtoeslag_eligible"] = df["income"] < 40000
    df["huurtoeslag_eligible"] = (df["income"] < 35000) & (df["housing_type"] == "rent")
    df["kindgebonden_budget_eligible"] = (df["income"] < 50000) & df["has_children"]

    # Create amounts for eligible people
    df["zorgtoeslag_amount"] = np.where(df["zorgtoeslag_eligible"], 150 - df["income"] * 0.002, 0)
    df["huurtoeslag_amount"] = np.where(df["huurtoeslag_eligible"], 200 - df["income"] * 0.003, 0)
    df["kindgebonden_budget_amount"] = np.where(
        df["kindgebonden_budget_eligible"], 100 * df["children_count"] - df["income"] * 0.001, 0
    )

    # Ensure non-negative amounts
    for col in ["zorgtoeslag_amount", "huurtoeslag_amount", "kindgebonden_budget_amount"]:
        df[col] = df[col].clip(lower=0)

    return df


class TestDataPreparation:
    """Tests for data preparation functionality."""

    def test_prepare_features_encodes_categoricals(self, sample_simulation_data: pd.DataFrame) -> None:
        """housing_type is correctly encoded to housing_type_rent."""
        learner = SynthesisLearner()
        X, _, _ = learner.prepare_data(sample_simulation_data)

        assert "housing_type_rent" in X.columns
        assert "housing_type" not in X.columns
        assert X["housing_type_rent"].isin([0, 1]).all()

    def test_prepare_targets_combines_eligibility(self, sample_simulation_data: pd.DataFrame) -> None:
        """y_eligible = zorgtoeslag OR huurtoeslag OR kindgebonden."""
        learner = SynthesisLearner()
        _, y_eligible, _ = learner.prepare_data(sample_simulation_data)

        expected = (
            sample_simulation_data["zorgtoeslag_eligible"]
            | sample_simulation_data["huurtoeslag_eligible"]
            | sample_simulation_data["kindgebonden_budget_eligible"]
        ).astype(int)

        assert (y_eligible == expected).all()

    def test_prepare_targets_sums_amounts(self, sample_simulation_data: pd.DataFrame) -> None:
        """y_amount = sum of three toeslagen amounts."""
        learner = SynthesisLearner()
        _, _, y_amount = learner.prepare_data(sample_simulation_data)

        expected = (
            sample_simulation_data["zorgtoeslag_amount"]
            + sample_simulation_data["huurtoeslag_amount"]
            + sample_simulation_data["kindgebonden_budget_amount"]
        )

        assert np.allclose(y_amount, expected)

    def test_handles_missing_values(self, sample_simulation_data: pd.DataFrame) -> None:
        """Missing values are handled correctly."""
        df = sample_simulation_data.copy()
        df.loc[0:10, "youngest_child_age"] = np.nan
        df.loc[5:15, "rent_amount"] = np.nan

        learner = SynthesisLearner()
        X, _, _ = learner.prepare_data(df)

        assert not X["youngest_child_age"].isna().any()
        assert not X["rent_amount"].isna().any()


class TestLearner:
    """Tests for the SynthesisLearner."""

    def test_decision_tree_respects_max_depth(self, sample_simulation_data: pd.DataFrame) -> None:
        """Tree depth <= max_depth constraint."""
        constraints = InterpretabilityConstraints(max_tree_depth=3)
        learner = SynthesisLearner(constraints=constraints)

        model = learner.train(sample_simulation_data)

        assert model._eligibility_tree.get_depth() <= 3

    def test_decision_tree_extracts_rules(self, sample_simulation_data: pd.DataFrame) -> None:
        """Rules are correctly extracted from tree."""
        learner = SynthesisLearner()
        model = learner.train(sample_simulation_data)

        assert len(model.eligibility_rules) > 0
        for rule in model.eligibility_rules:
            assert isinstance(rule, ExtractedRule)
            assert len(rule.conditions) > 0
            assert rule.prediction == "eligible"
            assert 0 <= rule.confidence <= 1

    def test_linear_regression_per_segment(self, sample_simulation_data: pd.DataFrame) -> None:
        """Separate formula per decision tree leaf."""
        learner = SynthesisLearner()
        model = learner.train(sample_simulation_data)

        assert len(model.amount_formulas) > 0
        for formula in model.amount_formulas:
            assert isinstance(formula, LinearFormula)
            assert isinstance(formula.intercept, float)
            assert isinstance(formula.coefficients, dict)

    def test_cross_validation(self, sample_simulation_data: pd.DataFrame) -> None:
        """Cross-validation returns expected metrics."""
        learner = SynthesisLearner()
        cv_results = learner.cross_validate(sample_simulation_data, cv=3)

        assert "accuracy_mean" in cv_results
        assert "f1_mean" in cv_results
        assert "recall_mean" in cv_results
        assert 0 <= cv_results["accuracy_mean"] <= 1


class TestYAMLGenerator:
    """Tests for the YAML generator."""

    @pytest.fixture
    def sample_model(self, sample_simulation_data: pd.DataFrame) -> LearnedModel:
        """Create a sample learned model."""
        learner = SynthesisLearner()
        return learner.train(sample_simulation_data)

    def test_generates_valid_requirements(self, sample_model) -> None:
        """Output contains valid requirements with LESS_OR_EQUAL etc."""
        generator = YAMLGenerator()
        spec = generator.generate(sample_model)

        assert "requirements" in spec
        requirements = spec["requirements"]

        # Check structure
        if requirements:
            # Should have operations like LESS_OR_EQUAL, GREATER_THAN, etc.
            yaml_str = yaml.dump(requirements)
            assert any(
                op in yaml_str for op in ["LESS_OR_EQUAL", "GREATER_THAN", "GREATER_OR_EQUAL", "LESS_THAN", "EQUALS"]
            )

    def test_generates_valid_actions(self, sample_model) -> None:
        """Output contains valid actions with ADD, MULTIPLY etc."""
        generator = YAMLGenerator()
        spec = generator.generate(sample_model)

        assert "actions" in spec
        actions = spec["actions"]
        assert len(actions) >= 2  # At least is_eligible and toeslag_bedrag

        # Check for is_eligible action
        has_eligible_action = any(a.get("output") == "is_eligible" for a in actions)
        assert has_eligible_action

        # Check for amount action
        has_amount_action = any(a.get("output") == "toeslag_bedrag" for a in actions)
        assert has_amount_action

    def test_yaml_is_parseable(self, sample_model) -> None:
        """Generated YAML can be parsed."""
        generator = YAMLGenerator()
        spec = generator.generate(sample_model)
        yaml_str = generator.to_yaml_string(spec)

        # Should not raise
        parsed = yaml.safe_load(yaml_str)

        assert parsed is not None
        assert "uuid" in parsed
        assert "name" in parsed
        assert "requirements" in parsed
        assert "actions" in parsed

    def test_yaml_has_correct_structure(self, sample_model) -> None:
        """Generated YAML has all required fields."""
        generator = YAMLGenerator()
        spec = generator.generate(sample_model)

        required_fields = [
            "$id",
            "uuid",
            "name",
            "law",
            "law_type",
            "legal_character",
            "decision_type",
            "discoverable",
            "valid_from",
            "service",
            "description",
            "properties",
            "requirements",
            "actions",
        ]

        for field in required_fields:
            assert field in spec, f"Missing required field: {field}"

    def test_custom_config(self, sample_model) -> None:
        """Custom configuration is applied."""
        config = YAMLGenerationConfig(
            service_name="TEST_SERVICE",
            law_name="test_law",
            law_display_name="Test Law",
        )
        generator = YAMLGenerator(config=config)
        spec = generator.generate(sample_model)

        assert spec["service"] == "TEST_SERVICE"
        assert spec["law"] == "test_law"
        assert spec["name"] == "Test Law"


class TestValidator:
    """Tests for the SynthesisValidator."""

    @pytest.fixture
    def trained_model(self, sample_simulation_data: pd.DataFrame) -> LearnedModel:
        """Create a trained model for validation."""
        learner = SynthesisLearner()
        return learner.train(sample_simulation_data)

    def test_calculates_accuracy(self, trained_model, sample_simulation_data: pd.DataFrame) -> None:
        """Accuracy is correctly calculated."""
        validator = SynthesisValidator()
        report = validator.validate(trained_model, sample_simulation_data)

        assert 0 <= report.metrics.eligibility_accuracy <= 1
        assert 0 <= report.metrics.overall_accuracy <= 1

    def test_calculates_per_group_metrics(self, trained_model, sample_simulation_data: pd.DataFrame) -> None:
        """Metrics per age group, income group etc. are calculated."""
        validator = SynthesisValidator()
        report = validator.validate(trained_model, sample_simulation_data)

        group_metrics = report.metrics.group_metrics
        assert len(group_metrics) > 0

        # Should have age groups
        assert any("age" in k for k in group_metrics)

    def test_identifies_problematic_cases(self, trained_model, sample_simulation_data: pd.DataFrame) -> None:
        """Cases with large deviations are identified."""
        validator = SynthesisValidator()
        report = validator.validate(trained_model, sample_simulation_data)

        # Problematic cases should be a DataFrame
        assert isinstance(report.problematic_cases, pd.DataFrame)

    def test_generates_recommendations(self, trained_model, sample_simulation_data: pd.DataFrame) -> None:
        """Recommendations are generated based on validation results."""
        validator = SynthesisValidator()
        report = validator.validate(trained_model, sample_simulation_data)

        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0

    def test_markdown_report_generation(self, trained_model, sample_simulation_data: pd.DataFrame) -> None:
        """Markdown report is generated correctly."""
        validator = SynthesisValidator()
        report = validator.validate(trained_model, sample_simulation_data)
        markdown = validator.generate_report_markdown(report)

        assert "# Validatierapport" in markdown
        assert "Eligibility Classificatie" in markdown
        assert "Bedrag Regressie" in markdown


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self, sample_simulation_data: pd.DataFrame) -> None:
        """
        End-to-end test:
        1. Train model on simulation data
        2. Generate YAML
        3. Validate against same data
        4. Check accuracy >= 90% (lower threshold for test data)
        """
        # Train
        learner = SynthesisLearner()
        model = learner.train(sample_simulation_data)

        # Generate YAML
        generator = YAMLGenerator()
        spec = generator.generate(model)
        yaml_str = generator.to_yaml_string(spec)

        # Validate YAML is parseable
        parsed = yaml.safe_load(yaml_str)
        assert parsed is not None

        # Validate model performance
        validator = SynthesisValidator(
            accuracy_threshold=0.80,  # Lower for test
            recall_threshold=0.80,
            amount_tolerance=100.0,
        )
        report = validator.validate(model, sample_simulation_data)

        # Should have reasonable accuracy on training data
        assert report.metrics.eligibility_accuracy >= 0.80
