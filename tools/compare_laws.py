"""
Tool to compare two sets of machine law YAML files structurally.

This tool compares law implementations by structural analysis:
- Comparing YAML structure (definitions, requirements, actions, inputs, outputs)
- Extracting and displaying legal basis for each difference
- Supporting directory/pattern-based comparison of multiple law files
"""

import argparse
import json
import logging
import sys
from datetime import date
from glob import glob
from pathlib import Path
from typing import Any

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class LawSetComparator:
    """Compare two sets of law implementations structurally."""

    def __init__(self, set_a_pattern: str, set_b_pattern: str) -> None:
        """
        Initialize the law set comparator.

        Args:
            set_a_pattern: Pattern or directory for first set of laws
            set_b_pattern: Pattern or directory for second set of laws
        """
        self.set_a_pattern = set_a_pattern
        self.set_b_pattern = set_b_pattern

        # Detect if we're in single-file comparison mode
        self.single_file_mode = self._is_single_file(set_a_pattern) and self._is_single_file(set_b_pattern)

        # Find all matching files
        self.files_a = self._find_law_files(set_a_pattern)
        self.files_b = self._find_law_files(set_b_pattern)

        logger.info(f"Found {len(self.files_a)} law files in set A")
        logger.info(f"Found {len(self.files_b)} law files in set B")

        # Match files by law name
        self.matched_laws = self._match_laws()
        logger.info(f"Matched {len(self.matched_laws)} laws between sets")

        # Results storage
        self.comparison_results: list[dict[str, Any]] = []

    def _is_single_file(self, pattern: str) -> bool:
        """Check if pattern represents a single file."""
        path = Path(pattern)
        return path.is_file() or (not path.is_dir() and "*" not in pattern and path.exists())

    def _find_law_files(self, pattern: str) -> list[Path]:
        """Find all YAML law files matching the pattern."""
        path = Path(pattern)

        # If it's a directory, find all YAML files in it
        if path.is_dir():
            files = list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))
        # If it's a glob pattern
        elif "*" in pattern:
            files = [Path(f) for f in glob(pattern, recursive=True)]
        # If it's a single file
        elif path.is_file():
            files = [path]
        else:
            raise ValueError(f"Cannot find files matching pattern: {pattern}")

        return sorted(files)

    def _match_laws(self) -> list[tuple[Path, Path]]:
        """Match law files between two sets by law name."""
        # Single-file mode: direct comparison without requiring matching keys
        if self.single_file_mode and len(self.files_a) == 1 and len(self.files_b) == 1:
            return [(self.files_a[0], self.files_b[0])]

        # Set mode: match by (service, law) key
        laws_a = {}
        for file in self.files_a:
            try:
                with open(file) as f:
                    data = yaml.safe_load(f)
                    law_name = data.get("law")
                    service = data.get("service")
                    if law_name:
                        key = (service, law_name)
                        laws_a[key] = file
            except Exception as e:
                logger.warning(f"Error loading {file}: {e}")

        laws_b = {}
        for file in self.files_b:
            try:
                with open(file) as f:
                    data = yaml.safe_load(f)
                    law_name = data.get("law")
                    service = data.get("service")
                    if law_name:
                        key = (service, law_name)
                        laws_b[key] = file
            except Exception as e:
                logger.warning(f"Error loading {file}: {e}")

        # Match by key
        matches = []
        for key in laws_a:
            if key in laws_b:
                matches.append((laws_a[key], laws_b[key]))

        return matches

    def compare_all(self) -> list[dict[str, Any]]:
        """Compare all matched laws."""
        for file_a, file_b in self.matched_laws:
            logger.info(f"Comparing {file_a.name} vs {file_b.name}")
            comparator = SingleLawComparator(file_a, file_b)
            result = comparator.compare()
            self.comparison_results.append(result)

        return self.comparison_results

    def generate_report(self, output_format: str = "markdown") -> str:
        """Generate a comparison report for all laws."""
        if output_format == "json":
            return json.dumps(self.comparison_results, indent=2)
        elif output_format == "markdown":
            return self._generate_markdown_report()
        else:  # text
            return self._generate_text_report()

    def _generate_markdown_report(self) -> str:
        """Generate a markdown formatted report."""
        report = []
        report.append("# Law Set Comparison Report")
        report.append("")
        report.append(f"**Set A**: {self.set_a_pattern}")
        report.append(f"**Set B**: {self.set_b_pattern}")
        report.append(f"**Comparison Date**: {date.today().isoformat()}")
        report.append(f"**Laws Compared**: {len(self.comparison_results)}")
        report.append("")

        # Generate report for each law
        for result in self.comparison_results:
            report.append(f"## {result['law_name']}")
            report.append("")
            report.append(f"**Service**: {result['service']}")
            report.append(f"**Files**: `{result['file_a']}` vs `{result['file_b']}`")
            report.append("")

            # Legal basis
            if result.get("legal_basis_a") or result.get("legal_basis_b"):
                report.append("### Legal Basis")
                report.append("")

                legal_basis_a = result.get("legal_basis_a", {})
                legal_basis_b = result.get("legal_basis_b", {})

                if legal_basis_a:
                    report.append("**Set A**:")
                    report.append(f"- Law: {legal_basis_a.get('law', 'N/A')}")
                    report.append(f"- Article: {legal_basis_a.get('article', 'N/A')}")
                    if legal_basis_a.get("url"):
                        report.append(f"- URL: {legal_basis_a.get('url')}")
                    report.append("")

                if legal_basis_b:
                    report.append("**Set B**:")
                    report.append(f"- Law: {legal_basis_b.get('law', 'N/A')}")
                    report.append(f"- Article: {legal_basis_b.get('article', 'N/A')}")
                    if legal_basis_b.get("url"):
                        report.append(f"- URL: {legal_basis_b.get('url')}")
                    report.append("")

            # Metadata changes
            if result["metadata_changes"]:
                report.append("### Metadata Changes")
                for field, change in result["metadata_changes"].items():
                    report.append(f"- **{field}**: {change['from']} → {change['to']}")
                report.append("")

            # Definition changes with legal basis
            if result["definition_changes"]:
                report.append("### Definition Changes")
                for def_name, change in result["definition_changes"].items():
                    legal_ref = self._format_legal_ref(change.get("legal_basis"))
                    report.append(f"- **{def_name}**: {change['from']} → {change['to']}{legal_ref}")
                report.append("")

            # Input changes with legal basis
            if result["input_changes"]:
                report.append("### Input Changes")

                if result["input_changes"].get("added"):
                    report.append("**Added**:")
                    for name, details in result["input_changes"]["added"].items():
                        legal_ref = self._format_legal_ref(details.get("legal_basis"))
                        report.append(f"- {name}{legal_ref}")
                    report.append("")

                if result["input_changes"].get("removed"):
                    report.append("**Removed**:")
                    for name, details in result["input_changes"]["removed"].items():
                        legal_ref = self._format_legal_ref(details.get("legal_basis"))
                        report.append(f"- {name}{legal_ref}")
                    report.append("")

                if result["input_changes"].get("modified"):
                    report.append("**Modified**:")
                    for name in result["input_changes"]["modified"]:
                        report.append(f"- {name}")
                    report.append("")

            # Output changes with legal basis
            if result["output_changes"]:
                report.append("### Output Changes")

                if result["output_changes"].get("added"):
                    report.append("**Added**:")
                    for name, details in result["output_changes"]["added"].items():
                        legal_ref = self._format_legal_ref(details.get("legal_basis"))
                        report.append(f"- {name}{legal_ref}")
                    report.append("")

                if result["output_changes"].get("removed"):
                    report.append("**Removed**:")
                    for name, details in result["output_changes"]["removed"].items():
                        legal_ref = self._format_legal_ref(details.get("legal_basis"))
                        report.append(f"- {name}{legal_ref}")
                    report.append("")

                if result["output_changes"].get("modified"):
                    report.append("**Modified**:")
                    for name in result["output_changes"]["modified"]:
                        report.append(f"- {name}")
                    report.append("")

            report.append("---")
            report.append("")

        return "\n".join(report)

    def _format_legal_ref(self, legal_basis: dict | None) -> str:
        """Format legal basis reference for display."""
        if not legal_basis:
            return ""

        parts = []
        if legal_basis.get("law"):
            parts.append(legal_basis["law"])
        if legal_basis.get("article"):
            art = legal_basis["article"]
            parts.append(f"Art. {art}")
        if legal_basis.get("paragraph"):
            parts.append(f"lid {legal_basis['paragraph']}")

        if parts:
            return f" *({', '.join(parts)})*"
        return ""

    def _generate_text_report(self) -> str:
        """Generate a plain text report."""
        report = []
        report.append("=" * 80)
        report.append("LAW SET COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Set A: {self.set_a_pattern}")
        report.append(f"Set B: {self.set_b_pattern}")
        report.append(f"Date: {date.today().isoformat()}")
        report.append(f"Laws Compared: {len(self.comparison_results)}")
        report.append("=" * 80)
        report.append("")

        for result in self.comparison_results:
            report.append(f"{result['law_name']} ({result['service']})")
            report.append("-" * 80)

            if result["metadata_changes"]:
                report.append("Metadata Changes:")
                for field, change in result["metadata_changes"].items():
                    report.append(f"  {field}: {change['from']} → {change['to']}")
                report.append("")

            if result["definition_changes"]:
                report.append("Definition Changes:")
                for def_name, change in result["definition_changes"].items():
                    report.append(f"  {def_name}: {change['from']} → {change['to']}")
                report.append("")

            report.append("")

        return "\n".join(report)


