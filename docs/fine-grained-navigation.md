# Fine-Grained Navigation Between Law Text and Regelspraak

## Implementation Overview

This document describes the implementation of fine-grained bidirectional navigation between Dutch law text and machine-executable rules (regelspraak) in the Machine Law project.

### Features Implemented

1. **Law Text → Regelspraak Navigation**
   - Inline indicators on law paragraphs showing related machine rules
   - Expandable sections showing all regelspraak implementations
   - Direct links to specific YAML sections with highlighting

2. **Regelspraak → Law Text Navigation**
   - Sidebar panel showing all legal basis references
   - Direct links from YAML fields to corresponding law articles
   - Automatic highlighting of targeted sections

3. **Article Detail View**
   - Focused view of individual law articles
   - Shows all regelspraak implementations referencing the article
   - Paragraph-level yaml references with descriptions

### Technical Implementation

#### Data Model
The navigation is based on the existing cross-reference structure in law content YAML files:

```yaml
# In laws/content/BWBR0015703.yaml
paragraphs:
  - number: 1
    content: "Paragraph text"
    yaml_references:
      - file: "law/participatiewet/bijstand/SZW-2023-01-01.yaml"
        section: "input.LEEFTIJD"
        description: "Age requirement for assistance"
        line_reference: "input.LEEFTIJD.legal_basis"
```

#### UI Components

1. **Inline Reference Indicators**
   - Blue pill-shaped buttons showing number of rules
   - Click to expand/collapse reference details
   - Styled with Material Design-inspired colors

2. **Reference Cards**
   - Show rule description and YAML section path
   - Direct links with anchor support (#section-name)
   - Automatic highlighting on arrival

3. **Sidebar Navigation**
   - Sticky sidebar showing all legal references
   - Grouped by section type (parameters, input, output, etc.)
   - Quick navigation to law articles

### Usage Examples

1. **From Law to Rules**:
   - Navigate to `/wetten/BWBR0015703` (Participatiewet)
   - Look for blue indicators next to paragraphs
   - Click to see which rules implement that paragraph
   - Click links to jump directly to YAML sections

2. **From Rules to Law**:
   - Navigate to `/wetten/BWBR0015703/yaml/law/participatiewet/bijstand/SZW-2023-01-01.yaml`
   - Use the sidebar to see all legal basis references
   - Click article links to view the original law text
   - Arrive at specific paragraphs with YAML references highlighted

3. **Article Deep Dive**:
   - Navigate to `/wetten/BWBR0015703/artikel/Artikel11`
   - See all rules that reference this article
   - View paragraph-by-paragraph breakdown
   - Direct navigation to specific YAML implementations

### Styling

- **Colors**:
  - Primary: #1976d2 (blue)
  - Background: #e3f2fd (light blue)
  - Highlight: #fffbe6 (yellow)
- **Animations**: Smooth transitions on hover and expand/collapse
- **Responsive**: Works on mobile and desktop devices

### Future Enhancements

1. **Search Integration**: Search for specific legal concepts across both law text and rules
2. **Visual Graph**: Interactive visualization of law-rule relationships
3. **Version Tracking**: Show how references change over time
4. **API Access**: REST endpoints for programmatic access to cross-references
