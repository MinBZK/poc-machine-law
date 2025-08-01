# Data Minimization Optimization Implementation

This document provides comprehensive documentation for the data minimization optimization system implemented in the Machine Law codebase.

## Overview

The data minimization optimization system prioritizes privacy by design, ensuring that law execution uses the least sensitive data first and minimizes total data usage. This implementation follows the principle that **data minimization takes priority over user experience optimization**.

## Key Principles

1. **Least Sensitive Data First**: Laws are ordered by sensitivity score (1-5 scale), with least sensitive laws executed first
2. **Early Elimination**: Use minimal data to eliminate laws that definitely don't apply (e.g., pension laws for young people)
3. **Progressive Data Collection**: Only collect additional sensitive data when necessary
4. **Comprehensive Metrics**: Track and measure data minimization effectiveness

## Architecture

### Core Components

1. **Data Sensitivity Classification** (`machine/sensitivity.py`)
   - 5-level sensitivity scale (1=administrative, 5=identifiers)
   - Automatic field classification based on patterns
   - Law-level sensitivity scoring

2. **Early Elimination Filter** (`machine/early_filter.py`)
   - Minimal data collection for initial filtering
   - Age/partnership/children-based law elimination
   - Simulation framework for testing

3. **Enhanced Service Layer** (`machine/service.py`)
   - New `get_data_minimized_sorted_laws()` method
   - Integration with existing impact-based sorting
   - Enable/disable data minimization features

4. **Advanced Metrics** (`machine/data_minimization_metrics.py`)
   - Session-based tracking
   - Historical analysis
   - Law-specific performance metrics

## Implementation Details

### 1. Data Sensitivity Classification System

#### Sensitivity Levels

```python
class SensitivityLevel(IntEnum):
    ADMINISTRATIVE = 1  # Dates, IDs, boolean flags
    DEMOGRAPHIC = 2     # Age ranges, general categories
    RANGES = 3         # Financial brackets, location areas
    PERSONAL_EXACT = 4  # Exact amounts, detailed attributes
    IDENTIFIERS = 5    # BSN, addresses, medical data
```

#### Field Classification

Fields are automatically classified using:
- **Exact matches**: Predefined mapping for common fields (BSN=5, LEEFTIJD=2, etc.)
- **Pattern matching**: Keywords in field names (BEDRAG→4, HEEFT_→1, etc.)
- **Type-based rules**: Data types combined with content patterns

#### Schema Extensions

The law schema now supports:

```yaml
# Law-level data minimization metadata
data_minimization:
  min_age: 18
  max_age: 67
  requires_partner: true
  requires_children: false
  early_elimination_fields:
    - "age"
    - "residence_country"

# Field-level sensitivity ratings
parameters:
  - name: "BSN"
    type: "string"
    data_sensitivity: 5  # Highest sensitivity

  - name: "is_eligible"
    type: "boolean"
    data_sensitivity: 1  # Lowest sensitivity
```

### 2. Early Elimination Strategy

The early elimination filter collects minimal data for initial law filtering:

```python
# Minimal data collection (lowest sensitivity)
minimal_data = {
    'age_bracket': '18-66',      # Sensitivity 2 (vs exact age=4)
    'has_partner': True,         # Sensitivity 1
    'residence_country': 'NL',   # Sensitivity 3 (vs full address=5)
    'has_children': False,       # Sensitivity 1
    'is_employed': True          # Sensitivity 2
}
```

**Early Elimination Rules:**
- **Age-based**: AOW pension (min_age: 67), Student finance (max_age: 30)
- **Partnership**: Partner-dependent benefits
- **Children**: Child-related laws
- **Employment**: Work-related benefits

### 3. Sensitivity-Based Law Ordering

Laws are now sorted by sensitivity score instead of financial impact:

```python
# Old: Impact-based (user experience optimized)
sorted(laws, key=lambda x: -x.impact_value)

# New: Sensitivity-based (privacy optimized)
sorted(laws, key=lambda x: x.sensitivity_score)
```

**Sensitivity Score Components:**
- **Primary**: Maximum sensitivity level (lower = better)
- **Secondary**: Average sensitivity (lower = better)
- **Tertiary**: Total field count (fewer = better)

### 4. Usage Examples

#### Basic Usage

```python
from machine.service import Services

# Initialize with data minimization enabled
services = Services(reference_date="2025-01-01")

# Get data-minimized law ordering
result = services.get_data_minimized_sorted_laws("123456789")

print(f"Early elimination rate: {result['metrics']['early_elimination_rate_percent']:.1f}%")
print(f"Max sensitivity accessed: {result['metrics']['max_sensitivity_accessed']}")

# Process laws in sensitivity order (least sensitive first)
for law in result['applicable_laws']:
    # Execute law with minimized data usage
    law_result = services.evaluate(
        service=law['service'],
        law=law['law'],
        parameters={"BSN": "123456789"}
    )
```

#### Advanced Configuration

```python
# Disable data minimization (fallback to impact-based)
services.set_data_minimization_enabled(False)

# Enable only early elimination, disable sensitivity ordering
result = services.get_data_minimized_sorted_laws(
    bsn="123456789",
    enable_early_elimination=True
)

# Get detailed metrics
metrics = services.get_data_minimization_metrics()
print(f"Services called: {metrics['services_called']}")
print(f"Sensitivity distribution: {metrics['sensitivity_distribution']}")
```

