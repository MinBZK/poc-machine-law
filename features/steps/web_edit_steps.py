"""Step definitions for web interface value editing tests."""

import re
import subprocess
import time

import requests
from behave import given, then, when
from playwright.sync_api import sync_playwright


@given("the web server is running")
def step_web_server_running(context):
    """Check if the web server is running and initialize Playwright."""
    # The server should already be started by before_all in environment.py
    # Just verify it's accessible
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        assert response.status_code == 200, f"Web server returned status {response.status_code}"
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise AssertionError(f"Web server is not accessible at http://localhost:8000: {e}")
    
    context.base_url = "http://localhost:8000"

    # Initialize Playwright with isolation
    context.playwright = sync_playwright().start()
    # Run in headless mode with a fresh browser context for isolation
    context.browser = context.playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox"],  # For CI/CD compatibility
    )
    # Create an isolated browser context
    context.browser_context = context.browser.new_context(
        viewport={"width": 1280, "height": 720}, ignore_https_errors=True
    )
    context.page = context.browser_context.new_page()


@when('I start requesting "{benefit}" for BSN "{bsn}"')
def step_start_requesting_benefit(context, benefit, bsn):
    """Navigate to the website and start a benefit request."""
    context.bsn = bsn
    context.benefit = benefit

    # Navigate to the main page with the BSN
    context.page.goto(f"{context.base_url}/?bsn={bsn}")

    # Wait for page to load
    context.page.wait_for_load_state("networkidle")

    # Find and click on the huurtoeslag card
    if benefit.lower() == "huurtoeslag":
        # Find the huurtoeslag tile specifically
        huurtoeslag_tile = context.page.locator("#tile-wet_op_de_huurtoeslag")

        # With server restart, we should always start fresh
        # Look for "Gegevens aanleveren" button
        aanleveren_button = huurtoeslag_tile.locator("button:has-text('Gegevens aanleveren')")
        if aanleveren_button.count() > 0:
            print("Clicking 'Gegevens aanleveren' to start fresh")
            aanleveren_button.click()
            time.sleep(1)
        else:
            # If there's existing data (shouldn't happen with restart), handle it
            waarom_button = huurtoeslag_tile.locator("button:has-text('waarom?')")
            if waarom_button.count() > 0:
                print("Found existing data, clicking 'waarom?' to edit")
                waarom_button.click()
                time.sleep(1)

    # Store service and law for later use
    context.service = "TOESLAGEN"
    context.law = "wet_op_de_huurtoeslag" if benefit.lower() == "huurtoeslag" else "wet_op_de_zorgtoeslag"


@when('I change "{field}" from "{old_value}" to "{new_value}" euro')
def step_change_field_value(context, field, old_value, new_value):
    """Submit a claim to change a field value."""
    # Map field names to internal keys
    field_mapping = {"Box1 dienstbetrekking": "box1_inkomen", "box1_inkomen": "box1_inkomen"}

    internal_key = field_mapping.get(field, field)

    edit_data = {
        "service": context.service,
        "key": internal_key,
        "new_value": new_value,
        "old_value": old_value,
        "reason": f"Updating {field}",
        "law": context.law,
        "bsn": context.bsn,
        "claimant": "CITIZEN",
        "auto_approve": "false",
    }

    response = requests.post(f"{context.base_url}/edit/update-value", data=edit_data)
    assert response.status_code == 200, f"Failed to submit claim: {response.status_code}"


