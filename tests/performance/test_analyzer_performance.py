import json
import statistics
import time
from pathlib import Path

from machine.nrml.item_type_analyzer import determine_item_type as rule_based_analyzer
from machine.nrml.schema_based_item_type_analyzer import (
    NrmlSchemaBasedItemTypeAnalyzer,
)
from machine.nrml.schema_based_item_type_analyzer import (
    determine_item_type as schema_based_analyzer,
)


def load_test_data():
    """Load test data from NRML files"""
    project_root = Path(__file__).parent.parent.parent
    brp_path = project_root / "law" / "nrml" / "brp_nationaliteit.nrml.json"

    with open(brp_path) as f:
        data = json.load(f)

    # Extract all items for testing
    items = []
    for fact_id, fact in data["facts"].items():
        for item_id, item in fact["items"].items():
            items.append((f"{fact_id}/{item_id}", item))

    return items


def measure_analyzer_performance(analyzer_func, items: list, iterations: int = 1000):
    """Measure performance of an analyzer function"""
    times = []

    for _ in range(iterations):
        start_time = time.perf_counter()

        for item_id, item in items:
            analyzer_func(item)

        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "total_calls": len(items) * iterations,
    }


def test_single_call_performance():
    """Test single call performance with detailed timing"""
    items = load_test_data()
    iterations = 10000

    print("=== Single Call Performance Comparison ===")
    print(f"Testing with {len(items)} items, {iterations} iterations each")
    print()

    # Test rule-based analyzer
    print("Testing Rule-Based Analyzer...")
    rule_stats = measure_analyzer_performance(rule_based_analyzer, items, iterations)

    # Test schema-based analyzer
    print("Testing Schema-Based Analyzer...")
    schema_stats = measure_analyzer_performance(schema_based_analyzer, items, iterations)

    # Print results
    print(f"\n{'Metric':<20} {'Rule-Based':<15} {'Schema-Based':<15} {'Difference':<15}")
    print("-" * 70)

    metrics = ["mean", "median", "min", "max", "stdev"]
    for metric in metrics:
        rule_val = rule_stats[metric] * 1000  # Convert to ms
        schema_val = schema_stats[metric] * 1000  # Convert to ms
        diff = schema_val / rule_val if rule_val > 0 else float("inf")

        print(f"{metric.capitalize():<20} {rule_val:<14.4f}ms {schema_val:<14.4f}ms {diff:<14.2f}x")

    print(f"\nTotal function calls: {rule_stats['total_calls']:,}")
    print(f"Calls per second (rule-based): {rule_stats['total_calls'] / rule_stats['mean']:,.0f}")
    print(f"Calls per second (schema-based): {schema_stats['total_calls'] / schema_stats['mean']:,.0f}")


def test_initialization_overhead():
    """Test initialization overhead for schema-based analyzer"""
    print("\n=== Initialization Overhead ===")

    iterations = 100
    init_times = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        NrmlSchemaBasedItemTypeAnalyzer()
        end_time = time.perf_counter()
        init_times.append(end_time - start_time)

    init_stats = {
        "mean": statistics.mean(init_times),
        "median": statistics.median(init_times),
        "stdev": statistics.stdev(init_times) if len(init_times) > 1 else 0,
        "min": min(init_times),
        "max": max(init_times),
    }

    print(f"Schema analyzer initialization ({iterations} runs):")
    for metric, value in init_stats.items():
        print(f"  {metric.capitalize()}: {value * 1000:.4f}ms")


def test_memory_usage_approximation():
    """Approximate memory usage difference"""
    print("\n=== Memory Usage Approximation ===")

    import sys

    # Test rule-based (no persistent state)
    rule_size = sys.getsizeof(rule_based_analyzer)

    # Test schema-based (has loaded schema)
    schema_analyzer = NrmlSchemaBasedItemTypeAnalyzer()
    schema_size = (
        sys.getsizeof(schema_analyzer)
        + sys.getsizeof(schema_analyzer.schema)
        + sys.getsizeof(schema_analyzer.item_type_schemas)
        + sum(sys.getsizeof(schema) for schema in schema_analyzer.item_type_schemas.values())
    )

    print(f"Rule-based analyzer: ~{rule_size:,} bytes")
    print(f"Schema-based analyzer: ~{schema_size:,} bytes")
    print(f"Difference: ~{schema_size - rule_size:,} bytes ({(schema_size / rule_size):.1f}x larger)")


def test_accuracy_comparison():
    """Test accuracy comparison between analyzers"""
    print("\n=== Accuracy Comparison ===")

    items = load_test_data()
    matches = 0
    total = 0

    for item_id, item in items:
        rule_result = rule_based_analyzer(item)
        schema_result = schema_based_analyzer(item)

        total += 1
        if rule_result.value == schema_result.value:
            matches += 1
        else:
            print(f"Mismatch for {item_id}: rule={rule_result.value}, schema={schema_result.value}")

    accuracy = (matches / total) * 100 if total > 0 else 0
    print(f"Accuracy match: {matches}/{total} ({accuracy:.1f}%)")


if __name__ == "__main__":
    print("NRML Item Type Analyzer Performance Comparison")
    print("=" * 60)

    test_single_call_performance()
    test_initialization_overhead()
    test_memory_usage_approximation()
    test_accuracy_comparison()

    print("\n=== Summary ===")
    print("Rule-based analyzer:")
    print("  + Faster per-call performance")
    print("  + Lower memory usage")
    print("  + No initialization overhead")
    print("  - Less accurate validation")
    print("  - Manual maintenance required")
    print()
    print("Schema-based analyzer:")
    print("  + More accurate validation")
    print("  + Automatic schema updates")
    print("  + Rich introspection capabilities")
    print("  - Slower per-call performance")
    print("  - Higher memory usage")
    print("  - Initialization overhead")
