# Demo Mode Documentation

## Overview

Demo Mode is a browser-based presentation interface for demonstrating machine-executable Dutch law files and running feature tests. It replaces the need for showing PyCharm during demos.

## Features

### 1. YAML Law Viewer
- Browse all law files in the `law/` directory
- Collapsible YAML structure for easy navigation
- Default collapsed sections for `legal_basis`, `references`, `explanation`, etc.
- Search functionality to quickly find laws
- Clean, presentation-focused interface

### 2. Cross-Law Navigation
- Automatic link detection for `service_reference` fields
- Click links to navigate between related laws
- Example: Zorgtoeslag → Zorgverzekeringswet

### 3. Feature Test Runner
- View law-specific features (from `law/**/*.feature`)
- View standalone features (from `features/*.feature`)
- Run individual feature tests with a button click
- View test results with pass/fail status
- Expandable scenario details

## Usage

### Starting Demo Mode

1. Start the web server:
   ```bash
   uv run web/main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/demo
   ```

### Navigation

- **Home Page**: Shows all available laws with search functionality
- **Law Viewer**: Click any law to view its YAML structure
- **Features**: Navigate to `/demo/features` to run tests

### Keyboard Shortcuts

- `Cmd/Ctrl + [` : Collapse all sections
- `Cmd/Ctrl + ]` : Expand all sections

### Demo Flow Example

1. Start at `/demo` and search for "zorgtoeslag"
2. Click on "Zorgtoeslag" to view the law
3. Use "Collapse All" to see the overview
4. Expand sections progressively: properties → input → output → parameters
5. Click on service_reference links to navigate to related laws (e.g., zorgverzekeringswet)
6. Navigate to Features tab to run tests
7. Run a feature test and view results

## File Structure

```
web/
├── routers/demo.py          # FastAPI routes for demo mode
├── demo/
│   ├── yaml_renderer.py     # YAML parsing and HTML rendering
│   └── feature_runner.py    # Behave feature test execution
├── templates/demo/
│   ├── base.html            # Base template
│   ├── index.html           # Law browser
│   ├── law_viewer.html      # YAML viewer
│   └── feature_viewer.html  # Feature test interface
└── static/
    ├── css/demo.css         # Demo mode styling
    └── js/demo.js           # Interactive functionality
```

## API Endpoints

- `GET /demo` - Main demo page with law list
- `GET /demo/law/{law_path}` - View specific law YAML
- `GET /demo/features` - Feature test browser
- `POST /demo/run-feature` - Execute a feature test
- `GET /demo/api/laws` - JSON API for law metadata

## Customization

### Default Collapsed Sections

Edit `web/demo/yaml_renderer.py` and modify the `should_collapse_by_default()` function:

```python
def should_collapse_by_default(key: str) -> bool:
    collapse_keys = {
        "legal_basis",
        "references",
        "explanation",
        "requirements",
        "actions",
    }
    return key in collapse_keys
```

### Styling

Edit `web/static/css/demo.css` to customize colors, fonts, and layout.

## Troubleshooting

### Law files not showing up

Check that YAML files exist in the `law/` directory and have valid YAML syntax.

### Feature tests failing to run

Ensure `behave` is installed and feature files have proper Gherkin syntax.

### Cross-law links not working

Verify that `service_reference` fields in YAML contain both `service` and `law` keys.

## Performance

- Law discovery is performed on each request (no caching yet)
- YAML parsing and HTML rendering happens on-demand
- Feature tests run synchronously with 5-minute timeout
