import locale
import uuid
from datetime import date, datetime
from pathlib import Path

from config_loader import ConfigLoader
from engines import CaseManagerInterface, ClaimManagerInterface, EngineInterface
from engines.factory import CaseManagerFactory, ClaimManagerFactory, MachineFactory
from fastapi import Request
from fastapi.templating import Jinja2Templates

# Load configuration
config_loader = ConfigLoader()

# Generate a unique server instance ID at startup
# This is used to detect stale sessions from previous server runs
SERVER_INSTANCE_ID = str(uuid.uuid4())

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


def get_zaken_case_manager():
    """Dependency to get CaseManager instance for toeslag/zaken workflows"""
    return machine_service.get_services().case_manager


def get_message_manager():
    """Dependency to get MessageManager instance for berichten"""
    return machine_service.get_services().message_manager


def get_simulated_date(request: Request, auto_reset: bool = True) -> date:
    """Get the current simulated date from session, defaults to today.

    Auto-resets to today when:
    - The server has restarted (session from previous server instance)
    - The stored date is more than 5 years in the future (stale data)

    This ensures that after a server restart, everyone starts fresh with today's date.
    """
    today = date.today()

    # Check if session is from current server instance
    session_server_id = request.session.get("server_instance_id")
    if session_server_id != SERVER_INSTANCE_ID:
        # Session is from a previous server run - reset to today
        request.session["simulated_date"] = today.isoformat()
        request.session["server_instance_id"] = SERVER_INSTANCE_ID
        return today

    date_str = request.session.get("simulated_date")
    if date_str:
        stored_date = date.fromisoformat(date_str)
        # Reset if date is unreasonably far in the future (stale session)
        # Use 5 years as threshold - more than that is likely stale
        if auto_reset and stored_date > today.replace(year=today.year + 5):
            request.session["simulated_date"] = today.isoformat()
            return today
        return stored_date
    return today


def set_simulated_date(request: Request, new_date: date) -> None:
    """Store the simulated date in session along with the server instance ID"""
    request.session["simulated_date"] = new_date.isoformat()
    request.session["server_instance_id"] = SERVER_INSTANCE_ID


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
        try:
            return locale.currency(value, grouping=True).replace("Eu", "€")
        except (ValueError, locale.Error):
            # Fallback to manual formatting if locale doesn't support currency formatting
            # Format with Dutch conventions: . for thousands, , for decimals
            sign = "-" if value < 0 else ""
            abs_value = abs(value)
            # Format with 2 decimals
            formatted = f"{abs_value:,.2f}"
            # Replace , with temporary marker, . with ,, marker with .
            formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
            return f"{sign}€ {formatted}"

    templates.env.filters["format_currency"] = format_currency

    return templates


templates = setup_jinja_env(str(TEMPLATES_DIR))
