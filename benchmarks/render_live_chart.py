"""Render the live-run benchmark lane (v2 fixed-task matrix) as a deterministic SVG.

Input: the published per-server reports under ``benchmarks/results/published/``
(produced by ``benchmarks.run_competitors``, artifact paths sanitized to
filenames). Output: a GitHub-readable horizontal bar chart showing the
weighted score and task coverage per server.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "benchmarks" / "results" / "published"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "autocad-mcp-livebench.svg"


def load_reports(input_dir: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "2.0":
            raise ValueError(f"{path.name}: unsupported schema_version")
        summary = data.get("summary") or {}
        if "score" not in summary or "coverage_percent" not in summary:
            raise ValueError(f"{path.name}: summary is missing score/coverage")
        reports.append(data)
    if not reports:
        raise SystemExit(f"no published reports found in {input_dir}")
    return reports


def render_chart(reports: list[dict[str, Any]], output: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            'Matplotlib is required. Install it with: pip install -e ".[pdf]"'
        ) from exc

    matplotlib.rcParams["svg.hashsalt"] = "autocad-mcp-livebench-v2"
    reports = sorted(reports, key=lambda item: item["summary"]["score"])
    labels = [item["adapter"] for item in reports]
    scores = [item["summary"]["score"] for item in reports]
    coverage = [item["summary"]["coverage_percent"] for item in reports]
    passed = [item["summary"]["passed"] for item in reports]
    attempted = [item["summary"]["attempted"] for item in reports]
    colors = ["#0969da" if label == "autocad-mcp-pro" else "#6e7781" for label in labels]

    fig, ax = plt.subplots(figsize=(12, 4.8), constrained_layout=True)
    fig.patch.set_facecolor("#f6f8fa")
    ax.set_facecolor("#f6f8fa")
    bars = ax.barh(labels, scores, color=colors, height=0.58)

    ax.set_xlim(0, 100)
    ax.set_xlabel(
        "Weighted live-run score / 100 (fixed 10-task matrix)", color="#24292f", labelpad=10
    )
    ax.set_title(
        "Live-run benchmark - headless ezdxf lane",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color="#24292f",
        pad=28,
    )
    ax.text(
        0,
        1.02,
        "Same 10 tasks, same harness, pinned competitor commits; artifacts verified by re-opening the DXF",
        transform=ax.transAxes,
        color="#57606a",
        fontsize=10,
    )

    for bar, score, cov, ok, total in zip(bars, scores, coverage, passed, attempted, strict=True):
        ax.text(
            min(score + 1.2, 82),
            bar.get_y() + bar.get_height() / 2,
            f"{score:g}  ({ok}/{total} pass, {cov:g}% coverage)",
            va="center",
            color="#24292f",
            fontweight="bold",
        )

    ax.text(
        0,
        -0.22,
        "Unsupported tasks score 0 in the fixed matrix; per-task statuses and reasons are in benchmarks/results/published/.",
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
        metadata={"Creator": "AutoCAD MCP Pro live benchmark renderer", "Date": None},
    )
    plt.close(fig)

    svg = output.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"
    output.write_text(normalized, encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    render_chart(load_reports(args.input_dir), args.output)
    print(f"Rendered live benchmark chart: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
