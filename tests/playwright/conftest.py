from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

# Constants
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Overrides the default browser context arguments."""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "record_video_dir": None,
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """Initialize Playwright for the entire test session."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright: Playwright, browser_name: str) -> Generator[Browser, None, None]:
    """Create a browser instance."""
    # Configure browser launch options
    launch_options = {
        "headless": True,
    }

    # Browser-specific arguments
    if browser_name in ["chromium", "firefox"]:
        # These options are only supported in Chromium and Firefox
        launch_options["args"] = ["--disable-dev-shm-usage", "--no-sandbox"]

    # Launch the browser with appropriate options
    browser = playwright[browser_name].launch(**launch_options)
    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser, browser_context_args: dict) -> Generator[BrowserContext, None, None]:
    """Create a new browser context for each test."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    """Create a new page for each test."""
    page = context.new_page()
    # Don't navigate to any URL by default, let the test do that
    return page
