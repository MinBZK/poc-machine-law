from datetime import datetime

from machine.service import Services

TODAY = datetime.today().strftime("%Y-%m-%d")
FORMATTED_DATE = datetime.today().strftime("%-d %B %Y")


async def get_services():
    """Dependency to get Services instance"""
    return Services(TODAY)  # Use today's date