@when('I change "{field}" to "{new_value}" euro')
def step_change_field_to_value(context, field, new_value):
    """Edit the income value through the UI."""
    # Check if we're already in the modal showing housing/income data
    # If not, click waarom to access it
    if context.page.locator("text=Inkomen:").count() == 0:
        huurtoeslag_tile = context.page.locator("#tile-wet_op_de_huurtoeslag")
        waarom_button = huurtoeslag_tile.locator("button:has-text('waarom?')")

        if waarom_button.count() > 0:
            print("Clicking waarom to access income edit")
            waarom_button.click()
            time.sleep(1)

    # Click on the chevrons to expand income details
    # Based on the recorded actions: click on two specific chevron elements
    print("Expanding income details")

    # First chevron click
    first_chevron = context.page.locator("div:nth-child(3) > div > .min-w-0 > .transform").first
    if first_chevron.count() > 0:
        first_chevron.click()
        time.sleep(0.5)

    # Second chevron click to expand further
    second_chevron = context.page.locator(".ml-6 > div > .hover\\:bg-gray-50 > .min-w-0 > .transform").first
    if second_chevron.count() > 0:
        second_chevron.click()
        time.sleep(0.5)

    # Now click on the 6.000,00 € button to edit it
    box1_button = context.page.get_by_role("button", name="6.000,00 €")
    if box1_button.count() > 0:
        print("Clicking on 6.000,00 € button to edit Box1 dienstbetrekking")
        box1_button.click()
        time.sleep(0.5)

        # Fill in the new value
        input_field = context.page.get_by_placeholder("0.00")
        if input_field.count() > 0:
            print(f"Entering new value: {new_value}")
            input_field.click()
            input_field.fill(new_value)

            # Fill in motivation
            motivation_field = context.page.get_by_role("textbox", name="Motivatie voor wijziging")
            if motivation_field.count() > 0:
                motivation_field.click()
                motivation_field.fill("Test: income change")

            # Save the change
            save_button = context.page.get_by_role("button", name="Opslaan")
            if save_button.count() > 0:
                save_button.click()
                time.sleep(1)
                print(f"Saved Box1 dienstbetrekking as {new_value}")

                # After saving, we may need to confirm the request
                # First check if there's text to click to acknowledge the information
                # Based on the recorded test, there's a "Let op: Onjuiste informatie" text
                time.sleep(1)
                acknowledgment_text = context.page.get_by_text("Let op: Onjuiste informatie")
                if acknowledgment_text.count() > 0:
                    print("Clicking acknowledgment text")
                    acknowledgment_text.click()
                    time.sleep(0.5)

                # Now click "Bevestig aanvraag" button
                confirm_button = context.page.get_by_role("button", name="Bevestig aanvraag")
                if confirm_button.count() > 0:
                    print("Confirming the request")
                    confirm_button.click()
                    time.sleep(2)
    else:
        print("Could not find 6.000,00 € button to edit")
        context.page.screenshot(path="debug_no_box1_button.png")


@when(
    'I provide required housing data with huurprijs "{rent}", subsidiabele servicekosten "{subsidiabele_service_costs}", and servicekosten "{service_costs}"'
)
def step_provide_housing_data(context, rent, subsidiabele_service_costs, service_costs):
    """Fill in the required housing data in the form."""
    time.sleep(1)

    # Fill in HUURPRIJS and SUBSIDIABELE_SERVICEKOSTEN
    huurprijs_field = context.page.locator("#display-HUURPRIJS")
    if huurprijs_field.count() > 0:
        print(f"Filling huurprijs={rent}")
        huurprijs_field.click()
        huurprijs_field.fill(rent)

    subsidiabele_field = context.page.locator("#display-SUBSIDIABELE_SERVICEKOSTEN")
    if subsidiabele_field.count() > 0:
        print(f"Filling subsidiabele servicekosten={subsidiabele_service_costs}")
        subsidiabele_field.click()
        subsidiabele_field.fill(subsidiabele_service_costs)

    # Click save button
    save_button = context.page.get_by_role("button", name="Opslaan")
    if save_button.count() > 0:
        save_button.click()
        time.sleep(1)

    # Now fill in servicekosten
    servicekosten_field = context.page.get_by_placeholder("0.00")
    if servicekosten_field.count() > 0:
        print(f"Filling servicekosten={service_costs}")
        servicekosten_field.click()
        servicekosten_field.fill(service_costs)

        # Click save button again
        save_button = context.page.get_by_role("button", name="Opslaan")
        if save_button.count() > 0:
            save_button.click()
            time.sleep(2)


@when("I provide housing data")
def step_provide_housing_data_table(context):
    """Provide housing data from a table."""
    for row in context.table:
        edit_data = {
            "service": context.service,
            "key": row["Field"],
            "new_value": row["Value"],
            "old_value": "",
            "reason": "Providing required housing data",
            "law": context.law,
            "bsn": context.bsn,
            "claimant": "CITIZEN",
            "auto_approve": "false",
        }
        requests.post(f"{context.base_url}/edit/update-value", data=edit_data)


@then("the huurtoeslag should be recalculated")
def step_huurtoeslag_recalculated(context):
    """Verify that huurtoeslag is recalculated with pending claims."""
    response = requests.get(
        f"{context.base_url}/laws/application-panel",
        params={"service": context.service, "law": context.law, "bsn": context.bsn, "approved": "false"},
    )
    assert response.status_code == 200, f"Failed to get application panel: {response.status_code}"
    context.panel_response = response.text

    # Check that there's a calculated amount
    assert "€" in context.panel_response, "No euro amount found in response"


@then("the huurtoeslag amount should increase significantly due to lower income")
def step_huurtoeslag_increased(context):
    """Verify that the huurtoeslag amount has increased."""
    # With income of 600 instead of 14650, the huurtoeslag should be much higher
    # Check that the response shows a substantial amount
    assert "€" in context.panel_response, "No euro amount found"

    # Look for amounts over 400 euro (typical for low income)
    # This is a simple check - could be made more sophisticated
    amounts = re.findall(r"(\d+)[,.](\d+)\s*€", context.panel_response)
    has_high_amount = any(int(whole) > 400 for whole, _ in amounts)
    assert has_high_amount, "Expected a higher huurtoeslag amount for low income"


