---
name: autocad-mcp
description: |
  Automate AutoCAD drawing operations through AutoCAD MCP Pro server (FastMCP 3.0).
  86 tools for drawings, entities, layers, blocks, dimensions, analysis, batch ops,
  templates, and validation. Dual backends: COM (live AutoCAD) and ezdxf (headless DXF).

  Trigger when: (1) User mentions AutoCAD, DXF, DWG, or CAD drawings,
  (2) User wants to create/modify engineering drawings programmatically,
  (3) Working with tools prefixed drawing_, entity_, layer_, block_, dimension_,
  analysis_, view_, system_, template_, or validation_,
  (4) User asks about CAD automation, drafting workflows, or MCP server setup.
---

# AutoCAD MCP Pro

## Contents

- [Quick Start](#quick-start)
- [Backend Selection](#backend-selection)
- [Key Concepts](#key-concepts)
- [Tool Groups](#tool-groups)
- [Common Workflows](#common-workflows)
- [Security Rules](#security-rules)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Quick Start

Standard workflow for any drawing task:

```
1. drawing_new()                              # or drawing_open(path)
2. layer_create(name, color, linetype)        # set up layers
3. entity_create_*(...)                       # draw geometry
4. dimension_*(...)                           # add dimensions
5. analysis_entity_stats()                    # verify drawing
6. drawing_save()                             # persist changes
```

Use `transaction_begin()` before complex operations. If something goes wrong, `transaction_rollback()` reverts all changes since begin.

For batch operations, use `entity_batch_create(entities)` with a list of entity definitions — handles are returned for each created entity.

## Backend Selection

| Environment Variable | Behavior |
|---------------------|----------|
| `AUTOCAD_MCP_BACKEND=auto` | Try COM first, fall back to ezdxf (default) |
| `AUTOCAD_MCP_BACKEND=com` | Force COM — requires running AutoCAD on Windows |
| `AUTOCAD_MCP_BACKEND=ezdxf` | Force ezdxf — headless DXF ops, no AutoCAD needed |

COM-only features: `system_run_command`, `system_run_lisp`, `view_zoom_extents/window` (view ops are no-ops in ezdxf). Screenshots: COM uses Win32 capture, ezdxf uses matplotlib render.

## Key Concepts

**Entity handles**: Hex strings (e.g. `"1A2B"`) returned by all create/copy operations. Required for modify/query operations (`entity_get`, `entity_move`, `entity_delete`, etc.).

**Coordinates**: Drawing units (mm default). Angles in degrees, counter-clockwise from X axis.

**ACI colors**: 1–255 = specific colors, 256 = ByLayer, 0 = ByBlock. Common: 1=red, 2=yellow, 3=green, 4=cyan, 5=blue, 6=magenta, 7=white.

**Transactions**: `transaction_begin` → operations → `transaction_commit` or `transaction_rollback`. ezdxf uses full DXF snapshots; COM uses native undo marks.

## Tool Groups

| Group | Count | Key Tools | Details |
|-------|-------|-----------|---------|
| Drawing Management | 11 | `drawing_new`, `drawing_open`, `drawing_save`, `drawing_export_*` | [tools-drawing.md](references/tools-drawing.md) |
| Entity Creation | 13 | `entity_create_line/circle/arc/polyline/text/hatch/...` | [tools-entity-creation.md](references/tools-entity-creation.md) |
| Entity Modification | 13 | `entity_move/copy/rotate/scale/mirror/offset/delete/...` | [tools-entity-modification.md](references/tools-entity-modification.md) |
| Dimensions | 5 | `dimension_linear/aligned/angular/radius/diameter` | [tools-dimensions.md](references/tools-dimensions.md) |
| Layer Management | 12 | `layer_create/delete/freeze/thaw/lock/unlock/isolate/...` | [tools-layers.md](references/tools-layers.md) |
| Block Operations | 7 | `block_insert/explode/create_from_entities/attributes/...` | [tools-blocks.md](references/tools-blocks.md) |
| Analysis | 9 | `analysis_entity_stats/find_in_region/measure_*/bounding_box` | [tools-analysis.md](references/tools-analysis.md) |
| Batch & Templates | 4 | `entity_batch_create/modify`, `template_apply_layers/list` | [tools-batch-template.md](references/tools-batch-template.md) |
| Validation | 1 | `validation_check` | [tools-batch-template.md](references/tools-batch-template.md) |
| View & Screenshot | 5 | `view_zoom_extents/window/screenshot/zoom_and_screenshot` | [tools-view-system.md](references/tools-view-system.md) |
| Transactions | 3 | `transaction_begin/commit/rollback` | [tools-view-system.md](references/tools-view-system.md) |
| System | 6 | `system_status/get_variable/run_command/run_lisp/about` | [tools-view-system.md](references/tools-view-system.md) |

**Resources** (6): `autocad://drawing`, `autocad://layers`, `autocad://blocks`, `autocad://stats`, `autocad://status`, `autocad://entities/{layer_name}`

**Prompt templates** (5): `prompt_floor_plan`, `prompt_pid_diagram`, `prompt_electrical_schematic`, `prompt_mechanical_drawing`, `prompt_quick_drawing`

## Common Workflows

**New drawing from scratch**: Set up layers first, then draw entities, add dimensions, save.
See [workflows.md](references/workflows.md) for step-by-step checklists.

**Edit existing DXF**: `drawing_open` → `entity_list` to find entities → modify/delete → save.

**Batch operations**: `entity_batch_create([{type:"line", ...}, {type:"circle", ...}])` — single call, multiple entities.

**Template-based**: `template_apply_layers("architectural")` creates standard layer sets, then add content.

**Quality check**: `validation_check(["empty_layers", "zero_length", "duplicate_entities"])` reports issues.

## Security Rules

All file paths pass through `validate_path()`:
- Path traversal blocked (`../` patterns rejected)
- `ALLOWED_PATHS` env restricts accessible directories
- Write operations require `allow_write=True`

Commands pass through `sanitize_command()`:
- Dangerous patterns blocked: ERASE ALL, DELETE, PURGE, QUIT
- LISP sanitized: `startapp`, `vl-file-delete`, `dos_*` rejected
- Override: `DANGEROUS_COMMANDS_ENABLED=true`

Details: [security.md](references/security.md)

## Architecture

```
server.py                    FastMCP 3.0 server (86 tools, 6 resources, 5 prompts)
├── config.py                Centralized pydantic-settings configuration
├── security.py              Path validation + command sanitization
└── backends/
    ├── base.py              AutoCADBackend ABC + data models
    ├── ezdxf_backend.py     Headless DXF via ezdxf (async via _async wrapper)
    └── com_backend.py       Live AutoCAD via pywin32 COM (STA single-thread)
```

Middleware stack: ErrorHandling → AuditLog → Timing → Logging

Adding a new tool: (1) abstract method in `base.py` → (2) implement in `ezdxf_backend.py` → (3) implement in `com_backend.py` → (4) register in `server.py` with `@mcp.tool` → (5) test

Details: [architecture.md](references/architecture.md)

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Backend unavailable" | Call `drawing_new()` or `drawing_open(path)` first |
| "Entity handle not found" | Use `entity_list()` to get valid handles |
| "Layer not found" | `layer_list()` to see existing, `layer_create()` to add |
| "Path validation failed" | Use absolute paths within `ALLOWED_PATHS` |
| "Command rejected" | Check `DANGEROUS_COMMANDS_ENABLED` setting |
| "COM backend failed" | Verify AutoCAD is running, or switch to ezdxf |
| "View ops are no-ops" | View/zoom only work with COM backend |

Full list: [troubleshooting.md](references/troubleshooting.md)

## Examples

- [Basic drawing workflow](examples/basic-workflow.md) — Room with walls, door, dimensions
- [Floor plan](examples/floor-plan.md) — Multi-room apartment layout
- [Mechanical part](examples/mechanical-part.md) — Flange with bolt pattern

## Utility Scripts

**Setup check**: `python scripts/check_setup.py` — Verify dependencies and configuration

**Drawing validation**: `python scripts/validate_drawing.py` — Check for common drawing issues
