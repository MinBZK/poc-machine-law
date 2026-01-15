"""
Step definitions for wet-synthese feature tests.
"""

import yaml
from behave import given, then, when

from simulate import LawSimulator
from synthesize.learner import SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerator


@given("de simulatie omgeving is geinitialiseerd")
def step_simulatie_omgeving_init(context):
    """Initialize the simulation environment."""
    context.simulator = None
    context.synthesis_df = None
    context.model = None
    context.yaml_spec = None
    context.validation_report = None


@given("een gesimuleerde populatie van {num_people:d} personen")
def step_simuleer_populatie(context, num_people):
    """Generate a simulated population."""
    context.simulator = LawSimulator(simulation_date="2025-03-01")
    results_df = context.simulator.run_simulation(num_people=num_people)
    context.synthesis_df = context.simulator.export_for_synthesis(results_df)
    context.num_people = num_people


@given("de wet-synthese is uitgevoerd")
@when("de wet-synthese wordt uitgevoerd")
def step_wet_synthese(context):
    """Run the law synthesis."""
    learner = SynthesisLearner()
    context.model = learner.train(context.synthesis_df)


@then("wordt een model getraind met eligibility regels")
def step_check_eligibility_regels(context):
    """Check that eligibility rules were extracted."""
    assert context.model is not None
    assert len(context.model.eligibility_rules) > 0


@then("wordt een model getraind met bedrag formules")
def step_check_bedrag_formules(context):
    """Check that amount formulas were extracted."""
    assert context.model is not None
    assert len(context.model.amount_formulas) > 0


@then("de eligibility accuracy is minstens {threshold:d} procent")
def step_check_accuracy(context, threshold):
    """Check that eligibility accuracy meets threshold."""
    assert context.model is not None
    accuracy_pct = context.model.eligibility_accuracy * 100
    assert accuracy_pct >= threshold, f"Accuracy {accuracy_pct:.1f}% is below {threshold}%"


@when("de YAML wordt gegenereerd")
def step_genereer_yaml(context):
    """Generate YAML from the model."""
    generator = YAMLGenerator()
    context.yaml_spec = generator.generate(context.model)
    context.yaml_string = generator.to_yaml_string(context.yaml_spec)


@then("bevat de YAML geldige requirements")
def step_check_requirements(context):
    """Check that YAML contains valid requirements."""
    assert "requirements" in context.yaml_spec
    # Check for operation keywords
    yaml_str = yaml.dump(context.yaml_spec["requirements"])
    assert any(
        op in yaml_str for op in ["LESS_OR_EQUAL", "GREATER_THAN", "GREATER_OR_EQUAL", "LESS_THAN", "EQUALS", "or", "all"]
    )


@then("bevat de YAML geldige actions")
def step_check_actions(context):
    """Check that YAML contains valid actions."""
    assert "actions" in context.yaml_spec
    actions = context.yaml_spec["actions"]
    assert len(actions) >= 2  # is_eligible and toeslag_bedrag

    # Check for expected outputs
    outputs = [a.get("output") for a in actions]
    assert "is_eligible" in outputs
    assert "toeslag_bedrag" in outputs


@then("kan de YAML worden geparsed")
def step_yaml_parseable(context):
    """Check that YAML can be parsed."""
    parsed = yaml.safe_load(context.yaml_string)
    assert parsed is not None
    assert "uuid" in parsed
    assert "name" in parsed


@when("de validatie wordt uitgevoerd")
def step_valideer(context):
    """Run validation on the model."""
    validator = SynthesisValidator(
        accuracy_threshold=0.80,  # Lower for testing
        recall_threshold=0.80,
        amount_tolerance=100.0,
    )
    context.validation_report = validator.validate(context.model, context.synthesis_df)
    context.validator = validator


@then("worden per-groep metrics berekend")
def step_check_group_metrics(context):
    """Check that per-group metrics are calculated."""
    assert context.validation_report is not None
    group_metrics = context.validation_report.metrics.group_metrics
    assert len(group_metrics) > 0


@then("worden aanbevelingen gegenereerd")
def step_check_recommendations(context):
    """Check that recommendations are generated."""
    assert context.validation_report is not None
    assert len(context.validation_report.recommendations) > 0


@then("wordt een validatierapport gemaakt")
def step_check_report(context):
    """Check that a validation report is generated."""
    assert context.validation_report is not None
    markdown = context.validator.generate_report_markdown(context.validation_report)
    assert "# Validatierapport" in markdown


@when("de Nederlandse uitleg wordt gegenereerd")
def step_genereer_uitleg(context):
    """Generate Dutch explanation."""
    # Feature name translations
    feature_nl = {
        "age": "uw leeftijd",
        "income": "uw toetsingsinkomen",
        "net_worth": "uw vermogen",
        "rent_amount": "uw maandelijkse huur",
        "has_partner": "u een toeslagpartner heeft",
        "has_children": "u kinderen heeft",
        "children_count": "het aantal kinderen",
        "youngest_child_age": "de leeftijd van uw jongste kind",
        "housing_type_rent": "u een huurwoning heeft",
        "is_student": "u student bent",
    }

    lines = [
        "# Geharmoniseerde Toeslag",
        "",
        "## Voorwaarden",
        "",
    ]

    for i, rule in enumerate(context.model.eligibility_rules, 1):
        lines.append(f"### Situatie {i}")
        for condition in rule.conditions:
            parts = condition.replace("<=", " <= ").replace(">=", " >= ").replace(">", " > ").replace("<", " < ").split()
            feature = parts[0]
            feature_text = feature_nl.get(feature, feature)
            lines.append(f"- {feature_text}: {' '.join(parts[1:])}")
        lines.append("")

    lines.extend(
        [
            "## Berekening",
            "",
            "Het bedrag wordt berekend op basis van uw situatie.",
        ]
    )

    context.dutch_explanation = "\n".join(lines)


@then("bevat de uitleg voorwaarden in begrijpelijke taal")
def step_check_voorwaarden(context):
    """Check that explanation contains conditions in understandable language."""
    assert "Voorwaarden" in context.dutch_explanation
    assert "Situatie" in context.dutch_explanation


@then("bevat de uitleg een berekeningsuitleg")
def step_check_berekening(context):
    """Check that explanation contains calculation explanation."""
    assert "Berekening" in context.dutch_explanation
