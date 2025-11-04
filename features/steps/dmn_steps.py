"""
Step definitions for DMN-based testing.

These steps allow Behave features to test DMN decision models directly.
"""
from behave import given, when, then
from pathlib import Path
from datetime import datetime
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


@given('the DMN engine is initialized')
def step_init_dmn_engine(context):
    """Initialize the DMN engine and DMN parameters context."""
    from machine.dmn import DMNEngine

    context.dmn_engine = DMNEngine()
    context.dmn_dir = Path("dmn")
    context.dmn_parameters = {}


@given('DMN person data')
def step_set_dmn_person_data(context):
    """Set person data for DMN from table."""
    for row in context.table:
        birth_date = datetime.strptime(row['birth_date'], "%Y-%m-%d").date()
        context.dmn_parameters['person'] = {
            'birth_date': birth_date,
            'partnership_status': row['partnership_status'],
            'health_insurance_status': row['health_insurance_status'],
            'is_resident': row['is_resident'].lower() == 'true',
        }


@given('DMN tax data')
def step_set_dmn_tax_data(context):
    """Set tax data for DMN from table."""
    for row in context.table:
        context.dmn_parameters['tax_data'] = {
            'box1_inkomen': int(row['box1_inkomen']),
            'box2_inkomen': int(row['box2_inkomen']),
            'box3_inkomen': int(row['box3_inkomen']),
            'vermogen': int(row['vermogen']),
        }


@given('DMN income data')
def step_set_dmn_income_data(context):
    """Set income data for DMN from table."""
    for row in context.table:
        context.dmn_parameters['income_data'] = {
            'work_income': int(row['work_income']),
            'unemployment_benefit': int(row['unemployment_benefit']),
            'disability_benefit': int(row['disability_benefit']),
            'pension': int(row['pension']),
            'other_benefits': int(row['other_benefits']),
        }


@given('DMN reference date is "{date_str}"')
def step_set_dmn_reference_date(context, date_str):
    """Set reference date for DMN."""
    context.dmn_parameters['reference_date'] = datetime.strptime(date_str, "%Y-%m-%d").date()


@when('the DMN zorgtoeslag decision is evaluated')
def step_evaluate_dmn_zorgtoeslag(context):
    """Evaluate the DMN zorgtoeslag decision."""
    # Load the DMN spec
    dmn_spec = context.dmn_engine.load_dmn(context.dmn_dir / "zorgtoeslag_toeslagen_2025.dmn")

    # Set default partner_income_data if not provided
    if 'partner_income_data' not in context.dmn_parameters:
        context.dmn_parameters['partner_income_data'] = None

    # Evaluate the eligibility decision
    result = context.dmn_engine.evaluate(
        dmn_spec,
        "decision_is_verzekerde_zorgtoeslag",
        context.dmn_parameters
    )

    context.dmn_result = result.output
    context.dmn_trace = result.path

    # Print the execution trace
    print("\n" + "="*80)
    print("DMN EXECUTION TRACE")
    print("="*80)
    print("\nINPUT PARAMETERS:")
    for key, value in context.dmn_parameters.items():
        print(f"  {key}: {value}")
    print("\nEXECUTION PATH:")
    trace_output = format_trace(result.path)
    print(trace_output)
    print("\nFINAL OUTPUT:")
    for key, value in result.output.items():
        print(f"  {key}: {value}")
    print("="*80 + "\n")


@then('the DMN eligibility result should be {expected_value}')
def step_check_dmn_eligibility(context, expected_value):
    """Check DMN eligibility result."""
    expected = expected_value.lower() == 'true'
    actual = context.dmn_result['is_verzekerde_zorgtoeslag']

    assert actual == expected, \
        f"Expected eligibility to be {expected}, but got {actual}"
