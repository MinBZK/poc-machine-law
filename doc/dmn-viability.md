# DMN Viability Assessment for Machine Law

## Executive Summary

This document assesses the viability of using **DMN (Decision Model and Notation)** as a rules language for modeling and executing legal rules in the Machine Law project. The project currently uses a custom YAML-based language, and both **NRML (Normalized Rule Modeling Language)** and **DMN** are being evaluated as potential replacements.

**Key Finding:** DMN is a mature, standardized approach with significant tooling support and adoption in the Netherlands government (via STTR). Its ability to reference other DMN models makes it suitable for modeling laws that depend on other laws, which is a critical requirement for the Machine Law project.

## Table of Contents

1. [Background](#background)
2. [What is DMN?](#what-is-dmn)
3. [DMN in the Netherlands](#dmn-in-the-netherlands)
4. [Comparison: NRML vs DMN](#comparison-nrml-vs-dmn)
5. [DMN Example: Kinderbijslag](#dmn-example-kinderbijslag)
6. [Cross-Law References: Kieswet Example](#cross-law-references-kieswet-example)
7. [Viability Assessment](#viability-assessment)
8. [Recommendations](#recommendations)
9. [References](#references)

---

## Background

The Machine Law project currently uses a **custom YAML-based language** for representing legal rules. As the project evolves, there is a need to evaluate more robust and standardized approaches for legal rule modeling.

Two candidates are being considered:
1. **NRML (Normalized Rule Modeling Language)**: A custom JSON-based format with rich metadata support, versioning, multi-language support, and complex expression capabilities tailored to the legal domain
2. **DMN (Decision Model and Notation)**: An industry-standard approach maintained by the Object Management Group (OMG), widely adopted in business and government

This assessment investigates whether **DMN** could serve as a viable rules language for the Machine Law project, with particular focus on its ability to model laws that reference and depend on other laws.

---

## What is DMN?

**Decision Model and Notation (DMN)** is an industry standard for modeling and executing business decisions, published by the OMG. It provides:

### Core Components

1. **Decision Tables**: Tabular representation of rules mapping inputs to outputs
2. **Decision Requirement Diagrams (DRD)**: Visual graphs showing decision dependencies
3. **FEEL (Friendly Enough Expression Language)**: Standardized expression language for conditions and calculations
4. **Business Knowledge Models**: Reusable decision logic components
5. **Hit Policies**: Rules for determining which table rows match (Unique, First, Collect, etc.)

### DMN Structure

```
┌─────────────────────────────────────────────────┐
│ Decision Requirement Diagram (DRD)              │
│  - Shows decision dependencies visually         │
│  - Connects inputs → decisions → outputs        │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ Decision Tables                                  │
│  ┌─────────────┬──────────────┬──────────────┐ │
│  │  Input 1    │   Input 2    │   Output     │ │
│  ├─────────────┼──────────────┼──────────────┤ │
│  │  condition  │  condition   │   result     │ │
│  │  condition  │  condition   │   result     │ │
│  └─────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ FEEL Expressions                                 │
│  - count(children[age <= 10])                   │
│  - (income * 0.35) + base_amount                │
│  - if status = "eligible" then amount else 0    │
└─────────────────────────────────────────────────┘
```

### Example Decision Table

**Loan Eligibility Decision**

Hit Policy: U (Unique)

| Age    | Income      | Risk Score | Eligibility |
|--------|-------------|------------|-------------|
| < 21   | -           | -          | DECLINED    |
| >= 21  | >= 100000   | > 50       | REVIEW      |
| >= 21  | >= 100000   | <= 50      | APPROVED    |
| >= 21  | < 100000    | -          | APPROVED    |

### FEEL Expression Examples

```
// Filtering collections
count(children[age <= 10])

// Arithmetic
(monthly_income - monthly_expenses) * 0.35

// Conditional logic
if benefit_amount > 0 then true else false

// Date calculations
years(date_of_birth, today()) >= 18

// Aggregation
sum(children.benefit_amount)
```

---

## DMN in the Netherlands

### STTR Standard (Standaard Toepasbare Regels)

The Netherlands has adopted DMN as the foundation for the **STTR** (Standard for Applicable Rules) used in the **Digitaal Stelsel Omgevingswet (DSO)** - the Digital Environment and Planning Act system.

**Key Facts:**
- **Official Standard**: Used by Dutch government for Omgevingswet (Environment and Planning Act)
- **DMN Versions**: Supports both DMN 1.1 and 1.2
- **Purpose**: Translate legal regulations into "toepasbare regels" (applicable rules) accessible to citizens
- **Availability**: Specification documents and example files available at [iplo.nl](https://iplo.nl/digitaal-stelsel/aansluiten/standaarden/sttr-imtr/)
- **Extensions**: STTR extends DMN using DMN's extension elements for domain-specific needs

### STTR Architecture

STTR uses a **layered model approach**:

1. **Legal Text Layer**: Original legislation
2. **Decision Logic Layer**: DMN decision tables and expressions
3. **Question Trees Layer**: User-facing questionnaires
4. **Rule Engine Layer**: Execution engine processing DMN rules

### Why STTR Matters

The existence of STTR demonstrates:
- DMN is viable for Dutch legal rules
- Government acceptance and standardization
- Active ecosystem and tooling in Netherlands
- Proven approach for translating laws to executable logic
- May require extensions for complex scenarios

---

## Comparison: NRML vs DMN

### Structure Comparison

| Aspect | NRML | DMN |
|--------|------|-----|
| **Format** | JSON | XML |
| **Schema** | Custom, tailored to legal domain | OMG standard |
| **Primary Use** | Complex legal rules with rich metadata | Business decision modeling |
| **Visual Tooling** | Limited (custom needed) | Extensive (many commercial/open tools) |
| **Expression Language** | Custom (aggregation, arithmetic, comparison) | FEEL (standardized) |
| **Versioning** | Built-in `validFrom` timestamps | Separate models or DMN 1.3+ temporal |
| **Internationalization** | Multi-language names/articles built-in | Not standardized in DMN |
| **Relationships** | Explicit `$ref` JSON pointers | `informationRequirement`, `knowledgeRequirement` |
| **Facts/Objects** | Rich fact definitions with metadata | Data types and item definitions |

### Feature Comparison

#### What DMN Does Well

1. **Standardization**: Industry-wide OMG standard with clear specification
2. **Visual Decision Tables**: Intuitive tabular rule representation
3. **Tooling Ecosystem**:
   - Camunda (open source DMN engine)
   - Red Hat Decision Manager
   - Trisotech Decision Modeler
   - Signavio Process Manager
   - Drools DMN Engine
4. **Government Adoption**: STTR standard in Netherlands
5. **FEEL Language**: Powerful, standardized expression language
6. **Decision Diagrams**: Clear visual representation of decision dependencies
7. **Validation**: Standard validators and schema checking
8. **Execution Engines**: Multiple mature execution engines available
9. **Documentation**: Extensive tutorials, examples, and community support
10. **Portability**: Models can be exchanged between different tools

#### What NRML Does Well

1. **Rich Metadata**:
   - Multi-language support (nl/en) for names
   - Grammatical articles (de/het/een)
   - Plural forms
   - Animated vs non-animated entities
2. **Built-in Versioning**: `validFrom` timestamps on every version
3. **Legal Domain Modeling**:
   - Explicit fact definitions
   - Relationship modeling via arguments
   - Cardinality specification (one/many)
4. **Custom Expression Types**:
   - Aggregation with conditions
   - Arithmetic expressions
   - Comparison operators
   - Conditional expressions
   - Nested expressions
5. **Schema Evolution**: Flexible custom schema adaptable to legal needs
6. **Input/Output Mapping**: Clear separation with `$ref` pointers
7. **Precision Control**: Decimal precision specification for monetary values
8. **Unit Management**: Explicit unit specification (€, jaar, etc.)

#### DMN Limitations for Legal Modeling

1. **No Built-in Versioning**: Must use separate DMN files for each version or wait for DMN 1.3+ temporal support
2. **Limited Metadata**: No standard for grammatical articles, plurals, or rich linguistic metadata
3. **XML Verbosity**: More verbose than JSON for similar structures
4. **No Standard I18n**: Multi-language support not standardized
5. **Relationship Complexity**: Modeling complex entity relationships less explicit than NRML
6. **Custom Extensions Needed**: Would require STTR-like extensions for legal-specific features

#### NRML Limitations

1. **No Standard**: Custom format requires custom tooling
2. **Limited Tooling**: No existing visual editors or engines
3. **Steeper Learning Curve**: Custom concepts vs industry-standard DMN
4. **No Portability**: Cannot import/export to other systems
5. **Maintenance Burden**: Full responsibility for specification evolution
6. **Community Support**: Limited to project vs DMN's global community

---

## DMN Example: Kinderbijslag

To illustrate DMN capabilities, here's how the `kinderbijslag.nrml.json` law would be represented in DMN.

### Original NRML Logic

The Kinderbijslag (child benefit) law calculates:
- **Young children** (age ≤ 10): €250.50 per child
- **Older children** (10 < age ≤ 18): €300.75 per child
- **Total benefit**: (young_count × €250.50) + (older_count × €300.75)
- **Send letter**: If total > 0
- **Risk alarm**: If number of children > 6

### DMN Representation

#### Decision Requirement Diagram

```
                    ┌─────────────┐
                    │  Children   │ (Input Data)
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐  ┌──────────────────┐  ┌────────────┐
│ Count Young     │  │ Count Older      │  │ Risk Alarm │
│ Children        │  │ Children         │  └────────────┘
└────────┬────────┘  └────────┬─────────┘
         │                    │
         └──────────┬─────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Total Benefit      │
         │ Amount             │
         └──────────┬─────────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Send Letter        │
         └────────────────────┘
```

#### Decision Tables

**1. Send Letter Decision**

Hit Policy: U (Unique)

| Total Benefit | Send Letter |
|---------------|-------------|
| > 0           | true        |
| <= 0          | false       |

**2. Risk Alarm Decision**

Hit Policy: U (Unique)

| Number of Children | Risk Alarm |
|-------------------|------------|
| > 6               | true       |
| <= 6              | false      |

#### FEEL Expressions

```feel
// Count young children
count(children[age <= 10])

// Count older children
count(children[age > 10 and age <= 18])

// Calculate total benefit
(count_young_children * 250.50) + (count_older_children * 300.75)
```

#### DMN XML Structure (Simplified)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="kinderbijslag_dmn"
             name="Kinderbijslag (Child Benefit)">

  <!-- Input: Children collection -->
  <inputData id="input_children" name="Children">
    <variable name="children" typeRef="tChildren"/>
  </inputData>

  <!-- Decision: Count young children -->
  <decision id="decision_count_young" name="Count Young Children">
    <variable name="count_young_children" typeRef="number"/>
    <informationRequirement>
      <requiredInput href="#input_children"/>
    </informationRequirement>
    <literalExpression>
      <text>count(children[age &lt;= 10])</text>
    </literalExpression>
  </decision>

  <!-- Decision: Total benefit calculation -->
  <decision id="decision_total_benefit" name="Total Child Benefit">
    <variable name="total_benefit" typeRef="number"/>
    <informationRequirement>
      <requiredDecision href="#decision_count_young"/>
    </informationRequirement>
    <informationRequirement>
      <requiredDecision href="#decision_count_older"/>
    </informationRequirement>
    <literalExpression>
      <text>(count_young_children * 250.50) + (count_older_children * 300.75)</text>
    </literalExpression>
  </decision>

  <!-- Decision Table: Send letter -->
  <decision id="decision_send_letter" name="Send Letter">
    <variable name="send_letter" typeRef="boolean"/>
    <informationRequirement>
      <requiredDecision href="#decision_total_benefit"/>
    </informationRequirement>
    <decisionTable hitPolicy="UNIQUE">
      <input label="Total Benefit">
        <inputExpression typeRef="number">
          <text>total_benefit</text>
        </inputExpression>
      </input>
      <output label="Send Letter" typeRef="boolean"/>
      <rule>
        <inputEntry><text>&gt; 0</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <rule>
        <inputEntry><text>&lt;= 0</text></inputEntry>
        <outputEntry><text>false</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>

</definitions>
```

### What's Different in DMN Version

When comparing the DMN version to the NRML version:

**Missing in DMN (may be required):**
1. Legal basis reference ("Algemene Kinderbijslagwet") - though can be added via annotations
2. Precision specification for monetary values - implicit in DMN
3. Explicit unit specification beyond type

**Missing in DMN (optional features, may not be needed):**
1. Multi-language names (nl: "kind", en: "child") - adds complexity, requires generation
2. Grammatical articles (nl: "het", "de", "een") - language-specific metadata
3. Plural forms (nl: "kinderen") - can be handled in presentation layer
4. Animated entity classification - domain-specific metadata
5. Built-in versioning (validFrom "2018") - can use separate DMN files or external version management
6. Input/output mapping metadata - DMN has its own approach
7. Schema version tracking - handled externally

**Note:** Language translations and rich linguistic metadata can be considered optional or even disadvantageous, as they increase the burden of law authoring and maintenance. These features may be better handled in a separate presentation/localization layer rather than in the core rules language.

**Equivalent or Better in DMN:**
1. Decision logic clarity with decision tables
2. Visual representation (DRD) - industry-standard diagrams
3. Standard tooling support - many commercial and open-source tools
4. Expression language (FEEL) - standardized and powerful
5. Decision dependencies - explicit and visual
6. Validation against standard - automatic checking
7. **Cross-law references** - can reference other DMN models (see next section)

---

## Cross-Law References: Kieswet Example

One of the **critical requirements** for the Machine Law project is the ability for laws to reference and depend on other laws. DMN supports this through **Business Knowledge Models (BKM)** and **Decision Services**, which can be imported and reused across different DMN models.

### Use Case: Kieswet (Electoral Law) Referencing Wet BRP (Nationality Law)

The Kieswet (Dutch Electoral Law) from the [regelrecht-laws repository](https://github.com/MinBZK/regelrecht-laws) needs to determine if a person is eligible to vote for Tweede Kamer elections. According to the actual kieswet YAML (KIESRAAD-2024-01-01.yaml), three requirements must be met:

1. **Dutch nationality** on candidate nomination day (verified via RvIG/Wet BRP)
2. **Age ≥ 18** on election day (verified via RvIG/Wet BRP)
3. **No judicial exclusion** by court order (verified via JUSTID)

Rather than reimplementing nationality logic, the Kieswet DMN can reference the Wet BRP (Basisregistratie Personen) nationality determination service.

**Note:** The DMN examples below are illustrative representations showing how the existing YAML-based kieswet logic could be modeled in DMN with cross-law references.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Wet BRP - RvIG Service (DMN)                            │
│                                                          │
│  Input: Person { nationality, birth_date }              │
│         reference_date                                   │
│                                                          │
│  Decision Logic (inside DMN):                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Nationality Check Decision Table:                  │ │
│  │  IF nationality in ["Nederlandse", "Nederlander",  │ │
│  │                      "NL", "NLD"]                   │ │
│  │  THEN has_dutch_nationality = true                 │ │
│  │  ELSE has_dutch_nationality = false                │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Age Calculation:                                   │ │
│  │  age = years(person.birth_date, reference_date)   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Outputs: has_dutch_nationality (bool), age (number)     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ Referenced by (imports and calls)
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Kieswet - Voting Eligibility (DMN)                      │
│  (KIESRAAD-2024-01-01)                                   │
│                                                          │
│  Input: Person { nationality, birth_date,               │
│                  voting_rights_revoked }                 │
│         election_date                                    │
│                                                          │
│  Decision Logic (inside DMN):                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Calls RvIG service:                                │ │
│  │  is_18_or_older = rvig_service(person,            │ │
│  │                     election_date).age >= 18       │ │
│  │                                                    │ │
│  │  has_dutch_nat = rvig_service(person,             │ │
│  │                    election_date).has_dutch_nat    │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Final Decision Table (Articles B1 & B3):          │ │
│  │  IF is_18_or_older = true AND                     │ │
│  │     has_dutch_nat = true AND                      │ │
│  │     voting_rights_revoked = false                 │ │
│  │  THEN heeft_stemrecht = true                      │ │
│  │  ELSE heeft_stemrecht = false                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Output: heeft_stemrecht (bool)                          │
└──────────────────────────────────────────────────────────┘

Key principle: All evaluation logic is inside the DMN rules.
Input is raw data (nationality string, dates, booleans).
No external system calls - pure decision logic.
```

### DMN Implementation

#### 1. Wet BRP - RvIG Service (rvig_brp_service.dmn)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="rvig_brp_service"
             name="RvIG - Wet BRP Service"
             namespace="https://wetten.overheid.nl/wet_brp/rvig">

  <!-- Input: Person Context Object with BRP Data -->
  <inputData id="input_person" name="Person">
    <variable name="person" typeRef="tPerson"/>
  </inputData>

  <inputData id="input_reference_date" name="Reference Date">
    <variable name="reference_date" typeRef="date"/>
  </inputData>

  <!-- Custom Data Type: Person -->
  <itemDefinition name="tPerson">
    <itemComponent name="nationality">
      <typeRef>string</typeRef>
    </itemComponent>
    <itemComponent name="birth_date">
      <typeRef>date</typeRef>
    </itemComponent>
  </itemDefinition>

  <!-- Decision: Check Dutch Nationality -->
  <decision id="decision_nationality" name="Dutch Nationality Check">
    <variable name="has_dutch_nationality" typeRef="boolean"/>
    <informationRequirement>
      <requiredInput href="#input_person"/>
    </informationRequirement>
    <decisionTable hitPolicy="UNIQUE">
      <input label="Nationality">
        <inputExpression typeRef="string">
          <text>person.nationality</text>
        </inputExpression>
      </input>
      <output label="Has Dutch Nationality" typeRef="boolean"/>
      <!-- Dutch nationality values -->
      <rule>
        <inputEntry><text>"Nederlandse"</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <rule>
        <inputEntry><text>"Nederlander"</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <rule>
        <inputEntry><text>"NL"</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <rule>
        <inputEntry><text>"NLD"</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <!-- All other nationalities -->
      <rule>
        <inputEntry><text>-</text></inputEntry>
        <outputEntry><text>false</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>

  <!-- Decision: Calculate Age -->
  <decision id="decision_age" name="Age Calculation">
    <variable name="age" typeRef="number"/>
    <informationRequirement>
      <requiredInput href="#input_person"/>
    </informationRequirement>
    <informationRequirement>
      <requiredInput href="#input_reference_date"/>
    </informationRequirement>
    <literalExpression>
      <text>years(person.birth_date, reference_date)</text>
    </literalExpression>
  </decision>

  <!-- Decision Service: Exportable service for other DMN models -->
  <decisionService id="rvig_service" name="RvIG Service">
    <outputDecision href="#decision_nationality"/>
    <outputDecision href="#decision_age"/>
    <inputData href="#input_person"/>
    <inputData href="#input_reference_date"/>
  </decisionService>

</definitions>
```

#### 2. Kieswet Voting Eligibility (kiesraad_2024.dmn)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/"
             id="kiesraad_2024"
             name="Kieswet - Tweede Kamer Voting Rights"
             namespace="https://wetten.overheid.nl/BWBR0004627/kiesraad">

  <!-- Import RvIG/Wet BRP Decision Service -->
  <import namespace="https://wetten.overheid.nl/wet_brp/rvig"
          locationURI="rvig_brp_service.dmn"
          importType="http://www.omg.org/spec/DMN/20180521/MODEL/"/>

  <!-- Input: Person Context Object -->
  <inputData id="input_person" name="Person">
    <variable name="person" typeRef="tPerson"/>
  </inputData>

  <!-- Input: Election Date (for Tweede Kamer) -->
  <inputData id="input_election_date" name="Election Date">
    <variable name="election_date" typeRef="date"/>
  </inputData>

  <!-- Custom Data Type: Person -->
  <itemDefinition name="tPerson">
    <itemComponent name="nationality">
      <typeRef>string</typeRef>
    </itemComponent>
    <itemComponent name="birth_date">
      <typeRef>date</typeRef>
    </itemComponent>
    <itemComponent name="voting_rights_revoked">
      <typeRef>boolean</typeRef>
    </itemComponent>
  </itemDefinition>

  <!-- Decision: Age Check (Article B1) - CALLS RvIG SERVICE -->
  <decision id="decision_age_check" name="Age Check - Article B1">
    <variable name="is_18_or_older" typeRef="boolean"/>
    <informationRequirement>
      <requiredInput href="#input_person"/>
    </informationRequirement>
    <informationRequirement>
      <requiredInput href="#input_election_date"/>
    </informationRequirement>
    <!-- This invokes the RvIG service -->
    <knowledgeRequirement>
      <requiredKnowledge href="https://wetten.overheid.nl/wet_brp/rvig#rvig_service"/>
    </knowledgeRequirement>
    <literalExpression>
      <text>
        rvig_service(person, election_date).age >= 18
      </text>
    </literalExpression>
  </decision>

  <!-- Decision: Nationality Check (Article B1) - CALLS RvIG SERVICE -->
  <decision id="decision_nationality_check" name="Nationality Check - Article B1">
    <variable name="has_dutch_nationality" typeRef="boolean"/>
    <informationRequirement>
      <requiredInput href="#input_person"/>
    </informationRequirement>
    <informationRequirement>
      <requiredInput href="#input_election_date"/>
    </informationRequirement>
    <!-- This invokes the RvIG/Wet BRP service -->
    <knowledgeRequirement>
      <requiredKnowledge href="https://wetten.overheid.nl/wet_brp/rvig#rvig_service"/>
    </knowledgeRequirement>
    <literalExpression>
      <text>
        rvig_service(person, election_date).has_dutch_nationality
      </text>
    </literalExpression>
  </decision>

  <!-- Decision: Judicial Exclusion Check (Article B3) -->
  <decision id="decision_judicial_exclusion" name="Judicial Exclusion Check - Article B3">
    <variable name="is_judicially_excluded" typeRef="boolean"/>
    <informationRequirement>
      <requiredInput href="#input_person"/>
    </informationRequirement>
    <literalExpression>
      <text>person.voting_rights_revoked</text>
    </literalExpression>
  </decision>

  <!-- Main Decision: heeft_stemrecht (has voting rights) -->
  <decision id="decision_heeft_stemrecht" name="Heeft Stemrecht">
    <variable name="heeft_stemrecht" typeRef="boolean"/>
    <informationRequirement>
      <requiredDecision href="#decision_age_check"/>
    </informationRequirement>
    <informationRequirement>
      <requiredDecision href="#decision_nationality_check"/>
    </informationRequirement>
    <informationRequirement>
      <requiredDecision href="#decision_judicial_exclusion"/>
    </informationRequirement>
    <decisionTable hitPolicy="UNIQUE">
      <input label="18+ on Election Day">
        <inputExpression typeRef="boolean">
          <text>is_18_or_older</text>
        </inputExpression>
      </input>
      <input label="Has NL Nationality">
        <inputExpression typeRef="boolean">
          <text>has_dutch_nationality</text>
        </inputExpression>
      </input>
      <input label="Judicially Excluded">
        <inputExpression typeRef="boolean">
          <text>is_judicially_excluded</text>
        </inputExpression>
      </input>
      <output label="Heeft Stemrecht" typeRef="boolean"/>
      <!-- Only eligible if all three conditions met -->
      <rule>
        <inputEntry><text>true</text></inputEntry>
        <inputEntry><text>true</text></inputEntry>
        <inputEntry><text>false</text></inputEntry>
        <outputEntry><text>true</text></outputEntry>
      </rule>
      <!-- Otherwise not eligible -->
      <rule>
        <inputEntry><text>-</text></inputEntry>
        <inputEntry><text>-</text></inputEntry>
        <inputEntry><text>-</text></inputEntry>
        <outputEntry><text>false</text></outputEntry>
      </rule>
    </decisionTable>
  </decision>

</definitions>
```

### Key DMN Features for Cross-Law References

1. **Decision Services**: The RvIG/Wet BRP service logic is wrapped in a `<decisionService>` that can be imported and invoked by other DMN models (like Kieswet)
   ```xml
   <decisionService id="rvig_service" name="RvIG Service">
     <outputDecision href="#decision_nationality"/>
     <outputDecision href="#decision_age"/>
     <inputData href="#input_bsn"/>
     <inputData href="#input_reference_date"/>
   </decisionService>
   ```

2. **Import Mechanism**: The Kieswet DMN uses `<import>` to reference the Wet BRP namespace and location
   ```xml
   <import namespace="https://wetten.overheid.nl/wet_brp/rvig"
           locationURI="rvig_brp_service.dmn"
           importType="http://www.omg.org/spec/DMN/20180521/MODEL/"/>
   ```

3. **Knowledge Requirement**: The Kieswet decisions declare they need the RvIG service
   ```xml
   <knowledgeRequirement>
     <requiredKnowledge href="https://wetten.overheid.nl/wet_brp/rvig#rvig_service"/>
   </knowledgeRequirement>
   ```

4. **Service Invocation**: The RvIG service is invoked with person context object and date
   ```xml
   <literalExpression>
     <text>
       rvig_service(person, election_date).has_dutch_nationality
     </text>
   </literalExpression>
   ```

This pattern matches the real kieswet implementation where:
- **RvIG** (Royal Archives) provides the BRP data service
- **Kieswet** consumes this service for both nationality and age checks
- Both are defined in the [regelrecht-laws repository](https://github.com/MinBZK/regelrecht-laws)

**Important Design Principles:**
1. **No external system dependencies**: All required data (nationality, birth_date, voting_rights_revoked) is passed as input parameters via the Person context object
2. **Pure decision logic**: Laws only contain decision logic, not data retrieval
3. **Evaluation happens in rules**: The DMN contains the logic to evaluate raw input (e.g., checking if `nationality in ["Nederlandse", "Nederlander", "NL", "NLD"]`)
4. **Caller provides raw data**: The system invoking the law provides raw data values, not pre-processed results
5. **Example**: Input is `person.nationality = "Nederlandse"`, not `has_dutch_nationality = true`

### Benefits of DMN Cross-Law References

**Advantages:**
1. **Reusability**: Nationality logic written once, used by multiple laws (Kieswet, benefits laws, etc.)
2. **Maintainability**: Updates to nationality rules automatically propagate to all dependent laws
3. **Standard Mechanism**: Uses DMN's built-in import/export capabilities
4. **Clear Dependencies**: Decision Requirement Diagrams show which laws depend on which
5. **Version Management**: Can reference specific versions of imported DMN models
6. **Tool Support**: DMN tools understand imports and can validate cross-references
7. **Modularity**: Laws can be developed and tested independently

**Considerations:**
1. **Namespace Management**: Need clear naming conventions for law URIs
2. **Circular Dependencies**: Must avoid law A importing law B which imports law A
3. **Version Compatibility**: Need strategy for handling breaking changes in referenced laws
4. **Performance**: May need caching or optimization for frequently called decision services
5. **Deployment**: Must ensure all referenced DMN files are available at runtime

### Comparison to Other Approaches

| Approach | DMN | NRML | Current YAML |
|----------|-----|------|--------------|
| Cross-law references | ✅ Built-in via imports | ✅ Via $ref pointers | ⚠️ Not standardized |
| Visual dependency graph | ✅ Standard DRD | ❌ Custom needed | ❌ Not supported |
| Tool validation | ✅ Standard tools check | ⚠️ Custom validation | ❌ Manual |
| Versioning imports | ✅ Can specify versions | ✅ Can reference versions | ❌ Not standard |
| Reusable services | ✅ Decision Services | ⚠️ Custom mechanism | ❌ Copy-paste |

---

## Viability Assessment

### Technical Viability: HIGH

DMN is **technically viable** for representing legal rules. The STTR standard proves this works in practice for Dutch government regulations.

**Evidence:**
- STTR successfully uses DMN for Omgevingswet
- FEEL expressions can handle complex calculations
- Decision tables map well to rule-based logic
- Multiple mature execution engines available
- Proven in production government systems

### Functional Completeness: HIGH

DMN can represent the **core decision logic** effectively, including the critical requirement for cross-law references.

**Core Requirements Met:**
1. **Decision logic**: Fully supported via decision tables and FEEL expressions
2. **Cross-law references**: Built-in support via Decision Services and imports
3. **Complex calculations**: FEEL expressions handle arithmetic, aggregations, conditionals
4. **Visual representation**: Standard DRD diagrams show dependencies
5. **Validation**: Standard tooling validates logic and cross-references

**Optional Features (may not be needed):**
1. Multi-language metadata - can be in presentation layer instead
2. Built-in versioning - can use separate DMN files or external version management
3. Grammatical metadata - likely not needed in core rules language
4. Legal citation tracking - can be added via annotations or external metadata

**Approach:**
- Focus on decision logic purity in DMN
- Handle presentation/localization concerns separately
- Use DMN annotations for supplementary metadata
- Leverage standard DMN features rather than extending

### Ecosystem & Tooling: EXCELLENT

DMN has **strong ecosystem support** that NRML cannot match.

**Advantages:**
- Visual modeling tools (Camunda Modeler, Trisotech, etc.)
- Multiple execution engines (Camunda, Drools, Red Hat)
- Validation tools and testing frameworks
- Government adoption (STTR in Netherlands)
- Large community and extensive documentation
- Training materials and certifications
- Integration with BPMN for process modeling

### Migration Effort: MODERATE

Migrating from current YAML to DMN would require **moderate effort**, less than building a custom NRML implementation.

**Required Work:**
1. Convert YAML laws to DMN XML format
2. Map existing expressions to FEEL syntax
3. Adopt DMN execution engine (e.g., Camunda)
4. Update tests to work with DMN engine
5. Train team on DMN and FEEL syntax
6. Establish DMN toolchain (modeler, validator, engine)
7. Set up cross-law reference patterns

**Not Required (compared to NRML):**
- No need to build custom execution engine
- No need to build visual tooling from scratch
- No need to implement cross-reference resolution
- No need to create validation framework
- Can leverage existing mature DMN ecosystem

**Estimated Effort:** 2-4 person-months for migration + tooling setup

### Hybrid Approach Viability: GOOD

A **hybrid approach** may offer the best of both worlds.

**Possible Hybrid Models:**

**Option A: NRML as Source of Truth, DMN as Export**
- Keep NRML for rich metadata and legal modeling
- Generate DMN for interoperability and standard tooling
- Use DMN engines for execution if desired
- Maintain NRML→DMN converter

**Option B: DMN for Logic, NRML for Metadata**
- Store decision logic in DMN
- Store legal metadata in NRML or complementary format
- Link the two via identifiers
- Execute using DMN engine, enrich with NRML metadata

**Option C: STTR-Inspired Extension**
- Extend DMN like STTR does
- Add legal-specific extension elements
- Keep within DMN standard framework
- Gain standard benefits while adding needed features

---

## Recommendations

### Short Term (0-6 months)

1. **Continue with current YAML implementation**
   - Current system is working
   - No urgent need for migration
   - Focus on feature development

2. **Create YAML→DMN Export** (Proof of Concept)
   - Build converter to export simple laws to DMN
   - Validate that core logic can be represented
   - Test with existing DMN engines (Camunda)
   - Identify specific gaps and solutions

3. **Study STTR in Depth**
   - Download and analyze STTR example files
   - Understand their extension approach
   - Learn from their solutions to similar problems
   - Consider adopting STTR patterns

4. **Engage with DMN Community**
   - Contact STTR/DSO team for insights
   - Join DMN working groups if applicable
   - Share learnings and challenges
   - Build relationships for future collaboration

### Medium Term (6-12 months)

5. **Prototype Hybrid Approach**
   - Implement YAML source with DMN export
   - Build tooling for conversion
   - Test integration with Camunda or other DMN engine
   - Evaluate benefits vs maintenance cost

6. **Evaluate DMN 1.3+ Features**
   - Monitor DMN specification evolution
   - Assess new features (temporal logic, etc.)
   - Determine if gaps are being closed
   - Plan adoption timeline if beneficial

7. **Build DMN Compatibility Layer**
   - Design YAML subset that cleanly maps to DMN
   - Document conversion patterns and limitations
   - Create validation tools
   - Enable partial DMN interoperability

### Long Term (12+ months)

8. **Decision Point: Full Migration or Hybrid**
   - Evaluate PoC results and hybrid approach
   - Assess if DMN standardization worth tradeoffs
   - Consider project maturity and team capacity
   - Make informed strategic decision

9. **If Migrating to DMN:**
   - Implement STTR-style extensions if needed
   - Build migration tooling for existing laws
   - Train team on DMN and FEEL
   - Adopt standard DMN toolchain
   - Maintain YAML archive for reference

10. **If Staying with YAML or NRML:**
    - Invest in visual tooling
    - Build robust execution engine
    - Create comprehensive documentation
    - Maintain DMN export for interoperability
    - Consider publishing as standard

### Key Decision Criteria

Choose **Full DMN Migration** if:
- Interoperability with government systems (STTR) is critical
- Standard tooling more valuable than custom features
- Team has DMN expertise or training resources
- Need to integrate with existing DMN/BPMN systems

Choose **Hybrid Approach** if:
- Want benefits of both systems
- Can maintain two representations
- Need custom metadata but want DMN execution
- Gradual migration preferred over big bang

Choose **Stay with Custom Format** if:
- Custom features are essential
- Custom control over format evolution needed
- No immediate need for external tool integration
- Team invested in current approach

---

## References

### DMN Specifications
- [OMG DMN Standard](https://www.omg.org/dmn/)
- [DMN 1.2 Specification](https://www.omg.org/spec/DMN/1.2/)
- [DMN 1.3 Specification](https://www.omg.org/spec/DMN/1.3/)

### STTR (Dutch Standard)
- [STTR/IMTR Overview (iplo.nl)](https://iplo.nl/digitaal-stelsel/aansluiten/standaarden/sttr-imtr/)
- [STTR Specification PDF](https://iplo.nl/publish/pages/192293/dso-specificatie-sttr-1-3-0-1-sept-2021.pdf)
- [DSO Developer Portal](https://aandeslagmetdeomgevingswet.nl/ontwikkelaarsportaal/)

### DMN Engines & Tools
- [Camunda DMN Engine](https://camunda.com/dmn/)
- [Drools DMN](https://drools.org/learn/dmn.html)
- [Red Hat Decision Manager](https://www.redhat.com/en/technologies/jboss-middleware/decision-manager)
- [Trisotech DMN Modeler](https://www.trisotech.com/dmn/)

### DMN Viewers & Online Tools
- [Camunda DMN Modeler](https://camunda.com/download/modeler/) - Desktop application (free, open source)
- [Camunda Web Modeler](https://demo.camunda.io/) - Online DMN editor and viewer
- [bpmn.io DMN Viewer](https://demo.bpmn.io/dmn) - Online DMN viewer (open source)
- [Trisotech DMN Modeler](https://www.trisotech.com/dmn/) - Commercial web-based tool with free trial

### Tutorials & Examples
- [Camunda DMN Tutorial](https://docs.camunda.org/get-started/dmn/)
- [OpenRules DMN Primer](https://openrules.com/dmn_primer.htm)
- [DMN Decision Tables by Example](https://documentation.flowable.com/latest/model/dmn/example/part1-decision-table)

### Academic & Industry Papers
- [A Layered Model Approach for Decision Rule Management](https://www.brcommunity.com/articles.php?id=c088)
- [DMN Wikipedia](https://en.wikipedia.org/wiki/Decision_Model_and_Notation)

---

## Appendix: DMN vs NRML Feature Matrix

| Feature | NRML | DMN | Notes |
|---------|------|-----|-------|
| **Core Modeling** |
| Decision logic | ✅ | ✅ | Both support complex logic |
| Conditions | ✅ | ✅ | NRML custom, DMN uses FEEL |
| Calculations | ✅ | ✅ | NRML arithmetic, DMN FEEL expressions |
| Aggregations | ✅ | ✅ | NRML explicit, DMN has sum/count/etc |
| Decision tables | ❌ | ✅ | DMN's primary strength |
| Visual diagrams | ❌ | ✅ | DMN has DRD standard |
| **Data & Types** |
| Type system | ✅ | ✅ | Both support custom types |
| Units | ✅ | ⚠️ | NRML explicit, DMN via custom types |
| Precision | ✅ | ⚠️ | NRML explicit, DMN implicit |
| Collections | ✅ | ✅ | Both support lists |
| Relations | ✅ | ⚠️ | NRML explicit $ref, DMN less clear |
| **Metadata (Optional)** |
| Multi-language | ✅ | ❌ | NRML has nl/en - may add complexity |
| Articles/grammar | ✅ | ❌ | NRML unique - may not be needed |
| Plurals | ✅ | ❌ | NRML unique - can be in UI layer |
| Legal basis | ✅ | ⚠️ | NRML explicit, DMN via annotations |
| Documentation | ⚠️ | ✅ | DMN has description fields |
| **Versioning** |
| Built-in versions | ✅ | ❌ | NRML validFrom, DMN external |
| Temporal logic | ❌ | ⚠️ | DMN 1.3+ may add |
| History tracking | ⚠️ | ❌ | Neither has full history |
| **Tooling** |
| Visual editors | ❌ | ✅✅✅ | DMN has many commercial tools |
| Execution engines | ⚠️ | ✅✅✅ | Custom vs Camunda/Drools/etc |
| Validators | ⚠️ | ✅✅ | Custom vs standard validators |
| Debuggers | ❌ | ✅ | DMN tools have debugging |
| Testing tools | ⚠️ | ✅ | DMN has standard test frameworks |
| **Standards & Adoption** |
| Industry standard | ❌ | ✅✅✅ | OMG standard |
| Government use | ❌ | ✅✅ | STTR in Netherlands |
| Community | ⚠️ | ✅✅✅ | DMN has large community |
| Training materials | ❌ | ✅✅✅ | DMN widely documented |
| Portability | ❌ | ✅✅ | DMN exchangeable between tools |
| **Integration** |
| Cross-law references | ✅ | ✅✅ | Both support, DMN has standard mechanism |
| BPMN integration | ❌ | ✅✅ | DMN designed to work with BPMN |
| API generation | ⚠️ | ✅ | DMN engines provide APIs |
| Import/export | ❌ | ✅ | DMN standard format |

**Legend:**
- ✅ Full support
- ⚠️ Partial support or workaround needed
- ❌ Not supported
- ✅✅ Strong support
- ✅✅✅ Excellent support

---

**Document Version:** 1.0
**Date:** 2025-10-31
**Author:** Machine Law Team
**Status:** Draft for Review
