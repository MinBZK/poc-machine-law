#!/usr/bin/env python3
"""Standalone synthesis runner to avoid class registration conflicts."""

import json
import sys
from datetime import datetime

import pandas as pd

from run_simulation import apply_custom_parameters
from simulate import LawSimulator
from synthesize.bracket_learner import BracketLearner, BracketLearnerConfig
from synthesize.bracket_yaml_generator import BracketYAMLConfig, BracketYAMLGenerator
from synthesize.feature_registry import get_feature_warnings, get_grouping_features_for_laws
from synthesize.learner import InterpretabilityConstraints, LearnedModel, SynthesisLearner
from synthesize.parametric_learner import ParametricConstraints, ParametricLearner
from synthesize.parametric_yaml_generator import ParametricYAMLConfig, ParametricYAMLGenerator
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

# All laws available for synthesis (financial laws only)
AVAILABLE_LAWS: dict[str, dict] = {
    "zorgtoeslag": {"label": "Zorgtoeslag", "group": "Toeslagen"},
    "huurtoeslag": {"label": "Huurtoeslag", "group": "Toeslagen"},
    "kindgebonden_budget": {"label": "Kindgebonden budget", "group": "Toeslagen"},
    "kinderopvangtoeslag": {"label": "Kinderopvangtoeslag", "group": "Toeslagen"},
    "bijstand": {"label": "Bijstand", "group": "Sociale zekerheid"},
    "aow": {"label": "AOW", "group": "Sociale zekerheid"},
    "ww": {"label": "WW-uitkering", "group": "Sociale zekerheid"},
}

DEFAULT_SELECTED_LAWS = ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"]


def _build_feature_law_map(selected_laws: list[str]) -> dict[str, list[str]]:
    """Build feature-to-law mapping for selected laws only."""
    full_map: dict[str, list[str]] = {
        "rent_amount": ["huurtoeslag"],
        "housing_type_rent": ["huurtoeslag"],
        "children_count": ["kindgebonden_budget", "kinderopvangtoeslag"],
        "has_children": ["kindgebonden_budget", "kinderopvangtoeslag"],
        "youngest_child_age": ["kindgebonden_budget"],
        "net_worth": ["zorgtoeslag"],
        "is_student": ["zorgtoeslag"],
        "income": ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand", "ww", "aow", "kinderopvangtoeslag"],
        "has_partner": ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand", "aow"],
        "age": ["zorgtoeslag", "kindgebonden_budget", "aow", "ww"],
    }
    # Filter to only selected laws
    result = {}
    for feat, laws in full_map.items():
        filtered = [l for l in laws if l in selected_laws]
        if filtered:
            result[feat] = filtered
    return result


def _count_splits_per_law(
    tree, feature_names: list[str], feature_law_map: dict[str, list[str]], all_laws: list[str]
) -> dict[str, int]:
    """Count how many splits in the decision tree use features belonging to each law.

    More splits = the model needs more branching to capture that law's logic = more complex.
    """
    tree_ = tree.tree_
    law_splits: dict[str, int] = {law: 0 for law in all_laws}

    for node_id in range(tree_.node_count):
        feature_idx = tree_.feature[node_id]
        if feature_idx == -2:  # leaf node
            continue
        feat = feature_names[feature_idx]
        laws = feature_law_map.get(feat, [])
        for law in laws:
            if law in law_splits:
                law_splits[law] += 1

    return law_splits


