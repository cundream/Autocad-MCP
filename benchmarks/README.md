# Benchmarks

## Two evidence layers

This repository publishes two deliberately separate forms of evidence:

1. **Source-reviewed capability benchmark.** Six named AutoCAD MCP projects are
   scored with a fixed 100-point rubric covering CAD breadth, correctness and
   delivery, backend reach, engineering production, tests, and security. The
   dated data lives in [`source_review.json`](source_review.json), and the README
   graphic is generated—not hand-edited—from that file.
2. **Fixed-task runtime benchmark.** Adapters execute the same ten tasks and
   return `pass`, `partial`, `unsupported`, `fail`, `timeout`, or `not_run`.
   AutoCAD MCP Pro currently has the reference adapter; other projects do not
   receive runtime scores until an adapter actually runs their public interface.

Regenerate the source-review chart:

```bash
pip install -e ".[pdf]"
python -m benchmarks.render_chart
```

The source-review chart is not presented as a shared live AutoCAD run. Review
dates, evidence grades, project URLs, and the boundary are stored with the data.

## Fixed-task runtime runner v2

The v2 runner separates runtime evidence from the source-review rubric. Every
adapter receives the same ten tasks and produces the same closed result enum:
`pass`, `partial`, `unsupported`, `fail`, `timeout`, or `not_run`. A timeout is
reported per task. Execution is in-process, so adapters that delegate blocking
work must provide cancellation-safe task implementations or be wrapped by an
external process supervisor. Reports include commit SHA, Python/platform
details, backend capability claims, durations, coverage, and hashes for returned
artifacts. Unsupported tasks remain in the fixed-matrix denominator with score
zero, preventing partial implementations from receiving an inflated score.

```bash
python -m benchmarks.run_competitors --list
python -m benchmarks.run_competitors --server autocad-mcp-pro --backend ezdxf --json
python -m benchmarks.run_competitors --task table_mleader --task auditable_delivery --json
```

The release-machine ezdxf self-check is **10/10 (100.0)**. Repository stars and
raw tool counts do not contribute to the score. Adapter registration lives in
`competitors.yaml`.

## Live competitor lane (v1.4)

Two competitor adapters now execute the exact same task matrix, black-box over
MCP stdio, against commits pinned in `competitors.yaml`:

| Server | Pinned | Score | Pass | Coverage |
|---|---|---:|---:|---:|
| autocad-mcp-pro (reference) | working tree | 100.0 | 10/10 | 100% |
| beiming183-cloud/AutoCAD-MCP | `11f7c47e` | 50.0 | 5/10 | 50% |
| puran-water/autocad-mcp | `95476a33` | 45.0 | 4/10 | 50% |

Method and boundaries:

- `benchmarks/competitors_env.py` clones the pinned SHA into
  `benchmarks/.competitors/<id>/` (gitignored), builds an isolated venv, and
  installs the competitor from its own `pyproject.toml`.
- `benchmarks/adapters/mcp_stdio.py` drives the competitor exactly like an MCP
  host (fastmcp `Client` over stdio). No competitor code is imported.
- Task playbooks call each server's **own documented tool contract**, read from
  the pinned source (consolidated `operation` + payload tools; beiming's
  `doc_id`/`expected_revision` discipline is honored via
  `transaction(operation="context")`).
- **Verification never trusts the competitor's response**: every geometry claim
  must survive `save`/`save_as_dxf` and re-opening the DXF with ezdxf inside
  the harness.
- Tasks with no documented equivalent are reported `unsupported` with the
  reason string; they stay in the fixed-matrix denominator at score zero.
- This lane is headless (ezdxf backends only). File-IPC / live-AutoCAD lanes
  (including COM-only servers such as best-cad-mcp or daobataotie/CAD-MCP)
  require a local AutoCAD session and are out of CI scope by design.

Published machine-readable reports (artifact paths sanitized to filenames)
live under [`results/published/`](results/published/); the README chart is
regenerated from them:

