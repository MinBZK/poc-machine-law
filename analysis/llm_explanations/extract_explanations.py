#!/usr/bin/env python3
"""
Script to extract LLM-generated "waarom" explanations for machine law decisions.

This script iterates over profiles and laws, executes each combination,
and generates LLM explanations for the results. Output is saved to JSONL
(JSON Lines) format for analysis (e.g., for thesis research on LLM explanations).

Output format:
- First line: metadata record with version info for reproducibility
- Subsequent lines: one record per profile × law combination

Usage (run from project root):
    # With Anthropic API key:
    export ANTHROPIC_API_KEY="your-key-here"
    uv run python analysis/llm_explanations/extract_explanations.py

    # Or pass key as argument:
    uv run python analysis/llm_explanations/extract_explanations.py --api-key "your-key-here"

    # Limit to specific laws or profiles:
    uv run python analysis/llm_explanations/extract_explanations.py --laws zorgtoeslag huurtoeslag --profiles 100000001

    # Save to specific output file:
    uv run python analysis/llm_explanations/extract_explanations.py --output my_explanations.jsonl
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root and web directory to path for proper imports
# From analysis/llm_explanations/ we need to go up two levels
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "web"))

import yaml


def get_git_info() -> dict:
    """Get git commit information for reproducibility."""
    info = {}

    try:
        # Main repo commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            info["machine_law_commit"] = result.stdout.strip()

        # Main repo branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            info["machine_law_branch"] = result.stdout.strip()

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            info["machine_law_dirty"] = len(result.stdout.strip()) > 0

        # Law submodule commit
        law_path = PROJECT_ROOT / "submodules" / "regelrecht-laws"
        if law_path.exists():
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=law_path,
            )
            if result.returncode == 0:
                info["regelrecht_laws_commit"] = result.stdout.strip()

            # Check for uncommitted changes in submodule
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=law_path,
            )
            if result.returncode == 0:
                info["regelrecht_laws_dirty"] = len(result.stdout.strip()) > 0

    except Exception as e:
        info["git_error"] = str(e)

    return info


def load_profiles_raw(profiles_path: str = "data/profiles.yaml") -> tuple[dict, dict]:
    """Load all profiles from the profiles.yaml file.

    Returns:
        Tuple of (profiles_dict, raw_yaml_data)
    """
    with open(profiles_path) as f:
        raw_data = yaml.safe_load(f)
    return raw_data.get("profiles", {}), raw_data


def get_discoverable_laws(services) -> dict[str, list[str]]:
    """Get all discoverable laws from the engine."""
    return services.get_discoverable_service_laws("CITIZEN")


def create_explanation_prompt(service_name: str, result: dict, profile: dict, bsn: str) -> str:
    """Create a prompt asking for an explanation of the result."""
    # Format the result for the prompt
    requirements_met = result.get("requirements_met", False)
    missing_required = result.get("missing_required", False)
    output = result.get("result", {})
    explanation = result.get("explanation", "")

    prompt = f"""Ik heb zojuist een berekening uitgevoerd voor de regeling '{service_name}'.

Burgerprofiel:
- Naam: {profile.get("name", "Onbekend")}
- Beschrijving: {profile.get("description", "Geen beschrijving")}
- BSN: {bsn}

Resultaat van de berekening:
- Voldoet aan voorwaarden: {"Ja" if requirements_met else "Nee"}
- Ontbrekende essentiële gegevens: {"Ja" if missing_required else "Nee"}
- Uitkomst: {json.dumps(output, indent=2, ensure_ascii=False)}

Korte uitleg van het systeem: {explanation}

Geef een duidelijke uitleg in eenvoudig Nederlands (B1-niveau) over:
1. WAAROM deze burger wel of niet in aanmerking komt voor deze regeling
2. Welke factoren uit het profiel van de burger hebben geleid tot dit resultaat
3. Wat de burger eventueel kan doen als ze niet in aanmerking komen

