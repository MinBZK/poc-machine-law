# Architecture

## Overview

This architecture represents a rules engine [law](../law) system designed for processing legal and administrative rules
in a flexible, maintainable way. The system follows a domain-driven design with event sourcing to provide transparency,
auditability, and flexibility in rule application.

The rules engine allows domain-specific rules to be defined as data (in YAML) rather than code, enabling non-technical
experts to manage rules while ensuring consistent, transparent application. The system handles complex rule
dependencies, recursive rule resolution, and integration with event-sourced domain models.

```mermaid
flowchart TD
%% Core components with detailed explanations
    Client([Client Code])
    Services["Services
    The Orchestrator
- Entry point for rule evaluation
- Manages service-specific rules
- Routes to appropriate domain"]

RuleService["RuleService
Domain-Specific Rules
- Handles rules for one service
- Creates/caches RulesEngines
- Finds applicable rules by date"]

RulesEngine["RulesEngine
The Evaluation Core
- Processes requirements
- Evaluates actions in dependency order
- Creates traceable execution path"]

RuleContext["RuleContext
The Value Resolver
- Resolves $references in priority order
- Looks up values from multiple sources
- Handles service cross-references
- Records resolution history"]

RuleResolver["RuleResolver
Rule Loading
- Finds rules in files
- Loads YAML specifications
- Selects correct version by date"]

ClaimManager["ClaimManager
Claim Processing
- Submits/approves/rejects claims
- Tracks claim history via events
- Rebuilds current claim state"]

%% Data sources
Rules[(YAML Rule Files
- Requirements
- Actions
- Definitions)]

ClaimData[(Claim Data
Current state of claims
- Service, key, value pairs
- Used for rule evaluation
- What claims are NOW)]

ClaimEvents[(Claim Events
History of claim changes
- Created, Approved, Rejected
- Source of truth
- What HAPPENED to claims)]

Sources[(Source Data
Tables, external data)]

%% Event sourcing components
Cases[(Case Events)]

%% Flow connections
Client -->|" evaluate(service, law, params) "|Services

Services -->|" Find domain rules "|RuleService
Services -->|" Load rule specs "|RuleResolver

RuleResolver -->|" Read definitions "|Rules

RuleService --> |" Create or reuse "|RulesEngine

RulesEngine -->|" Use for value resolution "| RuleContext

RuleContext -.->|" Query tables "|Sources
RuleContext -.->|" Look up current values "|ClaimData
RuleContext -.->|" Recursive resolution "|Services
RuleContext -.->|" Access definitions "|RuleResolver

Services -.->|"Process cases "|Cases
Services -.->|"Access claims manager "|ClaimManager

ClaimManager -.-> |" Store events "|ClaimEvents
ClaimEvents -.->|" Rebuild state "|ClaimData
```

## How It Works

The system operates through several key mechanisms:

### Rule Evaluation Flow

1. Client code initiates evaluation by calling `Services.evaluate()` with a service type, law, and parameters
2. Services routes to the appropriate RuleService for the domain
3. RuleService creates or retrieves a cached RulesEngine for the specific law and date
4. RulesEngine evaluates requirements, and if met, executes actions in dependency order
5. Throughout evaluation, RuleContext resolves values from multiple sources

### Value Resolution

RuleContext resolves references (paths like `$variable_name`) by checking multiple sources in priority order:

1. Claims (citizen-provided values)
2. Local scope (within current context)
3. Rule definitions
4. Input parameters
5. Previously calculated outputs
6. External data sources
7. Other services (recursive resolution)

### Event Sourcing Integration

The system uses event sourcing for cases and claims:

- Events are immutable facts about what happened (the source of truth)
- Current state is derived by applying all events in sequence
- Rule evaluation works with the current state, not directly with events
- Case events can trigger rules automatically through event handlers
