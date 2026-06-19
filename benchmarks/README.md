# Benchmarks

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
