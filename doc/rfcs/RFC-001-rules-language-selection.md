# RFC-001: Rules Language Selection

**Status:** Proposed | **Date:** 2025-11-05 | **Authors:** Tim, Anne

## Context

Machine Law requires a rules language for representing Dutch government legislation computationally. Multiple rules languages exist (DMN with FEEL, Datalog, NRML, and others), each with different characteristics and adoption levels. The choice of language fundamentally shapes the system's capabilities, maintainability, and ability to serve its specific mission.

During the proof-of-concept phase, we developed and tested a custom YAML-based language. This language is currently used in the `regelrecht-laws` submodule, which contains implementations of over 30 Dutch laws including Zorgtoeslagwet, Algemene Ouderdomswet, Participatiewet, and others. The POC has validated the approach's viability for representing real-world legislation.

## Decision

**Continue with and formalize the custom YAML-based rules language ("RegelRecht YAML"), with optional future conversion capabilities from existing rules languages.**

The language:
- Uses YAML syntax for structure and human readability
- Defines domain-specific constructs tailored to Dutch legislation
- Has been validated through POC implementations of actual laws
- Provides precise semantics matching our computational requirements

## Why

### Core Rationale

The decision centers on achieving **optimal fit** between language capabilities and mission requirements.

After evaluating all alternatives, the core trade-off is:

**Existing rules languages**: Provide varying levels of market adoption, ecosystem support, tooling, and compatibility. Market-driven standards offer cross-organization compatibility; NRML offers Dutch government domain alignment.

**Custom YAML**: Greater freedom and ownership. Complete control over semantics, versioning, and evolution without external dependencies. Better ability to limit functionality to exactly what's needed. No risk of external models being fed into the system with expectations of full feature support that may not align with our use case. No pressure to implement breaking changes or new features from external updates.

Since we are doing something new and complex, a rules language that is a 100% match for our specific requirements will benefit the project. The custom YAML language addresses these needs:

1. **Novel combination of concerns**: Supports temporal versioning, complex calculations, multi-law interactions, service references between laws, and explanation generation in one integrated system
2. **Evolving understanding**: As a research-oriented project, requirements continue to clarify through implementation; custom language can adapt without external constraints
3. **Precise semantics needed**: Government decisions require unambiguous interpretation; custom language provides exact semantics without vendor-specific ambiguities
4. **Proven viability**: POC with 30+ laws in `regelrecht-laws` demonstrates the YAML approach successfully models real legislation

### Conversion Strategy (Technically Feasible, Stakeholder-Driven)

Conversion from established formats to our YAML is technically feasible for features that align with our YAML's scope. The evaluated formats (DMN, NRML, Datalog) share core decision modeling concepts (inputs, rules, outputs, conditions, temporal aspects) that map to our YAML constructs. Features outside our YAML's intentionally limited scope would not be converted. The decision to implement converters is optional and will be driven by stakeholder adoption needs:

```
┌─────────┐      ┌──────────┐      ┌──────────────┐
│   DMN   │─────>│          │      │              │
├─────────┤      │          │      │   Machine    │
│  NRML   │─────>│Converters│─────>│     Law      │
├─────────┤      │(Feasible,│      │   (YAML)     │
│Datalog  │─────>│ optional)│      │              │
└─────────┘      └──────────┘      └──────────────┘
```

Benefits when stakeholders need this capability:
- Allow practitioners familiar with other formats to contribute
- Enable evaluation of existing law models in other formats
- Provide migration paths from legacy systems
- Maintain clear internal semantics through canonical YAML representation

**Technical feasibility**: Mapping from other formats to YAML is straightforward for core decision modeling concepts (inputs, rules, outputs, temporal aspects) that fall within our YAML's scope. Features in source formats that exceed our intentionally limited feature set would be excluded from conversion.

**Implementation decision**: Converters will be built when stakeholders demonstrate need, not preemptively.

### Trade-offs Acknowledged

**Custom language trade-offs:**
- Building and maintaining language infrastructure
- Creating documentation and examples
- Training users in new syntax and/or building custom tooling
- Potential for unique bugs or design oversights

**Mitigation strategies:**
- Start with minimal feature set, expand based on proven needs
- Learn from existing languages' design patterns
- Maintain comprehensive test suite
- Document all design decisions (via RFCs)
- Support conversion from other formats to leverage existing work (when stakeholders need it)

## Alternatives Considered

The alternatives to custom YAML fall into two categories:

**Market-driven standards** (DMN, Datalog, Prolog, OWL/RDF, Catala) are evaluated based on:
- Worldwide adoption and market penetration
- Tool ecosystem maturity
- Cross-organization compatibility
- Vendor support

**Dutch government-specific initiative** (NRML) is evaluated based on:
- Fit with Dutch government legislation needs
- Relationship to this initiative (both from MinBZK)
- Currently no external adoption beyond development team

Both categories represent valid alternatives to custom YAML, but are assessed using different criteria appropriate to their context.

*Note: Adoption levels (Low/Medium/High) for market-driven standards indicate worldwide usage and ecosystem maturity.*

### DMN with FEEL (Adoption: High)
**Strengths**:
- Most widely adopted decision modeling standard
- Strong vendor support and tool ecosystem
- Decision table paradigm natural for eligibility rules
- Business analysts can maintain decision tables

**Reality check**:
- ~80-90% of DMN usage focuses on decision tables
- FEEL expressions only ~10-20% due to complexity perception
- Tool support for FEEL varies (good in Camunda/Trisotech, variable elsewhere)
- Many projects use "DMN-lite" (mostly tables, minimal FEEL)

**Fit assessment**:
- Decision tables work well for simple eligibility checks
- Complex calculations (benefit amounts, tax formulas) need extensive FEEL
- Temporal versioning not native to standard
- Would need custom extensions for service references between laws
- External governance of standard may conflict with specific requirements