def analyze_per_law(
    model: LearnedModel,
    synthesis_df: pd.DataFrame,
    all_laws: list[str],
    feature_law_map: dict[str, list[str]],
    law_labels: dict[str, str],
) -> dict:
    """Analyze which source law the synthesized model resembles most and which is most complex.

    Uses the decision tree's built-in Gini feature importances to determine which law
    the model resembles most, and counts splits per law to determine complexity.
    """
    tree = model._eligibility_tree
    feature_names = model.feature_names
    importances = tree.feature_importances_  # Gini importance, shape: (n_features,)

    # --- A. Feature importance (Gini) ---
    total_importance = importances.sum()
    feature_importance = []
    for i, feat in enumerate(feature_names):
        laws = feature_law_map.get(feat, [])
        imp = float(importances[i] / total_importance) if total_importance > 0 else 0.0
        feature_importance.append({"feature": feat, "importance": round(imp, 4), "laws": laws})

    feature_importance.sort(key=lambda x: x["importance"], reverse=True)

    # --- B. Per-law importance (shared features split evenly) ---
    law_importance: dict[str, float] = {law: 0.0 for law in all_laws}
    for i, feat in enumerate(feature_names):
        laws = feature_law_map.get(feat, [])
        if not laws:
            continue
        share = 1.0 / len(laws)
        for law in laws:
            if law in law_importance:
                law_importance[law] += float(importances[i]) * share

    total_law_imp = sum(law_importance.values())
    law_importance_pct = {law: (v / total_law_imp if total_law_imp > 0 else 0.0) for law, v in law_importance.items()}

    # --- C. Complexity: count splits per law in the tree ---
    law_splits = _count_splits_per_law(tree, feature_names, feature_law_map, all_laws)
    total_splits = sum(law_splits.values()) or 1
    law_complexity = {law: splits / total_splits for law, splits in law_splits.items()}

    # --- D. Amount contribution (dynamic based on selected laws) ---
    amount_cols = {law: f"{law}_amount" for law in all_laws}
    total_mean = sum(synthesis_df[col].mean() for col in amount_cols.values() if col in synthesis_df.columns)
    amount_contribution = {}
    for law, col in amount_cols.items():
        if col in synthesis_df.columns and total_mean > 0:
            amount_contribution[law] = round(float(synthesis_df[col].mean() / total_mean), 4)
        else:
            amount_contribution[law] = 0.0

    # --- E. Eligibility rate per law ---
    elig_cols = {law: f"{law}_eligible" for law in all_laws}
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
            "label": law_labels.get(law, law),
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


def run_train_tree(params: dict, selected_laws: list[str]) -> dict:
    """Train a decision-tree synthesized law and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    max_depth = params.get("max_depth", 5)
    min_samples = params.get("min_samples", 50)
    max_rules = params.get("max_rules", 10)

    # Run simulation with optional demographic params
    simulator = LawSimulator(simulation_date)
    apply_custom_parameters(simulator, params)
    results_df = simulator.run_simulation(num_people=num_people)
    synthesis_df = simulator.export_for_synthesis(results_df, selected_laws=selected_laws)

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
    feature_law_map = _build_feature_law_map(selected_laws)
    law_labels = {k: AVAILABLE_LAWS[k]["label"] for k in selected_laws if k in AVAILABLE_LAWS}
    law_analysis = analyze_per_law(model, synthesis_df, selected_laws, feature_law_map, law_labels)

    # Extract tree structure for visualization
    tree_structure = extract_tree_structure(model._eligibility_tree, model.feature_names)

    # Feature warnings for missing simulation data
    feature_warnings = get_feature_warnings(selected_laws)

    return {
        "status": "success",
        "method": "tree",
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
        "feature_warnings": feature_warnings,
    }


def run_train_bracket(params: dict, selected_laws: list[str]) -> dict:
    """Train a bracket/staffel model and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    n_brackets = params.get("n_brackets", 5)

    simulator = LawSimulator(simulation_date)
    apply_custom_parameters(simulator, params)
    results_df = simulator.run_simulation(num_people=num_people)
    synthesis_df = simulator.export_for_synthesis(results_df, selected_laws=selected_laws)

    config = BracketLearnerConfig(n_brackets=n_brackets)
    learner = BracketLearner(config=config)

    # Get dynamic grouping keys based on selected laws
    grouping_features = get_grouping_features_for_laws(selected_laws)
    # Convert to bracket model column names and filter out continuous features
    continuous_features = (
        "income",
        "rent_amount",
        "children_count",
        "youngest_child_age",
        "net_worth",
        "age",
        "work_years",
    )
    grouping_keys = []
    for f in grouping_features:
        if f == "housing_type":
            grouping_keys.append("housing_type_rent")
        elif f not in continuous_features:
            grouping_keys.append(f)

    model = learner.train(synthesis_df, grouping_keys=grouping_keys)
    metrics = learner.evaluate(model, synthesis_df)

    # Generate YAML
    yaml_config = BracketYAMLConfig()
    generator = BracketYAMLGenerator(config=yaml_config)
    yaml_spec = generator.generate(model)
    yaml_string = generator.to_yaml_string(yaml_spec)

    # Generate explanation
    explanation = _generate_bracket_explanation(model, selected_laws)

    # Feature warnings for missing simulation data
    feature_warnings = get_feature_warnings(selected_laws)

    # Build bracket table for UI
    bracket_table = []
    for seg in model.segments:
        bracket_table.append(
            {
                "income_lower": seg.income_lower,
                "income_upper": seg.income_upper,
                "amount_at_lower": seg.amount_at_lower,
                "amount_at_upper": seg.amount_at_upper,
                "household_filter": seg.household_filter,
            }
        )

    return {
        "status": "success",
        "method": "bracket",
        "metrics": {
            "eligibility_accuracy": metrics["eligibility_accuracy"],
            "amount_r2": metrics["amount_r2"],
            "amount_mae": metrics["amount_mae"],
            "num_brackets": len(model.income_brackets) - 1,
            "num_segments": len(model.segments),
            "num_people": num_people,
        },
        "bracket_table": bracket_table,
        "income_brackets": model.income_brackets,
        "child_supplement": model.child_supplement,
        "feature_influence": model.feature_influence,
        "yaml": yaml_string,
        "explanation": explanation,
        "feature_warnings": feature_warnings,
    }


