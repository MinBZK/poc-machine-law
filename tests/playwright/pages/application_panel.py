from playwright.sync_api import Page, expect


class ApplicationPanel:
    """Page Object Model for the Application Panel component"""

    def __init__(self, page: Page):
        self.page = page
        self.panel_selector = "#application-panel"
        self.panel = self.page.locator(self.panel_selector)

        # Section toggles
        self.explanation_toggle = self.page.locator("button >> text=Uitleg")
        self.technical_details_toggle = self.page.locator("button >> text=Technische details")
        self.used_data_toggle = self.page.locator("button >> text=Gebruikte gegevens")

        # Form elements
        self.declaration_checkbox = self.page.locator("#declaration-checkbox")
        self.submit_button = self.page.locator("button >> text=Bevestig aanvraag")
        self.close_button = self.panel.locator(
            "button[aria-label='Close' i], button svg path[d*='M6 18L18 6M6 6l12 12']"
        ).first

        # Content sections
        self.explanation_content = self.page.locator("#explanation-content")
        self.used_data_content = self.panel.locator("div[x-show='showUsedData']")
        self.technical_details_content = self.panel.locator("div[x-show='showTechnical']")

    def is_visible(self) -> bool:
        """Check if the application panel is visible"""
        return self.panel.is_visible()

    def toggle_explanation(self) -> None:
        """Toggle the explanation section"""
        self.explanation_toggle.click()

    def toggle_technical_details(self) -> None:
        """Toggle the technical details section"""
        self.technical_details_toggle.click()

    def toggle_used_data(self) -> None:
        """Toggle the used data section"""
        self.used_data_toggle.click()

    def check_declaration(self) -> None:
        """Check the declaration checkbox"""
        self.declaration_checkbox.check()

    def submit_application(self) -> None:
        """Submit the application form"""
        self.submit_button.click()

    def close_panel(self) -> None:
        """Close the application panel"""
        self.close_button.click()

    def expect_submit_button_enabled(self) -> None:
        """Expect the submit button to be enabled"""
        expect(self.submit_button).not_to_be_disabled()

    def expect_submit_button_disabled(self) -> None:
        """Expect the submit button to be disabled"""
        expect(self.submit_button).to_be_disabled()

    def expect_explanation_visible(self) -> None:
        """Expect the explanation section to be visible"""
        expect(self.explanation_content).to_be_visible()

    def expect_technical_details_visible(self) -> None:
        """Expect the technical details section to be visible"""
        expect(self.technical_details_content).to_be_visible()

    def expect_used_data_visible(self) -> None:
        """Expect the used data section to be visible"""
        expect(self.used_data_content).to_be_visible()