**When FEEL is needed**: Complex calculations, date/time logic, list operations, string manipulation, conditional expressions beyond tables

### NRML (Nederlandse Regelgeving Markup Language)
**Note:** NRML is developed within the same MinBZK initiative as this project. It is not a market-driven standard but rather a parallel effort to create a Dutch government-specific rules language. Currently, NRML has no external adoption beyond its development team.

**Strengths**:
- Purpose-built for Dutch regulations with government context
- Domain-specific constructs for regulatory complexity
- Shared organizational knowledge and potential collaboration

**Relationship to this project**:
- Both NRML and custom YAML emerge from MinBZK's law-as-code efforts
- Different approaches to solving similar problems
- Potential for knowledge sharing and alignment

**Fit assessment**:
- Strong domain alignment with Dutch legislation
- Broader feature set designed for wider range of regulatory scenarios; risk of additional complexity when only subset of capabilities needed
- As a related initiative, not subject to external market forces or governance
- Service reference patterns would need validation

### Datalog (Adoption: Low, growing)
**Strengths**:
- Declarative rules that read like legal text
- Excellent for legal reasoning and explanations
- Temporal extensions available (temporal Datalog)
- Guaranteed termination (safer than Prolog)
- Bottom-up evaluation with predictable performance
- Natural for "why not eligible?" reasoning

**Open source implementations**:
- **Souffle** (C++): High-performance, used by Oracle/AWS, compiles to native code
- **Flix** (JVM/Scala): Modern syntax, functional programming features
- **PyDatalog** (Python): Easy integration with Python ecosystem
- **Logica** (Google): Compiles to SQL/BigQuery

**Fit assessment**:
- Natural fit for legal rule representation
- Strong for interdependent rules and explanations
- Less accessible to non-technical stakeholders without tooling
- Would need additional layer for law metadata and service references

**Example capability**:
```datalog
% Temporal versioning built-in
income_limit("single", 35000, "2024-01-01", "2024-12-31").
income_limit("single", 37000, "2025-01-01", "2025-12-31").

% Reason tracking for explanations
ineligible_reason(Person, "te jong") :-
    person(Person), age(Person, Age), Age < 18.
```

### Prolog (Adoption: Medium)
**Strengths**:
- Powerful logical inference and backtracking
- Established in legal expert systems
- Natural querying capabilities
- Finds all solutions automatically

**Context**:
- Strong academic presence
- Some legacy systems in legal domain
- Smaller practitioner base than in past

**Fit assessment**:
- Powerful expressiveness for complex legal logic
- Maintenance challenges with larger codebases
- Less predictable performance than Datalog
- Accessibility challenges for non-technical reviewers

### OWL/RDF with SHACL (Adoption: High in semantic web)
**Strengths**:
- Excellent for knowledge representation and ontologies
- Semantic reasoning capabilities
- Interoperability through linked data
- Powerful SPARQL queries
- SHACL for constraint validation

**Context**:
- Widely used in semantic web contexts
- Strong in representing relationships and taxonomies
- European government adoption for data sharing

**Fit assessment**:
- Strong for representing law structures and relationships
- Calculations and procedural logic awkward to express
- Complex for non-technical users
- Better suited as complement than primary language
- Service references could map to linked data patterns

### Catala (Adoption: Low)
**Strengths**:
- Programming language specifically designed for law
- Strong formal foundations with proof capabilities
- Direct code generation from legal text
- French research backing

**Context**:
- New language (2020)
- Pilot projects in France
- Limited production deployments
- Small but growing community

**Fit assessment**:
- Interesting approach with strong theoretical foundation
- Early-stage maturity presents risks
- Limited tooling and ecosystem
- Would require significant investment to adopt
- Formal verification capabilities valuable but not immediate need

### Regelspraak / RuleSpeak (Adoption: Low)
**Strengths**:
- Controlled natural language approach readable by non-programmers
- Rules expressed in structured Dutch/English sentences
- Lower barrier for legal experts to review and validate
- Bridges gap between legal text and executable rules

**Context**:
- RuleSpeak originated from SBVR (Semantics of Business Vocabulary and Rules)
- Regelspraak is a Dutch adaptation of controlled natural language principles
- Used in some Dutch government contexts for rule documentation
- Focus on human readability over machine execution

**Fit assessment**:
- Strong for documentation and stakeholder communication
- Requires translation layer to executable code
- Less precise semantics than formal languages
- Complementary approach rather than primary execution language
- Could inform human-readable rule documentation alongside YAML

### Other Logic Programming Options
**Answer Set Programming (ASP)** (Adoption: Low): Handles non-monotonic reasoning common in legal rules; primarily research-focused

**Production Rules Engines** (Drools, JENA) (Adoption: High): Established in enterprise; more procedural than declarative; strong Java ecosystem

**LegalRuleML** (Adoption: Low): OASIS standard for legal rules; more expressive than DMN; growing in research but limited production use

## Related

- [DMN Specification](https://www.omg.org/spec/DMN/) - Decision Model and Notation standard
- [NRML](https://github.com/MinBZK/NRML) - Nederlandse Regelgeving Markup Language
- [Datalog](https://en.wikipedia.org/wiki/Datalog) - Declarative logic programming
- [Catala](https://catala-lang.org/) - Programming language for law
- [Souffle](https://souffle-lang.github.io/) - High-performance Datalog engine
- [PyDatalog](https://github.com/pcarbonn/pyDatalog) - Python Datalog implementation
- [RuleSpeak](http://www.rulespeak.com/) - Controlled natural language for business rules
- [SBVR](https://www.omg.org/spec/SBVR/) - Semantics of Business Vocabulary and Rules
