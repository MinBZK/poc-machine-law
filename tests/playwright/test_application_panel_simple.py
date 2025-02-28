from playwright.sync_api import Page


def test_tile_click_opens_panel(page: Page):
    """Test that clicking on a tile opens the application panel."""
    try:
        # Navigate to homepage
        print("Navigating to homepage...")
        page.goto("http://0.0.0.0:8000", timeout=30000)

        # Wait for content to load
        print("Waiting for content to load...")
        page.wait_for_load_state("domcontentloaded")

        # Wait for the first tile to appear
        print("Waiting for tiles to appear...")
        tile_selector = "div[id^='tile-']"
        page.wait_for_selector(tile_selector, timeout=10000)

        # Take screenshot before clicking
        page.screenshot(path="/tmp/before_click.png")
        print("Screenshot saved to /tmp/before_click.png")

        # Find a tile with a button containing "aanvragen" text
        print("Finding tiles...")
        tiles = page.locator(tile_selector).all()
        print(f"Found {len(tiles)} tiles")

        if len(tiles) == 0:
            raise Exception("No tiles found on the page")

        aanvragen_button = None

        # Find a tile with a button containing "aanvragen"
        print("Looking for a button with 'aanvragen' text...")
        for i, tile in enumerate(tiles):
            buttons = tile.locator("button").all()
            for button in buttons:
                button_text = button.text_content()
                if button_text and "aanvragen" in button_text.lower():
                    print(f"Found button with 'aanvragen' in tile #{i + 1}")
                    aanvragen_button = button
                    break
            if aanvragen_button:
                break

        # If found, click the button
        if aanvragen_button:
            print("Clicking the 'aanvragen' button...")
            # Take a screenshot of the button for verification
            page.screenshot(path="/tmp/aanvragen_button.png")
            aanvragen_button.click()
        else:
            # Fallback to any button in any tile
            print("No 'aanvragen' button found, looking for any button...")
            for tile in tiles:
                buttons = tile.locator("button").all()
                if buttons:
                    print(f"Found a tile with {len(buttons)} buttons, clicking the last one...")
                    buttons[-1].click()
                    break
            else:
                print("No buttons found in any tile")
                raise Exception("No buttons found in any tile")

        # Wait for panel to appear
        print("Waiting for application panel...")
        panel = None

        # Give the UI time to update
        page.wait_for_timeout(1000)

        # Take a screenshot immediately after clicking
        page.screenshot(path="/tmp/after_click.png")
        print("Screenshot saved to /tmp/after_click.png")

        # Search for the panel by different methods
        # Method 1: Try waiting for panel with transform completed
        try:
            print("Method 1: Waiting for panel with transform completed...")
            # Wait for panel element to be in the DOM and visible
            panel_selector = "#application-panel > div:not([x-transition\\:enter-start])"
            panel = page.wait_for_selector(panel_selector, timeout=10000)
            print("Panel found!")
            # Take success screenshot
            page.screenshot(path="/tmp/method1_success.png")
            assert panel.is_visible(), "Panel should be visible (Method 1)"
            print("Method 1 succeeded! Panel is visible.")
            print("Test completed successfully!")
            # Don't return, just let the test complete successfully
        except Exception as e:
            print(f"Method 1 failed: {e}")

        # Method 2: Wait for any element in the panel to be visible
        try:
            print("Method 2: Waiting for elements inside the panel...")
            close_button = page.wait_for_selector(
                "#application-panel button svg path[d*='M6 18L18 6M6 6l12 12']", timeout=10000
            )
            print("Close button found in panel!")
            # Take success screenshot
            page.screenshot(path="/tmp/method2_success.png")
            assert close_button.is_visible(), "Close button should be visible (Method 2)"
            print("Method 2 succeeded! Close button is visible.")
            print("Test completed successfully!")
            return
        except Exception as e:
            print(f"Method 2 failed: {e}")

        # Method 3: Manual approach with timeout
        try:
            print("Method 3: Manual wait approach...")
            # Wait 3 seconds for animation to complete
            page.wait_for_timeout(3000)

            panel = page.locator("#application-panel")
            is_visible = panel.is_visible()
            print(f"Panel visible after timeout: {is_visible}")

            if is_visible:
                print("Panel is visible after timeout!")
                # Take success screenshot
                page.screenshot(path="/tmp/method3_success.png")
                assert is_visible, "Panel should be visible (Method 3)"
                print("Method 3 succeeded! Panel is visible after timeout.")
                print("Test completed successfully!")
                return
        except Exception as e:
            print(f"Method 3 failed: {e}")

        # Method 4: Evaluate visibility via JavaScript
        try:
            print("Method 4: Using JavaScript visibility check...")
            is_visible_js = page.evaluate("""() => {
                const panel = document.querySelector('#application-panel');
                if (!panel) return false;
                const style = window.getComputedStyle(panel);
                const isVisible = style.display !== 'none' &&
                                  style.visibility !== 'hidden' &&
                                  style.opacity !== '0';
                return isVisible;
            }""")

            print(f"JS visibility check result: {is_visible_js}")
            if is_visible_js:
                print("Panel is visible according to JavaScript!")
                # Take success screenshot
                page.screenshot(path="/tmp/method4_success.png")
                assert is_visible_js, "Panel should be visible (Method 4)"
                print("Method 4 succeeded! Panel is visible according to JavaScript.")
                print("Test completed successfully!")
                return
        except Exception as e:
            print(f"Method 4 failed: {e}")

        # Take screenshot showing the current state
        page.screenshot(path="/tmp/panel_not_visible.png")
        print("Screenshot saved to /tmp/panel_not_visible.png")

        # Gather debug info
        print("Debug: Checking HTML structure...")
        html = page.content()
        if "application-panel" in html:
            print("Panel element exists in the HTML")
        else:
            print("Panel element not found in HTML!")

        # Final assertion
        print("Could not verify panel visibility")
        raise Exception("Application panel did not become visible")

    except Exception as e:
        # Log any errors
        print(f"Error during test: {e}")
        try:
            page.screenshot(path="/tmp/error.png")
            print("Error screenshot saved to /tmp/error.png")
        except:
            print("Could not take error screenshot")
        raise
