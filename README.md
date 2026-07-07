# AutoCAD MCP Pro

**Production-grade AutoCAD automation for the Model Context Protocol.**
Dual-engine. Battle-tested. Model-agnostic.

[![Version](https://img.shields.io/badge/version-1.2.0-1f6feb)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-3fb950)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-1f6feb?logo=python&logoColor=white)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-FastMCP%203.0-8957e5)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-360%20passing-3fb950)](tests/)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Stars](https://img.shields.io/github/stars/U-C4N/Autocad-MCP?style=flat&color=e3b341)](https://github.com/U-C4N/Autocad-MCP/stargazers)

> **116 tools · 5 resources · 5 prompt templates · COM + ezdxf backends**
>
> One MCP contract, two execution engines: drive a **live AutoCAD** instance over COM, or run **fully headless** on any OS with ezdxf — same tool surface, same response shapes.

**New in 1.2** — 2D GD&T feature control frames + datum features (ISO 1101), ISO 129 dimension tolerances (±/deviation/limit/basic + text override), in-place editing of existing text and geometry (`entity_edit_text` / `entity_edit_geometry`), a friendly `drawing_settings` facade (units/scale/precision/osnap), and a scalar drawing-score + invalidity-ratio at `drawing_finalize`.

### What makes it different

| | AutoCAD MCP Pro | Typical AutoCAD MCP |
|---|:---:|:---:|
| Live **COM** + headless **ezdxf** (one API) | ✅ | one or the other |
| **Standards-validation gate** (ISO 128 critique → finalize) | ✅ | ❌ |
| **2D GD&T** authoring + datum-consistency gate (ISO 1101) | ✅ | ❌ |
| **ISO 129 dimension tolerances** (±/limit/fit text) | ✅ | ❌ |
| Deterministic OSNAP (no coordinate guessing) | ✅ | ❌ |
| Scalar **drawing-score** / invalidity-ratio | ✅ | ❌ |
| Security-hardened (AutoLISP allowlist, path guards, HTTP auth) | ✅ | rare |
| Test suite | **360** | few / none |

---

## From the Author

I built **AutoCAD MCP Pro** because I needed it.

My day job at **Anka-Makine** revolves around intensive AutoCAD work — production drawings, parametric assemblies, strict layer standards across dozens of templates, dimensioning and block work under tight schedules, repeated audits, exports, and screenshots for design reviews. The repetitive parts of that workflow add up fast.

After months of leaning on this server inside my own daily workflow — and watching it shave hours off my week without a single misstep on critical drawings — I decided it deserved a public release. It works. It is fast. It stays out of the way.

The model on the other end of the wire does not matter. The Model Context Protocol is the contract; AutoCAD MCP Pro is one well-typed implementation of that contract. Any MCP-aware client — and the LLM behind it — sees the same 116 tools.

I will keep this repository actively maintained as my own use of it evolves, and **a public benchmark suite is on the way** — I want to give you numbers, not adjectives.

— *Umutcan Edizsalan · Anka-Makine*

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Why It's the Best AutoCAD MCP](#why-its-the-best-autocad-mcp)
- [Highlights](#highlights)
- [AI Client Compatibility](#ai-client-compatibility)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [MCP Client Configuration](#mcp-client-configuration)
- [Backend Selection](#backend-selection)
- [Configuration Reference](#configuration-reference)
- [Tool Catalog](#tool-catalog)
- [Architecture](#architecture)
- [Security Model](#security-model)
- [Benchmarks](#benchmarks)
- [Development](#development)
- [Roadmap](#roadmap)
- [Author](#author)
- [License](#license)

---

## Why This Exists

Most CAD-automation tooling falls into two camps: heavyweight enterprise plug-ins that lock you into a single vendor, or one-off Python scripts that solve a single drawing and rot a week later. Neither plays well with the modern AI workflow, where the *agent* — not the engineer — is the one driving the tool.

AutoCAD MCP Pro takes a different stance:

1. **One protocol, two engines.** A live **COM** backend talks to a running AutoCAD instance for in-app, real-time control. A headless **ezdxf** backend reads and writes DXF files anywhere — Linux, macOS, CI runners — with no AutoCAD installation required. Same tool surface, same response shapes, two execution modes.
2. **Built for agents.** Every tool has a typed schema, a deterministic error contract, and structured progress updates. No string-parsing tricks; no positional-argument guessing. Pydantic on the way in, dataclasses on the way out.
3. **Hardened by default.** Path traversal, command injection, AutoLISP escape, transaction-driven memory blowups, COM hangs — all addressed in the default configuration. You opt **in** to risk, never out.

---

## Why It's the Best AutoCAD MCP

The AutoCAD-MCP field is crowded, but it clusters into a familiar shape: a
COM-only, Windows-only script with a handful of `draw_line` / `draw_circle`
tools, no tests, no security model, and — crucially — **no idea whether the
drawing it produced is actually correct.** Those projects let an LLM *push
geometry*. AutoCAD MCP Pro is built to let an LLM *produce a drawing that passes
review.* That difference is the whole thesis, and it shows up in five places no
other AutoCAD MCP covers at once:

### 1. It is the only one that checks its own work

Every competing AutoCAD/CAD MCP surveyed — COM scripts, the LT/AutoLISP servers,
the multi-CAD COM bridges — will happily emit a drawing with a leftover
construction line, a non-standard lineweight, an untrimmed corner, or two
dimensions stacked on top of each other, and report success. AutoCAD MCP Pro
runs a **closed quality gate** at `drawing_finalize`: an 8-step structural
validator **plus** an ISO-128 premium critique (lineweights, layer colours,
untrimmed corners, duplicate entities, leftover scaffolding, dimension overlap,
and GD&T datum consistency). Leftover scaffolding or an off-standard lineweight
**blocks the gate** instead of slipping into a review. This design-rule
validation is the durable moat — and it is exactly the capability Autodesk's own
in-AutoCAD AI demo leads with (automated compliance checking).

### 2. It speaks real engineering, not just geometry

- **2D GD&T (ISO 1101 / ASME Y14.5)** — feature control frames and datum
  features, with a gate that rejects a frame referencing an undefined datum. No
  competing AutoCAD MCP, and none of the surveyed text-to-CAD products, ships 2D
  GD&T authoring *with validation*.
- **ISO 129 dimension tolerances** — `±` / deviation / limit / basic callouts
  and fit text (`⌀20 H7`). A drawing without tolerances is not manufacturable;
  most MCPs cannot express them at all.
- **Deterministic engineering primitives** — involute gears (front view +
  section A-A), DIN 6885 keyed bores, ISO 7200 title blocks — parametric, not
  hand-drawn line-by-line by the model.

### 3. It removes the #1 LLM drawing error: guessed coordinates

Research on program-to-geometry (GeoGramBench, 2026) shows frontier models score
under 50% when they have to *compute* points. AutoCAD MCP Pro gives the model
**deterministic OSNAP** instead — `point_from_snap`, `point_intersection`,
`point_tangent` return exact endpoints, intersections, and tangents so the model
never guesses a coordinate. `selection_get` even reads the user's live pick set,
so the AI edits exactly what was selected.

### 4. It runs where you run — live *and* headless

One tool surface over **two engines**: drive a live AutoCAD session over COM, or
run fully headless with ezdxf on Linux, macOS, or a CI runner with no AutoCAD
installed. Most competitors are COM-only (Windows + a running AutoCAD) *or*
file-only — not both behind an identical API with identical response shapes.

### 5. It is engineered like a product, not a demo

**360 passing tests**, a ruff-clean codebase, a security model that assumes
hostile input (AutoLISP allowlist with bypass-regression tests, path-traversal
guards, HTTP bind guard + bearer-token auth, per-call COM timeout), and a scalar
**drawing-score + invalidity-ratio** so quality is a number you can track across
releases — not an adjective. A reproducible correctness benchmark ships in
[`benchmarks/`](benchmarks/).

> **In one line:** other AutoCAD MCPs help a model *draw*; AutoCAD MCP Pro helps
> a model *deliver a drawing that passes engineering review* — validated,
> toleranced, standards-compliant, on any OS, with the tests to prove it.

See the [feature comparison](#what-makes-it-different) at the top and the
[Roadmap](#roadmap) for how the moat widens from here (closed-loop
`critique → repair` refiner, ISO 286 fits, public benchmark numbers).

---

## Highlights

- **Dual Engine Architecture**
  - **COM backend**: live AutoCAD control via the Win32 COM API, routed through a single-thread STA executor with a per-call timeout so an unresponsive AutoCAD never hangs the server.
  - **ezdxf backend**: headless DXF file operations powered by [ezdxf](https://github.com/mozman/ezdxf). Works on every platform, ideal for batch workloads and CI pipelines.
  - Automatic backend selection, with a clean override via `AUTOCAD_MCP_BACKEND`.

- **116 Tools, 14 Categories**
  - Drawing management — `drawing_new`, `drawing_open`, `drawing_save`, `drawing_save_as`, `drawing_export_dxf`, `drawing_export_pdf`, `drawing_purge`, `drawing_audit`, `drawing_undo`, `drawing_redo`, `drawing_close`
  - Entity creation — line, circle, arc, polyline, rectangle, text, mtext, hatch, spline, ellipse, point, block reference, batch create
  - Dimensions — linear, aligned, angular, radius, diameter (with ISO 129 `tol_mode`: ± / deviation / limit / basic + fit text)
  - Entity modification — move, copy, rotate, scale, mirror, offset, delete, rectangular/polar array, batch modify, set properties, plus in-place `entity_edit_text` and `entity_edit_geometry` (handle-preserving)
  - Entity query — `entity_get`, `entity_list`, `entity_delete_many`, and `selection_get` (read the user's live viewport "pickfirst" selection so the AI dimensions/edits only what was picked, not the whole drawing — COM backend)
  - Layer management — full lifecycle: create, delete, modify, freeze/thaw, lock/unlock, hide/show, isolate, set current
  - Block operations — list, insert, explode, attribute get/set, create-from-entities, find references
  - Analysis — entity stats, region select, distance/area measurement, bounding box, select by type/layer, layer statistics
  - View control — zoom extents, zoom window, screenshot, combined zoom-and-screenshot
  - Transactions — begin, commit, rollback, with disk-backed snapshots
  - System — status, get/set variables, run command, run AutoLISP, about, plus `drawing_settings` (friendly units/scale/precision/osnap facade)
  - Templates and validation — apply standard layer templates, validate drawings against rule sets
  - Engineering / deterministic CAD — involute gear front view + section A-A, DIN 6885 keyed bore, ISO A3 title block, and the 8-step `drawing_finalize` gate
  - GD&T (ISO 1101 / ASME Y14.5) — `gd_frame` (feature control frames: all 14 characteristics, ⌀ zones, Ⓜ/Ⓛ/Ⓢ modifiers, multi-datum) and `datum_feature`, with a datum-consistency critique gate
  - Premium drafting workflow — `drawing_plan`, deterministic OSNAP (`point_from_snap` / `point_intersection` / `point_tangent`), `drawing_apply_iso_layers`, `dimension_auto`, `entity_select_smart`, `drawing_critique`, `construction_*`, and a scalar drawing-score + invalidity-ratio at finalize

- **Production-Grade Plumbing**
  - FastMCP 3.0 lifespan-managed backend singleton
  - Middleware stack: error handling, audit logging, timing, request logging
  - Structured progress reports for long-running operations (`drawing_open`, exports, batch ops)
  - 360 tests across drawing, entity, dimension, layer, block, analysis, batch/template, engineering, GD&T, premium, mocked-COM, and security suites
  - Ruff-clean codebase, 360-test suite

- **Closed-Loop Quality Gate**
  - `drawing_finalize` runs **both** the 8-step structural validator **and** the premium ISO-128 critique (lineweights, layer colors, untrimmed corners, duplicate entities, leftover construction, dimension overlap) — leftover scaffolding or a non-standard lineweight blocks the gate instead of slipping through.
  - Deterministic geometry: `point_from_snap` / `point_intersection` / `point_tangent` give the agent exact OSNAP coordinates instead of guessed ones — the single biggest source of LLM drawing errors.
  - Cross-backend parity: the same `EntityInfo.properties` contract, save-format-from-extension, offset side selection, and ARC length on **both** engines.

- **Security-First Defaults**
  - Path traversal & system-directory protection
  - AutoLISP allowlist with regression tests for known bypass patterns (`vla-SendCommand`, `acet-*`, alias tricks, `funcall` indirection, `c:` custom commands, error-handler hijacks)
  - Command sanitization for `system_run_command`
  - HTTP transport refuses non-loopback bind without an explicit opt-in **and** a configured auth token
  - Configurable file size limit on DXF input (`MAX_DXF_BYTES`) blocks decompression-bomb-style attacks
  - Per-call COM timeout (`COM_CALL_TIMEOUT`) prevents a hung AutoCAD from freezing the server

---

## AI Client Compatibility

AutoCAD MCP Pro implements the Model Context Protocol. **If a host can speak MCP, it can drive this server.** No model-specific code, no per-vendor patches — the contract is the tool schema, and any MCP-aware client (and any LLM behind it) inherits the full 116-tool surface for free.

| Host                        | Status      | Notes                              |
|-----------------------------|-------------|------------------------------------|
| Claude Desktop              | Verified    | Native MCP support                 |
| Cursor                      | Verified    | Native MCP support                 |
| Cline / Roo Code (VS Code)  | Verified    | Native MCP support                 |
| Continue                    | Verified    | MCP via configuration              |
| Goose                       | Verified    | MCP via configuration              |
| Custom MCP clients          | Supported   | STDIO and HTTP transports          |

---

## Quickstart

```bash
git clone https://github.com/U-C4N/autocad-mcp.git
cd autocad-mcp
pip install -e ".[full]"
python server.py
```

That is it. The server starts in STDIO mode and your MCP client will discover all 116 tools.

For headless / CI workflows:

```bash
AUTOCAD_MCP_BACKEND=ezdxf python server.py
```

For HTTP transport (local-only by default — see [Security Model](#security-model)):

```bash
fastmcp run server.py:mcp --transport http --port 8000
```

---

## Installation

### Core (ezdxf backend only — works everywhere)

```bash
pip install -e .
```

### With live AutoCAD control (Windows + AutoCAD)

```bash
pip install -e ".[com]"
```

### With PDF export and matplotlib-based screenshots

```bash
pip install -e ".[pdf]"
```

### Everything

```bash
pip install -e ".[full]"
```

### Development

```bash
pip install -e ".[full]"
pip install pytest pytest-asyncio pytest-cov ruff
```

---

## MCP Client Configuration

### Claude Desktop

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "autocad": {
      "command": "python",
      "args": ["C:/path/to/autocad-mcp/server.py"],
      "env": {
        "AUTOCAD_MCP_BACKEND": "auto",
        "ALLOWED_PATHS": "C:/Users/you/Documents/AutoCAD"
      }
    }
  }
}
```

### Cursor

`Settings → MCP → Add new server` and point at `python /path/to/server.py`.

### Cline / Continue / Goose

All standard MCP `command` + `args` configuration; same shape as Claude Desktop.

---

## Backend Selection

| `AUTOCAD_MCP_BACKEND` | Behavior                                                                              |
|-----------------------|---------------------------------------------------------------------------------------|
| `auto` *(default)*    | Try COM first on Windows, fall back to ezdxf if AutoCAD is not reachable.             |
| `com`                 | Force COM. Fails fast if AutoCAD is not running.                                      |
| `ezdxf`               | Force headless ezdxf. Works on Linux, macOS, Windows with no AutoCAD.                 |

---

## Configuration Reference

Copy `.env.example` to `.env` and edit:

| Variable                       | Default              | Purpose                                                               |
|--------------------------------|----------------------|-----------------------------------------------------------------------|
| `AUTOCAD_MCP_BACKEND`          | `auto`               | Backend selection (`auto`, `com`, `ezdxf`).                           |
| `LOG_LEVEL`                    | `INFO`               | Standard Python logging level.                                        |
| `ALLOWED_PATHS`                | *(empty)*            | Comma-separated absolute paths the server may read/write.             |
| `MAX_UNDO_STACK`               | `5`                  | Maximum number of in-flight transaction snapshots.                    |
| `MAX_DXF_BYTES`                | `52428800` (50 MB)   | Reject DXF files larger than this on `drawing_open`. `0` to disable.  |
| `MAX_LIST_LIMIT`               | `5000`               | Hard cap for `entity_list` and `analysis_select_*` responses.         |
| `COM_CALL_TIMEOUT`             | `60` (seconds)       | Per-call timeout for COM operations. Prevents a hung AutoCAD blocking the server. |
| `DANGEROUS_COMMANDS_ENABLED`   | `false`              | Disable command and AutoLISP sanitization. **Loud warning at startup.** |
| `ALLOW_REMOTE_HTTP`            | `false`              | Permit HTTP transport on non-loopback hosts.                          |
| `MCP_AUTH_TOKEN`               | *(empty)*            | Required when `ALLOW_REMOTE_HTTP=true`. Bearer token for HTTP clients. |

---

## Tool Catalog

| Group               | Count | Sample tools                                                              |
|---------------------|------:|---------------------------------------------------------------------------|
| Drawing             |    11 | `drawing_new`, `drawing_open`, `drawing_save`, `drawing_export_pdf`, `drawing_purge`, `drawing_close` |
| Entity Creation     |    13 | `entity_create_line`, `entity_create_polyline`, `entity_create_hatch`, `entity_create_block_ref`      |
| Dimensions          |     5 | `dimension_linear`, `dimension_aligned`, `dimension_angular`, `dimension_radius`, `dimension_diameter` (with ISO 129 `tol_mode`) |
| Entity Modification |    12 | `entity_move`, `entity_rotate`, `entity_offset`, `entity_edit_text`, `entity_edit_geometry`, `entity_set_properties` |
| Entity Query        |     4 | `entity_get`, `entity_list`, `entity_delete_many`, `selection_get`                                    |
| Layer Management    |    12 | `layer_create`, `layer_freeze`, `layer_isolate`, `layer_modify`                                       |
| Block Operations    |     7 | `block_insert`, `block_explode`, `block_create_from_entities`, `block_find_references`                |
| Analysis            |     8 | `analysis_entity_stats`, `analysis_bounding_box`, `analysis_select_by_layer`, `analysis_layer_stats`  |
| View                |     4 | `view_zoom_extents`, `view_screenshot`, `view_zoom_and_screenshot`                                    |
| Transactions        |     3 | `transaction_begin`, `transaction_commit`, `transaction_rollback`                                     |
| System              |     7 | `system_status`, `system_run_command`, `system_run_lisp`, `system_about`, `drawing_settings`         |
| Batch / Templates   |     5 | `entity_batch_create`, `entity_batch_modify`, `template_apply_layers`, `validation_check`             |
| Engineering         |     7 | `gear_draw_*`, `keyway_draw_*`, `titleblock_apply_iso_a3`, `drawing_finalize`                          |
| Premium workflow    |    11 | `drawing_plan`, `drawing_critique`, `point_from_snap` / `point_intersection` / `point_tangent`, `dimension_auto`, `entity_select_smart` |
| GD&T (ISO 1101)     |     2 | `gd_frame` (feature control frame), `datum_feature`                                                   |

`system_about` returns the live tool inventory — the counts above are illustrative; the runtime number is authoritative.

---

## Architecture

```
server.py                  FastMCP 3.0 server (lifespan, middleware, tools)
│
├── config.py              Centralized environment-driven configuration
├── security.py            Path validation, command + LISP sanitization
│
└── backends/
    ├── base.py            AutoCADBackend ABC + shared dataclasses
    │                      (EntityInfo, LayerInfo, BlockInfo, DrawingInfo, CommandResult)
    ├── ezdxf_backend.py   Headless DXF/DWG via ezdxf
    │                      sync calls wrapped in asyncio.to_thread
    │                      transaction snapshots persisted to temp files
    └── com_backend.py     Live AutoCAD via pywin32
                           single-thread STA executor with per-call timeout
                           UUID-named selection sets, leak-free cleanup
```

The server boots once, the backend is initialized in the FastMCP lifespan, and every tool call is dispatched through the middleware stack:

`ErrorHandlingMiddleware → AuditMiddleware → TimingMiddleware → LoggingMiddleware → tool`

Tool returns are flowed back through `_dc()`, which converts dataclasses to JSON-serializable dicts and preserves the typed contract on the wire.

---

## Security Model

AutoCAD MCP Pro assumes a hostile-input threat model: the MCP client may be untrusted, the model behind it may be jailbroken, and the inputs to every tool may be adversarial.

- **AutoLISP allowlist** — `security.py` blocks the full ActiveX/COM family (`vla-*`, `vlax-*`, `vlr-*`), Express Tools (`acet-*`), command channels (`command`, `command-s`, `vl-cmdf`), file I/O, code loading, indirection vectors (`funcall`, `function`, `apply`, `eval`), custom command invocation (`c:*`), and error-handler hijacks. Every known bypass is covered by a regression test.
- **Command sanitization** — destructive AutoCAD verbs (`ERASE`, `PURGE`, `SHELL`, `SCRIPT`, `APPLOAD`, `NETLOAD`, `VBARUN`, …) are rejected unless `DANGEROUS_COMMANDS_ENABLED=true` is set, in which case the server logs a loud `WARNING` at startup and surfaces an `unsafe_mode` flag in `system_status` and `system_about`.
- **Path validation** — every tool that takes a path runs through `validate_path()`, which blocks traversal patterns, system directories, and constrains writes to a configurable `ALLOWED_PATHS` list.
- **HTTP transport guard** — by default the server refuses to bind anything other than `127.0.0.1`. To bind a non-loopback host you must opt in via `ALLOW_REMOTE_HTTP=true` **and** set `MCP_AUTH_TOKEN`.
- **Resource exhaustion guards** — `MAX_DXF_BYTES` rejects oversize input, `MAX_LIST_LIMIT` caps response sizes, transaction snapshots persist to disk so memory stays bounded, and `COM_CALL_TIMEOUT` keeps a hung AutoCAD from taking the server with it.

If you find a security issue, please open a private contact rather than a public issue.

---

## Benchmarks

### Correctness — v1.1.0 vs v1.0.0

A reproducible A/B suite ([`benchmarks/`](benchmarks/)) runs the **same** 21
deterministic, headless (ezdxf) checks against the public v1.0.0 release
(`origin/main`) and v1.1.0 — each check in its own subprocess, so a hard crash is
recorded as a miss instead of taking down the run.

| Version | Checks passing | Pass rate |
|---------|----------------|-----------|
| **v1.0.0** (public release) | 8 / 21 | **38.1 %** |
| **v1.1.0** (this release)   | 21 / 21 | **100 %** |

**13 defects fixed · 0 regressions · 2.6× higher correctness pass-rate (+61.9 pts).**
Fixes span dimensions (aligned/angular no longer raise), full-circle arrays, deterministic
geometry (`point_intersection`/`point_tangent`), ARC selection, property parity, MTEXT
rotation, the headless screenshot crash, the now-live `dim_overlap` critique, ISO-13567
layer routing, and gear-outline geometry. Six core operations pass on **both** versions, so
the suite is not a cherry-picked failure list — see [`benchmarks/README.md`](benchmarks/README.md)
for the full table, methodology, and honesty caveats.

```bash
python benchmarks/compare_versions.py        # reproduce: current tree vs origin/main
```

### Performance (throughput) — coming

A scale/throughput suite is in active development. Targets:

- **Drawing scale** — 1k / 10k / 100k entity workloads
- **Workload classes** — bulk creation, mass-modify, region select, render-and-screenshot, end-to-end design pass
- **Backend variants** — ezdxf on CPython 3.11/3.12, COM against AutoCAD 2024+
- **Model compatibility** — tool-call success rate and prompt token usage by model, on a fixed set of canonical CAD prompts

Numbers will land in [`benchmarks/`](benchmarks/) with a one-command runner and a hardware footprint. The table below will be updated as new models and AutoCAD versions release.

| Workload                       | ezdxf (3.12) | COM (AutoCAD 2025) | Notes |
|--------------------------------|--------------|--------------------|-------|
| Open + audit 10k-entity DXF    | *coming*     | *coming*           |       |
| Bulk-create 5k LINE entities   | *coming*     | *coming*           |       |
| Region select on 100k drawing  | *coming*     | *coming*           |       |
| End-to-end "design pass" prompt| *coming*     | *coming*           | by model family |

> Have a workload you want included? Open an issue.

---

## Development

### Run tests

```bash
pytest -v
```

### Coverage report

```bash
pytest --cov=. --cov-report=term-missing
```

### Lint and format

```bash
ruff check .
ruff format --check .
```

### Project structure

```
autocad-mcp/
├── server.py
├── config.py
├── security.py
├── backends/
│   ├── base.py
│   ├── ezdxf_backend.py
│   └── com_backend.py
├── tests/
│   ├── test_drawing.py
│   ├── test_entity_creation.py
│   ├── test_dimensions.py
│   ├── test_layer_block.py
│   ├── test_analysis.py
│   ├── test_batch_template.py
│   ├── test_ezdxf_backend.py
│   └── test_security.py
├── pyproject.toml
├── Dockerfile
└── .github/workflows/ci.yml
```

---

## Roadmap

Sequenced by dependency, not wishlist: each release builds on the one before it.
The theme is **widen the standards-validation moat, then close the loop, then
reach production-drawing parity** — and only then chase breadth.

### Shipped

- [x] **1.0 — Foundation.** Dual COM + ezdxf engine, FastMCP 3.0 middleware stack, the core drawing / entity / layer / block / dimension / analysis tool surface.
- [x] **1.1 — Correctness & the enforced quality gate.** `drawing_finalize` runs the premium ISO-128 critique; deterministic geometry (`point_intersection` / `point_tangent`); dimension / save-format / polar-array / offset fixes across both engines; COM robustness (CoUninitialize, transaction & LISP guards); security hardening (HTTP bind guard, AutoLISP-allowlist bypass tests); mocked-COM harness. **318 tests.**
- [x] **1.2 — ISO production + a measurable moat.** 2D GD&T (ISO 1101) feature control frames + datum features with a datum-consistency gate; ISO 129 dimension tolerances (±/deviation/limit/basic + text override); in-place `entity_edit_text` / `entity_edit_geometry`; the `drawing_settings` facade; scalar drawing-score + invalidity-ratio at finalize. **360 tests.**

### Next — own the closed loop (the #1 accuracy lever)

- [ ] **1.3 — Closed-loop refiner.** Iterative `critique → repair → re-critique` with dedicated transaction-stack isolation, plus a pre-plan clarification pass in `drawing_plan` that surfaces missing/conflicting dimensions before any geometry. *Depends on the 1.2 scalar score as its objective function.*
- [ ] **1.4 — ISO production depth.** ISO 286 fit tables (`H7`/`g6` → resolved deviations feeding the 1.2 tolerance engine), a reusable ISO-25 dimension style, and MLEADER leader notes.

### Then — prove it & harden it

- [ ] **1.5 — Public benchmark suite.** A reproducible one-command runner in `benchmarks/` (correctness + throughput by backend and model) — turns the "numbers, not adjectives" promise into CI-tracked figures, anchored on the 1.2 drawing-score.
- [ ] **1.6 — Architecture & capability introspection.** A backend `capabilities()` map with per-tool enablement (e.g. auto-hide `system_run_command` on ezdxf), plus a `server.py` module split into a clean `services/` orchestration layer.
- [ ] **1.7 — CI & coverage.** Windows CI matrix exercising the mocked COM backend on every push, with a coverage gate.

### Later — breadth (table-stakes elsewhere, deliberately deferred)

- [ ] **2.0 — Multi-document & paper space.** Multi-drawing context, xref-aware tools, and first-class layout / paper-space + plot configuration.
- [ ] **2.1 — Optional 3D solids tier (COM-only).** Extrude / revolve / boolean on the live COM backend; ezdxf intentionally stays 2D (no ACIS kernel), so this ships behind a capability flag rather than breaking dual-backend parity.
- [ ] **2.2 — Native Linux/macOS live control.** Round-trip DWG via the [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter) so headless hosts get true DWG in/out.

---

## Requirements

- Python **3.11+**
- [FastMCP](https://github.com/jlowin/fastmcp) **3.0+**
- [ezdxf](https://github.com/mozman/ezdxf) **1.3+**
- *(optional, COM backend)* `pywin32` **306+**, AutoCAD 2020 or newer
- *(optional, screenshots)* `Pillow` **10.0+**
- *(optional, PDF export)* `matplotlib` **3.8+**

---

## Contributing

Pull requests are welcome — especially around the COM backend (mocking, additional Windows tooling), benchmark suite contributions, and additional layer / dimension standards.

For non-trivial changes, please open an issue first to align on direction.

---

## Author

**Umutcan Edizsalan**
Mechanical / engineering work at **Anka-Makine**.
Builds tools that survive contact with real production drawings.

GitHub: [@U-C4N](https://github.com/U-C4N)

This project exists because it earned its place in my own daily workflow. I will keep it maintained and aligned with my real usage.

---

## License

MIT — see [LICENSE](LICENSE).

Copyright © 2026 Umutcan Edizsalan.
