# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_Next: closed-loop refiner (critique→repair→re-critique with transaction-stack isolation), pre-plan clarification pass, ISO 286 fit-table lookup (H7/g6 → deviations), and a local-VLM visual judge._

### Fixed
- **Install from source** — `pip install -e ".[full]"` failed at
  "Preparing editable metadata" because the flat layout has no directory
  matching the project name, so hatchling could not infer which files to ship.
  `pyproject.toml` now declares the wheel file selection explicitly
  (`server.py`, `config.py`, `security.py`, `backends/`, `engineering/`). (#2)
- **`dimension_linear` on the COM backend** — always crashed with
  `<unknown>.AddDimLinear`: the AutoCAD ActiveX API has no `AddDimLinear`
  method. Linear dimensions are now created via `AddDimRotated` (identical
  argument order), with a mocked regression test. (#3)

## [1.2.0] — 2026-07-07

Production-ISO parity + a measurable quality moat. **360 tests, ruff-clean.** Tool count: 111 → 116.

### Added
- **`drawing_settings`** — read or change common AutoCAD drawing settings by
  friendly name (units mm/cm/m/inch/feet, linear/angular precision, LTSCALE,
  DIMSCALE, text size, point mode/size, OSMODE, fillet radius) without
  memorising system-variable names. Call with no argument for a full snapshot.
  A convenience facade over `system_get_variable` / `system_set_variable`;
  cross-backend.
- **In-place editing** — `entity_edit_text` re-labels or resizes an existing
  TEXT/MTEXT entity, and `entity_edit_geometry` re-drives a CIRCLE/LINE/ARC
  (center, radius, endpoints, arc angles) — both **preserve the entity handle**,
  so the user can adjust a drawing without delete-and-recreate. Cross-backend.
- **2D GD&T (ISO 1101 / ASME Y14.5)** — `gd_frame` draws a feature control frame
  (all 14 geometric characteristics, ⌀ zone prefix, Ⓜ/Ⓛ/Ⓢ material modifiers,
  multi-datum references) and `datum_feature` places a datum symbol. Frames are
  composed from LINE + TEXT so they render identically on **both** the COM and
  ezdxf backends (ezdxf's native TOLERANCE entity renders blank via matplotlib).
  No competing CAD MCP or surveyed text-to-CAD product ships 2D GD&T authoring.
- **GD&T datum-consistency gate** — a new `gdt` critique focus fails
  `drawing_finalize` when a feature control frame references a datum with no
  matching datum feature (a meaningless FCF per ISO 1101).
- **ISO 129 dimension tolerances** — `dimension_linear` / `dimension_radius` /
  `dimension_diameter` gain `tol_upper` / `tol_lower` / `tol_mode`
  (`symmetric` ±, `deviation` +a/-b, `limit` stacked, `basic` boxed) and a
  `text_override` (e.g. `⌀20 H7`). Toleranced production dimensions are now
  possible — previously the single biggest functional gap.
- **Scalar drawing-score + invalidity ratio** (`engineering/scoring.py`) — the
  `drawing_finalize` payload now carries a 0-100 `score`, an `invalidity_ratio`,
  and an A-F `grade` over the union of the structural validator and the premium
  critique, so drawing quality is regression-trackable (MUSE / CadBench grade an
  Invalidity Ratio, not shape).

### Fixed
- **Honesty**: the COM backend advertised a false `all_entity_types` capability
  (it authors 2D entities only, no 3D solids) — corrected to `entities_2d`.

## [1.1.1] — 2026-06-20

### Added
- **`selection_get`** (Entity Query, COM backend): reads AutoCAD's implied
  ("pickfirst") viewport selection — the entities the user highlighted with
  grips before invoking the AI — and returns their handles + `EntityInfo`.
  This lets the AI scope work to exactly what the user picked
  (`dimension_auto(selection_get()["handles"])`) instead of acting on the whole
  drawing. Resolves [#1](https://github.com/U-C4N/Autocad-MCP/issues/1) — the
  layer-juggling workaround is no longer needed. Surfaces the `PICKFIRST` sysvar
  state so an empty selection is self-explanatory. The ezdxf headless backend
  has no viewport, so it returns `ok=False` with an empty handle list (same
  shape, never raises). Tool count: 110 → 111.

## [1.1.0] — 2026-06-19

Correctness, cross-backend parity, and an **enforced** quality gate, landed across four audited
sprints (see `docs/analysis/`). 318 tests, ruff-clean.

### Added
- **Premium drafting workflow** (shared across both backends): `drawing_plan`, `drawing_critique`
  (ISO-128 focuses), `point_from_snap`, `drawing_apply_iso_layers`, `dimension_auto`,
  `entity_select_smart`, `construction_xline` / `construction_clear`.
- **Deterministic geometry** for exact OSNAP coordinates: `point_intersection`
  (line/line, line/circle, circle/circle) and `point_tangent` (external point → circle).
- **Engineering / deterministic CAD layer**: involute gear front view + section A-A,
  DIN 6885 keyed bore, ISO A3 title block, and the 8-step `drawing_finalize` validator.
- **HTTP bearer-token auth**: `StaticTokenVerifier` wired into FastMCP when `MCP_AUTH_TOKEN` is set.
- Mocked-COM test harness (`tests/test_com_backend.py` + Sprint-3/4 suites) — COM logic is now
  regression-tested on Linux CI without a live AutoCAD.
- `entity_create_mtext` rotation parameter; `dimension_auto` layer override; `bounding_box` /
  ARC `length` / TEXT-MTEXT `rotation`+`char_height` on both backends; `BlockInfo.description`.
- Security module (`security.py`), centralized config (`config.py`), `.env.example`, path
  validation, command/LISP sanitization, ruff config, pre-commit hooks, pytest-cov.

### Changed
- **`drawing_finalize` now enforces the premium critique** in addition to the structural validator:
  leftover construction geometry, non-ISO-128 lineweights, untrimmed corners, duplicate entities,
  and dimension overlap block the gate (was advisory-only). `strict_critique=True` fails on warnings too.
- **`drawing_save_as` derives the on-disk format from the file extension** — `part.dxf` writes DXF,
  not DWG. ezdxf refuses to mislabel a `.dwg` file.
- Dimension and construction layers resolve from the active layer set (iso13567 → `M-DIMEN-T-N` /
  `M-CONST-E-N`, not the hardcoded `DIM` / `CONSTRUCTION`).
- Premium meta-tools lifted into the shared `AutoCADBackend` base class (single source of truth).
- Dead code removed (`section.py`, `generate_tooth_profile`, `CommandResult`, `set_layer_active`, …).

### Fixed
- ezdxf `dimension_aligned` / `dimension_angular` raised `TypeError` (wrong ezdxf 1.4 args) — fixed.
- Full-circle polar array placed a duplicate copy over the original — fixed (divisor = count).
- `entity_offset` ignored `side_x`/`side_y` on both backends — now honored (and COM no longer leaks extras).
- COM `entity_create_hatch` built an associative hatch then deleted its boundary — now non-associative.
- Lineweight mm-vs-hundredths truncation wiped ISO-128 weights — fixed via `normalize_lineweight`.
- **`view_screenshot` / `drawing_export_pdf` could SIGSEGV** (matplotlib GUI backend in a worker thread)
  — now render headless via `Agg` (`Figure` + `FigureCanvasAgg`).
- `entity_select_smart` `length_range` silently rejected all ARCs (no `length`) — fixed.
- Gear tooth profile self-overlapped for high tooth counts (z ≥ ~42); section view drew duplicate
  bore lines; validator keyway heuristic was a permanent false-negative — all fixed.
- COM `system_run_lisp` always reported `"nil"`; `system_set_variable` didn't coerce numeric sysvars
  — fixed. `system_about` tool groups / `_registered_tool_count` no longer drift or surface `-1`.
- `drawing_new` bootstrap failures now surface as `degraded` instead of reporting success.

### Security
- HTTP remote-bind guard now fires on **every** launch path (including `fastmcp run server.py:mcp`),
  not only the `__main__` block — closing an anonymous-remote-bind gap.
- AutoLISP allowlist bypass-vector regression tests (newline injection, symbol aliasing, `vla*`/`acet-*`,
  `c:` custom commands).
- COM apartment leak bounded (`CoUninitialize` on teardown); transaction commit/rollback and
  `system_run_lisp` now respect the CMDACTIVE guard.

## [1.0.0] — 2026-03-01

### Added
- Initial release with 67 tools, 6 resources, 5 prompt templates
- Dual-engine architecture: COM backend (live AutoCAD) + ezdxf backend (headless)
- FastMCP 3.0 server with middleware stack (error handling, audit, timing, logging)
- Drawing management: new, open, save, save-as, export DXF/PDF, purge, audit, undo/redo
- Entity creation: line, circle, arc, polyline, rectangle, text, mtext, hatch, spline, ellipse, point, block reference
- Dimensions: linear, aligned, angular, radius, diameter
- Entity modification: move, copy, rotate, scale, mirror, offset, delete, rectangular/polar array
- Layer management: create, delete, set current, modify, freeze/thaw, lock/unlock, hide/show, isolate
- Block operations: list, insert, explode, attributes, create from entities, find references
- Analysis: entity stats, region search, distance/area measurement, bounding box, select by layer/type
- View control: zoom extents/window, screenshot
- Transaction support: begin, commit, rollback
- System tools: status, variables, command execution, AutoLISP evaluation
- 5 prompt templates: floor plan, P&ID, electrical schematic, mechanical drawing, quick drawing