def run_train_parametric(params: dict, selected_laws: list[str]) -> dict:
    """Train a parametric formula model and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))

    simulator = LawSimulator(simulation_date)
    apply_custom_parameters(simulator, params)
    results_df = simulator.run_simulation(num_people=num_people)
    synthesis_df = simulator.export_for_synthesis(results_df, selected_laws=selected_laws)

    constraints = ParametricConstraints()
    learner = ParametricLearner(constraints=constraints)
    model = learner.train(synthesis_df, selected_laws)

    # Generate YAML
    yaml_config = ParametricYAMLConfig()
    generator = ParametricYAMLGenerator(config=yaml_config)
    yaml_spec = generator.generate(model)
    yaml_string = generator.to_yaml_string(yaml_spec)

    # Generate explanation
    explanation = _generate_parametric_explanation(model, selected_laws)

    # Build component data for UI (convert numpy types to native Python)
    components = []
    for comp in model.template.components:
        components.append(
            {
                "name": comp.name,
                "label": AVAILABLE_LAWS.get(comp.name, {}).get("label", comp.name),
                "base_single": float(comp.base_single),
                "base_partner": float(comp.base_partner),
                "rate_single": float(comp.rate_single),
                "rate_partner": float(comp.rate_partner),
                "threshold_single": float(comp.threshold_single),
                "threshold_partner": float(comp.threshold_partner),
                "has_partner_variant": bool(comp.has_partner_variant),
            }
        )

    # Feature warnings for missing simulation data
    feature_warnings = get_feature_warnings(selected_laws)

    return {
        "status": "success",
        "method": "parametric",
        "metrics": {
            "eligibility_accuracy": model.metrics["eligibility_accuracy"],
            "amount_r2": model.metrics["amount_r2"],
            "amount_mae": model.metrics["amount_mae"],
            "optimization_mae": model.metrics.get("optimization_mae", 0),
            "num_components": len(model.template.components),
            "num_people": num_people,
        },
        "components": components,
        "yaml": yaml_string,
        "explanation": explanation,
        "feature_warnings": feature_warnings,
    }


def _generate_bracket_explanation(model, selected_laws: list[str]) -> str:
    """Generate Dutch explanation for bracket model."""
    law_names = [AVAILABLE_LAWS.get(l, {}).get("label", l) for l in selected_laws]
    laws_text = ", ".join(law_names[:-1]) + " en " + law_names[-1] if len(law_names) > 1 else law_names[0]

    lines = [
        "# Geharmoniseerde Toeslag — Staffelmodel",
        "",
        f"Deze toeslag combineert **{laws_text}** in een inkomensafhankelijke staffel.",
        "",
        "---",
        "",
        "## Hoe werkt het?",
        "",
        "Uw toeslagbedrag wordt bepaald door uw inkomen en huishoudsituatie.",
        "Binnen elke inkomensband wordt het bedrag vloeiend berekend (lineaire interpolatie),",
        "zodat er geen harde grenzen ('cliff effects') zijn.",
        "",
        "## Inkomensschijven",
        "",
        "| Van | Tot | Bedrag ondergrens | Bedrag bovengrens |",
        "|-----|-----|-------------------|-------------------|",
    ]

    seen_brackets = set()
    for seg in model.segments:
        key = (seg.income_lower, seg.income_upper)
        if key not in seen_brackets:
            seen_brackets.add(key)
            lines.append(
                f"| EUR {seg.income_lower:,.0f} | EUR {seg.income_upper:,.0f} "
                f"| EUR {seg.amount_at_lower:,.2f}/mnd | EUR {seg.amount_at_upper:,.2f}/mnd |"
            )

    if model.child_supplement > 0:
        lines.extend(
            [
                "",
                "## Kindtoeslag",
                "",
                f"Per kind ontvangt u **EUR {model.child_supplement:.2f}** extra per maand.",
            ]
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "*Het uiteindelijke bedrag is minimaal EUR 0 per maand.*",
        ]
    )

    return "\n".join(lines)


def _generate_parametric_explanation(model, selected_laws: list[str]) -> str:
    """Generate Dutch explanation for parametric model."""
    law_names = [AVAILABLE_LAWS.get(l, {}).get("label", l) for l in selected_laws]
    laws_text = ", ".join(law_names[:-1]) + " en " + law_names[-1] if len(law_names) > 1 else law_names[0]

    lines = [
        "# Geharmoniseerde Toeslag — Vereenvoudigde formule",
        "",
        f"Uw toeslag combineert **{laws_text}** en bestaat uit {len(model.template.components)} onderdeel(en):",
        "",
        "---",
        "",
    ]

    for i, comp in enumerate(model.template.components, 1):
        label = AVAILABLE_LAWS.get(comp.name, {}).get("label", comp.name)
        lines.append(f"## {i}. {label}-component")
        lines.append("")

        if comp.has_partner_variant:
            lines.append("**Alleenstaand:**")
            lines.append(f"- Basisbedrag: EUR {comp.base_single:.2f}/maand")
            lines.append(f"- Afbouw: {comp.rate_single:.1%} van inkomen boven EUR {comp.threshold_single:,.0f}")
            lines.append("")
            lines.append("**Met partner:**")
            lines.append(f"- Basisbedrag: EUR {comp.base_partner:.2f}/maand")
            lines.append(f"- Afbouw: {comp.rate_partner:.1%} van inkomen boven EUR {comp.threshold_partner:,.0f}")
        else:
            lines.append(f"- Basisbedrag: EUR {comp.base_single:.2f}/maand")
            lines.append(f"- Afbouw: {comp.rate_single:.1%} van inkomen boven EUR {comp.threshold_single:,.0f}")

        lines.append("")
        lines.append("*Formule: max(EUR 0, basisbedrag - afbouw% x max(EUR 0, inkomen - drempelinkomen))*")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Totaal",
            "",
            "Uw toeslag = som van alle componenten (minimaal EUR 0/maand)",
        ]
    )

    return "\n".join(lines)


def run_train(params: dict) -> dict:
    """Route to the appropriate training method."""
    method = params.get("method", "tree")
    selected_laws = params.get("selected_laws", DEFAULT_SELECTED_LAWS)

    if method == "tree":
        return run_train_tree(params, selected_laws)
    elif method == "bracket":
        return run_train_bracket(params, selected_laws)
    elif method == "parametric":
        return run_train_parametric(params, selected_laws)
    else:
        return {"status": "error", "message": f"Unknown method: {method}"}


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
    selected_laws = params.get("selected_laws", DEFAULT_SELECTED_LAWS)
    synthesis_df = simulator.export_for_synthesis(results_df, selected_laws=selected_laws)

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