class SingleLawComparator:
    """Compare two individual law YAML files."""

    def __init__(self, file_a: Path, file_b: Path) -> None:
        self.file_a = file_a
        self.file_b = file_b

        # Load YAML files
        with open(file_a) as f:
            self.law_a = yaml.safe_load(f)
        with open(file_b) as f:
            self.law_b = yaml.safe_load(f)

    def compare(self) -> dict[str, Any]:
        """Perform structural comparison."""
        return {
            "law_name": self.law_a.get("law", "Unknown"),
            "service": self.law_a.get("service", "Unknown"),
            "file_a": str(self.file_a.name),
            "file_b": str(self.file_b.name),
            "legal_basis_a": self.law_a.get("legal_basis", {}),
            "legal_basis_b": self.law_b.get("legal_basis", {}),
            "metadata_changes": self._compare_metadata(),
            "definition_changes": self._compare_definitions(),
            "input_changes": self._compare_section("input"),
            "output_changes": self._compare_section("output"),
        }

    def _compare_metadata(self) -> dict[str, Any]:
        """Compare metadata fields."""
        fields = ["name", "valid_from", "law_type", "legal_character"]
        changes = {}

        for field in fields:
            val_a = self.law_a.get(field)
            val_b = self.law_b.get(field)
            if val_a != val_b:
                changes[field] = {"from": val_a, "to": val_b}

        return changes

    def _compare_definitions(self) -> dict[str, Any]:
        """Compare definition constants with their legal basis."""
        defs_a = self.law_a.get("properties", {}).get("definitions", {})
        defs_b = self.law_b.get("properties", {}).get("definitions", {})

        changes = {}
        all_keys = set(defs_a.keys()) | set(defs_b.keys())

        for key in all_keys:
            val_a = defs_a.get(key)
            val_b = defs_b.get(key)

            if val_a != val_b:
                # Try to find legal basis for this definition
                # Definitions usually get their legal basis from the actions or requirements that use them
                legal_basis = self._find_definition_legal_basis(key)

                changes[key] = {
                    "from": val_a,
                    "to": val_b,
                    "legal_basis": legal_basis,
                }

        return changes

    def _find_definition_legal_basis(self, def_name: str) -> dict | None:
        """Find legal basis for a definition by searching where it's used."""
        # Search in inputs for references to this definition
        inputs = self.law_b.get("properties", {}).get("input", [])
        for inp in inputs:
            if inp.get("name", "").upper() == def_name:
                return inp.get("legal_basis")

        # Search in outputs
        outputs = self.law_b.get("properties", {}).get("output", [])
        for out in outputs:
            if out.get("name", "").upper() == def_name:
                return out.get("legal_basis")

        # If not found directly, return the law's main legal basis
        return self.law_b.get("legal_basis")

    def _compare_section(self, section_name: str) -> dict[str, Any]:
        """Compare a section (input/output) with legal basis tracking."""
        section_a = self.law_a.get("properties", {}).get(section_name, [])
        section_b = self.law_b.get("properties", {}).get(section_name, [])

        # Create mappings by name
        map_a = {item["name"]: item for item in section_a if "name" in item}
        map_b = {item["name"]: item for item in section_b if "name" in item}

        all_keys = set(map_a.keys()) | set(map_b.keys())

        added = {}
        removed = {}
        modified = []

        for key in all_keys:
            if key not in map_a:
                # Added in B
                added[key] = {"legal_basis": map_b[key].get("legal_basis")}
            elif key not in map_b:
                # Removed from A
                removed[key] = {"legal_basis": map_a[key].get("legal_basis")}
            elif map_a[key] != map_b[key]:
                # Modified
                modified.append(key)

        return {
            "added": added if added else None,
            "removed": removed if removed else None,
            "modified": modified if modified else None,
        }


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare two sets of machine law YAML files structurally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two versions of zorgtoeslag (single files)
  uv run python tools/compare_laws.py \\
    --set-a law/zorgtoeslagwet/TOESLAGEN-2024-01-01.yaml \\
    --set-b law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml

  # Compare all laws in two directories
  uv run python tools/compare_laws.py \\
    --set-a law_2024/ \\
    --set-b law_2025/

  # Compare using glob patterns
  uv run python tools/compare_laws.py \\
    --set-a "law/**/*-2024-*.yaml" \\
    --set-b "law/**/*-2025-*.yaml"
        """,
    )

    parser.add_argument("--set-a", required=True, help="Pattern/directory for first set of laws")
    parser.add_argument("--set-b", required=True, help="Pattern/directory for second set of laws")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "text"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Create comparator
        comparator = LawSetComparator(args.set_a, args.set_b)

        # Run comparison
        comparator.compare_all()

        # Generate report
        report = comparator.generate_report(output_format=args.format)

        # Output
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            logger.info(f"Report written to {args.output}")
        else:
            print(report)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
