# RFC-000: RFC Process for Machine Law

**Status:** Accepted | **Date:** 2025-11-05 | **Authors:** Tim

## Context

Machine Law needs structured documentation for design decisions, architectural choices, and implementation patterns with historical record of rationale and alternatives.

## Decision

**Adopt RFC (Request for Comments) process with standalone markdown documents in `doc/rfcs/`.**

## Structure

```markdown
# RFC-NNN: Title

**Status:** [Draft | Proposed | Accepted | Rejected | Superseded]
**Date:** YYYY-MM-DD
**Authors:** Name(s)

## Context
Why is this decision needed?

## Decision
What was decided?

## Why
Benefits, tradeoffs, alternatives
```

**Numbering**: Sequential (RFC-000 reserved for process, RFC-001+)
**Statuses**: Draft, Proposed, Accepted, Rejected, Superseded

## Why

**Benefits:**
- **Historical context**: Future contributors understand why decisions were made
- **Structured discussion**: Clear articulation of problems and solutions
- **Knowledge transfer**: Documents tribal knowledge
- **Version control**: Git tracks evolution
- **Discoverability**: All decisions in one location

**When to write RFC**: Law representation formats, execution engine architecture, computational model design, integration patterns, web interface architecture, design patterns affecting multiple components

**Don't write RFC for**: Bug fixes, routine implementation, temporary workarounds, individual law implementations

**Tradeoffs**: Writing overhead, maintenance burden; mitigated by complementing (not replacing) code comments

## Alternatives Rejected

- **Code comments**: Hard to discover, no structure
- **Wiki**: Separate from repo, version control unclear
- **GitHub Issues**: Not structured for long-term reference

## Related

Inspired by [Rust RFCs](https://github.com/rust-lang/rfcs), [Python PEPs](https://www.python.org/dev/peps/), [ADRs](https://adr.github.io/)
