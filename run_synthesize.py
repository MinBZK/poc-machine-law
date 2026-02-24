#!/usr/bin/env python3
"""Standalone synthesis runner to avoid class registration conflicts."""

import json
import sys
from datetime import datetime

import pandas as pd

from run_simulation import apply_custom_parameters
from simulate import LawSimulator
from synthesize.learner import InterpretabilityConstraints, LearnedModel, SynthesisLearner
from synthesize.validator import SynthesisValidator
from synthesize.yaml_generator import YAMLGenerationConfig, YAMLGenerator

# Mapping from feature names to the source laws they belong to
FEATURE_LAW_MAP: dict[str, list[str]] = {
    "rent_amount": ["huurtoeslag"],
    "housing_type_rent": ["huurtoeslag"],
    "children_count": ["kindgebonden_budget"],
    "has_children": ["kindgebonden_budget"],
    "youngest_child_age": ["kindgebonden_budget"],
    "net_worth": ["zorgtoeslag"],
    "is_student": ["zorgtoeslag"],
    "income": ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"],
    "has_partner": ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"],
    "age": ["zorgtoeslag", "kindgebonden_budget"],
}

LAW_LABELS: dict[str, str] = {
    "zorgtoeslag": "Zorgtoeslag",
    "huurtoeslag": "Huurtoeslag",
    "kindgebonden_budget": "Kindgebonden budget",
}


def _count_splits_per_law(tree, feature_names: list[str]) -> dict[str, int]:
    """Count how many splits in the decision tree use features belonging to each law.

    More splits = the model needs more branching to capture that law's logic = more complex.
    """
    tree_ = tree.tree_
    all_laws = ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"]
    law_splits: dict[str, int] = {law: 0 for law in all_laws}

    for node_id in range(tree_.node_count):
        feature_idx = tree_.feature[node_id]
        if feature_idx == -2:  # leaf node
            continue
        feat = feature_names[feature_idx]
        laws = FEATURE_LAW_MAP.get(feat, [])
        for law in laws:
            law_splits[law] += 1

    return law_splits


def analyze_per_law(model: LearnedModel, synthesis_df: pd.DataFrame) -> dict:
    """Analyze which source law the synthesized model resembles most and which is most complex.

    Uses the decision tree's built-in Gini feature importances to determine which law
    the model resembles most, and counts splits per law to determine complexity.
    """
    tree = model._eligibility_tree
    feature_names = model.feature_names
    importances = tree.feature_importances_  # Gini importance, shape: (n_features,)

    all_laws = ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"]

    # --- A. Feature importance (Gini) ---
    total_importance = importances.sum()
    feature_importance = []
    for i, feat in enumerate(feature_names):
        laws = FEATURE_LAW_MAP.get(feat, [])
        imp = float(importances[i] / total_importance) if total_importance > 0 else 0.0
        feature_importance.append({"feature": feat, "importance": round(imp, 4), "laws": laws})

    feature_importance.sort(key=lambda x: x["importance"], reverse=True)

    # --- B. Per-law importance (shared features split evenly) ---
    law_importance: dict[str, float] = {law: 0.0 for law in all_laws}
    for i, feat in enumerate(feature_names):
        laws = FEATURE_LAW_MAP.get(feat, [])
        if not laws:
            continue
        share = 1.0 / len(laws)
        for law in laws:
            law_importance[law] += float(importances[i]) * share

    total_law_imp = sum(law_importance.values())
    law_importance_pct = {law: (v / total_law_imp if total_law_imp > 0 else 0.0) for law, v in law_importance.items()}

    # --- C. Complexity: count splits per law in the tree ---
    law_splits = _count_splits_per_law(tree, feature_names)
    total_splits = sum(law_splits.values()) or 1
    law_complexity = {law: splits / total_splits for law, splits in law_splits.items()}

    # --- D. Amount contribution (exact: y_total = y_zorg + y_huur + y_kgb) ---
    amount_cols = {
        "zorgtoeslag": "zorgtoeslag_amount",
        "huurtoeslag": "huurtoeslag_amount",
        "kindgebonden_budget": "kindgebonden_budget_amount",
    }
    total_mean = sum(synthesis_df[col].mean() for col in amount_cols.values() if col in synthesis_df.columns)
    amount_contribution = {}
    for law, col in amount_cols.items():
        if col in synthesis_df.columns and total_mean > 0:
            amount_contribution[law] = round(float(synthesis_df[col].mean() / total_mean), 4)
        else:
            amount_contribution[law] = 0.0

    # --- E. Eligibility rate per law ---
    elig_cols = {
        "zorgtoeslag": "zorgtoeslag_eligible",
        "huurtoeslag": "huurtoeslag_eligible",
        "kindgebonden_budget": "kindgebonden_budget_eligible",
    }
    eligibility_rate = {}
    for law, col in elig_cols.items():
        if col in synthesis_df.columns:
            eligibility_rate[law] = round(float(synthesis_df[col].mean()), 4)
        else:
            eligibility_rate[law] = 0.0

    # --- F. Determine most similar / most complex ---
    most_similar = max(all_laws, key=lambda l: law_importance_pct[l])
    most_complex = max(all_laws, key=lambda l: law_complexity[l])

    # --- G. Build output ---
    laws_output = {}
    for law in all_laws:
        laws_output[law] = {
            "label": LAW_LABELS[law],
            "importance": round(law_importance_pct[law], 4),
            "complexity": round(law_complexity[law], 4),
            "splits": law_splits[law],
            "amount_contribution": amount_contribution[law],
            "eligibility_rate": eligibility_rate[law],
            "is_most_similar": law == most_similar,
            "is_most_complex": law == most_complex,
        }

    return {
        "feature_importance": feature_importance,
        "laws": laws_output,
        "most_similar": most_similar,
        "most_complex": most_complex,
    }


