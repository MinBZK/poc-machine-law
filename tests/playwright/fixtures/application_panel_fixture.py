import pytest
from playwright.sync_api import Page

from tests.playwright.pages.application_panel import ApplicationPanel


@pytest.fixture
def application_panel(page: Page) -> ApplicationPanel:
    """
    Fixture that provides an ApplicationPanel instance.

    This fixture:
    1. Loads the main dashboard
    2. Clicks on a tile to open the application panel
    3. Returns the ApplicationPanel page object
    """
    # The page is already loaded from the fixture

    # Wait for page content to be fully loaded with a longer timeout
    try:
        page.wait_for_selector(".bg-white", timeout=10000)

        # Debug info
        print("Found .bg-white element on the page")

        # Wait for tiles to be loaded, with retry logic
        tile_selector = "div[id^='tile-']"
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Wait for tiles with timeout
                page.wait_for_selector(tile_selector, timeout=5000)
                print(f"Found tiles on attempt {attempt + 1}")

                # Get all tiles and click the first one that's visible
                tiles = page.locator(tile_selector).all()
                if not tiles:
                    raise Exception("No tiles found on the page")

                print(f"Found {len(tiles)} tiles")
                for tile in tiles:
                    if tile.is_visible():
                        print("Clicking on visible tile")
                        tile.click()
                        break

                # Wait for panel to be visible
                page.wait_for_selector("#application-panel", timeout=10000)
                print("Application panel is visible")
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    # On last attempt, raise the exception
                    raise Exception(f"Failed to open application panel: {e}")
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                # Refresh the page and try again
                page.reload(wait_until="networkidle")
    except Exception as e:
        # Take a screenshot for debugging
        page.screenshot(path="/tmp/error_screenshot.png")
        print(f"ERROR: {e}")
        print("Screenshot saved to /tmp/error_screenshot.png")
        raise

    # Return the page object
    return ApplicationPanel(page)
