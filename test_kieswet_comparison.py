"""Direct comparison of k ieswet v0.1.6 and v0.1.7 implementations."""

import pandas as pd
from datetime import date
from eventsourcing.utils import clear_topic_cache

from machine.service import Services
from machine.law_evaluator import LawEvaluator
from machine.data_context import DataContext


def test_v016(bsn: str, reference_date: str) -> dict:
    """Test kieswet using v0.1.6 (Services-based) architecture."""
    print("\n=== Testing v0.1.6 (Services-based) ===")

    # Create Services instance
    services = Services(reference_date)

    # Set up verkiezingen data
    verkiezingen_df = pd.DataFrame([{
        "type": "TWEEDE_KAMER",
        "verkiezingsdatum": "2025-10-29"
    }])
    services.set_source_dataframe("KIESRAAD", "verkiezingen", verkiezingen_df)

    # Evaluate kieswet
    result = services.evaluate(
        service="KIESRAAD",
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=reference_date
    )

    print(f"  Requirements met: {result.requirements_met}")
    print(f"  Output: {result.output}")

    return {
        "requirements_met": result.requirements_met,
        "output": result.output
    }


def test_v017(bsn: str, reference_date: str) -> dict:
    """Test kieswet using v0.1.7 (LawEvaluator-based) architecture."""
    print("\n=== Testing v0.1.7 (Context-based) ===")

    # Create LawEvaluator with DataContext
    data_context = DataContext()
    law_evaluator = LawEvaluator(
        reference_date=reference_date,
        data_context=data_context
    )

    # Set up verkiezingen data
    verkiezingen_df = pd.DataFrame([{
        "type": "TWEEDE_KAMER",
        "verkiezingsdatum": "2025-10-29"
    }])
    data_context.add_source("KIESRAAD", "verkiezingen", verkiezingen_df)

    # Evaluate kieswet
    result = law_evaluator.evaluate_law(
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=reference_date
    )

    print(f"  Requirements met: {result.requirements_met}")
    print(f"  Output: {result.output}")

    return {
        "requirements_met": result.requirements_met,
        "output": result.output
    }


def setup_test_data_v016(services: Services, scenario: str, bsn: str):
    """Set up test data for v0.1.6."""
    if scenario == "eligible":
        # Dutch, 18+, no exclusion
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "2006-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        services.set_source_dataframe("RvIG", "personen", personen_df)

    elif scenario == "non_dutch":
        # Non-Dutch
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "DUITS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        services.set_source_dataframe("RvIG", "personen", personen_df)

    elif scenario == "underage":
        # Under 18
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "2008-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        services.set_source_dataframe("RvIG", "personen", personen_df)

    elif scenario == "excluded":
        # Court-ordered exclusion
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        services.set_source_dataframe("RvIG", "personen", personen_df)

        ontzettingen_df = pd.DataFrame([
            {
                "bsn": bsn,
                "type": "KIESRECHT",
                "startdatum": "2023-01-01",
                "einddatum": "2024-01-01"
            },
            {
                "bsn": bsn,
                "type": "KIESRECHT",
                "startdatum": "2024-06-01",
                "einddatum": "2025-12-01"
            }
        ])
        services.set_source_dataframe("JUSTID", "ontzettingen", ontzettingen_df)

    elif scenario == "detained":
        # Detained but eligible
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        services.set_source_dataframe("RvIG", "personen", personen_df)

        ontzettingen_df = pd.DataFrame([{
            "bsn": bsn,
            "type": "KIESRECHT",
            "startdatum": "2023-01-01",
            "einddatum": "2024-01-01"
        }])
        services.set_source_dataframe("JUSTID", "ontzettingen", ontzettingen_df)

        detenties_df = pd.DataFrame([{
            "bsn": bsn,
            "status": "INGESLOTEN"
        }])
        services.set_source_dataframe("DJI", "detenties", detenties_df)


