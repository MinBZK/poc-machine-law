"""Step definitions for kieswet v0.1.7 tests using LawEvaluator (context-based architecture)."""

import pandas as pd
from behave import given, when, then

from machine.data_context import DataContext
from machine.law_evaluator import LawEvaluator


@given('de volgende verkiezingen gegevens')
def step_set_verkiezingen_data(context):
    """Set election data in DataContext for v0.1.7 architecture."""
    if not context.table:
        raise ValueError("No table provided for verkiezingen")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        data.append(dict(row))

    df = pd.DataFrame(data)

    # Initialize LawEvaluator if not exists
    if not hasattr(context, 'law_evaluator'):
        context.law_evaluator = LawEvaluator(
            reference_date=context.date,
            data_context=DataContext()
        )

    # Add data to DataContext (no service specified - context-based!)
    # For kieswet, the verkiezingen table belongs to the election authority
    context.law_evaluator.data_context.add_source("KIESRAAD", "verkiezingen", df)


@when('de kieswet v0.1.7 wordt uitgevoerd')
def step_execute_kieswet_v017(context):
    """Execute kieswet using v0.1.7 schema with LawEvaluator."""
    if not hasattr(context, 'law_evaluator'):
        context.law_evaluator = LawEvaluator(
            reference_date=context.date,
            data_context=DataContext()
        )

    # Get BSN from context
    bsn = context.parameters.get("BSN")
    if not bsn:
        raise ValueError("No BSN provided in context")

    # Evaluate kieswet using LawEvaluator (no service parameter needed!)
    context.result = context.law_evaluator.evaluate_law(
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=context.date
    )


# Note: The "heeft de persoon stemrecht" steps are already defined in steps.py
# They check context.result.requirements_met which works for both v0.1.6 and v0.1.7
