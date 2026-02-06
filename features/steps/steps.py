import json
from typing import Any
from unittest import TestCase

import pandas as pd
from behave import given, then, when

from machine.service import Services

assertions = TestCase()


# =============================================================================
# Helpers
# =============================================================================


def parse_value(value: str) -> Any:
    """Parse string value to appropriate type."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    try:
        return int(value)
    except ValueError:
        pass

    return value


def compare_euro_amount(actual_cents: int, expected_euros: str) -> None:
    """Assert that an amount in eurocents equals the expected euros."""
    expected_cents = int(float(expected_euros) * 100)
    assertions.assertEqual(
        actual_cents,
        expected_cents,
        f"Expected amount to be {expected_euros} euros, but was {actual_cents / 100:.2f} euros",
    )


def parse_dutch_currency(amount: str) -> int:
    """Parse Dutch currency format like '€3.296,00' to eurocents."""
    return int(amount.replace("€", "").replace(".", "").replace(",", ""))


def _check_output_field(context, field: str, expected: str) -> None:
    """Check that an output field has a specific value."""
    actual = context.result.output.get(field)
    expected_val = parse_value(expected)
    if expected_val is False and actual is None:
        actual = False
    assertions.assertEqual(actual, expected_val, f"Expected {field} to be {expected_val}, but was {actual}")


def _check_output_contains(context, field: str, value: str) -> None:
    """Check that an output array field contains a specific value."""
    actual = context.result.output.get(field, [])
    expected = parse_value(value)
    actual_str = [str(x) for x in actual]
    expected_str = str(expected)
    assertions.assertIn(expected_str, actual_str, f"Expected {field} to contain {expected_str}, but it was {actual_str}")


def _check_output_empty(context, field: str) -> None:
    """Check that an output array field is empty."""
    actual = context.result.output.get(field, [])
    assertions.assertEqual(len(actual), 0, f"Expected {field} to be empty, but it was {actual}")


def _check_eurocent_field(context, field: str, amount: str) -> None:
    """Check eurocent field values with field name mapping."""
    field_mapping = {
        "bijdrage-inkomen": "bijdrage_inkomen",
        "werkgeversbijdrage": ["werkgeversbijdrage_awf", "zvw_werkgeversbijdrage"],
    }

    field_key = field.replace("-", "_").lower()
    output_fields = field_mapping.get(field_key, field_key)

    if isinstance(output_fields, list):
        actual_amount = None
        for f in output_fields:
            actual_amount = context.result.output.get(f)
            if actual_amount is not None:
                break
    else:
        actual_amount = context.result.output.get(output_fields)

    expected_amount = int(amount)
    assertions.assertEqual(
        actual_amount,
        expected_amount,
        f"Expected {field} to be {expected_amount} eurocent, but was {actual_amount} eurocent",
    )


def evaluate_law(context, service: str, law: str, approved: bool = True) -> None:
    """Execute a law evaluation and store results on context."""
    context.result = context.services.evaluate(
        service,
        law=law,
        parameters=context.parameters,
        reference_date=context.root_reference_date,
        overwrite_input=context.test_data,
        approved=approved,
    )
    context.service = service
    context.law = law


# =============================================================================
# Given Steps - Setup
# =============================================================================


@given("de volgende {service} {table} gegevens")
def step_impl(context, service, table):
    if not context.table:
        raise ValueError(f"No table provided for {table}")

    STRING_FIELDS = {
        "bsn",
        "partner_bsn",
        "jaar",
        "kind_bsn",
        "kvk_nummer",
        "ouder_bsn",
        "postcode",
        "huisnummer",
        "bsn_gezagdrager",
        "bsn_kind",
        "bsn_mentor",
        "bsn_betrokkene",
        "bsn_curator",
        "bsn_curandus",
        "bsn_bewindvoerder",
        "bsn_rechthebbende",
        "bsn_gevolmachtigde",
        "bsn_volmachtgever",
        "bsn_executeur",
        "bsn_erflater",
        "bsn_familielid",
        "bsn_patient",
    }

    data = []
    for row in context.table:
        processed_row = {k: v if k in STRING_FIELDS else parse_value(v) for k, v in row.items()}
        data.append(processed_row)

    df = pd.DataFrame(data)
    context.services.set_source_dataframe(service, table, df)


@given('de datum is "{date}"')
def step_impl(context, date):
    context.root_reference_date = date
    try:
        import eventsourcing.utils

        eventsourcing.utils.clear_topic_cache()
        eventsourcing.utils._type_cache.clear()
    except Exception:
        pass

    try:
        if hasattr(context, "services"):
            del context.services
    except Exception:
        pass
    context.services = Services(date)


@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    context.parameters["BSN"] = bsn


@given('een organisatie met KVK-nummer "{kvk_nummer}"')
def step_impl(context, kvk_nummer):
    context.parameters["KVK_NUMMER"] = kvk_nummer


@given('een {entity_type} met ID "{entity_id}"')
def step_impl(context, entity_type, entity_id):
    """Generic entity setup. Converts entity_type to UPPER_CASE_ID parameter."""
    param_mapping = {
        "ICT-project": "PROJECT_ID",
        "organisatie": "ORGANISATIE_ID",
        "archiefstuk": "ARCHIEFSTUK_ID",
        "project": "PROJECT_ID",
    }
    param_name = param_mapping.get(entity_type, f"{entity_type.upper().replace('-', '_')}_ID")
    context.parameters[param_name] = entity_id


@given('een werkgever met loonheffingennummer "{number}"')
def step_impl(context, number):
    context.parameters["LOONHEFFINGENNUMMER"] = number


@given('een werknemer met bruto jaarloon "{amount}" euro')
def step_impl(context, amount):
    context.parameters["BRUTO_LOON"] = float(amount)


@given('een onderneming met KVK nummer "{kvk_nummer}"')
def step_impl(context, kvk_nummer):
    context.parameters["KVK_NUMMER"] = kvk_nummer
    context.test_data["KVK_NUMMER"] = kvk_nummer


@given("er is geen Bibob-advies uitgebracht voor deze onderneming")
def step_impl(context):
    context.test_data["NO_BIBOB_ADVIES"] = True


@given('de aanvraag betreft een "{aanvraag_type}"')
def step_impl(context, aanvraag_type):
    context.parameters["AANVRAAG_TYPE"] = aanvraag_type


@given("een archiefstuk met de volgende eigenschappen")
def step_impl(context):
    if not context.table:
        raise ValueError("No table provided for archiefstuk properties")

    for row in context.table:
        for heading in context.table.headings:
            value = parse_value(row[heading])
            context.parameters[heading.upper()] = value
            context.test_data[heading.upper()] = value


@given("alle aanvragen worden beoordeeld")
def step_impl(context):
    context.services.case_manager.SAMPLE_RATE = 1.0


# =============================================================================
# When Steps - Actions
# =============================================================================


@when("de {law} wordt uitgevoerd door {service} met wijzigingen")
def step_impl(context, law, service):
    evaluate_law(context, service, law, approved=False)


@when("de {law} wordt uitgevoerd door {service} met")
def step_impl(context, law, service):
    headings = context.table.headings

    for row in context.table:
        if len(headings) > 1 and headings[0] != "key":
            for heading in headings:
                value = parse_value(row[heading])
                context.test_data[heading] = value
                context.parameters[heading] = value
        else:
            key = row.headings[0]
            value = parse_value(row[key])
            context.test_data[key] = value
            context.parameters[key] = value

    evaluate_law(context, service, law)


@when("de {law} wordt uitgevoerd door {service}")
def step_impl(context, law, service):
    evaluate_law(context, service, law)


@when("de persoon dit aanvraagt")
def step_impl(context):
    case_id = context.services.case_manager.submit_case(
        bsn=context.parameters["BSN"],
        service_type=context.service,
        law=context.law,
        parameters=context.result.input,
        claimed_result=context.result.output,
        approved_claims_only=True,
    )
    context.case_id = case_id


@when('de beoordelaar de aanvraag afwijst met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.decide(verified_result=context.result.output, reason=reason, verifier_id="BEOORDELAAR", approved=False)
    context.services.case_manager.save(case)


@when('de burger bezwaar maakt met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.object(reason=reason)
    context.services.case_manager.save(case)


@when('de beoordelaar het bezwaar {approve} met reden "{reason}"')
def step_impl(context, approve, reason):
    approve = approve.lower() == "toewijst"
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.decide(verified_result=context.result.output, reason=reason, verifier_id="BEOORDELAAR", approved=approve)
    context.services.case_manager.save(case)


@when("de burger {chance} indient")
def step_impl(context, chance):
    if not context.table:
        raise ValueError("No table provided for claims")

    if not hasattr(context, "claims"):
        context.claims = []

    for row in context.table:
        identifier = context.parameters.get("BSN") or context.parameters.get("KVK_NUMMER")
        claim_id = context.services.claim_manager.submit_claim(
            service=row["service"],
            key=row["key"],
            new_value=parse_value(row["nieuwe_waarde"]),
            reason=row["reden"],
            claimant="BURGER",
            case_id=None,
            evidence_path=row.get("bewijs"),
            law=row["law"],
            bsn=identifier,
        )
        context.claims.append(claim_id)


# =============================================================================
# Then Steps - Generic Output Assertions
# =============================================================================


@then('heeft de output "{field}" waarde "{value}"')
def step_impl(context, field, value):
    _check_output_field(context, field, value)


@then('is de output "{field}" waar')
def step_impl(context, field):
    _check_output_field(context, field, "true")


@then('is de output "{field}" onwaar')
def step_impl(context, field):
    _check_output_field(context, field, "false")


@then('bevat de output "{field}" waarde "{value}"')
def step_impl(context, field, value):
    _check_output_contains(context, field, value)


@then('bevat de output "{field}" niet de waarde "{value}"')
def step_impl(context, field, value):
    actual = context.result.output.get(field, [])
    expected = parse_value(value)
    actual_str = [str(x) for x in actual]
    expected_str = str(expected)
    assertions.assertNotIn(
        expected_str, actual_str, f"Expected {field} to NOT contain {expected_str}, but it was {actual_str}"
    )


@then('is de output "{field}" leeg')
def step_impl(context, field):
    _check_output_empty(context, field)


# Aliases for kernenergiewet feature files (delegate to canonical implementations)
@then('is het veld "{field}" gelijk aan "{value}"')
def step_impl(context, field, value):
    _check_output_field(context, field, value)


@then('is het veld "{field}" een lege lijst')
def step_impl(context, field):
    _check_output_empty(context, field)


@then('bevat het veld "{field}" de waarde "{value}"')
def step_impl(context, field, value):
    _check_output_contains(context, field, value)


# =============================================================================
# Then Steps - Requirements
# =============================================================================


@then("is voldaan aan de voorwaarden")
def step_impl(context):
    assertions.assertTrue(context.result.requirements_met, "Expected requirements to be met, but they were not")


@then("is niet voldaan aan de voorwaarden")
def step_impl(context):
    assertions.assertFalse(context.result.requirements_met, "Expected requirements to not be met, but they were")


@then("ontbreken er verplichte gegevens")
def step_impl(context):
    assertions.assertTrue(context.result.missing_required, "Er zouden gegevens moeten ontbreken.")


@then("ontbreken er geen verplichte gegevens")
def step_impl(context):
    assertions.assertFalse(context.result.missing_required, "Er zouden geen gegevens moeten ontbreken.")


# =============================================================================
# Then Steps - Euro Amount Assertions
# =============================================================================


@then('is het {field} "{amount}" eurocent')
def step_impl(context, field, amount):
    _check_eurocent_field(context, field, amount)


@then('is de {field} "{amount}" eurocent')
def step_impl(context, field, amount):
    _check_eurocent_field(context, field, amount)


@then('zijn de {field} "{amount}" euro')
def step_impl(context, field, amount):
    """Check field value in euros (converts from eurocent in output)."""
    field_key = field.replace(" ", "_").lower()
    actual_cents = context.result.output.get(field_key)
    expected_euros = float(amount)
    actual_euros = actual_cents / 100 if actual_cents else 0
    assertions.assertEqual(
        actual_euros, expected_euros, f"Expected {field} to be {expected_euros} euro, but was {actual_euros} euro"
    )


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    if "hoogte_toeslag" in context.result.output:
        actual_amount = context.result.output["hoogte_toeslag"]
    elif "jaarbedrag" in context.result.output:
        actual_amount = context.result.output["jaarbedrag"]
    else:
        raise ValueError("No toeslag amount found in output")
    compare_euro_amount(actual_amount, amount)


@then('is het pensioen "{amount}" euro')
def step_impl(context, amount):
    if "pensioen_uitkering_maandelijks" in context.result.output:
        actual_amount = context.result.output["pensioen_uitkering_maandelijks"]
    else:
        actual_amount = context.result.output["pensioenbedrag"]
    compare_euro_amount(actual_amount, amount)


@then('is het bijstandsuitkeringsbedrag "{amount}" euro')
def step_impl(context, amount):
    compare_euro_amount(context.result.output["uitkeringsbedrag"], amount)


@then('is de woonkostentoeslag "{amount}" euro')
def step_impl(context, amount):
    compare_euro_amount(context.result.output["woonkostentoeslag"], amount)


@then('is het startkapitaal "{amount}" euro')
def step_impl(context, amount):
    compare_euro_amount(context.result.output["startkapitaal"], amount)


@then('is het bedrijfskapitaal_max "{amount}" euro')
def step_impl(context, amount):
    compare_euro_amount(context.result.output["bedrijfskapitaal_max"], amount)


@then('is de huurtoeslag "{amount}" euro')
def step_impl(context, amount):
    compare_euro_amount(context.result.output["subsidiebedrag"], amount)


# =============================================================================
# Then Steps - Bbz 2004
# =============================================================================


@then('is de categorie_zelfstandige "{categorie}"')
def step_impl(context, categorie):
    _check_output_field(context, "categorie_zelfstandige", categorie)


@then('is de max_duur_maanden "{maanden}"')
def step_impl(context, maanden):
    _check_output_field(context, "max_duur_maanden", maanden)


@then('is het bedrijfskapitaal_type "{type}"')
def step_impl(context, type):
    _check_output_field(context, "bedrijfskapitaal_type", type)


# =============================================================================
# Then Steps - Zorgtoeslag
# =============================================================================


@then("heeft de persoon recht op zorgtoeslag")
def step_impl(context):
    _check_output_field(context, "is_verzekerde_zorgtoeslag", "true")


# =============================================================================
# Then Steps - Kinderopvangtoeslag
# =============================================================================


@then("heeft de persoon recht op kinderopvangtoeslag")
def step_impl(context):
    _check_output_field(context, "is_gerechtigd", "true")


@then("heeft de persoon geen recht op kinderopvangtoeslag")
def step_impl(context):
    _check_output_field(context, "is_gerechtigd", "false")


# =============================================================================
# Then Steps - WW (Werkloosheidswet)
# =============================================================================


@then("heeft de persoon recht op WW")
def step_impl(context):
    _check_output_field(context, "heeft_recht_op_ww", "true")


@then("heeft de persoon geen recht op WW")
def step_impl(context):
    _check_output_field(context, "heeft_recht_op_ww", "false")


@then('is de WW duur "{maanden}" maanden')
def step_impl(context, maanden):
    _check_output_field(context, "ww_duur_maanden", maanden)


@then('is de WW uitkering per maand ongeveer "{amount}"')
def step_impl(context, amount):
    expected = parse_dutch_currency(amount)
    actual = context.result.output.get("ww_uitkering_per_maand")
    tolerance = expected * 0.01
    assertions.assertAlmostEqual(
        actual,
        expected,
        delta=tolerance,
        msg=f"Expected WW benefit to be approximately {amount} (€{expected / 100:.2f}), but was €{actual / 100:.2f}",
    )


@then('is de WW uitkering per maand maximaal "{amount}"')
def step_impl(context, amount):
    expected = parse_dutch_currency(amount)
    actual = context.result.output.get("ww_uitkering_per_maand")
    assertions.assertEqual(
        actual,
        expected,
        f"Expected WW benefit to be exactly {amount} (€{expected / 100:.2f}), but was €{actual / 100:.2f}",
    )


@then("is de WW uitkering maximaal omdat het dagloon gemaximeerd is")
def step_impl(context):
    max_dagloon = 29067
    actual = context.result.output.get("ww_dagloon")
    assertions.assertEqual(actual, max_dagloon, f"Expected dagloon to be maximized at €290.67, but was €{actual / 100:.2f}")


# =============================================================================
# Then Steps - Kindgebonden Budget
# =============================================================================


@then('is het ALO-kop bedrag "{amount}"')
def step_impl(context, amount):
    expected = parse_dutch_currency(amount)
    actual = context.result.output.get("alo_kop_bedrag", 0)
    assertions.assertEqual(
        actual,
        expected,
        f"Expected ALO-kop to be {amount} (€{expected / 100:.2f}), but was €{actual / 100:.2f}",
    )


@then('is het kindgebonden budget ongeveer "{amount}" per jaar')
def step_impl(context, amount):
    expected = parse_dutch_currency(amount)
    actual = context.result.output.get("kindgebonden_budget_jaar")
    tolerance = expected * 0.02
    assertions.assertAlmostEqual(
        actual,
        expected,
        delta=tolerance,
        msg=f"Expected kindgebonden budget to be approximately {amount} (€{expected / 100:.2f}), but was €{actual / 100:.2f}",
    )


@then('is het totale kindgebonden budget ongeveer "{amount}" per jaar')
def step_impl(context, amount):
    expected = parse_dutch_currency(amount)
    actual = context.result.output.get("kindgebonden_budget_jaar")
    tolerance = expected * 0.02
    assertions.assertAlmostEqual(
        actual,
        expected,
        delta=tolerance,
        msg=f"Expected total kindgebonden budget to be approximately {amount} (€{expected / 100:.2f}), but was €{actual / 100:.2f}",
    )


@then("is het kindgebonden budget lager door hoog inkomen")
def step_impl(context):
    max_budget_2_kinderen_alo = 850200
    totaal = context.result.output.get("kindgebonden_budget_jaar", 0)
    assertions.assertLess(
        totaal, max_budget_2_kinderen_alo, f"Expected budget to be reduced from maximum €8,502, but was €{totaal / 100:.2f}"
    )


@then("ontvangt de persoon de ALO-kop omdat deze alleenstaand is")
def step_impl(context):
    heeft_partner = context.result.output.get("heeft_partner", True)
    alo_kop = context.result.output.get("alo_kop_bedrag", 0)
    assertions.assertFalse(heeft_partner, "Expected person to be single (alleenstaand)")
    assertions.assertGreater(alo_kop, 0, f"Expected ALO-kop for single parent, but was €{alo_kop / 100:.2f}")


@then("is het kindgebonden budget hoog door laag inkomen en meerdere kinderen")
def step_impl(context):
    totaal = context.result.output.get("kindgebonden_budget_jaar", 0)
    inkomen_afbouw = context.result.output.get("inkomen_afbouw", 0)
    assertions.assertGreater(
        totaal, 800000, f"Expected high budget for 3 children with low income, but was €{totaal / 100:.2f}"
    )
    assertions.assertLess(
        inkomen_afbouw, 100000, f"Expected minimal income reduction for low income, but afbouw was €{inkomen_afbouw / 100:.2f}"
    )


@then("ontvangt de persoon extra bedragen voor kinderen 12+ en 16+")
def step_impl(context):
    totaal = context.result.output.get("kindgebonden_budget_jaar", 0)
    assertions.assertGreater(
        totaal, 251100, f"Expected budget with age supplements, but was only €{totaal / 100:.2f}"
    )


@then("is het kindgebonden budget maximaal door laag inkomen")
def step_impl(context):
    inkomen_afbouw = context.result.output.get("inkomen_afbouw", 0)
    assertions.assertLess(
        inkomen_afbouw, 50000, f"Expected minimal/no income reduction for low income, but afbouw was €{inkomen_afbouw / 100:.2f}"
    )


# =============================================================================
# Then Steps - Case Management (Bezwaar/Beroep)
# =============================================================================


@then("wordt de aanvraag toegevoegd aan handmatige beoordeling")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(case.status, "IN_REVIEW", "Expected case to be in review")


@then('is de status "{status}"')
def step_impl(context, status):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(case.status, status, f"Expected status to be {status}, but was {case.status}")


@then("is de aanvraag afgewezen")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(case.status, "DECIDED", "Expected case to be decided")
    assertions.assertFalse(case.approved, "Expected case to be rejected")


@then("is de aanvraag toegekend")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertEqual(case.status, "DECIDED", "Expected case to be decided")
    assertions.assertTrue(case.approved, "Expected case to be approved")


@then("kan de burger in bezwaar gaan")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertTrue(case.can_object(), "Expected case to be objectable")


@then('kan de burger niet in bezwaar gaan met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertFalse(case.can_object(), "Expected case not to be objectable")
    assertions.assertEqual(reason, case.objection_status.get("not_possible_reason"), "Expected reasons to match")


@then("kan de burger in beroep gaan bij {competent_court}")
def step_impl(context, competent_court):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertTrue(case.can_appeal(), "Expected to be able to appeal")
    assertions.assertEqual(
        competent_court, case.appeal_status.get("competent_court"), "Expected another competent court"
    )


# =============================================================================
# Then Steps - LAA (Landelijke Aanpak Adreskwaliteit)
# =============================================================================


@then("genereert wet_brp/laa een signaal")
def step_impl(context):
    _check_output_field(context, "genereer_signaal", "true")


@then("genereert wet_brp/laa geen signaal")
def step_impl(context):
    _check_output_field(context, "genereer_signaal", "false")


@then('is het signaal_type "{signaal_type}"')
def step_impl(context, signaal_type):
    _check_output_field(context, "signaal_type", signaal_type)


@then('is de reactietermijn_weken "{weken}"')
def step_impl(context, weken):
    _check_output_field(context, "reactietermijn_weken", weken)


@then('is de onderzoekstermijn_maanden "{maanden}"')
def step_impl(context, maanden):
    _check_output_field(context, "onderzoekstermijn_maanden", maanden)


# =============================================================================
# Then Steps - Archiefwet
# =============================================================================


@then("moet het archiefstuk overgebracht worden")
def step_impl(context):
    _check_output_field(context, "moet_overgebracht_worden", "true")


@then("hoeft het archiefstuk niet overgebracht te worden")
def step_impl(context):
    _check_output_field(context, "moet_overgebracht_worden", "false")


@then('is de uiterste overbrengdatum "{date}"')
def step_impl(context, date):
    _check_output_field(context, "uiterste_overbrengdatum", date)


@then("is het archiefstuk openbaar")
def step_impl(context):
    _check_output_field(context, "is_openbaar", "true")


@then("is het archiefstuk niet openbaar")
def step_impl(context):
    _check_output_field(context, "is_openbaar", "false")


@then('is de beperking reden "{reason}"')
def step_impl(context, reason):
    _check_output_field(context, "beperking_reden", reason)


@then('is het archiefstuk openbaar vanaf "{date}"')
def step_impl(context, date):
    actual = context.result.output.get("openbaar_vanaf") or context.result.output.get("openbaar_vanaf_datum")
    assertions.assertEqual(actual, date, f"Expected openbaar_vanaf to be {date}, but was {actual}")


@then("mag het archiefstuk vernietigd worden")
def step_impl(context):
    _check_output_field(context, "mag_vernietigd_worden", "true")


@then("mag het archiefstuk niet vernietigd worden")
def step_impl(context):
    _check_output_field(context, "mag_vernietigd_worden", "false")


@then('mag het archiefstuk vernietigd worden vanaf "{date}"')
def step_impl(context, date):
    actual = context.result.output.get("vernietigingsdatum") or context.result.output.get("vernietig_vanaf_datum")
    assertions.assertEqual(actual, date, f"Expected vernietigingsdatum to be {date}, but was {actual}")


@then('is de reden van niet vernietigen "{reason}"')
def step_impl(context, reason):
    _check_output_field(context, "reden_niet_vernietigen", reason)


# =============================================================================
# Then Steps - Bibob/LBB
# =============================================================================


@then("is er geen advies uitgebracht")
def step_impl(context):
    _check_output_field(context, "advies_uitgebracht", "false")


@then("is er een advies uitgebracht")
def step_impl(context):
    _check_output_field(context, "advies_uitgebracht", "true")


@then("wordt verlening geadviseerd")
def step_impl(context):
    _check_output_field(context, "verlening_geadviseerd", "true")


@then("wordt verlening niet geadviseerd")
def step_impl(context):
    _check_output_field(context, "verlening_geadviseerd", "false")


@then("is weigering mogelijk")
def step_impl(context):
    _check_output_field(context, "weigering_mogelijk", "true")


@then("is weigering niet mogelijk")
def step_impl(context):
    _check_output_field(context, "weigering_mogelijk", "false")


@then("zijn voorschriften mogelijk")
def step_impl(context):
    _check_output_field(context, "voorschriften_mogelijk", "true")


@then("zijn voorschriften niet mogelijk")
def step_impl(context):
    _check_output_field(context, "voorschriften_mogelijk", "false")


@then('is de mate van gevaar "{mate}"')
def step_impl(context, mate):
    _check_output_field(context, "mate_van_gevaar", mate)


@then("is er sprake van financieringsrisico")
def step_impl(context):
    _check_output_field(context, "financieringsrisico", "true")


@then("is er een relatie tot strafbare feiten")
def step_impl(context):
    _check_output_field(context, "relatie_strafbare_feiten", "true")


# =============================================================================
# Then Steps - Adviesplicht / Bestuursorgaan
# =============================================================================


@then("valt het project onder adviesplicht")
def step_impl(context):
    _check_output_field(context, "adviesplicht", "true")


@then("valt het project niet onder adviesplicht")
def step_impl(context):
    _check_output_field(context, "adviesplicht", "false")


@then("is de organisatie een bestuursorgaan")
def step_impl(context):
    _check_output_field(context, "is_bestuursorgaan", "true")


@then("is de organisatie geen bestuursorgaan")
def step_impl(context):
    _check_output_field(context, "is_bestuursorgaan", "false")
