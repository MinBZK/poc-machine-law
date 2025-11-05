"""Benchmark FEEL evaluator performance."""
import time
from machine.dmn.feel_evaluator import FEELEvaluator

def benchmark_simple_expression():
    """Benchmark simple variable lookup."""
    evaluator = FEELEvaluator()
    context = {'x': 10, 'y': 20}

    iterations = 10000
    start = time.time()
    for _ in range(iterations):
        result = evaluator.evaluate('x + y', context)
    elapsed = time.time() - start

    print(f"Simple expression (x + y):")
    print(f"  {iterations} iterations in {elapsed:.3f}s")
    print(f"  {iterations/elapsed:.0f} evals/sec")
    print(f"  {elapsed/iterations*1000:.2f}ms per eval")
    return elapsed

def benchmark_nested_if():
    """Benchmark nested if-then-else."""
    evaluator = FEELEvaluator()
    context = {'a': True, 'b': False, 'c': 10, 'd': 20}

    expr = 'if a then if b then c else d else c + d'

    iterations = 10000
    start = time.time()
    for _ in range(iterations):
        result = evaluator.evaluate(expr, context)
    elapsed = time.time() - start

    print(f"\nNested if-then-else:")
    print(f"  {iterations} iterations in {elapsed:.3f}s")
    print(f"  {iterations/elapsed:.0f} evals/sec")
    print(f"  {elapsed/iterations*1000:.2f}ms per eval")
    return elapsed

def benchmark_complex_dmn():
    """Benchmark realistic DMN expression."""
    evaluator = FEELEvaluator()
    context = {
        'heeft_partner': False,
        'toetsingsinkomen': 25000,
        'vermogen': 50000,
        'constants': lambda: {
            'DREMPELINKOMEN_ALLEENSTAANDE': 39719,
            'DREMPELINKOMEN_TOESLAGPARTNER': 50206,
            'VERMOGENSGRENS_ALLEENSTAANDE': 141896,
            'VERMOGENSGRENS_TOESLAGPARTNER': 179429
        }
    }

    expr = 'if heeft_partner then constants().DREMPELINKOMEN_TOESLAGPARTNER else constants().DREMPELINKOMEN_ALLEENSTAANDE'

    iterations = 10000
    start = time.time()
    for _ in range(iterations):
        result = evaluator.evaluate(expr, context)
    elapsed = time.time() - start

    print(f"\nRealistic DMN expression (if-then-else with function calls):")
    print(f"  {iterations} iterations in {elapsed:.3f}s")
    print(f"  {iterations/elapsed:.0f} evals/sec")
    print(f"  {elapsed/iterations*1000:.2f}ms per eval")
    return elapsed

def benchmark_full_dmn_decision():
    """Benchmark a full DMN decision evaluation."""
    from pathlib import Path
    from machine.dmn import DMNEngine
    from datetime import date

    engine = DMNEngine()
    dmn_spec = engine.load_dmn(Path("dmn/zorgtoeslag_toeslagen_2025.dmn"))

    parameters = {
        'person': {
            'birth_date': date(1985, 5, 15),
            'partnership_status': 'alleenstaand',
            'health_insurance_status': 'verzekerd',
            'is_resident': True,
        },
        'reference_date': date(2025, 1, 1),
        'tax_data': {
            'box1_inkomen': 2500000,
            'box2_inkomen': 0,
            'box3_inkomen': 0,
            'vermogen': 5000000,
        },
        'income_data': {
            'work_income': 3500000,
            'unemployment_benefit': 0,
            'disability_benefit': 0,
            'pension': 0,
            'other_benefits': 0,
        },
        'partner_income_data': None,
    }

    iterations = 100  # Fewer iterations for full evaluation
    start = time.time()
    for _ in range(iterations):
        result = engine.evaluate(dmn_spec, "decision_hoogte_toeslag", parameters)
    elapsed = time.time() - start

    print(f"\nFull DMN decision evaluation (hoogte_toeslag with 18 decisions):")
    print(f"  {iterations} iterations in {elapsed:.3f}s")
    print(f"  {iterations/elapsed:.1f} evals/sec")
    print(f"  {elapsed/iterations*1000:.1f}ms per eval")
    return elapsed

if __name__ == '__main__':
    print("="*70)
    print("FEEL Evaluator Performance Benchmark")
    print("="*70)

    benchmark_simple_expression()
    benchmark_nested_if()
    benchmark_complex_dmn()
    benchmark_full_dmn_decision()

    print("\n" + "="*70)
    print("Analysis:")
    print("- Simple expressions: Very fast (microseconds)")
    print("- Complex expressions: String parsing overhead becomes noticeable")
    print("- Full DMN: Multiple decisions compound the overhead")
    print("="*70)
