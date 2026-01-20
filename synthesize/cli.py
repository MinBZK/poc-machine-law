"""
Command-line interface for Law Synthesis.

Usage:
    uv run python -m synthesize train --num-people 1000 --output output.yaml
    uv run python -m synthesize validate --yaml output.yaml --num-people 500
"""

import argparse
import sys
from pathlib import Path

from synthesize.learner import InterpretabilityConstraints, SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerationConfig, YAMLGenerator


def train_command(args: argparse.Namespace) -> int:
    """Train a synthesized law from simulation data."""
    print(f"Training synthesized law with {args.num_people} simulated people...")

    # Import here to avoid circular imports
    from simulate import LawSimulator

    # Run simulation
    print("Running simulation...")
    simulator = LawSimulator(simulation_date=args.date)
    results_df = simulator.run_simulation(num_people=args.num_people)

    # Export for synthesis
    synthesis_df = simulator.export_for_synthesis(results_df)
    print(f"Exported {len(synthesis_df)} records for synthesis")

    # Configure constraints
    constraints = InterpretabilityConstraints(
        max_tree_depth=args.max_depth,
        min_samples_leaf=args.min_samples,
        max_rules=args.max_rules,
    )

    # Train model
    print("Training model...")
    learner = SynthesisLearner(constraints=constraints)
    model = learner.train(synthesis_df)

    print("\nModel trained:")
    print(f"  - Eligibility accuracy: {model.eligibility_accuracy:.1%}")
    print(f"  - Amount R²: {model.amount_r2:.3f}")
    print(f"  - Amount MAE: EUR {model.amount_mae:.2f}/month")
    print(f"  - Number of rules: {len(model.eligibility_rules)}")
    print(f"  - Number of formulas: {len(model.amount_formulas)}")

    # Generate YAML
    print("\nGenerating YAML...")
    config = YAMLGenerationConfig(
        law_name=args.law_name,
        law_display_name=args.display_name,
    )
    generator = YAMLGenerator(config=config)
    yaml_spec = generator.generate(model)

    # Save YAML
    output_path = Path(args.output)
    generator.save_yaml(yaml_spec, str(output_path))
    print(f"YAML saved to: {output_path}")

    # Print extracted rules
    print("\n--- Extracted Eligibility Rules ---")
    for i, rule in enumerate(model.eligibility_rules, 1):
        print(f"\nRule {i} (n={rule.samples}, confidence={rule.confidence:.1%}):")
        for condition in rule.conditions:
            print(f"  - {condition}")

    print("\n--- Extracted Amount Formulas ---")
    for i, formula in enumerate(model.amount_formulas, 1):
        print(f"\nFormula {i} (n={formula.samples}, R²={formula.r2_score:.3f}):")
        print(f"  Intercept: {formula.intercept:.2f}")
        for feature, coef in formula.coefficients.items():
            print(f"  + {coef:.4f} * {feature}")

    return 0


def validate_command(args: argparse.Namespace) -> int:
    """Validate a synthesized law against new simulation data."""
    print(f"Validating synthesized law with {args.num_people} new simulated people...")

    # Import here to avoid circular imports
    from simulate import LawSimulator

    # Run new simulation for validation
    print("Running validation simulation...")
    simulator = LawSimulator(simulation_date=args.date)
    results_df = simulator.run_simulation(num_people=args.num_people)
    synthesis_df = simulator.export_for_synthesis(results_df)

    # Load and retrain model (we need the sklearn objects)
    # In a production system, we'd serialize the model
    print("Training model for validation...")
    constraints = InterpretabilityConstraints(
        max_tree_depth=args.max_depth,
        min_samples_leaf=args.min_samples,
    )
    learner = SynthesisLearner(constraints=constraints)
    model = learner.train(synthesis_df)

    # Validate
    print("Running validation...")
    validator = SynthesisValidator(
        accuracy_threshold=args.accuracy_target,
        recall_threshold=0.98,
        amount_tolerance=args.amount_tolerance,
    )
    report = validator.validate(model, synthesis_df)

    # Print report
    print("\n" + "=" * 60)
    print(validator.generate_report_markdown(report))
    print("=" * 60)

    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        with open(report_path, "w") as f:
            f.write(validator.generate_report_markdown(report))
        print(f"\nReport saved to: {report_path}")

    return 0 if report.passed else 1