```bash
python -m benchmarks.run_competitors --server puran-water-autocad-mcp --backend ezdxf
python -m benchmarks.run_competitors --server beiming183-autocad-mcp --backend ezdxf
python -m benchmarks.render_live_chart
```

## Correctness A/B suite

`correctness_suite.py` is a set of deterministic, headless (ezdxf-backend) checks
that exercise real drawing operations. `compare_versions.py` runs the **same**
suite against an older git ref and the current checkout, each check in its own
subprocess so a hard crash (e.g. a matplotlib-in-thread `SIGSEGV`) is recorded as
a miss rather than taking down the run.

Reproduce:

```bash
python benchmarks/compare_versions.py            # current tree vs origin/main
python benchmarks/compare_versions.py v1.0.0     # vs a tag/ref
python benchmarks/compare_versions.py --json results.json
```

### Result — v1.1.0 vs v1.0.0 (`origin/main`, commit 15fa2bc)

21 checks, ezdxf backend, CPython 3.14, one subprocess per check.

| Version | Checks passing | Pass rate |
|---------|----------------|-----------|
| **v1.0.0** (public release) | 8 / 21 | **38.1 %** |
| **v1.1.0** (this release)   | 21 / 21 | **100 %** |

**13 defects fixed, 0 regressions** — a 2.6× higher correctness pass-rate (+61.9 pts).

Fixed (failed on v1.0.0, pass on v1.1.0):

| Check | Category | What it proves |
|-------|----------|----------------|
| `dim_aligned_no_error` | Dimensions | aligned dim no longer raises `TypeError` |
| `dim_angular_no_error` | Dimensions | angular dim no longer raises `TypeError` |
| `array_polar_360_distinct` | Modify | full-circle array no longer duplicates the original |
| `point_intersection_line_line` | Geometry | deterministic line/line intersection exists & is correct |
| `point_tangent_external` | Geometry | external-point tangent is perpendicular & on-circle |
| `arc_has_length` | Query | ARC carries a `length` property |
| `arc_select_by_length` | Query | `entity_select_smart` length_range selects arcs |
| `ezdxf_bounding_box` | Query | `bounding_box` populated (COM/ezdxf parity) |
| `mtext_rotation_roundtrip` | Entities | MTEXT honors caller rotation |
| `screenshot_png` | Render | headless render returns a valid PNG (no GUI-thread crash) |
| `dim_overlap_critique_fires` | Quality gate | `dim_overlap` critique is live (was a no-op) |
| `iso13567_dim_layer` | Quality gate | `dimension_auto` lands dims on the active set's layer |
| `gear_no_self_overlap` | Engineering | gear outline never dips inside the root circle (z ≥ 42) |

Passing on **both** versions (6 core ops + 2 others) keep the suite honest — it is
not a cherry-picked list of failures; the baseline genuinely does basic CAD work.

### Caveats / honesty notes

- The baseline is `origin/main` (the public v1.0.0). All four audited fix sprints
  land between it and v1.1.0 — see `docs/analysis/`.
- `screenshot_png` on the baseline is host-dependent: it is recorded as a miss
  here because the default matplotlib backend is a GUI backend and the render runs
  off the main thread. On a host where matplotlib defaults to `Agg`, the baseline
  may not crash. v1.1.0 forces `Agg` and is deterministic.
- `center_linetype_applied` passes on both because it only checks the linetype
  **attribute** string (set on both); the v1.0.0 "renders as Continuous because the
  linetype was never loaded" defect is not observable through `EntityInfo`.
- COM-backend behaviour is not covered here (no live AutoCAD); see the mocked-COM
  suites in `tests/`.

## Performance (throughput) — coming

Scale / throughput numbers (1k–100k entities, render timings, model-by-model
tool-call success rate) are tracked in the main README and will be published here
with a hardware footprint.
