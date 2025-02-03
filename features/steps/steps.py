import asyncio
from typing import Any
from unittest import TestCase

import pandas as pd
from behave import given
from behave import when, then

from machine.service import Services

assertions = TestCase()


def parse_value(value: str) -> Any:
    """Parse string value to appropriate type"""
    # Try to convert to int (for monetary values in cents)
    try:
        return int(value)
    except ValueError:
        pass

    # Return as string for other cases
    return value


@given('de volgende {service} {table} gegevens')
def step_impl(context, service, table):
    if not context.table:
        raise ValueError(f"No table provided for {table}")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        processed_row = {k: v if k in {'bsn', 'partner_bsn', 'jaar'} else parse_value(v) for k, v in row.items()}
        data.append(processed_row)

    df = pd.DataFrame(data)

    # Set the DataFrame in services
    context.services.set_source_dataframe(service, table, df)


@given('de datum is "{date}"')
def step_impl(context, date):
    context.root_reference_date = date
    context.services = Services(date)


@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    context.parameters['BSN'] = bsn


@given('de datum van de verkiezingen is "{date}"')
def step_impl(context, date):
    context.parameters['ELECTION_DATE'] = date


@when('de {law} wordt uitgevoerd door {service}')
def step_impl(context, law, service):
    context.result = asyncio.run(
        context.services.evaluate(
            service,
            law=law,
            reference_date=context.root_reference_date,
            parameters=context.parameters,
            overwrite_input=context.test_data
        )
    )


@then('heeft de persoon recht op zorgtoeslag')
def step_impl(context):
    assertions.assertTrue(
        context.result.output['is_verzekerde_zorgtoeslag'],
        "Expected person to be eligible for healthcare allowance, but they were not"
    )


@then('heeft de persoon geen recht op zorgtoeslag')
def step_impl(context):
    assertions.assertFalse(
        context.result.output['is_verzekerde_zorgtoeslag'],
        "Expected person to not be eligible for healthcare allowance, but they were"
    )


@then('is voldaan aan de voorwaarden')
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected requirements to be met, but they were not"
    )


@then('is niet voldaan aan de voorwaarden')
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected requirements to not be met, but they were"
    )


@then('is het toeslagbedrag hoger dan "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['hoogte_toeslag']
    expected_min = int(float(amount) * 100)
    assertions.assertGreater(
        actual_amount,
        expected_min,
        f"Expected allowance amount to be greater than {amount} euros, but was {actual_amount / 100:.2f} euros"
    )


def compare_euro_amount(actual_amount, amount):
    expected_amount = int(float(amount) * 100)
    assertions.assertEqual(
        actual_amount,
        expected_amount,
        f"Expected amount to be {amount} euros, but was {actual_amount / 100:.2f} euros"
    )


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['hoogte_toeslag']
    compare_euro_amount(actual_amount, amount)


@then('is het pensioen "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['pension_amount']
    compare_euro_amount(actual_amount, amount)


@given('een kandidaat met BSN "{bsn}"')
def step_impl(context, bsn):
    if not hasattr(context, 'parameters'):
        context.parameters = {}
    context.parameters['BSN'] = bsn


@given('een partij met ID "{party_id}"')
def step_impl(context, party_id):
    if not hasattr(context, 'parameters'):
        context.parameters = {}
    context.parameters['PARTY_ID'] = party_id


@then('is de kandidaatstelling geldig')
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected candidacy to be valid, but it was not"
    )


@then('is de kandidaatstelling niet geldig')
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected candidacy to be invalid, but it was valid"
    )


@then("heeft de persoon stemrecht")
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected the person to have voting rights"
    )


@then("heeft de persoon geen stemrecht")
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected the person not to have voting rights"
    )


@given('de volgende kandidaatgegevens')
def step_impl(context):
    if not context.table:
        raise ValueError("No table provided for kandidaatgegevens")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        processed_row = {
            'kandidaat_bsn': row['kandidaat_bsn'],
            'positie': int(row['positie']) if row['positie'] != '...' else None,
            'acceptatie': parse_value(row['acceptatie'])
        }
        if processed_row['positie'] is not None:  # Skip the ... rows
            data.append(processed_row)

    df = pd.DataFrame(data)

    # Set in test_data for user_input
    if not hasattr(context, 'test_data'):
        context.test_data = {}

    # We need only kandidaat_bsn and positie for CANDIDATE_LIST
    candidate_list_df = df[['kandidaat_bsn', 'positie']]
    context.test_data['CANDIDATE_LIST'] = candidate_list_df

    # Get the acceptatie for the main candidate
    context.test_data['CANDIDATE_ACCEPTANCE'] = df['acceptatie'].iloc[0]


@then('is het bijstandsuitkeringsbedrag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['benefit_amount']
    compare_euro_amount(actual_amount, amount)


@then('is de woonkostentoeslag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['housing_assistance']
    compare_euro_amount(actual_amount, amount)


@then('is het startkapitaal "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['startup_assistance']
    compare_euro_amount(actual_amount, amount)