def explain_command(args: argparse.Namespace) -> int:
    """Generate Dutch explanation of synthesized law."""
    print("Generating Dutch explanation...")

    # Import here to avoid circular imports
    from simulate import LawSimulator

    # We need to train to get the rules
    print("Training model to extract rules...")
    simulator = LawSimulator(simulation_date=args.date)
    results_df = simulator.run_simulation(num_people=args.num_people)
    synthesis_df = simulator.export_for_synthesis(results_df)

    learner = SynthesisLearner()
    model = learner.train(synthesis_df)

    # Generate Dutch explanation
    lines = [
        "# Geharmoniseerde Toeslag",
        "",
        "Deze toeslag combineert zorgtoeslag, huurtoeslag en kindgebonden budget in één regeling.",
        "",
        "## Voorwaarden",
        "",
        "U komt in aanmerking voor de geharmoniseerde toeslag als u voldoet aan één van de volgende situaties:",
        "",
    ]

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

    for i, rule in enumerate(model.eligibility_rules, 1):
        lines.append(f"### Situatie {i}")
        lines.append("")
        for condition in rule.conditions:
            # Parse and translate condition
            parts = (
                condition.replace("<=", " <= ").replace(">=", " >= ").replace(">", " > ").replace("<", " < ").split()
            )
            feature = parts[0]
            operator = parts[1]
            value = parts[2]

            feature_text = feature_nl.get(feature, feature)

            # Translate operator
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

            # Format value
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
            "Het bedrag van uw toeslag wordt berekend op basis van uw persoonlijke situatie.",
            "De formule houdt rekening met uw inkomen, woonsituatie en gezinssamenstelling.",
            "",
        ]
    )

    # Add formula explanation
    if model.amount_formulas:
        formula = model.amount_formulas[0]
        lines.append("De basis berekening is:")
        lines.append("")
        lines.append(f"**Basisbedrag**: EUR {formula.intercept:.2f}")
        for feature, coef in formula.coefficients.items():
            feature_text = feature_nl.get(feature, feature)
            if coef > 0:
                lines.append(f"**Plus**: {coef:.4f} × {feature_text}")
            else:
                lines.append(f"**Min**: {abs(coef):.4f} × {feature_text}")
        lines.append("")
        lines.append("*Het uiteindelijke bedrag is minimaal EUR 0.*")

    explanation = "\n".join(lines)

    # Save or print
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write(explanation)
        print(f"Explanation saved to: {output_path}")
    else:
        print(explanation)

    return 0


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="synthesize",
        description="Law Synthesis - Generate simplified laws from simulation results",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train a synthesized law")
    train_parser.add_argument("--num-people", type=int, default=1000, help="Number of people to simulate")
    train_parser.add_argument("--output", type=str, default="geharmoniseerde_toeslag.yaml", help="Output YAML file")
    train_parser.add_argument("--max-depth", type=int, default=5, help="Maximum decision tree depth")
    train_parser.add_argument("--min-samples", type=int, default=50, help="Minimum samples per leaf")
    train_parser.add_argument("--max-rules", type=int, default=10, help="Maximum number of eligibility rules")
    train_parser.add_argument("--law-name", type=str, default="geharmoniseerde_toeslag", help="Technical law name")
    train_parser.add_argument("--display-name", type=str, default="Geharmoniseerde Toeslag", help="Display name")
    train_parser.add_argument("--date", type=str, default="2025-03-01", help="Simulation date")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a synthesized law")
    validate_parser.add_argument("--yaml", type=str, required=True, help="YAML file to validate")
    validate_parser.add_argument("--num-people", type=int, default=500, help="Number of people to simulate")
    validate_parser.add_argument("--accuracy-target", type=float, default=0.95, help="Target accuracy")
    validate_parser.add_argument("--amount-tolerance", type=float, default=50.0, help="Amount tolerance in EUR")
    validate_parser.add_argument("--report", type=str, help="Output report file")
    validate_parser.add_argument("--max-depth", type=int, default=5, help="Maximum decision tree depth")
    validate_parser.add_argument("--min-samples", type=int, default=50, help="Minimum samples per leaf")
    validate_parser.add_argument("--date", type=str, default="2025-03-01", help="Simulation date")

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Generate Dutch explanation")
    explain_parser.add_argument("--num-people", type=int, default=500, help="Number of people to simulate")
    explain_parser.add_argument("--output", type=str, help="Output markdown file")
    explain_parser.add_argument("--date", type=str, default="2025-03-01", help="Simulation date")

    args = parser.parse_args()

    if args.command == "train":
        return train_command(args)
    elif args.command == "validate":
        return validate_command(args)
    elif args.command == "explain":
        return explain_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
