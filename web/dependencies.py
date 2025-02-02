import locale
from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

from claims.application import ClaimsManager
from machine.service import Services

# Set Dutch locale
locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
TODAY = datetime.today().strftime("%Y-%m-%d")
FORMATTED_DATE = datetime.today().strftime("%-d %B %Y")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

manager = ClaimsManager()


async def get_services():
    """Dependency to get Services instance"""
    return Services(TODAY, manager)


def setup_jinja_env(directory: str) -> Jinja2Templates:
    templates = Jinja2Templates(directory=directory)

    def format_date(date_str: str) -> str:
        if not date_str:
            return ""

        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        elif isinstance(date_str, datetime):
            date_obj = date_str

        return date_obj.strftime("%-d %B %Y")

    templates.env.filters["format_date"] = format_date
    return templates


templates = setup_jinja_env(str(TEMPLATES_DIR))