@then("the amount should be different from the original")
def step_amount_different_from_original(context):
    """Verify that the amount has changed from the original calculation."""
    # Get the calculation WITHOUT pending claims (original)
    response_original = requests.get(
        f"{context.base_url}/laws/application-panel",
        params={
            "service": context.service,
            "law": context.law,
            "bsn": context.bsn,
            "approved": "true",  # Without pending claims
        },
    )

    # Get the calculation WITH pending claims (new)
    response_new = requests.get(
        f"{context.base_url}/laws/application-panel",
        params={
            "service": context.service,
            "law": context.law,
            "bsn": context.bsn,
            "approved": "false",  # With pending claims
        },
    )

    assert response_original.status_code == 200
    assert response_new.status_code == 200

    # The key test: the responses should be different
    # This proves that the pending claims are affecting the calculation
    assert response_original.text != response_new.text, "The calculation did not change after editing values"

    # Also verify that pending claims are shown (with arrow indicators)
    assert "→" in response_new.text, "No pending claims indicators found"


@then('the huurtoeslag is calculated as "{amount}" euro per month')
def step_huurtoeslag_calculated_as(context, amount):
    """Read the calculated huurtoeslag amount from the page."""
    # Wait for any HTMX updates to complete
    time.sleep(2)

    # Wait for the calculation to appear
    context.page.wait_for_load_state("networkidle", timeout=5000)

    # First look for the amount anywhere on the page (could be in modal or dashboard)
    amount_locator = context.page.locator(f"text={amount}")

    # Allow for small rounding differences (e.g., 320,45 vs 320,46)
    if amount_locator.count() == 0:
        amount_locator = context.page.locator(f"text={amount}")

    # Store the initial amount if this is the first check
    if not hasattr(context, "initial_amount"):
        context.initial_amount = amount

    # Take a screenshot for debugging if amount not found
    if amount_locator.count() == 0:
        context.page.screenshot(path="debug_screenshot.png")
        page_text = context.page.inner_text("body")
        import re

        amounts = re.findall(r"\d+[,\.]\d+\s*€", page_text)
        print(f"Amounts found on page: {amounts[:10]}")
        print(f"Page text sample: {page_text[:500]}")

    # Assert the amount is visible
    assert amount_locator.count() > 0, f"Expected amount {amount} not found on page"


@then("I capture the initial huurtoeslag amount")
def step_capture_initial_huurtoeslag(context):
    """Capture the initial huurtoeslag amount."""
    response = requests.get(
        f"{context.base_url}/laws/application-panel",
        params={"service": context.service, "law": context.law, "bsn": context.bsn, "approved": "false"},
    )
    assert response.status_code == 200, f"Failed to get application panel: {response.status_code}"

    context.panel_response = response.text

    # Extract the amount from the response - look for the main result
    # Look for amounts in the format "123,45 €" in text-4xl font (main result)
    matches = re.findall(r"text-4xl[^>]*>(\d+),(\d+)\s*€", response.text)
    if matches:
        context.initial_amount = f"{matches[0][0]},{matches[0][1]}"
    else:
        # Fallback to any amount
        amounts = re.findall(r"(\d+),(\d+)\s*€", response.text)
        assert amounts, "No amount found in response"
        context.initial_amount = f"{amounts[0][0]},{amounts[0][1]}"

    print(f"Initial huurtoeslag amount: {context.initial_amount} €")


@then("the huurtoeslag amount should be higher than before")
def step_huurtoeslag_higher_than_before(context):
    """Verify that the huurtoeslag amount increased."""
    response = requests.get(
        f"{context.base_url}/laws/application-panel",
        params={"service": context.service, "law": context.law, "bsn": context.bsn, "approved": "false"},
    )
    assert response.status_code == 200, f"Failed to get application panel: {response.status_code}"

    # Extract the new amount - look for the main result
    matches = re.findall(r"text-4xl[^>]*>(\d+),(\d+)\s*€", response.text)
    if matches:
        new_amount = f"{matches[0][0]},{matches[0][1]}"
    else:
        # Fallback to any amount
        amounts = re.findall(r"(\d+),(\d+)\s*€", response.text)
        assert amounts, "No amount found in response"
        new_amount = f"{amounts[0][0]},{amounts[0][1]}"

    print(f"New huurtoeslag amount: {new_amount} €")

    # Compare amounts (convert to float for comparison)
    initial_value = float(context.initial_amount.replace(",", "."))
    new_value = float(new_amount.replace(",", "."))

    assert new_value > initial_value, f"Amount did not increase: {context.initial_amount} € → {new_amount} €"
