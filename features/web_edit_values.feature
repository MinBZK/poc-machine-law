Feature: Edit values through web interface
  As a citizen
  I want to edit my income values through the web interface
  So that benefit calculations are updated with my actual situation

  Scenario: Edit form captures value changes correctly
    Given the web server is running
    When I start requesting "huurtoeslag" for BSN "100000001"
    And I provide required housing data with huurprijs "720", subsidiabele servicekosten "48", and servicekosten "50"
    Then the huurtoeslag is calculated as "58,01" euro per month
    When I change "Box1 dienstbetrekking" to "600" euro
    Then the huurtoeslag is calculated as "320,45" euro per month