Let op: bedragen in de uitkomst zijn in eurocenten, deel door 100 voor euros."""

    return prompt


# Available models with their characteristics (updated January 2025)
# See: https://platform.claude.com/docs/en/about-claude/models/overview
# Pricing: https://claude.com/pricing
AVAILABLE_MODELS = {
    "haiku": {
        "id": "claude-haiku-4-5-20251001",
        "description": "Fast and cheap, good for batch processing",
        "input_cost_per_mtok": 1.00,
        "output_cost_per_mtok": 5.00,
    },
    "sonnet": {
        "id": "claude-sonnet-4-5-20250929",
        "description": "Balanced performance and cost",
        "input_cost_per_mtok": 3.00,
        "output_cost_per_mtok": 15.00,
    },
    "opus": {
        "id": "claude-opus-4-5-20251101",
        "description": "Most capable, highest cost",
        "input_cost_per_mtok": 5.00,
        "output_cost_per_mtok": 25.00,
    },
}

DEFAULT_MODEL = "haiku"


def extract_explanations(
    api_key: str | None = None,
    laws_filter: list[str] | None = None,
    profiles_filter: list[str] | None = None,
    output_file: str = "explanations_output.jsonl",
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> list[dict]:
    """
    Extract LLM explanations for all profile × law combinations.

    Args:
        api_key: Anthropic API key (uses env var if not provided)
        laws_filter: List of law names to include (None = all)
        profiles_filter: List of BSNs to include (None = all)
        output_file: Path to output JSONL file
        model: Model to use (haiku, sonnet, opus)
        verbose: Print progress information

    Returns:
        List of explanation records
    """
    import anthropic

    # Set API key if provided
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    # Check for API key
    actual_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not actual_api_key:
        print("ERROR: No Anthropic API key found!")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key argument")
        sys.exit(1)

    # Validate model choice
    if model not in AVAILABLE_MODELS:
        print(f"ERROR: Unknown model '{model}'. Available: {', '.join(AVAILABLE_MODELS.keys())}")
        sys.exit(1)

    model_info = AVAILABLE_MODELS[model]
    model_id = model_info["id"]

    # Create Anthropic client
    client = anthropic.Anthropic(api_key=actual_api_key)

    # Import after setting up environment
    from explain.mcp_connector import MCPLawConnector
    from web.dependencies import TODAY, get_case_manager, get_claim_manager, get_machine_service

    # Initialize services
    if verbose:
        print("Initializing services...")

    services = get_machine_service()
    case_manager = get_case_manager()
    claim_manager = get_claim_manager()

    # Initialize MCP connector
    mcp_connector = MCPLawConnector(services, case_manager, claim_manager)

    # Load profiles with raw data for reproducibility
    profiles, raw_profiles_data = load_profiles_raw()
    if verbose:
        print(f"Loaded {len(profiles)} profiles")

    # Get available laws
    available_laws = mcp_connector.registry.get_service_names()
    if verbose:
        print(f"Available laws: {available_laws}")

    # Apply filters
    if laws_filter:
        available_laws = [law for law in available_laws if law in laws_filter]
        if verbose:
            print(f"Filtered to laws: {available_laws}")

    if profiles_filter:
        profiles = {bsn: profile for bsn, profile in profiles.items() if bsn in profiles_filter}
        if verbose:
            print(f"Filtered to {len(profiles)} profiles")

    if verbose:
        print(f"Using model: {model_id} ({model_info['description']})")

    # LLM parameters for reproducibility
    llm_params = {
        "model_id": model_id,
        "model_name": model,
        "max_tokens": 1500,
        "temperature": 0.3,
        "system_prompt": "Je bent een behulpzame assistent die Nederlandse burgers helpt met vragen over overheidsregelingen. Geef duidelijke, begrijpelijke uitleg in eenvoudig Nederlands (B1-niveau).",
    }

    # Collect git info
    git_info = get_git_info()

    # Results storage
    results = []
    total_combinations = len(profiles) * len(available_laws)
    current = 0

    # Open output file and write metadata first
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        # Write metadata record first
        metadata = {
            "record_type": "metadata",
            "extraction_date": datetime.now().isoformat(),
            "reference_date": TODAY,
            "git_info": git_info,
            "llm_params": llm_params,
            "filters": {
                "laws_filter": laws_filter,
                "profiles_filter": profiles_filter,
            },
            "total_profiles": len(profiles),
            "total_laws": len(available_laws),
            "expected_records": total_combinations,
            "global_services": raw_profiles_data.get("globalServices", {}),
        }
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

        # Iterate over all combinations
        for bsn, profile in profiles.items():
            # Get the full profile data including sources
            full_profile = raw_profiles_data.get("profiles", {}).get(bsn, profile)

            for law_name in available_laws:
                current += 1
                if verbose:
                    print(f"\n[{current}/{total_combinations}] Processing {law_name} for {profile.get('name', bsn)}...")

                record = {
                    "record_type": "explanation",
                    "record_number": current,
                    "timestamp": datetime.now().isoformat(),
                    "bsn": bsn,
                    "profile": {
                        "name": profile.get("name", "Unknown"),
                        "description": profile.get("description", ""),
                        "sources": full_profile.get("sources", {}),
                    },
                }

                try:
                    # Get the service
                    service = mcp_connector.registry.get_service(law_name)
                    if not service:
                        if verbose:
                            print("  Skipping: service not found")
                        record["error"] = "Service not found"
                        record["law"] = {"name": law_name}
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        results.append(record)
                        continue

                    # Get the rule spec to know which law definition file is used
                    rule_spec = services.get_rule_spec(service.law_path, TODAY, service.service_type)

                    record["law"] = {
                        "name": law_name,
                        "description": service.description,
                        "service_type": service.service_type,
                        "law_path": service.law_path,
                        "rule_spec_name": rule_spec.get("name") if rule_spec else None,
                        "rule_spec_version": rule_spec.get("version") if rule_spec else None,
                    }

                    # Execute the law calculation
                    calc_result = service.execute(bsn, {})

                    if "error" in calc_result:
                        if verbose:
                            print(f"  Error in calculation: {calc_result['error']}")
                        record["error"] = calc_result["error"]
                        record["calculation_result"] = None
                        record["llm_explanation"] = None
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        results.append(record)
                        continue

                    record["calculation_result"] = {
                        "requirements_met": calc_result.get("requirements_met"),
                        "missing_required": calc_result.get("missing_required"),
                        "missing_fields": calc_result.get("missing_fields", []),
                        "output": calc_result.get("result", {}),
                        "input_data": calc_result.get("input_data", {}),
                        "system_explanation": calc_result.get("explanation", ""),
                    }

                    # Create prompt for explanation
                    prompt = create_explanation_prompt(law_name, calc_result, profile, bsn)
                    record["prompt_used"] = prompt

                    # Get LLM explanation
                    if verbose:
                        print("  Requesting LLM explanation...")

                    response = client.messages.create(
                        model=model_id,
                        max_tokens=llm_params["max_tokens"],
                        temperature=llm_params["temperature"],
                        system=llm_params["system_prompt"],
                        messages=[{"role": "user", "content": prompt}],
                    )

                    llm_explanation = response.content[0].text
                    record["llm_explanation"] = llm_explanation

                    # Extract usage info if available
                    if hasattr(response, "usage"):
                        record["llm_usage"] = {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                        }

                    if verbose:
                        print(f"  Requirements met: {calc_result.get('requirements_met', 'N/A')}")
                        print(f"  Explanation length: {len(llm_explanation)} chars")

                except Exception as e:
                    if verbose:
                        print(f"  Exception: {str(e)}")
                    record["error"] = str(e)
                    record["calculation_result"] = None
                    record["llm_explanation"] = None

                # Write record immediately (streaming to file)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                results.append(record)

    if verbose:
        print(f"\n{'=' * 60}")
        print("Extraction complete!")
        print(f"Total records: {len(results)}")
        print(f"Output saved to: {output_path.absolute()}")

        # Summary statistics
        successful = sum(1 for r in results if r.get("llm_explanation"))
        errors = sum(1 for r in results if r.get("error"))
        met_requirements = sum(
            1 for r in results if (r.get("calculation_result") or {}).get("requirements_met") is True
        )

        print("\nStatistics:")
        print(f"  Successful explanations: {successful}")
        print(f"  Errors: {errors}")
        print(f"  Requirements met: {met_requirements}/{successful}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract LLM explanations for machine law decisions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract all combinations (uses haiku by default):
    uv run python analysis/llm_explanations/extract_explanations.py

    # Use a different model:
    uv run python analysis/llm_explanations/extract_explanations.py --model sonnet
    uv run python analysis/llm_explanations/extract_explanations.py --model opus

    # Extract specific laws only:
    uv run python analysis/llm_explanations/extract_explanations.py --laws zorgtoeslag huurtoeslag

    # Extract for specific profiles:
    uv run python analysis/llm_explanations/extract_explanations.py --profiles 100000001 100000002

    # Save to specific file:
    uv run python analysis/llm_explanations/extract_explanations.py --output my_results.jsonl

    # Quiet mode (less output):
    uv run python analysis/llm_explanations/extract_explanations.py --quiet
""",
    )

    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument(
        "--model",
        choices=list(AVAILABLE_MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Model to use: {', '.join(AVAILABLE_MODELS.keys())} (default: {DEFAULT_MODEL})",
    )
    parser.add_argument("--laws", nargs="+", help="Filter to specific laws (e.g., zorgtoeslag huurtoeslag)")
    parser.add_argument("--profiles", nargs="+", help="Filter to specific BSNs")
    parser.add_argument("--output", default="explanations_output.jsonl", help="Output JSONL file path")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--list-laws", action="store_true", help="List available laws and exit")
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles and exit")

    args = parser.parse_args()

    # List mode
    if args.list_laws or args.list_profiles:
        if args.list_profiles:
            profiles, _ = load_profiles_raw()
            print("Available profiles:")
            for bsn, profile in profiles.items():
                print(f"  {bsn}: {profile.get('name', 'Unknown')} - {profile.get('description', '')[:60]}...")
            print(f"\nTotal: {len(profiles)} profiles")

        if args.list_laws:
            # Need to initialize services to get laws
            if args.api_key:
                os.environ["ANTHROPIC_API_KEY"] = args.api_key

            from explain.mcp_connector import MCPLawConnector
            from web.dependencies import get_case_manager, get_claim_manager, get_machine_service

            services = get_machine_service()
            case_manager = get_case_manager()
            claim_manager = get_claim_manager()
            mcp_connector = MCPLawConnector(services, case_manager, claim_manager)

            print("\nAvailable laws:")
            for law_name in mcp_connector.registry.get_service_names():
                service = mcp_connector.registry.get_service(law_name)
                if service:
                    print(f"  {law_name}: {service.description} ({service.service_type})")

        return

    # Run extraction
    extract_explanations(
        api_key=args.api_key,
        laws_filter=args.laws,
        profiles_filter=args.profiles,
        output_file=args.output,
        model=args.model,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
