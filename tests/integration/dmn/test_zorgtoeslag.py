"""
Tests for zorgtoeslag_toeslagen_2025.dmn

Tests the main zorgtoeslag law with cross-DMN references.
"""
import pytest
from pathlib import Path
from datetime import date
from typing import Any


def format_trace(path_node: Any, indent: int = 0, show_details: bool = True) -> str:
    """
    Format a PathNode trace tree into a readable string.

    Args:
        path_node: The PathNode to format
        indent: Current indentation level
        show_details: Whether to show detailed node information

    Returns:
        Formatted trace string
    """
    if path_node is None:
        return ""

    lines = []
    prefix = "  " * indent

    # Format current node
    node_type = getattr(path_node, 'type', 'unknown')
    node_name = getattr(path_node, 'name', 'unnamed')
    node_result = getattr(path_node, 'result', None)
    node_details = getattr(path_node, 'details', {})

    # Create node description with more structure (using ASCII characters)
    if node_type == "dmn_evaluation":
        lines.append(f"{prefix}[DMN EVALUATION] {node_name}")
        if show_details and node_details:
            for key, value in node_details.items():
                lines.append(f"{prefix}  {key}: {value}")
    elif node_type == "decision":
        decision_id = node_details.get('decision_id', 'unknown')
        lines.append(f"{prefix}+ [DECISION] {node_name}")
        lines.append(f"{prefix}|   ID: {decision_id}")
        if node_result is not None:
            # Format result nicely
            if isinstance(node_result, dict):
                lines.append(f"{prefix}|   Result:")
                for key, value in node_result.items():
                    lines.append(f"{prefix}|     {key}: {value}")
            else:
                lines.append(f"{prefix}|   Result: {node_result}")
    else:
        lines.append(f"{prefix}+ [{node_type.upper()}] {node_name}")
        if node_result is not None:
            lines.append(f"{prefix}|   Result: {node_result}")
        if show_details and node_details:
            for key, value in node_details.items():
                lines.append(f"{prefix}|   {key}: {value}")

    # Format children recursively
    children = getattr(path_node, 'children', [])
    if children:
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            child_lines = format_trace(child, indent + 1, show_details)
            if child_lines:
                lines.append(child_lines)

    return "\n".join(lines)


class TestZorgtoeslag:
    """Test suite for Zorgtoeslag 2025 DMN."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(
            dmn_dir / "zorgtoeslag_toeslagen_2025.dmn"
        )

    def _print_trace(self, test_name, parameters, result):
        """Print execution trace for a test."""
        print("\n" + "="*80)
        print(f"DMN EXECUTION TRACE: {test_name}")
        print("="*80)
        print("\nINPUT PARAMETERS:")
        for key, value in parameters.items():
            print(f"  {key}: {value}")
        print("\nEXECUTION PATH:")
        trace_output = format_trace(result.path)
        print(trace_output)
        print("\nFINAL OUTPUT:")
        for key, value in result.output.items():
            print(f"  {key}: {value}")
        if result.errors:
            print("\nERRORS:")
            for error in result.errors:
                print(f"  - {error}")
        print("="*80 + "\n")

    def test_dmn_loads(self):
        """Test that the DMN file loads successfully."""
        assert self.dmn_spec is not None
        assert self.dmn_spec.name == "Zorgtoeslag 2025 (Toeslagen)"
        assert len(self.dmn_spec.imports) == 5  # Should have 5 imports

    def test_eligible_single_low_income(
        self,
        test_person_single,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test eligible single person with low income."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        self._print_trace("test_eligible_single_low_income", parameters, result)
        assert result.output["is_verzekerde_zorgtoeslag"] is True

    def test_ineligible_too_young(
        self,
        test_person_young,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test person under 18 is not eligible."""
        parameters = {
            'person': test_person_young,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        self._print_trace("test_ineligible_too_young", parameters, result)
        assert result.output["is_verzekerde_zorgtoeslag"] is False

    def test_ineligible_not_insured(
        self,
        test_person_not_insured,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test person without insurance is not eligible."""
        parameters = {
            'person': test_person_not_insured,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        self._print_trace("test_ineligible_not_insured", parameters, result)
        assert result.output["is_verzekerde_zorgtoeslag"] is False

    def test_benefit_calculation_single(
        self,
        test_person_single,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test benefit amount calculation for single person."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        self._print_trace("test_benefit_calculation_single", parameters, result)
        # Should get some benefit
        assert result.output["hoogte_toeslag"] > 0

    def test_no_benefit_high_income(
        self,
        test_person_single,
        reference_date,
        test_tax_data_high_income,
        test_income_data_high_income
    ):
        """Test no benefit for high income."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_high_income,
            'income_data': test_income_data_high_income,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        self._print_trace("test_no_benefit_high_income", parameters, result)
        assert result.output["hoogte_toeslag"] == 0

    def test_no_benefit_high_wealth(
        self,
        test_person_single,
        reference_date,
        test_tax_data_high_wealth,
        test_income_data_employed
    ):
        """Test no benefit for high wealth."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_high_wealth,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        self._print_trace("test_no_benefit_high_wealth", parameters, result)
        assert result.output["hoogte_toeslag"] == 0
