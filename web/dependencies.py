import locale
from datetime import datetime
from pathlib import Path

from config_loader import ConfigLoader
from engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from engines.factory import CaseManagerFactory, ClaimManagerFactory, MachineFactory
from fastapi.templating import Jinja2Templates

# Load configuration
config_loader = ConfigLoader()

# Set Dutch locale
try:
    locale.setlocale(locale.LC_ALL, "nl_NL.UTF-8")
    locale.setlocale(
        locale.LC_MONETARY, "it_IT.UTF-8"
    )  # Use Italian locale for monetary formatting, which is similar to Dutch but has better thousand separators and places the minus sign correctly
except locale.Error:
    # Fallback for CI environments where Dutch locale might not be installed
    try:
        locale.setlocale(locale.LC_ALL, "nl_NL")
        locale.setlocale(locale.LC_MONETARY, "it_IT")  # See comment above
    except locale.Error:
        try:
            # Try C.UTF-8 which is often available in Docker/CI
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            # If all else fails, use system default
            locale.setlocale(locale.LC_ALL, "")
            print("WARNING: Could not set Dutch locale, using system default")

TODAY = datetime.today().strftime("%Y-%m-%d")
try:
    FORMATTED_DATE = datetime.today().strftime("%-d %B %Y")
except ValueError:
    # Windows uses %#d instead of %-d
    FORMATTED_DATE = datetime.today().strftime("%d %B %Y")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def get_case_manager() -> CaseManagerInterface:
    """Dependency to get CaseManager instance"""
    return case_manager


def get_claim_manager() -> ClaimManagerInterface:
    """Dependency to get ClaimManager instance"""
    return claim_manager


def get_machine_service() -> EngineInterface:
    """Dependency to get EngineInterface instance"""
    return machine_service


def set_engine_id(id: str):
    global engine_id
    global case_manager
    global machine_service
    global claim_manager
    engine_id = id

    # Create case manager based on configuration
    case_manager = CaseManagerFactory.create_case_manager(engine_id=engine_id)

    # Create machine service based on configuration
    machine_service = MachineFactory.create_machine_service(engine_id=engine_id)

    # Create machine service based on configuration
    claim_manager = ClaimManagerFactory.create_claim_manager(engine_id=engine_id)


engine = config_loader.config.get_default_engine()
if engine is None:
    raise ValueError("Default engine not set")

set_engine_id(engine.id)


def get_engine_id() -> str:
    return engine_id


def setup_jinja_env(directory: str) -> Jinja2Templates:
    templates = Jinja2Templates(directory=directory)

    def format_date(date_str: str) -> str:
        if not date_str:
            return ""

        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        elif isinstance(date_str, datetime):
            date_obj = date_str

        try:
            return date_obj.strftime("%-d %B %Y")
        except ValueError:
            return date_obj.strftime("%d %B %Y")

    templates.env.filters["format_date"] = format_date

    def format_currency(value: float) -> str:
        """Format a number as currency with locale settings."""
        if value is None:
            return ""

        # Use locale.currency for proper formatting. Note: on some systems, the locale definitions use 'Eu' as the currency symbol instead of the actual euro sign €, so we replace it
        return locale.currency(value, grouping=True).replace("Eu", "€")

    templates.env.filters["format_currency"] = format_currency

    def get_yaml_explanation(yaml_explanations: dict, file_path: str, section_path: str) -> str:
        """Get explanation from loaded YAML content"""
        if not yaml_explanations or file_path not in yaml_explanations:
            return ""

        yaml_content = yaml_explanations[file_path]
        parts = section_path.split(".")
        current = yaml_content

        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list):
                    idx = int(part)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return ""
                else:
                    return ""

            # Extract explanation from legal_basis
            if isinstance(current, dict) and "legal_basis" in current:
                return current["legal_basis"].get("explanation", "")
            elif isinstance(current, dict) and "explanation" in current:
                return current.get("explanation", "")

            return ""
        except Exception:
            return ""

    templates.env.filters["get_yaml_explanation"] = get_yaml_explanation

    return templates


templates = setup_jinja_env(str(TEMPLATES_DIR))