def setup_test_data_v017(data_context: DataContext, scenario: str, bsn: str):
    """Set up test data for v0.1.7."""
    if scenario == "eligible":
        # Dutch, 18+, no exclusion
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "2006-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        data_context.add_source("RvIG", "personen", personen_df)

    elif scenario == "non_dutch":
        # Non-Dutch
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "DUITS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        data_context.add_source("RvIG", "personen", personen_df)

    elif scenario == "underage":
        # Under 18
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "2008-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        data_context.add_source("RvIG", "personen", personen_df)

    elif scenario == "excluded":
        # Court-ordered exclusion
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        data_context.add_source("RvIG", "personen", personen_df)

        ontzettingen_df = pd.DataFrame([
            {
                "bsn": bsn,
                "type": "KIESRECHT",
                "startdatum": "2023-01-01",
                "einddatum": "2024-01-01"
            },
            {
                "bsn": bsn,
                "type": "KIESRECHT",
                "startdatum": "2024-06-01",
                "einddatum": "2025-12-01"
            }
        ])
        data_context.add_source("JUSTID", "ontzettingen", ontzettingen_df)

    elif scenario == "detained":
        # Detained but eligible
        personen_df = pd.DataFrame([{
            "bsn": bsn,
            "geboortedatum": "1990-01-01",
            "nationaliteit": "NEDERLANDS",
            "verblijfsadres": "Amsterdam",
            "land_verblijf": "NLD"
        }])
        data_context.add_source("RvIG", "personen", personen_df)

        ontzettingen_df = pd.DataFrame([{
            "bsn": bsn,
            "type": "KIESRECHT",
            "startdatum": "2023-01-01",
            "einddatum": "2024-01-01"
        }])
        data_context.add_source("JUSTID", "ontzettingen", ontzettingen_df)

        detenties_df = pd.DataFrame([{
            "bsn": bsn,
            "status": "INGESLOTEN"
        }])
        data_context.add_source("DJI", "detenties", detenties_df)


def run_scenario_comparison(scenario_name: str, scenario: str, expected_result: bool):
    """Run a scenario and compare v0.1.6 vs v0.1.7."""
    # Clear event sourcing cache to avoid conflicts
    clear_topic_cache()

    print(f"\n{'='*60}")
    print(f"Scenario: {scenario_name}")
    print(f"Expected: {'[+] Has voting rights' if expected_result else '[-] No voting rights'}")
    print(f"{'='*60}")

    bsn = "999993653"
    reference_date = "2025-03-15"

    # Test v0.1.6
    services = Services(reference_date)
    verkiezingen_df = pd.DataFrame([{
        "type": "TWEEDE_KAMER",
        "verkiezingsdatum": "2025-10-29"
    }])
    services.set_source_dataframe("KIESRAAD", "verkiezingen", verkiezingen_df)
    setup_test_data_v016(services, scenario, bsn)

    result_v016 = services.evaluate(
        service="KIESRAAD",
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=reference_date
    )

    # Test v0.1.7
    data_context = DataContext()
    law_evaluator = LawEvaluator(
        reference_date=reference_date,
        data_context=data_context
    )
    verkiezingen_df = pd.DataFrame([{
        "type": "TWEEDE_KAMER",
        "verkiezingsdatum": "2025-10-29"
    }])
    data_context.add_source("KIESRAAD", "verkiezingen", verkiezingen_df)
    setup_test_data_v017(data_context, scenario, bsn)

    result_v017 = law_evaluator.evaluate_law(
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=reference_date
    )

    # Compare results
    v016_result = result_v016.requirements_met
    v017_result = result_v017.requirements_met

    print(f"\nv0.1.6 result: {v016_result} {'[+]' if v016_result == expected_result else '[-]'}")
    print(f"v0.1.7 result: {v017_result} {'[+]' if v017_result == expected_result else '[-]'}")

    if v016_result == v017_result:
        print("[+] MATCH - Both versions produce the same result")
    else:
        print("[-] MISMATCH - Versions produce different results!")

    if v016_result == expected_result and v017_result == expected_result:
        print("[+] CORRECT - Both match expected result")
    else:
        print("[-] INCORRECT - One or both don't match expected result")

    return v016_result == v017_result and v016_result == expected_result


if __name__ == "__main__":
    print("\n" + "="*60)
    print("KIESWET v0.1.6 vs v0.1.7 COMPARISON TEST")
    print("="*60)

    scenarios = [
        ("Dutch citizen, 18+, no exclusion", "eligible", True),
        ("Non-Dutch citizen", "non_dutch", False),
        ("Under 18 years old", "underage", False),
        ("Court-ordered exclusion", "excluded", False),
        ("Detained (no exclusion)", "detained", True),
    ]

    results = []
    for scenario_name, scenario, expected in scenarios:
        success = run_scenario_comparison(scenario_name, scenario, expected)
        results.append((scenario_name, success))

    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for scenario_name, success in results:
        status = "[+] PASS" if success else "[-] FAIL"
        print(f"{status}: {scenario_name}")

    print(f"\n{passed}/{total} scenarios passed")

    if passed == total:
        print("\n[+] ALL TESTS PASSED - v0.1.7 is backward compatible!")
    else:
        print("\n[-] SOME TESTS FAILED - Review differences above")
