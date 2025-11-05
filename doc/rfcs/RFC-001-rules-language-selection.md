# RFC-001: Rules Language Selection

**Status:** Accepted | **Date:** 2025-11-05 | **Authors:** Tim, Anne

## Context

Machine Law requires a rules language for representing Dutch government legislation computationally. Several established standards exist (NRML, DMN with FEEL, Datalog), each with proven track records in various domains. The choice of language fundamentally shapes the system's capabilities, maintainability, and ability to serve its specific mission.

During the proof-of-concept phase, we developed and tested a custom YAML-based language. This language is currently used in the `regelrecht-laws` submodule, which contains implementations of over 30 Dutch laws including Zorgtoeslagwet, Algemene Ouderdomswet, Participatiewet, and others. The POC has validated the approach's viability for representing real-world legislation.

## Decision

**Continue with and formalize the custom YAML-based rules language, with optional future conversion capabilities from established standards.**

The language:
- Uses YAML syntax for structure and human readability
- Defines domain-specific constructs tailored to Dutch legislation
- Has been validated through POC implementations of actual laws
- Can technically support conversion from established formats (DMN, NRML, Datalog); implemented when stakeholders need it
- Provides precise semantics matching our computational requirements

## Why

### Core Rationale

The decision centers on achieving **optimal fit** between language capabilities and mission requirements.

After evaluating all alternatives, the core trade-off is:

**Established standards** (DMN, NRML, Datalog): Market adoption and proven track records provide confidence, ecosystem support, tooling, and cross-organization compatibility.

**Custom YAML**: Greater freedom and ownership. Complete control over semantics, versioning, and evolution without external dependencies. Better ability to limit functionality to exactly what's needed. No risk of external models being fed into the system with expectations of full feature support that may not align with our use case. No pressure to implement breaking changes or new features from external standard updates.

Since we are doing something new and complex, a rules language that is a 100% match for our specific requirements will benefit the project. The custom YAML language addresses these needs:

1. **Novel combination of concerns**: Supports temporal versioning, complex calculations, multi-law interactions, service references between laws, and explanation generation in one integrated system
2. **Evolving understanding**: As a research-oriented project, requirements continue to clarify through implementation; custom language can adapt without external constraints
3. **Precise semantics needed**: Government decisions require unambiguous interpretation; custom language provides exact semantics without vendor-specific ambiguities
4. **Proven viability**: POC with 30+ laws in `regelrecht-laws` demonstrates the YAML approach successfully models real legislation
5. **Conversion capability**: Can serve as compilation target from other formats for features within our scope (technically feasible, implemented when stakeholders need it)

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
- Learn from established languages' design patterns
- Maintain comprehensive test suite
- Document all design decisions (via RFCs)
- Support conversion from established formats to leverage existing work

**Established language trade-offs:**
- Features designed for different domains may not align perfectly
- External governance of standards may conflict with mission needs
- Risk of users providing models using unsupported features
- Semantic ambiguities in standards require interpretation

## Alternatives Considered

*Note: Adoption ratings (X/10) indicate worldwide usage and market penetration, from research conducted to understand the maturity and ecosystem support of each option.*

### DMN with FEEL (Adoption: 9/10)
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

### NRML (Nederlandse Regelgeving Markup Language) (Adoption: 2/10)
**Strengths**:
- Purpose-built for Dutch regulations
- Domain-specific constructs for regulatory complexity
- Developed with Dutch government context in mind

**Context**:
- Netherlands-specific adoption
- Limited to Dutch regulatory domain
- Smaller ecosystem and community

**Fit assessment**:
- Strong domain alignment with Dutch legislation
- Broader feature set designed for wider range of regulatory scenarios; risk of additional complexity when only subset of capabilities needed
- Limited tooling compared to international standards
- Service reference patterns would need validation

### Datalog (Adoption: 3/10, growing)
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

### Prolog (Adoption: 5/10)
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

### OWL/RDF with SHACL (Adoption: 7/10 in semantic web)
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

### Catala (Adoption: 1/10)
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

### Other Logic Programming Options
**Answer Set Programming (ASP)** (Adoption: 2/10): Handles non-monotonic reasoning common in legal rules; primarily research-focused

**Production Rules Engines** (Drools, JENA) (Adoption: 8/10): Established in enterprise; more procedural than declarative; strong Java ecosystem

**LegalRuleML** (Adoption: 4/10): OASIS standard for legal rules; more expressive than DMN; growing in research but limited production use

### Comparative Summary

**Best for straightforward decisions**: DMN (when non-technical stakeholders need to review)
**Best for complex reasoning**: Datalog (interdependencies and explanations)
**Best for Dutch domain alignment**: NRML (if external governance acceptable)
**Best for semantic web integration**: OWL/RDF (knowledge graphs and data sharing)
**Best for formal verification**: Catala (though immature)

## Related

- [DMN Specification](https://www.omg.org/spec/DMN/) - Decision Model and Notation standard
- [NRML](https://github.com/MinBZK/NRML) - Nederlandse Regelgeving Markup Language
- [Datalog](https://en.wikipedia.org/wiki/Datalog) - Declarative logic programming
- [Catala](https://catala-lang.org/) - Programming language for law
- [Souffle](https://souffle-lang.github.io/) - High-performance Datalog engine
- [PyDatalog](https://github.com/pcarbonn/pyDatalog) - Python Datalog implementation
