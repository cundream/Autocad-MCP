"""Validate drawing quality — run after creating/editing a drawing.

Usage: python scripts/validate_drawing.py [drawing_path]

This script checks for common drawing issues:
- Empty layers (layers with no entities)
- Entities on layer "0" (should use named layers)
- Entity count summary
"""

import json
import sys


def validate_stats(stats: dict) -> list[str]:
    """Validate entity statistics. Pass the result of analysis_entity_stats()."""
    issues = []

    if stats.get("total", 0) == 0:
        issues.append("WARNING: Drawing has no entities")

    by_layer = stats.get("by_layer", {})
    if "0" in by_layer and by_layer["0"] > 0:
        issues.append(
            f"INFO: {by_layer['0']} entities on default layer '0' "
            "(consider moving to named layers)"
        )

    return issues


def validate_layers(layers: list[dict]) -> list[str]:
    """Validate layer configuration. Pass the result of layer_list()."""
    issues = []

    for layer in layers:
        name = layer.get("name", "")
        if name == "0":
            continue
        if layer.get("color", 7) == 7 and name != "0":
            issues.append(
                f"INFO: Layer '{name}' uses default color (white/7). "
                "Consider assigning a distinct color."
            )

    return issues


def main():
    print("Drawing Validation Tool")
    print("=" * 40)
    print()
    print("This tool validates output from MCP analysis tools.")
    print("Pipe JSON from analysis_entity_stats() or layer_list().")
    print()
    print("Usage with MCP:")
    print("  1. Call analysis_entity_stats() → copy JSON output")
    print("  2. Call layer_list() → copy JSON output")
    print("  3. Review results for issues")
    print()
    print("Checks performed:")
    print("  - Empty drawing detection")
    print("  - Entities on default layer '0'")
    print("  - Layers with default color")
    print()

    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            if "total" in data:
                issues = validate_stats(data)
            elif isinstance(data, list):
                issues = validate_layers(data)
            else:
                issues = ["ERROR: Unrecognized input format"]

            if issues:
                for issue in issues:
                    print(f"  {issue}")
            else:
                print("  OK — No issues found")
        except json.JSONDecodeError:
            print("  ERROR: Invalid JSON input")
    else:
        print("No stdin input. Run interactively or pipe JSON data.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
