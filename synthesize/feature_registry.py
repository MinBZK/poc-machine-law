"""
Feature Registry for Law Synthesis

Maps simulation features to YAML law input fields and tracks which features
each law requires. Used to dynamically select relevant features for synthesis
and warn when essential features are unavailable.
"""

from dataclasses import dataclass


@dataclass
class FeatureSpec:
    """Specification for a synthesis feature."""

    sim_column: str  # Column name in simulation results_df
    display_name: str  # Human-readable Dutch name
    yaml_inputs: list[str]  # YAML input field names this maps to
    laws: list[str]  # Which laws need this feature
    is_grouping: bool = False  # Can be used to segment (bracket model)
    is_continuous: bool = False  # Continuous numeric feature
    discretize_laws: list[str] | None = (
        None  # Laws where this feature has a hard threshold (eligible for auto-discretization)
    )
    available: bool = True  # Available in current simulation


# All features available in the simulation that are relevant for synthesis
FEATURE_REGISTRY: list[FeatureSpec] = [
    FeatureSpec(
        sim_column="income",
        display_name="Inkomen",
        yaml_inputs=["INKOMEN", "TOETSINGSINKOMEN"],
        laws=["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand", "aow", "ww", "kinderopvangtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="age",
        display_name="Leeftijd",
        yaml_inputs=["LEEFTIJD"],
        laws=["zorgtoeslag", "huurtoeslag", "bijstand", "aow", "ww"],
        is_continuous=True,
        discretize_laws=["aow", "bijstand", "ww"],  # Only these have hard age thresholds
    ),
    FeatureSpec(
        sim_column="has_partner",
        display_name="Heeft partner",
        yaml_inputs=["HEEFT_PARTNER"],
        laws=["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand", "aow"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="has_children",
        display_name="Heeft kinderen",
        yaml_inputs=["KINDEREN"],
        laws=["huurtoeslag", "kindgebonden_budget", "kinderopvangtoeslag"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="children_count",
        display_name="Aantal kinderen",
        yaml_inputs=["AANTAL_KINDEREN"],
        laws=["kindgebonden_budget", "kinderopvangtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="youngest_child_age",
        display_name="Leeftijd jongste kind",
        yaml_inputs=["KINDEREN_LEEFTIJDEN"],
        laws=["kindgebonden_budget"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="housing_type",
        display_name="Woonsituatie",
        yaml_inputs=["HUURPRIJS"],
        laws=["huurtoeslag"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="rent_amount",
        display_name="Huurprijs",
        yaml_inputs=["HUURPRIJS"],
        laws=["huurtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="net_worth",
        display_name="Vermogen",
        yaml_inputs=["VERMOGEN", "BEZITTINGEN"],
        laws=["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand"],
        is_continuous=True,
        discretize_laws=["zorgtoeslag", "huurtoeslag", "kindgebonden_budget", "bijstand"],  # All have asset thresholds
    ),
    FeatureSpec(
        sim_column="is_student",
        display_name="Is student",
        yaml_inputs=["IS_STUDENT"],
        laws=["bijstand"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="work_years",
        display_name="Arbeidsjaren",
        yaml_inputs=["WERKZAME_VERZEKERDE_JAREN", "ARBEIDSVERLEDEN_JAREN"],
        laws=["aow", "ww"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="has_dutch_nationality",
        display_name="Nederlandse nationaliteit",
        yaml_inputs=["HEEFT_NEDERLANDSE_NATIONALITEIT"],
        laws=["bijstand", "ww"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="is_detained",
        display_name="Is gedetineerd",
        yaml_inputs=["IS_GEDETINEERDE", "IS_GEDETINEERD"],
        laws=["bijstand", "ww"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="standaardpremie",
        display_name="Standaardpremie",
        yaml_inputs=["STANDAARDPREMIE"],
        laws=["zorgtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="is_health_insured",
        display_name="Zorgverzekerd",
        yaml_inputs=["IS_VERZEKERDE"],
        laws=["zorgtoeslag"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="receives_child_benefit",
        display_name="Ontvangt kinderbijslag",
        yaml_inputs=["ONTVANGT_KINDERBIJSLAG"],
        laws=["kindgebonden_budget"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="receives_study_financing",
        display_name="Ontvangt studiefinanciering",
        yaml_inputs=["ONTVANGT_STUDIEFINANCIERING"],
        laws=["bijstand"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="business_income",
        display_name="Bedrijfsinkomen",
        yaml_inputs=["BEDRIJFSINKOMEN"],
        laws=["bijstand"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="work_hours_per_week",
        display_name="Werkuren per week",
        yaml_inputs=["GEWERKTE_UREN", "GEMIDDELD_ARBEIDSUREN_PER_WEEK"],
        laws=["ww", "kinderopvangtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="childcare_hours_per_child",
        display_name="Opvanguren per kind",
        yaml_inputs=["AANGEGEVEN_UREN"],
        laws=["kinderopvangtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="childcare_hourly_rate",
        display_name="Uurtarief opvang",
        yaml_inputs=["UURTARIEF"],
        laws=["kinderopvangtoeslag"],
        is_continuous=True,
    ),
    FeatureSpec(
        sim_column="childcare_type",
        display_name="Soort opvang",
        yaml_inputs=["SOORT_OPVANG"],
        laws=["kinderopvangtoeslag"],
        is_grouping=True,
    ),
    # --- Business / ondernemer features ---
    FeatureSpec(
        sim_column="leeftijd_leidinggevende",
        display_name="Leeftijd leidinggevende",
        yaml_inputs=["LEEFTIJD_LEIDINGGEVENDE"],
        laws=["alcoholwet"],
        is_continuous=True,
        discretize_laws=["alcoholwet"],
    ),
    FeatureSpec(
        sim_column="vloeroppervlakte",
        display_name="Vloeroppervlakte (m²)",
        yaml_inputs=["VLOEROPPERVLAKTE"],
        laws=["alcoholwet"],
        is_continuous=True,
        discretize_laws=["alcoholwet"],
    ),
    FeatureSpec(
        sim_column="type_bedrijf_horeca",
        display_name="Horecabedrijf",
        yaml_inputs=["TYPE_BEDRIJF"],
        laws=["alcoholwet"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="is_onder_curatele",
        display_name="Onder curatele",
        yaml_inputs=["IS_ONDER_CURATELE"],
        laws=["alcoholwet"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="sbi_is_food",
        display_name="SBI-code levensmiddelen",
        yaml_inputs=["SBI_CODE"],
        laws=["haccp"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="bereidt_of_serveert_voedsel",
        display_name="Bereidt/serveert voedsel",
        yaml_inputs=["BEREIDT_OF_SERVEERT_VOEDSEL"],
        laws=["haccp"],
        is_grouping=True,
    ),
    FeatureSpec(
        sim_column="jaarlijks_elektriciteitsverbruik_kwh",
        display_name="Elektriciteitsverbruik (kWh/jaar)",
        yaml_inputs=["JAARLIJKS_ELEKTRICITEITSVERBRUIK"],
        laws=["energie_informatieplicht"],
        is_continuous=True,
        discretize_laws=["energie_informatieplicht"],
    ),
    FeatureSpec(
        sim_column="jaarlijks_gasverbruik_m3",
        display_name="Gasverbruik (m³/jaar)",
        yaml_inputs=["JAARLIJKS_GASVERBRUIK"],
        laws=["energie_informatieplicht"],
        is_continuous=True,
        discretize_laws=["energie_informatieplicht"],
    ),
    FeatureSpec(
        sim_column="is_woonfunctie",
        display_name="Woonfunctie",
        yaml_inputs=["IS_WOONFUNCTIE"],
        laws=["energie_informatieplicht"],
        is_grouping=True,
    ),
]


def get_features_for_laws(selected_laws: list[str]) -> list[FeatureSpec]:
    """Get all relevant features for the selected laws."""
    return [f for f in FEATURE_REGISTRY if any(law in f.laws for law in selected_laws)]


def get_grouping_features_for_laws(selected_laws: list[str]) -> list[str]:
    """Get grouping feature column names for the bracket model."""
    features = get_features_for_laws(selected_laws)
    return [f.sim_column for f in features if f.is_grouping]


def get_continuous_features_for_laws(selected_laws: list[str]) -> list[str]:
    """Get continuous feature column names eligible for auto-discretization.

    Only returns features that have explicit discretize_laws matching
    the selected laws. This prevents spurious splits (e.g. age split
    at 55 when only zorgtoeslag/huurtoeslag are selected).
    """
    features = get_features_for_laws(selected_laws)
    return [
        f.sim_column
        for f in features
        if f.is_continuous
        and f.sim_column != "income"
        and f.discretize_laws
        and any(law in f.discretize_laws for law in selected_laws)
    ]


def get_all_feature_columns_for_laws(selected_laws: list[str]) -> list[str]:
    """Get all feature column names needed for the selected laws."""
    features = get_features_for_laws(selected_laws)
    return [f.sim_column for f in features]


def get_missing_features_for_law(law: str) -> list[str]:
    """Get display names of features that a law needs but aren't available in simulation."""
    # These YAML inputs have no simulation equivalent yet
    unavailable_inputs = {
        "PARTNER_GEWERKTE_UREN": "Gewerkte uren partner",
    }

    # Map law to its missing YAML inputs
    law_missing: dict[str, list[str]] = {
        "kinderopvangtoeslag": ["PARTNER_GEWERKTE_UREN"],
    }

    missing_inputs = law_missing.get(law, [])
    return [unavailable_inputs[inp] for inp in missing_inputs if inp in unavailable_inputs]


def get_feature_warnings(selected_laws: list[str]) -> list[dict]:
    """Get warnings for laws with missing features.

    Returns list of {"law": str, "missing": list[str]} dicts.
    """
    warnings = []
    for law in selected_laws:
        missing = get_missing_features_for_law(law)
        if missing:
            warnings.append({"law": law, "missing": missing})
    return warnings
