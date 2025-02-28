import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip("More advanced tests requiring fixture setup")
def test_application_panel(page: Page):
    """
    Single test to verify the basic functionality of the application panel.

    The test:
    1. Opens the main page
    2. Finds a tile with an "aanvragen" button
    3. Clicks the button to open the panel
    4. Verifies the panel appears
    5. Interacts with the panel elements
    6. Closes the panel using ESC key
    """
    # Navigate to homepage
    page.goto("http://0.0.0.0:8000", timeout=30000)

    # Wait for content to load
    page.wait_for_load_state("domcontentloaded")

    # Wait for tiles to appear
    tile_selector = "div[id^='tile-']"
    page.wait_for_selector(tile_selector, timeout=10000)

    # Find a tile with a button containing "aanvragen" text
    tiles = page.locator(tile_selector).all()
    assert len(tiles) > 0, "No tiles found on the page"

    # Find and click the correct button
    aanvragen_button = None
    for tile in tiles:
        buttons = tile.locator("button").all()
        for button in buttons:
            button_text = button.text_content()
            if button_text and "aanvragen" in button_text.lower():
                aanvragen_button = button
                break
        if aanvragen_button:
            break

    assert aanvragen_button, "No button with 'aanvragen' text found"

    # Click the button to open the panel
    aanvragen_button.click()

    # Wait for panel to appear and become visible
    panel = page.wait_for_selector("#application-panel", timeout=15000)
    assert panel.is_visible(), "Panel should be visible"

    # Test interacting with the panel

    # 1. Check that the close button exists
    close_button = panel.locator("button svg path[d*='M6 18L18 6M6 6l12 12']")
    assert close_button.is_visible(), "Close button should be visible"

    # 2. Toggle the explanation section
    explanation_toggle = page.locator("button >> text=Uitleg")
    explanation_toggle.click()

    explanation_content = page.locator("#explanation-content")
    expect(explanation_content).to_be_visible()

    # 3. Toggle it back
    explanation_toggle.click()

    # 4. Check the declaration checkbox
    declaration_checkbox = page.locator("#declaration-checkbox")
    declaration_checkbox.check()

    # 5. Verify the submit button is enabled
    submit_button = page.locator("button >> text=Bevestig aanvraag")
    expect(submit_button).not_to_be_disabled()

    # Close the panel with ESC key
    page.keyboard.press("Escape")

    # Wait for panel to disappear
    page.wait_for_timeout(1000)
    expect(panel).not_to_be_visible()
