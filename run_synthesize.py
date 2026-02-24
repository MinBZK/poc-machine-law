#!/usr/bin/env python3
"""Standalone synthesis runner to avoid class registration conflicts."""

import json
import sys
from datetime import datetime

from simulate import LawSimulator
from synthesize.learner import InterpretabilityConstraints, SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerationConfig, YAMLGenerator


def run_train(params: dict) -> dict:
    """Train a synthesized law and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    max_depth = params.get("max_depth", 5)
    min_samples = params.get("min_samples", 50)
    max_rules = params.get("max_rules", 10)

    # Run simulation
    simulator = LawSimulator(simulation_date)
    results_df = simulator.run_simulation(num_people=num_people)
    synthesis_df = simulator.export_for_synthesis(results_df)

    # Configure and train
    constraints = InterpretabilityConstraints(
        max_tree_depth=max_depth,
        min_samples_leaf=min_samples,
        max_rules=max_rules,
    )
    learner = SynthesisLearner(constraints=constraints)
    model = learner.train(synthesis_df)

    # Generate YAML
    config = YAMLGenerationConfig()
    generator = YAMLGenerator(config=config)
    yaml_spec = generator.generate(model)
    yaml_string = generator.to_yaml_string(yaml_spec)

    # Generate explanation
    explanation = generate_explanation(model)

    # Extract rules as serializable dicts
    rules = [
        {
            "conditions": rule.conditions,
            "prediction": rule.prediction,
            "samples": rule.samples,
            "confidence": rule.confidence,
        }
        for rule in model.eligibility_rules
    ]

    # Extract formulas as serializable dicts
    formulas = [
        {
            "intercept": formula.intercept,
            "coefficients": formula.coefficients,
            "segment_conditions": formula.segment_conditions,
            "r2_score": formula.r2_score,
            "samples": formula.samples,
        }
        for formula in model.amount_formulas
    ]

    # Cross-validate
    cv_results = learner.cross_validate(synthesis_df)

    return {
        "status": "success",
        "metrics": {
            "eligibility_accuracy": model.eligibility_accuracy,
            "amount_r2": model.amount_r2,
            "amount_mae": model.amount_mae,
            "num_rules": len(model.eligibility_rules),
            "num_formulas": len(model.amount_formulas),
            "num_people": num_people,
            "cross_validation": cv_results,
        },
        "rules": rules,
        "formulas": formulas,
        "yaml": yaml_string,
        "explanation": explanation,
    }


def run_validate(params: dict) -> dict:
    """Validate a synthesized law and return report as JSON."""
    num_people = params.get("num_people", 500)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    max_depth = params.get("max_depth", 5)
    min_samples = params.get("min_samples", 50)
    max_rules = params.get("max_rules", 10)
    accuracy_target = params.get("accuracy_target", 0.95)
    amount_tolerance = params.get("amount_tolerance", 50.0)

    # Run simulation for validation
    simulator = LawSimulator(simulation_date)
    results_df = simulator.run_simulation(num_people=num_people)
    synthesis_df = simulator.export_for_synthesis(results_df)

    # Train model
    constraints = InterpretabilityConstraints(
        max_tree_depth=max_depth,
        min_samples_leaf=min_samples,
        max_rules=max_rules,
    )
    learner = SynthesisLearner(constraints=constraints)
    model = learner.train(synthesis_df)

    # Validate
    validator = SynthesisValidator(
        accuracy_threshold=accuracy_target,
        recall_threshold=0.98,
        amount_tolerance=amount_tolerance,
    )
    report = validator.validate(model, synthesis_df)

    # Generate markdown report
    report_markdown = validator.generate_report_markdown(report)

    return {
        "status": "success",
        "passed": report.passed,
        "report_markdown": report_markdown,
        "metrics": {
            "overall_accuracy": report.metrics.overall_accuracy,
            "eligibility_accuracy": report.metrics.eligibility_accuracy,
            "eligibility_precision": report.metrics.eligibility_precision,
            "eligibility_recall": report.metrics.eligibility_recall,
            "eligibility_f1": report.metrics.eligibility_f1,
            "amount_mae": report.metrics.amount_mae,
            "amount_rmse": report.metrics.amount_rmse,
            "amount_r2": report.metrics.amount_r2,
        },
        "group_metrics": report.metrics.group_metrics,
        "recommendations": report.recommendations,
    }


def _parse_condition(condition: str) -> tuple[str, str, str]:
    """Parse a condition string like 'age > 19.50' or 'income<=20000' into (feature, operator, value)."""
    import re

    match = re.match(r"(\w+)\s*(<=|>=|>|<|==|!=)\s*(.+)", condition.strip())
    if match:
        return match.group(1), match.group(2), match.group(3).strip()
    # Fallback: return raw condition as feature with unknown operator
    return condition, "", ""


def generate_explanation(model) -> str:
    """Generate Dutch explanation from model."""
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
        "Deze toeslag combineert zorgtoeslag, huurtoeslag en kindgebonden budget in een regeling.",
        "",
        "## Voorwaarden",
        "",
        "U komt in aanmerking als u voldoet aan een van de volgende situaties:",
        "",
    ]

    for i, rule in enumerate(model.eligibility_rules, 1):
        lines.append(f"### Situatie {i}")
        lines.append("")
        for condition in rule.conditions:
            feature, operator, value = _parse_condition(condition)

            feature_text = feature_nl.get(feature, feature)

            if operator == "<=":
                op_text = "niet hoger dan"
            elif operator == ">=":
                op_text = "minimaal"
            elif operator == ">":
                op_text = "hoger dan"
            elif operator == "<":
                op_text = "lager dan"
            else:
                op_text = operator

            if feature == "income":
                value_text = f"EUR {float(value):,.0f} per jaar"
            elif feature in ["has_partner", "has_children", "housing_type_rent", "is_student"]:
                value_text = "ja" if value in ["1", "1.0", "True"] else "nee"
            else:
                value_text = value

            lines.append(f"- {feature_text} is {op_text} {value_text}")
        lines.append("")

    lines.extend(
        [
            "## Berekening",
            "",
            "Het bedrag wordt berekend op basis van uw persoonlijke situatie.",
            "",
        ]
    )

    if model.amount_formulas:
        formula = model.amount_formulas[0]
        lines.append(f"**Basisbedrag**: EUR {formula.intercept:.2f}")
        for feature, coef in formula.coefficients.items():
            feature_text = feature_nl.get(feature, feature)
            if coef > 0:
                lines.append(f"**Plus**: {coef:.4f} x {feature_text}")
            else:
                lines.append(f"**Min**: {abs(coef):.4f} x {feature_text}")
        lines.append("")
        lines.append("*Het uiteindelijke bedrag is minimaal EUR 0.*")

    return "\n".join(lines)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)

    params = json.loads(sys.stdin.read())
    operation = params.get("operation", "train")

    try:
        if operation == "train":
            result = run_train(params)
        elif operation == "validate":
            result = run_validate(params)
        else:
            result = {"status": "error", "message": f"Unknown operation: {operation}"}
            print(json.dumps(result), file=sys.stderr)
            sys.exit(1)

        print(json.dumps(result))
    except Exception as e:
        logger.error("Synthesize error: %s", str(e), exc_info=True)
        error_result = {"status": "error", "message": "An internal error occurred during synthesis"}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
