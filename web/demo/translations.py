"""Translations for the demo interface (NL/EN)."""

from typing import Any

TRANSLATIONS: dict[str, dict[str, str]] = {
    "nl": {
        # Nav / Tabs
        "nav_presentation": "Presentatie",
        "nav_laws": "Wetten",
        "nav_graph": "Graaf analyse",
        "nav_scenarios": "Scenarios",
        "nav_simulation": "Simulatie",
        "nav_harmonize": "Harmonisatie",
        "nav_zaaksysteem": "Zaaksysteem",
        "nav_features": "Features",
        "nav_overheidnl": "Overheid.nl",
        # Header / brand
        "brand_title": "RegelRecht Demo Mode",
        "brand_subtitle": "Machine-uitvoerbaar Nederlands recht",
        # Menu
        "menu_demo_profile": "Demo Profiel",
        "menu_feature_flags": "Feature Flags",
        "menu_fullscreen": "Volledig scherm",
        "menu_exit_fullscreen": "Volledig scherm verlaten",
        "menu_dark_mode": "Donkere modus",
        "menu_light_mode": "Lichte modus",
        "menu_admin": "Admin",
        "menu_reset_state": "Reset state",
        "menu_resetting": "Bezig met resetten\u2026",
        "menu_language": "English",
        "menu_language_flag": "\U0001f1ec\U0001f1e7",
        # Presentation slides
        "slide_title": "RegelRecht",
        "slide_subtitle": "van wet naar digitale werking",
        "slide_presenter_placeholder": "[dubbelklik voor naam]",
        "slide_presenter_input_placeholder": "Uw naam",
        "slide_org": "Bureau Architectuur, BZK",
        "slide2_title": "Huidige Situatie",
        "slide2_line1": "Iedere organisatie",
        "slide2_line2_pre": "heeft een ",
        "slide2_line2_bold": "eigen interpretatie",
        "slide2_line2_post": " van de wet",
        "slide2_line3_pre": "die landt in ",
        "slide2_line3_bold": "eigen software",
        "slide2_line3_post": "",
        "slide3_title": "Het gevolg",
        "slide3_line1": "Geen overzicht",
        "slide3_line2": "Onvoorspelbaar",
        "slide3_line3": "Onbeheersbaar",
        "slide4_title": "Wat als",
        "slide4_line1_pre": "We ",
        "slide4_line1_bold": "beginnen met de wet",
        "slide4_line1_post": "",
        "slide4_line2_pre": "Deze ",
        "slide4_line2_bold": "machine uitvoerbaar",
        "slide4_line2_post": " maken",
        "slide4_line3_pre": "",
        "slide4_line3_bold": "Openbaar",
        "slide4_line3_post": " publiceren",
        "slide5_title": "Demo RegelRecht",
        "slide5_disclaimer1": "Proof of concept",
        "slide5_disclaimer2": "Compleet verhaal, geen eindproduct",
        "slide5_disclaimer3": "We maken beleid door te doen",
        # Law viewer
        "law_available_laws": "Beschikbare Wetten",
        "law_search_placeholder": "Zoek wetten...",
        "law_valid_from": "Geldig vanaf:",
        "law_collapse_all": "Alles inklappen",
        "law_breadcrumb_laws": "Wetten",
        "law_goto": "Ga naar",
        # Feature viewer
        "feature_files": "Feature Bestanden",
        "feature_search_placeholder": "Zoek features...",
        "feature_expand_all": "Alles uitklappen",
        "feature_collapse_all": "Alles inklappen",
        "feature_test_output": "Test Output",
        "feature_clear": "Wissen",
        "feature_output_placeholder": "Voer een scenario uit om de output hier te zien...",
        "feature_run": "Uitvoeren \u25b6",
        "feature_hidden_notice": "Let op: {n} scenario(s) verborgen (vereisen browser/UI setup)",
        "feature_scenario_count": "{n} scenario's",
        # Status messages (JS)
        "status_running_scenario": "Scenario wordt uitgevoerd...",
        "status_running_all": "Alle scenario's worden uitgevoerd...",
        "status_passed": "Geslaagd",
        "status_failed": "Mislukt",
        "status_running": "Bezig...",
        # Misc workspace
        "close_tab": "Sluiten",
        "clear_all_law_tabs": "Alles wissen",
        "close_all_law_tabs_confirm": "Alle wetten-tabs sluiten?",
        # Index page
        "welcome_title": "Welkom bij Machine Law Demo Mode",
        "welcome_description": "Selecteer een wet uit de zijbalk om de machine-uitvoerbare specificatie te bekijken.",
        "card_yaml_title": "YAML Wetten Bestanden",
        "card_yaml_desc": "Bekijk en verken machine-leesbare wet specificaties met inklapbare secties.",
        "card_crossref_title": "Kruisverwijzingen",
        "card_crossref_desc": "Navigeer tussen wetten met automatische link detectie voor service referenties.",
        "card_tests_title": "Feature Tests",
        "card_tests_desc": "Voer Gherkin feature tests uit om wet implementaties te verifi\u00ebren.",
        "quick_start_title": "Snel Beginnen",
        "quick_start_1_pre": "Klik op ",
        "quick_start_1_bold": "Zorgtoeslag",
        "quick_start_1_post": " in de zijbalk om de zorgtoeslag wet te bekijken",
        "quick_start_2": "Gebruik het zoekveld om snel specifieke wetten te vinden",
        "quick_start_3_pre": "Navigeer naar de ",
        "quick_start_3_link": "Features",
        "quick_start_3_post": " tab om tests uit te voeren",
        # Features list page
        "features_list_title": "Feature Files",
        "features_list_intro": "Selecteer een feature bestand uit de zijbalk om scenario's te bekijken en uit te voeren.",
    },
    "en": {
        # Nav / Tabs
        "nav_presentation": "Presentation",
        "nav_laws": "Laws",
        "nav_graph": "Graph Analysis",
        "nav_scenarios": "Scenarios",
        "nav_simulation": "Simulation",
        "nav_harmonize": "Harmonization",
        "nav_zaaksysteem": "Case System",
        "nav_features": "Features",
        "nav_overheidnl": "Government Portal",
        # Header / brand
        "brand_title": "RegelRecht Demo Mode",
        "brand_subtitle": "Machine-executable Dutch law",
        # Menu
        "menu_demo_profile": "Demo Profile",
        "menu_feature_flags": "Feature Flags",
        "menu_fullscreen": "Full screen",
        "menu_exit_fullscreen": "Exit full screen",
        "menu_dark_mode": "Dark mode",
        "menu_light_mode": "Light mode",
        "menu_admin": "Admin",
        "menu_reset_state": "Reset state",
        "menu_resetting": "Resetting\u2026",
        "menu_language": "Nederlands",
        "menu_language_flag": "\U0001f1f3\U0001f1f1",
        # Presentation slides
        "slide_title": "RegelRecht",
        "slide_subtitle": "from law to digital execution",
        "slide_presenter_placeholder": "[double-click for name]",
        "slide_presenter_input_placeholder": "Your name",
        "slide_org": "Bureau Architectuur, BZK",
        "slide2_title": "Current Situation",
        "slide2_line1": "Every organization",
        "slide2_line2_pre": "has its ",
        "slide2_line2_bold": "own interpretation",
        "slide2_line2_post": " of the law",
        "slide2_line3_pre": "which ends up in ",
        "slide2_line3_bold": "its own software",
        "slide2_line3_post": "",
        "slide3_title": "The Consequence",
        "slide3_line1": "No overview",
        "slide3_line2": "Unpredictable",
        "slide3_line3": "Unmanageable",
        "slide4_title": "What if",
        "slide4_line1_pre": "We ",
        "slide4_line1_bold": "start from the law",
        "slide4_line1_post": "",
        "slide4_line2_pre": "Make it ",
        "slide4_line2_bold": "machine executable",
        "slide4_line2_post": "",
        "slide4_line3_pre": "Publish it ",
        "slide4_line3_bold": "openly",
        "slide4_line3_post": "",
        "slide5_title": "Demo RegelRecht",
        "slide5_disclaimer1": "Proof of concept",
        "slide5_disclaimer2": "Complete story, not a final product",
        "slide5_disclaimer3": "We shape policy by doing",
        # Law viewer
        "law_available_laws": "Available Laws",
        "law_search_placeholder": "Search laws...",
        "law_valid_from": "Valid from:",
        "law_collapse_all": "Collapse all",
        "law_breadcrumb_laws": "Laws",
        "law_goto": "Go to",
        # Feature viewer
        "feature_files": "Feature Files",
        "feature_search_placeholder": "Search features...",
        "feature_expand_all": "Expand all",
        "feature_collapse_all": "Collapse all",
        "feature_test_output": "Test Output",
        "feature_clear": "Clear",
        "feature_output_placeholder": "Run a scenario to see output here...",
        "feature_run": "Run \u25b6",
        "feature_hidden_notice": "Note: {n} scenario(s) hidden (require browser/UI setup)",
        "feature_scenario_count": "{n} scenarios",
        # Status messages (JS)
        "status_running_scenario": "Running scenario...",
        "status_running_all": "Running all scenarios...",
        "status_passed": "Passed",
        "status_failed": "Failed",
        "status_running": "Running...",
        # Misc workspace
        "close_tab": "Close",
        "clear_all_law_tabs": "Clear all",
        "close_all_law_tabs_confirm": "Close all law tabs?",
        # Index page
        "welcome_title": "Welcome to Machine Law Demo Mode",
        "welcome_description": "Select a law from the sidebar to view its machine-executable specification.",
        "card_yaml_title": "YAML Law Files",
        "card_yaml_desc": "View and explore machine-readable law specifications with collapsible sections.",
        "card_crossref_title": "Cross-references",
        "card_crossref_desc": "Navigate between laws with automatic link detection for service references.",
        "card_tests_title": "Feature Tests",
        "card_tests_desc": "Run Gherkin feature tests to verify law implementations.",
        "quick_start_title": "Quick Start",
        "quick_start_1_pre": "Click on ",
        "quick_start_1_bold": "Zorgtoeslag",
        "quick_start_1_post": " in the sidebar to view the healthcare allowance law",
        "quick_start_2": "Use the search field to quickly find specific laws",
        "quick_start_3_pre": "Navigate to the ",
        "quick_start_3_link": "Features",
        "quick_start_3_post": " tab to run tests",
        # Features list page
        "features_list_title": "Feature Files",
        "features_list_intro": "Select a feature file from the sidebar to view and run scenarios.",
    },
}


def get_translations(lang: str = "nl") -> dict[str, str]:
    """Get the full translation dict for a language.

    Args:
        lang: Language code ('nl' or 'en'). Defaults to 'nl'.

    Returns:
        Dict mapping translation keys to translated strings.
    """
    return TRANSLATIONS.get(lang, TRANSLATIONS["nl"])


def t(key: str, lang: str = "nl", **kwargs: Any) -> str:
    """Look up a single translation string with optional interpolation.

    Args:
        key: Translation key (e.g. 'nav_laws').
        lang: Language code ('nl' or 'en').
        **kwargs: Interpolation values (e.g. n=3 for '{n} scenarios').

    Returns:
        Translated string, or the key itself if not found.
    """
    translations = get_translations(lang)
    value = translations.get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value