#### Metrics and Monitoring

```python
from machine.data_minimization_metrics import AdvancedDataMinimizationMetrics

# Advanced metrics tracking
metrics = AdvancedDataMinimizationMetrics()
metrics.start_session("123456789")

# ... process laws ...

session_metrics = metrics.end_session()
print(f"Session elimination rate: {session_metrics.early_elimination_rate:.1f}%")

# Historical analysis
analysis = metrics.get_historical_analysis(days_back=30)
print(f"30-day average elimination rate: {analysis['average_elimination_rate_percent']:.1f}%")

# Export metrics for analysis
metrics.export_metrics("data_minimization_report.json")
```

## Performance Impact

### Expected Benefits

- **50-70% reduction** in high-sensitivity data access for typical cases
- **Early elimination** of 30-40% of laws using minimal data
- **Progressive collection** prevents unnecessary sensitive data gathering
- **Faster initial filtering** using lightweight data
- **Lower computational overhead** for eliminated laws

### Trade-offs

- **User Experience**: Laws may not be ordered by personal relevance
- **Initial Setup**: Requires sensitivity metadata for law definitions
- **Processing Time**: Small overhead for sensitivity scoring

## Migration Guide

### For Existing Code

1. **Gradual Adoption**: Data minimization is opt-in and doesn't break existing functionality
2. **Backward Compatibility**: Original `get_sorted_discoverable_service_laws()` unchanged
3. **Feature Flag**: Use `set_data_minimization_enabled(False)` to disable

### For New Law Definitions

1. **Add Sensitivity Metadata**:
   ```yaml
   data_minimization:
     min_age: 18
     requires_partner: false

   parameters:
     - name: "BSN"
       data_sensitivity: 5
   ```

2. **Test Early Elimination**: Verify age/partnership filters work correctly

3. **Validate Sensitivity**: Check automatic field classification

## Testing

### Unit Tests

```bash
# Run data minimization test suite
python test_data_minimization.py

# Run specific component tests
python -m pytest machine/test_sensitivity.py
python -m pytest machine/test_early_filter.py
```

### Integration Tests

```bash
# Full system test with real law definitions
python -c "
from machine.service import Services
services = Services('2025-01-01')
result = services.get_data_minimized_sorted_laws('123456789')
print('Elimination rate:', result['metrics']['early_elimination_rate_percent'])
"
```

## Monitoring and Analytics

### Key Metrics to Track

1. **Early Elimination Rate**: Percentage of laws eliminated without sensitive data
2. **Max Sensitivity Accessed**: Highest sensitivity level needed per case
3. **Service Call Reduction**: Fewer cross-service data requests
4. **Field Access Distribution**: Breakdown by sensitivity level

### Dashboard Integration

```python
# Real-time metrics for monitoring dashboard
metrics_summary = services.get_data_minimization_metrics()

dashboard_data = {
    'elimination_rate': metrics_summary['early_elimination_rate_percent'],
    'privacy_score': 6 - metrics_summary['max_sensitivity_accessed'],  # Higher = better
    'services_used': metrics_summary['services_called_count'],
    'data_efficiency': metrics_summary['total_fields_accessed']
}
```

## Future Enhancements

### Planned Features

1. **Dynamic Sensitivity Adjustment**: Machine learning-based sensitivity scoring
2. **Cross-Law Data Sharing**: Optimized caching between related laws
3. **Audit Trail**: Detailed logging for compliance purposes
4. **A/B Testing**: Compare data minimization vs impact-based ordering

### Configuration Options

1. **Sensitivity Thresholds**: Configurable limits for different environments
2. **Custom Elimination Rules**: Domain-specific early filtering logic
3. **Privacy Policies**: Role-based data access controls

## Compliance and Legal Considerations

### GDPR Compliance

- **Data Minimization**: Article 5(1)(c) - data should be adequate, relevant and limited
- **Privacy by Design**: Article 25 - data protection by design and by default
- **Purpose Limitation**: Article 5(1)(b) - data collected for specified purposes

### Audit Requirements

- **Data Access Logging**: Every field access is tracked with sensitivity level
- **Decision Transparency**: Clear reasoning for law elimination/inclusion
- **Retention Policies**: Configurable data retention based on legal requirements

## Troubleshooting

### Common Issues

1. **High Sensitivity Scores**: Check automatic field classification accuracy
2. **Low Elimination Rates**: Verify early elimination rules match law requirements
3. **Performance Issues**: Monitor service call patterns and caching effectiveness

### Debug Tools

```python
# Debug field classification
from machine.sensitivity import DataSensitivityClassifier
classifier = DataSensitivityClassifier()
sensitivity = classifier.classify_field("UNKNOWN_FIELD", "string")
print(f"Auto-classified as: {sensitivity.name}")

# Debug early elimination
from machine.early_filter import EarlyEliminationFilter
filter = EarlyEliminationFilter()
minimal_data = filter.get_minimal_eligibility_data("123456789")
print(f"Minimal data collected: {minimal_data}")
```

## Contact and Support

For questions about the data minimization implementation, please:

1. Check this documentation first
2. Review the test examples in `test_data_minimization.py`
3. Examine the law schema extensions in `schema/v0.1.5/schema.json`
4. Create an issue with detailed reproduction steps if problems persist

---

**Implementation Status**: ✅ Complete and tested
**Last Updated**: 2025-08-01
**Version**: 1.0.0
