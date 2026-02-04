@skip-go
@skip
Feature: Edit values through web interface
  As a citizen
  I want to edit my income values through the web interface
  So that benefit calculations are updated with my actual situation

  @browser
  Scenario: Edit form captures value changes correctly
    Given the web server is running
    When I start requesting "huurtoeslag" for BSN "100000001"
    And I provide required housing data with huurprijs "720", subsidiabele servicekosten "48", and servicekosten "50"
    Then I capture the initial huurtoeslag amount
    When I change "Box1 dienstbetrekking" to "600" euro
    Then the amount should be different from the original
