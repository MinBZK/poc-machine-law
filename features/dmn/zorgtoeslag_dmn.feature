Feature: Berekening Zorgtoeslag 2025 (DMN)
  Als burger
  Wil ik weten of ik recht heb op zorgtoeslag via DMN beslissingsmodellen
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given the DMN engine is initialized

  Scenario: Persoon onder 18 heeft geen recht op zorgtoeslag (DMN)
    Given DMN person data:
      | birth_date | partnership_status | health_insurance_status | is_resident |
      | 2008-01-01 | alleenstaand       | verzekerd               | true        |
    And DMN reference date is "2025-02-01"
    When the DMN zorgtoeslag decision is evaluated
    Then the DMN eligibility result should be false

  Scenario: Persoon boven 18 heeft recht op zorgtoeslag (DMN)
    Given DMN person data:
      | birth_date | partnership_status | health_insurance_status | is_resident |
      | 2005-01-01 | alleenstaand       | verzekerd               | true        |
    And DMN tax data:
      | box1_inkomen | box2_inkomen | box3_inkomen | vermogen |
      | 79547        | 0            | 0            | 50000    |
    And DMN income data:
      | work_income | unemployment_benefit | disability_benefit | pension | other_benefits |
      | 79547       | 0                    | 0                  | 0       | 0              |
    And DMN reference date is "2025-02-01"
    When the DMN zorgtoeslag decision is evaluated
    Then the DMN eligibility result should be true
