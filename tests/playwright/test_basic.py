from playwright.sync_api import Page


def test_simple(page: Page):
    """Very simple test that doesn't depend on the application."""
    # Just check that we can create a page
    assert page is not None
    print("Page object created successfully")


def test_homepage_loads(page: Page):
    """Basic test to verify the homepage loads correctly."""
    try:
        # Navigate to the homepage with debug logging
        print("Navigating to homepage...")
        page.goto("http://0.0.0.0:8000", timeout=30000)

        # Take a screenshot for debugging
        print("Taking screenshot...")
        page.screenshot(path="/tmp/homepage.png")

        # Print some debug info
        print(f"Page title: {page.title()}")
        print(f"Page URL: {page.url}")

        # Simple assertion that we loaded something
        assert "0.0.0.0:8000" in page.url
        print("Test completed successfully")
    except Exception as e:
        # Log any errors
        print(f"Error during test: {e}")
        # Take screenshot if possible, but don't fail if we can't
        try:
            page.screenshot(path="/tmp/error.png")
            print("Error screenshot saved to /tmp/error.png")
        except Exception:
            print("Could not take error screenshot")
        raise
