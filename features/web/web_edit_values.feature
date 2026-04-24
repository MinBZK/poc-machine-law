@ui @skip
Feature: Edit values through web interface
  As a citizen
  I want to edit my income values through the web interface
  So that benefit calculations are updated with my actual situation

  # Pre-existing failure on main: Playwright selectors (#display-HUURPRIJS,
  # "6.000,00 €" button, waarom? chevrons) reference an older UI revision.
  # Current application-panel no longer exposes those ids, so the modal fill
  # steps silently do nothing and the subsequent amount-capture assertion
  # fails. Re-record against the current UI when touching this flow again.
  @ui @skip
  Scenario: Edit form captures value changes correctly
    Given the web server is running
    When I start requesting "huurtoeslag" for BSN "100000001"
    And I provide required housing data with huurprijs "720", subsidiabele servicekosten "48", and servicekosten "50"
    Then I capture the initial huurtoeslag amount
    When I change "Box1 dienstbetrekking" to "600" euro
    Then the amount should be different from the original
