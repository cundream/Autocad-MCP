"""Render the source-reviewed AutoCAD MCP benchmark as a deterministic SVG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "benchmarks" / "source_review.json"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "autocad-mcp-benchmark.svg"
REQUIRED_PROJECT_KEYS = {
    "repository",
    "url",
    "reviewed_version",
    "score",
    "evidence_grade",
    "note",
}


def load_benchmark(path: Path) -> dict[str, Any]:
    """Load and validate the benchmark snapshot used by docs and tests."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0":
        raise ValueError("unsupported benchmark schema_version")
    if data.get("evidence_boundary") != "source_review_not_shared_live_run":
        raise ValueError("benchmark evidence boundary must be explicit")

    rubric = data.get("rubric")
    if not isinstance(rubric, list) or sum(item.get("weight", 0) for item in rubric) != 100:
        raise ValueError("benchmark rubric weights must total 100")

    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError("benchmark must contain projects")

    seen: set[str] = set()
    for project in projects:
        missing = REQUIRED_PROJECT_KEYS - project.keys()
        if missing:
            raise ValueError(f"project is missing keys: {sorted(missing)}")
        repository = project["repository"]
        if repository in seen:
            raise ValueError(f"duplicate repository: {repository}")
        seen.add(repository)
        if not 0 <= project["score"] <= 100:
            raise ValueError(f"score outside 0..100: {repository}")
        if project["evidence_grade"] not in {"A", "B", "C"}:
            raise ValueError(f"invalid evidence grade: {repository}")
    return data


def render_chart(data: dict[str, Any], output: Path) -> None:
    """Render a GitHub-readable fixed-background horizontal bar chart."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            'Matplotlib is required. Install it with: pip install -e ".[pdf]"'
        ) from exc

    matplotlib.rcParams["svg.hashsalt"] = "autocad-mcp-source-review-v1"
    projects = sorted(data["projects"], key=lambda item: item["score"])
    labels = [item["repository"] for item in projects]
    scores = [item["score"] for item in projects]
    grades = [item["evidence_grade"] for item in projects]
    colors = [
        "#0969da" if label == "U-C4N/Autocad-MCP" else "#6e7781" for label in labels
    ]

    fig, ax = plt.subplots(figsize=(12, 6.4), constrained_layout=True)
    fig.patch.set_facecolor("#f6f8fa")
    ax.set_facecolor("#f6f8fa")
    bars = ax.barh(labels, scores, color=colors, height=0.62)

    ax.set_xlim(0, 100)
    ax.set_xlabel("Weighted capability score / 100", color="#24292f", labelpad=10)
    ax.set_title(
        "Source-reviewed capability benchmark",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color="#24292f",
        pad=28,
    )
    ax.text(
        0,
        1.02,
        f"Fixed rubric · reviewed {data['reviewed_at']} · evidence grade shown per project",
        transform=ax.transAxes,
        color="#57606a",
        fontsize=10,
    )

    for bar, score, grade in zip(bars, scores, grades, strict=True):
        ax.text(
            min(score + 1.2, 96),
            bar.get_y() + bar.get_height() / 2,
            f"{score}  ·  {grade}",
            va="center",
            color="#24292f",
            fontweight="bold",
        )

    ax.text(
        0,
        -0.17,
        "Shared live-run results are not implied. Scores reflect public-source and recorded test evidence.",
        transform=ax.transAxes,
        color="#57606a",
        fontsize=9,
    )
    ax.grid(axis="x", color="#d0d7de", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors="#57606a")
    ax.tick_params(axis="y", colors="#24292f", length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        format="svg",
        facecolor=fig.get_facecolor(),
        metadata={"Creator": "AutoCAD MCP Pro benchmark renderer", "Date": None},
    )
    plt.close(fig)

    svg = output.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"
    output.write_text(normalized, encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    render_chart(load_benchmark(args.input), args.output)
    print(f"Rendered benchmark chart: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