def extract_tree_structure(tree, feature_names: list[str]) -> dict:
    """Export sklearn decision tree as a nested JSON structure for visualization."""
    tree_ = tree.tree_
    classes = tree.classes_

    def _build_node(node_id: int) -> dict:
        is_leaf = tree_.children_left[node_id] == tree_.children_right[node_id]
        samples = int(tree_.n_node_samples[node_id])

        if is_leaf:
            # Leaf node: determine prediction and confidence
            value = tree_.value[node_id][0]
            predicted_class_idx = int(value.argmax())
            total = value.sum()
            confidence = float(value[predicted_class_idx] / total) if total > 0 else 0.0
            prediction = str(classes[predicted_class_idx]) if len(classes) > predicted_class_idx else "unknown"
            return {
                "is_leaf": True,
                "prediction": prediction,
                "samples": samples,
                "confidence": round(confidence, 3),
            }

        # Internal node: has a split
        feature_idx = tree_.feature[node_id]
        threshold = float(tree_.threshold[node_id])
        feature = feature_names[feature_idx] if feature_idx < len(feature_names) else f"feature_{feature_idx}"

        return {
            "is_leaf": False,
            "feature": feature,
            "threshold": round(threshold, 2),
            "samples": samples,
            "left": _build_node(tree_.children_left[node_id]),
            "right": _build_node(tree_.children_right[node_id]),
        }

    return _build_node(0)


def run_train(params: dict) -> dict:
    """Train a synthesized law and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    max_depth = params.get("max_depth", 5)
    min_samples = params.get("min_samples", 50)
    max_rules = params.get("max_rules", 10)

    # Run simulation with optional demographic params
    simulator = LawSimulator(simulation_date)
    apply_custom_parameters(simulator, params)
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

    # Per-law analysis
    law_analysis = analyze_per_law(model, synthesis_df)

    # Extract tree structure for visualization
    tree_structure = extract_tree_structure(model._eligibility_tree, model.feature_names)

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
        "tree_structure": tree_structure,
        "formulas": formulas,
        "yaml": yaml_string,
        "explanation": explanation,
        "law_analysis": law_analysis,
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

    # Run simulation for validation with optional demographic params
    simulator = LawSimulator(simulation_date)
    apply_custom_parameters(simulator, params)
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


def _format_condition_nl(condition: str, feature_nl: dict[str, str]) -> str:
    """Format a single condition as readable Dutch text."""
    feature, operator, value = _parse_condition(condition)
    feature_text = feature_nl.get(feature, feature)

    op_map = {"<=": "niet hoger dan", ">=": "minimaal", ">": "hoger dan", "<": "lager dan"}
    op_text = op_map.get(operator, operator)

    if feature == "income":
        value_text = f"EUR {float(value):,.0f} per jaar"
    elif feature in ("has_partner", "has_children", "housing_type_rent", "is_student"):
        value_text = "ja" if value in ("1", "1.0", "True") else "nee"
    else:
        value_text = value

    return f"{feature_text} is {op_text} {value_text}"


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

    num_rules = len(model.eligibility_rules)
    num_formulas = len(model.amount_formulas)

    lines = [
        "# Geharmoniseerde Toeslag",
        "",
        "Deze toeslag combineert **zorgtoeslag**, **huurtoeslag** en **kindgebonden budget** "
        "in één vereenvoudigde regeling.",
        "",
        "---",
        "",
        "## Wie komt in aanmerking?",
        "",
        f"U komt in aanmerking als u voldoet aan een van de volgende {num_rules} situaties:",
        "",
    ]

    for i, rule in enumerate(model.eligibility_rules, 1):
        confidence_pct = f"{rule.confidence:.0%}"
        lines.append(f"### Situatie {i}")
        lines.append("")
        lines.append(f"*Geldt voor {rule.samples} personen (zekerheid: {confidence_pct})*")
        lines.append("")

        for condition in rule.conditions:
            lines.append(f"- {_format_condition_nl(condition, feature_nl)}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Hoe wordt het bedrag berekend?",
            "",
            "Het maandelijkse toeslagbedrag wordt berekend op basis van uw persoonlijke situatie. "
            f"Er zijn {num_formulas} berekeningsgroep(en).",
            "",
        ]
    )

    for i, formula in enumerate(model.amount_formulas, 1):
        lines.append(f"### Groep {i}")
        lines.append("")

        if formula.segment_conditions:
            lines.append("**Van toepassing als:**")
            for cond in formula.segment_conditions:
                lines.append(f"- {_format_condition_nl(cond, feature_nl)}")
            lines.append("")

        lines.append(f"**Basisbedrag**: EUR {formula.intercept:.2f} per maand")
        lines.append("")

        adjustments = []
        for feature, coef in formula.coefficients.items():
            feature_text = feature_nl.get(feature, feature)
            if coef > 0:
                adjustments.append(f"- **+** EUR {coef:.4f} per eenheid {feature_text}")
            else:
                adjustments.append(f"- **−** EUR {abs(coef):.4f} per eenheid {feature_text}")

        if adjustments:
            lines.append("**Aanpassingen op basis van uw situatie:**")
            lines.extend(adjustments)
            lines.append("")

        lines.append(f"*Verklaarde waarde (R²): {formula.r2_score:.2f} — gebaseerd op {formula.samples} personen*")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Het uiteindelijke bedrag is minimaal EUR 0 per maand.*",
        ]
    )

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
