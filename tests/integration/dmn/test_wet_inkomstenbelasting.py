"""
Tests for wet_inkomstenbelasting DMN files (Belastingdienst and UWV).

Tests Business Knowledge Models (BKMs) and income calculations.
"""
import pytest
from pathlib import Path


class TestWetInkomstenbelastingBelastingdienst:
    """Tests for Belastingdienst income tax DMN (verzamelinkomen and vermogen)."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(
            dmn_dir / "wet_inkomstenbelasting_belastingdienst.dmn"
        )

    def test_dmn_loads(self):
        """Test DMN file loads successfully."""
        assert self.dmn_spec is not None
        assert "decision_verzamelinkomen" in self.dmn_spec.decisions
        assert "decision_vermogen" in self.dmn_spec.decisions

    def test_verzamelinkomen_all_boxes(self):
        """Test verzamelinkomen calculation with all income boxes."""
        tax_data = {
            'box1_inkomen': 3000000,  # €30,000
            'box2_inkomen': 500000,   # €5,000
            'box3_inkomen': 200000,   # €2,000
        }
        params = {'person': {}, 'tax_data': tax_data}

        result = self.engine.evaluate(
            self.dmn_spec, "decision_verzamelinkomen", params
        )

        # Total should be 30,000 + 5,000 + 2,000 = €37,000
        assert result.output["verzamelinkomen"] == 3700000

    def test_verzamelinkomen_box1_only(self):
        """Test verzamelinkomen with only box 1 income."""
        tax_data = {
            'box1_inkomen': 4000000,  # €40,000
            'box2_inkomen': 0,
            'box3_inkomen': 0,
        }
        params = {'person': {}, 'tax_data': tax_data}

        result = self.engine.evaluate(
            self.dmn_spec, "decision_verzamelinkomen", params
        )

        assert result.output["verzamelinkomen"] == 4000000

    def test_verzamelinkomen_null_values(self):
        """Test verzamelinkomen with null values (should treat as 0)."""
        tax_data = {
            'box1_inkomen': 2500000,
            'box2_inkomen': None,
            'box3_inkomen': None,
        }
        params = {'person': {}, 'tax_data': tax_data}

        result = self.engine.evaluate(
            self.dmn_spec, "decision_verzamelinkomen", params
        )

        assert result.output["verzamelinkomen"] == 2500000

    def test_vermogen_calculation(self):
        """Test vermogen (wealth) retrieval."""
        tax_data = {'vermogen': 10000000}  # €100,000
        params = {'person': {}, 'tax_data': tax_data}

        result = self.engine.evaluate(
            self.dmn_spec, "decision_vermogen", params
        )

        assert result.output["vermogen"] == 10000000

    def test_vermogen_null_defaults_to_zero(self):
        """Test that null vermogen defaults to 0."""
        tax_data = {'vermogen': None}
        params = {'person': {}, 'tax_data': tax_data}

        result = self.engine.evaluate(
            self.dmn_spec, "decision_vermogen", params
        )

        assert result.output["vermogen"] == 0


class TestWetInkomstenbelastingUWV:
    """Tests for UWV income tax DMN (toetsingsinkomen)."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(
            dmn_dir / "wet_inkomstenbelasting_uwv.dmn"
        )
        self.decision_id = "decision_toetsingsinkomen"

    def test_dmn_loads(self):
        """Test DMN file loads successfully."""
        assert self.dmn_spec is not None
        assert self.decision_id in self.dmn_spec.decisions

    def test_toetsingsinkomen_employed(self, test_income_data_employed):
        """Test toetsingsinkomen for employed person."""
        params = {'person': {}, 'income_data': test_income_data_employed}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, params)

        assert result.output["toetsingsinkomen"] == 3500000  # €35,000

    def test_toetsingsinkomen_unemployed(self, test_income_data_unemployed):
        """Test toetsingsinkomen for unemployed person with benefits."""
        params = {'person': {}, 'income_data': test_income_data_unemployed}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, params)

        assert result.output["toetsingsinkomen"] == 1800000  # €18,000

    def test_toetsingsinkomen_retired(self, test_income_data_retired):
        """Test toetsingsinkomen for retired person with pension."""
        params = {'person': {}, 'income_data': test_income_data_retired}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, params)

        assert result.output["toetsingsinkomen"] == 2000000  # €20,000

    def test_toetsingsinkomen_multiple_sources(self):
        """Test toetsingsinkomen with multiple income sources."""
        income_data = {
            'work_income': 2000000,          # €20,000
            'unemployment_benefit': 0,
            'disability_benefit': 500000,    # €5,000
            'pension': 1000000,              # €10,000
            'other_benefits': 300000,        # €3,000
        }
        params = {'person': {}, 'income_data': income_data}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, params)

        # Total: 20,000 + 5,000 + 10,000 + 3,000 = €38,000
        assert result.output["toetsingsinkomen"] == 3800000

    def test_toetsingsinkomen_null_values(self):
        """Test toetsingsinkomen with null values (should treat as 0)."""
        income_data = {
            'work_income': 2500000,
            'unemployment_benefit': None,
            'disability_benefit': None,
            'pension': None,
            'other_benefits': None,
        }
        params = {'person': {}, 'income_data': income_data}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, params)

        assert result.output["toetsingsinkomen"] == 2500000
